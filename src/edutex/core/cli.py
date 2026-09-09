"""
EduTeX command-line interface.

The CLI is intentionally thin: it loads configuration, assembles the
runtime pipeline, and delegates processing to the existing services.
It does not implement parsing, styling, layout, or LaTeX rendering itself.
"""

from __future__ import annotations

import json
import logging
import shutil
from importlib.resources import as_file, files
from pathlib import Path

import click

from edutex.activator.activator import Activator
from edutex.build.service import BuildService
from edutex.configuration.loader import load_config
from edutex.core.errors import EduTeXError
from edutex.knowledge.service import KnowledgeService
from edutex.knowledge.shortcode_lint import ShortcodeLinter, format_text
from edutex.extension.service import ExtensionService
from edutex.layout.service import LayoutService
from edutex.registry.models import EntityRecord, EntityType
from edutex.registry.registry import Registry
from edutex.resolver.resolver import Resolver
from edutex.theme.service import ThemeService


CLI_VERSION = "0.3.0"


def _configure_logging(level: str) -> None:
    """Configure framework logging without changing service behaviour."""
    logging.basicConfig(
        level=getattr(logging, level, logging.INFO),
        format="%(levelname)s: %(message)s",
    )


def _resolve_path(project_root: Path, configured_path: Path) -> Path:
    """Resolve a configuration path relative to the project root."""
    if configured_path.is_absolute():
        return configured_path
    return project_root / configured_path


def _require_file(path: Path, description: str) -> None:
    """Fail early with a user-facing error when an asset is missing."""
    if not path.is_file():
        raise click.ClickException(f"{description} not found: {path}")


def _register_project_assets(config, project_root: Path) -> Registry:
    """Create the registry from the assets selected in project configuration."""
    registry = Registry()

    knowledge_path = _resolve_path(project_root, config.knowledge.model)
    theme_path = project_root / "assets" / "themes" / config.theme.name / "theme.yaml"
    layout_path = project_root / "assets" / "layouts" / config.layout.name / "layout.yaml"

    _require_file(knowledge_path, "Knowledge Model")
    _require_file(theme_path, "Theme asset")
    _require_file(layout_path, "Layout asset")

    registry.register(EntityRecord(
        entity_id=knowledge_path.stem,
        entity_type=EntityType.KNOWLEDGE_MODEL,
        source_path=knowledge_path,
    ))
    registry.register(EntityRecord(
        entity_id=config.theme.name,
        entity_type=EntityType.THEME,
        source_path=theme_path,
    ))
    registry.register(EntityRecord(
        entity_id=config.layout.name,
        entity_type=EntityType.LAYOUT,
        source_path=layout_path,
    ))

    for extension_id in config.extensions.enabled:
        extension_path = (
            project_root / "assets" / "extensions" / extension_id / "extension.yaml"
        )
        _require_file(extension_path, f"Extension asset '{extension_id}'")
        registry.register(EntityRecord(
            entity_id=extension_id,
            entity_type=EntityType.EXTENSION,
            source_path=extension_path,
        ))

    registry.close_registration_window()
    return registry


def _run_lint_preflight(config, project_root: Path, *, output_format: str = "text"):
    """Lint the configured Knowledge Model before an opt-in build."""
    source_path = _resolve_path(project_root, config.knowledge.model)
    _require_file(source_path, "Knowledge Model")
    try:
        report = ShortcodeLinter().lint_file(source_path)
    except (OSError, UnicodeError) as exc:
        raise click.ClickException(f"Could not read source file: {exc}") from exc

    if output_format == "text":
        click.echo(format_text(report))
    return report


def _format_build_json(report, *, status: str, output_path: Path | None = None, message: str | None = None) -> str:
    """Serialize one complete build/lint result without mixed terminal text."""
    payload = {
        "lint": report.to_dict() if report is not None else None,
        "build": {"status": status},
    }
    if output_path is not None:
        payload["build"]["output"] = str(output_path)
    if message is not None:
        payload["build"]["message"] = message
    return json.dumps(payload, ensure_ascii=False, indent=2)


