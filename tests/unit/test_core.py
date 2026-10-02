"""Unit tests for the Core public contracts."""

from pathlib import Path


def test_public_core_api_exports_contract():
    import edutex.core as public_core
    from edutex.core.context import LifecyclePhase, RuntimeContext
    from edutex.core.diagnostics import format_diagnostics_text, serialize_diagnostic, serialize_diagnostics
    from edutex.core.errors import (
        ActivationError,
        BuildError,
        ConfigurationError,
        EduTeXError,
        ExtensionError,
        KnowledgeError,
        LayoutError,
        RegistryError,
        ResolverError,
        ThemeError,
    )

    expected = {
        "ActivationError": ActivationError,
        "BuildError": BuildError,
        "ConfigurationError": ConfigurationError,
        "EduTeXError": EduTeXError,
        "ExtensionError": ExtensionError,
        "format_diagnostics_text": format_diagnostics_text,
        "serialize_diagnostic": serialize_diagnostic,
        "serialize_diagnostics": serialize_diagnostics,
        "KnowledgeError": KnowledgeError,
        "LayoutError": LayoutError,
        "LifecyclePhase": LifecyclePhase,
        "RegistryError": RegistryError,
        "ResolverError": ResolverError,
        "RuntimeContext": RuntimeContext,
        "ThemeError": ThemeError,
    }

    for name, expected_value in expected.items():
        assert getattr(public_core, name) is expected_value
        assert name in public_core.__all__


def test_runtime_context_basic_contract():
    from edutex.core import LifecyclePhase, RuntimeContext

    context = RuntimeContext(Path("."))

    assert context.phase is LifecyclePhase.INITIALIZING
    assert context.get_metadata("missing") is None

    context.advance(LifecyclePhase.CONFIGURING)
    context.set_metadata("source", "test")

    assert context.phase is LifecyclePhase.CONFIGURING
    assert context.get_metadata("source") == "test"

def test_runtime_context_rejects_non_sequential_transitions():
    import pytest

    from edutex.core import EduTeXError, LifecyclePhase, RuntimeContext

    context = RuntimeContext(Path("."))

    with pytest.raises(EduTeXError, match="Invalid lifecycle transition"):
        context.advance(LifecyclePhase.PROCESSING)

    assert context.phase is LifecyclePhase.INITIALIZING

    context.advance(LifecyclePhase.CONFIGURING)

    with pytest.raises(EduTeXError, match="Invalid lifecycle transition"):
        context.advance(LifecyclePhase.INITIALIZING)

    assert context.phase is LifecyclePhase.CONFIGURING

def test_build_project_coordinates_runtime_lifecycle(tmp_path, monkeypatch):
    from types import SimpleNamespace

    import edutex.core.cli as cli_module
    from edutex.core import LifecyclePhase

    contexts = []

    class RecordingContext:
        def __init__(self, project_root):
            self.project_root = project_root
            self.phases = []
            contexts.append(self)

        def advance(self, phase):
            self.phases.append(phase)

    class FakeResolver:
        def __init__(self, registry):
            self.registry = registry

        def resolve(self):
            return object()

    class FakeActivator:
        def activate(self, graph):
            return object()

    class FakeKnowledge:
        def process(self, state, project_root):
            return None

        @property
        def meta(self):
            return object()

    class FakeTheme:
        def process(self, state, knowledge, project_root):
            return None

        @property
        def theme_model(self):
            return object()

    class FakeLayout:
        def process(self, state, theme, project_root):
            return None

        @property
        def document(self):
            return object()

    class FakeExtensions:
        document = object()

        def process(self, state, layout, project_root, *, extension_order):
            return None

        def terminate(self):
            return None

    class FakeBuild:
        def __init__(self):
            self.output_path = tmp_path / "output" / "result.html"

        def build(
            self,
            config,
            knowledge,
            theme,
            layout,
            project_root,
            *,
            document,
        ):
            return None

    config = SimpleNamespace(
        logging=SimpleNamespace(level=SimpleNamespace(value="INFO")),
        extensions=SimpleNamespace(enabled=[]),
    )

    monkeypatch.setattr(cli_module, "RuntimeContext", RecordingContext, raising=False)
    monkeypatch.setattr(cli_module, "_register_project_assets", lambda config, root: object())
    monkeypatch.setattr(cli_module, "Resolver", FakeResolver)
    monkeypatch.setattr(cli_module, "Activator", FakeActivator)
    monkeypatch.setattr(cli_module, "KnowledgeService", FakeKnowledge)
    monkeypatch.setattr(cli_module, "ThemeService", FakeTheme)
    monkeypatch.setattr(cli_module, "LayoutService", FakeLayout)
    monkeypatch.setattr(cli_module, "ExtensionService", FakeExtensions)
    monkeypatch.setattr(cli_module, "BuildService", FakeBuild)

    result = cli_module.build_project(
        tmp_path / "edutex.config.yaml",
        tmp_path,
        config=config,
    )

    assert result == tmp_path / "output" / "result.html"
    assert len(contexts) == 1
    assert contexts[0].phases == [
        LifecyclePhase.CONFIGURING,
        LifecyclePhase.REGISTERING,
        LifecyclePhase.RESOLVING,
        LifecyclePhase.ACTIVATING,
        LifecyclePhase.PROCESSING,
        LifecyclePhase.BUILDING,
        LifecyclePhase.COMPLETE,
    ]

