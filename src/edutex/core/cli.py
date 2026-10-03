"""
EduTeX command-line interface.

The CLI is intentionally thin: it loads configuration, assembles the
runtime pipeline, and delegates processing to the existing services.
It does not implement parsing, styling, layout, or LaTeX rendering itself.
"""

from __future__ import annotations

import html
import json
import logging
import shutil
from importlib.resources import as_file, files
from dataclasses import dataclass
from pathlib import Path

import click

from edutex.activator.activator import Activator
from edutex.build.service import BuildService
from edutex.configuration.loader import load_config
from edutex.course.service import CourseBuildError, CourseLesson, CourseManifest, build_course, validate_course
from edutex.core.errors import ConfigurationError, EduTeXError, KnowledgeError
from edutex.core.context import LifecyclePhase, RuntimeContext
from edutex.core.diagnostics import format_diagnostics_text, serialize_diagnostics
from edutex.extension.models import ExtensionDiagnostic
from edutex.extension.loader import ExtensionLoader
from edutex.extension.service import ExtensionService
from edutex.knowledge.authoring import validate_authoring
from edutex.knowledge.service import KnowledgeService
from edutex.knowledge.shortcode_lint import ShortcodeLinter, format_text
from edutex.layout.service import LayoutService
from edutex.registry.models import EntityRecord, EntityType
from edutex.registry.registry import Registry
from edutex.resolver.resolver import Resolver
from edutex.theme.service import ThemeService


CLI_VERSION = "1.0.0"


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
    """Fail early with a typed error when a required asset is missing."""
    if not path.is_file():
        message = f"{description} not found: {path}"
        if description == "Knowledge Model":
            raise KnowledgeError(message)
        raise click.ClickException(message)


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


def _format_build_json(
    report,
    *,
    status: str,
    output_path: Path | None = None,
    message: str | None = None,
    metadata: dict[str, object] | None = None,
) -> str:
    """Serialize one complete build/lint result without mixed terminal text."""
    payload = {
        "lint": report.to_dict() if report is not None else None,
        "build": {"status": status},
    }
    if output_path is not None:
        payload["build"]["output"] = str(output_path)
    if message is not None:
        payload["build"]["message"] = message
    if status == "completed" and metadata is not None:
        payload["build"]["metadata"] = metadata
    return json.dumps(payload, ensure_ascii=False, indent=2)


def _format_build_error_json(
    message: str,
    *,
    error_type: str = "build_error",
    diagnostics: Sequence[ExtensionDiagnostic] | None = None,
) -> str:
    """Serialize one build failure without Click's human-readable prefix."""
    error = {
        "type": error_type,
        "message": message,
    }
    if diagnostics:
        error["diagnostics"] = serialize_diagnostics(diagnostics)

    return json.dumps(
        {
            "lint": None,
            "build": {
                "status": "failed",
                "error": error,
            },
        },
        ensure_ascii=False,
        indent=2,
    )

def _format_validate_json(
    *,
    status: str,
    error_type: str | None = None,
    message: str | None = None,
    diagnostics: Sequence[ExtensionDiagnostic] | None = None,
) -> str:
    """Serialize one validation result without Click's human-readable prefix."""
    validation = {"status": status}
    if error_type is not None:
        error = {
            "type": error_type,
            "message": message or "",
        }
        if diagnostics:
            error["diagnostics"] = serialize_diagnostics(diagnostics)
        validation["error"] = error

    return json.dumps(
        {"validation": validation},
        ensure_ascii=False,
        indent=2,
    )



@dataclass(frozen=True)
class _PreparedPipeline:
    config: object
    state: object
    knowledge: KnowledgeService
    theme: ThemeService
    layout: LayoutService


def _prepare_project_pipeline(
    config_path: Path,
    project_root: Path,
    context: RuntimeContext,
    *,
    config=None,
    profile: str | None = None,
):
    """Prepare the shared runtime pipeline up to the processing phase."""
    if config is None:
        config = load_config(config_path, profile=profile)
    _configure_logging(config.logging.level.value)
    context.advance(LifecyclePhase.CONFIGURING)

    registry = _register_project_assets(config, project_root)
    context.advance(LifecyclePhase.REGISTERING)

    graph = Resolver(registry).resolve()
    context.advance(LifecyclePhase.RESOLVING)

    state = Activator().activate(graph)
    context.advance(LifecyclePhase.ACTIVATING)

    context.advance(LifecyclePhase.PROCESSING)

    knowledge = KnowledgeService()
    knowledge.process(state, project_root)

    theme = ThemeService()
    theme.process(state, knowledge, project_root)

    layout = LayoutService()
    layout.process(state, theme, project_root)

    return _PreparedPipeline(
        config=config,
        state=state,
        knowledge=knowledge,
        theme=theme,
        layout=layout,
    )


