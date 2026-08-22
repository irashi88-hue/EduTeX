document_id:      COMP-KNOW-001
title:            EduTeX Knowledge Component Specification
type:             Component Specification
version:          1.0.0
status:           Draft
owner:            EduTeX Framework Services
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
  - SHORTCODE_SPEC.md
  - STYLE_GUIDE.md

EduTeX Knowledge Component Specification

1. Purpose

This document defines the specification of the Knowledge component of the EduTeX Framework.

Knowledge is the first component of the Framework Services layer.

Its primary architectural capability is to prepare and manage the educational content model used during document generation.

This document defines the responsibilities, architecture, interfaces, dependencies, and constraints of Knowledge.

This document SHALL NOT define implementation details, algorithms, or programming interfaces.

2. Intended Audience

This document is intended for:

software architects designing EduTeX Framework Services components;

component specification authors whose services consume the educational content model;

contributors implementing or extending the Knowledge component;

reviewers validating Framework Services consistency.

3. Scope

3.1 In Scope

the architectural capability and primary responsibility of Knowledge;

the educational content model and its lifecycle;

the relationship between Knowledge and Knowledge Models as User Assets;

the public architectural contracts exposed by Knowledge;

the dependencies Knowledge holds on the Runtime Infrastructure;

the architectural constraints governing Knowledge;

extension points for content model evolution.

3.2 Out of Scope

implementation technology and programming language;

internal parsing algorithms and content transformation strategies;

document presentation, visual styling, and layout (defined in THEME_SPEC.md and LAYOUT_SPEC.md);

the shortcode format definition (defined in SHORTCODE_SPEC.md);

Knowledge Model authoring and content (User Assets — independent from framework implementation);

runtime processing pipelines beyond Knowledge Processing (defined in RUNTIME_ARCHITECTURE.md).

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

Knowledge is the first component of the Framework Services layer as defined by ARCHITECTURE.md.

It occupies the first position in the Processing Model defined by RUNTIME_ARCHITECTURE.md.

Knowledge consumes the activated framework state from the Runtime Infrastructure through ACT-001.

Knowledge exposes the processed educational content model to Theme and Layout through its public contracts.

5.2 Architectural Capability

The architectural capability of Knowledge is:

Prepares and manages the educational content model used during document generation.

This capability encompasses:

loading and interpreting the selected Knowledge Model from User Assets;

parsing and validating the source content according to the shortcode contract defined in SHORTCODE_SPEC.md;

producing the educational content model as the primary artifact of Knowledge Processing;

exposing the content model to subsequent processing stages through stable public contracts;

maintaining the boundary between educational content and document presentation.

5.3 Relationship to Other Components

Knowledge depends on the Runtime Infrastructure through the Activation Contract (ACT-001).

Knowledge is consumed by Theme, which applies visual and stylistic rules to the content model.

Knowledge is consumed by Layout, which organizes the content model into a document structure.

Knowledge does not depend on Theme or Layout.

Knowledge Models are User Assets. They are authored independently from the framework and consumed by Knowledge at runtime.

6. Responsibilities

6.1 Primary Responsibility

Knowledge SHALL prepare and manage the educational content model used during document generation.

6.2 Responsibility List

Knowledge is responsible for:

loading the selected Knowledge Model from the User Assets available in the activated framework state;

interpreting the Knowledge Model according to the structural contract defined in SHORTCODE_SPEC.md;

validating the source content against the shortcode contract and reporting validation errors through the Error Contract (CC-003);

producing the educational content model as a structured, typed representation of the source content;

exposing the educational content model through the Knowledge Content Contract (KNOW-001);

exposing the Knowledge Model metadata through the Knowledge Model Contract (KNOW-002);

maintaining the content model as immutable after the Knowledge Processing stage completes;

enforcing the boundary between educational content and document presentation.

6.3 Responsibility Boundaries

Knowledge SHALL NOT define document presentation, visual styling, or layout.

Knowledge SHALL NOT own or modify Knowledge Models. Knowledge Models are User Assets.

Knowledge SHALL NOT produce output formats. Output generation belongs to the Build System.

Knowledge SHALL NOT apply theme rules or layout rules to the content model.

Knowledge SHALL NOT contain implementation logic that is specific to a single educational domain.

7. Architecture

7.1 Educational Content Model

The educational content model is the primary architectural artifact produced by Knowledge.

It is a structured, typed representation of the source content defined by the selected Knowledge Model.

The content model is produced during the Knowledge Processing stage of the Processing Model.

The content model preserves the educational meaning of the source content independently from any presentation concern.

The content model SHALL be immutable after the Knowledge Processing stage completes.

7.2 Knowledge Model Relationship

A Knowledge Model is a User Asset that defines the structure, vocabulary, and rules of a specific educational content type.

Knowledge interprets the selected Knowledge Model to understand how to parse and represent the source content.

