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

The quality process SHALL verify the source packaging contract for the CLI entrypoint and public command surface.

---

# 7. Quality Checks

## QL-001 — Python Compilation

The process SHALL compile Python files under `src`, `tests` and `tools` without treating generated cache files as source inputs.

The quality runner SHALL expose an ordered `quality_check_catalog()` containing
the stable ID, public name, description, and required flag for every Q001-Q008
check. The catalog order SHALL match the execution order and the existing
`check_names()` result. Each check in the current baseline SHALL be required.

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

The public CLI contract SHALL be represented by one ordered, testable definition
used by Q005 and exposed through `public_cli_contract()`. The contract SHALL
include the following required commands and options:

- top-level help: `init`, `lint`, `build`, and `validate`;
- `init --help`: `--theme` and `--language`;
- `lint --help`: `--format`;
- `build --help`: `--lint`;
- `validate --help`: `--project` and `--config`.

The contract order SHALL remain stable because it is used for deterministic
diagnostics and release regression tests. Adding a new public option SHALL be
an explicit contract change, not an accidental change to the quality runner.

---

# 8. Interfaces

## 8.1 Quality Command

The public CLI contract is independent from the quality command itself. The
quality runner SHALL use the same contract definition for Q005 and SHALL report
which command or option is missing when the check fails.

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
counts, the ordered check catalog, the first failed check when present, and each
completed check's stable ID, name, pass/fail state, return code, and diagnostic
detail. The
`check_catalog` field SHALL be derived from `quality_check_catalog()` and SHALL
identify every expected check, including checks that did not run because an
earlier required check failed.

The completed result names SHALL form an ordered prefix of the catalog. The
quality runner SHALL expose `quality_baseline_catalog_diagnostics(results)` and
report additive fields `catalog_consistent` and `catalog_diagnostics`. Unknown,
duplicated, or out-of-order results SHALL make the baseline `failed`, even when
the individual result values are marked as passed. A valid shorter prefix SHALL
remain `incomplete`, not `failed`.

The quality runner SHALL also expose an ordered `quality_check_execution_plan()`
and `quality_check_execution_diagnostics()`. The plan IDs SHALL match the
catalog IDs exactly, including order and count. Execution-plan drift SHALL make
the baseline `failed` and SHALL be reported separately through additive fields
`execution_consistent` and `execution_diagnostics`.

Each completed entry in `checks` SHALL include the additive field `status`.
The value SHALL be `passed` when the existing boolean field `passed` is true and
`failed` otherwise. The existing `passed` boolean SHALL remain authoritative for
backward-compatible consumers; `status` is a normalized textual representation
for CI integrations.

The report SHALL expose the additive per-result field `id`, derived from the
quality catalog. Known results SHALL contain their stable Q001-Q007 ID. An
unknown result MAY contain a null ID, but SHALL already be rejected by the
catalog consistency contract.

The report SHALL expose the additive object `summary`, containing integer
fields `passed`, `failed`, and `pending`. The counts SHALL be derived from the
completed results: `passed` counts completed passing results, `failed` counts
completed failing results, and `pending` equals the number of expected catalog
checks without a completed result, never less than zero. The summary SHALL also
include additive fields `total`, `completed`, and `pass_rate`: `total` is the
number of catalog checks, `completed` is the number of supplied results, and
`pass_rate` is the percentage of completed results that passed, rounded to two
decimal places, or `0.0` when no results are completed. The summary SHALL also
include additive fields `completion_rate` and `failure_rate`: `completion_rate`
is the percentage of catalog checks represented by supplied results, and
`failure_rate` is the percentage of completed results that failed. Both rates
SHALL be rounded to two decimal places and SHALL be `0.0` when their respective
denominator is zero. The summary SHALL be informational and SHALL NOT replace
or alter `status`, `complete`, `exit_code`, or any existing outcome semantics.

The quality runner SHALL expose `quality_baseline_report_diagnostics(report)`
for local and CI-side contract inspection. A report produced by
`quality_baseline_report()` SHALL return no diagnostics. The helper SHALL report
missing summary fields, malformed check entries, missing check identity, and a
mismatch between a check's `passed` boolean and its normalized `status` value.
These diagnostics are observational and SHALL NOT alter the existing report
schema or baseline outcome semantics.