def _mark_lifecycle_failed(context: RuntimeContext) -> None:
    """Move a non-terminal runtime context to FAILED."""
    if context.phase not in {
        LifecyclePhase.COMPLETE,
        LifecyclePhase.FAILED,
    }:
        context.advance(LifecyclePhase.FAILED)


def _inspection_asset(path: Path) -> dict[str, object]:
    """Serialize one resolved project asset for inspection."""
    return {
        "path": str(path),
        "exists": path.is_file(),
    }


def _format_inspection_json(payload: dict[str, object]) -> str:
    """Serialize a successful inspection report."""
    return json.dumps(payload, ensure_ascii=False, indent=2)


def _format_inspection_error_json(
    message: str,
    *,
    error_type: str = "inspection_error",
) -> str:
    """Serialize an inspection failure without human-readable prefixes."""
    return json.dumps(
        {
            "inspection": {
                "status": "failed",
                "error": {
                    "type": error_type,
                    "message": message,
                },
            }
        },
        ensure_ascii=False,
        indent=2,
    )


def _inspection_entity(record: EntityRecord) -> dict[str, str]:
    """Serialize one runtime entity using stable public field names."""
    return {
        "id": record.entity_id,
        "type": record.entity_type.name.lower(),
        "source_path": str(record.source_path.resolve()),
    }


def _inspection_edge(edge) -> dict[str, str]:
    """Serialize one resolved graph edge."""
    return {
        "source_id": edge.source_id,
        "source_type": edge.source_type.name.lower(),
        "target_id": edge.target_id,
        "target_type": edge.target_type.name.lower(),
        "reference_type": edge.reference_type,
    }


def _inspect_project(
    config_path: Path,
    project_root: Path,
    profile: str | None = None,
) -> dict[str, object]:
    """Build the deterministic JSON payload for the inspect command."""
    config = load_config(config_path, profile=profile)
    knowledge_path = _resolve_path(project_root, config.knowledge.model)
    theme_path = (
        project_root / "assets" / "themes" / config.theme.name / "theme.yaml"
    )
    layout_path = (
        project_root / "assets" / "layouts" / config.layout.name / "layout.yaml"
    )
    extension_paths = [
        project_root / "assets" / "extensions" / extension_id / "extension.yaml"
        for extension_id in config.extensions.enabled
    ]

    required_assets = (
        ("Knowledge Model", knowledge_path),
        ("Theme asset", theme_path),
        ("Layout asset", layout_path),
    )
    for description, asset_path in required_assets:
        if not asset_path.is_file():
            raise ConfigurationError(f"{description} not found: {asset_path}")
    for extension_id, extension_path in zip(
        config.extensions.enabled,
        extension_paths,
    ):
        if not extension_path.is_file():
            raise ConfigurationError(
                f"Extension asset '{extension_id}' not found: {extension_path}"
            )

    extension_loader = ExtensionLoader()
    extension_details: list[dict[str, object]] = []
    for extension_id, extension_path in zip(
        config.extensions.enabled,
        extension_paths,
    ):
        manifest = extension_loader.read_manifest(
            extension_path,
            expected_id=extension_id,
        )
        module_path = extension_loader.local_module_path(
            extension_path.parent,
            manifest,
        )
        extension_details.append(
            {
                "id": manifest.extension_id,
                "name": manifest.name,
                "version": manifest.version,
                "target": manifest.target,
                "module": manifest.module,
                "entrypoint": manifest.entrypoint,
                "manifest_path": str(extension_path.resolve()),
                "module_path": str(module_path) if module_path is not None else None,
                "module_exists": True if module_path is not None else None,
            }
        )

    registry = _register_project_assets(config, project_root)
    graph = Resolver(registry).resolve()
    registry_entities = [_inspection_entity(record) for record in registry.get_all()]
    graph_entities = [_inspection_entity(record) for record in graph.entities]
    graph_edges = [_inspection_edge(edge) for edge in graph.edges]
    output_dir = _resolve_path(project_root, config.build.output_dir)

    return {
        "inspection": {
            "status": "completed",
            "project_root": str(project_root.resolve()),
            "config_file": str(config_path.resolve()),
            "configuration": {
                "framework_version": config.edutex.version,
                "knowledge_model": config.knowledge.model.as_posix(),
                "theme": config.theme.name,
                "layout": config.layout.name,
                "build": {
                    "output_format": config.build.output_format.value,
                    "output_dir": str(output_dir),
                    "output_file": config.build.output_file,
                },
                "extensions": list(config.extensions.enabled),
                "logging_level": config.logging.level.value,
                **({"profile": profile} if profile is not None else {}),
            },
            "assets": {
                "knowledge_model": _inspection_asset(knowledge_path),
                "theme": _inspection_asset(theme_path),
                "layout": _inspection_asset(layout_path),
                "extensions": [
                    _inspection_asset(extension_path)
                    for extension_path in extension_paths
                ],
            },
            "runtime": {
                "registry": {
                    "entity_count": len(registry_entities),
                    "entities": registry_entities,
                },
                "resolver": {
                    "status": "completed",
                    "entity_count": len(graph_entities),
                    "edge_count": len(graph_edges),
                    "entities": graph_entities,
                    "edges": graph_edges,
                },
                "extensions": extension_details,
            },
        }
    }


