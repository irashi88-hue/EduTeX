---
document_id:      MECH-COURSE-HTML-001
title:            EduTeX Single-File HTML Course Export Specification
type:             Component Specification
version:          0.1.0
status:           Draft
owner:            EduTeX Course Architecture
level:            3
parent:           ARCHITECTURE.md
normative_refs:
  - ARCHITECTURE.md
  - BUILD_SYSTEM_SPEC.md
  - KNOWLEDGE_MODEL_SPEC.md
  - KNOWLEDGE_SPEC.md
  - SHORTCODE_SPEC.md
  - SPECIFICATION_STANDARD.md
  - SPECIFICATION_TEMPLATE.md
informative_refs:
  - course_management.md
  - apply_single_file_course_html.py
  - scienze-chimica-single.html
---

EduTeX Single-File HTML Course Export Specification

1. Purpose

This specification defines the externally observable contract for building a complete EduTeX course as one self-contained HTML file. It defines the output artifact, lesson inclusion, navigation, offline operation, accessibility, failure behavior, and acceptance criteria.

This specification defines requirements, not a rendering algorithm or a mandated HTML implementation technique. It does not authorize implementation changes by itself.

2. Intended Audience

This document is intended for:

- course authors who build or distribute EduTeX courses;
- contributors implementing the course build command and HTML output;
- authors of Knowledge Models, themes, layouts, and exercises;
- reviewers validating course export behavior.

3. Scope

3.1 In Scope

- an additive single-file HTML output mode for a course declared by the existing course manifest;
- inclusion of every manifest lesson rendered through the ordinary EduTeX lesson build pipeline;
- a standalone course shell, lesson navigation, and preservation of lesson interactions;
- embedding local resources required to view and use the exported course;
- offline, accessibility, security, error, and compatibility requirements;
- testable acceptance criteria for the output.

3.2 Out of Scope

- changes to the course manifest schema or the meaning of its existing fields;
- changes to Knowledge Model, shortcode, theme, layout, exercise, or lesson-rendering contracts;
- a new course-authoring application or a new generic asset-selection interface;
- PDF, LaTeX, or other printable output behavior;
- hosting, publishing, analytics, synchronization, or distribution services;
- guaranteeing persistence where a browser blocks local storage;
- prescribing a particular HTML container, JavaScript framework, or internal build algorithm.

4. Normative References

| Document | Role |
|---|---|
| ARCHITECTURE.md | Normative |
| BUILD_SYSTEM_SPEC.md | Normative |
| KNOWLEDGE_MODEL_SPEC.md | Normative |
| KNOWLEDGE_SPEC.md | Normative |
| SHORTCODE_SPEC.md | Normative |
| SPECIFICATION_STANDARD.md | Normative |
| SPECIFICATION_TEMPLATE.md | Normative |

5. Overview

EduTeX course management currently builds a course index and separate lesson pages for HTML output. The single-file mode adds a portable alternative: one HTML artifact contains the course overview and the fully rendered content of every lesson in manifest order.

The course manifest remains the source of course metadata, module order, lesson order, prerequisites, and presentation settings. Each lesson SHALL be rendered by the ordinary EduTeX pipeline before it is incorporated into the course artifact. The single-file course output SHALL preserve the content and learner-facing behavior of those rendered lessons; it SHALL NOT substitute a raw-Markdown rendering path.

The proposed CLI form is:

```powershell
edutex course build --project . --format single-html
```

When the caller does not supply an explicit output path, the default destination SHALL be `output/course-single.html`. The existing `--format html` behavior SHALL remain the multi-file course build and SHALL NOT be silently changed by this specification.

6. Responsibilities

The Single-File Course Export capability SHALL:

- produce a complete course artifact from a valid course manifest and its declared lesson sources;
- use the existing course validation and ordinary lesson rendering behavior;
- combine the course overview and all lessons into one self-contained HTML file;
- preserve manifest ordering, metadata, presentation settings, prerequisite semantics, and supported lesson interactions;
- provide navigation among the course overview and lessons without loading companion lesson files;
- embed or otherwise make self-contained all local resources required at runtime;
- report failures without presenting an incomplete artifact as a successful build.

