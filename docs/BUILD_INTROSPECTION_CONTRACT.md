# Contratto di introspection dei metadati di build di EduTeX

Stato: draft per V1.1
Versione di riferimento: 1.1.0

Questo documento definisce i metadati aggiuntivi prodotti da
`edutex build --format json` quando il build termina correttamente.

## Compatibilità

Il contratto mantiene invariati:

- la chiave radice `lint`;
- la chiave radice `build`;
- `lint: null` quando il preflight non è richiesto;
- `build.status`;
- `build.output`;
- la forma di `build.error` nei fallimenti.

L'unica aggiunta di questa tranche è `build.metadata` nel percorso di successo.

## Rapporto di successo

```json
{
  "lint": null,
  "build": {
    "status": "completed",
    "output": "...",
    "metadata": {
      "project_root": "...",
      "config_file": "...",
      "output_format": "html",
      "output_path": "...",
      "output_exists": true
    }
  }
}
```

## Campi di `build.metadata`

| Campo | Tipo | Significato |
|---|---|---|
| `project_root` | stringa | Percorso assoluto della radice del progetto. |
| `config_file` | stringa | Percorso assoluto del file di configurazione usato. |
| `output_format` | stringa | Formato effettivamente selezionato: `html`, `latex` o `pdf`. |
| `output_path` | stringa | Percorso assoluto dell'artefatto prodotto. |
| `output_exists` | booleano | Deve essere `true` dopo un build completato. |

`build.output` e `build.metadata.output_path` devono identificare lo stesso
artefatto.

## Build con lint

Quando viene usato `--lint` e il lint blocca il build:

- `build.status` resta `blocked`;
- `lint` contiene il rapporto del preflight;
- `build.metadata` non viene prodotto;
- non deve essere dichiarato un artefatto inesistente.

## Errori

Nei fallimenti di configurazione, risoluzione o rendering resta valida la forma
esistente:

```json
{
  "lint": null,
  "build": {
    "status": "failed",
    "error": {
      "type": "...",
      "message": "..."
    }
  }
}
```

La nuova tranche non aggiunge metadati parziali ai fallimenti.

## Determinismo

- i nomi delle chiavi devono essere stabili;
- i percorsi devono essere serializzati come stringhe;
- `project_root`, `config_file` e `output_path` devono essere assoluti;
- lo stesso progetto e la stessa configurazione devono produrre metadati equivalenti;
- il formato JSON non deve contenere testo umano estraneo.

## Verifica locale

Dalla root del repository:

```powershell
python -m py_compile .\tests\test_build_introspection_contract.py
python -m pytest -q .\tests\test_build_introspection_contract.py
python -m pytest -q
python .\tools\quality_check.py --verbose
```
