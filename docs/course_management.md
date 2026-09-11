# Course management

EduTeX course management adds a manifest layer above individual Knowledge Models.
The manifest describes an ordered curriculum without changing the existing lesson
build pipeline.

## Manifest

Create `course.yaml` in the project root:

```yaml
id: german-a1
title: German A1
language: de
level: A1
version: 1.0.0
author: Luca Raiola
description: Beginner German course
objectives:
  - Introduce yourself confidently
competencies:
  - Speaking
estimated_duration_minutes: 90
presentation:
  theme: forest
  accent: "#86c7a5"
  accent_secondary: "#d4a85c"
  show_contents: true
  show_progress: true
  show_objectives: true
  show_competencies: true
  show_prerequisites: true
  show_lesson_navigation: true
modules:
  - id: module-01
    title: Greetings
    lessons:
      - id: lesson-01
        title: Hello and introductions
        source: assets/knowledge_models/de-a1-unit-01.md
        duration_minutes: 25
      - id: lesson-02
        title: Practice
        source: assets/knowledge_models/de-a1-unit-02.md
        duration_minutes: 30
        prerequisites: [lesson-01]
```

`source` paths are relative to the project root. Module, lesson, and prerequisite
IDs use lowercase letters, numbers, `_`, or `-`.

## Course metadata

- `objectives` lists learner outcomes;
- `competencies` lists skills developed;
- `estimated_duration_minutes` declares the overall estimate.

If the estimate is omitted, EduTeX sums lesson-level `duration_minutes` values.
All fields are optional, so older manifests remain valid.

## Presentation and themes

The optional `presentation` section controls the course index and generated lesson
navigation. Built-in themes are:

- `midnight` — the default blue/ink palette;
- `paper` — warm paper and terracotta;
- `forest` — green botanical palette;
- `sunset` — plum, coral, and warm neutrals.

Every color override must be a six-digit hexadecimal value such as `#86c7a5`.
Visibility flags control contents, progress, objectives, competencies, prerequisite
labels, and lesson navigation. Hiding a prerequisite label does not disable the
actual prerequisite gate.

Example:

```yaml
presentation:
  theme: paper
  accent: "#9a4d2f"
  show_progress: false
  show_lesson_navigation: true
```

## Validation

```powershell
edutex course validate --project .
edutex course validate --project . --format json
```

Validation rejects invalid presentation values, unknown prerequisite IDs,
self-references, duplicate entries, and dependency cycles. The JSON summary
includes dependency count, metadata counts, resolved duration, and theme.

## Build a complete HTML course

```powershell
edutex course build --project . --format html
```

The output contains `output/course.html` and one generated page per lesson under
`output/lessons/`. The index includes the configured metadata and progress UI.
Progress is stored in browser `localStorage`, scoped to the course ID.

## Build a printable roadmap

```powershell
edutex course build --project . --format latex
edutex course build --project . --format pdf
```

LaTeX and PDF produce the course roadmap. The existing `edutex build` command
remains the command for rendering one lesson according to the project
configuration.

### Reproducible HTML builds

An HTML course build regenerates the declared lesson pages and removes stale generated `*.html` pages from the immediate `output/lessons` directory when a lesson is removed from `course.yaml`. Cleanup is restricted to valid lesson-ID filenames in that owned folder; files elsewhere in the project are not touched.

### Knowledge Model source validation

`course validate` also validates the content of every linked `source` file using the official Knowledge Model loader. It rejects a lesson source that:

- does not begin with a YAML front matter block;
- has unclosed or invalid YAML front matter;
- omits required fields such as `id`, `title`, `language`, `level`, or `version`.

This reports authoring errors during validation instead of waiting for the HTML lesson build to fail.

### Structured diagnostics

JSON validation keeps the compatible `errors` and `warnings` arrays and also
returns an ordered `diagnostics` array. Each diagnostic contains `code`,
`message`, and `severity`, and may include `field` and a project-relative
`path`. Stable codes include:

- `COURSE_SOURCE_NOT_FOUND`;
- `COURSE_SOURCE_FRONTMATTER_MISSING`;
- `COURSE_SOURCE_FRONTMATTER_INVALID`;
- `COURSE_SOURCE_REQUIRED_FIELD`;
- `COURSE_PREREQUISITE_UNKNOWN`;
- `COURSE_PREREQUISITE_CYCLE`;
- `COURSE_PRESENTATION_INVALID`;
- `COURSE_DURATION_UNDECLARED` for the non-blocking duration warning.

The text output remains unchanged; JSON consumers should use `diagnostics`
for editor and CI integrations instead of parsing human-readable messages.


## Accessibility baseline

Course and lesson HTML exports include keyboard-oriented accessibility affordances:

- a visible-on-focus skip link to the primary content landmark;
- an identified, focusable main content region;
- labelled course and lesson navigation links;
- explicit disabled state for unavailable previous/next controls;
- existing live regions for progress, completion, and prerequisite status.

The generated HTML remains static and self-contained, so these attributes are
available without a client-side framework.

## PDF metadata and language

LaTeX course output configures `hyperref` with stable PDF metadata:

- `pdftitle` uses the course title;
- `pdfauthor` uses the manifest author, falling back to `EduTeX`;
- `pdfsubject` uses the course description, falling back to `EduTeX course roadmap`;
- `pdflang` uses a normalized BCP 47-style language tag, including sensible
  default regions for common language-only values such as `de` (`de-DE`) and
  `en` (`en-US`).

The same fallback values are used by `\title` and `\author`, keeping the
visible title page and PDF metadata aligned. PDF metadata is emitted in the
`.tex` source before compilation; the final embedded metadata can be inspected
with `pdfinfo` after a LaTeX compiler has produced the PDF.

## PDF text accessibility and navigation

The LaTeX course renderer includes a small accessibility baseline for generated
PDFs:

- pdfLaTeX output loads `cmap` so copied and searched text receives a
  ToUnicode mapping;
- when the engine exposes `pdfgentounicode`, the renderer loads
  `glyphtounicode.tex` when available and enables Unicode mapping;
- `hyperref` is configured with Unicode support and an explicit numbered PDF
  outline, with bookmarks opened in the viewer by default;
- CJK documents continue to use the existing XeLaTeX path, while the Unicode
  mapping guard remains harmless for engines that do not expose the pdfTeX
  primitive.

These settings affect text extraction and navigation, not the visible course
content. After compiling a PDF, validate it with `qpdf --check`, `pdftotext`,
and a parser load check; use `pdfinfo` to inspect metadata.