def build_project(
    config_path: Path,
    project_root: Path,
    *,
    config=None,
    extension_diagnostics: list[ExtensionDiagnostic] | None = None,
) -> Path:
    """
    Execute the complete EduTeX pipeline for a project.

    This function is separate from Click so it can be tested without a
    subprocess and reused by future frontends. An already-loaded config may
    be supplied by callers that need to perform a preflight first.
    """
    context = RuntimeContext(project_root)

    try:
        pipeline = _prepare_project_pipeline(
            config_path,
            project_root,
            context,
            config=config,
        )

        extensions = ExtensionService()
        try:
            extensions.process(
                pipeline.state,
                pipeline.layout,
                project_root,
                extension_order=pipeline.config.extensions.enabled,
            )

            build = BuildService()
            context.advance(LifecyclePhase.BUILDING)
            build.build(
                pipeline.config,
                pipeline.knowledge,
                pipeline.theme,
                pipeline.layout,
                project_root,
                document=extensions.document,
            )
            output_path = build.output_path
        finally:
            if extension_diagnostics is not None:
                extension_diagnostics.extend(
                    getattr(extensions, "diagnostics", ())
                )
            extensions.terminate()

        context.advance(LifecyclePhase.COMPLETE)
        return output_path
    except Exception:
        _mark_lifecycle_failed(context)
        raise



@click.group(context_settings={"help_option_names": ["-h", "--help"]})
@click.version_option(version=CLI_VERSION, prog_name="edutex")
def main() -> None:
    """EduTeX — generate educational documents from Knowledge Models."""


@main.group("course")
def course_group() -> None:
    """Validate and render a course curriculum manifest."""


@course_group.command("validate")
@click.option("--project", "project_root", type=click.Path(file_okay=False, dir_okay=True, path_type=Path), default=Path("."), show_default=True)
@click.option("--manifest", "manifest_file", type=click.Path(dir_okay=False, path_type=Path), default="course.yaml", show_default=True)
@click.option("--format", "output_format", type=click.Choice(("text", "json"), case_sensitive=False), default="text", show_default=True)
def course_validate_command(project_root: Path, manifest_file: Path, output_format: str) -> None:
    """Validate course.yaml and every linked lesson source."""
    project_root = project_root.resolve()
    manifest_path = manifest_file if manifest_file.is_absolute() else project_root / manifest_file
    report = validate_course(manifest_path, project_root)
    if output_format.lower() == "json":
        click.echo(report.to_json())
    else:
        if report.valid:
            course = report.manifest
            click.echo(f"Course valid: {course.title} ({course.module_count} modules, {course.lesson_count} lessons)")
            for warning in report.warnings:
                click.echo(f"WARNING: {warning}")
        else:
            click.echo("Course invalid:")
            for error in report.errors:
                click.echo(f"ERROR: {error}")
    if not report.valid:
        raise click.exceptions.Exit(1)


