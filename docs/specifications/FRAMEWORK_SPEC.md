%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
%
% EduTeX Framework Specification
%
%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%

# EduTeX Framework Specification

---

Document ID: FW-SPEC-001

Version: 1.1.0

Status: Released

Classification: Authoritative

Owner: EduTeX Framework

Level: Level 1 — Framework

Parent Document: Vision



### Dependencies

None

### Related documents

- DIR-SPEC
- FILE-SPEC
- ARCHITECTURE.md
- RUNTIME_ARCHITECTURE.md

---

# Scope

This document defines the governing principles of the EduTeX framework.

It establishes the project's vision, design philosophy, architectural principles, development process and long-term evolution strategy.

The Framework Specification represents the primary governing document of the EduTeX project. Every architectural decision and implementation specification shall be derived from the principles defined in this document.

---

# Intended Audience

This document is intended for:

- Framework Maintainers
- Software Architects
- Contributors
- Technical Reviewers

It is expected to be read before any architectural or implementation specification.

---

# Document Dependencies

```
                    FRAMEWORK_SPEC
                           │
        ┌──────────────────┼──────────────────┐
        │                  │                  │
        ▼                  ▼                  ▼
  ARCHITECTURE       TERMINOLOGY      Repository Design
                                               │
                                               ▼
                                   Directory Specifications
                                               │
                                               ▼
                                      File Specifications
                                               │
                                               ▼
                                         Implementation
```

This document is the root specification of the EduTeX project.

---

# Out of Scope

The Framework Specification SHALL NOT define:

- static architecture;
- runtime execution;
- runtime lifecycle;
- processing pipelines;
- component internal behaviour.

This document intentionally does not define:

- implementation details;
- source code;
- LaTeX macros;
- repository file contents;
- testing procedures;
- component implementation.

Those aspects are specified in their respective documents.

---
# How to Read This Document

This specification is organized from high-level project principles to framework lifecycle and development practices.

Each section builds upon the concepts introduced in the previous ones, progressively refining the understanding of the EduTeX framework.

Readers unfamiliar with the project are encouraged to read the document sequentially.

Experienced contributors may instead use the Table of Contents to navigate directly to the relevant section.

This document intentionally focuses on governing principles rather than implementation details. Whenever a topic requires additional technical depth, the corresponding derived specification should be consulted.

# Table of Contents

- Part I - Project
    - I.1 Vision
    - I.2 Project Goals
    - I.3 Design Philosophy
    - I.4 Design Principles
- Part II - Framework
    - II.1 Framework Organization
    - II.2 Framework Lifecycle
    - II.3 Processing Flow
- Part III - Development
    - III.1 Build System
    - III.2 Documentation
    - III.3 Development Workflow
- Part IV - Evolution
    - IV.1 Future Extensions
- Appendices
    - Appendix A - Terminology
    - Appendix B - Naming Summary
    - Appendix C - References

## PART I — Project


The Project section defines the fundamental principles upon which the EduTeX framework is built.

It establishes the long-term vision of the project, its objectives, the design philosophy adopted during development and the principles governing all architectural and implementation decisions.

The EduTeX Framework is organized through a hierarchy of Architectural Elements.

The detailed architectural organization is defined by the Architecture Specification.

The concepts introduced in this part are normative and apply to every component of the framework.

-------------------------------------------------------------------------------

# I.1 Vision

## Purpose

Defines the long-term vision of the EduTeX project.

## Description

The EduTeX framework aims to provide a modular, maintainable and extensible infrastructure for creating educational documents using LaTeX.

Rather than focusing on a specific subject or publication, EduTeX provides a generic framework capable of supporting different educational domains while promoting consistency, reusability and long-term maintainability.

The framework is intended to evolve as a stable platform upon which books, notes and educational resources can be developed independently from the underlying infrastructure.

## Design Decisions

- EduTeX is an educational framework, not a single book.
- The framework shall remain domain-independent.
- Long-term maintainability has priority over short-term implementation speed.
- The framework is designed to support future growth without architectural redesign.

## Related Sections

- Project Goals
- Design Philosophy

-------------------------------------------------------------------------------

# I.2 Project Goals

## Purpose

Defines the primary objectives that guide the development of the EduTeX framework.

## Description

The project pursues a set of engineering objectives intended to ensure quality, maintainability and scalability throughout its lifecycle.

The goals represent measurable directions for the evolution of the framework rather than implementation requirements.

## Goals

