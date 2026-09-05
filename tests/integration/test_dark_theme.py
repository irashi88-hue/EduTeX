from pathlib import Path

import yaml
from click.testing import CliRunner

from edutex.core.cli import main


def test_dark_theme_html_and_latex(tmp_path: Path) -> None:
    project = tmp_path / "dark-project"
    runner = CliRunner()
    result = runner.invoke(main, ["init", str(project), "--theme", "dark", "--language", "it"])
    assert result.exit_code == 0, result.output

    result = runner.invoke(main, ["build", "--project", str(project)])
    assert result.exit_code == 0, result.output
    html = (project / "output" / "document.html").read_text(encoding="utf-8")
    palette = yaml.safe_load(
        (project / "assets" / "themes" / "dark" / "theme.yaml").read_text(encoding="utf-8")
    )["palette"]
    assert palette["canvas"] in html
    assert palette["ink"] in html
    assert f'<html lang="it">' in html

    config_path = project / "edutex.config.yaml"
    config = config_path.read_text(encoding="utf-8")
    config_path.write_text(
        config.replace('output_format: "html"', 'output_format: "latex"'), encoding="utf-8"
    )
    result = runner.invoke(main, ["build", "--project", str(project)])
    assert result.exit_code == 0, result.output
    latex = (project / "output" / "document.tex").read_text(encoding="utf-8")
    assert "PageBackground" in latex
    assert "DocumentInk" in latex
    assert palette["page_bg"].lstrip("#").upper() in latex
    assert palette["ink"].lstrip("#").upper() in latex