Knowledge does not own Knowledge Models. Knowledge Models are authored by users and remain independent from framework implementation.

Knowledge SHALL NOT embed domain-specific rules derived from a single Knowledge Model into its core implementation.

The mechanism by which Knowledge selects and loads the active Knowledge Model is governed by the configuration (CFG-001) and the activated framework state (ACT-001).

7.3 Content Parsing and Validation

Knowledge parses source content according to the shortcode contract defined in SHORTCODE_SPEC.md.

Parsing transforms the source content into the internal representation consumed by the educational content model.

Validation verifies that the parsed content conforms to the structural rules of the selected Knowledge Model.

If parsing or validation fails, Knowledge SHALL propagate a fatal error through the Error Contract (CC-003).

7.4 Processing Stage Position

Knowledge Processing is the first stage of the Processing Model as defined by RUNTIME_ARCHITECTURE.md.

Knowledge SHALL complete its processing stage before Theme Processing begins.

The educational content model produced by Knowledge is the primary input for Theme Processing and Layout Processing.

7.5 Content Model Immutability

Once the Knowledge Processing stage completes, the educational content model SHALL be treated as immutable.

Theme and Layout SHALL consume the content model without modifying it.

Immutability preserves the integrity of the educational content throughout the remaining processing stages.

7.6 Relationship to Runtime Infrastructure

Knowledge accesses the activated framework state through ACT-001 to obtain:

the selected Knowledge Model from User Assets;

validated configuration values relevant to content processing through CFG-001.

Knowledge uses the Error Contract (CC-003) to propagate fatal processing errors.

8. Interfaces

8.1 Public Architectural Contracts

Knowledge exposes the following public architectural contracts.

KNOW-001 — Knowledge Content Contract

Purpose: Provides read-only access to the educational content model produced during Knowledge Processing.

Consumers: Theme, Layout.

Guarantee: The content model exposed through this contract SHALL be fully parsed, validated, and typed. No unvalidated or partially processed content SHALL be exposed.

Constraint: This contract is strictly read-only. Consumers SHALL NOT modify the educational content model.

Constraint: This contract SHALL NOT be available before the Knowledge Processing stage completes successfully.

KNOW-002 — Knowledge Model Contract

Purpose: Provides read-only access to the metadata of the selected Knowledge Model, including its structural rules and vocabulary.

Consumers: Theme, Layout, diagnostic tooling.

Guarantee: The Knowledge Model metadata exposed through this contract SHALL correspond to the Knowledge Model active during the current processing session.

Constraint: This contract is strictly read-only.

8.2 Consumed Contracts

Knowledge consumes the following contracts from the Runtime Infrastructure.

Contract

Source

Purpose

ACT-001 Activation Contract

Activator

Access to the activated framework state, including User Assets.

CFG-001 Configuration Contract

Configuration

Validated configuration governing Knowledge Model selection and parsing.

CC-003 Error Contract

Core

Propagates fatal content processing errors.

8.3 Contract Stability

All public contracts defined in §8.1 are architectural contracts.

They SHALL NOT be modified without a corresponding revision of this specification and ARCHITECTURE.md.

Consumers SHALL depend only on these contracts, not on Knowledge internals.

9. Dependencies

9.1 Upstream Dependencies

Component

Contract Consumed

Reason

Activator

ACT-001

Access to the activated framework state and User Assets.

Configuration

CFG-001

Validated configuration governing Knowledge Model selection.

Core

CC-003

Propagates fatal content processing errors.

Knowledge SHALL NOT depend on Theme or Layout.

9.2 Normative Document Dependencies

Document

Dependency Reason

ARCHITECTURE.md

Defines the Framework Services layer and User Asset model.

RUNTIME_ARCHITECTURE.md

Defines the Processing Model and Knowledge Processing stage.

SHORTCODE_SPEC.md

Defines the shortcode contract used for content parsing and validation.

9.3 Downstream Dependents

Component

Contract Consumed

Dependency Nature

Theme

KNOW-001, KNOW-002

Consumes the content model and Knowledge Model metadata for styling.

Layout

KNOW-001, KNOW-002

Consumes the content model and Knowledge Model metadata for structure.

10. Constraints

10.1 Architectural Constraints

The following constraints govern Knowledge.

KNOW-C-001 — No Presentation Logic

Knowledge SHALL NOT define document presentation, visual styling, or layout.

These responsibilities belong exclusively to Theme and Layout respectively.

KNOW-C-002 — No Knowledge Model Ownership

Knowledge SHALL NOT own or modify Knowledge Models.

Knowledge Models are User Assets authored independently from the framework.

KNOW-C-003 — No Output Generation

Knowledge SHALL NOT produce output formats or final document representations.

Output generation belongs to the Build System.

KNOW-C-004 — Content Model Immutability

The educational content model SHALL be immutable after the Knowledge Processing stage completes.

