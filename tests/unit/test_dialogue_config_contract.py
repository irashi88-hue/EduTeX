"""Contract tests for the optional dialogue configuration and renderer plumbing."""

import inspect

import pytest
from pydantic import ValidationError

from edutex.build.html_renderer import HtmlRenderer
from edutex.configuration.schema import DialogueConfig, EduTexConfig


def test_dialogue_is_disabled_by_default():
    config = DialogueConfig()

    assert config.enabled is False
    assert config.endpoint == "http://localhost:11434"
    assert config.model == ""
    assert config.timeout_seconds == 60


def test_enabled_dialogue_requires_a_model():
    with pytest.raises(ValidationError):
        DialogueConfig(enabled=True, model="   ")


def test_enabled_dialogue_with_model_is_accepted():
    config = DialogueConfig(enabled=True, model="llama3.2")

    assert config.enabled is True
    assert config.model == "llama3.2"


def test_endpoint_must_be_http_or_https():
    with pytest.raises(ValidationError):
        DialogueConfig(endpoint="file:///tmp/model")

    accepted = DialogueConfig(endpoint="https://models.example.org")
    assert accepted.endpoint == "https://models.example.org"


def test_timeout_must_be_positive_and_bounded():
    with pytest.raises(ValidationError):
        DialogueConfig(timeout_seconds=0)
    with pytest.raises(ValidationError):
        DialogueConfig(timeout_seconds=601)


def test_edutex_config_exposes_optional_dialogue_section():
    field = EduTexConfig.model_fields["dialogue"]

    assert field.default_factory is DialogueConfig


def test_html_renderer_accepts_optional_dialogue_config_defaulting_to_none():
    parameter = inspect.signature(HtmlRenderer.render).parameters["dialogue_config"]

    assert parameter.default is None