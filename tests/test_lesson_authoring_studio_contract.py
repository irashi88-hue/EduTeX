from __future__ import annotations

from edutex.course.studio import compose_lesson_body, parse_lesson_blocks, split_lesson_frontmatter


def test_frontmatter_and_unsupported_blocks_round_trip_without_markdown_editor() -> None:
    source = "---\nid: lesson-01\ntitle: Test\nlanguage: it\nlevel: A1\nversion: 1.0.0\n---\n\n# Titolo\n\n::: custom.widget\nraw: keep\n:::\n\nTesto semplice.\n"
    frontmatter, body = split_lesson_frontmatter(source)
    blocks, tail = parse_lesson_blocks(body)
    assert frontmatter.startswith("---\nid: lesson-01")
    assert any(not block["editable"] for block in blocks)
    assert compose_lesson_body(blocks, tail, blocks) == body


def test_supported_exercise_types_parse_into_guided_blocks() -> None:
    fixtures = {
        "choice": "::: exercise\ntype: choice\nquestion: Pick one\noptions:\n- A\n- B\nanswer: A\n:::",
        "true_false": "::: exercise\ntype: true_false\nstatement: Sky is blue\nanswer: true\n:::",
        "cloze": "::: exercise\ntype: cloze\nsentence: I __ here.\nanswers:\n- am\n:::",
        "matching": "::: exercise\ntype: matching\nwords:\n- A\nmeanings:\n- B\n:::",
        "short_answer": "::: exercise\ntype: short_answer\nprompt: Answer\nanswer: yes\n:::",
        "translation": "::: exercise\ntype: translation\nsource: Ciao\nanswer: Hallo\n:::",
        "builder": "::: exercise\ntype: builder\ntokens:\n- I\nanswer: I am\n:::",
    }
    for expected, shortcode in fixtures.items():
        blocks, _ = parse_lesson_blocks(shortcode + "\n")
        assert blocks[0]["kind"] == "exercise"
        assert blocks[0]["data"]["exercise_type"] == expected




def test_locked_block_shows_type_and_plain_text_preview() -> None:
    blocks, _ = parse_lesson_blocks("::: custom.widget\n**Un esempio leggibile**\n:::\n")
    block = blocks[0]
    assert "custom.widget" in block["display"]
    assert "Un esempio leggibile" in block["preview"]
    assert "**" not in block["preview"]


def test_table_preview_is_readable_and_keeps_markdown_hidden() -> None:
    blocks, _ = parse_lesson_blocks("| Voce | Significato |\n| --- | --- |\n| **Haus** | Casa |\n")
    block = blocks[0]
    assert "Voce" in block["preview"]
    assert "Haus" in block["preview"]
    assert "**" not in block["preview"]

def test_editing_a_supported_block_keeps_frontmatter_outside_the_editor() -> None:
    body = "# Title\n\n::: exercise\ntype: choice\nquestion: Pick one\noptions:\n- A\nanswer: A\n:::\n"
    blocks, tail = parse_lesson_blocks(body)
    blocks[0]["dirty"] = True
    blocks[0]["data"]["text"] = "New title"
    result = compose_lesson_body(blocks, tail, parse_lesson_blocks(body)[0])
    assert result.startswith("# New title\n")
    assert "::: exercise" in result