Consumers SHALL NOT modify the content model through KNOW-001.

KNOW-C-005 — Fatal Error on Parsing or Validation Failure

If content parsing or validation fails, Knowledge SHALL propagate a fatal error through CC-003.

Document generation SHALL NOT proceed if the educational content model cannot be produced.

KNOW-C-006 — Domain Independence

Knowledge SHALL NOT embed structural rules specific to a single educational domain in its core implementation.

Domain-specific rules SHALL reside in Knowledge Models as User Assets.

KNOW-C-007 — Processing Stage Order

Knowledge SHALL complete the Knowledge Processing stage before Theme Processing begins.

KNOW-C-008 — Technology Independence

Knowledge SHALL remain independent from any specific implementation technology.

This specification defines behavior and contracts, not implementation.

11. Extension Points

11.1 Knowledge Model Type Extension

Future versions MAY introduce additional Knowledge Model types representing new educational content domains.

New Knowledge Model types SHALL conform to the structural contract defined in SHORTCODE_SPEC.md.

Existing Knowledge Model types SHALL NOT be removed or incompatibly modified without a major version increment of the relevant specifications.

11.2 Content Model Schema Extension

The educational content model schema MAY be extended in future versions to support additional content node types.

Extensions SHALL be additive and SHALL NOT remove or incompatibly alter existing content node types.

11.3 Parsing Pipeline Extension

Future versions MAY introduce additional parsing stages within the Knowledge Processing stage.

Parsing pipeline extensions SHALL remain internal to Knowledge and SHALL NOT affect the contract exposed through KNOW-001.

12. Examples

12.1 Knowledge Processing Sequence

The following illustrates the conceptual Knowledge Processing sequence.

Activator: activated framework state available (ACT-001)
    │
    ▼
Knowledge: loads selected Knowledge Model from User Assets via ACT-001
    │
    ▼
Knowledge: reads validated configuration via CFG-001
    │
    ▼
Knowledge: parses source content according to SHORTCODE_SPEC.md
    │
    ├── Parsing fails
    │       │
    │       ▼
    │   CC-003 Error Contract: fatal error propagated
    │   Document generation halted
    │
    └── Parsing succeeds
            │
            ▼
        Knowledge: validates content against Knowledge Model rules
            │
            ├── Validation fails
            │       │
            │       ▼
            │   CC-003 Error Contract: fatal error propagated
            │   Document generation halted
            │
            └── Validation succeeds
                    │
                    ▼
                Knowledge: educational content model produced
                    │
                    ▼
                KNOW-001 Knowledge Content Contract: available to Theme and Layout
                KNOW-002 Knowledge Model Contract: available to Theme and Layout

12.2 Content Model Boundary Example

The following illustrates the boundary between Knowledge, Theme, and Layout.

Source content: "::: rule\nDas Verb steht an zweiter Stelle.\n:::"
    │
    ▼
Knowledge: parses shortcode → content node {type: rule, body: "Das Verb..."}
    │
    ▼
KNOW-001: exposes content node to Theme and Layout

Theme: applies visual style to rule node     (presentation concern — not Knowledge)
Layout: positions rule node in document      (structure concern — not Knowledge)

-- WRONG --
Knowledge: applies font or colour to rule node   ✗
Knowledge: decides rule node position on page    ✗

13. Future Evolution

13.1 Anticipated Extensions

Future versions of Knowledge MAY introduce:

a formal content model schema exposable through KNOW-002 for validation tooling;

support for multiple simultaneous Knowledge Models within a single processing session;

a content query API within KNOW-001 for filtered access to content nodes by type.

13.2 Stability Commitment

The public contracts defined in §8 are considered stable.

Breaking changes to these contracts SHALL require a major version increment of this specification.

Additive changes SHALL be introduced as minor version increments.

13.3 Out-of-Scope Evolution

The following SHALL NOT be introduced into Knowledge in future versions:

presentation, styling, or layout logic;

ownership or modification of Knowledge Models;

output format generation;

reverse dependencies on Theme or Layout.

14. Summary — Quick Reference

Attribute

Value

Component

Knowledge

Document ID

COMP-KNOW-001

Architectural Layer

Framework Services

Architectural Capability

Prepares and manages the educational content model used during document generation

Primary Artifact

Educational content model

Public Contracts

KNOW-001 Knowledge Content Contract, KNOW-002 Knowledge Model Contract

Consumed Contracts

ACT-001 (Activator); CFG-001 (Configuration); CC-003 (Core)

Upstream Dependencies

Activator, Configuration, Core

Downstream Dependents

Theme, Layout

Key Constraints

No presentation logic, no Knowledge Model ownership, content model immutability

Extension Points

Knowledge Model Type Extension, Content Model Schema Extension, Parsing Pipeline Extension

15. Change History

Version

Date

Description

1.0.0

2026-08-21

Initial release

End of document.
