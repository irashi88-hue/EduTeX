# EduTeX Architecture

**Parent Specification**
- FRAMEWORK_SPEC.md

**Child Specifications**
- CORE_SPEC.md
- CONFIGURATION_SPEC.md
- EXTENSION_SYSTEM_SPEC.md
- KNOWLEDGE_SYSTEM_SPEC.md

---

# ARCHITECTURE.md

**Document ID:** ARCH-SPEC-001

**Version:** 2.0.0

**Status:** Released

**Classification:** Authoritative

**Owner:** EduTeX Architecture

**Level:** Level 2 — Architecture

**Parent Document:** FRAMEWORK_SPEC.md

## Related Documents

- FRAMEWORK_SPEC.md
- RUNTIME_ARCHITECTURE.md
- SPECIFICATION_STANDARD.md
- SPECIFICATION_TEMPLATE.md
- MASTER_SPECIFICATION_PROMPT.md
- DOCUMENTATION_ARCHITECTURE.md

---

# 1. Purpose

This document defines the **static architecture** of the EduTeX Framework.

Its purpose is to describe the architectural structure of the framework by defining its architectural elements, their responsibilities, their relationships, and the governing architectural rules.

This document SHALL NOT describe runtime behavior, implementation details, processing pipelines, or lifecycle execution.

---

# 2. Scope

This specification defines:

- the architectural decomposition of the framework;
- the architectural element model;
- the component model;
- architectural dependencies;
- architectural constraints;
- architectural design rules.

This specification SHALL remain implementation independent.

---

# 3. Relationship with Other Specifications

The EduTeX documentation hierarchy separates architectural concerns into multiple complementary specifications.

This document is responsible exclusively for describing the **static architecture** of the framework.

The relationship between the primary architectural documents is defined below.

| Document | Responsibility |
|-----------|----------------|
| FRAMEWORK_SPEC.md | Defines the vision, objectives and high-level design of the framework. |
| ARCHITECTURE.md | Defines the static architectural structure of the framework. |
| RUNTIME_ARCHITECTURE.md | Defines runtime behavior, lifecycle and processing model. |
| *_SPEC.md | Defines the detailed specification of individual architectural components. |

No architectural information SHALL exist in multiple authoritative documents.

Each architectural concept SHALL have a single authoritative owner.

---

# 4. Vision

The EduTeX Framework SHALL provide a modular, maintainable and extensible architecture for the creation of educational documents.

The architecture SHALL remain independent from any specific educational domain, document type, output format or implementation technology.

The architectural model SHALL support long-term evolution while preserving stability of the public architecture.

---

# 5. Goals

The architecture SHALL satisfy the following objectives:

- separation of concerns;
- single responsibility;
- deterministic system behavior;
- modular extensibility;
- low coupling;
- high cohesion;
- implementation independence;
- architectural stability;
- documentation-driven development.

---

# 6. Design Philosophy

The EduTeX architecture follows the principle:

> **Architecture defines structure. Specifications define behavior.**

The Architecture Specification SHALL describe:

- architectural elements;
- architectural relationships;
- architectural constraints;
- architectural rules.

Detailed behavior SHALL be delegated to dedicated specifications.

The architecture SHALL evolve only through controlled architectural refactoring while preserving the stability of the architectural model.

---

# 7. Architectural Principles

## AP-001 — Separation of Concerns

Each architectural element SHALL own a clearly defined responsibility.

Responsibilities SHALL NOT overlap.

---

## AP-002 — Single Responsibility

Each architectural component SHALL provide exactly one architectural capability.

Multiple unrelated responsibilities SHALL NOT be assigned to the same architectural component.

---

## AP-003 — Modularity

Architectural elements SHALL be independently evolvable whenever possible.

Changes to one component SHOULD minimize impact on the remainder of the framework.

---

## AP-004 — Static and Dynamic Separation

Static architectural structure SHALL be described exclusively by the Architecture Specification.

Dynamic runtime behavior SHALL be described exclusively by the Runtime Architecture Specification.

---

## AP-005 — Specification Ownership

Each architectural component SHALL own a dedicated Component Specification.

The Architecture Specification SHALL reference component specifications rather than duplicate their internal design.

---

## AP-006 — Architectural Element Classification

The framework SHALL distinguish between different categories of architectural elements.

Architectural Components, Architectural Mechanisms and User Assets SHALL remain conceptually independent.

---

## AP-007 — Technology Independence

Architectural decisions SHALL remain independent from programming languages, LaTeX implementation details, build systems or external tools.

