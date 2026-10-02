# Contratto di introspection tooling di EduTeX

Stato: draft per V1.1
Versione di riferimento: 1.1.0

Questo documento definisce il contratto JSON del comando `edutex inspect`. Il comando espone informazioni risolte sulla configurazione, sugli asset e sul runtime del progetto senza eseguire il build del documento.

## Scopo

Il comando è destinato a:

- IDE;
- strumenti di authoring;
- script CI;
- diagnostica locale;
- integrazioni esterne.

Il comando non deve modificare file, configurazione o artefatti di build e non deve importare né eseguire codice Python delle estensioni.

## Sintassi

```text
edutex inspect [--project PROJECT] [--config CONFIG] [--format json]
```

Valori predefiniti:

```text
--project: .
--config: edutex.config.yaml
--format: json
```

Il comando restituisce codice `0` quando la configurazione e gli asset richiesti sono validi e registry e resolver terminano correttamente. Restituisce un codice diverso da `0` in caso di errore.

## Rapporto JSON di successo

La radice contiene esattamente la chiave `inspection`:

```json
{
  "inspection": {
    "status": "completed",
    "project_root": "...",
    "config_file": "...",
    "configuration": {
      "framework_version": "1.0.0",
      "knowledge_model": "assets/knowledge_models/example.md",
      "theme": "default",
      "layout": "default",
      "build": {
        "output_format": "html",
        "output_dir": "...",
        "output_file": "document"
      },
      "extensions": [],
      "logging_level": "INFO"
    },
    "assets": {
      "knowledge_model": {"path": "...", "exists": true},
      "theme": {"path": "...", "exists": true},
      "layout": {"path": "...", "exists": true},
      "extensions": []
    },
    "runtime": {
      "registry": {
        "entity_count": 3,
        "entities": [
          {
            "id": "example",
            "type": "knowledge_model",
            "source_path": "..."
          }
        ]
      },
      "resolver": {
        "status": "completed",
        "entity_count": 3,
        "edge_count": 0,
        "entities": [
          {
            "id": "example",
            "type": "knowledge_model",
            "source_path": "..."
          }
        ],
        "edges": []
      },
      "extensions": []
    }
  }
}
```

L'esempio abbreviato omette gli altri entity record e tutti i campi delle estensioni eventualmente abilitate.

## Campi obbligatori

| Campo | Tipo | Significato |
|---|---|---|
| `inspection.status` | stringa | Deve essere `completed` in caso di successo. |
| `inspection.project_root` | stringa | Percorso assoluto della radice del progetto. |
| `inspection.config_file` | stringa | Percorso assoluto del file di configurazione. |
| `inspection.configuration` | oggetto | Configurazione validata e normalizzata. |
| `inspection.assets` | oggetto | Asset selezionati e verificati dal progetto. |
| `inspection.runtime` | oggetto | Snapshot del registry e del grafo risolto. |

La configurazione mantiene i campi già pubblicati:

- `framework_version`;
- `knowledge_model`;
- `theme`;
- `layout`;
- `build`;
- `extensions`;
- `logging_level`.

Il blocco `build` mantiene:

- `output_format`;
- `output_dir`, risolto in forma assoluta;
- `output_file`.

Gli array `configuration.extensions`, `assets.extensions` e `runtime.extensions` mantengono l'ordine dichiarato nella configurazione.

## Asset

Ogni asset principale contiene:

```json
{"path": "...", "exists": true}
```

Gli asset principali sono `knowledge_model`, `theme` e `layout`. Le estensioni configurate sono rappresentate in `assets.extensions` da oggetti con gli stessi campi `path` ed `exists`. I loro percorsi sono assoluti.

## Registry

`runtime.registry` descrive le entità effettivamente registrate per il progetto:

- `entity_count`: numero di elementi in `entities`;
- `entities`: array ordinato di entity record.

Ogni entity record contiene:

| Campo | Tipo | Significato |
|---|---|---|
| `id` | stringa | Identificatore dell'entità nel registry. |
| `type` | stringa | Tipo stabile in snake case, per esempio `knowledge_model`, `theme`, `layout` o `extension`. |
| `source_path` | stringa | Percorso assoluto dell'asset registrato. |

L'ordine è quello di registrazione: Knowledge Model, tema, layout e poi estensioni nell'ordine di configurazione. L'array riflette le entità del runtime, non tutte le directory presenti su disco.

## Resolver

`runtime.resolver` descrive il grafo prodotto dal resolver:

- `status`: `completed` in caso di successo;
- `entity_count`: numero di elementi in `entities`;
- `entities`: entity record presenti nel grafo, con gli stessi campi e nello stesso ordine del registry;
- `edge_count`: numero di elementi in `edges`;
- `edges`: relazioni risolte, nell'ordine prodotto dal resolver.

Ogni edge contiene:

| Campo | Tipo | Significato |
|---|---|---|
| `source_id` | stringa | ID dell'entità sorgente. |
| `source_type` | stringa | Tipo dell'entità sorgente in snake case. |
| `target_id` | stringa | ID dell'entità destinazione. |
| `target_type` | stringa | Tipo dell'entità destinazione in snake case. |
| `reference_type` | stringa | Tipo della relazione dichiarata. |

`entity_count` ed `edge_count` devono corrispondere alla lunghezza dei rispettivi array. Un progetto senza riferimenti produce `edges: []` e `edge_count: 0`.

## Estensioni abilitate

`runtime.extensions` contiene esclusivamente le estensioni abilitate nella configurazione, nello stesso ordine. Ogni elemento contiene i campi del manifest validato:

- `id`;
- `name`;
- `version`;
- `target`;
- `module`;
- `entrypoint`;
- `manifest_path`, percorso assoluto del manifest;
- `module_path`, percorso assoluto per un modulo locale oppure `null` per un riferimento a modulo importabile;
- `module_exists`, `true` per un file locale verificato oppure `null` quando il manifest usa un nome di modulo importabile.

L'ispezione legge e valida il manifest, l'ID atteso e i percorsi locali. Un percorso locale deve rimanere dentro la directory dell'estensione e il file deve esistere. Se il manifest usa un nome di modulo importabile, l'ispezione non prova a importarlo e lascia `module_path` e `module_exists` a `null`.

Il comando non importa il modulo e non verifica se `entrypoint` sia callable: ciò potrebbe eseguire codice arbitrario dell'estensione. Tale verifica resta responsabilità del caricamento durante il normale processamento.

## Rapporto JSON di errore

In caso di errore la radice mantiene la chiave `inspection` e il payload non contiene sezioni di successo parziali:

```json
{
  "inspection": {
    "status": "failed",
    "error": {
      "type": "ConfigurationError",
      "message": "..."
    }
  }
}
```

La forma di errore resta invariata. Errori di configurazione, asset, manifest, registry o resolver non devono produrre `runtime` parziale.

## Regole di determinismo e compatibilità

- l'ordine delle chiavi documentate deve essere stabile;
- l'ordine degli asset e delle estensioni abilitate deve essere quello della configurazione;
- gli entity record del registry e del resolver devono seguire l'ordine di registrazione;
- gli stessi input devono produrre lo stesso rapporto;
- i percorsi devono essere serializzati come stringhe assolute, salvo i campi di modulo esplicitamente nullable;
- il comando non deve eseguire il build, importare estensioni o modificare il progetto;
- la nuova sezione `runtime` è additiva: i campi di successo già pubblicati non cambiano;
- la forma del rapporto di errore resta invariata;
- i rapporti di `edutex lint --format json`, `edutex validate --format json`, `edutex build --format json` e `edutex course validate --format json` restano invariati.
