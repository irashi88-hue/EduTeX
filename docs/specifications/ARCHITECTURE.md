# EduTeX Architecture

**Parent Specification**
- FRAMEWORK_SPEC.md

**Child Specifications**
- CORE_SPEC.md
- CONFIGURATION_SPEC.md
- EXTENSION_SYSTEM_SPEC.md
- KNOWLEDGE_SYSTEM_SPEC.md

---

**Version:** 1.0.0

**Status:** Approved

---

# 1. Purpose

This document defines the software architecture of the EduTeX framework.

It specifies the architectural decomposition of the framework, the responsibilities of its components, and the relationships between them.

This document is the authoritative architectural reference for all lower-level specifications.

Implementation details are intentionally excluded.

---

# 2. Scope

This specification defines:

- the architectural decomposition of EduTeX;
- the responsibilities of each Macro Component;
- the relationships between components;
- the internal decomposition of each Macro Component;
- the architectural dependency rules.

This specification does not define:

- implementation details;
- source code organization;
- directory structures;
- file structures;
- Knowledge Type implementations (Book, Course, Manual, etc.).

These topics are specified in dedicated component specifications.

---

# 3. Architectural Overview

EduTeX is organized into four Macro Components.

```
EduTeX
│
├── Core
├── Configuration
├── Extension System
└── Educational Knowledge
```

| Macro Component | Purpose |
|-----------------|---------|
| Core | Coordinates framework execution and orchestrates architectural components. |
| Configuration | Provides and validates framework configuration. |
| Extension System | Provides the mechanisms used to extend framework capabilities. |
| Educational Knowledge | Represents the educational domain through one or more Knowledge Models. |

---

# 4. Architectural Principles

The architecture follows the principles defined in the Framework Specification.

- Separation of Concerns
- High Cohesion
- Low Coupling
- Extensibility by Design
- Architecture Before Implementation

---

# 5. System Decomposition

## 5.1 Core

### Purpose

Coordinates framework execution and orchestrates component interaction.

### Responsibilities

- Manage framework lifecycle.
- Coordinate execution.
- Orchestrate architectural components.
- Provide execution services.

### Provides

- Lifecycle management
- Component orchestration

### Consumes

- Configuration

### Dependencies

- Configuration

---

## 5.2 Configuration

### Purpose

Provides and validates the framework configuration.

### Responsibilities

- Load configuration.
- Validate configuration.
- Apply default values.
- Expose configuration.

### Provides

- Configuration data
- Configuration validation
- Default configuration

### Consumes

None.

### Dependencies

None.

---

## 5.3 Extension System

### Purpose

Provides the architectural mechanism used to extend the framework.

### Responsibilities

- Register extensions.
- Resolve extensions.
- Activate extensions.
- Manage the extension lifecycle.

### Provides

- Extension registry
- Extension resolution
- Extension activation

### Consumes

- Core services
- Configuration

### Dependencies

- Core
- Configuration

---

## 5.4 Educational Knowledge

### Purpose

Represents the educational domain managed by the framework.

### Responsibilities

- Manage Knowledge Models.
- Organize educational knowledge.
- Expose Knowledge Models.
- Separate educational domain from framework infrastructure.

### Provides

- Knowledge Models
- Knowledge structure

### Consumes

- Core services
- Configuration

### Dependencies

- Core
- Configuration

---

# 6. Internal Component Decomposition

## 6.1 Core

| Internal Component | Responsibility |
|--------------------|----------------|
| Execution | Controls the execution lifecycle and orchestrates framework components. |
| Runtime | Provides the execution environment and shared runtime services. |

Execution and Runtime separate execution control from runtime state, reducing coupling and improving maintainability.

---

## 6.2 Configuration

| Internal Component | Responsibility |
|--------------------|----------------|
| Manager | Loads, maintains and exposes framework configuration. |
| Validator | Validates configuration consistency before execution. |

Management and validation remain independent, allowing validation policies to evolve without affecting configuration management.

---

## 6.3 Extension System

| Internal Component | Responsibility |
|--------------------|----------------|
| Registry | Discovers, validates and registers extensions. |
| Resolver | Selects extensions for the current execution context. |
| Activator | Initializes and activates selected extensions. |

The decomposition separates discovery, selection and activation into independent architectural responsibilities.

---

## 6.4 Educational Knowledge

