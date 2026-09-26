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
from pathlib import Path

import click

from edutex.activator.activator import Activator
from edutex.build.service import BuildService
from edutex.configuration.loader import load_config
from edutex.course.service import CourseBuildError, CourseLesson, CourseManifest, build_course, validate_course
from edutex.core.errors import EduTeXError, KnowledgeError
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


def _format_build_error_json(message: str, *, error_type: str = "build_error") -> str:
    """Serialize one build failure without Click's human-readable prefix."""
    return json.dumps(
        {
            "lint": None,
            "build": {
                "status": "failed",
                "error": {
                    "type": error_type,
                    "message": message,
                },
            },
        },
        ensure_ascii=False,
        indent=2,
    )


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
    try:
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
    finally:
        extensions.terminate()


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
) -> Path:
    """Build one course lesson through the normal EduTeX pipeline."""
    config_path = project_root / "edutex.config.yaml"
    if not config_path.is_file():
        raise click.ClickException(
            f"Lesson build requires project configuration: {config_path}"
        )
    config = load_config(config_path)
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


@course_group.command("build")
@click.option("--project", "project_root", type=click.Path(file_okay=False, dir_okay=True, path_type=Path), default=Path("."), show_default=True)
@click.option("--manifest", "manifest_file", type=click.Path(dir_okay=False, path_type=Path), default="course.yaml", show_default=True)
@click.option("--format", "output_format", type=click.Choice(("html", "latex", "pdf"), case_sensitive=False), default="html", show_default=True)
@click.option("--output", "output_file", type=click.Path(dir_okay=False, path_type=Path), default=None)
def course_build_command(project_root: Path, manifest_file: Path, output_format: str, output_file: Path | None) -> None:
    """Build a course index or printable roadmap."""
    project_root = project_root.resolve()
    manifest_path = manifest_file if manifest_file.is_absolute() else project_root / manifest_file
    try:
        lesson_builder = None
        if output_format.lower() == "html":
            lesson_builder = lambda manifest, lesson, module_number, lesson_number: _build_course_lesson(
                manifest,
                lesson,
                module_number,
                lesson_number,
                project_root=project_root,
            )
        output = build_course(
            manifest_path,
            project_root,
            output_format,
            output_file,
            lesson_builder=lesson_builder,
        )
    except CourseBuildError as exc:
        raise click.ClickException(str(exc)) from exc
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
        message = str(exc)
        if output_format == "json":
            click.echo(_format_build_error_json(message, error_type=exc.__class__.__name__))
            raise click.exceptions.Exit(1) from exc
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
        try:
            extensions.process(state, layout, project_root)
        finally:
            extensions.terminate()
    except EduTeXError as exc:
        raise click.ClickException(str(exc)) from exc
    except OSError as exc:
        raise click.ClickException(f"File operation failed: {exc}") from exc

    click.echo("Configuration, assets, and processing pipeline are valid.")


if __name__ == "__main__":
    main()
