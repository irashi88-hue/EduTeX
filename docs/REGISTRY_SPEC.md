document_id:      COMP-REG-001
title:            EduTeX Registry Component Specification
type:             Component Specification
version:          1.0.0
status:           Draft
owner:            EduTeX Runtime Infrastructure
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
  - CONFIGURATION_SPEC.md
  - STYLE_GUIDE.md

EduTeX Registry Component Specification

1. Purpose

This document defines the specification of the Registry component of the EduTeX Framework.

Registry is the third component in the Runtime Infrastructure layer, downstream of Core and Configuration.

Its primary architectural capability is to maintain the authoritative registry of runtime entities managed by the framework.

This document defines the responsibilities, architecture, interfaces, dependencies, and constraints of Registry.

This document SHALL NOT define implementation details, algorithms, or programming interfaces.

2. Intended Audience

This document is intended for:

software architects designing EduTeX Runtime Infrastructure components;

component specification authors who register or look up runtime entities;

contributors implementing or extending the Registry component;

reviewers validating Runtime Infrastructure consistency.

3. Scope

3.1 In Scope

the architectural capability and primary responsibility of Registry;

the runtime entity model and registration lifecycle;

the public architectural contracts exposed by Registry;

the dependencies Registry holds on Core and Configuration;

the architectural constraints governing Registry;

extension points for entity type evolution.

3.2 Out of Scope

implementation technology and programming language;

internal storage mechanisms and data structures;

educational content, document-specific logic, or user assets;

reference resolution between entities (defined in RESOLVER_SPEC.md);

entity activation and initialization (defined in ACTIVATOR_SPEC.md);

responsibilities belonging to Core or Configuration;

runtime processing pipelines (defined in RUNTIME_ARCHITECTURE.md).

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

Registry is the third component in the Runtime Infrastructure Dependency Model defined by ARCHITECTURE.md.

It depends on Core and Configuration, and is consumed by Resolver and Activator.

Registry is the single authoritative source of truth for all runtime entities within the framework.

No other component SHALL maintain a parallel registry of runtime entities.

5.2 Architectural Capability

The architectural capability of Registry is:

Maintains the authoritative registry of runtime entities managed by the framework.

This capability encompasses:

accepting registrations of runtime entities from authorized sources;

maintaining the registry as the single authoritative source of runtime entity definitions;

exposing registered entities for lookup by Resolver and Activator;

enforcing registration rules and entity uniqueness;

managing the registration lifecycle in alignment with the Runtime Lifecycle.

5.3 Relationship to Other Components

Registry depends on Core for the Runtime Context (CC-001) and the Lifecycle Contract (CC-002).

Registry depends on Configuration for validated configuration values (CFG-001) relevant to registration rules and entity constraints.

Registry is consumed by Resolver, which queries it to locate entities during reference resolution.

Registry is consumed by Activator, which queries it to locate entities prior to activation.

Framework Services register their entities with Registry during the Initialization phase.

6. Responsibilities

6.1 Primary Responsibility

Registry SHALL maintain the authoritative registry of runtime entities managed by the framework.

6.2 Responsibility List

Registry is responsible for:

accepting and recording registrations of runtime entities submitted during the Initialization phase;

enforcing entity uniqueness within each entity type namespace;

maintaining the authoritative registry for the duration of the Runtime Lifecycle;

exposing registered entities through the Registry Contract (REG-001) for lookup by authorized consumers;

validating that registered entities conform to the entity registration contract (REG-002);

propagating fatal errors through the Error Contract (CC-003) when registration fails due to constraint violations;

managing the closure of the registry at the appropriate Runtime Lifecycle phase.

6.3 Responsibility Boundaries

Registry SHALL NOT resolve references or relationships between entities.

Registry SHALL NOT activate or initialize registered entities.

Registry SHALL NOT manage configuration values.

Registry SHALL NOT contain educational knowledge or document-specific logic.

Registry SHALL NOT allow registration of entities outside the designated registration window.

Registry SHALL NOT allow duplicate registrations within the same entity type namespace unless explicitly permitted by the configuration.

7. Architecture

7.1 Runtime Entity Model

A runtime entity is any framework-managed element that must be known to the framework before it can be resolved or activated.

