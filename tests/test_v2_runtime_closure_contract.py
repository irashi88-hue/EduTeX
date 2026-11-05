"""End-to-end V2 runtime closure for configuration-selected operations."""

from __future__ import annotations

import json
from pathlib import Path

import yaml
from click.testing import CliRunner

from edutex.core.cli import _extension_processing_order, main
from edutex.registry.models import EntityRecord, EntityReference, EntityType
from edutex.registry.registry import Registry
from edutex.resolver.resolver import Resolver


def _project(tmp_path: Path) -> Path:
    project = tmp_path / "project"
    result = CliRunner().invoke(main, ["init", str(project), "--theme", "default"])
    assert result.exit_code == 0, result.output
    return project


def _set_runtime(project: Path, runtime: dict) -> None:
    path = project / "edutex.config.yaml"
    config = yaml.safe_load(path.read_text(encoding="utf-8"))
    config["runtime"] = runtime
    path.write_text(yaml.safe_dump(config, sort_keys=False), encoding="utf-8")


def _identity(kind: str, name: str) -> dict[str, str]:
    return {"type": kind, "id": name}


def _reference(source_type: str, source_id: str, target_type: str, target_id: str,
               *, optional: bool = False) -> dict:
    return {
        "source": _identity(source_type, source_id),
        "target": _identity(target_type, target_id),
        "optional": optional,
    }


def test_required_closure_optional_exclusion_and_selected_services(tmp_path: Path) -> None:
    project = _project(tmp_path)
    assets = project / "assets" / "runtime"
    assets.mkdir(parents=True)
    for name in ("aaa-km.md", "aaa-theme.yaml", "aaa-layout.yaml",
                 "first.txt", "second.txt", "unused.txt"):
        (assets / name).write_text("not a valid rendered asset", encoding="utf-8")
    _set_runtime(project, {
        "assets": [
            {"type": "knowledge_model", "id": "aaa-km", "path": "assets/runtime/aaa-km.md"},
            {"type": "theme", "id": "aaa-theme", "path": "assets/runtime/aaa-theme.yaml"},
            {"type": "layout", "id": "aaa-layout", "path": "assets/runtime/aaa-layout.yaml"},
            {"type": "component", "id": "first", "path": "assets/runtime/first.txt"},
            {"type": "component", "id": "second", "path": "assets/runtime/second.txt"},
            {"type": "component", "id": "unused", "path": "assets/runtime/unused.txt"},
        ],
        "references": [
            _reference("knowledge_model", "example", "knowledge_model", "aaa-km"),
            _reference("knowledge_model", "example", "theme", "aaa-theme"),
            _reference("knowledge_model", "example", "layout", "aaa-layout"),
            _reference("knowledge_model", "example", "component", "first"),
            _reference("component", "first", "component", "second"),
            _reference("component", "second", "component", "unused", optional=True),
        ],
    })
    inspect = CliRunner().invoke(main, ["inspect", "--project", str(project)])
    assert inspect.exit_code == 0, inspect.output
    runtime = json.loads(inspect.output)["inspection"]["runtime"]
    identities = {(item["type"], item["id"]) for item in runtime["resolver"]["entities"]}
    assert ("component", "first") in identities
    assert ("component", "second") in identities
    assert ("component", "unused") not in identities
    assert ("knowledge_model", "aaa-km") in identities
    assert ("theme", "aaa-theme") in identities
    assert ("layout", "aaa-layout") in identities
    assert runtime["resolver"]["edge_count"] == 5

    # The dependency assets are intentionally invalid as primary KM/theme/layout.
    # A successful build/validation proves processing used the selected assets.
    for command in ("validate", "build"):
        result = CliRunner().invoke(main, [command, "--project", str(project)])
        assert result.exit_code == 0, result.output


def test_required_missing_target_keeps_structured_diagnostic(tmp_path: Path) -> None:
    project = _project(tmp_path)
    _set_runtime(project, {
        "references": [_reference("knowledge_model", "example", "component", "missing")]
    })
    result = CliRunner().invoke(main, ["inspect", "--project", str(project)])
    assert result.exit_code != 0
    error = json.loads(result.output)["inspection"]["error"]
    assert error["code"] == "RUNTIME_REFERENCE_MISSING"
    assert error["details"]["missing_references"][0]["expected_target"] == {
        "type": "component", "id": "missing"
    }


def test_optional_target_in_scope_keeps_edge(tmp_path: Path) -> None:
    project = _project(tmp_path)
    _set_runtime(project, {"references": [
        _reference("knowledge_model", "example", "layout", "default", optional=True)
    ]})
    result = CliRunner().invoke(main, ["inspect", "--project", str(project)])
    assert result.exit_code == 0, result.output
    edges = json.loads(result.output)["inspection"]["runtime"]["resolver"]["edges"]
    assert len(edges) == 1 and edges[0]["target_type"] == "layout"


