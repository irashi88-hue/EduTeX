# SPECIFICATION_EXAMPLES.md

**Document Type**: Document Standard
**Document ID**: DS-EXAMPLES-001
**Version**: 1.0.0
**Status**: Approved
**Owner**: EduTeX Project

---

# 1. Purpose

## 1.1 Purpose

This document provides practical examples demonstrating how EduTeX specifications should be written.

It complements:

* SPECIFICATION_STANDARD.md
* SPECIFICATION_TEMPLATE.md

It is an educational document.

It SHALL NOT introduce new rules or modify existing requirements.

---

## 1.2 Scope

This document contains:

* good examples;
* bad examples;
* common mistakes;
* recommended practices.

All examples are illustrative.

The Specification Standard remains the only normative reference.

---

# 2. How to Use This Document

This document should be consulted:

* while writing a new specification;
* during specification reviews;
* while creating LLM prompts;
* when onboarding new contributors.

If an example conflicts with the Specification Standard, the Specification Standard always takes precedence.

---

# 3. Good Examples

## Example 1 — Purpose

### Good

```text
The purpose of this specification is to define the Core component responsible for framework initialization and lifecycle management.
```

Why it is good:

* concise;
* defines one objective;
* no implementation details.

---

## Example 2 — Scope

### Good

```text
In Scope

• Core responsibilities
• Lifecycle
• Public interfaces

Out of Scope

• Internal implementation
• Plugin behavior
• Build configuration
```

Why it is good:

* explicit boundaries;
* no ambiguity.

---

## Example 3 — Responsibility

### Good

```text
The Core SHALL initialize the framework lifecycle.

The Core SHALL expose the service registry.

The Core SHALL NOT manage educational content.
```

Why it is good:

* uses normative language;
* responsibilities are measurable;
* single responsibility.

---

## Example 4 — Architecture

### Good

```text
The Core consists of three logical modules:

• Bootstrap
• Lifecycle Manager
• Service Registry
```

Why it is good:

* describes architecture;
* avoids implementation.

---

## Example 5 — Dependency

### Good

| Dependency    | Purpose                    |
| ------------- | -------------------------- |
| Configuration | Read project configuration |
| Logging       | Report execution status    |

Why it is good:

* explicit;
* concise;
* traceable.

---

# 4. Bad Examples

## Example 1 — Undefined Purpose

### Bad

```text
This document explains the Core.
```

Problems:

* vague;
* no objective;
* no responsibility.

---

## Example 2 — Undefined Scope

### Bad

```text
This document describes everything related to the Core.
```

Problems:

* impossible boundaries;
* unmaintainable.

---

## Example 3 — Mixing Responsibilities

### Bad

```text
The Core manages plugins, educational books, themes, PDF generation and configuration.
```

Problems:

* violates Single Responsibility;
* mixes architectural concerns.

---

## Example 4 — Implementation Leakage

### Bad

```text
Core contains the BootstrapManager class that calls initialize() inside CoreService.
```

Problems:

* implementation details;
* programming language dependency;
* wrong abstraction level.

---

## Example 5 — Duplicate Definitions

### Bad

```text
The Service Registry is defined here...
```

when another specification already defines it.

Problems:

* duplicate source of truth;
* inconsistency risk.

---

# 5. Common Mistakes

The following mistakes are frequently encountered.

---

## Mixing Architecture and Implementation

Incorrect:

Describe classes, methods or source files.

Correct:

Describe responsibilities and relationships.

---

## Writing Requirements as Explanations

Incorrect:

```text
The Core usually initializes...
```

Correct:

```text
The Core SHALL initialize...
```

---

## Overlapping Sections

Incorrect:

Responsibilities repeated inside Architecture.

Correct:

Each section has one responsibility.

---

## Missing Scope

Incorrect:

Readers cannot determine what belongs to the specification.

Correct:

Clearly identify:

* In Scope
* Out of Scope

---

## Ambiguous Terminology

Incorrect:

```text
Sometimes...
Generally...
Usually...
```

Correct:

Use precise normative language.

---

# 6. Best Practices

## Keep Responsibilities Small

Smaller specifications are easier to evolve.

---

## Prefer References Over Duplication

Reference authoritative documents.

Avoid copying information.

---

## Keep Architecture Stable

Architecture should evolve more slowly than implementation.

---

## Keep Sections Independent

Each section should answer one primary question.

---

## Write for Future Readers

Assume the reader has never seen the project before.

---

## Prefer Simplicity

Simple specifications are easier to maintain than comprehensive but confusing ones.

---

# 7. Example Skeleton

The following illustrates the recommended structure of a specification.

```text
Metadata

Purpose

Scope

Normative References

Overview

Responsibilities

Architecture

Interfaces

Dependencies

Constraints

Extension Points (optional)

Examples (optional)

Future Evolution (optional)

References

Change History
```

---

# 8. Review Example

Example review comments.

### Good

```text
The Responsibilities section is complete and consistent with the Scope.
```

---

### Good

```text
Dependency declarations are explicit and traceable.
```

---

### Improvement Needed

```text
Architecture includes implementation details.

Move class-level information to implementation documentation.
```

---

### Improvement Needed

```text
Responsibilities overlap with another specification.

Consider splitting the document.
```

---

# 9. LLM Example

### Prompt

```text
Generate a Component Specification using SPECIFICATION_STANDARD.md and SPECIFICATION_TEMPLATE.md.

Follow every SHALL requirement.

Do not invent architectural concepts.

Keep the abstraction level appropriate for a Component Specification.
```

Why it is good:

* references authoritative documents;
* avoids duplication;
* keeps the prompt concise.

---

# 10. Summary

A good specification:

* has one responsibility;
* defines explicit boundaries;
* remains technology independent;
* avoids duplication;
* is traceable;
* is easy to review;
* is easy to evolve.

A specification is successful not because it is long, but because it communicates architectural intent clearly and consistently.

---

# End of Document
