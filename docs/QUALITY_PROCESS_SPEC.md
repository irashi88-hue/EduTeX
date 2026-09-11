---
document_id:      PROC-QUALITY-001
title:            EduTeX Local Quality Validation Process
type:             Process Specification
version:          1.0.0
status:           Draft
owner:            EduTeX Project
level:            2
parent:           SPECIFICATION_STANDARD.md
normative_refs:
  - SPECIFICATION_STANDARD.md
  - STYLE_GUIDE.md
  - BUILD_SYSTEM_SPEC.md
informative_refs:
  - SHORTCODE_SPEC.md
  - CORE_SPEC.md
---

# EduTeX Local Quality Validation Process

---

# 1. Purpose

This document defines the local quality validation process for the EduTeX project.

The process provides a repeatable verification step for source compilation, automated tests and public command-line contracts.

The process is intended to detect regressions before changes are integrated into the project checkout.

---

# 2. Intended Audience

This document is intended for:

- EduTeX contributors changing framework code;
- maintainers reviewing changes to the processing pipeline;
- authors maintaining the local development environment;
- tooling authors integrating EduTeX checks into CI systems.

---

# 3. Scope

## 3.1 In Scope

This process covers:

- Python source compilation;
- execution of the configured pytest suite;
- verification of the public `edutex` command-line interface;
- verification of standalone shortcode lint output;
- verification of the opt-in `edutex build --lint` preflight;
- reporting of deterministic pass and failure results.

## 3.2 Out of Scope

This process does not define:

- renderer implementation;
- shortcode semantics;
- release versioning;
- package publication;
- CI-provider configuration;
- network-based dependency installation;
- automatic correction of source files.

---

# 4. Normative References

| Document | Role |
|---|---|
| `SPECIFICATION_STANDARD.md` | Normative |
| `STYLE_GUIDE.md` | Normative |
| `BUILD_SYSTEM_SPEC.md` | Normative |

---

# 5. Overview

The process is implemented by a repository-local quality command.

The command is executed from the project root and uses the active Python interpreter.

The command executes checks in a deterministic order and stops after the first failed check.

The process does not install dependencies or use network services.

The process does not modify Knowledge Models, configuration files or existing build outputs.

The implementation support for this process is `tools/quality_check.py`.

The implementation file is an operational tool and is not itself an architectural specification.

---

# 6. Responsibilities

## 6.1 Process Runner

The process runner SHALL determine the repository root from its own location.

The process runner SHALL use `pathlib.Path` for repository and asset paths.

The process runner SHALL preserve the active Python environment when invoking subprocesses.

The process runner SHALL capture standard output and standard error for diagnostics.

The process runner SHALL return exit code `0` only when all required checks pass.

The process runner SHALL return a non-zero exit code when a required check fails.

The process runner SHALL NOT install packages or call network services.

## 6.2 Repository Checks

The quality process SHALL compile Python files under `src`, `tests` and `tools`.

The quality process SHALL execute the configured command `python -m pytest -q`.

The quality process SHALL verify the public commands `init`, `lint`, `build` and `validate`.

The quality process SHALL verify the `lint --format json` contract on a temporary invalid source file.

The quality process SHALL verify blocking and non-blocking `build --lint` paths on temporary projects.

---

# 7. Quality Checks

## QL-001 — Python Compilation

The process SHALL compile Python files under `src`, `tests` and `tools` without treating generated cache files as source inputs.

The process SHALL report the source path when compilation fails.

The process SHALL perform this check before subprocess-based checks.

---

## QL-002 — Test Suite

The process SHALL execute the project's configured pytest suite through the active Python interpreter.

A non-zero pytest exit code SHALL fail the quality process.

The process SHALL preserve pytest output in the failure diagnostic.

---

## QL-003 — Shortcode Lint Contract

The process SHALL execute the standalone lint command on a valid temporary Knowledge Model.

The valid source check SHALL complete with exit code `0`.

The process SHALL execute the JSON lint command on an invalid temporary Knowledge Model.

The invalid source check SHALL complete with a non-zero exit code.

The JSON output SHALL be decodable and SHALL contain `valid: false` and a diagnostic code.

---

## QL-004 — Build Lint Preflight

The process SHALL create a temporary project through the public `init` command.

The process SHALL verify that an error in `build --lint` blocks the build before output generation.

The process SHALL verify that a warning in `build --lint` does not block a successful build.

The process SHALL verify that a build without `--lint` remains executable as the normal build path.

Temporary projects SHALL be removed after the check completes.

---

## QL-005 — CLI Contract

The process SHALL verify the help output for the public commands.

The process SHALL verify that `init --help` exposes `--theme` and `--language`.

The process SHALL verify that `lint --help` exposes `--format`.

The process SHALL verify that `build --help` exposes `--lint`.