The report SHALL expose the additive field `missing_checks`, containing the
ordered IDs from the catalog for which no completed result exists. A complete
run SHALL report an empty list. An interrupted run SHALL list every check after
the last completed check, while a valid shorter prefix SHALL remain
`incomplete`.

The report SHALL expose the additive fields `status`, `complete`, and
`exit_code`. `status` SHALL be one of `passed`, `failed`, or `incomplete`:

- `passed` means all expected checks completed and passed;
- `failed` means at least one completed check failed;
- `incomplete` means no completed check failed, but fewer than all expected checks
  completed, including an empty result set.

`complete` SHALL be true only for `passed`. `exit_code` SHALL be `0` only for
`passed` and `1` for both `failed` and `incomplete`. The default text mode and
exit-code behavior SHALL remain unchanged.

Each JSON quality report SHALL also include the additive field `failed_check_id`.
When `failed_check` identifies a known catalog result, `failed_check_id` SHALL
contain its stable Q001-Q007 identifier. When there is no failed check, or when
the failed result name is unknown, `failed_check_id` SHALL be null. The existing
human-readable `failed_check` field SHALL remain unchanged.

Each JSON quality report SHALL also include the additive fields `run_finished_at`
and `duration_seconds`. `run_finished_at` SHALL be the UTC finish timestamp for
the quality baseline execution, serialized as RFC 3339 text with a `Z` UTC suffix
and second precision. `duration_seconds` SHALL be a JSON number representing the
elapsed execution duration in seconds and SHALL be non-negative. The command
entrypoint SHALL capture one finish timestamp and one monotonic elapsed duration
after the checks complete. Direct callers of the report helper MAY provide both
fields for deterministic tests; when omitted, the helper SHALL generate the
current UTC finish timestamp and use `0.0` as the compatibility default duration.
Existing schema, fields, check
ordering, outcome semantics, and exit-code behavior SHALL remain unchanged.

Each JSON quality report SHALL also include the additive field `run_started_at`.
The value SHALL be the UTC start timestamp for the quality baseline execution,
serialized as RFC 3339 text with a `Z` UTC suffix and second precision. The
command entrypoint SHALL capture this timestamp once for each invocation and
pass that same value to report construction. Direct callers of the report
helper MAY provide `run_started_at` for deterministic integration tests; when
omitted, the helper SHALL generate the current UTC timestamp. Existing schema,
fields, check ordering, outcome semantics, and exit-code behavior SHALL remain
unchanged.

Each JSON quality report SHALL include the additive field `run_id`. `run_id`
SHALL identify the single quality baseline execution that produced the report
and SHALL be a UUID version 4 string. The command entrypoint SHALL generate the
identifier once per invocation and pass that same value to report construction.
Direct callers of the report helper MAY provide a `run_id` for deterministic
integration tests; when omitted, the helper SHALL generate a UUID version 4
identifier. Existing schema, fields, check ordering, outcome semantics, and
exit-code behavior SHALL remain unchanged.

The quality runner SHALL expose `quality_baseline_status(results)` for local
consumers that need the normalized outcome without parsing the full report.

## QL-014 - Runtime Summary and Report Alignment

The compact runtime summary SHALL remain JSON-safe and backward-compatible for
its existing fields. It SHALL additionally expose the normalized language code,
compiler readiness, required compiler tools, compiled-PDF status, per-gate
statuses, and missing structural gates by deriving them from
`pdf_runtime_report(language)`.

The summary SHALL NOT independently probe tools or calculate statuses, so a
consumer cannot receive contradictory compiler or inspection information from
the two APIs.
---

## QL-015 - Packaging Contract

The quality runner SHALL verify the source files required to publish and invoke
the EduTeX CLI. The check SHALL inspect the checkout under test rather than a
globally installed command.

The packaging contract SHALL require `src/edutex/core/cli.py` and
`pyproject.toml`. The CLI source SHALL contain the supported `init`, `lint`,
`build`, `validate`, and `course` command declarations, the `--theme`,
`--language`, `--lint`, and `--format` options, the structured build-error
helper, and the current CLI version marker. The project metadata SHALL point the
`edutex` console script to `edutex.core.cli:main`.

