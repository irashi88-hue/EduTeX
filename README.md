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



## Release 0.4.0 — Shortcode authoring quality

EduTeX 0.4.0 consolida la pipeline di authoring e aggiunge il contratto
completo per gli esercizi interattivi di traduzione.

Highlights:

- `type: translation` nei Knowledge Model;
- alias `source:` / `prompt:`;
- alias `answer:` / `expected:`;
- risposte alternative separate da `|`;
- normalizzazione delle risposte e fallback alla soluzione;
- controlli accessibili per risposta, verifica, reset e feedback;
- etichette dell’interfaccia in italiano e inglese;
- rendering UTF-8 e Unicode-safe;
- documentazione, test di integrazione e release smoke coverage.

La release preserva inoltre i contratti esistenti per `choice`,
`short_answer`, `true_false`, `cloze`, `builder` e `matching`.

## Release 0.3.0 — Shortcode authoring quality

EduTeX 0.3.0 adds authoring-time quality checks for Knowledge Models. The
standalone `lint` command, the opt-in `build --lint` preflight, deterministic
JSON output, and semantic shortcode diagnostics help identify source problems
before rendering. The normal build remains unchanged unless `--lint` is passed.

### Japanese Knowledge Models

The initial Japanese path accepts `ja` in Knowledge Model metadata and in the
project initializer:

```powershell
edutex init japanese-project --language ja --theme default
```

The generated starter lesson covers あいさつと自己紹介 (greetings and
introductions) and uses mixed kanji, hiragana, and katakana. HTML output uses
`lang="ja"` and Japanese interface labels. LaTeX output keeps the Unicode
content and selects a CJK-capable preamble; PDF output requires XeLaTeX or
LuaLaTeX through `latexmk` or directly.

## Release 0.2.0 — Interactive HTML exercises

EduTeX 0.2.0 consolidates the first interactive exercise toolkit for HTML
output. The implementation remains renderer-based: lesson authors can use the
exercise types below without changing the parser, layout, or solution appendix.

### Supported exercise types

#### Fill-in-the-blank with clickable words

```text
::: exercise
title: Completa la frase
type: cloze
sentence: Ich ______ Luca.
answers:
- heiße
::: solution
Ich heiße Luca.
:::
:::
```

The available words can be clicked into the blanks, removed by clicking the
filled blank, checked, and reset. Each blank receives visual feedback.

#### Short answer

```text
::: exercise
title: Rispondi alla domanda
type: short_answer
prompt: Come ti chiami?
answer: Ich heiße Luca.
::: solution
Ich heiße Luca.
:::
:::
```

Short-answer fields include a German special-character bar (`ä ö ü Ä Ö Ü ß`)
that inserts a character at the cursor position. Final punctuation (`.`, `!`,
`?`, `…`) is ignored during answer comparison.

#### True or false

```text
::: exercise
title: Verifica le frasi
type: true_false
statement: Berlin è la capitale della Germania.
answer: true
statement: Wien è la capitale della Svizzera.
answer: false
:::
```

#### Sentence builder

```text
::: exercise
title: Costruisci la frase
type: builder
tokens:
- Ich
- heiße
- Luca.
::: solution
Ich heiße Luca.
:::
:::
```

Words are shuffled and selected with buttons. Selected words can be removed,
then the sentence can be checked or reset.

#### Matching

```text
::: exercise
title: Abbina le parole
type: matching
words:
- Hallo
- Tschüss
meanings:
- ciao
- arrivederci
::: solution
Hallo = ciao; Tschüss = arrivederci.
:::
:::
```

Matching meanings are shuffled, cannot be reused within the same exercise, and
can be checked or reset. The HTML renderer also keeps the existing solution
toggle and appendix link.

### HTML interaction conventions

All interactive exercises are generated as self-contained HTML. They use
keyboard-accessible controls, visible focus styles, localized Italian labels
for German lessons, and client-side feedback without external JavaScript
libraries or network requests.

LaTeX and other output paths remain available through the existing build
configuration. This release intentionally pauses the addition of new exercise
types so the current set can be tested and refined before further expansion.

## Specifications

All architectural specifications are located in docs/.

## Simple usage

### Create a project

EduTeX can create a ready-to-build project with one command:

```bash
edutex init my-project
```

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


### Lint preflight durante il build

Il lint durante il build è opt-in: il comando normale resta invariato e non
controlla gli shortcode automaticamente.

```powershell
edutex build --project path/to/project
edutex build --project path/to/project --lint
```

Con `--lint`, EduTeX controlla il Knowledge Model configurato prima di avviare
il pipeline. Gli errori bloccano il build con codice di uscita `1`; i warning
vengono mostrati ma non impediscono la generazione dell'output.

Per strumenti CI o editor è disponibile un report JSON deterministico:

```powershell
edutex build --project path/to/project --lint --format json
```

Il formato testuale resta il predefinito:

```powershell
edutex build --project path/to/project --lint --format text
```

Il report JSON contiene sempre due sezioni:

| Campo | Contenuto |
| --- | --- |
| `lint` | Report del Knowledge Model: `path`, `valid`, `errors`, `warnings` |
| `build` | Esito del build: `status`, più `output` se completato o `message` se bloccato |

Gli stati possibili sono:

- `completed`: il lint non ha errori e il build è terminato correttamente;
- `blocked`: il lint contiene almeno un errore e il build non è stato avviato.

Esempio di successo:

```json
{
  "lint": {
    "path": "assets/knowledge_models/example.md",
    "valid": true,
    "errors": [],
    "warnings": []
  },
  "build": {
    "status": "completed",
    "output": "output/document.html"
  }
}
```

Esempio di blocco:

```json
{
  "lint": {
    "path": "assets/knowledge_models/example.md",
    "valid": false,
    "errors": [
      {
        "severity": "error",
        "code": "SC101",
        "message": "formula requires a non-empty body."
      }
    ],
    "warnings": []
  },
  "build": {
    "status": "blocked",
    "message": "Build blocked: shortcode lint found errors."
  }
}
```

## Quality baseline

EduTeX includes a lightweight validation baseline that does not require
importing the complete runtime. It protects version consistency,
Python compilation, the supported interactive-exercise dispatch table, and the
self-contained accessible HTML contract.

Run the dependency-free check from the project root:

```bash
python tools/validate_release.py
```

When the development dependencies are installed, run the smoke test suite too:

```bash
python -m pytest -q tests/test_release_smoke.py
```

The full end-to-end pipeline remains the preferred check when all framework
modules and project assets are available.

## Local quality baseline

Run the local quality baseline from the project root:

```powershell
python tools\quality_check.py
```

The check is deterministic and does not install packages or use the network. It
verifies Python syntax, the configured pytest suite, the standalone lint command
in text and JSON modes, the opt-in `build --lint` preflight, and the public CLI
commands and options. Use `--verbose` to print additional diagnostics:

```powershell
python tools\quality_check.py --verbose
```

The regular build remains unchanged; the lint preflight is opt-in:

```powershell
edutex build
edutex build --lint
```