Runtime entities are typed: each entity belongs to exactly one entity type.

Entity types define the structure and constraints applicable to entities of that type.

The set of entity types recognized by Registry is defined by the configuration schema and the entity registration contract (REG-002).

7.2 Registration Lifecycle

The registry accepts registrations exclusively during the registration window.

The registration window opens at the start of the Initialization phase.

The registration window closes before the Resolver begins its resolution pass.

After the registration window closes, the registry SHALL be treated as read-only.

Attempts to register entities outside the registration window SHALL be rejected and reported through the Error Contract (CC-003).

7.3 Entity Uniqueness

Within each entity type namespace, entity identifiers SHALL be unique.

Registry SHALL reject duplicate registrations that violate uniqueness within the same namespace.

Duplicate detection is performed at registration time.

7.4 Registry Closure

Upon framework termination, Registry releases all registered entity records.

Registry closure is coordinated through the Lifecycle Contract (CC-002).

After closure, the registry SHALL NOT accept lookups or registrations.

7.5 Relationship to Configuration

Registry consumes CFG-001 to access configuration values that govern registration rules, entity type definitions, and namespace constraints.

Registry SHALL NOT own or modify configuration values.

7.6 Relationship to Core

Registry consumes CC-001 to access the Runtime Context.

Registry consumes CC-002 to determine the registration window boundaries.

Registry uses CC-003 to propagate fatal registration errors.

8. Interfaces

8.1 Public Architectural Contracts

Registry exposes the following public architectural contracts.

REG-001 — Registry Contract

Purpose: Provides read-only lookup access to the authoritative registry of registered runtime entities.

Consumers: Resolver, Activator.

Guarantee: Entities returned through this contract SHALL have been validated against the entity registration contract (REG-002) at registration time.

Constraint: This contract is strictly read-only. Consumers SHALL NOT modify registry state through this contract.

Constraint: This contract SHALL NOT be available before the registration window closes.

REG-002 — Entity Registration Contract

Purpose: Defines the structure, required fields, and constraints that a runtime entity must satisfy to be accepted by Registry.

Consumers: Framework Services and any authorized source submitting entity registrations.

Guarantee: Only entities conforming to this contract SHALL be accepted into the registry.

Constraint: This contract SHALL be stable within a major version of this specification.

8.2 Consumed Contracts

Registry consumes the following contracts from upstream components.

Contract

Source

Purpose

CC-001 Runtime Context Contract

Core

Access to the shared Runtime Context.

CC-002 Lifecycle Contract

Core

Determines the registration window boundaries.

CC-003 Error Contract

Core

Propagates fatal registration errors.

CFG-001 Configuration Contract

Configuration

Access to validated configuration governing registration rules.

8.3 Contract Stability

All public contracts defined in §8.1 are architectural contracts.

They SHALL NOT be modified without a corresponding revision of this specification and ARCHITECTURE.md.

Consumers SHALL depend only on these contracts, not on Registry internals.

9. Dependencies

9.1 Upstream Dependencies

Component

Contract Consumed

Reason

Core

CC-001

Access to the shared Runtime Context.

Core

CC-002

Determines registration window boundaries.

Core

CC-003

Propagates fatal registration errors.

Configuration

CFG-001

Validated configuration governing registration rules.

Registry SHALL NOT depend on Resolver or Activator.

9.2 Normative Document Dependencies

Document

Dependency Reason

ARCHITECTURE.md

Defines the Runtime Infrastructure model and dependency rules.

RUNTIME_ARCHITECTURE.md

Defines the Runtime Lifecycle and Initialization phase.

9.3 Downstream Dependents

Component

Contract Consumed

Dependency Nature

Resolver

REG-001

Queries the registry to locate entities for resolution.

Activator

REG-001

Queries the registry to locate entities for activation.

Framework Services submit entity registrations through REG-002 during the Initialization phase.

10. Constraints

10.1 Architectural Constraints

The following constraints govern Registry.

REG-C-001 — Single Authoritative Registry

Registry SHALL be the sole authoritative source of runtime entity records within the framework.

No other component SHALL maintain a parallel or shadow registry.

REG-C-002 — Registration Window Enforcement