The process SHALL verify that `validate --help` exposes `--project` and `--config`.

---

# 8. Interfaces

## 8.1 Quality Command

The local quality command SHALL be invoked from the repository root with:

```powershell
python tools\quality_check.py
```

The command MAY be invoked with verbose diagnostics:

```powershell
python tools\quality_check.py --verbose
```

With `--json`, the command SHALL emit only a JSON report using schema
`edutex.quality-baseline.v1`, suitable for CI consumers. The report SHALL
include completed and expected check counts, ordered check results, return
codes, diagnostic details, and the first failed check when present.

The command SHALL return exit code `0` when the quality process passes.

The command SHALL return exit code `1` when a required check fails.

## 8.2 Direct Test Command

The project test suite SHALL remain directly executable with:

```text
python -m pytest -q
```

The quality command SHALL NOT replace the direct test command.

---

# 9. Dependencies

| Dependency | Type | Purpose |
|---|---|---|
| Active Python interpreter | Runtime | Execute the quality command and project CLI |
| Configured pytest installation | Development | Execute the project test suite |
| EduTeX CLI | Project interface | Verify public commands and lint/build behavior |
| Temporary filesystem | Operating system | Isolate generated test projects and source files |

---

# 10. Constraints

The process SHALL work with Windows and POSIX path conventions.

The process SHALL use the active interpreter rather than assuming a system-wide executable name.

The process SHALL use UTF-8 when reading and writing temporary source files.

The process SHALL avoid hard-coded path separators in Python path operations.

The process SHALL not alter the configured project version.

The process SHALL not require a LaTeX compiler for lint-only checks.

The process SHALL not make the normal `edutex build` path dependent on the quality command.

---

# 11. Verification

A contributor SHALL run the quality command after changing the CLI, linter, build preflight or related tests.

A reviewer SHOULD inspect the named check output when the process fails.

A change SHALL NOT be considered quality-validated when the quality command returns a non-zero exit code.

The direct pytest suite SHALL also be run when a change modifies test configuration or test discovery.

---

# 12. Future Evolution

Future process revisions MAY add a CI-provider adapter.

Future process revisions MAY add coverage reporting after a project-level coverage target is approved.

Future process revisions MAY add static analysis tools after their configuration is defined by a separate process or component specification.

The quality command SHOULD remain independent from release packaging.

---

# 13. References

The process implementation is `tools/quality_check.py`.

The shortcode contract is defined by `SHORTCODE_SPEC.md`.

The build responsibilities are defined by `BUILD_SYSTEM_SPEC.md`.

---

# 14. Change History

| Version | Date | Description |
|---|---|---|
| 1.0.0 | 2026-09-08 | Initial draft defining local quality validation for source, tests and CLI contracts |

---

*End of document.*

## Q006 Course management contract

The course-management quality check creates an isolated temporary course and verifies:

- `course validate --format json` returns a valid manifest with the configured presentation theme;
- HTML builds produce the course index and every declared lesson page;
- disabled presentation blocks remain absent from the generated index;
- LaTeX builds produce `output/course.tex`;
- PDF builds are verified when `latexmk` or `pdflatex` is available, otherwise the PDF sub-check is reported as skipped rather than treated as a code failure.

The temporary fixture includes project assets and `edutex.config.yaml`, matching the official lesson build path.



## QL-007 — PDF/LaTeX Accessibility Contract

The process SHALL build a temporary course in LaTeX format and inspect the generated `.tex` source.

The source SHALL contain the configured text-mapping, Unicode, bookmark, and PDF metadata markers exposed by the course renderer.

When `latexmk` or `pdflatex` is available, the process SHALL also build the PDF.

When a PDF is built, the process SHALL run `qpdf --check` when `qpdf` is available and SHALL run `pdftotext` when `pdftotext` is available. Extracted text SHALL contain the course title.

When no LaTeX compiler is available, the source contract SHALL pass and the compiled-PDF sub-check SHALL be reported as skipped rather than treated as a code failure.

## QL-008 — Compiled PDF Runtime Gates

When QL-007 finds a supported LaTeX compiler, the runtime contract SHALL use
`latexmk`, `pdflatex`, or `xelatex` according to the course language and SHALL
verify that the expected PDF file exists.

For a compiled PDF, the process SHALL:

- run `qpdf --check` when available;
- extract text with `pdftotext` when available and require the course title;
- inspect `Title`, `Author`, and `Subject` with `pdfinfo` when available;
- load the file with `pypdf` when available;
- render the first page with `pdftoppm` when available.

Missing optional inspection tools do not fail the check; a failed tool that is
present does fail the runtime contract. Missing LaTeX compilers continue to
skip only the compiled-PDF portion.

## QL-009 — PDF Tool Diagnostics

