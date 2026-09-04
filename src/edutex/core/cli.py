"""
EduTeX command-line interface.

The CLI is intentionally thin: it loads configuration, assembles the
runtime pipeline, and delegates processing to the existing services.
It does not implement parsing, styling, layout, or LaTeX rendering itself.
"""

from __future__ import annotations

import logging
from pathlib import Path

import click

from edutex.activator.activator import Activator
from edutex.build.service import BuildService
from edutex.configuration.loader import load_config
from edutex.core.errors import EduTeXError
from edutex.knowledge.service import KnowledgeService
from edutex.extension.service import ExtensionService
from edutex.layout.service import LayoutService
from edutex.registry.models import EntityRecord, EntityType
from edutex.registry.registry import Registry
from edutex.resolver.resolver import Resolver
from edutex.theme.service import ThemeService


CLI_VERSION = "0.1.0"


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
    theme_dir = project_root / "assets" / "themes" / config.theme.name
    layout_dir = project_root / "assets" / "layouts" / config.layout.name
    theme_path = theme_dir / "theme.yaml"
    layout_path = layout_dir / "layout.yaml"

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
        source_path=theme_dir,
    ))
    registry.register(EntityRecord(
        entity_id=config.layout.name,
        entity_type=EntityType.LAYOUT,
        source_path=layout_dir,
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


def build_project(config_path: Path, project_root: Path) -> Path:
    """
    Execute the complete EduTeX pipeline for a project.

    This function is separate from Click so it can be tested without a
    subprocess and reused by future frontends.
    """
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
def build_command(project_root: Path, config_file: Path) -> None:
    """Build the configured project and produce the selected output."""
    project_root = project_root.resolve()
    config_path = _resolve_path(project_root, config_file)

    try:
        output_path = build_project(config_path, project_root)
    except EduTeXError as exc:
        raise click.ClickException(str(exc)) from exc
    except OSError as exc:
        raise click.ClickException(f"File operation failed: {exc}") from exc

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