---

## AP-008 — Architectural Stability

The architectural model SHALL evolve only through controlled architectural revisions.

Implementation changes SHALL NOT require modifications to the Architecture Specification unless the architectural structure itself changes.

# 8. Architectural Elements

## 8.1 Overview

The EduTeX Framework is composed of a set of architectural elements organized according to their architectural responsibility.

Architectural elements are grouped into categories that define their role within the framework.

Each architectural element SHALL belong to exactly one architectural category.

The architecture distinguishes between:

- Runtime Infrastructure
- Framework Services
- Architectural Mechanisms
- User Assets

Each category represents a different level of responsibility within the framework.

---

# 8.2 Runtime Infrastructure

Runtime Infrastructure contains the fundamental architectural components required for the execution of the framework.

These components provide the services required by all higher architectural layers.

Runtime Infrastructure consists of:

- Core
- Configuration
- Registry
- Resolver
- Activator

Runtime Infrastructure SHALL NOT contain educational knowledge or document-specific logic.

Runtime Infrastructure SHALL remain independent from user content.

---

# 8.3 Framework Services

Framework Services provide reusable functional capabilities built on top of the Runtime Infrastructure.

Framework Services extend the framework without modifying the Runtime Infrastructure itself.

Framework Services currently include:

- Knowledge
- Theme
- Layout

Additional framework services MAY be introduced in future versions provided they comply with the architectural principles defined in this document.

---

# 8.4 Architectural Mechanisms

Architectural Mechanisms define how architectural components collaborate.

Unlike architectural components, mechanisms do not own business responsibilities.

Instead, they coordinate interactions between architectural elements.

Current architectural mechanisms include:

- Extension System
- Build System

Architectural mechanisms SHALL remain independent from individual component implementations.

Mechanisms SHALL coordinate components through their public contracts.

---

# 8.5 User Assets

User Assets represent the educational artifacts managed by the framework.

The framework SHALL process User Assets without embedding domain-specific knowledge inside the Runtime Infrastructure.

Current User Assets include:

- Knowledge Models

Future versions MAY introduce additional asset types without requiring modifications to the Runtime Infrastructure.

---

# 8.6 Architectural Element Hierarchy

The architectural organization of EduTeX is represented by the following conceptual hierarchy.

```text
EduTeX Framework

├── Runtime Infrastructure
│   ├── Core
│   ├── Configuration
│   ├── Registry
│   ├── Resolver
│   └── Activator
│
├── Framework Services
│   ├── Knowledge
│   ├── Theme
│   └── Layout
│
├── Architectural Mechanisms
│   ├── Extension System
│   └── Build System
│
└── User Assets
    └── Knowledge Models
```

This hierarchy defines the static architectural organization of the framework.

It SHALL NOT be interpreted as a runtime execution flow.

Runtime behavior is specified by the Runtime Architecture Specification.

# 9. Component Model

## 9.1 Overview

The EduTeX Framework is composed of Architectural Elements.

An Architectural Element represents a distinct entity within the architectural model and SHALL belong to exactly one architectural category.

The architecture recognizes three categories of Architectural Elements:

- Architectural Components
- Architectural Mechanisms
- User Assets

Each category defines a different architectural responsibility.

---

# 9.2 Architectural Components

An Architectural Component is an autonomous Architectural Element that owns a single architectural responsibility.

An Architectural Component SHALL:

- own exactly one architectural capability;
- expose one or more public architectural contracts;
- encapsulate its internal implementation;
- declare its dependencies explicitly;
- evolve independently within architectural constraints.

Architectural Components SHALL own behavior.

Architectural Components MAY own internal state.

Architectural Components SHALL NOT own other Architectural Components.

Component composition SHALL be achieved through collaboration rather than containment.

---

# 9.3 Architectural Mechanisms

An Architectural Mechanism is an Architectural Element responsible for coordinating collaboration between Architectural Components.

Architectural Mechanisms SHALL NOT own business responsibilities.

Architectural Mechanisms SHALL NOT own educational knowledge.

Architectural Mechanisms MAY coordinate multiple Architectural Components.

Architectural Mechanisms MAY maintain internal execution state required to perform coordination.

Architectural Mechanisms SHALL expose public architectural contracts when interaction with other elements is required.

Current Architectural Mechanisms include:

- Extension System
- Build System

---

# 9.4 User Assets

User Assets represent the educational artifacts manipulated by the framework.

User Assets SHALL remain independent from Runtime Infrastructure.

