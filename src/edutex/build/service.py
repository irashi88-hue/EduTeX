"""
EduTeX Build Service
Component: Build System (MECH-BUILD-001)
Contracts: BUILD-001 (Build Contract), BUILD-002 (Build Output Contract)

Orchestrates the Build stage â€” the terminal stage of the Processing Model.
Consumes DocumentStructure (LAYOUT-001), ThemeModel (THEME-002),
and KnowledgeModelMeta (KNOW-002) to produce the final output.

Responsibilities:
  - Render the DocumentStructure to LaTeX source via the LatexRenderer.
  - Write the .tex file to the output directory.
  - Invoke latexmk to compile the PDF (when available).
  - Expose the output path through BUILD-001.

Build SHALL NOT own educational content, visual styling, or document structure.
These are owned by Knowledge, Theme, and Layout respectively.
"""

from __future__ import annotations

import re
import subprocess
import shutil
from pathlib import Path

from edutex.build.html_renderer import HtmlRenderer
from edutex.build.renderer import LatexRenderer
from edutex.configuration.schema import EduTexConfig, OutputFormat
from edutex.core.errors import BuildError
from edutex.knowledge.service import KnowledgeService
from edutex.layout.models import DocumentStructure
from edutex.layout.service import LayoutService
from edutex.theme.service import ThemeService


