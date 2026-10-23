# EduTeX V2 Runtime Evolution Charter

**Status:** Draft proposal

**Version:** 0.1.0
**Scope:** Define the goal, boundaries, and acceptance direction for EduTeX 2.0 runtime work. This charter is not yet a normative runtime contract.

## 1. Goal

EduTeX 2.0 will make runtime execution **selective, explicit, deterministic, and scalable**. For a requested operation, EduTeX should resolve the relevant dependency graph and activate only the components required for that operation, while providing actionable diagnostics and a controlled migration path for projects created with EduTeX 1.x.

The purpose of V2 is not parallelism for its own sake. It is to make runtime behavior and dependency relationships sufficiently explicit that larger projects can be executed predictably and efficiently.

## 2. Guiding principles

1. **Specification before implementation.** Define runtime and migration contracts before changing runtime behavior.
2. **Determinism before concurrency.** Equivalent inputs must lead to equivalent graph and activation outcomes. Parallel execution is considered only after that property can be tested.
3. **Explicit dependency semantics.** Required and optional references, identity, namespaces, and failure behavior must be documented rather than inferred.
4. **One authoritative registry.** Registry remains the authoritative source of runtime entities; resolution and activation retain distinct responsibilities unless an approved architecture revision says otherwise.
5. **Migration, not silent breakage.** Incompatible 1.x behavior must be identified and accompanied by actionable migration guidance.
6. **Measure before optimizing.** Establish representative runtime and build baselines before setting numeric performance targets.

## 3. Intended scope

The V2 runtime work is expected to specify and evaluate:

- dependency graph identity and resolution, including cycle and unresolved-reference diagnostics;
- required versus optional references and their runtime semantics;
- hierarchical or scoped entity namespaces, including uniqueness and lookup rules;
- operation-scoped activation and lazy activation of the required dependency closure;
- lifecycle transitions, activation failures, and termination behavior for the selected runtime scope;
- observability of the resolved graph and activation decisions;
- safe parallel activation only where dependency ordering, shared state, and deterministic outcomes are demonstrably controlled;
- compatibility and migration behavior for 1.x projects.

This list defines areas for specification and review; it does not pre-approve a particular API, algorithm, namespace syntax, or concurrency model.

## 4. Out of scope

Unless separately justified by a V2 runtime requirement, this work does not include:

- a wholesale rewrite of EduTeX;
- unrelated lesson-authoring, course-content, theme, or output-format features;
- parallelizing builds without explicit safety and determinism contracts;
- arbitrary changes to educational content models;
- numeric speedup promises before a reproducible baseline exists.

## 5. V2 acceptance direction

The runtime contract and its implementation should make it possible to verify that:

1. Equivalent inputs produce an equivalent resolved graph and equivalent runtime outcomes, independent of registration order.
2. Missing required references and dependency cycles produce stable, actionable diagnostics.
3. An absent optional reference follows documented behavior and does not accidentally behave like a missing required reference.
4. A requested operation activates only its declared dependency closure; unrelated components are not activated as a side effect.
5. Any parallel activation mode is opt-in or otherwise explicitly governed, and its observable result matches the deterministic serial contract.
6. A documented compatibility matrix and migration path cover supported 1.x project patterns and explain unsupported or changed behavior.

The exact test strategy and any quantitative performance goals are to be set during contract design, after a baseline and representative project fixtures are agreed.

## 6. Recommended sequence

### Phase 0 — Runtime and compatibility audit

Compare the released runtime architecture and component specifications with the 1.7.0 implementation. Identify current lifecycle behavior, implicit assumptions, compatibility-sensitive inputs, and measurable baselines.

### Phase 1 — Resolution and identity contract

Specify graph identity, namespace rules, required and optional references, cycle behavior, and deterministic diagnostics. Keep Registry, Resolver, and Activator responsibilities explicit.

### Phase 2 — Operation-scoped and lazy activation

Specify how a command or runtime operation declares its required scope, how the dependency closure is obtained, and how activation and termination behave for that scope.

### Phase 3 — Lifecycle evolution

Specify lifecycle extension points and failure/termination behavior, including how partial activation is reported and cleaned up. Preserve existing guarantees unless a deliberate, documented migration changes them.

### Phase 4 — Concurrency evaluation

Evaluate parallel activation only after graph, lifecycle, shared-state, determinism, and failure contracts are testable. Retain a serial execution path as the reference behavior unless the final contract establishes another equivalent baseline.

## 7. Decisions required before implementation

The following items remain open and must be resolved in the relevant specifications:

- what constitutes an activation unit and how each CLI operation declares its runtime scope;
- the syntax, ownership, and lookup rules for hierarchical namespaces;
- whether optional references are absent, deferred, or represented explicitly in the resolved graph;
- which lifecycle hooks exist and which component owns each hook;
- how activation failures affect already-activated dependencies and termination;
- which entities, if any, may be activated concurrently and how that eligibility is declared;
- which 1.x behaviors are preserved, deprecated, or replaced, and for how long.

## 8. Relationship to existing specifications

This charter proposes evolution of the runtime model described in `RUNTIME_ARCHITECTURE.md` and its component contracts, especially `REGISTRY_SPEC.md`, `RESOLVER_SPEC.md`, and `ACTIVATOR_SPEC.md`. It does not replace those specifications. Changes to normative behavior must be made in the authoritative specification that owns the relevant concept, with cross-references updated as needed.

## 9. First deliverable

The first V2 deliverable is a reviewed runtime and migration contract, not a runtime implementation. It should define the terms, invariants, compatibility policy, and testable acceptance criteria needed to implement the phases above without prematurely fixing implementation details.
