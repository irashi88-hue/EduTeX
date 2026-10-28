# EduTeX V2 Runtime Completion Charter

**Status:** Draft proposal
**Version:** 0.2.0
**Scope:** Define the goal, boundaries, decisions, and acceptance direction for EduTeX 2.0 runtime work. This charter is not a normative runtime contract.

## 1. Goal

EduTeX 2.0 will make runtime execution explicit, deterministic, diagnosable, and appropriately scoped. Operations that already identify a target, such as Preview and per-lesson Course build, will use that target together with the configured support assets and their required dependency closure. Full-project Build and Validate will retain their configured full-project behavior.

The V2 runtime will define typed graph identity, canonical ordering, stable structured diagnostics, lifecycle termination, and cleanup behavior for both normal termination and partial activation failure. It will provide an actionable compatibility and migration path for projects using supported EduTeX 1.8.x releases.

V2 does not promise a particular speedup. Scoping is a correctness and isolation contract first; performance claims require representative measurements.

## 2. Decisions and guiding principles

1. **Specification before implementation.** Define runtime and migration contracts before changing runtime behavior.
2. **Determinism by default.** Equivalent registries and operation scopes produce equivalent graphs, activation order, and diagnostics, independent of registration order.
3. **Typed identity.** An entity is identified by its entity type and entity ID. Hierarchical namespaces are not part of this V2 scope.
4. **Operation scope without a generic CLI selector.** Existing operation inputs determine roots. V2 does not add a generic root-selection flag.
5. **Serial activation as the reference behavior.** Activation is deterministic and serial. Parallel activation is outside this scope.
6. **One authoritative registry.** Registry remains authoritative for registered runtime entities; Resolver and Activator retain distinct responsibilities.
7. **Cleanup is part of the lifecycle contract.** A fatal failure must not expose partial activated state or skip required cleanup attempts.
8. **Migration, not silent breakage.** Changed or unsupported project behavior receives actionable diagnostics and migration guidance.
9. **Measure before optimizing.** Do not make numeric performance promises without a reproducible baseline.

## 3. Operation scope

The runtime contract will preserve and formalize the following operation scopes:

- **Build and Validate:** use the complete runtime entity set selected by project configuration, preserving existing full-project behavior.
- **Preview:** use the explicitly selected source file as the Knowledge Model root and retain the configured support assets.
- **Course build:** use each lesson source declared by the course manifest as that build's Knowledge Model root and retain the configured support assets for each lesson build.
- **Runtime inspection:** report the complete configuration-selected registered and resolved graph without activating entities.

For operations with roots, the runtime will include the roots and their required dependency closure. Configured support assets that belong to the operation remain in scope. Entities outside the operation scope are not activated incidentally.

The initial V2 contract adds no generic CLI root-selection option. A future target-selection interface requires a concrete use case and a separate review.

## 4. In scope

V2 runtime work will specify and test:

- typed entity identity and canonical graph and edge ordering;
- required and optional reference outcomes;
- deterministic cycle detection and stable, structured diagnostics;
- operation scopes and dependency closure for the operations listed in Section 3;
- serial, dependency-ordered activation;
- the `TERMINATING` lifecycle phase and valid completion/failure transitions;
- activation failure rollback, normal deactivation, cleanup continuation, and structured cleanup-error aggregation;
- the guarantee that partial activation state is not exposed;
- compatibility behavior and migration guidance for supported 1.8.x projects.

## 5. Out of scope

This V2 runtime contract does not include:

- hierarchical entity namespaces or a namespace migration;
- parallel activation or parallel build execution;
- a generic CLI flag or public API for selecting arbitrary roots;
- a wholesale framework rewrite or unrelated authoring, course-content, theme, or output-format work;
- numeric performance targets without a reproducible representative baseline;
- a compatibility promise for releases earlier than 1.8.x.

## 6. Acceptance direction

The normative contract and implementation should make it possible to verify that:

1. Build and Validate preserve their configured full-project behavior.
2. Preview and each Course build use the selected Knowledge Model source and retain the configured support assets.
3. Runtime inspection can report the full configuration-selected graph without activating entities.
4. Scoped operations include their roots and required dependency closure and do not activate unrelated entities.
5. Typed identity, canonical graph order, activation order, and diagnostics do not depend on registration order.
6. Missing required references, missing optional references, and cycles have distinct, stable, actionable outcomes.
7. Activation is serial and dependency ordered, and no partial activated state is exposed.
8. A failure after activation has begun triggers cleanup of the failing entity and previously activated entities in reverse order.
9. Cleanup continues after individual cleanup errors; errors are structured and aggregated while the original activation failure remains primary.
10. Normal termination deactivates successfully activated entities in reverse activation order before completion.
11. Lifecycle tests cover `TERMINATING`, `COMPLETE`, and `FAILED` outcomes.
12. Compatibility and migration documentation identifies supported 1.8.x patterns and explains relevant changes.

## 7. Recommended sequence

### Phase 0 - Freeze scope and baseline

Confirm operation scopes, supported compatibility baseline, and the current 1.8.0 runtime behavior before implementation changes.

### Phase 1 - Finalize graph and diagnostic contracts

Specify typed identity, canonical graph and edge ordering, reference outcomes, cycle diagnostics, and JSON error details in the owning specifications.

### Phase 2 - Finalize operation-scoped activation

Specify how existing operation inputs establish roots, how configured support assets are retained, and how the required dependency closure is resolved and activated serially.

### Phase 3 - Finalize lifecycle and cleanup

Specify `TERMINATING`, normal deactivation, partial activation rollback, cleanup continuation, structured aggregation, and failure transitions. Add contract tests before implementation.

### Phase 4 - Compatibility and migration

Publish the supported 1.8.x compatibility matrix and migration guidance. Validate the contract against representative existing projects and the complete test suite.

## 8. Relationship to existing specifications

This charter proposes evolution of `RUNTIME_ARCHITECTURE.md` and the relevant component contracts, especially `CORE_SPEC.md`, `REGISTRY_SPEC.md`, `RESOLVER_SPEC.md`, and `ACTIVATOR_SPEC.md`. It does not replace them. Normative behavior must be added to the specification that owns the relevant concept, with cross-references updated consistently.

## 9. First deliverable

The first V2 deliverable is a reviewed runtime and migration contract, followed by corresponding updates to the authoritative runtime and component specifications. Runtime implementation changes begin only after those contracts and their acceptance tests are agreed.
