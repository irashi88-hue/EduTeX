from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace

import pytest

from edutex.build.hooks import (
    BuildHook,
    BuildHookContext,
    BuildHookError,
    BuildHookPhase,
    BuildHookRegistry,
    run_build_hooks,
)
from edutex.build.service import BuildService


ROOT = Path(__file__).resolve().parents[1]
CONTRACT = ROOT / "docs" / "BUILD_HOOKS_CONTRACT.md"
IMPLEMENTATION = ROOT / "src" / "edutex" / "build" / "hooks.py"


def context() -> BuildHookContext:
    return BuildHookContext(Path("project"), "html", Path("output/document.html"), {"run": "test"})


def test_hooks_are_opt_in_and_run_in_registration_order() -> None:
    calls: list[str] = []
    registry = BuildHookRegistry()
    registry.register(BuildHook("pre-one", BuildHookPhase.PRE_BUILD, lambda _ctx: calls.append("pre-one")))
    registry.register(BuildHook("post-one", BuildHookPhase.POST_BUILD, lambda _ctx: calls.append("post-one")))
    registry.register(BuildHook("pre-two", BuildHookPhase.PRE_BUILD, lambda _ctx: calls.append("pre-two")))

    registry.run(BuildHookPhase.PRE_BUILD, context())
    assert calls == ["pre-one", "pre-two"]
    registry.run(BuildHookPhase.POST_BUILD, context())
    assert calls == ["pre-one", "pre-two", "post-one"]


def test_empty_hook_sequence_is_a_noop() -> None:
    run_build_hooks((), BuildHookPhase.PRE_BUILD, context())


def test_duplicate_ids_and_frozen_registry_are_rejected() -> None:
    hook = BuildHook("same", BuildHookPhase.PRE_BUILD, lambda _ctx: None)
    registry = BuildHookRegistry()
    registry.register(hook)
    with pytest.raises(ValueError, match="Duplicate"):
        registry.register(hook)
    registry.freeze()
    with pytest.raises(RuntimeError, match="frozen"):
        registry.register(BuildHook("later", BuildHookPhase.POST_BUILD, lambda _ctx: None))


def test_context_metadata_is_detached_and_read_only() -> None:
    metadata = {"value": "original"}
    received: list[BuildHookContext] = []
    hook = BuildHook("capture", BuildHookPhase.PRE_BUILD, received.append)
    run_build_hooks((hook,), BuildHookPhase.PRE_BUILD, BuildHookContext(Path("project"), "html", metadata=metadata))
    metadata["value"] = "changed"
    assert received[0].metadata["value"] == "original"
    with pytest.raises(TypeError):
        received[0].metadata["new"] = "value"  # type: ignore[index]


def test_hook_error_identifies_phase_and_id_and_stops_execution() -> None:
    calls: list[str] = []
    registry = BuildHookRegistry()
    def fail(_ctx: BuildHookContext) -> None:
        raise ValueError("boom")
    registry.register(BuildHook("failing", BuildHookPhase.PRE_BUILD, fail))
    registry.register(BuildHook("unreached", BuildHookPhase.PRE_BUILD, lambda _ctx: calls.append("unreached")))

    with pytest.raises(BuildHookError, match="failing.*pre-build") as error:
        registry.run(BuildHookPhase.PRE_BUILD, context())
    assert error.value.hook_id == "failing"
    assert calls == []


def test_build_service_invokes_hooks_around_the_existing_build(tmp_path: Path, monkeypatch) -> None:
    service = BuildService()
    order: list[tuple[str, Path | None]] = []
    config = SimpleNamespace(
        build=SimpleNamespace(
            output_format=SimpleNamespace(value="html"),
            output_dir=Path("output"),
            output_file="course",
        )
    )
    registry = BuildHookRegistry()
    registry.register(BuildHook(
        "before", BuildHookPhase.PRE_BUILD,
        lambda ctx: order.append(("pre", ctx.output_path)),
    ))
    registry.register(BuildHook(
        "after", BuildHookPhase.POST_BUILD,
        lambda ctx: order.append(("post", ctx.output_path)),
    ))

    def fake_build(self, _config, _knowledge, _theme, _layout, project_root, document=None):
        del document
        self._output_path = project_root / "output" / "course.html"

    monkeypatch.setattr(BuildService, "_build_without_hooks", fake_build)
    service.build(config, None, None, None, tmp_path, hooks=registry)

    expected = tmp_path / "output" / "course.html"
    assert order == [("pre", expected), ("post", expected)]
    assert registry._frozen is True


def test_build_service_without_hooks_keeps_legacy_path(tmp_path: Path, monkeypatch) -> None:
    service = BuildService()
    called: list[bool] = []
    config = SimpleNamespace(build=SimpleNamespace(output_format=SimpleNamespace(value="html")))

    def fake_build(self, _config, _knowledge, _theme, _layout, _project_root, document=None):
        del document
        called.append(True)

    monkeypatch.setattr(BuildService, "_build_without_hooks", fake_build)
    service.build(config, None, None, None, tmp_path)
    assert called == [True]


def test_documentation_and_implementation_markers_are_present() -> None:
    contract = CONTRACT.read_text(encoding="utf-8")
    implementation = IMPLEMENTATION.read_text(encoding="utf-8")
    for marker in ("opt-in", "pre-build", "post-build", "ordine", "deterministici", "BuildService"):
        assert marker in contract
    for marker in ("BuildHookPhase", "BuildHookContext", "BuildHookRegistry", "BuildHookError"):
        assert marker in implementation