An obsolete CLI version marker or a missing required marker SHALL fail Q008 and
report the affected file and marker. This check is intentionally static and
shall not install packages, invoke a global executable, or modify project
files.

The packaging contract SHALL remain additive: it SHALL NOT change the runtime
CLI behavior, quality report schema, or existing Q001-Q007 semantics.


---

## QL-016 - Release Metadata Contract

The quality runner SHALL verify that the release metadata identifies one coherent
EduTeX release. The `[project].version` value in `pyproject.toml` SHALL be a
valid semantic version, and `CLI_VERSION` in `src/edutex/core/cli.py` SHALL also
be a valid semantic version with the same value.

The project metadata SHALL expose the console entry point
`edutex = "edutex.core.cli:main"`. Missing, malformed, or mismatched release
versions SHALL fail Q009 with a diagnostic naming the affected metadata. A
missing or mismatched entry point SHALL also fail Q009. The check SHALL inspect
the checkout under test without installing packages or invoking a global command.

Q009 is additive: it does not change the quality report schema, the existing
Q001-Q008 semantics, or runtime CLI behavior.

---

## QL-017 - Quality Report Schema Contract

The quality runner SHALL expose a stable quality-report schema contract. A report
produced by `quality_baseline_report()` SHALL contain the required top-level
fields, per-check fields, and summary fields defined by `quality_report_contract()`.

The report contract SHALL preserve ordered catalog identities, normalized check
statuses, the `missing_checks` list, outcome fields (`status`, `complete`, and
`exit_code`), and the `failed_check_id` correlation field. Complete, failed, and
incomplete reports SHALL remain JSON serializable and SHALL pass
`quality_baseline_report_diagnostics()`.

Q010 SHALL exercise representative complete, failed, and empty reports without
installing packages, accessing the network, or changing runtime behavior. The
existing `edutex.quality-baseline.v1` schema identifier and all prior Q001-Q009
semantics SHALL remain unchanged.

---

## QL-018 - Quality Report Consistency Contract

The quality runner SHALL verify the internal consistency of each public quality
report. The report status, completion flag, exit code, completed and expected
check counts, ordered catalog, check result order, missing-check list, failed
check correlation, and summary counts SHALL agree with the underlying result
sequence and quality catalog.

Q011 SHALL exercise representative complete, failed, and incomplete reports.
The check SHALL preserve the existing `edutex.quality-baseline.v1` schema and
shall not change report fields, runtime behavior, installation behavior, or
network behavior. Existing Q001-Q010 identifiers and semantics SHALL remain
unchanged.

---

## QL-019 - Quality Report Diagnostics Contract

The quality runner SHALL verify that `quality_baseline_report_diagnostics()`
returns no diagnostics for a valid report and deterministic diagnostics for
representative malformed reports. The contract SHALL cover missing top-level
sections, check status drift, missing check identity, and missing summary fields.

Q012 SHALL not change the report schema or runtime behavior. It SHALL preserve
the `edutex.quality-baseline.v1` identifier and all Q001-Q011 semantics, and it
SHALL not install packages, access the network, or invoke a global executable.

---

## QL-020 - Quality Report Value-Types Contract

The quality runner SHALL verify that generated quality reports use stable JSON
value types. Boolean, integer, numeric, string, nullable-string, list, and
object fields SHALL retain their documented types. Duration and rate values SHALL
be numeric and non-negative; boolean values SHALL NOT be accepted as integers.

Q013 SHALL exercise complete, failed, and incomplete reports. It SHALL preserve
the `edutex.quality-baseline.v1` identifier, report fields, runtime behavior,
and all Q001-Q012 semantics. It SHALL not install packages, access the network,
or invoke a global executable.


## QL-021 - Quality Report Identity Contract

The quality process SHALL validate that representative reports use coherent
identifiers and chronology. Each report check identifier SHALL correspond to
its stable catalog name and SHALL remain in catalog order. Completed and missing
check identifiers SHALL be unique and SHALL partition the ordered catalog.

The report SHALL expose a non-empty run identifier. `run_started_at` and
`run_finished_at` SHALL be UTC RFC 3339 strings that can be parsed by the active
Python interpreter, and the finish time SHALL NOT precede the start time.

