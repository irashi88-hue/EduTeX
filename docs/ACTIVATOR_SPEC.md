document_id:      COMP-ACT-001
title:            EduTeX Activator Component Specification
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
  - REGISTRY_SPEC.md
  - RESOLVER_SPEC.md
  - STYLE_GUIDE.md

EduTeX Activator Component Specification

1. Purpose

This document defines the specification of the Activator component of the EduTeX Framework.

Activator is the fifth and final component in the Runtime Infrastructure layer, downstream of Core, Configuration, Registry, and Resolver.

Its primary architectural capability is to activate runtime entities according to the Runtime Lifecycle.

This document defines the responsibilities, architecture, interfaces, dependencies, and constraints of Activator.

This document SHALL NOT define implementation details, algorithms, or programming interfaces.

2. Intended Audience

This document is intended for:

software architects designing EduTeX Runtime Infrastructure components;

Framework Service authors whose entities are subject to activation;

contributors implementing or extending the Activator component;

reviewers validating Runtime Infrastructure consistency.

3. Scope

3.1 In Scope

the architectural capability and primary responsibility of Activator;

the activation model and activation lifecycle;

the public architectural contracts exposed by Activator;

the dependencies Activator holds on Core, Configuration, Registry, and Resolver;

the architectural constraints governing Activator;

extension points for activation order and lifecycle hook evolution.

3.2 Out of Scope

implementation technology and programming language;

internal activation algorithms and ordering strategies;

educational content, document-specific logic, or user assets;

entity registration (defined in REGISTRY_SPEC.md);

reference resolution (defined in RESOLVER_SPEC.md);

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

Activator is the fifth and terminal component in the Runtime Infrastructure Dependency Model defined by ARCHITECTURE.md.

It depends on all four preceding components: Core, Configuration, Registry, and Resolver.

Activator operates after the resolution pass completes and produces the activated framework state that Framework Services consume.

No other Runtime Infrastructure component depends on Activator.

5.2 Architectural Capability

The architectural capability of Activator is:

Activates runtime entities according to the Runtime Lifecycle.

This capability encompasses:

consuming the resolved entity graph from Resolver through RES-001;

determining the correct activation order for all resolved entities;

performing entity activation in dependency order;

managing the activation lifecycle of each entity from pre-activation through active state;

exposing the activated framework state to Framework Services through a stable public contract;

detecting and reporting activation failures through the Error Contract (CC-003).

5.3 Relationship to Other Components

Activator depends on Core for the Runtime Context (CC-001), the Lifecycle Contract (CC-002), and the Error Contract (CC-003).

Activator depends on Configuration for validated configuration values (CFG-001) that govern activation rules and constraints.

Activator depends on Registry for read-only entity lookup (REG-001) when additional entity metadata is required during activation.

Activator depends on Resolver for the resolved entity graph (RES-001), which is the primary input for determining activation order.

Framework Services consume the Activation Contract (ACT-001) to access the activated framework state and to interact with activated entities.

6. Responsibilities

6.1 Primary Responsibility

Activator SHALL activate runtime entities according to the Runtime Lifecycle.

6.2 Responsibility List

Activator is responsible for:

consuming the resolved entity graph from Resolver through RES-001 after the resolution pass completes;

computing the activation order for all resolved entities, respecting the dependency relationships expressed in the resolved entity graph;

performing entity activation in the computed order, ensuring that an entity is activated only after all its dependencies are active;

managing the activation lifecycle of each entity: pre-activation, activation, and post-activation;

propagating fatal errors through the Error Contract (CC-003) when an entity fails to activate;

exposing the activated framework state through the Activation Contract (ACT-001) once all entities are active;

coordinating entity deactivation during the Termination phase of the Runtime Lifecycle in reverse activation order.

6.3 Responsibility Boundaries

Activator SHALL NOT register new entities into Registry.

Activator SHALL NOT perform reference resolution between entities.

Activator SHALL NOT manage configuration values.

Activator SHALL NOT contain educational knowledge or document-specific logic.

Activator SHALL NOT begin activation before the resolution pass completes successfully.

Activator SHALL NOT activate entities in an order that violates the dependency relationships expressed in the resolved entity graph.

7. Architecture

7.1 Activation Model

The activation model defines how Activator transforms the resolved entity graph into an activated framework state.

The activated framework state is the primary architectural artifact produced by Activator.

It represents the collection of all entities that have been successfully activated and are ready to serve their runtime responsibilities.

The activated framework state is established during the Activation phase of the Runtime Lifecycle.

Once all entities are active, the activated framework state is exposed through ACT-001 and remains available until the Termination phase begins.

7.2 Activation Order

Activator determines activation order by traversing the resolved entity graph produced by Resolver.

