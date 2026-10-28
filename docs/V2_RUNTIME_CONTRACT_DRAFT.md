# EduTeX V2 Runtime Contract Proposal

**Status:** Draft proposal
**Version:** 0.2.0
**Purpose:** Translate the agreed V2 runtime scope and the EduTeX 1.8.0 implementation audit into proposed, testable runtime contracts. This document is not yet normative and does not authorize implementation changes.

## 1. Objective

EduTeX 2.0 will define explicit operation scopes, deterministic typed graph behavior, actionable runtime diagnostics, and complete activation and termination behavior. Build and Validate retain their configured full-project behavior. Preview and per-lesson Course build use their existing selected Knowledge Model sources while retaining configured support assets.

For operations with roots, runtime scope includes those roots and their required dependency closure. Activation is serial and dependency ordered. Runtime inspection reports the configuration-selected graph without activating entities.

V2 does not promise a performance improvement. Scope and activation behavior are correctness contracts; any performance target requires a representative, reproducible baseline.

## 2. Audited 1.8.0 baseline

The following observations come from the current source and focused tests:

- `RuntimeContext` enforces explicit transitions among configuration, registration, resolution, activation, processing, build, completion, and failure. The current lifecycle does not define a `TERMINATING` phase.
- `_register_project_assets` registers the Knowledge Model selected in configuration, the explicit Theme if configured, the selected Layout, and enabled Extensions; it does not register every asset file on disk. When no Theme is explicitly configured, the bundled default is handled later by the processing pipeline.
- `_prepare_project_pipeline` resolves and activates the configured registered set, then processes Knowledge, Theme, and Layout services. Build and Validate call this shared pipeline.
- Preview overrides the configured Knowledge Model with its selected source file before calling `build_project`; the remaining configured support assets are retained.
- Course build supplies a per-lesson builder that overrides the Knowledge Model with each lesson source and invokes `build_project` for that lesson.
- Runtime inspection registers the configuration-selected asset set and resolves that graph for reporting; it does not call the Activator.
- `Registry` uses `(EntityType, entity_id)` as its key and closes registration before resolution. The current identity model has no hierarchical namespace field.
- `Resolver.resolve()` reads all registered entities, skips an absent optional reference, fails on an absent required reference, detects cycles, and freezes the resolved graph.
- `Activator.activate()` topologically orders and activates every entity in the supplied graph. `deactivate()` visits activated entities in reverse order. The current entity activation path creates an `ActivatedEntity` wrapper; no per-entity activation hook or partial-failure rollback is evident in that path.
- The focused Registry, Resolver, Activator, Core, and generation integration tests passed together (43 tests).

These observations describe the audited baseline, not a guarantee that all runtime behavior is covered by those tests.

## 3. Proposed runtime contracts

### 3.1 Operation scope

1. Build and Validate SHALL retain the complete runtime entity set selected by project configuration, including the existing handling of the bundled default Theme. They SHALL NOT silently omit configured entities.
2. Preview SHALL use its explicitly selected source file as the Knowledge Model root and SHALL retain the configured support assets.
3. Each Course build SHALL use the lesson source declared by the course manifest as that build's Knowledge Model root and SHALL retain the configured support assets.
4. Runtime inspection SHALL report the complete configuration-selected registered and resolved graph and SHALL NOT activate entities merely to inspect them.
5. For an operation with roots, its runtime scope SHALL include the roots, the configured support assets belonging to the operation, and the transitive closure of required references from those roots and support assets.
6. An optional reference SHALL NOT expand the operation scope by itself. If its target is already in scope, the reference SHALL be resolved normally; otherwise the reference SHALL be omitted from the scoped graph without causing a resolution error.
7. Entities outside the operation scope SHALL NOT be activated incidentally.
8. The initial V2 contract SHALL NOT add a generic CLI root-selection flag. Any future public root-selection mechanism requires a concrete use case and separate review.

### 3.2 Resolution and graph behavior

1. Resolution SHALL begin only after the Registry registration window closes. The Resolver SHALL treat registered entities as read-only.
2. Entity identity SHALL be the typed pair `(entity_type, entity_id)`. The same ID under different entity types represents distinct entities. Hierarchical namespaces are outside this contract.
3. The resolved graph SHALL contain each in-scope entity exactly once, including entities with no resolved references.
4. Each present reference whose target is in the operation scope SHALL create an edge preserving its source, target, and reference type. A present optional reference to an in-scope target SHALL resolve normally.
5. A missing required target SHALL fail resolution before activation using `RUNTIME_REFERENCE_MISSING`. Its structured details SHALL identify `source` and `expected_target`, each with `type` and `id`, and SHALL include `reference_type`.
6. A missing optional target SHALL NOT fail resolution and SHALL be omitted without creating a graph node or edge.
7. A dependency cycle SHALL fail resolution before activation using `RUNTIME_DEPENDENCY_CYCLE`. Its `details.cycle` SHALL be an ordered list of typed identities, follow edge direction, begin at the canonically smallest identity in the cycle, and repeat that identity at the end.
8. If multiple cycles exist, Resolver SHALL report the first cycle found by deterministic depth-first traversal, visiting entities and outgoing edges in canonical order.
9. Entities SHALL be ordered by `(entity_type.name, entity_id)`. Edges SHALL be ordered by `(source_type.name, source_id, target_type.name, target_id, reference_type)`. Equivalent registry contents and operation scopes SHALL produce the same graph and order independent of registration order.
10. The resolved graph and its entity and edge collections SHALL be immutable to consumers. Deep immutability of arbitrary entity metadata is outside this contract.

### 3.3 Runtime diagnostics

