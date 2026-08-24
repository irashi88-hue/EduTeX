document_id:      ASSET-KNOW-001
title:            EduTeX Knowledge Model Specification
type:             User Asset Specification
version:          1.0.0
status:           Released
owner:            EduTeX Content Architecture
level:            3
parent:           ARCHITECTURE.md
normative_refs:
  - ARCHITECTURE.md
  - RUNTIME_ARCHITECTURE.md
  - KNOWLEDGE_SPEC.md
  - SHORTCODE_SPEC.md
  - SPECIFICATION_STANDARD.md
  - SPECIFICATION_TEMPLATE.md
informative_refs:
  - STYLE_GUIDE.md

EduTeX Knowledge Model Specification

1. Purpose

This document specifies the structure, content rules, and constraints that define a valid Knowledge Model within the EduTeX framework.

A Knowledge Model is a User Asset.

It is an educational artifact authored by content creators and consumed by the Knowledge Service during Knowledge Processing.

This document defines what a Knowledge Model is, what it must contain, and what constraints govern its structure.

It does not define how the Knowledge Service processes a Knowledge Model, nor how the shortcode parser is implemented.

2. Intended Audience

This document is intended for:

content authors creating EduTeX Knowledge Models;

component specification authors defining Knowledge Service behaviour;

framework contributors reviewing the content contract boundary.

3. Scope

3.1 In Scope

the definition of a Knowledge Model as a User Asset;

the required structure of a Knowledge Model source file;

the YAML frontmatter fields required by every Knowledge Model;

the shortcode content model as the body of a Knowledge Model;

the supported shortcode types and their roles within a Knowledge Model;

the nesting rules applicable to Knowledge Model content;

the constraints governing Knowledge Model authoring;

the relationship between a Knowledge Model and the Knowledge Service.

3.2 Out of Scope

Knowledge Service processing logic (defined in KNOWLEDGE_SPEC.md);

shortcode parser implementation (defined in KNOWLEDGE_SPEC.md);

shortcode syntax and grammar (defined in SHORTCODE_SPEC.md);

Theme and Layout processing (defined in THEME_SPEC.md and LAYOUT_SPEC.md);

framework implementation logic of any kind.

4. Normative References

Document

Role

ARCHITECTURE.md

Normative

RUNTIME_ARCHITECTURE.md

Normative

KNOWLEDGE_SPEC.md

Normative

SHORTCODE_SPEC.md

Normative

SPECIFICATION_STANDARD.md

Normative

SPECIFICATION_TEMPLATE.md

Normative

5. Overview

A Knowledge Model is the primary educational artifact in the EduTeX framework.

It is a structured Markdown source file that encodes educational content using the EduTeX shortcode system defined in SHORTCODE_SPEC.md.

The Knowledge Service, as defined in KNOWLEDGE_SPEC.md, interprets the Knowledge Model during Knowledge Processing to produce the educational content model.

A Knowledge Model SHALL NOT contain framework implementation logic.

A Knowledge Model SHALL remain independent from Runtime Infrastructure.

The Knowledge Model is the sole carrier of educational knowledge within the EduTeX framework.

6. Responsibilities

A Knowledge Model is responsible for:

declaring its identity and metadata through a YAML frontmatter block;

expressing educational content through the shortcode types defined in SHORTCODE_SPEC.md;

structuring content in a form that the Knowledge Service can interpret through KNOW-001 and KNOW-002;

respecting the nesting rules defined in SHORTCODE_SPEC.md.

A Knowledge Model SHALL NOT:

contain framework configuration or implementation logic;

reference Runtime Infrastructure components directly;

define presentation or layout rules;

duplicate or redefine shortcode syntax.

7. Knowledge Model Structure

7.1 Source File Format

A Knowledge Model is a Markdown source file.

Every Knowledge Model SHALL contain:

a YAML frontmatter block at the top of the file;

a body section containing shortcode-structured educational content.

7.2 YAML Frontmatter

Every Knowledge Model SHALL declare a YAML frontmatter block delimited by --- markers.

The frontmatter SHALL include the following required fields.

Field

Type

Description

id

string

Unique identifier for this Knowledge Model within the framework.

title

string

Human-readable title of the Knowledge Model.

language

string

The target language of the educational content (e.g. it, fr).

level

string

The proficiency level addressed by this Knowledge Model.

version

string

The version of this Knowledge Model, following semantic versioning.

The following fields are optional.

Field

Type

Description

description

string

A short description of the Knowledge Model's educational scope.

tags

array

A list of descriptive tags for categorisation purposes.

author

string

The name of the content author.

The id field SHALL be unique across all Knowledge Models registered with the framework.

The version field SHALL follow semantic versioning conventions.

7.3 Body

The body of a Knowledge Model consists of Markdown prose and shortcode blocks as defined in SHORTCODE_SPEC.md.

Prose content MAY appear between shortcode blocks.

Shortcode blocks SHALL conform to the syntax and grammar defined in SHORTCODE_SPEC.md.

8. Content Model

8.1 Shortcode Types

A Knowledge Model body MAY include any combination of the shortcode types defined in SHORTCODE_SPEC.md.

The supported types and their educational roles within a Knowledge Model are described below.

Shortcode Type