Activation order SHALL respect dependency relationships: an entity SHALL NOT be activated before all entities it depends on are active.

The activation order is derived from the resolved entity graph and SHALL NOT be modified by consumers.

If the resolved entity graph contains no dependency relationships between two entities, their relative activation order is determined by Activator according to its internal ordering strategy.

7.3 Activation Lifecycle

Each entity undergoes a three-phase activation lifecycle.

The first phase is pre-activation: Activator prepares the entity for activation, verifying that all dependencies are active.

The second phase is activation: Activator performs the activation of the entity, transitioning it to the active state.

The third phase is post-activation: Activator confirms that the entity has reached the active state and records it in the activated framework state.

If any phase fails, Activator propagates a fatal error through CC-003 and halts framework execution.

7.4 Deactivation

During the Termination phase of the Runtime Lifecycle, Activator coordinates the deactivation of all active entities.

Deactivation proceeds in reverse activation order, ensuring that an entity is deactivated before any entity it depends on.

Deactivation failures are reported through CC-003 but do not prevent subsequent deactivations from proceeding.

7.5 Activated Framework State

The activated framework state is the collection of all entities that have successfully completed activation.

It is exposed through ACT-001 to Framework Services, which consume it to perform their runtime responsibilities.

The activated framework state SHALL be consistent: no entity SHALL appear as active unless it has completed all three activation lifecycle phases.

The activated framework state SHALL remain stable throughout the Processing phase of the Runtime Lifecycle.

7.6 Relationship to Resolver

Activator consumes RES-001 exclusively in read-only mode.

The resolved entity graph is the authoritative input for activation order determination.

Activator SHALL NOT modify the resolved entity graph.

8. Interfaces

8.1 Public Architectural Contracts

Activator exposes the following public architectural contracts.

ACT-001 — Activation Contract

Purpose: Provides access to the activated framework state, including all active entities and their runtime representations.

Consumers: Framework Services (Knowledge, Theme, Layout).

Guarantee: Entities accessible through this contract SHALL have completed all three activation lifecycle phases. No partially activated entity SHALL be exposed.

Constraint: This contract SHALL NOT be available before all entities have been successfully activated.

Constraint: Framework Services SHALL NOT bypass this contract to access entity internals directly.

ACT-002 — Deactivation Contract

Purpose: Defines the deactivation sequence and notification mechanism used during the Termination phase.

Consumers: Core (via CC-002), Framework Services requiring pre-termination cleanup.

Guarantee: Deactivation SHALL proceed in reverse activation order.

Constraint: Deactivation failures SHALL be reported through CC-003 but SHALL NOT prevent subsequent deactivations.

8.2 Consumed Contracts

Activator consumes the following contracts from upstream components.

Contract

Source

Purpose

CC-001 Runtime Context Contract

Core

Access to the shared Runtime Context.

CC-002 Lifecycle Contract

Core

Determines activation and deactivation window boundaries.

CC-003 Error Contract

Core

Propagates fatal activation errors.

CFG-001 Configuration Contract

Configuration

Validated configuration governing activation rules and constraints.

REG-001 Registry Contract

Registry

Read-only entity metadata lookup during activation.

RES-001 Resolution Contract

Resolver

Resolved entity graph used to determine activation order.

8.3 Contract Stability

All public contracts defined in §8.1 are architectural contracts.

They SHALL NOT be modified without a corresponding revision of this specification and ARCHITECTURE.md.

Consumers SHALL depend only on these contracts, not on Activator internals.

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

Determines activation and deactivation window boundaries.

Core

CC-003

Propagates fatal activation errors.

Configuration

CFG-001

Validated configuration governing activation rules.

Registry

REG-001

Read-only entity metadata lookup during activation.

Resolver

RES-001

Resolved entity graph for activation order determination.

Activator has no downstream Runtime Infrastructure dependents.

9.2 Normative Document Dependencies

Document

Dependency Reason

ARCHITECTURE.md

Defines the Runtime Infrastructure model and dependency rules.

RUNTIME_ARCHITECTURE.md

Defines the Runtime Lifecycle, activation phase, and termination phase.

9.3 Downstream Dependents

Layer

Contract Consumed

Dependency Nature

Framework Services

ACT-001

Consume the activated framework state to perform runtime responsibilities.

Activator is the terminal component of the Runtime Infrastructure.

Framework Services are the first consumers of the activated framework state.

10. Constraints

10.1 Architectural Constraints

The following constraints govern Activator.

ACT-C-001 — No Registration

Activator SHALL NOT register new entities into Registry.

ACT-C-002 — No Resolution

Activator SHALL NOT perform reference resolution between entities.

This responsibility belongs exclusively to Resolver.

ACT-C-003 — Activation After Resolution

Activator SHALL NOT begin entity activation before the resolution pass of Resolver completes successfully.

