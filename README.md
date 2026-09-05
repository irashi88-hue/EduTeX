# EduTeX

A modular framework for generating educational documents from structured content.

## Architecture

EduTeX is organized into four architectural layers:

```
Runtime Infrastructure   -> Core, Configuration, Registry, Resolver, Activator
Framework Services       -> Knowledge, Theme, Layout
Architectural Mechanisms -> Extension System, Build System
User Assets              -> Knowledge Models
```

## Project Structure

```
src/edutex/          # Framework source code
  core/              # Runtime orchestration (CC-001, CC-002, CC-003)
  configuration/     # Validated configuration (CFG-001, CFG-002)
  registry/          # Entity registry (REG-001, REG-002)
  resolver/          # Reference resolution (RES-001, RES-002)
  activator/         # Runtime activation (ACT-001, ACT-002)
  knowledge/         # Knowledge processing (KNOW-001, KNOW-002)
  theme/             # Theme processing (THEME-001, THEME-002)
  layout/            # Layout processing (LAYOUT-001, LAYOUT-002)
  extension/         # Extension system (EXT-001, EXT-002)
  build/             # Build system (BUILD-001, BUILD-002)
assets/
  knowledge_models/  # User-authored Knowledge Models (.md)
  themes/            # Theme definitions
  layouts/           # Layout definitions
tests/
  unit/              # Unit tests per component
  integration/       # End-to-end pipeline tests
docs/                # Architecture and specification documents
tools/               # Developer tooling scripts
```

## Specifications

All architectural specifications are located in docs/.

## Simple usage

### Create a project

EduTeX can create a ready-to-build project with one command:

```bash
edutex init my-project
```

The starter project uses the midnight-blue `dark` theme by default. Use `--theme default` for the light theme and `--language it` or `--language en` to select the starter language.

The starter project uses HTML by default, so it does not require a LaTeX
distribution. Validate and build it with:

```bash
edutex validate --project my-project
edutex build --project my-project
```

Open `my-project/output/document.html` in a browser. To avoid overwriting an
existing directory, `init` refuses non-empty folders unless `--force` is used.

### Windows launcher

On Windows, double-click `edutex_launcher.pyw`. The launcher creates a local
`.edutex-venv` environment and installs EduTeX only on first use. Later
validation and builds reuse that environment; no manual activation is needed.
Use **Create project** for a new project, or choose an existing project folder
and click **Validate** or **Build**.

### Command line options

From the project root:

```bash
edutex validate
edutex build
edutex build --project path/to/project --config edutex.config.yaml
```

The `build` command runs the complete pipeline:

`configuration -> registry -> resolver -> activator -> knowledge -> theme -> layout -> extensions -> build`

The output format and destination are controlled by the `build` section of
`edutex.config.yaml`. With `output_format: pdf`, EduTeX writes the LaTeX source and compiles the PDF with `latexmk` (or `pdflatex`
as a fallback). If neither compiler is installed, the command fails explicitly
after preserving the generated `.tex` source. With `output_format: latex`, it
writes only the `.tex` source.

## Automated Integration Tests

From the project root, with the development dependencies installed:

```bash
python -m pytest -q
```

The integration suite verifies project initialization, configuration validation,
the complete pipeline, LaTeX source generation, explicit failure when no LaTeX
compiler is available, and PDF generation when `latexmk` or `pdflatex` is installed.


### Extensions

Extensions are optional assets under `assets/extensions/<extension-id>/`.
Each extension contains an `extension.yaml` manifest and a Python module with
one callable entrypoint. Enable an extension by listing its ID in the project
configuration:

```yaml
extensions:
  enabled:
    - reading_tip
```

The example `reading_tip` extension targets `layout.post_structure` and is
intentionally disabled by default. Extensions run after Layout and before
Build; they receive an isolated document snapshot and must return a new
`DocumentStructure`.