The quality runner SHALL expose a stable runtime summary containing the
language, selected compiler, and availability of `latexmk`, `pdflatex`,
`xelatex`, `qpdf`, `pdftotext`, `pdfinfo`, and `pdftoppm`.

The summary SHALL distinguish the compiler gate from optional inspection tools.
A missing compiler SHALL explain why compiled-PDF checks were skipped; it SHALL
not hide the availability of downstream inspection tools. The compact
`pdf_runtime_summary(language)` view SHALL be derived from the structured report
and SHALL expose the same language, compiler readiness, required compiler tools,
compiled-PDF status, inspection-gate statuses, and missing structural gates.

The summary is intended for verbose diagnostics and CI environment reports and
MUST NOT install or download tools.

## QL-010 — Structured PDF Runtime Report

The quality runner SHALL expose `pdf_runtime_report(language)` as a JSON-safe
report with schema identifier `edutex.pdf-runtime.v1`.

The report SHALL include:

- requested language and normalized language code;
- selected compiler and compiler readiness;
- required compiler tools for standard or CJK output;
- compiled-PDF status (`ready` or `skipped_no_compiler`);
- whether any inspection gate is available;
- `inspection_gates`, with availability, role, and status for `qpdf`,
  `pdftotext`, `pdfinfo`, `pdftoppm`, and the optional `pypdf` parser;
- each known command-line tool's availability, executable path, role, and
  version when version probing succeeds;
- `missing_gates`, listing unavailable structural validation gates such as
  `qpdf` without treating optional-tool absence as a compiler failure.

When a compiled PDF is available, Q007 SHALL report the effective gate results
using statuses such as `passed`, `failed`, `skipped_unavailable`, or
`passed_or_unavailable` for the optional parser. A missing optional tool SHALL
be visible as skipped/unavailable rather than silently omitted.

Version probing SHALL use the executable's supported version convention and
MUST NOT make a missing or incompatible version flag a quality failure. For
`latexmk`, the report SHALL ignore wrapper or Perl initialization lines and
normalize a later semantic line such as `Latexmk: This is Latexmk, John
Collins, 4.85.` to `latexmk version 4.85`.

The report is intended for JSON diagnostics and MUST remain read-only: it does
not install tools, mutate PATH, or change project files.
## QL-011 - Compiled PDF Gate Testability

The compiled-PDF inspection phase SHALL be isolated behind a testable internal
helper. The helper SHALL return both an ordered status map and diagnostic
failure messages for `qpdf`, `pdftotext`, `pdfinfo`, `pypdf`, and `pdftoppm`.

Tests SHALL cover at least:

- all optional tools unavailable, with no failure reported;
- all available gates passing, including text, metadata, and render checks;
- a failing structural gate whose command diagnostics remain visible.

These tests MAY use simulated subprocess results and SHALL NOT require a local
LaTeX compiler or a valid PDF fixture.
## QL-012 - pypdf Parser Diagnostics

The optional `pypdf` parser gate SHALL expose an explicit status and diagnostic:

- `passed` when the PDF is loaded and its language contract passes;
- `failed` when `pypdf` is available but parsing or language validation fails;
- `skipped_unavailable` when the optional package is not installed.

The compiled-PDF inspection helper SHALL accept an `expected_language` keyword
argument. Its default SHALL remain `en-US` for backward compatibility. Q007
SHALL pass the normalized course language to the helper rather than embedding a
language literal in the parser gate. The normalization SHALL map the short
English course code `en` to the historical PDF tag `en-US` and SHALL preserve
explicit non-English tags such as `it-IT` or `ja`.

Tests SHALL cover a matching configurable non-English language, a mismatch
diagnostic, and the default English behavior.

The structured runtime report SHALL identify the parser role and include a
JSON-safe diagnostic field. Missing `pypdf` remains non-blocking, while an
actual parser failure on an available installation SHALL remain a Q007 failure.
## QL-013 - JSON Quality Baseline Output

The quality runner SHALL expose a `--json` mode for CI integrations. The mode
SHALL emit a JSON-safe report with schema identifier
`edutex.quality-baseline.v1` and SHALL NOT mix human-readable status lines into
stdout.

The report SHALL include the overall result, completed and expected check
counts, the first failed check when present, and each completed check's name,
pass/fail state, return code, and diagnostic detail. The default text mode and
exit-code behavior SHALL remain unchanged.
## QL-014 - Runtime Summary and Report Alignment

The compact runtime summary SHALL remain JSON-safe and backward-compatible for
its existing fields. It SHALL additionally expose the normalized language code,
compiler readiness, required compiler tools, compiled-PDF status, per-gate
statuses, and missing structural gates by deriving them from
`pdf_runtime_report(language)`.

The summary SHALL NOT independently probe tools or calculate statuses, so a
consumer cannot receive contradictory compiler or inspection information from
the two APIs.

