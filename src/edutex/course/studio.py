"""Loopback-only visual editor for EduTeX course manifests."""
from __future__ import annotations

import hashlib
import json
import os
import secrets
import stat
import tempfile
import webbrowser
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from importlib.resources import files
from pathlib import Path
from typing import Any
from urllib.parse import parse_qs, urlsplit

import yaml

from edutex.course.service import CourseValidation, load_course_manifest

MAX_REQUEST_BYTES = 1_000_000


class StudioError(ValueError):
    """Base error for local authoring operations."""


class StudioConflictError(StudioError):
    """The manifest changed after the editor loaded it."""


class StudioValidationError(StudioError):
    """A proposed manifest failed EduTeX course validation."""

    def __init__(self, report: CourseValidation) -> None:
        self.report = report
        super().__init__("; ".join(report.errors) or "Course manifest is invalid.")


def _resolve_paths(project_root: Path, manifest_path: Path | str = "course.yaml") -> tuple[Path, Path]:
    root = Path(project_root).expanduser().resolve()
    candidate = Path(manifest_path).expanduser()
    if not candidate.is_absolute():
        candidate = root / candidate
    candidate = candidate.resolve()
    try:
        candidate.relative_to(root)
    except ValueError as exc:
        raise StudioError("The course manifest must be inside the project directory.") from exc
    if not candidate.is_file():
        raise StudioError(f"Course manifest not found: {candidate}")
    return root, candidate