def test_extension_processing_obeys_dependency_before_configured_order() -> None:
    registry = Registry()
    registry.register(EntityRecord("dependent", EntityType.EXTENSION, Path("dependent.yaml"),
        references=[EntityReference("requires", "dependency", EntityType.EXTENSION)]))
    registry.register(EntityRecord("dependency", EntityType.EXTENSION, Path("dependency.yaml")))
    registry.close_registration_window()
    graph = Resolver(registry).resolve()
    assert _extension_processing_order(graph, ("dependent", "dependency")) == (
        "dependency", "dependent"
    )


def test_preview_closure_uses_preview_source_not_configured_source(tmp_path: Path) -> None:
    project = _project(tmp_path)
    configured = project / "assets/knowledge_models/example.md"
    preview_source = configured.with_name("preview-only.md")
    preview_source.write_text(configured.read_text(encoding="utf-8"), encoding="utf-8")
    component = project / "assets/knowledge_models/preview-support.txt"
    component.write_text("support", encoding="utf-8")
    _set_runtime(project, {
        "assets": [
            {"type": "knowledge_model", "id": "preview-only",
             "path": "assets/knowledge_models/preview-only.md"},
            {"type": "component", "id": "preview-support",
             "path": "assets/knowledge_models/preview-support.txt"},
        ],
        "references": [
            _reference("knowledge_model", "preview-only", "component", "preview-support")
        ],
    })
    import edutex.core.cli as cli_module
    real_activate = cli_module.Activator.activate
    captured = []

    def capture(self, graph):
        captured.append({(e.entity_type.name.lower(), e.entity_id) for e in graph.entities})
        return real_activate(self, graph)

    from pytest import MonkeyPatch
    with MonkeyPatch.context() as patch:
        patch.setattr(cli_module.Activator, "activate", capture)
        result = CliRunner().invoke(main, ["preview", str(preview_source),
                                           "--project", str(project)])
    assert result.exit_code == 0, result.output
    assert len(captured) == 1
    assert ("knowledge_model", "preview-only") in captured[0]
    assert ("component", "preview-support") in captured[0]
    assert ("knowledge_model", "example") not in captured[0]


def test_course_build_closure_is_per_lesson(tmp_path: Path) -> None:
    project = _project(tmp_path)
    (project / "lessons").mkdir(exist_ok=True)
    for name in ("hello", "goodbye"):
        (project / "lessons" / f"{name}.md").write_text(
            f"---\nid: {name}\ntitle: {name.title()}\nlanguage: en\n"
            "level: A1\nversion: 1.0.0\nauthor: Tester\n---\n"
            f"# {name.title()}\n\nA lesson.\n",
            encoding="utf-8",
        )
        (project / "lessons" / f"{name}-support.txt").write_text(
            "support", encoding="utf-8"
        )
    (project / "course.yaml").write_text(
        "id: v2-course\n"
        "title: V2 Course\n"
        "language: en\n"
        "level: A1\n"
        "version: 1.0.0\n"
        "author: Tester\n"
        "description: Runtime closure test\n"
        "modules:\n"
        "  - id: module-01\n"
        "    title: Lessons\n"
        "    lessons:\n"
        "      - id: lesson-01\n"
        "        title: Hello\n"
        "        source: lessons/hello.md\n"
        "        duration_minutes: 10\n"
        "        objectives: [Say hello]\n"
        "      - id: lesson-02\n"
        "        title: Goodbye\n"
        "        source: lessons/goodbye.md\n"
        "        duration_minutes: 10\n"
        "        objectives: [Say goodbye]\n", encoding="utf-8"
    )
    _set_runtime(project, {
        "assets": [
            *({"type": "knowledge_model", "id": name,
               "path": f"lessons/{name}.md"} for name in ("hello", "goodbye")),
            *({"type": "component", "id": f"{name}-support",
               "path": f"lessons/{name}-support.txt"} for name in ("hello", "goodbye")),
        ],
        "references": [
            _reference("knowledge_model", name, "component", f"{name}-support")
            for name in ("hello", "goodbye")
        ],
    })
    import edutex.core.cli as cli_module
    real_activate = cli_module.Activator.activate
    captured = []

    def capture(self, graph):
        captured.append({(e.entity_type.name.lower(), e.entity_id) for e in graph.entities})
        return real_activate(self, graph)

    from pytest import MonkeyPatch
    with MonkeyPatch.context() as patch:
        patch.setattr(cli_module.Activator, "activate", capture)
        result = CliRunner().invoke(main, ["course", "build", "--project", str(project),
                                           "--format", "html"])
    assert result.exit_code == 0, result.output
    assert len(captured) == 2
    assert ("knowledge_model", "example") not in captured[0] | captured[1]
    for name, scope in zip(("hello", "goodbye"), captured):
        other = "goodbye" if name == "hello" else "hello"
        assert ("knowledge_model", name) in scope
        assert ("component", f"{name}-support") in scope
        assert ("knowledge_model", other) not in scope
        assert ("component", f"{other}-support") not in scope
