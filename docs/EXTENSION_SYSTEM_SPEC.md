document_id:      MECH-EXT-001
title:            EduTeX Extension System Specification
type:             Component Specification
version:          1.0.0
status:           Draft
owner:            EduTeX Architectural Mechanisms
level:            3
parent:           ARCHITECTURE.md
normative_refs:
  - ARCHITECTURE.md
  - RUNTIME_ARCHITECTURE.md
  - SPECIFICATION_STANDARD.md
  - SPECIFICATION_TEMPLATE.md
informative_refs:
  - FRAMEWORK_SPEC.md
  - CORE_SPEC.md
  - ACTIVATOR_SPEC.md
  - KNOWLEDGE_SPEC.md
  - THEME_SPEC.md
  - LAYOUT_SPEC.md
  - STYLE_GUIDE.md

EduTeX Extension System Specification

1. Purpose

This document defines the specification of the Extension System architectural mechanism of the EduTeX Framework.

The Extension System is the first of two Architectural Mechanisms defined by ARCHITECTURE.md.

Its primary architectural capability is to coordinate the contribution of additional capabilities into the framework processing pipeline through a defined extension mechanism.

This document defines the responsibilities, architecture, interfaces, dependencies, and constraints of the Extension System.

This document SHALL NOT define implementation details, algorithms, or programming interfaces.

2. Intended Audience

This document is intended for:

software architects designing EduTeX Architectural Mechanisms;

Framework Service authors who expose or consume extension points;

contributors implementing or extending the Extension System;

reviewers validating Architectural Mechanism consistency.

3. Scope

3.1 In Scope

the architectural capability and coordination responsibility of the Extension System;

the extension model and extension lifecycle;

the extension point model and how components expose extension points;

the public architectural contracts exposed by the Extension System;

the dependencies the Extension System holds on the Runtime Infrastructure and Framework Services;

the architectural constraints governing the Extension System;

extension points for the extension mechanism itself.

3.2 Out of Scope

implementation technology and programming language;

internal extension dispatch algorithms;

educational content, visual styling, or document structure (owned by Framework Services);

output format generation (owned by the Build System);

the content of individual extensions (User Assets or third-party contributions);

runtime processing pipelines beyond Extension Processing (defined in RUNTIME_ARCHITECTURE.md).

4. Normative References

Document

Role

ARCHITECTURE.md

Normative

RUNTIME_ARCHITECTURE.md

Normative

SPECIFICATION_STANDARD.md

Normative

SPECIFICATION_TEMPLATE.md

Normative

5. Overview

5.1 Position in the Architecture

The Extension System is an Architectural Mechanism as defined by ARCHITECTURE.md §10.4 and §11.3.

Unlike Framework Services components, it does not own a business responsibility.

It coordinates collaboration between Architectural Components by providing a defined mechanism through which additional capabilities can be contributed into the processing pipeline without modifying existing components.

The Extension System operates during the Extension Processing stage of the Processing Model, which follows Layout Processing.

5.2 Architectural Capability

The architectural capability of the Extension System is:

Coordinates the contribution of additional capabilities into the framework processing pipeline through a defined extension mechanism.

This capability encompasses:

maintaining the registry of declared extension points exposed by Framework Services components;

loading and validating extensions registered in the activated framework state;

coordinating extension contribution at each declared extension point during Extension Processing;

enforcing extension isolation so that extensions cannot modify core component behavior;

propagating fatal errors through the Error Contract (CC-003) when extension loading or contribution fails.

5.3 Relationship to Other Components

The Extension System depends on the Runtime Infrastructure through ACT-001.

The Extension System coordinates with Framework Services components (Knowledge, Theme, Layout) by consuming their declared extension points through EXT-002.

The Extension System does not own the responsibilities of any Framework Services component.

Extensions are User Assets or third-party contributions. The Extension System does not own extension content.

6. Responsibilities

6.1 Primary Responsibility

The Extension System SHALL coordinate the contribution of additional capabilities into the framework processing pipeline without modifying existing component behavior.

6.2 Responsibility List

The Extension System is responsible for:

maintaining the registry of extension points declared by Framework Services components through EXT-002;

loading extensions from the activated framework state via ACT-001 during the Initialization phase;

validating that loaded extensions conform to the Extension Contract (EXT-001);

coordinating extension contribution at each declared extension point during Extension Processing;

enforcing extension isolation: extensions SHALL NOT modify the internal state of any Framework Services component;

enforcing extension ordering when multiple extensions target the same extension point;

propagating fatal errors through CC-003 when a required extension cannot be loaded or fails during contribution;

coordinating extension deactivation during the Termination phase.

6.3 Responsibility Boundaries