def test_build_project_marks_failure_and_terminates_extensions(tmp_path, monkeypatch):
    import pytest
    from types import SimpleNamespace

    import edutex.core.cli as cli_module
    from edutex.core import LifecyclePhase

    contexts = []
    terminations = []

    class RecordingContext:
        def __init__(self, project_root):
            self.project_root = project_root
            self.phase = LifecyclePhase.INITIALIZING
            self.phases = []
            contexts.append(self)

        def advance(self, phase):
            self.phases.append(phase)
            self.phase = phase

    class FakeResolver:
        def __init__(self, registry):
            self.registry = registry

        def resolve(self):
            return object()

    class FakeActivator:
        def activate(self, graph):
            return object()

    class FakeKnowledge:
        def process(self, state, project_root):
            return None

        @property
        def meta(self):
            return object()

    class FakeTheme:
        def process(self, state, knowledge, project_root):
            return None

        @property
        def theme_model(self):
            return object()

    class FakeLayout:
        def process(self, state, theme, project_root):
            return None

        @property
        def document(self):
            return object()

    class FakeExtensions:
        document = object()

        def process(self, state, layout, project_root, *, extension_order):
            return None

        def terminate(self):
            terminations.append(True)

    class FakeBuild:
        def build(
            self,
            config,
            knowledge,
            theme,
            layout,
            project_root,
            *,
            document,
        ):
            raise RuntimeError("synthetic build failure")

    config = SimpleNamespace(
        logging=SimpleNamespace(level=SimpleNamespace(value="INFO")),
        extensions=SimpleNamespace(enabled=[]),
    )

    monkeypatch.setattr(cli_module, "RuntimeContext", RecordingContext)
    monkeypatch.setattr(
        cli_module,
        "_register_project_assets",
        lambda config, root: object(),
    )
    monkeypatch.setattr(cli_module, "Resolver", FakeResolver)
    monkeypatch.setattr(cli_module, "Activator", FakeActivator)
    monkeypatch.setattr(cli_module, "KnowledgeService", FakeKnowledge)
    monkeypatch.setattr(cli_module, "ThemeService", FakeTheme)
    monkeypatch.setattr(cli_module, "LayoutService", FakeLayout)
    monkeypatch.setattr(cli_module, "ExtensionService", FakeExtensions)
    monkeypatch.setattr(cli_module, "BuildService", FakeBuild)

    with pytest.raises(RuntimeError, match="synthetic build failure"):
        cli_module.build_project(
            tmp_path / "edutex.config.yaml",
            tmp_path,
            config=config,
        )

    assert len(contexts) == 1
    assert contexts[0].phases == [
        LifecyclePhase.CONFIGURING,
        LifecyclePhase.REGISTERING,
        LifecyclePhase.RESOLVING,
        LifecyclePhase.ACTIVATING,
        LifecyclePhase.PROCESSING,
        LifecyclePhase.BUILDING,
        LifecyclePhase.FAILED,
    ]
    assert contexts[0].phase is LifecyclePhase.FAILED
    assert terminations == [True]