Educational Role

rule

Encodes a grammatical or conceptual rule the learner must acquire.

note

Provides a clarifying remark, exception, or warning.

example

Illustrates a rule or concept with a concrete instance.

exercise

Presents a learner task requiring active engagement.

solution

Provides the expected answer to an enclosing exercise.

vocab

Defines a vocabulary entry with translation and morphological metadata.

conjugation

Presents the conjugation paradigm for a given verb.

formula

Encodes a mathematical or chemical formula.

8.2 Subtypes

The example shortcode supports the subtypes simple, comparative, and contextual as defined in SHORTCODE_SPEC.md.

The formula shortcode supports the subtypes math and chem as defined in SHORTCODE_SPEC.md.

8.3 Nesting

The only supported nesting within a Knowledge Model is a solution block nested inside an exercise block.

All other nesting combinations are prohibited.

Nesting rules are fully defined in SHORTCODE_SPEC.md.

9. Dependencies

9.1 Upstream Dependencies

A Knowledge Model has no upstream component dependencies.

A Knowledge Model is a User Asset.

It SHALL remain independent from Runtime Infrastructure, Framework Services, and Architectural Mechanisms.

9.2 Relationship to the Knowledge Service

The Knowledge Service, defined in KNOWLEDGE_SPEC.md, is the sole consumer of a Knowledge Model at runtime.

The Knowledge Service interprets the Knowledge Model through the shortcode contract defined in SHORTCODE_SPEC.md.

The Knowledge Model does not depend on the Knowledge Service.

The dependency is unidirectional: the Knowledge Service depends on the Knowledge Model, not the reverse.

10. Constraints

KM-C-001: Every Knowledge Model SHALL include a YAML frontmatter block.

KM-C-002: The id field in the frontmatter SHALL be present and unique across all registered Knowledge Models.

KM-C-003: The title field in the frontmatter SHALL be present and non-empty.

KM-C-004: The language field in the frontmatter SHALL be present.

KM-C-005: The level field in the frontmatter SHALL be present.

KM-C-006: The version field in the frontmatter SHALL be present and follow semantic versioning.

KM-C-007: All shortcode blocks in the body SHALL conform to the syntax defined in SHORTCODE_SPEC.md.

KM-C-008: A Knowledge Model SHALL NOT contain framework configuration, implementation logic, or references to Runtime Infrastructure components.

KM-C-009: Nesting SHALL be restricted to solution inside exercise as defined in SHORTCODE_SPEC.md.

KM-C-010: A Knowledge Model SHALL NOT define presentation or layout rules.

11. Validation

The Knowledge Service SHALL validate every Knowledge Model before producing the educational content model.

Validation SHALL include:

verifying the presence and completeness of the YAML frontmatter fields defined in §7.2;

verifying that all shortcode blocks conform to the syntax and type definitions in SHORTCODE_SPEC.md;

verifying that nesting rules defined in §8.3 are satisfied.

If validation fails, the Knowledge Service SHALL propagate a fatal error through the Error Contract (CC-003) as defined in KNOWLEDGE_SPEC.md.

A Knowledge Model author SHALL NOT be required to understand the validation implementation.

Validation is the responsibility of the Knowledge Service, not of the Knowledge Model itself.

12. Authoring Guidelines

This section is informative.

A Knowledge Model is authored as a plain Markdown file.

Content authors do not need to understand the EduTeX runtime to author a valid Knowledge Model.

Authors SHALL:

provide all required frontmatter fields;

use only shortcode types defined in SHORTCODE_SPEC.md;

restrict nesting to solution inside exercise.

Authors SHOULD:

provide a meaningful description field to aid discoverability;

use tags to support Knowledge Model categorisation;

increment the version field when making substantive content changes.

13. Architecture Compatibility

13.1 User Asset Boundary

A Knowledge Model is a User Asset as defined in ARCHITECTURE.md §10.5 and §11.4.

It SHALL remain independent from Runtime Infrastructure.

It SHALL NOT contain framework implementation logic.

13.2 Knowledge Processing Boundary

Knowledge Processing, as defined in RUNTIME_ARCHITECTURE.md §10.3, is responsible for interpreting the Knowledge Model.

The Knowledge Model defines what educational content exists.

Knowledge Processing defines how that content is interpreted.

These responsibilities SHALL NOT overlap.

13.3 Shortcode Contract Boundary

The shortcode syntax and grammar are defined in SHORTCODE_SPEC.md.

This document references those definitions but does not redefine them.

The Knowledge Model is the content artifact that uses the shortcode system.

The shortcode system is the syntax contract between the author and the Knowledge Service.

14. Summary

A Knowledge Model is a User Asset that carries educational content in the EduTeX framework.

It is a Markdown source file with a YAML frontmatter block and a body of shortcode-structured content.

It has no dependencies on Runtime Infrastructure, Framework Services, or Architectural Mechanisms.

Its structure is governed by this specification.

Its syntax is governed by SHORTCODE_SPEC.md.

Its interpretation at runtime is the responsibility of the Knowledge Service as defined in KNOWLEDGE_SPEC.md.

15. Change History

Version

Date

Description

1.0.0

2026-08-24

Initial release of Knowledge Model User Asset Specification.

— End of Document —