def _build_course_lesson(
    manifest: CourseManifest,
    lesson: CourseLesson,
    module_number: int,
    lesson_number: int,
    *,
    project_root: Path,
    profile: str | None = None,
) -> Path:
    """Build one course lesson through the normal EduTeX pipeline."""
    config_path = project_root / "edutex.config.yaml"
    if not config_path.is_file():
        raise click.ClickException(
            f"Lesson build requires project configuration: {config_path}"
        )
    config = load_config(config_path, profile=profile)
    lesson_config = config.model_copy(
        update={
            "knowledge": config.knowledge.model_copy(
                update={"model": Path(lesson.source)}
            ),
            "build": config.build.model_copy(
                update={
                    "output_format": "html",
                    "output_dir": Path("output") / "lessons",
                    "output_file": lesson.lesson_id,
                }
            ),
        }
    )
    output = build_project(config_path, project_root, config=lesson_config)
    _add_course_lesson_navigation(
        output,
        manifest,
        lesson,
        module_number,
        lesson_number,
    )
    return output


def _add_course_lesson_navigation(
    html_path: Path,
    manifest: CourseManifest,
    lesson: CourseLesson,
    module_number: int,
    lesson_number: int,
) -> None:
    """Add course navigation to a generated standalone lesson page."""
    language_code = (
        manifest.language.lower().replace("_", "-").split("-", 1)[0]
    )
    labels = {
        "course_navigation": "Course navigation",
        "course_index": "Course index",
        "module": "Module",
        "lesson_aria": "lesson",
        "lesson": "Lesson",
        "previous": "Previous",
        "next": "Next",
        "mark_complete": "Mark lesson complete",
        "mark_incomplete": "Mark as incomplete",
        "completed": "Completed",
        "skip_to_lesson": "Skip to lesson content",
        "lesson_content": "Lesson content",
    }
    if language_code == "it":
        labels.update(
            {
                "course_navigation": "Navigazione del corso",
                "course_index": "Indice del corso",
                "module": "Modulo",
                "lesson_aria": "lezione",
                "lesson": "Lezione",
                "previous": "Precedente",
                "next": "Successiva",
                "mark_complete": "Segna come completata",
                "mark_incomplete": "Segna come non completata",
                "completed": "Completata",
                "skip_to_lesson": "Vai al contenuto della lezione",
                "lesson_content": "Contenuto della lezione",
            }
        )
    elif language_code == "ja":
        labels.update(
            {
                "course_navigation": "コースナビゲーション",
                "course_index": "コース目次",
                "module": "モジュール",
                "lesson_aria": "レッスン",
                "lesson": "レッスン",
                "previous": "前へ",
                "next": "次へ",
                "mark_complete": "レッスンを完了にする",
                "mark_incomplete": "完了を取り消す",
                "completed": "完了",
                "skip_to_lesson": "レッスン内容へ移動",
                "lesson_content": "レッスン内容",
            }
        )
    lessons = [item for module in manifest.modules for item in module.lessons]
    index = next(i for i, item in enumerate(lessons) if item.lesson_id == lesson.lesson_id)
    previous = lessons[index - 1] if index > 0 else None
    following = lessons[index + 1] if index + 1 < len(lessons) else None
    def link(item: CourseLesson | None, label: str) -> str:
        if item is None:
            return f"<span class=\"course-nav-disabled\" aria-disabled=\"true\">{label}</span>"
        title = html.escape(item.title, quote=True)
        return (
            f"<a href=\"{item.lesson_id}.html\" "
            f"aria-label=\"{label} {labels['lesson_aria']}: {title}\">{label}: {html.escape(item.title)}</a>"
        )
    storage_key = json.dumps(f"edutex:course:{manifest.course_id}:completed")
    lesson_id_json = json.dumps(lesson.lesson_id)
    completion_ui = (
        f"<button type=\"button\" class=\"course-complete\" "
        f"data-course-complete=\"{html.escape(lesson.lesson_id, quote=True)}\" "
        f"aria-label=\"{html.escape(labels['mark_complete'], quote=True)}\" "
        f"aria-pressed=\"false\">"
        f"{html.escape(labels['mark_complete'])}</button>"
        "<span class=\"course-complete-status\" aria-live=\"polite\"></span>"
    )
    if manifest.presentation.show_lesson_navigation:
        nav = (
            f"<nav class=\"course-lesson-nav\" aria-label=\"{html.escape(labels['course_navigation'], quote=True)}\">"
            f"<a href=\"../course.html\" aria-label=\"{html.escape(labels['course_index'], quote=True)}\">{html.escape(labels['course_index'])}</a>"
            f"<span>{html.escape(labels['module'])} {module_number} · {html.escape(labels['lesson'])} {lesson_number}</span>"
            f"{link(previous, labels['previous'])}"
            f"{link(following, labels['next'])}"
            f"{completion_ui}"
            "</nav>"
        )
    else:
        nav = f"<div class=\"course-complete-only\">{completion_ui}</div>"
    source = html_path.read_text(encoding="utf-8")
    style = f"""<style>
.skip-link{{position:absolute;left:1rem;top:-4rem;z-index:10;padding:.55rem .8rem;background:{manifest.presentation.ink};color:#fff;font-weight:800}}
.skip-link:focus-visible{{top:1rem}}
.course-lesson-nav{{display:flex;gap:.8rem;flex-wrap:wrap;align-items:center;margin:0 auto 1.25rem;padding:.8rem 1rem;max-width:980px;background:{manifest.presentation.ink};color:#fff;font:600 .92rem/1.4 Inter,"Segoe UI",Arial,sans-serif}}
.course-lesson-nav a{{color:{manifest.presentation.accent}}}.course-lesson-nav span{{color:#d7e4f5}}.course-nav-disabled{{opacity:.55}}
.course-lesson-nav a:focus-visible,.course-complete:focus-visible{{outline:3px solid {manifest.presentation.accent};outline-offset:3px}}
.course-complete{{border:1px solid {manifest.presentation.accent};border-radius:4px;padding:.35rem .6rem;background:{manifest.presentation.surface};color:{manifest.presentation.ink};font:inherit;cursor:pointer}}
.course-complete-status{{color:{manifest.presentation.accent_secondary}}}
.course-complete-only{{max-width:980px;margin:0 auto 1.25rem;padding:.8rem 1rem;background:{manifest.presentation.surface};color:{manifest.presentation.ink};font:600 .92rem/1.4 Inter,"Segoe UI",Arial,sans-serif}}
</style>"""
    script_labels = json.dumps(
        {
            "mark_complete": labels["mark_complete"],
            "mark_incomplete": labels["mark_incomplete"],
            "completed": labels["completed"],
        },
        ensure_ascii=False,
    )
    script = f"""<script>
(() => {{
  const labels = {script_labels};
  const key = {storage_key};
  const lessonId = {lesson_id_json};
  const button = document.querySelector('[data-course-complete]');
  const status = document.querySelector('.course-complete-status');
  const read = () => {{
    try {{ return new Set(JSON.parse(localStorage.getItem(key) || '[]')); }}
    catch (error) {{ return new Set(); }}
  }};
  const write = (items) => {{
    try {{ localStorage.setItem(key, JSON.stringify([...items])); }} catch (error) {{}}
  }};
  const refresh = () => {{
    const completed = read();
    const isComplete = completed.has(lessonId);
    button.textContent = isComplete ? labels.mark_incomplete : labels.mark_complete;
    button.setAttribute("aria-label", button.textContent);
    button.setAttribute("aria-pressed", String(isComplete));
    if (status) status.textContent = isComplete ? labels.completed : "";
  }};
  if (button) button.addEventListener('click', () => {{
    const completed = read();
    if (completed.has(lessonId)) completed.delete(lessonId); else completed.add(lessonId);
    write(completed); refresh();
  }});
  refresh();
}})();
</script>"""
    source = source.replace("</head>", style + "</head>", 1)
    source = source.replace("<body>", f"<body><a class=\"skip-link\" href=\"#lesson-content\">{html.escape(labels['skip_to_lesson'])}</a>" + nav, 1)
    source = source.replace("<main>", f"<main id=\"lesson-content\" tabindex=\"-1\" aria-label=\"{html.escape(labels['lesson_content'], quote=True)}\">", 1)
    source = source.replace("</body>", script + "</body>", 1)
    html_path.write_text(source, encoding="utf-8")