User Assets SHALL NOT contain framework implementation logic.

Current User Assets include:

- Knowledge Models

Future versions MAY introduce additional asset categories.

---

# 9.5 Public Architectural Contracts

Collaboration between Architectural Elements SHALL occur exclusively through Public Architectural Contracts.

A Public Architectural Contract defines the externally visible capabilities offered by an Architectural Element.

Public Architectural Contracts MAY include:

- services;
- interfaces;
- extension points;
- configuration contracts;
- resource contracts.

Internal implementation SHALL NEVER be considered part of a Public Architectural Contract.

---

# 9.6 Component Relationships

Architectural Components collaborate through explicitly defined relationships.

The architecture recognizes the following relationship types.

## Dependency

A component requires services provided by another Architectural Element.

Dependencies SHALL be explicit.

Dependencies SHALL be unidirectional.

---

## Coordination

Architectural Mechanisms coordinate collaboration between Architectural Components.

Coordination SHALL NOT transfer ownership of responsibilities.

---

## Ownership

Every architectural responsibility SHALL be owned by exactly one Architectural Component.

Ownership SHALL NOT be shared.

---

## Visibility

Architectural Elements SHALL expose only their Public Architectural Contracts.

Internal implementation SHALL remain hidden.

---

# 9.7 Component Specifications

Every Architectural Component SHALL own a dedicated Component Specification.

Component Specifications constitute the authoritative description of component behavior.

This document SHALL reference Component Specifications but SHALL NOT duplicate their internal architecture.

| Component | Specification |
|-----------|---------------|
| Core | CORE_SPEC.md |
| Configuration | CONFIGURATION_SPEC.md |
| Registry | REGISTRY_SPEC.md |
| Resolver | RESOLVER_SPEC.md |
| Activator | ACTIVATOR_SPEC.md |

Additional Component Specifications MAY be introduced without modifying the architectural model.

---

# 9.8 Architectural Boundaries

The Architecture Specification defines:

- the Architectural Element Model;
- architectural relationships;
- dependency rules;
- architectural constraints.

Component Specifications define:

- internal architecture;
- responsibilities;
- interfaces;
- lifecycle;
- constraints;
- future evolution.

This separation SHALL be preserved throughout the framework documentation.

# 10. Dependency Model

## 10.1 Overview

The EduTeX Framework follows a strictly controlled dependency model.

Dependencies define the static relationships between architectural elements.

The dependency model SHALL guarantee:

- deterministic architecture;
- low coupling;
- high cohesion;
- architectural stability;
- independent evolution of components.

Dependency relationships describe architectural structure only.

They SHALL NOT describe runtime execution.

---

# 10.2 Dependency Principles

Architectural dependencies SHALL follow these principles.

## Unidirectional Dependencies

Dependencies SHALL always have a single direction.

Bidirectional dependencies SHALL NOT exist.

---

## Explicit Dependencies

Every dependency SHALL be explicitly defined.

Implicit architectural dependencies SHALL NOT exist.

---

## Dependency Visibility

Components SHALL depend only on public architectural contracts.

Internal implementation SHALL NOT be visible outside the owning component.

---

## Stable Dependencies

Higher-level architectural elements SHOULD depend on more stable architectural elements.

Lower-level infrastructure SHALL NOT depend on higher-level services.

---

# 10.3 Architectural Dependency Hierarchy

The architectural dependency hierarchy is defined as follows.

```text
                User Assets
                     │
                     ▼
           Framework Services
                     │
                     ▼
      Architectural Mechanisms
                     │
                     ▼
        Runtime Infrastructure
```

Dependencies SHALL always point toward lower architectural layers.

Reverse dependencies SHALL NOT exist.

---

# 10.4 Dependency Graph

The Runtime Infrastructure provides the foundation of the framework.

Framework Services consume Runtime Infrastructure.

Architectural Mechanisms coordinate architectural elements without owning their responsibilities.

User Assets remain independent from framework implementation.

The conceptual dependency graph is shown below.

```text
                   User Assets
                         │
                         ▼
                Framework Services
              ┌──────────┼──────────┐
              │          │          │
          Knowledge    Theme     Layout
              │          │          │
              └──────────┼──────────┘
                         │
                         ▼
            Architectural Mechanisms
             ┌──────────────────────┐
             │ Extension System     │
             │ Build System         │
             └──────────────────────┘
                         │
                         ▼
             Runtime Infrastructure
      ┌─────────────────────────────────┐
      │ Core                            │
      │ Configuration                   │
      │ Registry                        │
      │ Resolver                        │
      │ Activator                       │
      └─────────────────────────────────┘
```

