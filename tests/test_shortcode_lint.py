from edutex.knowledge.shortcode_lint import format_text, lint_source

def codes(report): return [item.code for item in report.diagnostics]

def test_valid_source_is_clean():
    report=lint_source('::: formula.math\nE = mc^2\n:::\n\n::: example.comparative\n+ correct\n- incorrect\n:::\n',path='lesson.md')
    assert report.valid and not report.diagnostics

def test_parser_errors_have_stable_codes():
    assert codes(lint_source('::: exmaple\ntext\n:::',path='lesson.md'))==['SC001']
    assert codes(lint_source('::: note\ntext\n',path='lesson.md'))==['SC003']

def test_missing_solution_is_warning():
    report=lint_source('::: exercise\nWrite a sentence.\n:::',path='lesson.md')
    assert report.valid and codes(report)==['SC201']
    assert format_text(report).startswith('WARNING lesson.md:1:1 [SC201]')

def test_matching_mismatch_is_error():
    report=lint_source('::: exercise\ntype: matching\nwords:\n- one\n- two\nmeanings:\n- uno\n:::\n')
    assert not report.valid and 'SC105' in codes(report)

def test_json_contract_is_deterministic():
    report=lint_source('::: formula.math\n:::\n',path='lesson.md')
    assert report.to_json()==report.to_json()
    payload=report.to_dict(); assert list(payload)==['path','valid','errors','warnings']; assert payload['errors'][0]['code']=='SC101'

def test_empty_content_shortcodes_are_errors():
    cases = [
        '::: rule\n:::',
        '::: note\n   \n:::',
        '::: example.simple\n:::',
        '::: exercise\nTask.\n::: solution\n   \n:::\n:::',
    ]

    for source in cases:
        report = lint_source(source, path="lesson.md")
        assert not report.valid
        assert [item.code for item in report.diagnostics].count("SC106") == 1


def test_non_empty_content_shortcodes_remain_valid():
    report = lint_source(
        "::: rule\nVerb second.\n:::\n"
        "::: note\nRemember the exception.\n:::\n"
        "::: example.simple\nIch lerne. — Studio.\n:::\n",
        path="lesson.md",
    )

    assert report.valid
    assert "SC106" not in [item.code for item in report.diagnostics]

