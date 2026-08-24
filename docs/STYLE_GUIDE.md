---
document_id:      DS-STYLE-001
title:            EduTeX Document Style Guide
type:             Document Standard
version:          1.3.0
status:           Frozen
owner:            EduTeX Project
level:            1
parent:           none
normative_refs:
  - SPECIFICATION_STANDARD.md
  - SPECIFICATION_TEMPLATE.md
informative_refs: []
---

# EduTeX Document Style Guide

---

# 1. Purpose

This document defines the official visual and structural style for all EduTeX specifications.

Its objective is to ensure that every document in the EduTeX project shares a consistent, readable and professional appearance regardless of its content type or author.

This document governs **form**, not content.

Content rules remain defined by `SPECIFICATION_STANDARD.md`.

---

# 2. Intended Audience

This document is intended for:

- human authors writing EduTeX specifications;
- LLMs generating EduTeX specifications;
- reviewers validating EduTeX documents.

All contributors to the EduTeX project SHALL read this document before producing or reviewing any specification.

---

# 3. Scope

## 3.1 In Scope

- Metadata block format
- Heading hierarchy
- Section numbering
- Rule and principle formatting
- Table formatting
- Code block usage
- List formatting
- Separator usage
- Inline emphasis conventions
- Inline notes convention
- Language requirements
- Line break convention
- Change history format

## 3.2 Out of Scope

- Content requirements
- Architectural decisions
- Specification lifecycle and governance
- Shortcode system (defined in `SHORTCODE_SPEC.md`)

---

# 4. Normative References

| Document                   | Role      |
|----------------------------|-----------|
| SPECIFICATION_STANDARD.md  | Normative |
| SPECIFICATION_TEMPLATE.md  | Normative |

---

# 5. Metadata Block

## 5.1 Format

Every document SHALL open with a YAML frontmatter block delimited by `---`.

The metadata block SHALL be the very first content in the file, before any heading.

```yaml
---
document_id:      ARCH-SPEC-001
title:            EduTeX Architecture Specification
type:             Architecture Specification
version:          2.1.0
status:           Released
owner:            EduTeX Architecture
level:            2
parent:           FRAMEWORK_SPEC.md
normative_refs:
  - FRAMEWORK_SPEC.md
  - SPECIFICATION_STANDARD.md
informative_refs:
  - RUNTIME_ARCHITECTURE.md
---
```

## 5.2 Required Fields

| Field             | Description                                              |
|-------------------|----------------------------------------------------------|
| `document_id`     | Unique document identifier (see §5.3)                    |
| `title`           | Full human-readable document title                       |
| `type`            | Document type (see §5.4)                                 |
| `version`         | Semantic version (`MAJOR.MINOR.PATCH`)                   |
| `status`          | Lifecycle status (see §5.5)                              |
| `owner`           | Responsible team or role                                 |
| `level`           | Hierarchy level (0 = vision, 1 = framework, 2 = arch...) |
| `parent`          | Parent document filename, or `none`                      |
| `normative_refs`  | List of normative reference filenames                    |
| `informative_refs`| List of informative reference filenames (may be empty)   |

## 5.3 Document ID Convention

Document IDs follow the pattern `PREFIX-TYPE-NNN`:

| Prefix | Meaning                    | Example          |
|--------|----------------------------|------------------|
| `FW`   | Framework Specification    | `FW-SPEC-001`    |
| `ARCH` | Architecture Specification | `ARCH-SPEC-001`  |
| `RT`   | Runtime Specification      | `RT-SPEC-001`    |
| `COMP` | Component Specification    | `COMP-CORE-001`  |
| `DS`   | Document Standard          | `DS-STYLE-001`   |
| `KN`   | Knowledge Specification    | `KN-SPEC-001`    |
| `PROC` | Process Specification      | `PROC-SPEC-001`  |

## 5.4 Document Types

Allowed values for the `type` field:

- `Framework Specification`
- `Architecture Specification`
- `Runtime Specification`
- `Component Specification`
- `Knowledge Specification`
- `Document Standard`
- `Process Specification`

## 5.5 Status Values

Allowed values for the `status` field, in lifecycle order:

`Draft` → `Review` → `Approved` → `Released` → `Frozen` → `Deprecated`

---

# 6. Document Title

## 6.1 Rule

Immediately after the closing `---` of the metadata block, every document SHALL include a single `#` heading with the document title.

This heading SHALL match the `title` field in the metadata block exactly.

```markdown
---
...
---

# EduTeX Architecture Specification
```

A horizontal rule `---` SHALL follow the title heading to visually separate it from the body.

```markdown
# EduTeX Architecture Specification

---

# 1. Purpose
```

## 6.2 No Filename as Title

The document filename SHALL NOT be used as the document title heading.

```markdown
<!-- WRONG -->
# ARCHITECTURE.md

<!-- CORRECT -->
# EduTeX Architecture Specification
```

---

# 7. Heading Hierarchy

## 7.1 Levels

EduTeX documents use four heading levels.

