# Theme zero-configuration contract

## Purpose

HTML and LaTeX builds use EduTeX's bundled `default` theme whenever the configuration
omits `theme.name`. The bundled asset is shipped with the `edutex` package, so a project
can build without copying or maintaining `assets/themes/default/theme.yaml`.

## Selection and failure behavior

- An omitted theme, including an empty `theme: {}` mapping, selects the bundled `default`.
- A theme name explicitly supplied in configuration selects only the matching project asset
  at `assets/themes/<name>/theme.yaml`.
- A missing or invalid explicitly selected theme is a build error. It must never silently
  fall back to the bundled theme.
- Existing projects that explicitly select `default` continue to use their project theme
  asset, preserving current customization behavior.
- The default is loaded as a package resource and does not become a project registry entity.

## Supported outputs

Zero-configuration theme selection is used by both HTML and LaTeX builds. Other build
format behavior is unchanged.

## Validation

Contract tests build both formats without any project theme directory, verify explicit
missing/invalid theme failures, and validate that the bundled YAML is included in package
metadata. Q044 checks the implementation, documentation, package resource, and tests.
