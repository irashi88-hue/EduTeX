"""Focused tests for common chemical notation in generated HTML."""

from edutex.build.html_renderer import HtmlRenderer


def test_html_chemistry_renders_reaction_arrow_and_subscripts() -> None:
    rendered = HtmlRenderer._render_chemistry(
        r"2H_2 + O_2 \rightarrow 2H_2O"
    )

    assert rendered == (
        "2H<sub>2</sub> + O<sub>2</sub> &#8594; "
        "2H<sub>2</sub>O"
    )


def test_html_chemistry_renders_equilibrium_arrows_and_charges() -> None:
    rendered = HtmlRenderer._render_chemistry(
        r"SO_{4}^{2-} \rightleftharpoons H^+ + SO_4^{2-}"
    )

    assert rendered == (
        "SO<sub>4</sub><sup>2-</sup> &#8652; "
        "H<sup>+</sup> + SO<sub>4</sub><sup>2-</sup>"
    )


def test_html_chemistry_renders_short_arrow_alias_and_heat_symbol() -> None:
    rendered = HtmlRenderer._render_chemistry(
        r"A \Delta -> B"
    )

    assert rendered == "A &#916; &#8594; B"


def test_html_chemistry_does_not_unescape_html_input() -> None:
    rendered = HtmlRenderer._render_chemistry(
        "&lt;script&gt;alert(1)&lt;/script&gt; \\rightarrow"
    )

    assert rendered == "&lt;script&gt;alert(1)&lt;/script&gt; &#8594;"