The Extension System SHALL NOT own educational content, visual styling, or document structure.

The Extension System SHALL NOT modify the behavior of Core, Configuration, Registry, Resolver, or Activator.

The Extension System SHALL NOT produce output formats. Output generation belongs to the Build System.

The Extension System SHALL NOT own extension content. Extensions are independent contributions.

The Extension System SHALL NOT allow extensions to bypass the public contracts of Framework Services components.

7. Architecture

7.1 Extension Model

An extension is a self-contained contribution that provides additional capability at a declared extension point.

Extensions are loaded from the activated framework state and validated against EXT-001 before contribution.

Each extension declares which extension point it targets.

Extensions SHALL NOT have side effects on components other than the one that declared the target extension point.

7.2 Extension Point Model

An extension point is a declared location within a Framework Services component where additional capability may be contributed.

Extension points are declared by Framework Services components through EXT-002.

Each extension point has a defined contract specifying the shape of acceptable contributions.

The Extension System maintains the registry of all declared extension points for the duration of the Runtime Lifecycle.

7.3 Extension Processing Stage

Extension Processing is the fourth stage of the Processing Model as defined by RUNTIME_ARCHITECTURE.md.

It follows Layout Processing and precedes Build System output generation.

During Extension Processing, the Extension System coordinates contribution at each declared extension point in a deterministic order.

7.4 Extension Isolation

Extensions operate within the boundaries defined by the extension point contract.

Extensions SHALL NOT access the internal state of any component.

Extensions SHALL interact with components exclusively through their public architectural contracts.

The Extension System enforces this isolation by mediating all extension contributions.

7.5 Relationship to Runtime Infrastructure

The Extension System accesses the activated framework state through ACT-001 to obtain loaded extensions and validated configuration through CFG-001.

The Extension System uses CC-003 to propagate fatal extension errors.

8. Interfaces

8.1 Public Architectural Contracts

The Extension System exposes the following public architectural contracts.

EXT-001 — Extension Contract

Purpose: Defines the structure, required fields, and constraints that an extension must satisfy to be accepted by the Extension System.

Consumers: Extension authors, Framework Services components declaring extension points.

Guarantee: Only extensions conforming to this contract SHALL be loaded and coordinated by the Extension System.

Constraint: Extensions SHALL declare exactly one target extension point per extension unit.

EXT-002 — Extension Point Contract

Purpose: Defines the protocol by which Framework Services components declare extension points and receive extension contributions.

Consumers: Knowledge, Theme, Layout.

Guarantee: Extension contributions delivered through this contract SHALL have been validated against EXT-001.

Constraint: Framework Services components SHALL NOT receive extension contributions from sources other than the Extension System.

8.2 Consumed Contracts

The Extension System consumes the following contracts from upstream components.

Contract

Source

Purpose

ACT-001 Activation Contract

Activator

Access to the activated framework state, including loaded extensions.

CFG-001 Configuration Contract

Configuration

Validated configuration governing extension loading and ordering.

CC-003 Error Contract

Core

Propagates fatal extension processing errors.

KNOW-001 Knowledge Content Contract

Knowledge

Read-only access to the content model at Knowledge extension points.

THEME-001 Theme Contract

Theme

Read-only access to the styled representation at Theme extension points.

LAYOUT-001 Layout Contract

Layout

Read-only access to the document structure at Layout extension points.

8.3 Contract Stability

All public contracts defined in §8.1 are architectural contracts.

They SHALL NOT be modified without a corresponding revision of this specification and ARCHITECTURE.md.

Consumers SHALL depend only on these contracts, not on Extension System internals.

9. Dependencies

9.1 Upstream Dependencies

Component

Contract Consumed

Reason

Activator

ACT-001

Access to the activated framework state and loaded extensions.

Configuration

CFG-001

Validated configuration governing extension loading and ordering.

Core

CC-003

Propagates fatal extension processing errors.

Knowledge

KNOW-001

Read-only access to content model at Knowledge extension points.

Theme

THEME-001

Read-only access to styled representation at Theme extension points.

Layout

LAYOUT-001

Read-only access to document structure at Layout extension points.

The Extension System SHALL NOT depend on the Build System.

9.2 Normative Document Dependencies

Document

Dependency Reason

ARCHITECTURE.md

Defines Architectural Mechanisms and the Extension System role.

RUNTIME_ARCHITECTURE.md

Defines Extension Processing stage and its position in the Processing Model.

9.3 Downstream Dependents

The Extension System has no downstream Framework Services dependents.

Extensions contribute capabilities into Framework Services components at declared extension points.

The Build System operates after Extension Processing completes.

10. Constraints

10.1 Architectural Constraints

The following constraints govern the Extension System.