class BuildService:
    """
    Build Service â€” orchestrates the Build stage (MECH-BUILD-001).

    Usage:
        service = BuildService()
        service.build(config, knowledge, theme, layout, project_root)
        print(service.output_path)   # BUILD-001
    """

    def __init__(self) -> None:
        self._output_path: Path | None = None
        self._tex_source:  str  | None = None
        self._html_source: str  | None = None

    # ------------------------------------------------------------------
    # BUILD-001 â€” Build Contract
    # ------------------------------------------------------------------

    @property
    def output_path(self) -> Path:
        """Path to the final output file (BUILD-001)."""
        if self._output_path is None:
            raise BuildError("Output path is not available â€” build() has not been called.")
        return self._output_path

    @property
    def tex_source(self) -> str:
        """The generated LaTeX source (BUILD-002)."""
        if self._tex_source is None:
            raise BuildError("LaTeX source is not available â€” build() has not been called.")
        return self._tex_source

    @property
    def html_source(self) -> str:
        """The generated HTML source (BUILD-002)."""
        if self._html_source is None:
            raise BuildError("HTML source is not available â€” build() has not been called.")
        return self._html_source

    # ------------------------------------------------------------------
    # Build entry point
    # ------------------------------------------------------------------

    def build(
        self,
        config: EduTexConfig,
        knowledge: KnowledgeService,
        theme: ThemeService,
        layout: LayoutService,
        project_root: Path,
        document: DocumentStructure | None = None,
    ) -> None:
        """
        Execute the Build stage.

        Args:
            config:       Validated framework configuration (CFG-001).
            knowledge:    Completed Knowledge Service (KNOW-001, KNOW-002).
            theme:        Completed Theme Service (THEME-001, THEME-002).
            layout:       Completed Layout Service (LAYOUT-001, LAYOUT-002).
            project_root: Project root directory.
            document:     Optional post-extension document structure. When
                          omitted, the Layout Service document is used.

        Raises:
            BuildError: If rendering or compilation fails (CC-003).
        """
        output_dir  = project_root / config.build.output_dir
        output_file = config.build.output_file
        output_fmt  = config.build.output_format

        # A BuildService instance may be reused; never expose a stale artifact.
        self._output_path = None
        self._tex_source = None
        self._html_source = None

        output_dir.mkdir(parents=True, exist_ok=True)

        document_to_render = document if document is not None else layout.document

        if output_fmt == OutputFormat.html:
            try:
                html_source = HtmlRenderer().render(
                    doc=document_to_render,
                    meta=knowledge.meta,
                    theme=theme.theme_model,
                )
            except Exception as exc:
                raise BuildError(f"HTML rendering failed: {exc}") from exc
            self._html_source = html_source
            html_path = output_dir / f"{output_file}.html"
            html_path.write_text(html_source, encoding="utf-8")
            self._output_path = html_path
            return

        # Step 1 â€” render DocumentStructure to LaTeX source
        try:
            tex_source = LatexRenderer().render(
                doc=document_to_render,
                meta=knowledge.meta,
                theme=theme.theme_model,
            )
        except Exception as exc:
            raise BuildError(f"LaTeX rendering failed: {exc}") from exc

        self._tex_source = tex_source

        # Step 2 â€” write .tex file
        tex_path = output_dir / f"{output_file}.tex"
        tex_path.write_text(tex_source, encoding="utf-8")

        if output_fmt == OutputFormat.latex:
            self._output_path = tex_path
            return

        # Step 3 â€” compile PDF via latexmk (if available)
        if output_fmt == OutputFormat.pdf:
            self._output_path = self._compile_pdf(
                tex_path,
                output_dir,
                output_file,
                language=getattr(knowledge.meta, "language", "en"),
            )
        else:
            self._output_path = tex_path

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _compile_pdf(
        self, tex_path: Path, output_dir: Path, output_file: str, language: object = "en"
    ) -> Path:
        """
        Compile the generated LaTeX source to PDF.

        ``latexmk`` is preferred because it manages auxiliary passes. If it is
        unavailable, ``pdflatex`` is used directly. A PDF build never falls
        back silently to a .tex path: the requested output contract is PDF.
        """
        language_code = str(language or "en").lower().replace("_", "-").split("-", 1)[0]
        tex_source = tex_path.read_text(encoding="utf-8")
        contains_cjk = bool(
            re.search(
                r"[\u3040-\u30ff\u3400-\u4dbf\u4e00-\u9fff\uf900-\ufaff\uac00-\ud7af]",
                tex_source,
            )
        )
        requires_cjk = language_code in {"ja", "zh", "ko"} or contains_cjk
        if requires_cjk:
            if shutil.which("latexmk") and shutil.which("xelatex"):
                command = ["latexmk", "-xelatex", "-interaction=nonstopmode", "-halt-on-error", "-outdir=" + str(output_dir), str(tex_path)]
                compiler_name = "latexmk (XeLaTeX)"
            elif shutil.which("xelatex"):
                command = ["xelatex", "-interaction=nonstopmode", "-halt-on-error", "-output-directory=" + str(output_dir), str(tex_path)]
                compiler_name = "xelatex"
            elif shutil.which("latexmk") and shutil.which("lualatex"):
                command = ["latexmk", "-lualatex", "-interaction=nonstopmode", "-halt-on-error", "-outdir=" + str(output_dir), str(tex_path)]
                compiler_name = "latexmk (LuaLaTeX)"
            elif shutil.which("lualatex"):
                command = ["lualatex", "-interaction=nonstopmode", "-halt-on-error", "-output-directory=" + str(output_dir), str(tex_path)]
                compiler_name = "lualatex"
            else:
                raise BuildError(
                    "PDF compilation for Japanese/CJK documents requires 'xelatex' "
                    "or 'lualatex' (directly or through latexmk), but none was found "
                    "in PATH. The .tex source was generated at: "
                    f"{tex_path}"
                )
        elif shutil.which("latexmk"):
            command = ["latexmk", "-pdf", "-interaction=nonstopmode", "-halt-on-error", "-outdir=" + str(output_dir), str(tex_path)]
            compiler_name = "latexmk"
        elif shutil.which("pdflatex"):
            command = ["pdflatex", "-interaction=nonstopmode", "-halt-on-error", "-output-directory=" + str(output_dir), str(tex_path)]
            compiler_name = "pdflatex"
        else:
            raise BuildError(
                "PDF compilation requires 'latexmk' or 'pdflatex', but neither "
                "was found in PATH. Install a LaTeX distribution (for example "
                "MiKTeX or TeX Live) and retry. The .tex source was generated at: "
                f"{tex_path}"
            )

        try:
            result = subprocess.run(
                command,
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace",
                timeout=120,
            )
        except subprocess.TimeoutExpired as exc:
            raise BuildError(f"{compiler_name} compilation timed out.") from exc
        except OSError as exc:
            raise BuildError(f"Could not start {compiler_name}: {exc}") from exc

        if result.returncode != 0:
            diagnostics = (result.stderr or result.stdout)[-3000:]
            raise BuildError(
                f"{compiler_name} compilation failed (exit {result.returncode}):\n"
                f"{diagnostics}"
            )

        pdf_path = output_dir / f"{output_file}.pdf"
        if not pdf_path.exists():
            raise BuildError(
                f"{compiler_name} completed successfully but PDF was not found at: "
                f"{pdf_path}"
            )

        return pdf_path