def _course_build_artifacts(
    project_root: Path,
    manifest_path: Path,
    output_path: Path,
    output_format: str,
) -> list[str]:
    """Return the stable list of public artifacts produced by course build."""
    artifacts = [output_path.resolve()]
    if output_format.lower() == "html":
        report = validate_course(manifest_path, project_root)
        if report.manifest is not None:
            for module in report.manifest.modules:
                for lesson in module.lessons:
                    lesson_path = (
                        project_root / "output" / "lessons" / f"{lesson.lesson_id}.html"
                    ).resolve()
                    if lesson_path.is_file():
                        artifacts.append(lesson_path)
    return list(dict.fromkeys(str(item) for item in artifacts))


def _course_build_report(
    *,
    status: str,
    project_root: Path | None = None,
    manifest_path: Path | None = None,
    output_format: str | None = None,
    output_path: Path | None = None,
    artifacts: list[str] | None = None,
    error_type: str | None = None,
    message: str | None = None,
) -> str:
    """Serialize one course-build report without human-readable prefixes."""
    result: dict[str, object] = {"status": status}
    if status == "completed":
        result.update(
            {
                "project_root": str(project_root.resolve()),
                "manifest": str(manifest_path.resolve()),
                "output_format": output_format,
                "output": str(output_path.resolve()),
                "artifacts": artifacts or [],
            }
        )
    else:
        result["error"] = {
            "type": error_type or "CourseBuildError",
            "message": message or "",
        }
    return json.dumps(
        {"course_build": result},
        ensure_ascii=False,
        indent=2,
    )


