"""Offline packaging and installed-wheel smoke test for EduTeX."""

from __future__ import annotations

import os
import subprocess
import sys
import tarfile
import tempfile
import tomllib
import zipfile
from pathlib import Path
from typing import Sequence


class ReleaseSmokeError(RuntimeError):
    """Raised when the release smoke test fails."""


def _argv(command: Sequence[object]) -> list[str]:
    return [str(value) for value in command]


def run(
    command: Sequence[object],
    *,
    cwd: Path,
    env: dict[str, str] | None = None,
) -> None:
    result = subprocess.run(
        _argv(command),
        cwd=cwd,
        env=env,
        check=False,
    )

    if result.returncode != 0:
        raise ReleaseSmokeError(
            f"Command failed with exit code {result.returncode}: "
            f"{' '.join(_argv(command))}"
        )


def capture(
    command: Sequence[object],
    *,
    cwd: Path,
    env: dict[str, str] | None = None,
) -> str:
    result = subprocess.run(
        _argv(command),
        cwd=cwd,
        env=env,
        check=False,
        capture_output=True,
        text=True,
        encoding="utf-8",
    )

    if result.returncode != 0:
        detail = (result.stdout + "\n" + result.stderr).strip()
        raise ReleaseSmokeError(
            f"Command failed with exit code {result.returncode}: "
            f"{' '.join(_argv(command))}\n{detail}"
        )

    return result.stdout


def load_project_metadata(root: Path) -> tuple[str, str]:
    with (root / "pyproject.toml").open("rb") as stream:
        document = tomllib.load(stream)

    project = document.get("project", {})
    name = str(project.get("name", "")).strip()
    version = str(project.get("version", "")).strip()

    if not name or not version:
        raise ReleaseSmokeError(
            "pyproject.toml does not contain project name and version."
        )

    return name, version


def find_single(directory: Path, pattern: str) -> Path:
    matches = sorted(directory.glob(pattern))

    if len(matches) != 1:
        names = ", ".join(item.name for item in matches)
        raise ReleaseSmokeError(
            f"Expected exactly one artifact matching {pattern!r}; "
            f"found {len(matches)}: {names}"
        )

    return matches[0]


def verify_wheel(path: Path, version: str) -> None:
    required_members = (
        "edutex/core/cli.py",
        "edutex/build/html_renderer.py",
        "edutex/project_template/edutex.config.yaml",
        "edutex/project_template/assets/themes/default/theme.yaml",
    )

    with zipfile.ZipFile(path) as archive:
        members = set(archive.namelist())

        for member in required_members:
            if member not in members:
                raise ReleaseSmokeError(
                    f"Missing wheel member: {member}"
                )

        metadata_name = next(
            (
                name
                for name in members
                if name.endswith(".dist-info/METADATA")
            ),
            None,
        )

        if metadata_name is None:
            raise ReleaseSmokeError("Wheel metadata file is missing.")

        metadata = archive.read(metadata_name).decode("utf-8")

    if f"Version: {version}" not in metadata:
        raise ReleaseSmokeError(
            f"Wheel metadata does not contain Version: {version}."
        )


def verify_sdist(path: Path) -> None:
    required_suffixes = (
        "/pyproject.toml",
        "/src/edutex/core/cli.py",
        "/src/edutex/build/html_renderer.py",
        "/src/edutex/project_template/edutex.config.yaml",
        "/src/edutex/project_template/assets/themes/default/theme.yaml",
    )

    with tarfile.open(path, "r:gz") as archive:
        members = {
            name.replace("\\", "/")
            for name in archive.getnames()
        }

    for suffix in required_suffixes:
        if not any(name.endswith(suffix) for name in members):
            raise ReleaseSmokeError(
                f"Missing sdist member with suffix: {suffix}"
            )


