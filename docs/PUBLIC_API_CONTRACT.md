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

## Confronto tra configurazioni V1.1

`edutex config diff` confronta la configurazione base con un profilo selezionato.
Il profilo è obbligatorio; il formato predefinito è testo e `--format json`
produce un rapporto strutturato.

```text
edutex config diff --profile NAME [--project PROJECT] [--config CONFIG] [--format text|json]
```

Una comparazione valida restituisce exit code 0 anche se rileva differenze.
Il rapporto JSON espone `comparison.changed` e `comparison.changes`; ogni
variazione contiene il percorso e i valori `base_value` e `profile_value`.
Gli errori di configurazione o di profilo restituiscono exit code 1.


## Report JSON di `course build` V1.1

L'opzione `--report-format` controlla il rapporto del comando e non modifica
`--format`, che continua a selezionare l'artefatto `html`, `latex` o `pdf`.
Il valore predefinito è `text`, così l'output testuale precedente resta
compatibile.

```text
edutex course build [--project PROJECT] [--manifest MANIFEST]
  [--format html|latex|pdf] [--output OUTPUT]
  [--profile NAME] [--report-format text|json]
```

Con `--report-format json`, un successo restituisce:

```json
{
  "course_build": {
    "status": "completed",
    "project_root": "...",
    "manifest": "...",
    "output_format": "html",
    "output": "...",
    "artifacts": ["...", "..."]
  }
}
```

`project_root`, `manifest`, `output` e ogni elemento di `artifacts` sono
percorsi assoluti. `artifacts` elenca tutti gli artefatti pubblici prodotti:
l'indice e le pagine delle lezioni per HTML, oppure l'artefatto principale per
LaTeX/PDF. Ogni percorso elencato identifica un file esistente.

Gli errori JSON hanno sempre exit code `1` e questa forma stabile:

```json
{
  "course_build": {
    "status": "failed",
    "error": {
      "type": "CourseBuildError",
      "message": "..."
    }
  }
}
```


## API pubblica di query del Content Model V1.2

Il modulo `edutex.knowledge` espone gli entry point Python:

```python
from edutex.knowledge import ContentQuery, query_content
```

`query_content(content_model)` restituisce una query read-only con le operazioni
`all()`, `by_type()`, `by_subtype()`, `search()` e `count()`. I risultati sono
copie distaccate, includono i nodi annidati in ordine preorder e non modificano
il `ContentModel` originale.