@course_group.command("build")
@click.option("--project", "project_root", type=click.Path(file_okay=False, dir_okay=True, path_type=Path), default=Path("."), show_default=True)
@click.option("--manifest", "manifest_file", type=click.Path(dir_okay=False, path_type=Path), default="course.yaml", show_default=True)
@click.option("--format", "output_format", type=click.Choice(("html", "latex", "pdf"), case_sensitive=False), default="html", show_default=True)
@click.option("--output", "output_file", type=click.Path(dir_okay=False, path_type=Path), default=None)
@click.option(
    "--profile",
    type=str,
    default=None,
    help="Configuration profile to apply.",
)
@click.option(
    "--report-format",
    "report_format",
    type=click.Choice(("text", "json"), case_sensitive=False),
    default="text",
    show_default=True,
    help="Report format for terminal or tooling integration.",
)
def course_build_command(
    project_root: Path,
    manifest_file: Path,
    output_format: str,
    output_file: Path | None,
    profile: str | None = None,
    report_format: str = "text",
) -> None:
    """Build a course index or printable roadmap."""
    project_root = project_root.resolve()
    manifest_path = manifest_file if manifest_file.is_absolute() else project_root / manifest_file
    output_format = output_format.lower()
    report_format = report_format.lower()
    try:
        if profile is not None:
            if output_format != "html":
                raise CourseBuildError(
                    "--profile is supported for course build only with --format html."
                )
            try:
                load_config(project_root / "edutex.config.yaml", profile=profile)
            except ConfigurationError as exc:
                raise CourseBuildError(str(exc)) from exc

        lesson_builder = None
        if output_format == "html":
            lesson_builder = lambda manifest, lesson, module_number, lesson_number: _build_course_lesson(
                manifest,
                lesson,
                module_number,
                lesson_number,
                project_root=project_root,
                profile=profile,
            )
        output = build_course(
            manifest_path,
            project_root,
            output_format,
            output_file,
            lesson_builder=lesson_builder,
        )
    except Exception as exc:
        if report_format == "json":
            click.echo(
                _course_build_report(
                    status="failed",
                    error_type=exc.__class__.__name__,
                    message=str(exc),
                )
            )
            raise click.exceptions.Exit(1) from exc
        if isinstance(exc, CourseBuildError):
            raise click.ClickException(str(exc)) from exc
        raise

    if report_format == "json":
        artifacts = _course_build_artifacts(
            project_root,
            manifest_path,
            output,
            output_format,
        )
        click.echo(
            _course_build_report(
                status="completed",
                project_root=project_root,
                manifest_path=manifest_path,
                output_format=output_format,
                output_path=output,
                artifacts=artifacts,
            )
        )
    else:
        click.echo(f"Course build completed: {output}")


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
            for name in ("edutex.config.yaml", "README.md", "course.yaml"):
                template_file = template_path / name
                if template_file.is_file():
                    shutil.copy2(template_file, target / name)
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


@main.group("author")
def author_group() -> None:
    """Validate Knowledge Model authoring before processing."""