`failed_check` and `failed_check_id` SHALL be null when no check failed and SHALL
identify the first failed catalog check when a failure is present. The contract
SHALL be additive and SHALL preserve `edutex.quality-baseline.v1` and QL-001
through QL-020.


## QL-022 - Quality Report Catalog Metadata Contract

The quality process SHALL validate the stable metadata projection of the quality
check catalog. Each catalog entry SHALL contain exactly the fields `id`, `name`,
`description`, and `required`; identifiers and names SHALL remain in catalog
order, descriptions SHALL be non-empty strings, and required checks SHALL have
`required: true`.

The `check_catalog` field of complete, failed, and incomplete reports SHALL
match the ordered catalog metadata. Catalog names SHALL map back to their stable
identifiers through `quality_check_id()`. Q015 SHALL be additive and SHALL
preserve `edutex.quality-baseline.v1` and QL-001 through QL-021.

## QL-023 - Quality Report Serialization Contract

The quality process SHALL verify that representative complete, failed, and
incomplete reports serialize as JSON through the active Python interpreter. The
serialized representation SHALL be deterministic for identical input, SHALL use
sorted object keys for the public CLI JSON output, SHALL round-trip through
`json.loads()`, and SHALL end with one newline when emitted by the CLI.

Q016 SHALL be additive. It SHALL preserve `edutex.quality-baseline.v1`, all
report fields, runtime behavior, and QL-001 through QL-022.


## QL-024 - Quality CLI JSON Output Contract

The quality process SHALL verify the public `python tools/quality_check.py
--json` output channel. The command SHALL emit one JSON object on standard
output, SHALL emit no diagnostic text on standard error for the representative
incomplete run, SHALL use the `edutex.quality-baseline.v1` schema, and SHALL
report an exit code aligned with the JSON report's `exit_code` field. The output
SHALL be newline-terminated. The same contract SHALL hold when `--verbose` is
combined with `--json`; verbose diagnostics SHALL NOT contaminate JSON output.

Q017 SHALL be additive and SHALL preserve QL-001 through QL-023, the existing
report fields, and all runtime behavior outside the quality runner.


## QL-025 - Quality Runner Stop-on-Failure Contract

The quality runner SHALL execute checks in the ordered execution plan and SHALL
stop immediately after the first failed check. It SHALL return all results up to
and including that failure, preserving the failed check's name, return code, and
diagnostic detail. When every check passes, it SHALL return every executed
result in order.

Q018 SHALL be additive and SHALL preserve QL-001 through QL-024, the public
report schema, and all runtime behavior outside the quality runner.


## QL-026 - Quality Runner/Report Alignment Contract

The quality process SHALL verify that the public report produced from runner
results remains aligned with the actual execution sequence. When the runner
stops at a first failure, the report SHALL preserve the executed prefix, failed
check identity, return code, and diagnostic detail; checks after the failure
SHALL remain missing.

When every check in a representative execution plan passes, the report SHALL
be complete, SHALL have no missing checks, and SHALL not identify a failed
check. In both scenarios, `quality_baseline_report_diagnostics()` SHALL return
no diagnostics. Q019 SHALL use synthetic plans and SHALL not install packages,
access the network, or invoke a global executable.

Q019 SHALL be additive and SHALL preserve `edutex.quality-baseline.v1`, all
report fields, runtime behavior, and QL-001 through QL-025.


## QL-027 - Quality Report Outcome Contract

The quality process SHALL validate the outcome semantics of generated reports.
A complete report SHALL use `status: "passed"`, `passed: true`,
`complete: true`, `exit_code: 0`, no failed-check identity, and no missing
checks. A report containing a failed check SHALL use `status: "failed"`,
`passed: false`, `complete: false`, and `exit_code: 1`, and SHALL identify the
first failed catalog check.

A report with no failed checks but an incomplete execution SHALL use
`status: "incomplete"`, `passed: false`, `complete: false`, and `exit_code: 1`,
without inventing a failed-check identity. Catalog-inconsistent results SHALL
produce a failed outcome with catalog diagnostics and an exit code of 1.

