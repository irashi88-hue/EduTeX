# CORE_SPEC.md

**Document Type**: Component Specification
**Document ID**: COMP-CORE-001
**Version**: 1.0.0
**Status**: Draft
**Owner**: EduTeX Project

---

# 1. Purpose

## 1.1 Purpose

This specification defines the EduTeX Core component.

The Core is the runtime orchestrator of the EduTeX framework.

It is responsible for coordinating the initialization and lifecycle of the framework while delegating all domain-specific responsibilities to dedicated components.

This specification defines:

* the responsibilities of the Core;
* its architectural boundaries;
* its public role within the framework;
* its interactions with other framework components.

It does **not** define the implementation of the Core.

---

# 2. Scope

## In Scope

* Framework bootstrap
* Runtime lifecycle
* Global execution context
* Component orchestration
* Framework entry point
* Coordination of core services

## Out of Scope

* Configuration parsing
* Dependency resolution
* Plugin implementation
* Knowledge management
* Theme management
* Layout management
* Build execution
* Document generation
* Rendering
* Educational content

---

# 3. Normative References

This specification depends on:

* FRAMEWORK_SPEC.md
* ARCHITECTURE.md
* DOCUMENTATION_ARCHITECTURE.md
* SPECIFICATION_STANDARD.md

---

# 4. Overview

The Core represents the central runtime coordinator of EduTeX.

Its primary objective is to establish a controlled execution environment in which the remaining framework components can operate.

The Core SHALL remain intentionally lightweight.

Whenever a new capability is introduced into the framework, the preferred solution SHALL be to introduce or extend another component rather than increasing the responsibilities of the Core.

The Core is therefore designed around orchestration rather than execution.

---

# 5. Responsibilities

The Core SHALL be responsible for:

* starting the framework;
* creating the runtime context;
* coordinating component initialization;
* controlling the framework lifecycle;
* exposing the primary framework entry point;
* coordinating shutdown procedures.

The Core SHALL maintain the overall execution flow of the framework.

The Core SHALL remain independent from domain-specific logic.

---

## 5.1 Non-Responsibilities

The Core SHALL NOT:

* read configuration files;
* resolve dependencies;
* register services;
* activate extensions;
* generate documents;
* render outputs;
* manage themes;
* manage layouts;
* manage books;
* manage courses;
* perform build operations.

These responsibilities belong to dedicated framework components.

---

# 6. Architecture

The Core is composed of a minimal set of runtime responsibilities.

Conceptually it consists of:

```text
EduTeX Core

├── Bootstrap Coordinator
├── Lifecycle Manager
├── Runtime Context
└── Component Coordinator
```

These logical responsibilities do not imply implementation classes.

The internal implementation remains unspecified.

---

## Architectural Principle

The Core SHALL coordinate.

The Core SHALL NOT execute domain logic.

This principle has priority over implementation convenience.

---

# 7. Interfaces

The Core exposes a minimal public interface to the remainder of the framework.

Typical interactions include:

* framework initialization;
* lifecycle control;
* runtime status;
* controlled shutdown.

All other functionality SHALL be accessed through dedicated components.

The Core SHALL avoid exposing implementation-specific APIs.

---

# 8. Dependencies

The Core depends only on the existence of other architectural components.

It depends conceptually on:

| Component        | Purpose                 |
| ---------------- | ----------------------- |
| Configuration    | Framework configuration |
| Registry         | Service discovery       |
| Resolver         | Dependency resolution   |
| Activator        | Component activation    |
| Extension System | Extension management    |

The Core depends on their contracts rather than their implementations.

---

# 9. Constraints

The Core SHALL satisfy the following constraints.

## Minimal Responsibility

The Core SHALL remain as small as reasonably possible.

---

## Stability

The Core SHALL evolve more slowly than the surrounding framework.

---

## Technology Independence

The Core SHALL remain independent from implementation technologies.

---

## Deterministic Lifecycle

Framework startup and shutdown SHALL occur in a deterministic order.

---

## Delegation

Whenever functionality can reasonably belong to another component, it SHALL be delegated.

---

# 10. Extension Points

The Core does not define user-facing extension points.

Framework extensibility is delegated to the Extension System.

The Core only coordinates extension activation.

---

# 11. Future Evolution

Future versions of the Core MAY introduce:

* improved lifecycle coordination;
* runtime diagnostics;
* monitoring capabilities;
* execution metrics.

Future evolution SHALL preserve the orchestration philosophy defined in this specification.

The Core SHALL NOT gradually absorb responsibilities belonging to other components.

---

# 12. References

Informative references:

* ARCHITECTURE.md
* DOCUMENTATION_ARCHITECTURE.md

---

# 13. Change History

| Version | Description           |
| ------- | --------------------- |
| 1.0.0   | Initial specification |