This graph represents the static architecture of the framework.

It SHALL NOT be interpreted as a runtime sequence diagram.

---

# 11. Design Rules

The following rules govern every architectural decision within the EduTeX Framework.

## DR-001 — Unidirectional Dependencies

Architectural dependencies SHALL be unidirectional.

Circular dependencies SHALL NOT exist.

---

## DR-002 — Single Responsibility

Each architectural component SHALL own exactly one architectural responsibility.

Responsibilities SHALL NOT overlap.

---

## DR-003 — Configuration Ownership

Configuration SHALL be managed exclusively by the Configuration component.

Other components SHALL consume configuration without owning it.

---

## DR-004 — Encapsulation

Architectural components SHALL expose functionality exclusively through public contracts.

Internal implementation SHALL remain encapsulated.

---

## DR-005 — Separation of Concerns

Architectural Components, Architectural Mechanisms and User Assets SHALL remain conceptually independent.

Their responsibilities SHALL NOT overlap.

---

## DR-006 — Component Isolation

Each architectural component SHALL own its internal architecture.

Component implementation SHALL be documented exclusively in its dedicated Component Specification.

---

## DR-007 — Architectural Ownership

Every architectural concept SHALL have a single authoritative document.

The ownership model is defined as follows.

| Architectural Concept | Authoritative Document |
|------------------------|------------------------|
| Framework Vision | FRAMEWORK_SPEC.md |
| Static Architecture | ARCHITECTURE.md |
| Runtime Behaviour | RUNTIME_ARCHITECTURE.md |
| Component Behaviour | Individual Component Specifications |

Architectural information SHALL NOT be duplicated across authoritative documents.

---

## DR-008 — Architectural Stability

The Architecture Specification SHALL evolve only when the architectural model changes.

Implementation changes SHALL NOT require modifications to this document.

# 12. Documentation Mapping

## 12.1 Documentation Hierarchy

The EduTeX Framework documentation is organized as a hierarchy of authoritative specifications.

Each document owns a specific architectural concern.

The documentation hierarchy is defined as follows.

```text
Level 0
└── Vision

Level 1
└── FRAMEWORK_SPEC.md

Level 2
├── ARCHITECTURE.md
└── RUNTIME_ARCHITECTURE.md

Level 3
├── CORE_SPEC.md
├── CONFIGURATION_SPEC.md
├── REGISTRY_SPEC.md
├── RESOLVER_SPEC.md
├── ACTIVATOR_SPEC.md
└── Additional Component Specifications

Level 4+
└── Domain-specific specifications
```

Each lower-level document SHALL conform to the architectural constraints defined by higher-level specifications.

---

## 12.2 Documentation Responsibilities

Architectural responsibilities are distributed as follows.

| Document | Responsibility |
|-----------|----------------|
| FRAMEWORK_SPEC.md | Framework vision, goals and overall design philosophy |
| ARCHITECTURE.md | Static architectural structure and architectural rules |
| RUNTIME_ARCHITECTURE.md | Runtime lifecycle, execution model and processing pipelines |
| Component Specifications | Detailed definition of individual architectural components |

Each architectural concept SHALL have exactly one authoritative owner.

---

## 12.3 Architectural Traceability

Every architectural decision SHALL be traceable to one authoritative document.

Specifications SHALL reference higher-level documents rather than duplicate their contents.

Traceability SHALL be preserved throughout the documentation hierarchy.

---

# 13. Normative References

The following documents are normative references for this specification.

- FRAMEWORK_SPEC.md
- SPECIFICATION_STANDARD.md
- SPECIFICATION_TEMPLATE.md
- DOCUMENTATION_ARCHITECTURE.md

The latest approved version of each document SHALL be considered authoritative.

---

# 14. Future Evolution

The Architecture Specification defines the stable architectural model of the EduTeX Framework.

Future architectural revisions SHALL preserve:

- architectural consistency;
- separation of concerns;
- documentation ownership;
- implementation independence.

New architectural elements MAY be introduced provided they comply with the principles and design rules defined by this specification.

---

# 15. Change History

| Version | Date | Description |
|----------|------|-------------|
| 1.x.x | Previous Releases | Initial architecture definition |
| 2.0.0 | 05/08/2026 | Major architectural refactoring introducing the Architectural Element Model, Runtime Infrastructure, Framework Services, Architectural Mechanisms, User Assets, Component Model separation and Runtime Architecture extraction. |
