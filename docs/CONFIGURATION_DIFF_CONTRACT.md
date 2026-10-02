# Contratto del confronto tra configurazione base e profilo

Stato: candidato per V1.1
Versione di riferimento: 1.1.0

Questo contratto definisce `edutex config diff`, che confronta la configurazione
base con la configurazione effettiva prodotta da un profilo selezionato.

## Invocazione

Dalla root del progetto:

```powershell
edutex config diff --profile web
edutex config diff --project . --config edutex.config.yaml --profile web --format json
```

`--project` individua la root del progetto. `--config` accetta un percorso
relativo alla root oppure assoluto. `--profile NAME` è obbligatorio. Il formato
predefinito è testo; `--format json` produce il rapporto strutturato.

## Semantica

- La configurazione base e quella con il profilo vengono caricate e validate
  tramite il loader pubblico già usato dagli altri comandi.
- Il confronto riguarda i valori effettivi del modello validato, inclusi i
  valori predefiniti dello schema. Non risolve asset, non avvia la pipeline e
  non modifica il file YAML.
- Le mappe vengono confrontate ricorsivamente. Liste e valori scalari sono
  confrontati come valori atomici.
- `changes` contiene solo i campi effettivamente diversi, ordinati
  deterministicamente per percorso puntato.
- Il confronto concluso correttamente restituisce exit code 0, anche quando
  trova differenze. Errori di configurazione o di selezione del profilo
  restituiscono exit code 1.

## Rapporto JSON di successo

```json
{
  "comparison": {
    "status": "completed",
    "project_root": "...",
    "config_file": "...",
    "profile": "web",
    "changed": true,
    "changes": [
      {
        "path": "build.output_format",
        "base_value": "pdf",
        "profile_value": "html"
      }
    ]
  }
}
```

I percorsi `project_root` e `config_file` sono assoluti. Se non ci sono
modifiche, `changed` è `false` e `changes` è una lista vuota. Nel testo viene
mostrato un riepilogo leggibile; i valori sono serializzati come JSON.

## Errori JSON

```json
{
  "comparison": {
    "status": "failed",
    "error": {
      "type": "ConfigurationError",
      "message": "..."
    }
  }
}
```

In modalità testo gli errori usano il normale canale diagnostico della CLI.
La forma del rapporto JSON di errore non contiene differenze parziali.
