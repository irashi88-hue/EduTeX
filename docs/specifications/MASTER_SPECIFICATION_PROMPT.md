# MASTER_SPECIFICATION_PROMPT.md

**Document Type**: Document Standard
**Document ID**: DS-PROMPT-001
**Version**: 1.0.0
**Status**: Approved
**Owner**: EduTeX Project

---

# 1. Purpose

## 1.1 Purpose

This document defines the master prompt used to generate EduTeX specifications through Large Language Models (LLMs).

Its objective is to ensure that every generated specification:

* complies with the Specification Standard;
* follows the Specification Template;
* maintains architectural consistency;
* preserves project terminology;
* remains suitable for technical review.

This document defines the generation methodology, not the specification content itself.

---

## 1.2 Scope

This prompt applies to the generation of all EduTeX specifications, including but not limited to:

* Framework Specifications
* Architecture Specifications
* Component Specifications
* Knowledge Specifications
* Process Specifications

---

## 1.3 Normative References

The prompt SHALL be used together with the following documents:

* FRAMEWORK_SPEC.md
* ARCHITECTURE.md
* DOCUMENTATION_ARCHITECTURE.md
* SPECIFICATION_STANDARD.md
* SPECIFICATION_TEMPLATE.md

The prompt SHALL NOT replace these documents.

---

# 2. Input Documents

Before generating a specification, the following authoritative inputs SHALL be available.

## Mandatory Inputs

* Framework Specification
* Architecture
* Documentation Architecture
* Specification Standard
* Specification Template

## Optional Inputs

* Existing Specifications
* Domain-specific documents
* Project notes
* Requirement documents

Only authoritative documents SHALL be considered normative.

---

# 3. Generation Objectives

The generated specification SHALL:

* satisfy all applicable SHALL requirements;
* follow the Specification Template;
* remain consistent with the project architecture;
* avoid duplicated definitions;
* introduce only concepts supported by the provided documentation;
* maintain the intended abstraction level.

---

# 4. LLM Responsibilities

During generation, the LLM SHALL:

* interpret the authoritative documentation;
* organize information into the template structure;
* preserve architectural intent;
* produce technically consistent documentation.

The LLM SHALL NOT redesign the architecture.

---

# 5. LLM Restrictions

The LLM SHALL NOT:

* invent components;
* invent responsibilities;
* invent dependencies;
* redefine authoritative concepts;
* contradict higher-level specifications;
* introduce implementation details unless explicitly requested.

Whenever information is missing, the LLM SHOULD explicitly identify the missing information instead of making assumptions.

---

# 6. Generation Workflow

The recommended workflow is:

```text
Load authoritative documents

↓

Identify document type

↓

Determine applicable requirements

↓

Apply Specification Template

↓

Generate draft

↓

Perform self-consistency review

↓

Produce final specification
```

Each step SHALL preserve traceability to the authoritative inputs.

---

# 7. Prompt Structure

The master prompt SHOULD follow the structure below.

## Step 1 — Context

Provide:

* project context;
* document purpose;
* specification type.

---

## Step 2 — Authoritative Sources

Explicitly identify all normative documents.

Example:

```text
The following documents are authoritative.

- FRAMEWORK_SPEC.md
- ARCHITECTURE.md
- SPECIFICATION_STANDARD.md
```

---

## Step 3 — Generation Task

Clearly define the requested specification.

Example:

```text
Generate CORE_SPEC.md
```

---

## Step 4 — Constraints

State mandatory constraints.

Examples:

* Follow Specification Standard.
* Follow Specification Template.
* Preserve terminology.
* Maintain abstraction level.
* Do not invent architecture.

---

## Step 5 — Output Format

Specify the expected output.

Example:

```text
Produce a complete Markdown document.
```

---

# 8. Reference Prompt

The following prompt is the reference implementation.

---

## MASTER PROMPT

```text
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
```

---

# 9. Post-Generation Checklist

Before returning the specification, the LLM SHOULD verify:

* Purpose is present.
* Scope is complete.
* Normative references are correct.
* Responsibilities are explicit.
* Architecture is technology independent.
* Dependencies are declared.
* Constraints are complete.
* Terminology is consistent.
* No duplicated definitions exist.
* No unsupported assumptions were introduced.

---

# 10. Human Review

LLM generation does not replace technical review.

Every generated specification SHALL undergo the standard review process defined in:

* SPECIFICATION_STANDARD.md

Human reviewers remain responsible for approving the document.

---

# 11. Future Evolution

Future versions of this prompt MAY introduce:

* domain-specific prompt specializations;
* automated validation integration;
* multi-stage generation workflows;
* specification refinement prompts.

Backward compatibility SHOULD be preserved whenever practical.

---

# End of Document
