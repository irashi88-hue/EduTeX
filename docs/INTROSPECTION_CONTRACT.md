# Contratto di introspection tooling di EduTeX

Stato: draft per V1.1
Versione di riferimento: 1.1.0

Questo documento definisce il contratto JSON del comando `edutex inspect`.
Il comando espone informazioni risolte sulla configurazione e sugli asset del
progetto senza eseguire il build del documento.

## Scopo

Il comando è destinato a:

- IDE;
- strumenti di authoring;
- script CI;
- diagnostica locale;
- integrazioni esterne.

Il comando non deve modificare file, configurazione o artefatti di build.

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

Il comando restituisce codice `0` quando la configurazione e gli asset sono
validi. Restituisce un codice diverso da `0` in caso di errore.

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
      "knowledge_model": {
        "path": "...",
        "exists": true
      },
      "theme": {
        "path": "...",
        "exists": true
      },
      "layout": {
        "path": "...",
        "exists": true
      },
      "extensions": []
    }
  }
}
```

## Campi obbligatori

| Campo | Tipo | Significato |
|---|---|---|
| `inspection.status` | stringa | Deve essere `completed` in caso di successo. |
| `inspection.project_root` | stringa | Radice assoluta del progetto. |
| `inspection.config_file` | stringa | Percorso assoluto del file di configurazione. |
| `inspection.configuration` | oggetto | Configurazione validata e normalizzata. |
| `inspection.assets` | oggetto | Asset risolti dal progetto. |

La configurazione deve contenere:

- `framework_version`;
- `knowledge_model`;
- `theme`;
- `layout`;
- `build`;
- `extensions`;
- `logging_level`.

Il blocco `build` deve contenere:

- `output_format`;
- `output_dir`, risolto in forma assoluta;
- `output_file`.

Gli array `extensions` devono mantenere l'ordine dichiarato nella
configurazione.

## Asset

Ogni asset principale deve contenere:

```json
{
  "path": "...",
  "exists": true
}
```

Gli asset principali sono:

- `knowledge_model`;
- `theme`;
- `layout`.

Le estensioni sono rappresentate da un array di oggetti con la stessa forma
`path` e `exists`.

## Rapporto JSON di errore

In caso di errore la radice mantiene la chiave `inspection`:

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

Il rapporto di errore non deve contenere testo umano estraneo al JSON.

## Regole di determinismo

- l'ordine delle chiavi documentate deve essere stabile;
- l'ordine delle estensioni deve essere quello della configurazione;
- gli stessi input devono produrre lo stesso rapporto;
- i percorsi devono essere serializzati come stringhe;
- il comando non deve eseguire il build;
- il comando non deve modificare il progetto.

## Compatibilità

Il comando `inspect` è aggiuntivo e non modifica la forma dei rapporti
prodotti da:

- `edutex lint --format json`;
- `edutex validate --format json`;
- `edutex build --format json`;
- `edutex course validate --format json`.

Le modifiche future alla forma di `inspection` devono essere documentate e
coperte da test di regressione.