def build_project(
    config_path: Path,
    project_root: Path,
    *,
    config=None,
) -> Path:
    """
    Execute the complete EduTeX pipeline for a project.

    This function is separate from Click so it can be tested without a
    subprocess and reused by future frontends. An already-loaded config may
    be supplied by callers that need to perform a preflight first.
    """
    if config is None:
        config = load_config(config_path)
    _configure_logging(config.logging.level.value)

    registry = _register_project_assets(config, project_root)
    graph = Resolver(registry).resolve()
    activator = Activator()
    state = activator.activate(graph)

    knowledge = KnowledgeService()
    knowledge.process(state, project_root)

    theme = ThemeService()
    theme.process(state, knowledge, project_root)

    layout = LayoutService()
    layout.process(state, theme, project_root)

    extensions = ExtensionService()
    extensions.process(state, layout, project_root)

    build = BuildService()
    build.build(
        config,
        knowledge,
        theme,
        layout,
        project_root,
        document=extensions.document,
    )
    return build.output_path


@click.group(context_settings={"help_option_names": ["-h", "--help"]})
@click.version_option(version=CLI_VERSION, prog_name="edutex")
def main() -> None:
    """EduTeX — generate educational documents from Knowledge Models."""


@main.command("init")
@click.argument(
    "project_dir",
    type=click.Path(file_okay=False, path_type=Path),
    default=Path("edutex-project"),
    required=False,
)
@click.option(
    "--theme",
    type=click.Choice(["default", "dark"], case_sensitive=False),
    default="dark",
    show_default=True,
    help="Theme for the generated project.",
)
@click.option(
    "--language",
    type=click.Choice(["en", "it", "ja"], case_sensitive=False),
    default="it",
    show_default=True,
    help="Language stored in the starter knowledge model.",
)
@click.option(
    "--force",
    is_flag=True,
    help="Overwrite the generated starter files in an existing directory.",
)
def init_command(project_dir: Path, theme: str, language: str, force: bool) -> None:
    """Create a ready-to-build EduTeX project."""
    target = project_dir.expanduser().resolve()
    if target.exists() and not target.is_dir():
        raise click.ClickException(f"Project path is not a directory: {target}")

    if target.exists() and any(target.iterdir()) and not force:
        raise click.ClickException(
            f"Project directory is not empty: {target}. "
            "Choose an empty directory or pass --force."
        )

    target.mkdir(parents=True, exist_ok=True)
    try:
        template = files("edutex.project_template")
        with as_file(template) as template_path:
            for name in ("edutex.config.yaml", "README.md"):
                shutil.copy2(template_path / name, target / name)
            shutil.copytree(
                template_path / "assets",
                target / "assets",
                dirs_exist_ok=True,
            )
            config_path = target / "edutex.config.yaml"
            config_text = config_path.read_text(encoding="utf-8")
            config_path.write_text(
                config_text.replace('name: "dark"', f'name: "{theme.lower()}"', 1),
                encoding="utf-8",
            )
            model_path = target / "assets" / "knowledge_models" / "example.md"
            if language.lower() == "ja":
                japanese_template = (
                    template_path / "assets" / "knowledge_models" / "example-ja.md"
                )
                if japanese_template.is_file():
                    shutil.copy2(japanese_template, model_path)
            else:
                model_text = model_path.read_text(encoding="utf-8")
                model_path.write_text(
                    model_text.replace("language: it", f"language: {language.lower()}", 1),
                    encoding="utf-8",
                )
    except OSError as exc:
        raise click.ClickException(f"Could not create project: {exc}") from exc

    click.echo(f"EduTeX project created: {target}")
    click.echo("Next steps:")
    click.echo(f"  edutex validate --project {target}")
    click.echo(f"  edutex build --project {target}")


