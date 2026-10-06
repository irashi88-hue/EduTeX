# Theme composition contract

Status: candidate for V1.5
Quality check: Q043

## Configuration

A theme may declare ordered parent theme IDs in `extends`. IDs resolve only to
sibling directories beneath the selected theme root, each containing `theme.yaml`.
Legacy themes without `extends` remain valid and retain their existing values.

```yaml
id: school-blue
name: School Blue
version: "1.0.0"
extends: [default, school-brand]
palette:
  link: "#174ea6"
tokens:
  typography:
    body_font: "Atkinson Hyperlegible"
styles:
  exercise:
    background_color: "#eaf2ff"
```

## Composition and precedence

Parent layers are processed from left to right; the selected theme is the final
layer. The last-defined value wins. `styles`, `palette`, and `tokens` use recursive
mapping merge, so a partial node style preserves inherited fields. Lists and scalar
values are replaced, not concatenated. Identity metadata (`id`, `name`, and
`version`) always belongs to the selected theme.

## Safety and validation

Missing parents, duplicate parent IDs, malformed `extends`, unknown/path-like IDs,
and inheritance cycles are fatal `ThemeError` failures with deterministic context.
References cannot escape the sibling theme root, including through resolved paths.
Theme composition only reads YAML assets and does not mutate them or content models.