Q020 SHALL exercise complete, failed, incomplete, and catalog-inconsistent
reports without installing packages, accessing the network, or invoking a global
executable. It SHALL preserve `edutex.quality-baseline.v1`, all report fields,
and QL-001 through QL-026.


## QL-028 - Quality Runner Exception Contract

The quality runner SHALL convert an ordinary exception raised by an executable
check into a failed `CheckResult` instead of allowing the exception to escape
the runner. The generated result SHALL preserve the catalog check identity, use
a non-zero return code, and expose deterministic diagnostic text containing the
exception type and message.

The runner SHALL stop immediately after the converted exception result, and
checks after the raising check SHALL not execute. The resulting report SHALL
remain JSON-safe, SHALL have a failed outcome, and SHALL identify the raising
check through `failed_check_id`. Q021 SHALL use a synthetic execution plan and
SHALL not install packages, access the network, or invoke a global executable.

Q021 SHALL be additive and SHALL preserve `edutex.quality-baseline.v1`, all
report fields, runtime behavior outside exception handling, and QL-001 through
QL-027.


## QL-029 - Quality Runner Identity Contract

The quality runner SHALL verify that each executable plan entry returns a
`CheckResult` whose name matches the stable catalog name for the plan ID. A
result with a mismatched identity SHALL be normalized into a failed result using
the expected catalog name, a non-zero return code, and deterministic diagnostic
text identifying both the expected and returned names.

The runner SHALL stop after the normalized identity mismatch, and checks after
the mismatch SHALL not execute. The resulting report SHALL remain JSON-safe,
SHALL have a failed outcome, and SHALL identify the expected check through
`failed_check_id`. Q022 SHALL use a synthetic execution plan and SHALL not
install packages, access the network, or invoke a global executable.

Q022 SHALL be additive and SHALL preserve `edutex.quality-baseline.v1`, all
report fields, runtime behavior outside identity handling, and QL-001 through
QL-028.


## QL-030 - Quality Runner Return-Code Contract

The quality runner SHALL enforce coherent return-code semantics for each
executed check. A passed result SHALL use return code `0`. A failed result SHALL
use a non-zero return code. A passed result with a non-zero code SHALL be
normalized into a failed result while preserving the non-zero code and exposing
deterministic mismatch diagnostics. A failed result with code `0` SHALL be
normalized to code `1` while preserving its diagnostic detail.

The runner SHALL stop after either normalized return-code mismatch, and the
resulting report SHALL remain JSON-safe and internally diagnostic-free. Q023
SHALL use synthetic execution plans and SHALL not install packages, access the
network, or invoke a global executable.

Q023 SHALL be additive and SHALL preserve `edutex.quality-baseline.v1`, all
report fields, runtime behavior outside return-code normalization, and QL-001
through QL-029.


## QL-031 - Quality Execution-Plan Structure Contract

The quality process SHALL validate the structural integrity of the executable
quality plan. Every plan entry SHALL be a two-item pair containing a known,
unique, non-empty catalog ID and a callable check. Malformed entries, unknown or
duplicate IDs, and non-callable check values SHALL produce deterministic
diagnostics.

The plan diagnostics function SHALL remain safe when the plan cannot be loaded,
and the runner SHALL return a failed result rather than crash when structural
diagnostics are present. Q024 SHALL use synthetic malformed plans and SHALL not
install packages, access the network, or invoke a global executable.

Q024 SHALL be additive and SHALL preserve `edutex.quality-baseline.v1`, all
report fields, runtime behavior outside plan validation, and QL-001 through
QL-030.


## QL-032 - Quality Execution Diagnostics/Report Contract

The quality process SHALL propagate executable-plan diagnostics into the public
quality report. When the plan is structurally invalid, the runner SHALL stop
before invoking checks, return a failed result with the diagnostics as its
detail, and the report SHALL set `execution_consistent: false` while preserving
the diagnostic list verbatim.

Plan diagnostics SHALL NOT be misclassified as catalog diagnostics. The report
SHALL remain JSON-safe and use a failed outcome with exit code 1. Q025 SHALL use
a synthetic malformed plan and SHALL not install packages, access the network,
or invoke a global executable.

Q025 SHALL be additive and SHALL preserve `edutex.quality-baseline.v1`, all
report fields, runtime behavior outside diagnostic propagation, and QL-001
through QL-031.

