# SPECIFICATION_TEMPLATE.md

**Document Type**: Document Standard
**Document ID**: DS-TEMPLATE-001
**Version**: 1.0.0
**Status**: Approved
**Owner**: EduTeX Project

---

# 1. Purpose

## 1.1 Purpose

This document defines the standard template used to create every specification within the EduTeX framework.

It provides the document skeleton while the writing rules are defined in **SPECIFICATION_STANDARD.md**.

This template SHALL be used by:

* human authors;
* LLM-generated specifications;
* future documentation tools.

---

## 1.2 Scope

This template applies to every specification unless a specialized template explicitly overrides it.

Examples:

* Framework Specifications
* Architecture Specifications
* Component Specifications
* Knowledge Specifications
* Process Specifications

---

## 1.3 Normative Reference

This document depends on:

* SPECIFICATION_STANDARD.md

All requirements defined there remain applicable.

---

# 2. Template Philosophy

The template defines **where** information belongs.

It does **not** define:

* writing style;
* validation rules;
* governance.

Those subjects belong to the Specification Standard.

Each section has one responsibility.

Sections SHALL NOT overlap.

---

# 3. Standard Document Structure

Every specification SHALL follow the structure below unless otherwise specified.

```text
Metadata

1. Purpose

2. Scope

3. Normative References

4. Overview

5. Responsibilities

6. Architecture

7. Interfaces

8. Dependencies

9. Constraints

10. Extension Points (optional)

11. Examples (optional)

12. Future Evolution (optional)

13. References

14. Change History
```

Optional sections may be omitted if not applicable.

---

# 4. Section Templates

## Metadata

### Purpose

Identify the document.

### Template

```yaml
Document Name:

Document ID:

Document Type:

Version:

Status:

Owner:

Normative References:

Informative References:
```

---

## 1. Purpose

### Purpose

Explain why the document exists.

### Content

Describe:

* motivation;
* objective;
* intended audience.

---

## 2. Scope

### Purpose

Define document boundaries.

### Content

Include:

### In Scope

* ...

### Out of Scope

* ...

---

## 3. Normative References

### Purpose

Declare authoritative documents.

### Content

List only documents that introduce mandatory constraints.

---

## 4. Overview

### Purpose

Provide a high-level description of the subject.

### Content

The overview should enable readers to understand the specification before entering technical details.

---

## 5. Responsibilities

### Purpose

Describe what the subject is responsible for.

### Content

Use concise responsibility statements.

Avoid implementation details.

Recommended format:

```text
The component SHALL...

The component SHALL NOT...
```

---

## 6. Architecture

### Purpose

Describe internal organization.

### Content

Typical elements include:

* modules;
* services;
* subsystems;
* interactions.

Architecture SHOULD remain technology independent.

---

## 7. Interfaces

### Purpose

Describe interactions with external elements.

### Content

Examples:

* public APIs;
* contracts;
* configuration interfaces;
* communication mechanisms.

---

## 8. Dependencies

### Purpose

Describe required relationships.

### Content

Each dependency should include:

* dependency name;
* dependency type;
* reason.

Recommended format:

| Dependency | Type | Purpose |
| ---------- | ---- | ------- |

---

## 9. Constraints

### Purpose

Describe limitations.

Examples include:

* architectural constraints;
* performance constraints;
* compatibility constraints.

---

## 10. Extension Points (Optional)

### Purpose

Describe supported extensibility mechanisms.

May include:

* plugins;
* hooks;
* events;
* customization points.

Omit this section if the subject is not extensible.

---

## 11. Examples (Optional)

### Purpose

Provide illustrative examples.

Examples SHALL clarify the specification.

Examples SHALL NOT define requirements.

---

## 12. Future Evolution (Optional)

### Purpose

Describe expected future evolution.

Examples:

* planned extensions;
* known limitations;
* future compatibility.

This section is informative only.

---

## 13. References

### Purpose

Collect informative references.

Unlike Normative References, these documents do not introduce mandatory constraints.

---

## 14. Change History

### Purpose

Track document evolution.

Template:

| Version | Date | Description |
| ------- | ---- | ----------- |

---

# 5. Writing Guidance

Each section SHOULD answer one question.

| Section          | Primary Question                 |
| ---------------- | -------------------------------- |
| Purpose          | Why does this exist?             |
| Scope            | What does it cover?              |
| Overview         | What is it?                      |
| Responsibilities | What does it do?                 |
| Architecture     | How is it organized?             |
| Interfaces       | How does it interact?            |
| Dependencies     | What does it require?            |
| Constraints      | What limits apply?               |
| Extension Points | How can it evolve?               |
| References       | Where is additional information? |

---

# 6. Section Ordering Rules

Sections SHALL appear in a logical order.

General principles:

* General before specific.
* Stable concepts before variable concepts.
* Architecture before implementation.
* Requirements before examples.

---

# 7. Optional Sections

Optional sections MAY be omitted.

If omitted:

* numbering SHALL remain consistent;
* removed sections SHALL NOT be replaced by placeholders.

---

# 8. Custom Sections

Projects MAY introduce additional sections.

Additional sections SHALL:

* have a single responsibility;
* not duplicate existing sections;
* follow the philosophy of this template.

---

# 9. Specialization

Specialized templates MAY extend this template.

Examples:

* COMPONENT_TEMPLATE.md
* KNOWLEDGE_TEMPLATE.md
* PROCESS_TEMPLATE.md

Extensions SHALL preserve compatibility with this template.

---

# 10. Template Compliance

A specification conforms to this template if:

* mandatory sections are present;
* section order is preserved;
* each section fulfills its intended responsibility;
* no duplicated responsibilities exist.

---

# End of Document
