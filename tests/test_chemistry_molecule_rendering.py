"""Contract tests for simple structured molecule rendering."""

from edutex.build.html_renderer import HtmlRenderer


def render(body: str) -> str | None:
    return HtmlRenderer._render_molecule(body)


def test_renders_branched_carbon_tree_and_derived_formula() -> None:
    rendered = render("""molecule:
  name: 2-methylpropane
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

    assert rendered is not None
    assert 'class="bond bond-single"' in rendered
    assert rendered.count('class="bond bond-single"') == 3
    assert rendered.count('class="bond bond-single bond-implicit-h"') == 10
    assert rendered.count('<line ') == 13
    assert "C<sub>4</sub>H<sub>10</sub>" in rendered
    assert "2-methylpropane" in rendered


def test_renders_double_and_triple_bonds_as_parallel_svg_lines() -> None:
    rendered = render("""molecule:
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

    assert rendered is not None
    assert rendered.count('class="bond bond-double"') == 2
    assert rendered.count('class="bond bond-triple"') == 3
    assert rendered.count('class="bond bond-single"') == 1
    assert "C<sub>4</sub>H<sub>4</sub>" in rendered


def test_renders_heteroatoms_and_escapes_molecule_name() -> None:
    rendered = render("""molecule:
  name: '<script>alert(1)</script>'
  atoms:
    - {id: c1, element: C}
    - {id: c2, element: C}
    - {id: o1, element: O}
  bonds:
    - {from: c1, to: c2, order: single}
    - {from: c2, to: o1, order: single}
""")

    assert rendered is not None
    assert ">O</text>" in rendered
    assert "C<sub>2</sub>H<sub>6</sub>O" in rendered
    assert "&lt;script&gt;" in rendered
    assert "<script>" not in rendered


def test_rejects_cycles_and_broken_valence_with_safe_visible_message() -> None:
    cycle = render("""molecule:
  atoms:
    - {id: c1, element: C}
    - {id: c2, element: C}
    - {id: c3, element: C}
  bonds:
    - {from: c1, to: c2, order: single}
    - {from: c2, to: c3, order: single}
    - {from: c3, to: c1, order: single}
""")
    invalid_valence = render("""molecule:
  atoms:
    - {id: c1, element: C}
    - {id: c2, element: C}
    - {id: c3, element: C}
  bonds:
    - {from: c1, to: c2, order: triple}
    - {from: c1, to: c3, order: double}
""")

    assert cycle is not None and 'class="formula-molecule-error"' in cycle
    assert invalid_valence is not None and 'class="formula-molecule-error"' in invalid_valence


def test_legacy_formula_text_is_not_claimed_as_a_molecule() -> None:
    assert render(r"2H_2 + O_2 \\rightarrow 2H_2O") is None