ACT-C-004 — Dependency-Ordered Activation

Activator SHALL activate entities in an order that respects the dependency relationships expressed in the resolved entity graph.

An entity SHALL NOT be activated before all entities it depends on are active.

ACT-C-005 — Fatal Error on Activation Failure

If an entity fails to complete any activation lifecycle phase, Activator SHALL propagate a fatal error through CC-003.

The framework SHALL NOT proceed to the Processing phase if any activation fails.

ACT-C-006 — Consistent Activated State

The activated framework state SHALL contain only entities that have successfully completed all three activation lifecycle phases.

Partially activated entities SHALL NOT be exposed through ACT-001.

ACT-C-007 — Reverse-Order Deactivation

During the Termination phase, Activator SHALL deactivate entities in reverse activation order.

ACT-C-008 — No Educational Logic

Activator SHALL NOT contain educational knowledge, domain-specific logic, or user content.

ACT-C-009 — Technology Independence

Activator SHALL remain independent from any specific implementation technology.

This specification defines behavior and contracts, not implementation.

11. Extension Points

11.1 Activation Lifecycle Hooks

Future versions MAY introduce lifecycle hooks that allow entities to perform custom logic at each activation phase.

Hooks SHALL be invoked by Activator at the defined lifecycle boundaries.

Hooks SHALL NOT alter the activation order or the activation lifecycle structure.

11.2 Activation Strategy Extension

Future versions MAY introduce alternative activation strategies for specific entity type combinations, such as lazy activation or parallel activation where dependency order permits.

Activation strategy extensions SHALL remain transparent to consumers of ACT-001.

Consumers SHALL observe only the activated framework state, not the strategy used to produce it.

12. Examples

12.1 Activation Sequence

The following illustrates the conceptual activation sequence.

Resolver: resolution pass completes
    │
    ▼
Activator: consumes RES-001 resolved entity graph
    │
    ▼
Activator: computes activation order from dependency graph
    │
    ▼
Activator: activates Entity A (no dependencies)
    │  Phase 1 — pre-activation: dependencies verified (none)
    │  Phase 2 — activation: entity transitions to active state
    │  Phase 3 — post-activation: entity recorded as active
    │
    ▼
Activator: activates Entity B (depends on A — A is now active)
    │  Phase 1 — pre-activation: A confirmed active
    │  Phase 2 — activation
    │  Phase 3 — post-activation
    │
    ├── Activation failure at any phase
    │       │
    │       ▼
    │   CC-003 Error Contract: fatal error propagated
    │   Framework execution halted
    │
    └── All entities activated successfully
            │
            ▼
        ACT-001 Activation Contract: activated framework state available
            │
            ▼
        Framework Services: consume ACT-001

12.2 Deactivation Sequence

The following illustrates the conceptual deactivation sequence during the Termination phase.

Core: Termination Phase begins
    │
    ▼
Activator: receives CC-002 Lifecycle Contract termination signal
    │
    ▼
Activator: deactivates Entity B (activated last — deactivated first)
    │
    ▼
Activator: deactivates Entity A (activated first — deactivated last)
    │
    ▼
ACT-002 Deactivation Contract: termination complete

13. Future Evolution

13.1 Anticipated Extensions

Future versions of Activator MAY introduce:

lifecycle hooks within ACT-001 for entities to perform custom pre- and post-activation logic;

lazy activation support for entities not required at framework startup;

parallel activation for entities with no shared dependencies, where safe to do so.

13.2 Stability Commitment

The public contracts defined in §8 are considered stable.

Breaking changes to these contracts SHALL require a major version increment of this specification.

Additive changes SHALL be introduced as minor version increments.

13.3 Out-of-Scope Evolution

The following SHALL NOT be introduced into Activator in future versions:

entity registration or reference resolution logic;

educational content or domain-specific logic;

activation that violates dependency order;

dependencies on Framework Services.

14. Summary — Quick Reference

Attribute

Value

Component

Activator

Document ID

COMP-ACT-001

Architectural Layer

Runtime Infrastructure

Architectural Capability

Activates runtime entities according to the Runtime Lifecycle

Primary Artifact

Activated framework state

Public Contracts

ACT-001 Activation Contract, ACT-002 Deactivation Contract

Consumed Contracts

CC-001, CC-002, CC-003 (Core); CFG-001 (Configuration); REG-001 (Registry); RES-001 (Resolver)

Upstream Dependencies

Core, Configuration, Registry, Resolver

Downstream Dependents

Framework Services (via ACT-001)

Key Constraints

Dependency-ordered activation, activation after resolution, consistent activated state

Extension Points

Activation Lifecycle Hooks, Activation Strategy Extension

15. Change History

Version

Date

Description

1.0.0

2026-08-11

Initial release

End of document.