@main.command("lint")
@click.argument(
    "source_file",
    type=click.Path(exists=True, dir_okay=False, readable=True, path_type=Path),
)
@click.option(
    "--format",
    "output_format",
    type=click.Choice(("text", "json"), case_sensitive=False),
    default="text",
    show_default=True,
    help="Report format for terminal or tooling integration.",
)
def lint_command(source_file: Path, output_format: str) -> None:
    """Lint one Knowledge Model source file without building it."""
    try:
        report = ShortcodeLinter().lint_file(source_file)
    except (OSError, UnicodeError) as exc:
        raise click.ClickException(f"Could not read source file: {exc}") from exc

    if output_format.lower() == "json":
        click.echo(report.to_json())
    else:
        click.echo(format_text(report))

    if not report.valid:
        raise click.exceptions.Exit(1)


@main.command("build")
@click.option(
    "--project",
    "project_root",
    type=click.Path(file_okay=False, dir_okay=True, path_type=Path),
    default=Path("."),
    show_default=True,
    help="Project directory containing edutex.config.yaml and assets.",
)
@click.option(
    "--config",
    "config_file",
    type=click.Path(dir_okay=False, path_type=Path),
    default="edutex.config.yaml",
    show_default=True,
    help="Configuration file, relative to the project directory unless absolute.",
)
@click.option(
    "--lint",
    "run_lint",
    is_flag=True,
    help="Run shortcode linting before the build.",
)
@click.option(
    "--format",
    "output_format",
    type=click.Choice(("text", "json"), case_sensitive=False),
    default="text",
    show_default=True,
    help="Output format for the build result and optional lint report.",
)
def build_command(project_root: Path, config_file: Path, run_lint: bool, output_format: str) -> None:
    """Build the configured project and produce the selected output."""
    project_root = project_root.resolve()
    config_path = _resolve_path(project_root, config_file)

    output_format = output_format.lower()
    lint_report = None
    try:
        config = None
        if run_lint:
            config = load_config(config_path)
            lint_report = _run_lint_preflight(
                config,
                project_root,
                output_format=output_format,
            )
            if not lint_report.valid:
                message = "Build blocked: shortcode lint found errors."
                if output_format == "json":
                    click.echo(_format_build_json(lint_report, status="blocked", message=message))
                else:
                    click.echo(message)
                raise click.exceptions.Exit(1)
        output_path = build_project(config_path, project_root, config=config)
    except EduTeXError as exc:
        raise click.ClickException(str(exc)) from exc
    except OSError as exc:
        raise click.ClickException(f"File operation failed: {exc}") from exc

    if output_format == "json":
        click.echo(
            _format_build_json(
                lint_report,
                status="completed",
                output_path=output_path,
            )
        )
    else:
        click.echo(f"Build completed: {output_path}")


@main.command("validate")
@click.option(
    "--project",
    "project_root",
    type=click.Path(file_okay=False, dir_okay=True, path_type=Path),
    default=Path("."),
    show_default=True,
    help="Project directory containing edutex.config.yaml and assets.",
)
@click.option(
    "--config",
    "config_file",
    type=click.Path(dir_okay=False, path_type=Path),
    default="edutex.config.yaml",
    show_default=True,
    help="Configuration file, relative to the project directory unless absolute.",
)
def validate_command(project_root: Path, config_file: Path) -> None:
    """Validate configuration and runtime asset resolution without building."""
    project_root = project_root.resolve()
    config_path = _resolve_path(project_root, config_file)

    try:
        config = load_config(config_path)
        registry = _register_project_assets(config, project_root)
        graph = Resolver(registry).resolve()
        state = Activator().activate(graph)

        knowledge = KnowledgeService()
        knowledge.process(state, project_root)
        theme = ThemeService()
        theme.process(state, knowledge, project_root)
        layout = LayoutService()
        layout.process(state, theme, project_root)
        extensions = ExtensionService()
        extensions.process(state, layout, project_root)
    except EduTeXError as exc:
        raise click.ClickException(str(exc)) from exc
    except OSError as exc:
        raise click.ClickException(f"File operation failed: {exc}") from exc

    click.echo("Configuration, assets, and processing pipeline are valid.")


if __name__ == "__main__":
    main()
