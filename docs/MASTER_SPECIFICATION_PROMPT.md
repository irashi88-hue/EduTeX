document_id:      DS-PROMPT-001
title:            EduTeX Master Specification Prompt
type:             Document Standard
version:          1.1.0
status:           Released
owner:            EduTeX Project
level:            1
parent:           SPECIFICATION_STANDARD.md
normative_refs:
  - FRAMEWORK_SPEC.md
  - ARCHITECTURE.md
  - SPECIFICATION_STANDARD.md
  - SPECIFICATION_TEMPLATE.md
informative_refs:
  - DOCUMENTATION_ARCHITECTURE.md

EduTeX Master Specification Prompt

1. Purpose

This document defines the master prompt used to generate EduTeX specifications through Large Language Models (LLMs).

Its objective is to ensure that every generated specification:

complies with the Specification Standard;

follows the Specification Template;

maintains architectural consistency;

preserves project terminology;

remains suitable for technical review.

This document defines the generation methodology, not the specification content itself.

2. Intended Audience

This document is intended for:

contributors using LLMs to generate EduTeX specifications;

LLMs operating as specification authors;

reviewers validating LLM-generated documents.

3. Scope

3.1 In Scope

LLM generation methodology for EduTeX specifications;

mandatory inputs and constraints for generation;

the reference master prompt;

post-generation review checklist.

3.2 Out of Scope

content of individual specifications;

architectural decisions;

specification lifecycle and governance (defined in SPECIFICATION_STANDARD.md).

4. Normative References

Document

Role

FRAMEWORK_SPEC.md

Normative

ARCHITECTURE.md

Normative

SPECIFICATION_STANDARD.md

Normative

SPECIFICATION_TEMPLATE.md

Normative

DOCUMENTATION_ARCHITECTURE.md

Informative

5. Input Documents

Before generating a specification, the following authoritative inputs SHALL be available.

5.1 Mandatory Inputs

Framework Specification

Architecture

Documentation Architecture

Specification Standard

Specification Template

5.2 Optional Inputs

Existing Specifications

Domain-specific documents

Project notes

Requirement documents

Only authoritative documents SHALL be considered normative.

6. Generation Objectives

The generated specification SHALL:

satisfy all applicable SHALL requirements;

follow the Specification Template;

remain consistent with the project architecture;

avoid duplicated definitions;

introduce only concepts supported by the provided documentation;

maintain the intended abstraction level.

7. LLM Responsibilities

During generation, the LLM SHALL:

interpret the authoritative documentation;

organize information into the template structure;

preserve architectural intent;

produce technically consistent documentation.

The LLM SHALL NOT redesign the architecture.

8. LLM Restrictions

The LLM SHALL NOT:

invent components;

invent responsibilities;

invent dependencies;

redefine authoritative concepts;

contradict higher-level specifications;

introduce implementation details unless explicitly requested.

Whenever information is missing, the LLM SHOULD explicitly identify the missing information instead of making assumptions.

9. Generation Workflow

The recommended workflow is:

Load authoritative documents
        │
        ▼
Identify document type
        │
        ▼
Determine applicable requirements
        │
        ▼
Apply Specification Template
        │
        ▼
Generate draft
        │
        ▼
Perform self-consistency review
        │
        ▼
Produce final specification

Each step SHALL preserve traceability to the authoritative inputs.

10. Prompt Structure

The master prompt SHOULD follow the structure below.

10.1 Step 1 — Context

Provide:

project context;

document purpose;

specification type.

10.2 Step 2 — Authoritative Sources

Explicitly identify all normative documents.

Example:

The following documents are authoritative.

- FRAMEWORK_SPEC.md
- ARCHITECTURE.md
- SPECIFICATION_STANDARD.md

10.3 Step 3 — Generation Task

Clearly define the requested specification.

Example:

Generate CORE_SPEC.md

10.4 Step 4 — Constraints

State mandatory constraints.

Examples:

Follow Specification Standard.

Follow Specification Template.

Preserve terminology.

Maintain abstraction level.

Do not invent architecture.

10.5 Step 5 — Output Format

Specify the expected output.

Example:

Produce a complete Markdown document.

11. Reference Prompt

The following prompt is the reference implementation.

You are an experienced Software Architect responsible for producing official EduTeX specifications.

You SHALL follow every applicable requirement defined in SPECIFICATION_STANDARD.md.

You SHALL organize the document according to SPECIFICATION_TEMPLATE.md.

Authoritative documents always take precedence over assumptions.

Never invent architectural concepts.

Never redefine concepts already defined elsewhere.

Maintain the appropriate abstraction level.

Prefer references over duplication.

Use clear and precise technical English.

Use normative language whenever requirements are introduced.

If required information is missing, explicitly identify the missing information instead of making assumptions.

Produce a complete Markdown specification suitable for direct inclusion in the EduTeX repository.

12. Post-Generation Checklist

Before returning the specification, the LLM SHOULD verify:

Purpose is present.

Scope is complete.

Normative references are correct.

Responsibilities are explicit.

Architecture is technology independent.

Dependencies are declared.

Constraints are complete.

Terminology is consistent.

No duplicated definitions exist.

No unsupported assumptions were introduced.

13. Human Review

LLM generation does not replace technical review.

Every generated specification SHALL undergo the standard review process defined in SPECIFICATION_STANDARD.md.

Human reviewers remain responsible for approving the document.

14. Future Evolution

Future versions of this prompt MAY introduce:

domain-specific prompt specializations;

automated validation integration;

multi-stage generation workflows;

specification refinement prompts.

Backward compatibility SHOULD be preserved whenever practical.

15. Change History

Version

Date

Description

1.0.0

2026-08-07

Initial release

1.1.0

2026-08-07

Uniformed to STYLE_GUIDE.md v1.2.0: added YAML frontmatter, Intended Audience and Scope sections, converted bullet chars to -, converted dates to ISO 8601, added normative references table, renumbered all sections, added End of document. closing

End of document.
