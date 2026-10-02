"""Test del contratto API pubblico di EduTeX."""

from __future__ import annotations

from pathlib import Path

import click

from edutex.core.cli import main


ROOT = Path(__file__).resolve().parents[1]
CONTRACT = ROOT / "docs" / "PUBLIC_API_CONTRACT.md"


def find_parameter(command: click.Command, name: str) -> click.Parameter:
    for parameter in command.params:
        if parameter.name == name:
            return parameter

    raise AssertionError(
        f"Parametro mancante: {command.name}.{name}"
    )


def find_option(command: click.Command, option: str) -> click.Parameter:
    for parameter in command.params:
        if option in parameter.opts:
            return parameter

    raise AssertionError(
        f"Opzione mancante: {command.name} {option}"
    )


def get_choices(
    command: click.Command,
    option: str,
) -> tuple[str, ...]:
    parameter = find_option(command, option)

    if not isinstance(parameter.type, click.Choice):
        raise AssertionError(
            f"L'opzione {option} non usa click.Choice."
        )

    return tuple(parameter.type.choices)


def test_documentazione_api_pubblica() -> None:
    contract = CONTRACT.read_text(encoding="utf-8")

    required_markers = (
        "edutex = edutex.core.cli:main",
        "edutex init",
        "edutex lint",
        "edutex build",
        "edutex validate",
        "edutex inspect",
        "edutex config diff",
        "edutex course validate",
        "edutex course build",
        "--theme default|dark",
        "--language en|it|ja",
        "--format text|json",
        "--format html|latex|pdf",
        "--profile NAME",
        "build.output_format",
        "1.0.0",
    )

    for marker in required_markers:
        assert marker in contract, (
            f"Marker mancante nella documentazione: {marker}"
        )


def test_comandi_principali() -> None:
    assert set(main.commands) == {
        "init",
        "lint",
        "build",
        "validate",
        "inspect",
        "config",
        "course",
    }

    course = main.commands["course"]

    assert isinstance(course, click.Group)
    assert set(course.commands) == {"build", "validate"}


def test_contratto_config_diff() -> None:
    config_group = main.commands["config"]
    assert isinstance(config_group, click.Group)
    assert set(config_group.commands) == {"diff"}

    command = config_group.commands["diff"]
    assert find_option(command, "--project").default == Path(".")
    assert find_option(command, "--config").default == "edutex.config.yaml"
    assert find_option(command, "--profile").required is True
    assert get_choices(command, "--format") == ("text", "json")


def test_contratto_init() -> None:
    command = main.commands["init"]

    assert find_parameter(command, "project_dir").default == Path(
        "edutex-project"
    )
    assert get_choices(command, "--theme") == ("default", "dark")
    assert get_choices(command, "--language") == ("en", "it", "ja")
    assert find_option(command, "--force").is_flag is True


def test_contratto_lint() -> None:
    command = main.commands["lint"]

    assert find_parameter(command, "source_file").required is True
    assert get_choices(command, "--format") == ("text", "json")


def test_contratto_build() -> None:
    command = main.commands["build"]

    assert find_option(command, "--project").default == Path(".")
    assert find_option(command, "--config").default == "edutex.config.yaml"
    assert find_option(command, "--lint").is_flag is True
    assert get_choices(command, "--format") == ("text", "json")


def test_contratto_validate() -> None:
    command = main.commands["validate"]

    assert find_option(command, "--project").default == Path(".")
    assert find_option(command, "--config").default == "edutex.config.yaml"
    assert get_choices(command, "--format") == ("text", "json")



def test_contratto_inspect() -> None:
    command = main.commands["inspect"]

    assert find_option(command, "--project").default == Path(".")
    assert find_option(command, "--config").default == "edutex.config.yaml"
    assert get_choices(command, "--format") == ("json",)


def test_contratto_course_validate() -> None:
    command = main.commands["course"].commands["validate"]

    assert find_option(command, "--project").default == Path(".")
    assert find_option(command, "--manifest").default == "course.yaml"
    assert get_choices(command, "--format") == ("text", "json")


def test_contratto_course_build() -> None:
    command = main.commands["course"].commands["build"]

    assert find_option(command, "--project").default == Path(".")
    assert find_option(command, "--manifest").default == "course.yaml"
    assert get_choices(command, "--format") == ("html", "latex", "pdf")
    assert find_option(command, "--output").default is None

def test_profile_option_is_available_on_configuration_commands() -> None:
    commands = (
        main.commands["build"],
        main.commands["validate"],
        main.commands["inspect"],
        main.commands["course"].commands["build"],
    )
    for command in commands:
        parameter = find_option(command, "--profile")
        assert parameter.default is None
        assert parameter.required is False
