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

1. Required and optional references SHALL have distinct, documented missing-target behavior.
2. Cyclic dependencies SHALL be rejected with a diagnostic that identifies the cycle.
3. A resolved graph exposed after resolution SHALL be immutable, unless a future contract explicitly revises this guarantee.
4. Equivalent registries SHALL yield equivalent resolved relationships and diagnostics regardless of entity registration order. The exact canonical ordering and diagnostic format remain to be specified.
5. V2 SHALL preserve existing reference behavior by default unless the migration contract explicitly changes it.

### 3.3 Activation and termination

1. Activation SHALL respect dependency order for the selected operation scope.
2. Activation SHALL be deterministic for equivalent resolved inputs.
3. Termination or deactivation SHALL occur in reverse activation order for entities that were successfully activated, unless a revised lifecycle contract defines a more precise failure or cleanup rule.
4. The contract SHALL distinguish entity discovery, graph resolution, activation, and service processing; these terms SHALL NOT be treated as interchangeable.
5. V2 SHALL define observable activation semantics before promising lazy-loading performance benefits.
6. Behavior after partial activation failure, including cleanup of already activated entities, remains open and must be specified before lifecycle implementation changes.

### 3.4 Concurrency

1. Serial deterministic behavior SHALL remain the reference contract during the initial V2 runtime work.
2. Parallel activation SHALL be considered only after dependency ordering, shared-state rules, failure propagation, termination, and equivalence to the serial contract are testable.
3. This proposal does not require parallel activation or authorize it by default.

## 4. Compatibility direction

- Existing 1.x projects SHALL retain full-project operation semantics by default. Any narrower target scope SHALL be an explicit opt-in and SHALL NOT be enabled silently.
- Changed or unsupported project patterns SHALL receive actionable diagnostics and migration guidance rather than being silently ignored.
- The exact supported 1.x compatibility matrix, deprecation policy, and migration duration remain open decisions.

## 5. Acceptance criteria for the normative contract and implementation

The eventual contract and implementation should have tests demonstrating that:

- current full-project Build and Validate behavior remains intact under the compatibility default;
- inspection can report the full graph without activating entities;
- a declared root scope includes its transitive required dependencies and excludes unrelated entities from activation;
- missing required references, missing optional references, and dependency cycles follow distinct and stable documented outcomes;
- registration-order changes do not change canonical graph results, activation order, or diagnostics;
- deactivation order is the reverse of successful activation order;
- partial activation failure has explicitly tested cleanup behavior;
- any later parallel mode is equivalent to the serial reference for observable results and diagnostics.

Performance targets SHALL be established only after a reproducible baseline is measured on representative project fixtures.

## 6. Recommended implementation sequence

1. Complete the 1.7.0 runtime audit and record representative full-project behavior and measurements.
2. Finalize operation-scope terminology and the compatibility policy.
3. Define graph identity, namespace, reference, determinism, and diagnostic contracts.
4. Define scoped resolution and activation semantics, including partial-failure cleanup.
5. Add contract tests before implementing behavior changes.
6. Evaluate lazy activation and performance against the baseline.
7. Evaluate parallel activation as a separate, later tranche.

## 7. Open decisions

The following decisions SHALL be resolved in the owning specifications before implementation:

- What identifies a runtime operation and its root entities?
- Which target-aware operations (including any opt-in Build or Validate mode) have a concrete use case and require root selection?
- How are hierarchical namespaces represented and kept compatible with existing `(EntityType, entity_id)` identities?
- Are unresolved optional references omitted from the graph, represented explicitly, or reported as diagnostics?
- How is canonical ordering defined for entities, edges, activation, and diagnostics?
- What cleanup guarantee applies if activation fails partway through?
- What work, beyond wrapper creation, is considered entity activation?
- Which representative projects and measurements justify a scalability or performance target?

## 8. Change control

This document is a proposal for review. It SHALL NOT be treated as an implementation specification until the open decisions are resolved and the relevant authoritative runtime and component specifications are updated. No implementation change is implied by this draft.