It SHALL NOT:

- change the meaning of `html`, `latex`, or `pdf` output modes;
- omit a lesson or lesson resource silently;
- require a running EduTeX installation, a web server, or a network connection to open and use the exported course;
- reimplement course validation, Knowledge Model parsing, or lesson rendering with a separate set of rules;
- include project files outside the validated project/resource scope.

7. Architecture

7.1 Build Input and Lesson Rendering

The single-file build SHALL use the existing course manifest as its authoritative input. It SHALL validate the manifest and every linked lesson source using the same validation rules as the ordinary course build.

Every lesson declared by the manifest SHALL be rendered through the ordinary EduTeX lesson build pipeline with the applicable project configuration and course presentation settings. Lessons SHALL be incorporated in the same module and lesson order declared by the manifest.

A failure to validate or render any declared lesson SHALL fail the single-file build. The build SHALL NOT produce a success result that contains a partial course.

7.2 Output Artifact and Resource Embedding

The successful build SHALL produce one learner-facing `.html` artifact. That artifact SHALL contain the course overview and the complete rendered content of all declared lessons.

All EduTeX-owned styles, scripts, fonts, images, and other local resources required to render or use the course SHALL be embedded in, or resolved entirely within, the artifact. Opening or moving the artifact SHALL NOT require a companion directory, generated lesson page, project source file, or relative local asset.

Markdown image destinations in lesson content SHALL be resolved relative to the source Knowledge Model file. Local image files with supported media types (`image/gif`, `image/jpeg`, `image/png`, `image/svg+xml`, and `image/webp`) SHALL be embedded in the generated lesson HTML and therefore in the final artifact. The resolved image path SHALL remain within the project root. Missing, empty, unsupported, or out-of-project images SHALL fail the build with an actionable diagnostic.

HTTP(S) and protocol-relative image sources in lesson content SHALL be rejected in `single-html`; they SHALL NOT trigger a network request or remain as external image resources.

The artifact SHALL NOT make automatic network requests for required content or presentation resources. Author-authored external links MAY remain as ordinary links, but they SHALL require an explicit learner action and SHALL NOT be fetched merely because the course is opened or navigated.

Temporary files MAY be used during generation. They SHALL NOT be required by the completed artifact and SHALL be removed or kept outside the learner-facing output set before the build reports success. This mode SHALL NOT emit separate learner-facing lesson HTML pages as required companion outputs.

The output SHALL be valid, UTF-8 HTML with a doctype, a single top-level document, a meaningful document title, and a root language derived from the course manifest. Lesson language metadata, when available, SHALL be applied to the corresponding lesson content.

7.3 Course and Lesson Navigation

The course overview SHALL provide an accessible table of contents covering every module and lesson. Each lesson SHALL have a stable in-document destination derived from its manifest lesson ID.

Selecting a lesson SHALL open or reveal that lesson within the same artifact. The destination SHALL be addressable using a URL fragment so a copied lesson link can open the corresponding lesson in the saved file. Browser back and forward navigation SHOULD restore the previously selected course or lesson destination.

Learners SHALL be able to return from a lesson to the course overview. Where the ordinary course output provides previous/next lesson navigation, the single-file output SHALL preserve equivalent navigation and SHALL honor existing prerequisite rules. Direct fragment navigation SHALL NOT bypass a prerequisite gate. An unavailable destination SHALL expose an understandable status to the learner.

The course overview SHALL retain manifest-driven course metadata and presentation visibility settings. The single-file mode SHALL preserve existing progress and completion behavior where supported by the ordinary HTML course output.

7.4 Progress and Prerequisite State

Completion state and prerequisite checks SHALL follow the existing course-management contract. Progress data SHALL remain scoped to the course identity and SHALL NOT be transmitted to an external service by the single-file artifact.

If browser storage is unavailable or rejects a read or write, opening, reading, navigating, and interacting with the course SHALL continue without an uncaught runtime error. The artifact MAY retain progress in memory for the current page session; it SHALL NOT claim that progress was saved persistently when persistence failed.

7.5 Offline Operation