- Create a reusable educational framework.
- Separate educational content from framework infrastructure.
- Promote modularity and low coupling.
- Maximize maintainability.
- Simplify future extensions.
- Support consistent document generation.
- Enable specification-driven development.
- Preserve architectural consistency across future versions.

## Design Decisions

Project goals are intentionally technology-independent and remain valid regardless of future implementation changes.

## Related Sections

- Vision
- Design Philosophy

-------------------------------------------------------------------------------

# I.3 Design Philosophy

## Purpose

Defines the engineering philosophy adopted throughout the EduTeX project.

## Description

EduTeX is developed according to engineering principles that prioritize clarity, consistency and maintainability over premature optimization or unnecessary complexity.

Architectural decisions are driven by long-term project sustainability rather than immediate implementation convenience.

The framework evolves incrementally through documented decisions and controlled architectural growth.

## Principles

- Simplicity over unnecessary complexity.
- Specification before implementation.
- Documentation before code.
- Modular architecture.
- Separation of responsibilities.
- Progressive refinement.
- Long-term maintainability.
- Consistency across the entire framework.

## Design Decisions

Every architectural decision shall be documented before implementation.

## Related Sections

- Design Principles
- Development Workflow

-------------------------------------------------------------------------------

# I.4 Design Principles

## Purpose

Defines the governing engineering principles applicable to the entire framework.

## Description

These principles provide the criteria used to evaluate architectural decisions throughout the project.

Every component of the framework shall comply with these principles unless an explicitly documented exception exists.

## Principles

- Separation of Concerns
- Single Responsibility
- Modularity
- Extensibility
- Reusability
- Low Coupling
- High Cohesion
- Specification-Driven Development
- Documentation as Single Source of Truth
- Consistency over Convenience

## Design Decisions

The Design Principles constitute the highest-level engineering constraints of the project and therefore apply to every derived specification.

## Related Sections

- Framework Lifecycle
- Development Workflow

---

## PART II — Framework


The Framework section describes the high-level organization and operational behavior of EduTeX.

It defines how the framework is structured, how it initializes, how it executes and how its components interact during document generation.

This section intentionally describes the framework from a conceptual perspective. Detailed component responsibilities and interactions are defined in the Architecture Specification.

-------------------------------------------------------------------------------

# II.1 Framework Organization

## Purpose

Provides a conceptual overview of the EduTeX repository organization.

## Description

The EduTeX repository is organized to separate framework infrastructure from educational content and project-specific resources.

The repository structure reflects the logical organization of the framework and promotes maintainability, modularity and scalability.

Its organization is designed to support independent evolution of framework components while preserving architectural consistency.

This section introduces the repository at a conceptual level only.

The physical directory hierarchy, responsibilities and dependencies are documented in the corresponding Repository and Directory Specifications.


## Principles

- Separate framework infrastructure from educational content.
- Organize the repository according to responsibilities.
- Minimize dependencies between directories.
- Preserve modularity.
- Support future extensions without structural redesign.

## Design Decisions

The repository organization follows the architectural decomposition of the framework rather than implementation convenience.

## Related Documents

- ARCH
- Directory Specifications

-------------------------------------------------------------------------------

# II.2 Framework Lifecycle

## Purpose

Describes the high-level lifecycle followed during framework execution.

## Description

The runtime lifecycle of the EduTeX Framework is defined by the Runtime Architecture Specification.

-------------------------------------------------------------------------------


# II.3 Processing Flow

## Purpose

Describes the conceptual processing sequence followed after framework initialization.

## Description

The document processing model is defined by the Runtime Architecture Specification.

---

## PART III — Development


The Development section defines the engineering practices adopted throughout the EduTeX project.

It establishes how the framework is built, documented and evolved in order to ensure long-term maintainability, consistency and architectural integrity.

The principles described in this section apply to every contribution made to the project.

-------------------------------------------------------------------------------

# III.1 Build System

## Purpose

Describes the conceptual organization of the EduTeX build system.

## Description

The build system is responsible for transforming the project sources into their final outputs through a deterministic and reproducible process.

Its primary objective is to provide a reliable development workflow while remaining independent from the educational content managed by the framework.

The implementation of the build system shall remain modular and extensible in order to support future improvements without affecting the framework architecture.

## Principles

- Reproducible builds.
- Deterministic execution.
- Automation whenever appropriate.
- Separation between build logic and framework logic.
- Extensibility.

## Design Decisions

The Build System is an Architectural Mechanism responsible for document generation.

Its architectural definition is provided by the Architecture Specification.

## Related Sections

- Development Workflow

## Related Documents