@author_group.command("validate")
@click.argument(
    "source_file",
    type=click.Path(exists=False, dir_okay=False, readable=True, path_type=Path),
)
@click.option(
    "--format",
    "output_format",
    type=click.Choice(("text", "json"), case_sensitive=False),
    default="text",
    show_default=True,
    help="Authoring report format for terminal or tooling integration.",
)
def author_validate_command(source_file: Path, output_format: str) -> None:
    """Validate Knowledge Model frontmatter and shortcode authoring."""
    report = validate_authoring(source_file)
    if output_format.lower() == "json":
        click.echo(
            json.dumps(
                {
                    "authoring": {
                        "status": "completed",
                        **report.to_dict(),
                    }
                },
                ensure_ascii=False,
                indent=2,
            )
        )
    else:
        click.echo(report.to_text())
    if not report.valid:
        raise click.exceptions.Exit(1)


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
@click.option(
    "--profile",
    type=str,
    default=None,
    help="Configuration profile to apply.",
)
def build_command(project_root: Path, config_file: Path, run_lint: bool, output_format: str, profile: str | None = None) -> None:
    """Build the configured project and produce the selected output."""
    project_root = project_root.resolve()
    config_path = _resolve_path(project_root, config_file)

    output_format = output_format.lower()
    lint_report = None
    extension_diagnostics: list[ExtensionDiagnostic] = []
    try:
        config = load_config(config_path, profile=profile)
        if run_lint:
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
        output_path = build_project(
            config_path,
            project_root,
            config=config,
            extension_diagnostics=extension_diagnostics,
        )
    except EduTeXError as exc:
        message = str(exc)
        if output_format == "json":
            click.echo(
                _format_build_error_json(
                    message,
                    error_type=exc.__class__.__name__,
                    diagnostics=extension_diagnostics,
                )
            )
            raise click.exceptions.Exit(1) from exc
        if extension_diagnostics:
            message = f"{message}\n{format_diagnostics_text(extension_diagnostics)}"
        raise click.ClickException(message) from exc
    except OSError as exc:
        message = f"File operation failed: {exc}"
        if output_format == "json":
            click.echo(_format_build_error_json(message, error_type="file_error"))
            raise click.exceptions.Exit(1) from exc
        raise click.ClickException(message) from exc

    if output_format == "json":
        click.echo(
            _format_build_json(
                lint_report,
                status="completed",
                output_path=output_path,
                metadata={
                    "project_root": str(project_root),
                    "config_file": str(config_path.resolve()),
                    "output_format": config.build.output_format.value,
                    "output_path": str(output_path),
                    "output_exists": output_path.is_file(),
                },
            )
        )
    else:
        click.echo(f"Build completed: {output_path}")


@main.command("inspect")
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
    "--format",
    "output_format",
    type=click.Choice(("json",), case_sensitive=False),
    default="json",
    show_default=True,
    help="Inspection report format.",
)
@click.option(
    "--profile",
    type=str,
    default=None,
    help="Configuration profile to apply.",
)
def inspect_command(
    project_root: Path,
    config_file: Path,
    output_format: str,
    profile: str | None = None,
) -> None:
    """Inspect resolved configuration and project assets."""
    del output_format

    project_root = project_root.resolve()
    config_path = _resolve_path(project_root, config_file)

    try:
        payload = _inspect_project(config_path, project_root, profile=profile)
    except EduTeXError as exc:
        click.echo(
            _format_inspection_error_json(
                str(exc),
                error_type=exc.__class__.__name__,
            )
        )
        raise click.exceptions.Exit(1) from exc
    except OSError as exc:
        click.echo(
            _format_inspection_error_json(
                f"File operation failed: {exc}",
                error_type="file_error",
            )
        )
        raise click.exceptions.Exit(1) from exc

    click.echo(_format_inspection_json(payload))


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
@click.option(
    "--format",
    "output_format",
    type=click.Choice(["text", "json"], case_sensitive=False),
    default="text",
    show_default=True,
    help="Output format.",
)
@click.option(
    "--profile",
    type=str,
    default=None,
    help="Configuration profile to apply.",
)
def validate_command(
    project_root: Path,
    config_file: Path,
    output_format: str = "text",
    profile: str | None = None,
) -> None:
    """Validate configuration and runtime asset resolution without building."""
    project_root = project_root.resolve()
    config_path = _resolve_path(project_root, config_file)
    context = RuntimeContext(project_root)
    extension_diagnostics: list[ExtensionDiagnostic] = []

    try:
        pipeline = _prepare_project_pipeline(
            config_path,
            project_root,
            context,
            profile=profile,
        )

        extensions = ExtensionService()
        try:
            extensions.process(
                pipeline.state,
                pipeline.layout,
                project_root,
                extension_order=pipeline.config.extensions.enabled,
            )
        finally:
            extension_diagnostics.extend(
                getattr(extensions, "diagnostics", ())
            )
            extensions.terminate()

        context.advance(LifecyclePhase.COMPLETE)
        if output_format == "json":
            click.echo(_format_validate_json(status="completed"))
        else:
            click.echo("Configuration, assets, and processing pipeline are valid.")
    except EduTeXError as exc:
        _mark_lifecycle_failed(context)
        if output_format == "json":
            click.echo(
                _format_validate_json(
                    status="failed",
                    error_type=exc.__class__.__name__,
                    message=str(exc),
                    diagnostics=extension_diagnostics,
                )
            )
            raise click.exceptions.Exit(1) from exc
        message = str(exc)
        if extension_diagnostics:
            message = f"{message}\n{format_diagnostics_text(extension_diagnostics)}"
        raise click.ClickException(message) from exc
    except OSError as exc:
        _mark_lifecycle_failed(context)
        message = f"File operation failed: {exc}"
        if output_format == "json":
            click.echo(
                _format_validate_json(
                    status="failed",
                    error_type=exc.__class__.__name__,
                    message=message,
                    diagnostics=extension_diagnostics,
                )
            )
            raise click.exceptions.Exit(1) from exc
        raise click.ClickException(message) from exc
    except Exception as exc:
        _mark_lifecycle_failed(context)
        if output_format == "json":
            click.echo(
                _format_validate_json(
                    status="failed",
                    error_type=exc.__class__.__name__,
                    message=str(exc),
                    diagnostics=extension_diagnostics,
                )
            )
            raise click.exceptions.Exit(1) from exc
        raise



