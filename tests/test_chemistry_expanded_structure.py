"""Tests for expanded molecular structural formulas."""

from edutex.build.html_renderer import HtmlRenderer


PROPANONE = """molecule:
  name: Propanone (acetone)
  atoms:
    - {id: c1, element: C}
    - {id: c2, element: C}
    - {id: o1, element: O}
    - {id: c3, element: C}
  bonds:
    - {from: c1, to: c2, order: single}
    - {from: c2, to: o1, order: double}
    - {from: c2, to: c3, order: single}
"""


def render(body: str) -> str | None:
    return HtmlRenderer._render_molecule(body)


def test_propanone_shows_each_carbon_oxygen_and_implicit_hydrogen() -> None:
    result = render(PROPANONE)

    assert result is not None
    assert 'formula-expanded' in result
    assert result.count('class="atom atom-C"') == 3
    assert result.count('class="atom atom-O"') == 1
    assert result.count('class="atom atom-H implicit-hydrogen"') == 6
    assert result.count('bond-implicit-h"') == 6
    assert "C<sub>3</sub>H<sub>6</sub>O" in result
    assert "Propanone (acetone)" in result


def test_double_bond_lines_are_separated_and_stop_at_atom_labels() -> None:
    result = render(PROPANONE)
    assert result is not None
    assert result.count('class="bond bond-double"') == 2
    assert 'margin:0 auto' in result
    assert "xmlns=" not in result


def test_single_double_and_triple_bonds_keep_distinct_svg_strokes() -> None:
    result = render("""molecule:
  atoms:
    - {id: c1, element: C}
    - {id: c2, element: C}
    - {id: c3, element: C}
    - {id: c4, element: C}
  bonds:
    - {from: c1, to: c2, order: double}
    - {from: c2, to: c3, order: single}
    - {from: c3, to: c4, order: triple}
""")

    assert result is not None
    assert result.count('class="bond bond-double"') == 2
    assert result.count('class="bond bond-single"') == 1
    assert result.count('class="bond bond-triple"') == 3
    assert result.count('class="atom atom-C"') == 4


def test_branched_molecule_formula_and_explicit_hydrogens() -> None:
    result = render("""molecule:
  atoms:
    - {id: c1, element: C}
    - {id: c2, element: C}
    - {id: c3, element: C}
    - {id: c4, element: C}
  bonds:
    - {from: c1, to: c2, order: single}
    - {from: c2, to: c3, order: single}
    - {from: c2, to: c4, order: single}
""")

    assert result is not None
    assert "C<sub>4</sub>H<sub>10</sub>" in result
    assert result.count('class="atom atom-H implicit-hydrogen"') == 10


def test_invalid_valence_and_legacy_formula_text_are_safe() -> None:
    invalid = render("""molecule:
  atoms:
    - {id: c1, element: C}
    - {id: c2, element: C}
    - {id: c3, element: C}
  bonds:
    - {from: c1, to: c2, order: triple}
    - {from: c1, to: c3, order: double}
""")

    assert invalid is not None and 'class="formula-molecule-error"' in invalid
    assert render(r"2H_2 + O_2 \rightarrow 2H_2O") is None
