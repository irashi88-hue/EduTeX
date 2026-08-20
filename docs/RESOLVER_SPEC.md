document_id:      COMP-RES-001
title:            EduTeX Resolver Component Specification
type:             Component Specification
version:          1.0.1
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
  - REGISTRY_SPEC.md
  - STYLE_GUIDE.md

EduTeX Resolver Component Specification

1. Purpose

This document defines the specification of the Resolver component of the EduTeX Framework.

Resolver is the fourth component in the Runtime Infrastructure layer, downstream of Core, Configuration, and Registry.

Its primary architectural capability is to resolve relationships and references between registered runtime entities.

This document defines the responsibilities, architecture, interfaces, dependencies, and constraints of Resolver.

This document SHALL NOT define implementation details, algorithms, or programming interfaces.

2. Intended Audience

This document is intended for:

software architects designing EduTeX Runtime Infrastructure components;

component specification authors whose entities participate in resolution;

contributors implementing or extending the Resolver component;

reviewers validating Runtime Infrastructure consistency.

3. Scope

3.1 In Scope

the architectural capability and primary responsibility of Resolver;

the resolution model and resolution lifecycle;

the public architectural contracts exposed by Resolver;

the dependencies Resolver holds on Core, Configuration, and Registry;

the architectural constraints governing Resolver;

extension points for resolution strategy evolution.

3.2 Out of Scope

implementation technology and programming language;

internal resolution algorithms and graph traversal strategies;

educational content, document-specific logic, or user assets;

entity registration (defined in REGISTRY_SPEC.md);

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

Resolver is the fourth component in the Runtime Infrastructure Dependency Model defined by ARCHITECTURE.md.

It depends on Core, Configuration, and Registry, and is consumed by Activator.

Resolver operates after the registration window closes and before Activator begins entity activation.

Resolver is the single component responsible for establishing the resolved relationship graph used by Activator.

5.2 Architectural Capability

The architectural capability of Resolver is:

Resolves relationships and references between registered runtime entities.

This capability encompasses:

reading the authoritative registry through REG-001;

identifying and traversing declared relationships and references between registered entities;

producing a resolved entity graph that makes relationships explicit and navigable;

detecting and reporting unresolvable references and circular dependencies;

making the resolved graph available to Activator through a stable public contract.

5.3 Relationship to Other Components

Resolver depends on Core for the Runtime Context (CC-001) and the Lifecycle Contract (CC-002).

Resolver depends on Configuration for validated configuration values (CFG-001) that govern resolution rules and constraints.

Resolver depends on Registry for read-only access to the authoritative entity registry (REG-001).

Resolver is consumed exclusively by Activator, which uses the resolved entity graph (RES-001) to determine activation order and entity relationships.

Framework Services do not consume Resolver directly; they interact with resolution outcomes through Activator.

6. Responsibilities

6.1 Primary Responsibility

Resolver SHALL resolve relationships and references between registered runtime entities.

6.2 Responsibility List

Resolver is responsible for:

reading all registered entities from Registry through REG-001 after the registration window closes;

identifying all declared relationships and references between registered entities;

traversing the entity graph to establish resolved relationships;

detecting unresolvable references and reporting them through the Error Contract (CC-003);

detecting circular dependencies within the entity graph and reporting them through CC-003;

producing the resolved entity graph as the primary output of the resolution pass;

exposing the resolved entity graph through the Resolution Contract (RES-001) for consumption by Activator;

completing the resolution pass before Activator begins entity activation.

6.3 Responsibility Boundaries

Resolver SHALL NOT register new entities into Registry.

Resolver SHALL NOT activate or initialize any entity.

Resolver SHALL NOT manage configuration values.

Resolver SHALL NOT contain educational knowledge or document-specific logic.

Resolver SHALL NOT modify the authoritative registry maintained by Registry.

Resolver SHALL NOT perform resolution before the registration window closes.

7. Architecture

7.1 Resolution Model

The resolution model defines how Resolver transforms the flat authoritative entity registry into a resolved entity graph.

The resolved entity graph makes the relationships and references between entities explicit and navigable.

The resolved entity graph is the primary architectural artifact produced by Resolver.

The resolved entity graph is produced once, during the Resolution phase of the Runtime Lifecycle.

After the resolution pass completes, the resolved entity graph SHALL be treated as immutable.

7.2 Resolution Lifecycle

Resolver operates within a defined resolution window.

The resolution window opens after the registration window of Registry closes.

The resolution window closes upon successful completion of the resolution pass.

Resolver SHALL complete the resolution pass before Activator begins activation.