| Level | Markdown | Usage                                  |
|-------|----------|----------------------------------------|
| H1    | `#`      | Document title and top-level sections  |
| H2    | `##`     | Subsections                            |
| H3    | `###`    | Named items within a subsection        |
| H4    | `####`   | Rarely used; only for deep nesting     |

H4 SHOULD be avoided. If needed, consider restructuring.

H5 and H6 SHALL NOT be used.

## 7.2 Section Numbering

Top-level sections SHALL be numbered starting from 1.

```markdown
# 1. Purpose
# 2. Intended Audience
# 3. Scope
# 4. Normative References
```

Subsections SHALL use dotted numbering.

```markdown
## 3.1 In Scope
## 3.2 Out of Scope
```

Sub-subsections SHALL use three-level dotted numbering.

```markdown
### 2.1.1 Specific Case
```

The document title heading (`#`) is NOT numbered.

## 7.3 Consistency Rule

Heading levels SHALL NOT be skipped.

```markdown
<!-- WRONG: jumps from H1 to H3 -->
# 7. Architectural Principles
### AP-001 — Separation of Concerns

<!-- CORRECT -->
# 7. Architectural Principles
## AP-001 — Separation of Concerns
```

---

# 8. Section Separators

A horizontal rule `---` SHALL appear after the content of every top-level section (`#`), closing it before the next section begins.

The `---` belongs to the section it closes, not to the section that follows.

A single `---` SHALL also appear immediately after the document title heading (`#`), before the first numbered section.
This separator is part of the document title block and is not governed by the section separator rule.

A horizontal rule SHALL NOT appear inside subsections, with one explicit exception: named rule entries (see §10) MAY be separated by `---` to improve readability when the rule group is long.

```markdown
# 1. Purpose

Content here.

---

# 2. Intended Audience

This document is intended for:

- human authors writing EduTeX specifications;
- LLMs generating EduTeX specifications;
- reviewers validating EduTeX documents.

All contributors to the EduTeX project SHALL read this document before producing or reviewing any specification.

---

# 3. Scope

Content here.

---
```

---

# 9. Normative Language

Normative statements SHALL use RFC 2119 keywords in uppercase.

| Keyword      | Meaning                              |
|--------------|--------------------------------------|
| SHALL        | Mandatory requirement                |
| SHALL NOT    | Mandatory prohibition                |
| SHOULD       | Recommended, exceptions allowed      |
| SHOULD NOT   | Not recommended, exceptions allowed  |
| MAY          | Optional                             |

Keywords SHALL appear in plain uppercase in all contexts.

They SHALL NOT be bolded, italicised or otherwise styled.

```markdown
<!-- WRONG -->
Every specification **SHALL** define its purpose.

<!-- CORRECT -->
Every specification SHALL define its purpose.
```

---

# 10. Rules and Principles

## 10.1 Format

Named rules (architectural principles, design rules, validation rules, writing rules) SHALL follow a consistent format.

Each rule entry SHALL include:

- **Identifier** — unique code (e.g. `AP-001`, `DR-003`, `WR-002`)
- **Name** — short descriptive name after an em dash
- **Body** — one or more normative statements

When a section contains multiple named rule entries, a horizontal rule `---` MAY be placed between entries to improve readability.
This is the only permitted use of `---` inside a subsection.

```markdown
## AP-001 — Separation of Concerns

Each architectural element SHALL own a clearly defined responsibility.

Responsibilities SHALL NOT overlap.
```

## 10.2 Extended Rule Format

When a rule requires additional context, the following extended format SHALL be used:

```markdown
## SR-001 — Explicit Purpose

**Applies To:** All Specifications

**Requirement**
Every specification SHALL define its purpose.

**Rationale**
The purpose identifies why the document exists.

**Verification**
Verify that a dedicated Purpose section exists.
```

The extended format SHALL be used consistently within a section — compact and extended formats SHALL NOT be mixed within the same rule group.

---

# 11. Tables

## 11.1 Format

Tables SHALL use standard Markdown pipe syntax.

Column headers SHALL be written in title case.

```markdown
| Component     | Specification        |
|---------------|----------------------|
| Core          | CORE_SPEC.md         |
| Configuration | CONFIGURATION_SPEC.md|
```

## 11.2 Alignment

Columns SHALL be left-aligned by default.

Numeric columns MAY be right-aligned.

## 11.3 Usage

Tables SHALL be used for:

- structured comparisons
- dependency declarations
- component inventories
- rule summaries

Tables SHALL NOT be used as a substitute for prose when a sentence is clearer.

---

# 12. Code Blocks

Code blocks SHALL use fenced syntax with an explicit language tag.

```markdown
    ```text
    Bootstrap
        │
        ▼
    Initialization
    ```
```

Allowed language tags:

| Tag      | Usage                                   |
|----------|-----------------------------------------|
| `text`   | ASCII diagrams, pseudo-code, structures |
| `yaml`   | Configuration examples, metadata        |
| `markdown`| Markdown syntax examples               |
| `latex`  | LaTeX source examples                   |

