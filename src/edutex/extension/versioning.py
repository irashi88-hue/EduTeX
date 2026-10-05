"""Semantic-version validation for EduTeX extension manifests."""

from __future__ import annotations


def _is_ascii_digits(value: str) -> bool:
    return bool(value) and all(character in "0123456789" for character in value)


def _has_no_numeric_leading_zero(value: str) -> bool:
    return len(value) == 1 or not value.startswith("0")


def _valid_identifiers(value: str, *, numeric_leading_zeroes_forbidden: bool) -> bool:
    identifiers = value.split(".")
    if not identifiers or any(not identifier for identifier in identifiers):
        return False
    for identifier in identifiers:
        if not all(character in "0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz-" for character in identifier):
            return False
        if (
            numeric_leading_zeroes_forbidden
            and _is_ascii_digits(identifier)
            and not _has_no_numeric_leading_zero(identifier)
        ):
            return False
    return True


def is_valid_semver(value: object) -> bool:
    """Return whether ``value`` is an exact SemVer 2.0.0 string."""
    if not isinstance(value, str) or not value:
        return False
    if value.count("+") > 1:
        return False

    core_and_prerelease, plus, build = value.partition("+")
    if plus and not _valid_identifiers(
        build,
        numeric_leading_zeroes_forbidden=False,
    ):
        return False

    core, hyphen, prerelease = core_and_prerelease.partition("-")
    core_parts = core.split(".")
    if len(core_parts) != 3:
        return False
    if any(
        not _is_ascii_digits(part) or not _has_no_numeric_leading_zero(part)
        for part in core_parts
    ):
        return False

    if hyphen and not _valid_identifiers(
        prerelease,
        numeric_leading_zeroes_forbidden=True,
    ):
        return False
    return True


def validate_semver(value: object, *, field_name: str = "version") -> str:
    """Validate and return one extension version without normalizing it."""
    if not is_valid_semver(value):
        raise ValueError(
            f"Extension {field_name} must be a valid SemVer 2.0.0 string; "
            f"got {value!r}."
        )
    return value