The completed file SHALL open and support course overview, lesson reading, in-course navigation, and EduTeX-provided lesson interactions when opened directly from a local filesystem in a supported browser, without network access.

No required stylesheet, script, font, image, lesson page, or other resource may depend on a remote host. If a requested resource cannot be embedded or safely represented in the artifact, the build SHALL fail with a diagnostic identifying the affected lesson and resource where available; it SHALL NOT silently omit the resource.

7.6 Accessibility and Responsive Behavior

The course shell SHALL preserve the existing course and lesson HTML accessibility baseline, including:

- a skip link to the primary content landmark;
- a named, focusable main content region;
- meaningful labels for course and lesson navigation;
- keyboard-operable lesson disclosure and navigation controls;
- visible keyboard focus and understandable disabled or unavailable states;
- accessible status announcements for progress, completion, and prerequisite state;
- no keyboard trap when entering or leaving lesson content.

If lessons are represented using embedded browsing contexts, each context SHALL have a meaningful accessible title and SHALL remain keyboard accessible. Lesson content and interactive controls SHALL retain the accessibility semantics produced by the ordinary lesson renderer.

The course and lessons SHALL remain usable at narrow viewport widths. Motion used for navigation SHALL respect the user's reduced-motion preference. Essential course content SHALL not depend on animation, color alone, or hover-only interaction.

7.7 Security and Content Integrity

Course metadata, module titles, lesson titles, IDs, and resource values SHALL be encoded for their output context. They SHALL NOT be interpreted as executable markup solely because they appear in metadata.

The single-file output SHALL preserve the security constraints of the ordinary EduTeX lesson renderer and SHALL NOT make remote scripts or resources executable by default. Packaging SHALL NOT broaden the set of project files that a course can read. Lesson styling or behavior SHALL NOT corrupt the course overview or other lessons.

7.8 Failure and Diagnostics

A build failure SHALL return a non-zero CLI result and a diagnostic that identifies the failure stage and, where applicable, the lesson ID and project-relative resource path. Existing course validation diagnostics SHALL be reused for manifest and lesson-source validation failures.

The following stable diagnostic codes are proposed for failures specific to this output mode:

- `COURSE_SINGLE_HTML_BUILD_FAILED` — a declared lesson could not be rendered or assembled;
- `COURSE_SINGLE_HTML_RESOURCE_UNAVAILABLE` — a required local resource could not be embedded or represented safely.

Human-readable diagnostic text MAY evolve. Stable codes and structured fields, when present, SHALL remain suitable for CLI and JSON consumers. A failed build SHALL NOT replace a previously valid destination with a truncated or partial artifact.

8. Interfaces

8.1 CLI Interface

The course build command SHALL accept `single-html` as an output format value. It SHALL accept the same project selection, configuration, profile, and explicit output-path options as the ordinary HTML course build wherever those options are applicable. The output mode SHALL be selectable explicitly; it SHALL NOT become the default HTML mode without a separate specification change.

8.2 Input Interface

The input is the existing course manifest, its declared Knowledge Model sources, validated project configuration, and the resources already supported by the ordinary EduTeX lesson pipeline. This specification introduces no mandatory manifest fields.

8.3 Output Interface

The output is one standalone HTML course artifact. Its default path is `output/course-single.html`; an explicit output-path option, if provided by the CLI, SHALL select the artifact destination. The artifact SHALL not depend on files relative to that destination.

9. Dependencies

| Dependency | Type | Purpose |
|---|---|---|
| Course manifest and validation | Framework service | Defines and validates course metadata, order, sources, presentation, and prerequisites. |
| Knowledge Model loader and service | Framework service | Validates and processes each lesson source. |
| Ordinary lesson HTML renderer | Build service | Produces the authoritative rendered lesson content and interactions. |
| Project configuration, Theme, and Layout | Configuration and framework services | Provide the same applicable presentation and build behavior as ordinary course HTML output. |
| Browser | External runtime | Opens and operates the completed static HTML artifact. |

10. Constraints