1. Fatal runtime JSON errors SHALL preserve the existing `type` and `message` fields and command-specific JSON nesting.
2. Fatal runtime JSON errors SHALL expose a stable `code` and structured `details` as defined by the specification owning the error category.
3. Human-readable `message` text MAY evolve without changing the stable code or its code-specific details.
4. Resolver diagnostics SHALL use the codes and details in Section 3.2.
5. Activation and cleanup diagnostics SHALL use stable codes `RUNTIME_ACTIVATION_FAILED` and `RUNTIME_CLEANUP_FAILED`, with the structured details defined by ACT-003 in `ACTIVATOR_SPEC.md` and propagated through CC-003.

### 3.4 Activation and activated state

1. Activator SHALL consume the resolved graph for the operation scope and SHALL activate entities serially in deterministic dependency order.
2. An entity SHALL NOT be activated before all its in-scope dependencies are active.
3. The activation lifecycle SHALL retain the defined pre-activation, activation, and post-activation stages.
4. The activated framework state SHALL NOT be exposed until every in-scope entity has completed all activation stages successfully.
5. If activation fails, the framework SHALL NOT proceed to Processing or Build for that operation.
6. Activation behavior SHALL NOT depend on registry registration order.

### 3.5 Rollback and cleanup

1. If an entity fails before its activation operation has begun, rollback SHALL clean up previously activated entities in reverse activation order.
2. If an entity fails after its activation operation has begun, rollback SHALL first attempt cleanup for that failing entity, then clean up previously activated entities in reverse activation order.
3. Cleanup SHALL continue for all remaining eligible entities even if an individual cleanup operation fails.
4. Cleanup errors SHALL be represented as structured diagnostics and aggregated. On activation failure, the original activation error SHALL remain primary; cleanup failures SHALL be included as structured secondary details.
5. During rollback, the lifecycle SHALL enter `TERMINATING` before cleanup and SHALL enter `FAILED` after cleanup attempts finish, whether or not cleanup itself succeeds.
6. During normal termination, entities that completed activation SHALL be deactivated in reverse activation order. Cleanup SHALL continue after individual failures.
7. Normal execution SHALL enter `TERMINATING` before final deactivation and SHALL enter `COMPLETE` only if the required termination cleanup succeeds. If cleanup fails, the lifecycle SHALL enter `FAILED` after all cleanup attempts finish.
8. Partially activated state SHALL never be exposed through the Activation Contract.
9. Exact lifecycle hook interfaces and CC-003 integration details SHALL be defined in the owning component specifications before implementation. Activation and cleanup diagnostic codes SHALL be `RUNTIME_ACTIVATION_FAILED` and `RUNTIME_CLEANUP_FAILED`, as specified by ACT-003.

### 3.6 Concurrency

1. Activation SHALL be serial in the initial V2 runtime contract.
2. Parallel activation and parallel build execution are outside this scope and SHALL NOT be enabled by this contract.
3. Any future concurrency proposal requires a separate use case, specification, determinism and failure contract, and tests against the serial reference behavior.

## 4. Compatibility and migration direction

1. EduTeX 1.8.x SHALL be the supported compatibility baseline for V2.
2. Releases earlier than 1.8.x are outside the V2 compatibility promise.
3. V2 SHALL preserve the operation scopes described in Section 3.1 unless a documented migration explicitly changes a behavior.
4. V2 SHALL preserve typed entity identity and the required and optional reference outcomes described in Section 3.2.
5. V2 SHALL NOT silently omit configured entities or reinterpret existing entity identities.
6. Changed or unsupported project patterns SHALL receive actionable diagnostics and migration guidance.
7. Stable diagnostic codes and structured fields SHALL remain stable; human-readable message text MAY evolve.
8. A migration guide SHALL describe relevant changes for supported 1.8.x projects before release.

## 5. Acceptance criteria

The contract is covered when repository tests demonstrate that:

- Build and Validate retain their configured full-project scope;
- Preview and per-lesson Course build use their selected Knowledge Model source and retain configured support assets;
- inspection reports the full configuration-selected graph without activation;
- operation roots include their required dependency closure and unrelated entities are not activated;
- required and optional missing-reference outcomes and cycle diagnostics follow Section 3.2;
- typed identity and canonical graph results are independent of registration order;
- activation order is deterministic, serial, and dependency first;
- partial activation failure cleans up the failing entity when activation had begun, followed by previously activated entities in reverse order;
- cleanup continues after individual errors and preserves the primary activation failure with structured cleanup details;
- normal deactivation uses reverse activation order and continues after individual cleanup failures;
- lifecycle transitions through `TERMINATING` to `COMPLETE` or `FAILED` as specified;
- JSON errors preserve command-specific nesting and stable fields;
- the compatibility matrix and migration guide cover supported 1.8.x patterns.

Performance targets are outside these acceptance criteria until a reproducible baseline exists.

## 6. Recommended implementation sequence

1. Review and approve this contract and the operation-scope definitions.
2. Update the authoritative Core, Runtime Architecture, Resolver, and Activator specifications and cross-references.
3. Add contract tests for scope, graph ordering, diagnostics, lifecycle transitions, rollback, and cleanup aggregation.
4. Implement the approved runtime behavior in small, independently testable tranches.
5. Run the complete test suite and repository quality checks.
6. Publish the supported 1.8.x compatibility matrix and migration guide.

## 7. Explicitly out of scope

This contract does not define:

- hierarchical entity namespaces;
- parallel activation or parallel builds;
- generic public root-selection options;
- compatibility for releases earlier than 1.8.x;
- numeric performance targets;
- unrelated content, authoring, theme, layout, or output-format changes.

## 8. Change control

This document remains a proposal until reviewed and the relevant authoritative specifications are updated. It does not authorize runtime implementation changes by itself. No implementation changes are implied by this draft.