EXT-C-001 — No Business Responsibility Ownership

The Extension System SHALL NOT own educational content, visual styling, or document structure responsibilities.

These belong exclusively to Knowledge, Theme, and Layout respectively.

EXT-C-002 — No Core Infrastructure Modification

The Extension System SHALL NOT modify the behavior of Core, Configuration, Registry, Resolver, or Activator.

EXT-C-003 — Extension Isolation

Extensions SHALL NOT access the internal state of any component directly.

The Extension System SHALL enforce this isolation by mediating all extension contributions through EXT-002.

EXT-C-004 — No Output Generation

The Extension System SHALL NOT produce output formats or final document representations.

Output generation belongs to the Build System.

EXT-C-005 — Validation Before Contribution

The Extension System SHALL NOT coordinate contribution of an extension that has not been validated against EXT-001.

EXT-C-006 — Deterministic Extension Ordering

Extension contributions at each extension point SHALL be coordinated in a deterministic order.

The ordering SHALL be governed by the validated configuration (CFG-001).

EXT-C-007 — Fatal Error on Extension Failure

If a required extension fails to load or fails during contribution, the Extension System SHALL propagate a fatal error through CC-003.

EXT-C-008 — Technology Independence

The Extension System SHALL remain independent from any specific implementation technology.

11. Extension Points

11.1 Extension Point Registry Evolution

Future versions MAY introduce additional extension points within existing Framework Services components.

New extension points SHALL be declared through EXT-002 and SHALL NOT modify the public contracts of the declaring component.

11.2 Extension Versioning

Future versions MAY introduce a versioning mechanism within EXT-001 to allow extensions to declare compatibility with specific framework versions.

12. Examples

12.1 Extension Processing Sequence

The following illustrates the conceptual Extension Processing sequence.

Layout Processing completes
    │
    ▼
Extension System: loads extensions from activated state via ACT-001
    │
    ├── Extension fails EXT-001 validation
    │       │
    │       ▼
    │   CC-003: fatal error propagated
    │   Document generation halted
    │
    └── All extensions validated
            │
            ▼
        Extension System: iterates declared extension points (EXT-002)
            │
            ▼
        Extension System: coordinates contribution at each point
        in deterministic order
            │
            ├── Contribution fails
            │       │
            │       ▼
            │   CC-003: fatal error propagated
            │
            └── All contributions succeed
                    │
                    ▼
                Extension Processing complete
                Build System begins output generation

12.2 Extension Isolation Example

The following illustrates how extension isolation is enforced.

Extension targets Knowledge extension point "post-parse"
    │
    ▼
Extension System: mediates contribution via EXT-002
    │
    ▼
Extension: receives content node snapshot (read-only view)
Extension: returns augmented node data
    │
    ▼
Extension System: delivers augmented data to Knowledge extension point

-- WRONG --
Extension: directly modifies Knowledge internal state        ✗
Extension: calls KNOW-001 to rewrite content model          ✗
Extension: accesses Core Runtime Context directly           ✗

13. Future Evolution

13.1 Anticipated Extensions

Future versions of the Extension System MAY introduce:

a richer extension versioning and compatibility model within EXT-001;

support for optional extensions that degrade gracefully when unavailable;

an extension introspection API for tooling and diagnostic purposes.

13.2 Stability Commitment

The public contracts defined in §8 are considered stable.

Breaking changes to these contracts SHALL require a major version increment of this specification.

Additive changes SHALL be introduced as minor version increments.

13.3 Out-of-Scope Evolution

The following SHALL NOT be introduced into the Extension System in future versions:

ownership of educational content, styling, or structural responsibilities;

modification of Runtime Infrastructure behavior;

output format generation.

14. Summary — Quick Reference

Attribute

Value

Component

Extension System

Document ID

MECH-EXT-001

Architectural Layer

Architectural Mechanisms

Architectural Capability

Coordinates the contribution of additional capabilities into the framework processing pipeline

Primary Artifact

Coordinated extension contributions at declared extension points

Public Contracts

EXT-001 Extension Contract, EXT-002 Extension Point Contract

Consumed Contracts

ACT-001 (Activator); CFG-001 (Configuration); CC-003 (Core); KNOW-001 (Knowledge); THEME-001 (Theme); LAYOUT-001 (Layout)

Upstream Dependencies

Activator, Configuration, Core, Knowledge, Theme, Layout

Downstream Dependents

None (extensions contribute into Framework Services; Build System follows)

Key Constraints

No business ownership, extension isolation, deterministic ordering, validation before contribution

Extension Points

Extension Point Registry Evolution, Extension Versioning

15. Change History

Version

Date

Description

1.0.0

2026-08-21

Initial release

End of document.
