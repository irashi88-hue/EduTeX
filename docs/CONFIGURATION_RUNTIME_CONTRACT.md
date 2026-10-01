# Contratto runtime della configurazione di EduTeX

Stato: candidato per V1
Versione di riferimento: 1.0.0

Questo documento descrive il comportamento runtime osservato del caricamento e
della risoluzione della configurazione EduTeX. Il contratto distingue lo
schema YAML, i default, l'immutabilità del modello e la risoluzione dei
percorsi.

Il modello radice validato è `EduTexConfig`.

## Struttura top-level

Le sezioni obbligatorie sono:

```yaml
edutex:
  version: "1.0.0"
knowledge:
  model: "assets/knowledge_models/example.md"
theme:
  name: "default"
layout:
  name: "default"
```

Le sezioni `build`, `extensions` e `logging` sono opzionali e vengono create
con i default del modello quando sono assenti.

| Sezione | Obbligatoria | Tipo runtime | Descrizione |
|---|---:|---|---|
| `edutex` | sì | `EduTexVersionConfig` | Versione del framework. |
| `knowledge` | sì | `KnowledgeConfig` | Selezione del Knowledge Model. |
| `theme` | sì | `ThemeConfig` | Nome del tema. |
| `layout` | sì | `LayoutConfig` | Nome del layout. |
| `build` | no | `BuildConfig` | Formato e destinazione dell'artefatto. |
| `extensions` | no | `ExtensionsConfig` | Estensioni abilitate. |
| `logging` | no | `LoggingConfig` | Livello di logging. |

## Campi e default

### `edutex`

| Campo | Tipo | Vincolo |
|---|---|---|
| `version` | stringa | obbligatoria, non vuota dopo `strip()`. |

### `knowledge`

| Campo | Tipo | Vincolo |
|---|---|---|
| `model` | `Path` | obbligatorio, non vuoto; il percorso può essere relativo o assoluto. |

### `theme` e `layout`

| Campo | Tipo | Vincolo |
|---|---|---|
| `name` | stringa | obbligatorio, `strip()` applicato, non vuoto. |

Il nome non è un percorso arbitrario: viene usato per cercare l'asset
corrispondente nella struttura del progetto.

### `build`

| Campo | Tipo | Default | Valori |
|---|---|---|---|
| `output_format` | `OutputFormat` | `pdf` | `pdf`, `latex`, `html`. |
| `output_dir` | `Path` | `output` | Directory dell'artefatto. |
| `output_file` | stringa | `document` | Nome base senza estensione. |

`build.output_file` è il campo pubblico che definisce il nome base dell'artefatto.
Viene usato come nome base al quale il Build Service aggiunge
l'estensione del formato scelto. Il modello verifica che non sia vuoto, ma non
trasforma il valore in un identificatore o in un percorso relativo sicuro: i
consumatori non devono inserire separatori di percorso se intendono un semplice
nome file.

### `extensions`

| Campo | Tipo | Default | Vincolo |
|---|---|---|---|
| `enabled` | lista di stringhe | `[]` | Ogni nome viene sottoposto a `strip()` e non può essere vuoto. |

### `logging`

| Campo | Tipo | Default | Valori |
|---|---|---|---|
| `level` | `LogLevel` | `INFO` | `DEBUG`, `INFO`, `WARNING`, `ERROR`. |

## Normalizzazione e immutabilità

Il modello validato è immutabile:

- i modelli Pydantic rifiutano la riassegnazione dei campi;
- la lista `extensions.enabled` rifiuta modifiche in-place;
- i nomi di tema, layout, estensioni e la versione vengono ripuliti dagli
  spazi iniziali e finali prima della validazione finale;
- un valore vuoto dopo la normalizzazione è un errore di configurazione.

La configurazione deve essere caricata e validata prima dell'avvio della
pipeline. Un componente non deve modificare il modello validato durante il
runtime.

## Risoluzione del file di configurazione

La CLI usa `--project` come root del progetto e risolve la root in forma
assoluta.

Per `--config` valgono queste regole:

- se il valore è relativo, il percorso finale è `project_root / config_file`;
- se il valore è assoluto, viene usato senza ri-ancorarlo alla root;
- il default è `edutex.config.yaml`;
- un file mancante produce `ConfigurationError`.

Esempio:

```text
--project C:\work\lesson
--config configs\local.yaml
```

risolve il file come:

```text
C:\work\lesson\configs\local.yaml
```

Un `--config` assoluto mantiene invece il proprio percorso assoluto.

## Risoluzione degli asset

I percorsi relativi configurati vengono risolti rispetto alla root del progetto:

- `knowledge.model` viene risolto rispetto a `project_root`;
- `build.output_dir` viene risolto rispetto a `project_root`;
- un percorso assoluto mantiene il proprio valore assoluto;
- `theme.name` seleziona `project_root/assets/themes/<name>/theme.yaml`;
- `layout.name` seleziona `project_root/assets/layouts/<name>/layout.yaml`;
- gli identificativi in `extensions.enabled` selezionano gli asset delle
  estensioni del progetto.

Il tema e il layout sono nomi logici, non percorsi arbitrari forniti
all'utente.

## Artefatti di build

Il Build Service crea `output_dir` se non esiste e produce:

| `output_format` | Artefatto principale |
|---|---|
| `html` | `<output_dir>/<output_file>.html` |
| `latex` | `<output_dir>/<output_file>.tex` |
| `pdf` | `<output_dir>/<output_file>.pdf`, con sorgente `.tex` intermedio. |

La compilazione PDF può richiedere strumenti LaTeX disponibili nel `PATH`; la
configurazione valida non garantisce da sola la presenza del compilatore.

## Errori di caricamento

Gli errori di configurazione sono rappresentati come `ConfigurationError`.
Quando il comando usa `--format json`, l'errore resta nel rapporto strutturato:

```json
{
  "validation": {
    "status": "failed",
    "error": {
      "type": "ConfigurationError",
      "message": "..."
    }
  }
}
```

Per un errore di build la stessa informazione si trova in `build.error`, mentre
la radice mantiene `lint: null` se il preflight `--lint` non è stato richiesto.

I messaggi già distinti dal loader includono:

- file di configurazione non trovato;
- file non codificato in UTF-8;
- YAML non valido;
- file vuoto;
- radice YAML non rappresentata da una mapping;
- fallimento della validazione dello schema.

## Compatibilità

Dalla V1:

- le quattro sezioni obbligatorie non possono essere rimosse o rinominate;
- i default di `build`, `extensions` e `logging` sono parte del contratto;
- i valori ammessi degli enum non possono cambiare senza documentazione;
- la risoluzione dei percorsi relativi deve restare ancorata a `project_root`;
- la configurazione validata deve restare immutabile;
- gli errori JSON devono mantenere `error.type` e `error.message`.

## Verifica locale

Dalla root del repository:

```powershell
python -m py_compile .\tests\test_configuration_runtime_contract.py
python -m pytest -q .\tests\test_configuration_runtime_contract.py
python -m pytest -q .\tests\test_validate_json.py .\tests\test_build_lint_json.py .\tests\test_course_management.py
```