The resolution pass is a single, complete traversal of all registered entities and their declared relationships.

7.3 Reference Types

Resolver recognizes references declared between registered entities.

A reference is a declared relationship from one entity to another, identified by entity type and identifier.

References may be:

direct: one entity explicitly names another entity as a dependency or relationship;

typed: the relationship has a declared type that constrains how Resolver interprets it.

The set of recognized reference types is determined by the entity registration contract (REG-002) and the configuration (CFG-001).

7.4 Error Conditions

Resolver identifies two categories of resolution errors.

The first category is unresolvable references: a declared reference points to an entity identifier that does not exist in the registry.

The second category is circular dependencies: a set of entities form a reference cycle with no acyclic resolution order.

Both error categories SHALL be propagated through the Error Contract (CC-003) as fatal errors.

The framework SHALL NOT proceed to the activation phase if resolution errors are present.

7.5 Resolved Entity Graph

The resolved entity graph is an augmented representation of the registered entities.

It preserves all entity records from the authoritative registry and adds explicit, navigable relationship edges.

The resolved entity graph is the sole input to Activator for determining activation order and entity relationships.

The resolved entity graph SHALL NOT be modified after the resolution pass completes.

7.6 Relationship to Registry

Resolver consumes REG-001 in read-only mode.

Resolver SHALL NOT modify the authoritative registry.

The resolved entity graph is a separate artifact produced by Resolver; it is not a modification of the registry.

8. Interfaces

8.1 Public Architectural Contracts

Resolver exposes the following public architectural contracts.

RES-001 — Resolution Contract

Purpose: Provides read-only access to the resolved entity graph produced by the resolution pass.

Consumers: Activator.

Guarantee: The resolved entity graph exposed through this contract SHALL reflect all registered entities and their resolved relationships, with no unresolvable references or circular dependencies.

Constraint: This contract is strictly read-only. Consumers SHALL NOT modify the resolved entity graph.

Constraint: This contract SHALL NOT be available before the resolution pass completes successfully.

RES-002 — Resolution Error Contract

Purpose: Defines the structure of resolution error reports produced when unresolvable references or circular dependencies are detected.

Consumers: Core (via CC-003), diagnostic tooling.

Guarantee: Every resolution error SHALL be represented in a consistent structure identifying the affected entities and the nature of the error.

Constraint: Resolution errors SHALL be propagated through CC-003 as fatal errors.

8.2 Consumed Contracts

Resolver consumes the following contracts from upstream components.

Contract

Source

Purpose

CC-001 Runtime Context Contract

Core

Access to the shared Runtime Context.

CC-002 Lifecycle Contract

Core

Determines the resolution window boundaries.

CC-003 Error Contract

Core

Propagates fatal resolution errors.

CFG-001 Configuration Contract

Configuration

Validated configuration governing resolution rules and reference types.

REG-001 Registry Contract

Registry

Read-only access to the authoritative entity registry.

REG-002 Entity Registration Contract

Registry

Informs Resolver of recognized reference types and entity structure.

8.3 Contract Stability

All public contracts defined in §8.1 are architectural contracts.

They SHALL NOT be modified without a corresponding revision of this specification and ARCHITECTURE.md.

Consumers SHALL depend only on these contracts, not on Resolver internals.

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

Determines the resolution window boundaries.

Core

CC-003

Propagates fatal resolution errors.

Configuration

CFG-001

Validated configuration governing resolution rules.

Registry

REG-001

Read-only access to the authoritative entity registry.

Resolver SHALL NOT depend on Activator or any Framework Service.

9.2 Normative Document Dependencies

Document

Dependency Reason

ARCHITECTURE.md

Defines the Runtime Infrastructure model and dependency rules.

RUNTIME_ARCHITECTURE.md

Defines the Runtime Lifecycle and resolution phase ordering.

9.3 Downstream Dependents

Component

Contract Consumed

Dependency Nature

Activator

RES-001

Consumes the resolved entity graph to determine activation order.

10. Constraints

10.1 Architectural Constraints

The following constraints govern Resolver.

RES-C-001 — No Registration

Resolver SHALL NOT register new entities into Registry.

RES-C-002 — No Activation

Resolver SHALL NOT activate or initialize any entity.

This responsibility belongs exclusively to Activator.

RES-C-003 — Read-Only Registry Access

Resolver SHALL access the authoritative registry exclusively through REG-001 in read-only mode.

Resolver SHALL NOT modify the authoritative registry maintained by Registry.

RES-C-004 — Resolution After Registration Closure

