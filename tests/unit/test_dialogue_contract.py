"""Contract tests for the text-only dialogue exercise: parser, prompt and verdict."""

from edutex.build.dialogue import (
    DEFAULT_MAX_TURNS,
    build_system_prompt,
    is_dialogue_body,
    parse_dialogue_body,
    parse_verdict,
)

VALID_BODY = """type: dialogue
title: Dialogo al ristorante
level: A1
language: tedesco
topic: Essen im Restaurant
role: il cameriere
goal: Ordinare un pasto completo
max_turns: 8
min_criteria: 3
vocabulary:
- Speisekarte
- bestellen
structures:
- Ich möchte ...
- Ich nehme ...
criteria:
- Saluta e chiede un tavolo
- Ordina almeno un piatto con "Ich möchte" o "Ich nehme"
- Chiede il conto
"""

MINIMAL_BODY = """type: dialogue
level: A2
language: italiano
topic: Al mercato
role: il venditore
goal: Comprare della frutta
criteria:
- Saluta
- Chiede il prezzo
"""


def test_is_dialogue_body_detects_exact_type_line():
    assert is_dialogue_body(VALID_BODY)
    assert not is_dialogue_body("type: choice\nquestion: Pick one\n")
    assert not is_dialogue_body("type: dialogues\n")


def test_valid_body_parses_into_spec():
    result = parse_dialogue_body(VALID_BODY)

    assert result.errors == ()
    assert result.spec is not None
    assert result.spec.title == "Dialogo al ristorante"
    assert result.spec.level == "A1"
    assert result.spec.language == "tedesco"
    assert result.spec.criteria == (
        "Saluta e chiede un tavolo",
        'Ordina almeno un piatto con "Ich möchte" o "Ich nehme"',
        "Chiede il conto",
    )
    assert result.spec.vocabulary == ("Speisekarte", "bestellen")
    assert result.spec.structures == ("Ich möchte ...", "Ich nehme ...")
    assert result.spec.max_turns == 8
    assert result.spec.min_criteria == 3


def test_optional_keys_take_defaults():
    result = parse_dialogue_body(MINIMAL_BODY)

    assert result.errors == ()
    assert result.spec is not None
    assert result.spec.title == ""
    assert result.spec.vocabulary == ()
    assert result.spec.structures == ()
    assert result.spec.max_turns == DEFAULT_MAX_TURNS
    assert result.spec.min_criteria == 2


def test_missing_required_key_is_reported():
    result = parse_dialogue_body(VALID_BODY.replace("goal: Ordinare un pasto completo\n", ""))

    assert result.spec is None
    assert "chiave obbligatoria mancante: goal" in result.errors


def test_free_text_line_is_rejected():
    result = parse_dialogue_body(VALID_BODY + "Scrivi un dialogo.\n")

    assert result.spec is None
    assert "testo libero non ammesso: Scrivi un dialogo." in result.errors


def test_unknown_key_is_rejected():
    result = parse_dialogue_body(VALID_BODY + "color: blue\n")

    assert result.spec is None
    assert "chiave sconosciuta: color" in result.errors


def test_list_item_without_list_key_is_rejected():
    result = parse_dialogue_body("type: dialogue\n- Saluta\n")

    assert result.spec is None
    assert any(error.startswith("voce di lista senza chiave") for error in result.errors)


def test_list_key_with_inline_value_is_rejected():
    result = parse_dialogue_body(VALID_BODY.replace("vocabulary:\n", "vocabulary: Speisekarte\n"))

    assert result.spec is None
    assert "vocabulary deve usare righe che iniziano con un trattino" in result.errors


def test_duplicate_key_is_rejected():
    result = parse_dialogue_body(VALID_BODY + "level: B1\n")

    assert result.spec is None
    assert "chiave duplicata: level" in result.errors


def test_invalid_level_is_rejected():
    result = parse_dialogue_body(VALID_BODY.replace("level: A1", "level: Z9"))

    assert result.spec is None
    assert "livello non valido: Z9" in result.errors


def test_max_turns_must_be_an_integer_in_range():
    zero = parse_dialogue_body(VALID_BODY.replace("max_turns: 8", "max_turns: 0"))
    too_many = parse_dialogue_body(VALID_BODY.replace("max_turns: 8", "max_turns: 21"))
    not_a_number = parse_dialogue_body(VALID_BODY.replace("max_turns: 8", "max_turns: otto"))

    assert "max_turns fuori intervallo 1-20: 0" in zero.errors
    assert "max_turns fuori intervallo 1-20: 21" in too_many.errors
    assert "max_turns non e un intero: otto" in not_a_number.errors


def test_criteria_need_at_least_two_entries():
    body = "type: dialogue\nlevel: A1\nlanguage: tedesco\ntopic: Cibo\nrole: il cameriere\ngoal: Ordinare\ncriteria:\n- Saluta\n"
    result = parse_dialogue_body(body)

    assert result.spec is None
    assert "criteria richiede almeno due voci" in result.errors


def test_min_criteria_must_fit_criteria_count():
    result = parse_dialogue_body(VALID_BODY.replace("min_criteria: 3", "min_criteria: 4"))

    assert result.spec is None
    assert "min_criteria fuori intervallo 1-3: 4" in result.errors


def test_system_prompt_is_deterministic_and_carries_the_fields():
    spec = parse_dialogue_body(VALID_BODY).spec
    assert spec is not None

    first = build_system_prompt(spec)
    second = build_system_prompt(spec)

    assert first == second
    assert "Sei un insegnante di tedesco di livello A1." in first
    assert "Interpreta: il cameriere." in first
    assert "Ordinare un pasto completo" in first
    assert "Speisekarte, bestellen" in first
    assert "Fai una sola domanda per turno. Non superare 8 turni." in first
    assert "Il verdetto è SUPERATO solo se soddisfi almeno 3 criteri su 3." in first
    assert "VERDETTO: SUPERATO oppure VERDETTO: NON SUPERATO" in first


def test_verdict_superato_is_parsed():
    text = "Ottimo lavoro.\nVERDETTO: SUPERATO\nCRITERI: 3/3\nBuona pronuncia e lessico corretto."

    verdict = parse_verdict(text)

    assert verdict.status == "SUPERATO"
    assert verdict.criteria == "3/3"
    assert verdict.reason == "Buona pronuncia e lessico corretto."


def test_verdict_non_superato_is_parsed():
    text = "VERDETTO: NON SUPERATO\nCRITERI: 1/3\nManca l'ordine."

    verdict = parse_verdict(text)

    assert verdict.status == "NON SUPERATO"
    assert verdict.criteria == "1/3"


def test_missing_verdict_returns_empty_result():
    verdict = parse_verdict("Continuiamo: cosa ordini?")

    assert verdict.status is None
    assert verdict.criteria is None
    assert verdict.reason == ""


def test_malformed_verdict_is_ignored():
    verdict = parse_verdict("VERDETTO: FORSE\nCRITERI: 2/3")

    assert verdict.status is None