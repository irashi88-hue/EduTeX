# EduTeX

A modular framework for generating educational documents from structured content.

## Architecture

EduTeX is organized into four architectural layers:

```
Runtime Infrastructure   -> Core, Configuration, Registry, Resolver, Activator
Framework Services       -> Knowledge, Theme, Layout
Architectural Mechanisms -> Extension System, Build System
User Assets              -> Knowledge Models
```

## Project Structure

```
src/edutex/          # Framework source code
  core/              # Runtime orchestration (CC-001, CC-002, CC-003)
  configuration/     # Validated configuration (CFG-001, CFG-002)
  registry/          # Entity registry (REG-001, REG-002)
  resolver/          # Reference resolution (RES-001, RES-002)
  activator/         # Runtime activation (ACT-001, ACT-002)
  knowledge/         # Knowledge processing (KNOW-001, KNOW-002)
  theme/             # Theme processing (THEME-001, THEME-002)
  layout/            # Layout processing (LAYOUT-001, LAYOUT-002)
  extension/         # Extension system (EXT-001, EXT-002)
  build/             # Build system (BUILD-001, BUILD-002)
assets/
  knowledge_models/  # User-authored Knowledge Models (.md)
  themes/            # Theme definitions
  layouts/           # Layout definitions
tests/
  unit/              # Unit tests per component
  integration/       # End-to-end pipeline tests
docs/                # Architecture and specification documents
tools/               # Developer tooling scripts
```

## Specifications

All architectural specifications are located in docs/.