## QL-033 - Quality Diagnostics Channel Separation Contract

The quality process SHALL preserve catalog diagnostics and executable-plan
diagnostics as independent report channels. Catalog mismatches SHALL be
reported only through `catalog_diagnostics`; execution-plan mismatches SHALL be
reported only through `execution_diagnostics`. Each channel SHALL preserve its
source diagnostic list and deterministic order without duplication or
reclassification.

When both channels contain diagnostics, the report SHALL be failed, SHALL use
exit code `1`, and SHALL set both `catalog_consistent` and
`execution_consistent` to `false`. The report SHALL remain JSON-safe, and
`quality_baseline_report_diagnostics()` SHALL return no diagnostics for this
valid representation of two independent failures. Q026 SHALL use a synthetic
malformed plan and synthetic catalog mismatch without installing packages,
accessing the network, or invoking a global executable.

Q026 SHALL be additive and SHALL preserve `edutex.quality-baseline.v1`, all
report fields, runtime behavior outside diagnostic-channel validation, and
QL-001 through QL-032.

## QL-034 - Quality Report Diagnostic Outcome Contract

The quality process SHALL validate global coherence between report diagnostics
and report outcome fields. A non-empty `catalog_diagnostics` list SHALL imply
`catalog_consistent: false`; a non-empty `execution_diagnostics` list SHALL imply
`execution_consistent: false`.

A report containing diagnostics SHALL use `status: "failed"`,
`passed: false`, `complete: false`, and `exit_code: 1`. The report diagnostic
validator SHALL detect mutations of these relationships with deterministic
diagnostics. A generated report whose diagnostic channels and outcome fields
are coherent SHALL produce no report diagnostics, even when the run failed due
to a catalog or execution inconsistency.

Q027 SHALL use synthetic reports and SHALL not install packages, access the
network, or invoke a global executable. Q027 SHALL be additive and SHALL
preserve `edutex.quality-baseline.v1`, all report fields, runtime behavior
outside report-diagnostic validation, and QL-001 through QL-033.

## QL-035 - Quality Diagnostic Value-Types Contract

The quality process SHALL validate the public diagnostic value types.
`catalog_diagnostics` and `execution_diagnostics` SHALL be lists whose members
are strings. `catalog_consistent` and `execution_consistent` SHALL be boolean
values, not numeric or textual substitutes.

A generated report with valid diagnostic channels SHALL be JSON serializable.
The report diagnostic validator SHALL identify scalar diagnostic channels,
non-string diagnostic members, non-boolean consistency flags, and any
non-serializable diagnostic value with deterministic diagnostics. Q028 SHALL use
synthetic report mutations and SHALL not install packages, access the network,
or invoke a global executable.

Q028 SHALL be additive and SHALL preserve `edutex.quality-baseline.v1`, all
report fields, runtime behavior outside diagnostic value validation, and QL-001
through QL-034.

## QL-036 - Quality Diagnostic Uniqueness Contract

The quality process SHALL require every diagnostic message to be a non-empty
string after whitespace trimming. Each diagnostic channel SHALL contain no
duplicate message, while preserving the source order of distinct messages.

The report diagnostic validator SHALL identify empty messages, whitespace-only
messages, and duplicate messages independently for `catalog_diagnostics` and
`execution_diagnostics`. Distinct messages in a deliberate order SHALL remain
valid and SHALL not be sorted or rewritten. Q029 SHALL use synthetic report
mutations and SHALL not install packages, access the network, or invoke a global
executable.

Q029 SHALL be additive and SHALL preserve `edutex.quality-baseline.v1`, all
report fields, runtime behavior outside diagnostic uniqueness validation, and
QL-001 through QL-035.

## QL-037 - Quality Diagnostic Determinism Contract

The quality process SHALL produce deterministic diagnostic validation. For an
unchanged report input, repeated calls to `quality_baseline_report_diagnostics()`
SHALL return identical diagnostic content and order. Report serialization with
identical input SHALL also be byte-for-byte stable under the public JSON
serialization contract.

