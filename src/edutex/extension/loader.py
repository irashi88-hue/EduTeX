"""Load and validate user extension assets."""

from __future__ import annotations

import importlib
import importlib.util
from pathlib import Path
from types import ModuleType

import yaml

from edutex.core.errors import ExtensionError
from edutex.extension.models import ExtensionManifest, LoadedExtension


class ExtensionLoader:
    """Load one extension manifest and its contribution handler."""

    def load(self, manifest_path: Path, expected_id: str | None = None) -> LoadedExtension:
        if not manifest_path.is_file():
            raise ExtensionError(f"Extension asset not found: {manifest_path}")

        try:
            raw = yaml.safe_load(manifest_path.read_text(encoding="utf-8"))
        except yaml.YAMLError as exc:
            raise ExtensionError(
                f"Failed to parse extension asset {manifest_path}: {exc}"
            ) from exc

        if not isinstance(raw, dict):
            raise ExtensionError("Extension asset must be a YAML mapping.")

        required = ("id", "name", "version", "target", "module", "entrypoint")
        missing = [
            field
            for field in required
            if field not in raw
            or raw[field] is None
            or (isinstance(raw[field], str) and not raw[field].strip())
        ]
        if missing:
            raise ExtensionError(
                f"Extension asset {manifest_path} is missing required fields: "
                + ", ".join(missing)
            )

        invalid = [
            field
            for field in required
            if not isinstance(raw[field], str) or not raw[field].strip()
        ]
        if invalid:
            raise ExtensionError(
                f"Extension asset {manifest_path} fields must be non-empty strings: "
                + ", ".join(invalid)
            )

        extension_id = raw["id"].strip()
        if expected_id is not None and extension_id != expected_id:
            raise ExtensionError(
                f"Extension ID mismatch: registry selected {expected_id!r}, "
                f"but manifest declares {extension_id!r}."
            )

        manifest = ExtensionManifest(
            extension_id=extension_id,
            name=raw["name"].strip(),
            version=raw["version"].strip(),
            target=raw["target"].strip(),
            module=raw["module"].strip(),
            entrypoint=raw["entrypoint"].strip(),
        )

        module = self._load_module(manifest_path.parent, manifest)
        handler = getattr(module, manifest.entrypoint, None)
        if handler is None or not callable(handler):
            raise ExtensionError(
                f"Extension {extension_id!r} entrypoint {manifest.entrypoint!r} "
                "is not a callable."
            )

        return LoadedExtension(manifest=manifest, handler=handler)

    @staticmethod
    def _load_module(directory: Path, manifest: ExtensionManifest) -> ModuleType:
        module_ref = Path(manifest.module)
        if module_ref.suffix == ".py" or module_ref.parent != Path("."):
            directory = directory.resolve()
            module_path = (directory / module_ref).resolve()
            try:
                module_path.relative_to(directory)
            except ValueError as exc:
                raise ExtensionError(
                    "Extension module path must stay inside the extension directory: "
                    f"{manifest.module!r}"
                ) from exc

            if not module_path.is_file():
                raise ExtensionError(f"Extension module not found: {module_path}")
            module_name = "edutex_user_extension_" + manifest.extension_id.replace("-", "_")
            spec = importlib.util.spec_from_file_location(module_name, module_path)
            if spec is None or spec.loader is None:
                raise ExtensionError(f"Cannot load extension module: {module_path}")
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            return module

        try:
            return importlib.import_module(manifest.module)
        except Exception as exc:
            raise ExtensionError(
                f"Cannot import extension module {manifest.module!r}: {exc}"
            ) from exc