Registry SHALL accept entity registrations only within the designated registration window.

Registrations submitted outside the registration window SHALL be rejected.

REG-C-003 — Entity Uniqueness

Within each entity type namespace, entity identifiers SHALL be unique.

Registry SHALL reject duplicate registrations that violate this constraint.

REG-C-004 — Read-Only After Closure

Once the registration window closes, the registry SHALL be treated as read-only.

No entity SHALL be added, modified, or removed after closure.

REG-C-005 — No Resolution or Activation

Registry SHALL NOT resolve references between entities.

Registry SHALL NOT activate or initialize any registered entity.

These responsibilities belong exclusively to Resolver and Activator respectively.

REG-C-006 — No Educational Logic

Registry SHALL NOT contain educational knowledge, domain-specific logic, or user content.

REG-C-007 — No Downstream Dependencies

Registry SHALL NOT depend on Resolver, Activator, or any Framework Service.

REG-C-008 — Technology Independence

Registry SHALL remain independent from any specific implementation technology.

This specification defines behavior and contracts, not implementation.

11. Extension Points

11.1 Entity Type Extension

Future versions MAY introduce additional entity types recognized by Registry.

New entity types SHALL be introduced through the entity registration contract (REG-002).

Existing entity types SHALL NOT be removed or incompatibly modified without a major version increment.

11.2 Namespace Extension

Future versions MAY introduce additional namespaces for entity type isolation.

Namespace extensions SHALL be additive and SHALL NOT affect existing namespaces.

12. Examples

12.1 Registration Sequence

The following illustrates the conceptual registration sequence.

Core: Initialization Phase begins
    │
    ▼
Registry: registration window opens
    │
    ▼
Framework Services: submit entity registrations via REG-002
    │
    ├── Entity fails REG-002 validation
    │       │
    │       ▼
    │   CC-003 Error Contract: fatal error propagated
    │   Framework execution halted
    │
    └── Entity passes REG-002 validation
            │
            ▼
        Registry: entity recorded in authoritative registry
            │
            ▼
        Registration window closes
            │
            ▼
        REG-001 Registry Contract: available to Resolver and Activator

12.2 Lookup and Uniqueness Example

The following illustrates a lookup and a rejected duplicate registration.

Resolver: queries REG-001 for entity of type T with identifier "X"
    │
    ▼
Registry: returns entity record for "X" of type T

-- Duplicate registration attempt --
Framework Service: submits entity of type T with identifier "X"
    │
    ▼
Registry: detects duplicate within namespace T
    │
    ▼
CC-003 Error Contract: registration error propagated   ✗

-- Correct usage --
Framework Service: submits entity of type T with identifier "Y"  ✓

13. Future Evolution

13.1 Anticipated Extensions

Future versions of Registry MAY introduce:

a richer entity type model with hierarchical namespaces;

a query API within REG-001 supporting filtered lookups by entity type or attribute;

diagnostic introspection capabilities for tooling and validation infrastructure.

13.2 Stability Commitment

The public contracts defined in §8 are considered stable.

Breaking changes to these contracts SHALL require a major version increment of this specification.

Additive changes SHALL be introduced as minor version increments.

13.3 Out-of-Scope Evolution

The following SHALL NOT be introduced into Registry in future versions:

reference resolution or activation logic;

educational content or domain-specific logic;

mutable registry state after the registration window closes;

reverse dependencies on Resolver, Activator, or Framework Services.

14. Summary — Quick Reference

Attribute

Value

Component

Registry

Document ID

COMP-REG-001

Architectural Layer

Runtime Infrastructure

Architectural Capability

Maintains the authoritative registry of runtime entities managed by the framework

Primary Artifact

Authoritative runtime entity registry

Public Contracts

REG-001 Registry Contract, REG-002 Entity Registration Contract

Consumed Contracts

CC-001, CC-002, CC-003 (Core); CFG-001 (Configuration)

Upstream Dependencies

Core, Configuration

Downstream Dependents

Resolver, Activator

Key Constraints

Single authoritative registry, registration window, read-only after closure

Extension Points

Entity Type Extension, Namespace Extension

15. Change History

Version

Date

Description

1.0.0

2026-08-11

Initial release

End of document.