def test_validate_command_coordinates_runtime_lifecycle(tmp_path, monkeypatch):
    from pathlib import Path
    from types import SimpleNamespace

    import edutex.core.cli as cli_module
    from edutex.core import LifecyclePhase

    contexts = []

    class RecordingContext:
        def __init__(self, project_root):
            self.project_root = project_root
            self.phase = LifecyclePhase.INITIALIZING
            self.phases = []
            contexts.append(self)

        def advance(self, phase):
            self.phases.append(phase)
            self.phase = phase

    class FakeResolver:
        def __init__(self, registry):
            self.registry = registry

        def resolve(self):
            return object()

    class FakeActivator:
        def activate(self, graph):
            return object()

    class FakeKnowledge:
        def process(self, state, project_root):
            return None

    class FakeTheme:
        def process(self, state, knowledge, project_root):
            return None

    class FakeLayout:
        def process(self, state, theme, project_root):
            return None

    class FakeExtensions:
        def process(self, state, layout, project_root, *, extension_order):
            return None

        def terminate(self):
            return None

    config = SimpleNamespace(
        logging=SimpleNamespace(level=SimpleNamespace(value="INFO")),
        extensions=SimpleNamespace(enabled=[]),
    )

    monkeypatch.setattr(cli_module, "RuntimeContext", RecordingContext)
    monkeypatch.setattr(cli_module, "load_config", lambda path, profile=None: config)
    monkeypatch.setattr(
        cli_module,
        "_configure_logging",
        lambda level: None,
    )
    monkeypatch.setattr(
        cli_module,
        "_register_project_assets",
        lambda config, root: object(),
    )
    monkeypatch.setattr(cli_module, "Resolver", FakeResolver)
    monkeypatch.setattr(cli_module, "Activator", FakeActivator)
    monkeypatch.setattr(cli_module, "KnowledgeService", FakeKnowledge)
    monkeypatch.setattr(cli_module, "ThemeService", FakeTheme)
    monkeypatch.setattr(cli_module, "LayoutService", FakeLayout)
    monkeypatch.setattr(cli_module, "ExtensionService", FakeExtensions)

    cli_module.validate_command.callback(
        tmp_path,
        Path("edutex.config.yaml"),
    )

    assert len(contexts) == 1
    assert contexts[0].phases == [
        LifecyclePhase.CONFIGURING,
        LifecyclePhase.REGISTERING,
        LifecyclePhase.RESOLVING,
        LifecyclePhase.ACTIVATING,
        LifecyclePhase.PROCESSING,
        LifecyclePhase.COMPLETE,
    ]
    assert contexts[0].phase is LifecyclePhase.COMPLETE