Resolver SHALL NOT begin the resolution pass before the registration window of Registry closes.

RES-C-005 — Fatal Error on Unresolvable Reference

If a declared reference cannot be resolved to a registered entity, Resolver SHALL propagate a fatal error through CC-003.

The framework SHALL NOT proceed to the activation phase.

RES-C-006 — Fatal Error on Circular Dependency

If the entity graph contains a circular dependency, Resolver SHALL propagate a fatal error through CC-003.

The framework SHALL NOT proceed to the activation phase.

RES-C-007 — Immutable Resolved Graph

The resolved entity graph SHALL be treated as immutable after the resolution pass completes.

RES-C-008 — No Educational Logic

Resolver SHALL NOT contain educational knowledge, domain-specific logic, or user content.

RES-C-009 — No Downstream Dependencies

Resolver SHALL NOT depend on Activator or any Framework Service.

RES-C-010 — Technology Independence

Resolver SHALL remain independent from any specific implementation technology.

This specification defines behavior and contracts, not implementation.

11. Extension Points

11.1 Reference Type Extension

Future versions MAY introduce additional reference types recognized during resolution.

New reference types SHALL be introduced through the entity registration contract (REG-002) and the configuration schema.

Existing reference types SHALL NOT be removed or incompatibly modified without a major version increment.

11.2 Resolution Strategy Extension

Future versions MAY introduce alternative resolution strategies for specific entity type combinations.

Resolution strategy extensions SHALL remain transparent to consumers of RES-001.

Consumers SHALL observe only the resolved entity graph, not the strategy used to produce it.

12. Examples

12.1 Resolution Pass Sequence

The following illustrates the conceptual resolution pass.

Registry: registration window closes
    │
    ▼
Resolver: resolution window opens
    │
    ▼
Resolver: reads all entities via REG-001
    │
    ▼
Resolver: traverses declared references between entities
    │
    ├── Unresolvable reference detected
    │       │
    │       ▼
    │   CC-003 Error Contract: fatal error propagated
    │   Framework execution halted
    │
    ├── Circular dependency detected
    │       │
    │       ▼
    │   CC-003 Error Contract: fatal error propagated
    │   Framework execution halted
    │
    └── All references resolved successfully
            │
            ▼
        Resolver: resolved entity graph produced
            │
            ▼
        RES-001 Resolution Contract: available to Activator

12.2 Reference Resolution Example

The following illustrates how Resolver handles a direct reference between two entities.

Entity A (type: Theme) declares reference → Entity B (type: Layout, id: "default")
    │
    ▼
Resolver: looks up entity with type Layout and id "default" in REG-001
    │
    ├── Entity not found
    │       │
    │       ▼
    │   RES-002: unresolvable reference error for Entity A → "default"
    │   CC-003: fatal error propagated                              ✗
    │
    └── Entity found
            │
            ▼
        Resolver: adds resolved edge A → B in resolved entity graph  ✓

13. Future Evolution

13.1 Anticipated Extensions

Future versions of Resolver MAY introduce:

a richer resolution error report within RES-002, including suggested corrections;

support for optional references that do not cause fatal errors when unresolvable;

a resolution introspection API for diagnostic tooling.

13.2 Stability Commitment

The public contracts defined in §8 are considered stable.

Breaking changes to these contracts SHALL require a major version increment of this specification.

Additive changes SHALL be introduced as minor version increments.

13.3 Out-of-Scope Evolution

The following SHALL NOT be introduced into Resolver in future versions:

entity registration or activation logic;

educational content or domain-specific logic;

mutable resolved graph state after the resolution pass completes;

reverse dependencies on Activator or Framework Services.

14. Summary — Quick Reference

Attribute

Value

Component

Resolver

Document ID

COMP-RES-001

Architectural Layer

Runtime Infrastructure

Architectural Capability

Resolves relationships and references between registered runtime entities

Primary Artifact

Resolved entity graph

Public Contracts

RES-001 Resolution Contract, RES-002 Resolution Error Contract

Consumed Contracts

CC-001, CC-002, CC-003 (Core); CFG-001 (Configuration); REG-001 (Registry)

Upstream Dependencies

Core, Configuration, Registry

Downstream Dependents

Activator

Key Constraints

Read-only registry access, resolution after registration closure, immutable graph

Extension Points

Reference Type Extension, Resolution Strategy Extension

15. Change History

Version

Date

Description

1.0.1

2026-08-20

Add REG-002 to §8.2 consumed contracts table (review fix)

1.0.0

2026-08-11

Initial release

End of document.