- ARCH

-------------------------------------------------------------------------------

# III.2 Documentation

## Purpose

Defines the role of documentation within the EduTeX project.

## Description

Documentation is considered a primary engineering artifact.

Every architectural decision shall be documented before implementation.

Documentation provides the governing knowledge of the project and represents the primary source of truth for contributors.

Project documentation evolves together with the framework through controlled reviews and versioned releases.

FRAMEWORK_SPEC

│

├── ARCHITECTURE

├── RUNTIME_ARCHITECTURE

└── COMPONENT_SPECIFICATIONS

## Principles

- Documentation before implementation.
- Single Source of Truth.
- Progressive refinement.
- Traceability.
- Consistency.
- Version-controlled evolution.

## Design Decisions

Documentation defines project knowledge.

Implementation realizes documented decisions.


## Related Documents

- Framework Specification
- ARCH
- TERM

-------------------------------------------------------------------------------

# III.3 Development Workflow

## Purpose

Defines the high-level workflow adopted for the evolution of the EduTeX project.

## Description

Development follows a specification-driven process in which engineering decisions are progressively refined before implementation.

Every contribution progresses through review and validation before becoming part of the project baseline.

The workflow prioritizes architectural consistency and long-term maintainability over implementation speed.

## Workflow

1. Requirements Definition
2. Specification Development
3. Technical Review
4. Editorial Review
5. Freeze
6. Implementation
7. Validation
8. Integration

The workflow is iterative and supports future refinement through controlled revisions.

## Principles

- Specification before implementation.
- Review before freeze.
- Freeze before development.
- Controlled evolution.
- Continuous improvement.

## Design Decisions

The Development Workflow governs the evolution of every governing and derived document within the EduTeX project.

## Related Documents

- Documentation
- Future Extensions

---

## PART IV — Evolution


The Evolution section defines the principles governing the long-term growth of the EduTeX framework.

It establishes how the project evolves while preserving architectural consistency, documentation quality and maintainability.

The objective of this section is to ensure that future extensions strengthen the framework rather than introduce architectural degradation.

-------------------------------------------------------------------------------

# IV.1 Future Extensions

## Purpose

Defines the principles governing the future evolution of the EduTeX framework.

## Description

EduTeX is designed to evolve incrementally through controlled architectural improvements.

Future extensions shall preserve the project's governing principles and integrate consistently with the existing framework.

The framework is intended to support new capabilities without requiring architectural redesign.

Every extension shall be evaluated from both technical and documentation perspectives before becoming part of the project baseline.

## Principles

- Preserve architectural consistency.
- Prefer extension over modification.
- Maintain backward compatibility whenever feasible.
- Minimize architectural disruption.
- Document every significant architectural decision.
- Keep documentation synchronized with framework evolution.
- Review changes before adoption.
- Evolve incrementally.

Future revisions SHALL preserve the separation between:

- Framework Vision
- Static Architecture
- Runtime Architecture
- Component Specifications.


## Design Decisions

Future extensions shall derive from the governing documents of the project.

Architectural changes shall be introduced through controlled revisions rather than implementation-driven decisions.

Every approved extension becomes part of the documented project knowledge and shall follow the same review and freeze process adopted for the existing framework.


## Related Sections

- Development Workflow

## Related Documents

- Framework Specification
- ARCH
- Documentation

---

# Appendices

# Appendix A — Terminology

## Purpose

Provide the official definitions of the technical and architectural terminology adopted throughout the EduTeX project.

## Organization

The terminology is organized into categories:

- Domain Terms
- Engineering Terms
- Repository Terms
- Lifecycle Terms
- Documentation Terms

Each term shall include:

- Definition
- Context
- Related Terms
- Referenced By


-------------------------------------------------------------------------------

# Appendix B — Naming Summary

## Purpose

Summarize the official naming conventions adopted throughout the project.

Examples include:

- Document IDs
- Directory naming
- File naming
- Component naming
- Specification naming

-------------------------------------------------------------------------------

# Appendix C — References

## Purpose

List the external references used by the project.

Examples:

- ECSS
- ISO
- LaTeX
- TeX

-------------------------------------------------------------------------------



# Revision History

| Version | Date | Description |
|----------|------|-------------|
| 1.0.0-RC1 | 28/07/2026 | First assembled release candidate |
| 1.1.0 | 05/08/2026 | Minor issue aligned with V2 architecture |

-------------------------------------------------------------------------------

# Document Status

Status: Released

Next Milestone:

Framework Specification v1.1.0 (Frozen)