Code blocks SHALL NOT be used for emphasis or to highlight prose.

---

# 13. Lists

## 13.1 Unordered Lists

Unordered lists SHALL use `-` as the bullet character.

`*` and `+` SHALL NOT be used as bullet characters.

## 13.2 Ordered Lists

Ordered lists SHALL be used only when sequence or priority matters.

```markdown
1. Bootstrap
2. Initialization
3. Resource Loading
```

## 13.3 Nesting

List nesting SHALL NOT exceed two levels.

If deeper structure is needed, consider using subsections instead.

## 13.4 Punctuation

List items SHALL NOT end with a period unless the item is a complete sentence.

---

# 14. Inline Emphasis

| Style      | Markdown   | Usage                                           |
|------------|------------|-------------------------------------------------|
| Bold       | `**text**` | Key terms on first use, field names in metadata |
| Italic     | `_text_`   | Titles of documents, foreign words, light stress|
| Code       | `` `text` ``| Filenames, identifiers, field names, code refs |
| ALL CAPS   | —          | RFC 2119 normative keywords only                |

Bold SHALL NOT be used for decoration.

Italic SHALL NOT be used for emphasis in normative statements.

---

# 15. Document References

References to other EduTeX documents SHALL use the filename in backticks.

```markdown
This document depends on `SPECIFICATION_STANDARD.md`.
```

References SHALL NOT use relative file paths.

References SHALL NOT use bare document IDs without the filename.

---

# 16. Language

All EduTeX specification documents SHALL be written in English.

Technical English SHALL be used: clear, precise and free of colloquialisms.

Educational content documents (Knowledge Models) MAY use the target language of the educational subject, provided that all structural and normative elements remain in English.

---

# 17. Inline Notes

When a short clarifying note is needed within a specification — outside of the shortcode system — the following blockquote convention SHALL be used:

```markdown
> **Note:** This behaviour is defined in detail by `CORE_SPEC.md`.
```

Inline notes SHALL be used sparingly.

They SHALL NOT introduce normative requirements.

For normative content, a dedicated section or rule SHALL be used instead.

---

# 18. Line Breaks and Paragraphs

Each sentence SHALL appear on its own line in the Markdown source.

A blank line SHALL separate paragraphs.

Inline line breaks (trailing two spaces or `<br>`) SHALL NOT be used.

This convention improves diff readability in version control and is consistent with the existing authoritative documents.

```markdown
<!-- CORRECT -->
Each architectural element SHALL own a clearly defined responsibility.
Responsibilities SHALL NOT overlap.

<!-- WRONG -->
Each architectural element SHALL own a clearly defined responsibility. Responsibilities SHALL NOT overlap.
```

---

# 19. Summary — Quick Reference

| Element              | Rule                                                                      |
|----------------------|---------------------------------------------------------------------------|
| Metadata             | YAML frontmatter, required fields per §5.2                                |
| Title heading        | `#` matching metadata `title`, followed by `---`                          |
| Filename as title    | NEVER                                                                     |
| Section numbering    | `# 1.`, `## 1.1`, `### 1.1.1`                                             |
| Heading levels       | Max H3 in practice, H4 only if unavoidable, no H5/H6                     |
| Section separators   | `---` closes every `#` section                                            |
| Normative keywords   | SHALL / SHALL NOT / SHOULD / SHOULD NOT / MAY — plain uppercase, no style |
| Rule format          | `## XX-NNN — Name` + body (compact or extended, never mixed)              |
| Bullet character     | `-` only                                                                  |
| Date format          | `YYYY-MM-DD`                                                              |
| Document references  | `` `FILENAME.md` ``                                                       |
| Language             | English for all specification documents                                   |
| Inline notes         | `> **Note:** ...` — informative only, never normative                     |
| Line breaks          | One sentence per line; blank line between paragraphs                      |
| Document ending      | `---` + `*End of document.*`                                              |
| Change History       | Last numbered section; dates in `YYYY-MM-DD` format                       |

---

# 20. Change History

| Version | Date       | Description                                                                                                                                                                                                                                              |
|---------|------------|----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| 1.0.0   | 2026-08-07 | Initial release                                                                                                                                                                                                                                          |
| 1.1.0   | 2026-08-07 | Fixed subsection numbering in §2; clarified separator semantics in §7; unified normative keyword styling in §8; corrected document level; added PROC prefix to §4.3; added §15 Language, §16 Inline Notes, §17 Line Breaks; reordered closing sections |
| 1.2.0   | 2026-08-07 | Added §2 Intended Audience; renumbered all subsequent sections; clarified title separator rule in §9; added explicit rule for separators between named rules in §11.1; added Change History row to Quick Reference; status set to Frozen |
| 1.3.0   | 2026-08-24 | Fixed subsection numbering in §5 (was 7.x), §6 (was 5.x) and §11 (was 13.x) to match their parent section numbers. No content changes. |

---

*End of document.*
