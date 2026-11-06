"""Pure helpers for the text-only dialogue exercise.

Parsing, prompt construction and verdict parsing only: no rendering and no
network access. The contract is described in docs/DIALOGUE_EXERCISE_DRAFT.md.
"""

from __future__ import annotations

import re
from dataclasses import dataclass

DIALOGUE_TYPE = "dialogue"
DEFAULT_MAX_TURNS = 8
MAX_TURNS_LIMIT = 20
MIN_CRITERIA_COUNT = 2
LEVELS = ("A1", "A2", "B1", "B2", "C1", "C2")
REQUIRED_KEYS = frozenset({"type", "level", "language", "topic", "role", "goal", "criteria"})
OPTIONAL_KEYS = frozenset({"title", "max_turns", "min_criteria"})
LIST_KEYS = frozenset({"vocabulary", "structures", "criteria"})
KNOWN_KEYS = REQUIRED_KEYS | OPTIONAL_KEYS | LIST_KEYS
VERDICT_WINDOW = 6

_VERDICT_PATTERN = re.compile(r"^VERDETTO:\s*(SUPERATO|NON SUPERATO)$")
_CRITERIA_PATTERN = re.compile(r"^CRITERI:\s*(\d+/\d+)$")


@dataclass(frozen=True)
class DialogueSpec:
    title: str
    level: str
    language: str
    topic: str
    role: str
    goal: str
    criteria: tuple[str, ...]
    vocabulary: tuple[str, ...]
    structures: tuple[str, ...]
    max_turns: int
    min_criteria: int


@dataclass(frozen=True)
class DialogueParseResult:
    spec: DialogueSpec | None
    errors: tuple[str, ...]


@dataclass(frozen=True)
class DialogueVerdict:
    status: str | None
    criteria: str | None
    reason: str


def is_dialogue_body(body: str) -> bool:
    """Return True when an exercise body declares type: dialogue."""
    return any(line.strip().lower() == "type: dialogue" for line in body.splitlines())


def parse_dialogue_body(body: str) -> DialogueParseResult:
    """Parse the body of a dialogue exercise, collecting every error found."""
    errors: list[str] = []
    values: dict[str, str] = {}
    lists: dict[str, list[str]] = {}
    current_list: str | None = None

    for raw_line in body.splitlines():
        line = raw_line.strip()
        if not line:
            continue

        if line.startswith("- "):
            if current_list is None:
                errors.append(f"voce di lista senza chiave: {line[2:].strip()}")
            else:
                lists[current_list].append(line[2:].strip())
            continue

        key, separator, value = line.partition(":")
        key = key.strip().lower()
        if not separator:
            errors.append(f"testo libero non ammesso: {line}")
            current_list = None
            continue
        if key not in KNOWN_KEYS:
            errors.append(f"chiave sconosciuta: {key}")
            current_list = None
            continue
        if key in values or key in lists:
            errors.append(f"chiave duplicata: {key}")
            current_list = None
            continue

        value = value.strip()
        if key in LIST_KEYS:
            if value:
                errors.append(f"{key} deve usare righe che iniziano con un trattino")
                current_list = None
            else:
                lists[key] = []
                current_list = key
        else:
            values[key] = value
            current_list = None

    if "type" in values and values["type"].lower() != DIALOGUE_TYPE:
        errors.append(f"tipo inatteso: {values['type']}")

    for key in sorted(REQUIRED_KEYS):
        present = key in lists if key in LIST_KEYS else key in values
        if not present:
            errors.append(f"chiave obbligatoria mancante: {key}")

    level = values.get("level", "")
    if "level" in values and level not in LEVELS:
        errors.append(f"livello non valido: {level}")

    max_turns = DEFAULT_MAX_TURNS
    if "max_turns" in values:
        try:
            max_turns = int(values["max_turns"])
        except ValueError:
            errors.append(f"max_turns non e un intero: {values['max_turns']}")
            max_turns = DEFAULT_MAX_TURNS
        else:
            if not 1 <= max_turns <= MAX_TURNS_LIMIT:
                errors.append(f"max_turns fuori intervallo 1-{MAX_TURNS_LIMIT}: {max_turns}")

    criteria = tuple(lists.get("criteria", []))
    if "criteria" in lists and len(criteria) < MIN_CRITERIA_COUNT:
        errors.append("criteria richiede almeno due voci")

    min_criteria = len(criteria)
    if "min_criteria" in values:
        try:
            min_criteria = int(values["min_criteria"])
        except ValueError:
            errors.append(f"min_criteria non e un intero: {values['min_criteria']}")
            min_criteria = len(criteria)
        else:
            if not 1 <= min_criteria <= len(criteria):
                errors.append(f"min_criteria fuori intervallo 1-{len(criteria)}: {min_criteria}")

    if errors:
        return DialogueParseResult(spec=None, errors=tuple(errors))

    spec = DialogueSpec(
        title=values.get("title", ""),
        level=level,
        language=values["language"],
        topic=values["topic"],
        role=values["role"],
        goal=values["goal"],
        criteria=criteria,
        vocabulary=tuple(lists.get("vocabulary", [])),
        structures=tuple(lists.get("structures", [])),
        max_turns=max_turns,
        min_criteria=min_criteria,
    )
    return DialogueParseResult(spec=spec, errors=())


def build_system_prompt(spec: DialogueSpec) -> str:
    """Return the deterministic system prompt for a dialogue exercise."""
    vocabulary = ", ".join(spec.vocabulary) or "nessuno"
    structures = ", ".join(spec.structures) or "nessuna"
    criteria = "; ".join(spec.criteria)
    return "\n".join(
        [
            f"Sei un insegnante di {spec.language} di livello {spec.level}. "
            f"Parla solo in {spec.language}. Spiega in italiano solo se lo studente non capisce.",
            f"Interpreta: {spec.role}. Limita la conversazione all'obiettivo: {spec.goal}, "
            f"sul tema {spec.topic}. Se lo studente esce dal tema, riportalo gentilmente.",
            f"Usa il lessico: {vocabulary}. Incoraggia le strutture: {structures}.",
            f"Fai una sola domanda per turno. Non superare {spec.max_turns} turni.",
            "Correggi gli errori in modo breve: mostra la frase corretta e poi continua.",
            f"Quando ti viene chiesto di valutare, controlla i criteri: {criteria}.",
            f"Il verdetto è SUPERATO solo se soddisfi almeno {spec.min_criteria} criteri "
            f"su {len(spec.criteria)}.",
            "Formato del verdetto, come ultime tre righe:",
            "VERDETTO: SUPERATO oppure VERDETTO: NON SUPERATO",
            "CRITERI: n/N",
            "una breve motivazione in italiano",
        ]
    )


def parse_verdict(text: str) -> DialogueVerdict:
    """Extract the indicative verdict from the last lines of a model answer."""
    lines = [line.strip() for line in text.splitlines() if line.strip()][-VERDICT_WINDOW:]
    verdict_index = next(
        (index for index, line in enumerate(lines) if _VERDICT_PATTERN.match(line)),
        None,
    )
    if verdict_index is None:
        return DialogueVerdict(status=None, criteria=None, reason="")

    match = _VERDICT_PATTERN.match(lines[verdict_index])
    status = match.group(1) if match else None
    criteria: str | None = None
    reason_parts: list[str] = []
    for line in lines[verdict_index + 1 :]:
        criteria_match = _CRITERIA_PATTERN.match(line)
        if criteria_match and criteria is None:
            criteria = criteria_match.group(1)
        else:
            reason_parts.append(line)
    return DialogueVerdict(status=status, criteria=criteria, reason=" ".join(reason_parts))