Diagnostic validation SHALL not depend on incidental mutation, invocation count,
or unordered collection traversal. Q030 SHALL use synthetic reports, repeated
validator calls, and repeated serialization without installing packages,
accessing the network, or invoking a global executable.

Q030 SHALL be additive and SHALL preserve `edutex.quality-baseline.v1`, all
report fields, runtime behavior outside diagnostic determinism validation, and
QL-001 through QL-036.

## QL-038 - Quality Diagnostic Completeness Contract

The quality process SHALL propagate every source diagnostic into its designated
report channel. Catalog diagnostics SHALL be copied completely into
`catalog_diagnostics`, and execution-plan diagnostics SHALL be copied completely
into `execution_diagnostics`, preserving content and order.

A report with both diagnostic channels SHALL contain the complete concatenation
of the two source lists without omissions, substitutions, or cross-channel
movement. Q031 SHALL use synthetic catalog mismatches and malformed execution
plans without installing packages, accessing the network, or invoking a global
executable.

Q031 SHALL be additive and SHALL preserve `edutex.quality-baseline.v1`, all
report fields, runtime behavior outside diagnostic completeness validation, and
QL-001 through QL-037.

## QL-039 - Quality Diagnostic Channel Isolation Contract

The quality process SHALL isolate catalog diagnostics from executable-plan
diagnostics. A catalog-only inconsistency SHALL leave `execution_diagnostics`
empty and `execution_consistent: true`. An execution-only inconsistency SHALL
leave `catalog_diagnostics` empty and `catalog_consistent: true`.

When both sources are invalid, both channels SHALL be populated independently
without cross-contamination, and the report SHALL use the failed outcome
semantics. Q032 SHALL use synthetic single-source and combined failures without
installing packages, accessing the network, or invoking a global executable.

Q032 SHALL be additive and SHALL preserve `edutex.quality-baseline.v1`, all
report fields, runtime behavior outside diagnostic channel isolation, and
QL-001 through QL-038.

## QL-040 - Quality Diagnostic Provenance Contract

The quality process SHALL preserve the provenance of failures. A genuine failed
check SHALL retain its `failed_check`, `failed_check_id`, return code, and detail
without being represented as catalog or execution-plan diagnostics.

A malformed execution plan SHALL produce execution diagnostics, SHALL not assign
a failed-check identity, and SHALL preserve the runner diagnostic detail in the
report. Diagnostic failures and check failures SHALL both use failed outcome
semantics while remaining distinguishable by their source fields. Q033 SHALL use
synthetic check and plan failures without installing packages, accessing the
network, or invoking a global executable.

Q033 SHALL be additive and SHALL preserve `edutex.quality-baseline.v1`, all
report fields, runtime behavior outside diagnostic provenance validation, and
QL-001 through QL-039.

## QL-041 - Quality Runner/Report Consistency Contract

The quality process SHALL preserve exact source consistency between runner
results and the final report. For a genuine failed check, the report SHALL
preserve the runner result order, pass/fail status, return code, detail,
completed count, and failed-check identity. A structural execution diagnostic
SHALL NOT be projected as a fabricated failed check; its execution diagnostics
and runner detail SHALL remain available in the report while the check-result
projection remains empty.

Q034 SHALL validate both scenarios with deterministic synthetic fixtures,
without installing packages, accessing the network, or invoking a global
executable. Q034 SHALL be additive and SHALL preserve
`edutex.quality-baseline.v1`, all report fields, runtime behavior outside
runner/report consistency validation, and QL-001 through QL-040.

## QL-042 - Release Baseline End-to-End Contract

The quality process SHALL validate the complete public release baseline through
its actual `quality_check.py --json` subprocess path. The JSON stdout SHALL be
parseable, newline-terminated, free of stderr contamination, and aligned with
the process exit code and the direct report contract.

The complete all-pass path SHALL report `passed`, `complete: true`,
`exit_code: 0`, all catalog checks completed, no missing checks, no failed-check
identity, and empty catalog and execution diagnostic channels. The contract
MAY use private deterministic child-process probes to avoid recursive execution
of Q035, but SHALL NOT alter normal CLI behavior. Q035 SHALL be additive and
SHALL preserve `edutex.quality-baseline.v1`, all report fields, runtime behavior
outside end-to-end release validation, and QL-001 through QL-041.

