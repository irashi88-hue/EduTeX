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