| Internal Component | Responsibility |
|--------------------|----------------|
| Knowledge Model Abstraction | Defines the common abstraction shared by all Knowledge Models. |

The architecture depends only on the Knowledge Model abstraction.

Concrete Knowledge Types are defined independently and do not affect the framework architecture.

# 7. Component Relationships

```
                  +------------------+
                  |  Configuration   |
                  +------------------+
                           |
                           v
+------------------------------------------------------+
|                       Core                           |
+------------------------------------------------------+
        |                         |
        |                         |
        v                         v
+------------------+     +-------------------------+
| Extension System |     | Educational Knowledge   |
+------------------+     +-------------------------+
```

## Relationship Summary

| Source | Target | Relationship |
|---------|--------|--------------|
| Configuration | Core | Provides framework configuration. |
| Core | Extension System | Coordinates the extension lifecycle. |
| Core | Educational Knowledge | Provides execution services to Knowledge Models. |
| Extension System | Educational Knowledge | Extends framework behavior without owning educational knowledge. |

---

# 8. Dependency Rules

The following architectural rules apply to every component of the framework.

## DR-001 — Dependency Direction

Architectural dependencies shall follow the component hierarchy.

Circular dependencies are prohibited.

---

## DR-002 — Configuration Ownership

The Configuration component is the single owner of framework configuration.

No other component shall maintain an independent configuration state.

---

## DR-003 — Knowledge Independence

Educational Knowledge shall remain independent from Extension implementations.

Knowledge Models shall never depend on specific extensions.

---

## DR-004 — Extension Boundaries

Extensions may extend framework behavior.

Extensions shall not modify the architectural responsibilities of Macro Components.

---

## DR-005 — Architectural Stability

The framework architecture shall remain independent from individual Knowledge Types.

New Knowledge Types shall be introduced through dedicated specifications without modifying the architecture.

---

# 9. Architectural Decisions

This section summarizes the architectural decisions adopted by the framework.

| ID | Decision | Status |
|----|----------|--------|
| AD-001 | High-Level System Decomposition | Approved |
| AD-002 | Core Internal Decomposition | Approved |
| AD-003 | Configuration Internal Decomposition | Approved |
| AD-004 | Extension System Internal Decomposition | Approved |
| AD-005 | Educational Knowledge Abstraction | Approved |
| AD-006 | Framework and Knowledge Separation | Approved |

---

# Appendix A — Component Hierarchy

```text
EduTeX
│
├── Core
│   ├── Execution
│   └── Runtime
│
├── Configuration
│   ├── Manager
│   └── Validator
│
├── Extension System
│   ├── Registry
│   ├── Resolver
│   └── Activator
│
└── Educational Knowledge
    └── Knowledge Model Abstraction
```

---

# Appendix B — Dependency Overview

```
                  +------------------+
                  |  Configuration   |
                  +------------------+
                           |
                           v
+------------------------------------------------------+
|                       Core                           |
+------------------------------------------------------+
        |                         |
        |                         |
        v                         v
+------------------+     +-------------------------+
| Extension System |     | Educational Knowledge   |
+------------------+     +-------------------------+
```

Only the dependencies illustrated above are permitted by the architecture.

---

# Appendix C — Architectural Terminology

| Term | Definition |
|------|------------|
| Framework | The complete EduTeX software system. |
| Macro Component | A top-level architectural component. |
| Internal Component | A subdivision of a Macro Component with a dedicated architectural responsibility. |
| Knowledge Model | The architectural abstraction representing educational knowledge. |
| Knowledge Type | A concrete implementation of a Knowledge Model (Book, Course, Manual, etc.). |

The complete project terminology is defined in the Terminology Specification.

---

# References

| Document | Purpose |
|----------|---------|
| FRAMEWORK_SPEC.md | Framework vision, goals and design principles. |
| TERMINOLOGY.md | Project terminology and definitions. |
| CORE_SPEC.md | Core architecture and behavior. |
| CONFIGURATION_SPEC.md | Configuration component specification. |
| EXTENSION_SYSTEM_SPEC.md | Extension System specification. |
| KNOWLEDGE_SYSTEM_SPEC.md | Educational Knowledge specification. |

---

# Document Status

| Property | Value |
|----------|-------|
| Version | 1.0.0 |
| Status | Approved |
| Owner | EduTeX Project |
| Classification | Architecture Specification |