def test_validate_command_marks_failure_and_terminates_extensions(
    tmp_path,
    monkeypatch,
):
    import pytest
    from pathlib import Path
    from types import SimpleNamespace

    import edutex.core.cli as cli_module
    from edutex.core import LifecyclePhase

    contexts = []
    terminations = []

    class RecordingContext:
        def __init__(self, project_root):
            self.project_root = project_root
            self.phase = LifecyclePhase.INITIALIZING
            self.phases = []
            contexts.append(self)

        def advance(self, phase):
            self.phases.append(phase)
            self.phase = phase

    class FakeResolver:
        def __init__(self, registry):
            self.registry = registry

        def resolve(self):
            return object()

    class FakeActivator:
        def activate(self, graph):
            return object()

    class FakeKnowledge:
        def process(self, state, project_root):
            return None

    class FakeTheme:
        def process(self, state, knowledge, project_root):
            return None

    class FakeLayout:
        def process(self, state, theme, project_root):
            return None

    class FakeExtensions:
        def process(self, state, layout, project_root, *, extension_order):
            raise RuntimeError("synthetic validation failure")

        def terminate(self):
            terminations.append(True)

    config = SimpleNamespace(
        logging=SimpleNamespace(level=SimpleNamespace(value="INFO")),
        extensions=SimpleNamespace(enabled=[]),
    )

    monkeypatch.setattr(cli_module, "RuntimeContext", RecordingContext)
    monkeypatch.setattr(cli_module, "load_config", lambda path, profile=None: config)
    monkeypatch.setattr(
        cli_module,
        "_configure_logging",
        lambda level: None,
    )
    monkeypatch.setattr(
        cli_module,
        "_register_project_assets",
        lambda config, root: object(),
    )
    monkeypatch.setattr(cli_module, "Resolver", FakeResolver)
    monkeypatch.setattr(cli_module, "Activator", FakeActivator)
    monkeypatch.setattr(cli_module, "KnowledgeService", FakeKnowledge)
    monkeypatch.setattr(cli_module, "ThemeService", FakeTheme)
    monkeypatch.setattr(cli_module, "LayoutService", FakeLayout)
    monkeypatch.setattr(cli_module, "ExtensionService", FakeExtensions)

    with pytest.raises(RuntimeError, match="synthetic validation failure"):
        cli_module.validate_command.callback(
            tmp_path,
            Path("edutex.config.yaml"),
        )

    assert len(contexts) == 1
    assert contexts[0].phases == [
        LifecyclePhase.CONFIGURING,
        LifecyclePhase.REGISTERING,
        LifecyclePhase.RESOLVING,
        LifecyclePhase.ACTIVATING,
        LifecyclePhase.PROCESSING,
        LifecyclePhase.FAILED,
    ]
    assert contexts[0].phase is LifecyclePhase.FAILED
    assert terminations == [True]

def test_runtime_context_allows_validation_completion_without_build():
    from pathlib import Path

    from edutex.core import LifecyclePhase, RuntimeContext

    context = RuntimeContext(Path("."))

    for phase in (
        LifecyclePhase.CONFIGURING,
        LifecyclePhase.REGISTERING,
        LifecyclePhase.RESOLVING,
        LifecyclePhase.ACTIVATING,
        LifecyclePhase.PROCESSING,
    ):
        context.advance(phase)

    context.advance(LifecyclePhase.COMPLETE)

    assert context.phase is LifecyclePhase.COMPLETE

def test_prepare_project_pipeline_returns_activated_state(tmp_path, monkeypatch):
    from types import SimpleNamespace

    import edutex.core.cli as cli_module

    activated_state = object()

    class FakeResolver:
        def __init__(self, registry):
            self.registry = registry

        def resolve(self):
            return object()

    class FakeActivator:
        def activate(self, graph):
            return activated_state

    class FakeKnowledge:
        def process(self, state, project_root):
            return None

    class FakeTheme:
        def process(self, state, knowledge, project_root):
            return None

    class FakeLayout:
        def process(self, state, theme, project_root):
            return None

    config = SimpleNamespace(
        logging=SimpleNamespace(level=SimpleNamespace(value="INFO")),
    )
    context = SimpleNamespace(advance=lambda phase: None)

    monkeypatch.setattr(cli_module, "_configure_logging", lambda level: None)
    monkeypatch.setattr(
        cli_module,
        "_register_project_assets",
        lambda config, root: object(),
    )
    monkeypatch.setattr(cli_module, "Resolver", FakeResolver)
    monkeypatch.setattr(cli_module, "Activator", FakeActivator)
    monkeypatch.setattr(cli_module, "KnowledgeService", FakeKnowledge)
    monkeypatch.setattr(cli_module, "ThemeService", FakeTheme)
    monkeypatch.setattr(cli_module, "LayoutService", FakeLayout)

    prepared = cli_module._prepare_project_pipeline(
        tmp_path / "edutex.config.yaml",
        tmp_path,
        context,
        config=config,
    )

    assert prepared.config is config
    assert prepared.state is activated_state