- The output mode is additive and SHALL preserve backward compatibility for ordinary multi-file HTML course builds.
- Manifest order is authoritative; the exporter SHALL NOT reorder lessons based on filesystem order or registration order.
- The exporter SHALL NOT silently drop unsupported or unavailable required resources.
- The completed artifact SHALL not depend on external services, a local EduTeX runtime, or a web server.
- This specification sets no maximum course size, build-time target, or guarantee that every third-party browser extension or nonstandard HTML feature will work.
- The current single-file prototype and sample output are informative examples only. They are not evidence of compliance. In particular, a successful implementation must satisfy the standalone-artifact and no-required-companion-output requirements in this document.

11. Contract Requirements

| ID | Requirement |
|---|---|
| SFH-C-001 | `single-html` is an explicit, additive output mode; existing `html` behavior is unchanged. |
| SFH-C-002 | Every manifest lesson is validated and rendered through the ordinary lesson pipeline. |
| SFH-C-003 | A successful build produces one self-contained learner-facing HTML artifact with all declared lessons. |
| SFH-C-004 | The artifact works when moved and opened offline without companion files or automatic network requests. |
| SFH-C-005 | Course and lesson navigation works within the artifact, including stable lesson fragments and return navigation. |
| SFH-C-006 | Existing prerequisite and progress semantics are preserved; direct fragment navigation cannot bypass prerequisite gates. |
| SFH-C-007 | Required local resources are embedded or cause an actionable build failure; they are never silently omitted. |
| SFH-C-008 | The output preserves the stated keyboard, focus, landmark, status, responsive, and reduced-motion requirements. |
| SFH-C-009 | Storage failure does not make course reading or navigation fail and does not produce an uncaught runtime error. |
| SFH-C-010 | A failure in any declared lesson or required resource fails the build without publishing a partial artifact or replacing a previous valid output. |
| SFH-C-011 | Metadata and resources are encoded and packaged without weakening the ordinary renderer's security constraints. |

12. Acceptance Criteria

A conforming implementation SHALL pass tests that demonstrate all of the following:

1. The CLI accepts `--format single-html`, writes the documented default output, and supports an explicit output path where that option is available.
2. A course with multiple modules and lessons produces one standalone HTML artifact containing every lesson in manifest order and all required local lesson resources.
3. The artifact can be copied to a clean directory and opened offline; the course shell, lesson text, supported exercises, and in-course navigation continue to work.
4. The ordinary `--format html` build continues to produce the existing multi-file output and is not overwritten by a default `single-html` build.
5. Course-index links, direct lesson fragments, return-to-index controls, and browser history operate without loading separate lesson pages.
6. Prerequisites cannot be bypassed through direct fragments, embedded lesson links, or previous/next controls; completion updates the existing progress view.
7. Missing or unembeddable required resources and a failed lesson build produce non-zero results and actionable diagnostics. The output destination is not left as a partial or truncated course.
8. Storage read/write failure is tested and does not prevent reading or navigating the course.
9. Keyboard-only navigation reaches course controls and lesson content; focus remains visible; landmarks, labels, statuses, and any embedded-context titles are present and meaningful.
10. Narrow viewports and reduced-motion preferences are tested. No automatic external resource request is required for a successful offline run.
11. Course and lesson text containing quotes, angle brackets, ampersands, and non-ASCII characters is rendered without metadata-driven markup execution or character corruption.

13. Examples

The following is an illustrative invocation, not a requirement to use any particular implementation algorithm:

```powershell
edutex course build --project . --format single-html
```

Expected default artifact:

```text
output/course-single.html
```

A successful build includes the course overview and all rendered lessons in this artifact. No companion lesson page is required to open or use it.

14. Future Evolution

Future revisions MAY define browser compatibility targets, size limits, richer printing behavior, or optional packaging formats. Any extension SHALL preserve the standalone and backward-compatibility guarantees unless an explicitly versioned contract changes them.

15. References

Informative references:

- `course_management.md` — current course manifest, multi-file HTML, validation, progress, prerequisite, and accessibility behavior.
- `apply_single_file_course_html.py` — non-normative implementation patch prototype.
- `scienze-chimica-single.html` — non-normative sample artifact.

16. Change History

| Version | Date | Description |
|---|---|---|
| 0.1.0 | 2026-10-28 | Initial draft defining the single-file HTML course export contract and acceptance criteria. |
