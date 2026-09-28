"""Unit tests for the Core public contracts."""

from pathlib import Path


def test_public_core_api_exports_contract():
    import edutex.core as public_core
    from edutex.core.context import LifecyclePhase, RuntimeContext
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
