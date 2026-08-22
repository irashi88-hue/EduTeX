document_id:      DS-TEMPLATE-001
title:            EduTeX Specification Template
type:             Document Standard
version:          1.1.0
status:           Released
owner:            EduTeX Project
level:            1
parent:           SPECIFICATION_STANDARD.md
normative_refs:
  - SPECIFICATION_STANDARD.md
informative_refs: []

EduTeX Specification Template

1. Purpose

This document defines the standard template used to create every specification within the EduTeX framework.

It provides the document skeleton while the writing rules are defined in SPECIFICATION_STANDARD.md.

This template SHALL be used by:

human authors;

LLM-generated specifications;

future documentation tools.

2. Intended Audience

This document is intended for:

human authors writing EduTeX specifications;

LLMs generating EduTeX specifications;

tooling authors implementing document generation.

3. Scope

3.1 In Scope

standard document structure for all EduTeX specifications;

section templates with purpose and content guidance;

writing guidance and ordering rules;

optional section handling;

template compliance criteria.

3.2 Out of Scope

writing style rules (defined in SPECIFICATION_STANDARD.md);

validation rules and governance;

shortcode system (defined in SHORTCODE_SPEC.md).

4. Normative References

Document

Role

SPECIFICATION_STANDARD.md

Normative

5. Template Philosophy

The template defines where information belongs.

It does not define:

writing style;

validation rules;

governance.

Those subjects belong to SPECIFICATION_STANDARD.md.

Each section has one responsibility.

Sections SHALL NOT overlap.

6. Standard Document Structure

Every specification SHALL follow the structure below unless otherwise specified.

Metadata (YAML frontmatter)

1. Purpose

2. Intended Audience

3. Scope

4. Normative References

5. Overview

6. Responsibilities

7. Architecture

8. Interfaces

9. Dependencies

10. Constraints

11. Extension Points (optional)

12. Examples (optional)

13. Future Evolution (optional)

14. References

15. Change History

Optional sections may be omitted if not applicable.

7. Metadata Template

7.1 Purpose

Identify the document.

7.2 Template

---
document_id:      PREFIX-TYPE-NNN
title:            Full Document Title
type:             Document Type
version:          MAJOR.MINOR.PATCH
status:           Draft
owner:            EduTeX Project
level:            N
parent:           PARENT_DOCUMENT.md
normative_refs:
  - DOCUMENT.md
informative_refs:
  - DOCUMENT.md
---

8. Section Templates

8.1 Purpose

Purpose

Explain why the document exists.

Content

Describe:

motivation;

objective.

8.2 Intended Audience

Purpose

Declare who the document is written for.

Content

List the intended reader roles.

8.3 Scope

Purpose

Define document boundaries.

Content

Include:

In Scope: what the document covers;

Out of Scope: what the document explicitly excludes.

8.4 Normative References

Purpose

Declare authoritative documents.

Content

List only documents that introduce mandatory constraints.

Use the standard table format:

Document

Role

8.5 Overview

Purpose

Provide a high-level description of the subject.

Content

The overview should enable readers to understand the specification before entering technical details.

8.6 Responsibilities

Purpose

Describe what the subject is responsible for.

Content

Use concise responsibility statements.

Avoid implementation details.

Recommended format:

The component SHALL...

The component SHALL NOT...

8.7 Architecture

Purpose

Describe internal organization.

Content

Typical elements include:

modules;

services;

subsystems;

interactions.

Architecture SHOULD remain technology independent.

8.8 Interfaces

Purpose

Describe interactions with external elements.

Content

Examples:

public APIs;

contracts;

configuration interfaces;

communication mechanisms.

8.9 Dependencies

Purpose

Describe required relationships.

Content

Each dependency should include:

dependency name;

dependency type;

reason.

Recommended format:

Dependency

Type

Purpose

8.10 Constraints

Purpose

Describe limitations.

Examples include:

architectural constraints;

performance constraints;

compatibility constraints.

8.11 Extension Points (Optional)

Purpose

Describe supported extensibility mechanisms.

May include:

plugins;

hooks;

events;

customization points.

Omit this section if the subject is not extensible.

8.12 Examples (Optional)

Purpose

Provide illustrative examples.

Examples SHALL clarify the specification.

Examples SHALL NOT define requirements.

8.13 Future Evolution (Optional)

Purpose

Describe expected future evolution.

Examples:

planned extensions;

known limitations;

future compatibility.

This section is informative only.

8.14 References

Purpose

Collect informative references.

Unlike Normative References, these documents do not introduce mandatory constraints.

8.15 Change History

Purpose

Track document evolution.

Template:

Version

Date

Description

Dates SHALL follow the YYYY-MM-DD format (ISO 8601).

9. Writing Guidance

Each section SHOULD answer one question.

Section

Primary Question

Purpose

Why does this exist?

Intended Audience

Who is this written for?

Scope

What does it cover?

Overview

What is it?

Responsibilities

What does it do?

Architecture

How is it organized?

Interfaces

How does it interact?

Dependencies

What does it require?

Constraints

What limits apply?

Extension Points

How can it evolve?

References

Where is additional information?

10. Section Ordering Rules

Sections SHALL appear in a logical order.

General principles:

General before specific.

Stable concepts before variable concepts.

Architecture before implementation.

Requirements before examples.

11. Optional Sections

Optional sections MAY be omitted.

If omitted:

numbering SHALL remain consistent;

removed sections SHALL NOT be replaced by placeholders.

12. Custom Sections

Projects MAY introduce additional sections.

Additional sections SHALL:

have a single responsibility;

not duplicate existing sections;

follow the philosophy of this template.

13. Specialization

Specialized templates MAY extend this template.

Examples:

COMPONENT_TEMPLATE.md

KNOWLEDGE_TEMPLATE.md

PROCESS_TEMPLATE.md

Extensions SHALL preserve compatibility with this template.

14. Template Compliance

A specification conforms to this template if:

mandatory sections are present;

section order is preserved;

each section fulfills its intended responsibility;

no duplicated responsibilities exist.

15. Change History

Version

Date

Description

1.0.0

2026-08-07

Initial release

1.1.0

2026-08-07

Uniformed to STYLE_GUIDE.md v1.2.0: added YAML frontmatter, Intended Audience and Scope sections, converted bullet chars to -, ISO 8601 dates, normative references table, renumbered all sections, updated metadata template to reflect new frontmatter format, added End of document. closing

End of document.
