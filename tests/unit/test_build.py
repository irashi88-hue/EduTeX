"""Unit tests for the Build System public contracts."""


def test_public_build_api_exports_contract():
    import edutex.build as public_build
    from edutex.build.html_renderer import HtmlRenderer
    from edutex.build.renderer import LatexRenderer
    from edutex.build.service import BuildService

    expected = {
        "BuildService": BuildService,
        "HtmlRenderer": HtmlRenderer,
        "LatexRenderer": LatexRenderer,
    }

    for name, expected_value in expected.items():
        assert getattr(public_build, name) is expected_value
        assert name in public_build.__all__


def test_build_service_contract_requires_build():
    import pytest

    from edutex.build import BuildService
    from edutex.core.errors import BuildError

    service = BuildService()

    for attribute in ("output_path", "tex_source", "html_source"):
        with pytest.raises(BuildError, match="build"):
            getattr(service, attribute)

def test_build_service_clears_stale_artifacts_on_failure(tmp_path, monkeypatch):
    import pytest
    from types import SimpleNamespace

    import edutex.build.service as build_service_module
    from edutex.configuration import EduTexConfig
    from edutex.core.errors import BuildError
    from edutex.build import BuildService

    class FakeHtmlRenderer:
        calls = 0

        def render(self, *, doc, meta, theme):
            if self.calls:
                raise RuntimeError("synthetic renderer failure")
            type(self).calls += 1
            return "<!doctype html><html><body>ok</body></html>"

    monkeypatch.setattr(
        build_service_module,
        "HtmlRenderer",
        FakeHtmlRenderer,
    )

    config = EduTexConfig.model_validate(
        {
            "edutex": {"version": "0.3.0"},
            "knowledge": {"model": "knowledge.md"},
            "theme": {"name": "default"},
            "layout": {"name": "default"},
            "build": {
                "output_format": "html",
                "output_dir": "output",
                "output_file": "result",
            },
        }
    )

    knowledge = SimpleNamespace(meta=object())
    theme = SimpleNamespace(theme_model=object())
    layout = SimpleNamespace(document=object())

    service = BuildService()
    service.build(config, knowledge, theme, layout, tmp_path)

    assert service.output_path == tmp_path / "output" / "result.html"
    assert service.html_source.startswith("<!doctype html>")

    with pytest.raises(BuildError, match="HTML rendering failed"):
        service.build(config, knowledge, theme, layout, tmp_path)

    for attribute in ("output_path", "tex_source", "html_source"):
        with pytest.raises(BuildError, match="build"):
            getattr(service, attribute)
