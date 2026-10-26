# EduTeX V2 Runtime Contract Proposal

**Status:** Draft proposal

**Version:** 0.1.0
**Purpose:** Translate the agreed V2 runtime goal and the 1.7.0 implementation audit into proposed, testable runtime contracts. This document is not yet normative and does not authorize implementation changes.

## 1. Objective

EduTeX 2.0 should make runtime execution explicit, deterministic, and scalable. Each operation should have a defined asset scope and dependency lifecycle. The 1.7.0 CLI already limits registration to assets selected by configuration; V2 should formalize this behavior and evolve graph and lifecycle capabilities. Lazy activation is conditional on a measured need, not a performance promise. Full-project operations must not silently omit configured entities.

Selective or lazy activation is a runtime capability to define and evaluate, not a performance promise. The current Activator primarily creates activated wrappers, so performance claims require a representative baseline and evidence that activation is a material cost.

## 2. Audited 1.7.0 baseline

The following observations come from the current source and focused tests:

- `RuntimeContext` enforces explicit phase transitions, including configuration, registration, resolution, activation, processing, build, completion, and failure.
- `_register_project_assets` registers only the Knowledge Model selected in configuration, the explicit Theme if configured, the selected Layout, and enabled Extensions; it does not register every asset file on disk. When no Theme is explicitly configured, the bundled default is handled later by the processing pipeline.
- The shared `_prepare_project_pipeline` in `src/edutex/core/cli.py` resolves and activates this configured set, then processes Knowledge, Theme, and Layout services. Build and Validate call this shared pipeline.
- `preview` overrides the configured Knowledge Model with its selected source file before calling `build_project`; the remaining configured support assets are retained.
- `course build` supplies a per-lesson builder that overrides the Knowledge Model with each lesson source and invokes `build_project` for that lesson.
- Runtime inspection registers the configuration-selected asset set and resolves that graph for reporting; it does not call the Activator.
- `Registry` uses `(EntityType, entity_id)` as its key and closes registration before resolution. The current identity model has no hierarchical namespace field.
- `Resolver.resolve()` reads all registered entities, skips an absent optional reference, fails on an absent required reference, detects cycles, and freezes the resolved graph.
- `Activator.activate()` topologically orders and activates every entity in the supplied graph. `deactivate()` visits activated entities in reverse order. The current entity activation path creates an `ActivatedEntity` wrapper; no per-entity activation hook is evident in that path.
- The focused Registry, Resolver, Activator, Core, and generation integration tests passed together (43 tests).

These are baseline observations, not a guarantee that all runtime behaviors are covered by those tests.

## 3. Proposed runtime contracts

### 3.1 Operation scope

1. The runtime contract SHALL define the asset scope for each operation.
2. Full-project Build and Validate SHALL retain the full set selected by project configuration by default. Any narrower scope SHALL be an explicit opt-in and SHALL NOT silently omit configured entities.
3. Preview SHALL use its explicitly selected source file as the Knowledge Model input while retaining the other configured support assets.
4. Course build SHALL use the lesson sources declared by the manifest; each per-lesson build SHALL use that lesson's source as its Knowledge Model input.
5. Runtime inspection SHALL report the complete configuration-selected registered and resolved graph and SHALL NOT activate entities merely to inspect them.
6. The current configuration and CLI source selection define the existing operation scope. A new generic root-selection mechanism SHOULD be introduced only for a concrete operation and use case.
7. If a future target-specific operation declares root entities, its resolved and activated set SHALL include those roots and their required dependency closure; entities outside that scope SHALL NOT be activated incidentally.

### 3.2 Resolution and graph behavior

1. Resolution SHALL begin after the Registry registration window closes. The Resolver SHALL treat registered entities as read-only.
2. The resolved graph SHALL contain each entity in the operation scope exactly once, including entities with no resolved references.
3. Reference identity SHALL use the typed pair `(target_type, target_id)`. Entities with the same ID and different types are distinct. Hierarchical namespaces are outside this contract.
4. Each present, successfully resolved reference SHALL create an edge preserving its source, target, and reference type. A present optional reference SHALL resolve normally.
5. A missing required target SHALL fail resolution before activation using `RUNTIME_REFERENCE_MISSING`, with structured `source`, `expected_target`, and `reference_type` details.
6. A missing optional target SHALL NOT fail resolution and SHALL be omitted without creating a graph node or edge.
7. A dependency cycle SHALL fail resolution before activation using `RUNTIME_DEPENDENCY_CYCLE`, with the canonical ordered cycle identities defined by the Resolver specification.
8. The resolved graph structure and its entity and edge collections SHALL be immutable to consumers. Deep immutability of arbitrary entity metadata is outside this contract.
9. Equivalent registry contents and operation scopes SHALL produce the same graph, with canonical entity and edge ordering independent of registration order.
10. JSON diagnostics SHALL preserve command-specific nesting and the `type` and `message` fields, and use stable `code` and `details` fields as defined by the owning specification.

### 3.3 Activation and termination

This closeout does not revise activation or deactivation behavior. Partial-activation rollback, runtime resource hooks, cleanup aggregation, and TERMINATING/COMPLETE/FAILED state transitions are deferred. The existing Runtime Architecture remains authoritative. Any future lifecycle change requires a separate contract and implementation-backed tests.

### 3.4 Concurrency

Serial execution remains the default reference behavior. Parallel activation is outside the scope of this closeout; it is neither required nor enabled by this contract. Any future concurrency proposal requires a separate use case, contract, and tests.

## 4. Compatibility direction

1. EduTeX 1.7.x is the compatibility baseline for this contract.
2. For that baseline, V2 SHALL preserve the operation scopes in Section 3.1, typed entity identity, and the reference outcomes in Section 3.2.
3. V2 SHALL NOT silently omit configured entities, reinterpret existing entity identities, or apply an identity migration.
4. This contract does not promise support for releases earlier than 1.7.x or define extension API compatibility and deprecation periods. Those require a separate published policy.
5. Stable diagnostic codes and structured fields SHALL remain stable; human-readable message text MAY evolve.

## 5. Acceptance criteria

The contract is covered when repository tests demonstrate that:
- the operation scopes in Section 3.1 are preserved;
- missing required references, missing optional references, and dependency cycles follow Section 3.2;
- equivalent registry contents produce equivalent graphs and canonical ordering regardless of registration order;
- JSON diagnostics preserve command-specific nesting and the stable fields defined by the owning specification.

This closeout adds no acceptance criteria for activation lifecycle changes, rollback, resource hooks, or parallel execution.

## 6. Closeout checklist

1. Verify each normative statement against the current implementation and its tests.
2. Run the complete test suite and the repository quality checks.
3. Keep this closeout limited to documented, verifiable behavior; do not introduce runtime behavior changes in this work.
4. Treat the deferred items in Section 7 as separate future work, not as requirements of this closeout.

## 7. Deferred work

The following topics are explicitly deferred and are not blockers for this bounded contract:
- public APIs for selecting target roots;
- support and migration promises for releases earlier than the 1.7.x baseline;
- extension API compatibility and deprecation policy;
- activation/deactivation hooks, partial-activation rollback, cleanup aggregation, and new termination states;
- additional stable diagnostic codes beyond those defined by the owning specifications;
- performance targets and parallel activation.

## 8. Change control

This document is a proposal for review. It SHALL NOT be treated as an implementation specification until the open decisions are resolved and the relevant authoritative runtime and component specifications are updated. No implementation change is implied by this draft.
