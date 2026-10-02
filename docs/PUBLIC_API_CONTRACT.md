# Contratto dell'API pubblica di EduTeX

Stato: candidato per V1
Versione di riferimento: 1.0.0

Questo documento descrive l'interfaccia pubblica che EduTeX deve mantenere
stabile verso la versione 1.0.0.

## Entry point

```text
edutex = edutex.core.cli:main
```

## Comandi pubblici

```text
edutex init
edutex lint
edutex build
edutex inspect
edutex validate
edutex course validate
edutex course build
```

## Sintassi CLI

```text
edutex init [PROJECT_DIR] [--theme default|dark] [--language en|it|ja] [--force]

edutex lint SOURCE_FILE [--format text|json]

edutex build [--project PROJECT] [--config CONFIG] [--lint] [--format text|json]

edutex inspect [--project PROJECT] [--config CONFIG] [--format json]

edutex validate [--project PROJECT] [--config CONFIG] [--format text|json]

edutex inspect [--project PROJECT] [--config CONFIG] [--format json]

edutex course validate [--project PROJECT] [--manifest MANIFEST] [--format text|json]

edutex course build [--project PROJECT] [--manifest MANIFEST] [--format html|latex|pdf] [--output OUTPUT]
```

## Valori predefiniti

```text
init PROJECT_DIR: edutex-project
init --theme: dark
init --language: it

build --project: .
build --config: edutex.config.yaml
build --format: text

validate --project: .
validate --config: edutex.config.yaml
validate --format: text

inspect --project: .
inspect --config: edutex.config.yaml
inspect --format: json

course validate --project: .
course validate --manifest: course.yaml
course validate --format: text

course build --project: .
course build --manifest: course.yaml
course build --format: html
```

## Opzioni globali

```text
edutex --version
edutex --help
```

Il formato dell'artefatto generato e definito dalla chiave `build.output_format`.

## Configurazione pubblica

Le chiavi supportate sono:

```yaml
edutex:
  version: "1.0.0"

knowledge:
  model: "assets/knowledge_models/example.md"

theme:
  name: "default"

layout:
  name: "default"

build:
  output_format: "html"
  output_dir: "output"
  output_file: "document"

extensions:
  enabled: []

logging:
  level: "INFO"
```

## Codici di uscita

- `0`: comando completato correttamente;
- valore diverso da `0`: errore di input, validazione, configurazione, lint o build;
- il formato `json` deve produrre output decodificabile;
- l'output JSON non deve essere mescolato con testo diagnostico casuale.

## Compatibilita verso V1

Prima di `1.0.0`:

- le nuove opzioni devono essere aggiunte esplicitamente;
- i comandi esistenti non devono essere rimossi senza documentazione;
- le modifiche ai rapporti JSON devono avere test di regressione;
- le modifiche alla configurazione devono preservare i progetti validi quando possibile.

Da `1.0.0`:

- nomi dei comandi, opzioni e chiavi di configurazione documentate sono API pubblica;
- i campi JSON documentati sono API pubblica;
- le modifiche incompatibili richiedono una nuova versione principale.

## Verifica

```powershell
python -m pytest -q
python tools/quality_check.py --verbose
python tools/release_smoke.py
```

## Profili di configurazione V1.1

`edutex build`, `edutex validate`, `edutex inspect` e `edutex course build`
accettano l'opzione `--profile NAME`. I profili sono definiti in `profiles:` nel
file `edutex.config.yaml`. `course build --profile` è ammesso solo con `--format
html`; per PDF e LaTeX l'opzione viene rifiutata.
