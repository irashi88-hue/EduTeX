"""Framework-version compatibility for EduTeX extensions."""

from __future__ import annotations

from edutex.extension.versioning import is_valid_semver


FRAMEWORK_VERSION = "1.0.0"
_OPERATORS = (">=", "<=", ">", "<", "=")


def _ascii_digits(value: str) -> bool:
    return bool(value) and all(character in "0123456789" for character in value)


def _stable_tuple(value: str) -> tuple[int, int, int]:
    if not is_valid_semver(value) or "-" in value or "+" in value:
        raise ValueError(f"Framework version must be stable SemVer 2.0.0: {value!r}")
    parts = value.split(".")
    if len(parts) != 3 or any(not _ascii_digits(part) for part in parts):
        raise ValueError(f"Framework version must be stable SemVer 2.0.0: {value!r}")
    return tuple(int(part) for part in parts)  # type: ignore[return-value]


def _constraint_clauses(constraint: str) -> tuple[tuple[str, tuple[int, int, int]], ...]:
    if not isinstance(constraint, str) or not constraint.strip():
        raise ValueError("Extension framework compatibility must be a non-empty string")
    clauses: list[tuple[str, tuple[int, int, int]]] = []
    for raw_clause in constraint.split(","):
        clause = raw_clause.strip()
        operator = "="
        for candidate in _OPERATORS:
            if clause.startswith(candidate):
                operator = candidate
                clause = clause[len(candidate):].strip()
                break
        if not clause or any(character not in "0123456789." for character in clause):
            raise ValueError(
                "Extension framework compatibility must use comma-separated "
                "SemVer comparators such as '>=1.0.0,<2.0.0'"
            )
        try:
            target = _stable_tuple(clause)
        except ValueError as exc:
            raise ValueError(
                "Extension framework compatibility must use comma-separated "
                "SemVer comparators such as '>=1.0.0,<2.0.0'"
            ) from exc
        clauses.append((operator, target))
    return tuple(clauses)


def is_framework_compatible(
    constraint: str,
    framework_version: str = FRAMEWORK_VERSION,
) -> bool:
    """Return whether one framework version satisfies every constraint clause."""
    clauses = _constraint_clauses(constraint)
    current = _stable_tuple(framework_version)
    for operator, expected in clauses:
        if operator == "=" and current != expected:
            return False
        if operator == ">" and not current > expected:
            return False
        if operator == ">=" and not current >= expected:
            return False
        if operator == "<" and not current < expected:
            return False
        if operator == "<=" and not current <= expected:
            return False
    return True


def validate_framework_compatibility(
    constraint: str,
    framework_version: str = FRAMEWORK_VERSION,
) -> str:
    """Validate a declared constraint and return it unchanged."""
    if not is_framework_compatible(constraint, framework_version):
        raise ValueError(
            f"Extension is incompatible with framework {framework_version}: "
            f"declared compatibility {constraint!r}."
        )
    return constraint
