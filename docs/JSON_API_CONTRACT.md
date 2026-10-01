# Contratto JSON pubblico di EduTeX

Stato: candidato per V1
Versione di riferimento: 1.0.0

Questo documento descrive il contratto osservabile dei rapporti JSON prodotti
con l'opzione `--format json`. Il contratto è ricavato dall'inventario eseguito
sulla CLI reale di EduTeX; non aggiunge campi non osservati.

## Regole comuni

- Il comando deve scrivere un singolo oggetto JSON sulla sua uscita normale.
- L'oggetto radice deve essere decodificabile da un parser JSON standard.
- Il formato JSON non deve essere mescolato con il testo diagnostico umano.
- Un'operazione completata correttamente restituisce codice di uscita `0`.
- Un'operazione fallita restituisce un codice di uscita diverso da `0`.
- I nomi dei campi sono case-sensitive.
- I percorsi restituiti sono stringhe; la loro forma concreta dipende dal
percorso passato al comando e non deve essere interpretata come un percorso
relativo garantito.

Il contratto distingue i campi obbligatori della radice dai campi interni che
possono evolvere solo con una modifica documentata e testata.

## `edutex lint --format json`

### Radice obbligatoria

La radice deve contenere esattamente questi campi:

```json
{
  "path": "...",
  "valid": true,
  "errors": [],
  "warnings": []
}
```


| Campo      | Tipo     | Significato                                                       |
| ---------- | -------- | ----------------------------------------------------------------- |
| `path`     | stringa  | File Knowledge Model sottoposto a lint.                           |
| `valid`    | booleano | `true` se il file è valido; `false` se contiene errori bloccanti. |
| `errors`   | array    | Diagnostica di errore prodotta dal lint.                          |
| `warnings` | array    | Diagnostica non bloccante prodotta dal lint.                      |


Il comando deve restituire `valid: true` e codice `0` per una sorgente valida.
Per una sorgente non valida deve restituire `valid: false` e un codice diverso
da `0`; gli elementi diagnostici devono rimanere nel rispettivo array.

La forma interna degli elementi di `errors` e `warnings` non viene ampliata da
questa tranche oltre a quanto già esposto dalla CLI: i consumatori devono
trattarli come valori JSON e non devono inventare chiavi ulteriori.

## `edutex validate --format json`

### Radice obbligatoria

La radice deve contenere il campo `validation`:

```json
{
  "validation": {
    "status": "completed"
  }
}
```

`validation` è un oggetto. Il campo obbligatorio `validation.status` è una
stringa. Nel percorso di successo il valore è `completed`.

Nel percorso di errore l'oggetto mantiene `status: "failed"` e può contenere
un oggetto `error` con i dati dell'errore runtime:

```json
{
  "validation": {
    "status": "failed",
    "error": {
      "type": "...",
      "message": "...",
      "diagnostics": []
    }
  }
}
```

`error.type` e `error.message` identificano rispettivamente il tipo e il
messaggio dell'errore. `error.diagnostics` è presente quando il fallimento
produce diagnostica strutturata di un'estensione.

## `edutex build --format json`

### Radice obbligatoria

La radice deve contenere questi due campi:

```json
{
  "lint": null,
  "build": {}
}
```


| Campo   | Tipo             | Significato                                                                                  |
| ------- | ---------------- | -------------------------------------------------------------------------------------------- |
| `lint`  | oggetto o `null` | Risultato del lint; è `null` quando il build è eseguito senza l'opzione `--lint`.             |
| `build` | oggetto          | Risultato della generazione dell'artefatto.                                                   |


Nel percorso di successo, `build.status` è `completed` e il codice di uscita
è `0`.

Nel percorso di errore, `build.status` è `failed`. Quando l'errore deriva da
un'estensione, `build.error` contiene almeno `type`, `message` e, se prodotti,
`diagnostics`.

Quando il preflight `--lint` non è richiesto, `lint` è `null`; quando è
richiesto, contiene il risultato del preflight. La chiave `lint` non deve essere
sostituita con testo libero o con un prefisso umano.

## `edutex course validate --format json`

### Radice obbligatoria

La radice deve contenere questi sei campi:

```json
{
  "manifest": "...",
  "valid": true,
  "errors": [],
  "warnings": [],
  "diagnostics": [],
  "course": {}
}
```


| Campo         | Tipo     | Significato                                                    |
| ------------- | -------- | -------------------------------------------------------------- |
| `manifest`    | stringa  | Manifesto del corso sottoposto a validazione.                  |
| `valid`       | booleano | Esito della validazione del corso.                             |
| `errors`      | array    | Errori di validazione del manifesto o delle lezioni collegate. |
| `warnings`    | array    | Avvisi non bloccanti.                                          |
| `diagnostics` | array    | Diagnostica strutturata aggiuntiva.                            |
| `course`      | oggetto  | Rappresentazione validata del corso quando disponibile.        |


Un manifesto valido deve produrre `valid: true` e codice `0`. Gli array devono
rimanere presenti anche quando sono vuoti.

## Diagnostica delle estensioni

Quando un'estensione fallisce durante `validate` o `build`, il rapporto JSON
mantiene l'errore nella sezione del comando interessato. Per il percorso
verificato dal quality gate, i valori stabili sono:

- `error.type`: `ExtensionError`;
- `error.message`: messaggio dell'errore del gestore;
- `error.diagnostics`: array di oggetti diagnostici;
- `diagnostics[].extension_id`: identificativo dell'estensione;
- `diagnostics[].point_id`: punto di estensione, per esempio
`layout.post_structure`;
- `diagnostics[].phase`: fase della diagnostica, per esempio `handler`;
- `diagnostics[].message`: dettaglio leggibile della diagnostica.

Gli identificatori `extension_id`, `point_id` e `phase` sono dati strutturati,
non testo da ricavare facendo parsing del messaggio. Nuovi codici o nuovi valori
ammessi devono essere aggiunti a questo documento e coperti da test.

## Configurazione e risoluzione dei percorsi

La configurazione pubblica mantiene la struttura seguente:

```yaml
edutex:
  version: "0.7.0"
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

Regole di risoluzione:

- `--project` identifica la radice del progetto;
- `--config` è risolto rispetto alla radice del progetto quando è relativo;
- un percorso di configurazione assoluto viene usato senza ri-ancorarlo al
progetto;
- `knowledge.model` e `build.output_dir` sono percorsi relativi alla radice del
progetto quando sono relativi;
- `theme.name`, `layout.name` e gli identificativi in `extensions.enabled` sono
nomi logici risolti dagli asset del progetto;
- `build.output_file` è il nome base dell'artefatto; l'estensione finale è
determinata da `build.output_format`.

I formati di output configurabili sono quelli già esposti dalla CLI e dalla
configurazione: `html`, `latex` e `pdf`.

## Compatibilità

Prima della V1:

- le nuove chiavi JSON devono essere aggiunte esplicitamente;
- i campi obbligatori non devono essere rimossi o rinominati senza una modifica
documentata del contratto;
- i cambiamenti ai tipi devono avere un test di regressione;
- gli errori devono continuare a essere rappresentati in JSON valido quando è
richiesto `--format json`;
- i messaggi umani non devono essere usati come sostituto dei campi strutturati.

Dalla V1, le chiavi e i tipi documentati qui sono API pubblica.

## Verifica locale

Dalla radice del repository:

```powershell
python -m py_compile .\tests\test_json_api_contract.py
python -m pytest -q .\tests\test_json_api_contract.py
python -m pytest -q
python .\tools\quality_check.py --verbose
python .\tools\release_smoke.py
```