def main() -> int:
    root = Path(__file__).resolve().parents[1]
    name, version = load_project_metadata(root)
    distribution = name.replace("-", "_")

    egg_info = root / "src" / "edutex.egg-info"
    had_egg_info = egg_info.exists()

    with tempfile.TemporaryDirectory(
        prefix=f"{distribution}-release-smoke-"
    ) as temporary:
        workspace = Path(temporary)
        artifacts = workspace / "artifacts"
        install_dir = workspace / "install"
        project_dir = workspace / "initialized-project"

        artifacts.mkdir()
        install_dir.mkdir()

        try:
            run(
                (
                    sys.executable,
                    "-m",
                    "pip",
                    "wheel",
                    "--no-index",
                    "--no-deps",
                    "--no-build-isolation",
                    "--wheel-dir",
                    artifacts,
                    root,
                ),
                cwd=root,
            )

            sdist_environment = os.environ.copy()
            sdist_environment["EDUTEX_SDIST_DIR"] = str(artifacts)

            sdist_code = (
                "import os\n"
                "from setuptools.build_meta import build_sdist\n"
                "print(build_sdist(os.environ['EDUTEX_SDIST_DIR']))\n"
            )

            run(
                (
                    sys.executable,
                    "-c",
                    sdist_code,
                ),
                cwd=root,
                env=sdist_environment,
            )

            wheel = find_single(
                artifacts,
                f"{distribution}-{version}-*.whl",
            )
            sdist = find_single(
                artifacts,
                f"{distribution}-{version}.tar.gz",
            )

            verify_wheel(wheel, version)
            verify_sdist(sdist)

            run(
                (
                    sys.executable,
                    "-m",
                    "pip",
                    "install",
                    "--no-index",
                    "--no-deps",
                    "--target",
                    install_dir,
                    wheel,
                ),
                cwd=root,
            )

            runtime_environment = os.environ.copy()
            runtime_environment["PYTHONPATH"] = str(install_dir)

            loaded_path = capture(
                (
                    sys.executable,
                    "-c",
                    "import edutex; print(edutex.__file__)",
                ),
                cwd=root,
                env=runtime_environment,
            ).strip().splitlines()[-1]

            resolved_loaded = Path(loaded_path).resolve()
            resolved_install = install_dir.resolve()

            if resolved_install not in resolved_loaded.parents:
                raise ReleaseSmokeError(
                    "The CLI did not load edutex from the installed wheel: "
                    f"{resolved_loaded}"
                )

            run(
                (
                    sys.executable,
                    "-m",
                    "edutex",
                    "--version",
                ),
                cwd=root,
                env=runtime_environment,
            )

            run(
                (
                    sys.executable,
                    "-m",
                    "edutex",
                    "--help",
                ),
                cwd=root,
                env=runtime_environment,
            )

            run(
                (
                    sys.executable,
                    "-m",
                    "edutex",
                    "init",
                    project_dir,
                    "--theme",
                    "default",
                    "--language",
                    "it",
                ),
                cwd=root,
                env=runtime_environment,
            )

            config_path = project_dir / "edutex.config.yaml"
            required_project_files = (
                config_path,
                project_dir / "README.md",
                project_dir / "course.yaml",
                project_dir / "assets" / "knowledge_models" / "example.md",
            )

            for required_file in required_project_files:
                if not required_file.is_file():
                    raise ReleaseSmokeError(
                        f"Initialized project is missing: {required_file}"
                    )

            config_text = config_path.read_text(encoding="utf-8")

            if 'output_format: "pdf"' in config_text:
                config_path.write_text(
                    config_text.replace(
                        'output_format: "pdf"',
                        'output_format: "html"',
                        1,
                    ),
                    encoding="utf-8",
                )

            run(
                (
                    sys.executable,
                    "-m",
                    "edutex",
                    "validate",
                    "--project",
                    project_dir,
                    "--config",
                    config_path,
                ),
                cwd=root,
                env=runtime_environment,
            )

            run(
                (
                    sys.executable,
                    "-m",
                    "edutex",
                    "build",
                    "--project",
                    project_dir,
                    "--config",
                    config_path,
                ),
                cwd=root,
                env=runtime_environment,
            )

            output_dir = project_dir / "output"

            if not output_dir.is_dir() or not any(output_dir.iterdir()):
                raise ReleaseSmokeError(
                    "Installed-wheel build produced no output artifact."
                )

        finally:
            if not had_egg_info and egg_info.exists():
                for child in sorted(
                    egg_info.rglob("*"),
                    reverse=True,
                ):
                    if child.is_file() or child.is_symlink():
                        child.unlink()
                    elif child.is_dir():
                        child.rmdir()
                egg_info.rmdir()

    print(
        f"Release smoke passed for {name} {version}: "
        "wheel, sdist, installed CLI, init, validate, and build."
    )
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except ReleaseSmokeError as error:
        print(f"RELEASE SMOKE FAILED: {error}", file=sys.stderr)
        raise SystemExit(1)