@main.group("config")
def config_group() -> None:
    """Compare and inspect project configuration."""


@config_group.command("diff")
@click.option(
    "--project",
    "project_root",
    type=click.Path(file_okay=False, dir_okay=True, path_type=Path),
    default=Path("."),
    show_default=True,
    help="Project directory containing the configuration file.",
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
    "--profile",
    required=True,
    type=str,
    help="Profile to compare against the base configuration.",
)
@click.option(
    "--format",
    "output_format",
    type=click.Choice(("text", "json"), case_sensitive=False),
    default="text",
    show_default=True,
    help="Comparison report format.",
)
def config_diff_command(
    project_root: Path,
    config_file: Path,
    profile: str,
    output_format: str,
) -> None:
    """Compare the base configuration with one selected profile."""
    project_root = project_root.expanduser().resolve()
    config_path = _resolve_path(project_root, config_file).expanduser().resolve()
    output_format = output_format.lower()

    try:
        base_config = load_config(config_path)
        profile_config = load_config(config_path, profile=profile)
    except EduTeXError as exc:
        if output_format == "json":
            click.echo(
                json.dumps(
                    {
                        "comparison": {
                            "status": "failed",
                            "error": {
                                "type": exc.__class__.__name__,
                                "message": str(exc),
                            },
                        }
                    },
                    ensure_ascii=False,
                    indent=2,
                )
            )
            raise click.exceptions.Exit(1) from exc
        raise click.ClickException(str(exc)) from exc

    changes = _configuration_diff_rows(base_config, profile_config)
    payload = {
        "comparison": {
            "status": "completed",
            "project_root": str(project_root),
            "config_file": str(config_path),
            "profile": profile,
            "changed": bool(changes),
            "changes": changes,
        }
    }

    if output_format == "json":
        click.echo(json.dumps(payload, ensure_ascii=False, indent=2))
        return

    click.echo(f"Configuration comparison: base -> profile '{profile}'")
    if not changes:
        click.echo("No configuration differences.")
        return

    for change in changes:
        before = json.dumps(change["base_value"], ensure_ascii=False, sort_keys=True)
        after = json.dumps(change["profile_value"], ensure_ascii=False, sort_keys=True)
        click.echo(f"{change['path']}: {before} -> {after}")


def _configuration_diff_rows(base_config, profile_config) -> list[dict[str, object]]:
    """Return a deterministic recursive diff of two validated configurations."""
    base_values = base_config.model_dump(mode="json")
    profile_values = profile_config.model_dump(mode="json")
    changes: list[dict[str, object]] = []
    missing = object()

    def visit(path: str, base_value: object, profile_value: object) -> None:
        if isinstance(base_value, dict) and isinstance(profile_value, dict):
            keys = sorted(set(base_value) | set(profile_value))
            for key in keys:
                child_path = f"{path}.{key}" if path else str(key)
                old = base_value.get(key, missing)
                new = profile_value.get(key, missing)
                if old is missing or new is missing:
                    changes.append(
                        {
                            "path": child_path,
                            "base_value": None if old is missing else old,
                            "profile_value": None if new is missing else new,
                        }
                    )
                else:
                    visit(child_path, old, new)
            return
        if base_value != profile_value:
            changes.append(
                {
                    "path": path,
                    "base_value": base_value,
                    "profile_value": profile_value,
                }
            )

    visit("", base_values, profile_values)
    return changes


if __name__ == "__main__":
    main()