def _etag(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _course_mapping(document: dict[str, Any]) -> dict[str, Any]:
    nested = document.get("course")
    if isinstance(nested, dict):
        return nested
    return document


def load_course_document(
    project_root: Path, manifest_path: Path | str = "course.yaml"
) -> tuple[dict[str, Any], str, CourseValidation]:
    """Return the raw YAML mapping, its content hash, and validation report."""
    root, path = _resolve_paths(project_root, manifest_path)
    try:
        document = yaml.safe_load(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, yaml.YAMLError) as exc:
        raise StudioError(f"Could not read course manifest: {exc}") from exc
    if not isinstance(document, dict) or not isinstance(_course_mapping(document), dict):
        raise StudioError("Course manifest must contain a YAML mapping.")
    report = load_course_manifest(path, root)
    return document, _etag(path), report


def save_course_document(
    project_root: Path,
    document: dict[str, Any],
    expected_etag: str,
    manifest_path: Path | str = "course.yaml",
) -> tuple[str, CourseValidation]:
    """Validate and atomically save an edited raw YAML document."""
    root, path = _resolve_paths(project_root, manifest_path)
    if not isinstance(document, dict) or not isinstance(_course_mapping(document), dict):
        raise StudioError("Edited course manifest must be a YAML mapping.")
    if not secrets.compare_digest(_etag(path), str(expected_etag)):
        raise StudioConflictError("The manifest changed on disk. Reload before saving.")

    temp_path: Path | None = None
    try:
        with tempfile.NamedTemporaryFile(
            mode="w",
            encoding="utf-8",
            newline="\n",
            prefix=f".{path.name}.",
            suffix=".tmp.yaml",
            dir=path.parent,
            delete=False,
        ) as handle:
            temp_path = Path(handle.name)
            yaml.safe_dump(document, handle, sort_keys=False, allow_unicode=True)
            handle.flush()
            os.fsync(handle.fileno())

        report = load_course_manifest(temp_path, root)
        if not report.valid:
            raise StudioValidationError(report)
        os.chmod(temp_path, stat.S_IMODE(path.stat().st_mode))
        os.replace(temp_path, path)
        temp_path = None
        return _etag(path), load_course_manifest(path, root)
    except StudioError:
        raise
    except (OSError, UnicodeError, yaml.YAMLError, TypeError, ValueError) as exc:
        raise StudioError(f"Could not save course manifest: {exc}") from exc
    finally:
        if temp_path is not None:
            try:
                temp_path.unlink(missing_ok=True)
            except OSError:
                pass


def _json_response(handler: BaseHTTPRequestHandler, status: int, payload: dict[str, Any]) -> None:
    body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
    handler.send_response(status)
    handler.send_header("Content-Type", "application/json; charset=utf-8")
    handler.send_header("Content-Length", str(len(body)))
    handler.send_header("Cache-Control", "no-store")
    handler.send_header("X-Content-Type-Options", "nosniff")
    handler.send_header("Referrer-Policy", "no-referrer")
    handler.end_headers()
    handler.wfile.write(body)


def run_author_studio(
    project_root: Path,
    manifest_path: Path | str = "course.yaml",
    *,
    open_browser: bool = True,
) -> None:
    """Serve the course editor on loopback until interrupted by the user."""
    root, manifest = _resolve_paths(project_root, manifest_path)
    token = secrets.token_urlsafe(32)
    studio_html = files("edutex.course").joinpath("studio.html").read_text(encoding="utf-8")

    class StudioHandler(BaseHTTPRequestHandler):
        server_version = "EduTeXStudio/1.0"

        def log_message(self, _format: str, *_args: object) -> None:
            return

        def _host_ok(self) -> bool:
            expected = f"127.0.0.1:{self.server.server_port}"
            return self.headers.get("Host", "") == expected

        def _authorized(self) -> bool:
            return (
                self._host_ok()
                and secrets.compare_digest(
                    self.headers.get("X-EduTeX-Token", ""), token
                )
            )

        def _send_page(self, supplied_token: str) -> None:
            page = studio_html.replace("__EDUTEX_STUDIO_TOKEN__", json.dumps(supplied_token))
            body = page.encode("utf-8")
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.send_header("Content-Length", str(len(body)))
            self.send_header("Cache-Control", "no-store")
            self.send_header("X-Content-Type-Options", "nosniff")
            self.send_header("Referrer-Policy", "no-referrer")
            self.send_header(
                "Content-Security-Policy",
                "default-src 'self'; connect-src 'self'; img-src 'self' data:; "
                "style-src 'self' 'unsafe-inline'; script-src 'self' 'unsafe-inline'; "
                "object-src 'none'; base-uri 'none'; frame-ancestors 'none'",
            )
            self.end_headers()
            self.wfile.write(body)

        def do_GET(self) -> None:
            parsed = urlsplit(self.path)
            if parsed.path == "/":
                supplied = parse_qs(parsed.query).get("token", [""])[0]
                if not self._host_ok() or not secrets.compare_digest(supplied, token):
                    self.send_error(403, "Invalid local studio token")
                    return
                self._send_page(supplied)
                return
            if parsed.path != "/api/course" or not self._authorized():
                self.send_error(404 if parsed.path != "/api/course" else 403)
                return
            try:
                document, etag, report = load_course_document(root, manifest)
                _json_response(
                    self,
                    200,
                    {
                        "document": document,
                        "course": _course_mapping(document),
                        "etag": etag,
                        "valid": report.valid,
                        "errors": report.errors,
                        "warnings": report.warnings,
                    },
                )
            except (StudioError, TypeError, ValueError) as exc:
                _json_response(self, 422, {"error": str(exc)})

        def do_POST(self) -> None:
            if urlsplit(self.path).path != "/api/course":
                self.send_error(404)
                return
            if not self._authorized():
                self.send_error(403, "Invalid local studio token")
                return
            origin = self.headers.get("Origin")
            expected_origin = f"http://127.0.0.1:{self.server.server_port}"
            if origin and origin != expected_origin:
                self.send_error(403, "Cross-origin requests are not allowed")
                return
            try:
                length = int(self.headers.get("Content-Length", "0"))
            except ValueError:
                self.send_error(400, "Invalid Content-Length")
                return
            if length < 1 or length > MAX_REQUEST_BYTES:
                self.send_error(413, "Request body is empty or too large")
                return
            try:
                payload = json.loads(self.rfile.read(length).decode("utf-8"))
                if not isinstance(payload, dict):
                    raise StudioError("Request body must be a JSON object.")
                new_etag, report = save_course_document(
                    root,
                    payload.get("document"),
                    str(payload.get("etag", "")),
                    manifest,
                )
                _json_response(
                    self,
                    200,
                    {"saved": True, "etag": new_etag, "warnings": report.warnings},
                )
            except StudioConflictError as exc:
                _json_response(self, 409, {"error": str(exc), "reload": True})
            except StudioValidationError as exc:
                _json_response(
                    self,
                    422,
                    {
                        "error": "Course validation failed; no changes were saved.",
                        "errors": exc.report.errors,
                        "diagnostics": [item.to_dict() for item in exc.report.diagnostics],
                    },
                )
            except (StudioError, UnicodeError, json.JSONDecodeError) as exc:
                _json_response(self, 400, {"error": str(exc)})

    server = ThreadingHTTPServer(("127.0.0.1", 0), StudioHandler)
    server.daemon_threads = True
    url = f"http://127.0.0.1:{server.server_port}/?token={token}"
    print(f"EduTeX course studio: {url}")
    print("The editor is available only on this computer. Press Ctrl+C to stop it.")
    if open_browser:
        webbrowser.open_new_tab(url)
    try:
        server.serve_forever(poll_interval=0.2)
    except KeyboardInterrupt:
        print("\nEduTeX course studio stopped.")
    finally:
        server.server_close()
