document_id:      DS-SHORT-001
title:            EduTeX Shortcode Specification
type:             Document Standard
version:          1.0.0
status:           Draft
owner:            EduTeX Project
level:            1
parent:           SPECIFICATION_STANDARD.md
normative_refs:
  - SPECIFICATION_STANDARD.md
  - STYLE_GUIDE.md
informative_refs:
  - FRAMEWORK_SPEC.md

EduTeX Shortcode Specification

1. Intended Audience

This document is intended for:

authors writing EduTeX educational content in Markdown;

developers implementing the EduTeX shortcode parser;

LaTeX template authors rendering shortcode output.

2. Purpose

This document defines the EduTeX shortcode system.

Shortcodes are structured inline commands embedded in Markdown source files.
They allow authors to produce semantically rich educational elements — such as examples, rules, exercises and vocabulary entries — without writing LaTeX directly.

The shortcode system is the primary interface between educational content and the EduTeX rendering pipeline.

3. Scope

3.1 In Scope

shortcode syntax and grammar;

all supported shortcode types and their fields;

subtype system;

nesting rules;

rendering intent for each shortcode type;

visual conventions (colours, layout).

3.2 Out of Scope

LaTeX implementation of individual shortcodes (defined in Component Specifications);

parser implementation details;

Knowledge Model structure (defined in KNOWLEDGE_SPEC.md);

document-level configuration.

4. Normative References

Document

Role

SPECIFICATION_STANDARD.md

Normative

STYLE_GUIDE.md

Normative

5. Shortcode Syntax

5.1 General Form

Every shortcode follows this grammar:

::: type[.subtype] [field1 | field2 | ...]
[body content]
:::

type — mandatory; identifies the shortcode kind.

.subtype — optional; selects a variant of the type.

field1 | field2 | ... — optional inline fields on the opening line, pipe-separated.

body — optional multiline content between the delimiters.

::: — the opening and closing delimiter; three colons.

5.2 Rules

The opening ::: and the type SHALL appear on the same line.

The closing ::: SHALL appear on its own line.

Fields on the opening line are positional and pipe-separated.

Body content MAY contain Markdown formatting.

Shortcodes MAY be nested (see §6).

Type and subtype names SHALL be lowercase.

Unknown types SHALL be flagged as errors by the parser.

5.3 Examples of Valid Syntax

::: note
This is a note.
:::

::: example.simple
Ich gehe nach Hause. — Vado a casa.
:::

::: vocab
der Hund | il cane | m | Hunde | Der Hund bellt laut.
:::

6. Nesting

Shortcodes MAY be nested when semantically justified.

The only currently supported nesting is :::solution inside :::exercise.

Nested shortcodes SHALL use the same ::: delimiter.

The parser SHALL resolve nesting by matching the innermost closing ::: first.

::: exercise
Coniuga il verbo _sein_ al presente.

::: solution
ich bin | du bist | er ist | wir sind | ihr seid | sie sind
:::
:::

Arbitrary nesting beyond the defined cases SHALL NOT be used.

7. Shortcode Types

7.1 Overview

Type

Subtypes

Fields on opening line

rule

—

—

note

—

—

example

simple, comparative, contextual

—

exercise

—

—

solution

—

— (nested inside exercise)

vocab

—

word | translation | gender | plural | example

verb

—

infinitive | translation | auxiliary | past-participle | 3sg

conjugation

—

infinitive | translation

formula

math, chem

—

7.2 rule — Grammatical Rule

Purpose

Highlight a grammatical rule that the reader must learn.

Syntax

::: rule
Body text describing the rule.
:::

Rendering Intent

Displayed as a visually distinct box.

Left border accent in a neutral dark colour (e.g. slate blue).

Label Regola (or localised equivalent) displayed above the body.

Example

::: rule
In einer deutschen Hauptsatz steht das Verb immer an zweiter Stelle.
Il verbo in una frase principale tedesca occupa sempre la seconda posizione.
:::

7.3 note — Note or Exception

Purpose

Add a clarifying remark, exception or warning that does not constitute a rule.

Syntax

::: note
Body text.
:::

Rendering Intent

Lighter visual weight than rule.

Left border accent in amber.

Label Nota displayed above the body.

SHALL NOT be used to introduce normative content.

7.4 example — Example

Purpose

Provide an illustrative example of a rule or concept.

Subtypes

example.simple (default when no subtype given)

A single sentence or phrase with its translation on the same or next line, separated by —.

::: example
Ich gehe heute in die Schule. — Oggi vado a scuola.
:::

example.comparative

Two parallel entries showing a correct and an incorrect form.
Lines prefixed with + are correct; lines prefixed with - are incorrect.

::: example.comparative
+ Ich gehe morgen ins Kino. ✓
- Ich morgen gehe ins Kino. ✗
:::

example.contextual

A short passage in the target language followed by its translation in italics on the next line.

::: example.contextual
Anna schreibt einen Brief. Sie schreibt ihn auf Deutsch.
_Anna scrive una lettera. La scrive in tedesco._
:::

Rendering Intent

Box with a subtle background tint.

Label Beispiel (or localised equivalent) displayed above the body.

Comparative subtype: correct lines in green, incorrect lines in red.

7.5 exercise — Exercise

Purpose

Present a task for the reader to complete.

Syntax

::: exercise
Task description.

::: solution
Solution text.
:::
:::

Fields

None on the opening line.
The body contains the task description in Markdown.
A ::: solution block MAY be nested inside.

Interactive translation variant

An exercise MAY declare an interactive translation task using the following fields:

::: exercise
title: Übersetze den Satz
type: translation
source: Mi chiamo Luca.
answer: Ich heiße Luca. | Ich heisse Luca.

::: solution
Ich heiße Luca.
:::
:::

The `type: translation` field enables an answer area with check and reset controls.

The `source:` field contains the text that the learner must translate.
The `prompt:` field MAY be used as an alias for `source:`.

The `answer:` field declares one accepted answer or multiple accepted answers.
Multiple accepted answers SHALL be separated by `|`.
The `expected:` field MAY be used as an alias for `answer:`.

Before comparison, EduTeX normalizes surrounding and repeated whitespace and ignores letter case.
The declared answer remains Unicode-sensitive.

If neither `answer:` nor `expected:` is declared, EduTeX SHALL use the first non-empty line of the nested `solution` block as the accepted answer.

The current translation interface labels are localized in Italian and English.
No additional interface locale is implied by this exercise syntax.

Solution Handling

The solution SHALL be hidden in the rendered PDF output.

Solutions SHALL be collected and printed in a dedicated appendix at the end of the document.

The exercise body SHALL include a reference marker pointing to the appendix entry.

Rendering Intent

Box with a distinct border.

Label Übung (or localised equivalent) displayed above the body.

Translation exercises SHALL render:

- the source text;
- an accessible answer area;
- a verification control;
- a reset control;
- a live status region for feedback.

Solution marker printed inline (e.g. → Soluzione p. 42).

7.6 solution — Solution

Purpose

Contain the solution to an exercise.

Syntax

solution SHALL only appear nested inside exercise.
It SHALL NOT appear as a top-level shortcode.

::: solution
Solution content.
:::

7.7 vocab — Vocabulary Entry

Purpose

Introduce a new vocabulary item with its grammatical information.

Syntax

::: vocab
word | translation | gender | plural | example sentence
:::

Fields (positional, pipe-separated)

Position

Field

Description

1

word

The German word including its article

2

translation

Italian translation

3

gender

m (masculine), f (feminine), n (neuter)

4

plural

Plural form of the noun

5

example

A short example sentence using the word

Gender Colour Convention

The box background colour SHALL reflect the grammatical gender:

Gender

Code

Colour

Hex

Masculine

m

Steel blue

#DBEAFE

Feminine

f

Soft rose

#FCE7F3

Neuter

n

Sage green

#D1FAE5

Example

::: vocab
der Hund | il cane | m | Hunde | Der Hund bellt laut.
:::

Rendering Intent

Compact card layout.

Article and word displayed prominently.

Gender-coded background colour.

Plural and example sentence displayed in smaller type below.

7.8 verb — Verb Entry

Purpose

Introduce a new verb with its core grammatical information.

Syntax

::: verb
infinitive | translation | auxiliary | past-participle | 3sg
:::

Fields (positional, pipe-separated)

Position

Field

Description

1

infinitive

German infinitive form

2

translation

Italian translation of the infinitive

3

auxiliary

haben or sein

4

past-participle

Partizip II form

5

3sg

Third person singular present (for irregular verbs)

Example

::: verb
gehen | andare | sein | gegangen | geht
:::

Rendering Intent

Compact card layout, similar to vocab.

Neutral background (no gender colour).

Auxiliary and past-participle displayed as grammatical tags.

7.9 conjugation — Verb Conjugation Table

Purpose

Display the full conjugation of a verb in a given tense.

Syntax

::: conjugation infinitive | translation
pronoun | conjugated-form | meaning
pronoun | conjugated-form | meaning
...
:::

Opening Line Fields

Position

Field

Description

1

infinitive

German infinitive

2

translation

Italian translation

Body Rows (three columns, pipe-separated)

Column

Content

1

Pronoun

2

Conjugated form

3

Italian meaning

Example

::: conjugation gehen | andare
ich    | gehe   | io vado
du     | gehst  | tu vai
er/sie | geht   | lui/lei va
wir    | gehen  | noi andiamo
ihr    | geht   | voi andate
sie    | gehen  | loro vanno
:::

Rendering Intent

Three-column table with clear column headers.

Header row displays the infinitive and translation.

Alternating row shading for readability.

7.10 formula — Formula

Purpose

Render a mathematical or chemical formula using LaTeX.

Subtypes

formula.math

Standard mathematical expression rendered in display math mode.

::: formula.math
E = mc^2
:::

formula.chem

Chemical equation rendered using the mhchem LaTeX package.

::: formula.chem
C_6H_{12}O_6 + 6O_2 \rightarrow 6CO_2 + 6H_2O
:::

Rendering Intent

Centred display block.

No label.

formula.math uses LaTeX display math (\[ ... \]).

formula.chem uses \ce{...} from the mhchem package.

8. Visual Summary

Shortcode

Label

Border colour

Background

rule

Regola

Slate blue

Light blue-grey

note

Nota

Amber

Light yellow

example

Beispiel

Teal

Light teal

exercise

Übung

Indigo

Light indigo

vocab (m)

—

Steel blue

#DBEAFE

vocab (f)

—

Rose

#FCE7F3

vocab (n)

—

Green

#D1FAE5

verb

—

Grey

Light grey

conjugation

—

—

Striped table

formula

—

—

Centred block

9. Future Evolution

Future versions MAY introduce:

additional subtypes for example (e.g. dialogue);

a table shortcode for custom reference tables;

tense parameter for conjugation (e.g. conjugation.past);

localisation support for labels (currently German/Italian assumed).

New shortcode types SHALL be defined in a revision of this document before implementation.

10. Change History

Version

Date

Description

1.0.0

2026-08-10

Initial release

End of document.
