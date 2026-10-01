# Catalogo diagnostico pubblico di EduTeX

Stato: candidato per V1
Versione di riferimento: 1.0.0

Questo documento descrive le diagnostiche già esposte dalla CLI e dai rapporti
JSON di EduTeX. Il catalogo mantiene separati i contratti delle estensioni,
della validazione dei corsi e del lint dei Knowledge Model.

Non esiste un codice diagnostico globale condiviso da tutti i sottosistemi:
`ExtensionDiagnostic`, `CourseDiagnostic` e le diagnostiche del lint hanno
proprietà e identificatori differenti.

## Regole comuni

- La diagnostica strutturata deve essere serializzabile in JSON.
- L'ordine degli elementi deve essere preservato dall'origine al rapporto.
- I messaggi leggibili non sostituiscono i campi strutturati.
- Il canale JSON non deve contenere il prefisso del canale testuale umano.
- L'aggiunta di un nuovo codice o campo pubblico richiede documentazione e test.
- Un codice appartenente a una famiglia non deve essere riutilizzato con un
  significato diverso in un'altra famiglia.

## Diagnostica runtime delle estensioni

### Modello `ExtensionDiagnostic`

La diagnostica prodotta dall'Extension System ha questi quattro campi:

| Campo | Tipo | Presenza | Significato |
|---|---|---|---|
| `extension_id` | stringa o `null` | obbligatorio | Identificativo dell'estensione coinvolta, se già noto. |
| `point_id` | stringa o `null` | obbligatorio | Punto di estensione coinvolto, se già noto. |
| `phase` | stringa | obbligatorio | Fase del processing in cui è stato rilevato il problema. |
| `message` | stringa | obbligatorio | Dettaglio dell'eccezione o del problema. |

Esempio serializzato:

```json
{
  "extension_id": "reading_tip",
  "point_id": "layout.post_structure",
  "phase": "handler",
  "message": "handler boom"
}
```

`extension_id` e `point_id` possono essere `null` quando l'errore avviene
prima che il contesto sia stato completamente risolto. I consumatori non devono
scartare la diagnostica per questo motivo.

### Integrazione nei rapporti CLI

Un errore del processing delle estensioni usa:

```json
{
  "type": "ExtensionError",
  "message": "Extension processing failed",
  "diagnostics": [
    {
      "extension_id": "reading_tip",
      "point_id": "layout.post_structure",
      "phase": "handler",
      "message": "handler boom"
    }
  ]
}
```

L'oggetto è inserito in:

- `build.error` per `edutex build --format json`;
- `validation.error` per `edutex validate --format json`.

Nel canale testuale, la stessa famiglia usa il titolo `Extension diagnostics:`
e riporta i campi `extension_id`, `point_id`, `phase` e `message` senza perdere
il dettaglio strutturato.

### Valori osservati

Sono già coperti dalla CLI e dai test:

- `error.type = ExtensionError`;
- `point_id = layout.post_structure`;
- `phase = handler`;
- serializzazione in ordine di input;
- messaggio del gestore conservato sia nel campo `message` dell'errore sia
  nella diagnostica dell'estensione.

Le stringhe di fase non costituiscono un enum chiuso in questa versione: un
nuovo valore deve però essere documentato quando diventa parte dell'output
pubblico.

## Diagnostica della validazione dei corsi

La validazione di `course.yaml` espone una lista top-level `diagnostics` e,
per compatibilità, mantiene anche le liste legacy `errors` e `warnings`.

Ogni diagnostica di corso usa almeno questi campi:

| Campo | Tipo | Presenza | Significato |
|---|---|---|---|
| `code` | stringa | obbligatorio | Codice stabile della condizione rilevata. |
| `severity` | stringa | obbligatorio | Gravità, per esempio `error` o `warning`. |
| `message` | stringa | obbligatorio | Descrizione leggibile. |
| `field` | stringa | opzionale | Campo del manifesto coinvolto, quando disponibile. |
| `path` | stringa | opzionale | Percorso dell'asset coinvolto, quando disponibile. |

I campi opzionali non devono essere inseriti con valori fittizi. Se il
contesto non è disponibile, la chiave deve essere omessa.

### Codici documentati

| Codice | Gravità osservata | Uso |
|---|---|---|
| `COURSE_SOURCE_FRONTMATTER_MISSING` | `error` | La sorgente di una lezione collegata non contiene il front matter richiesto. |
| `COURSE_DURATION_UNDECLARED` | `warning` | Una lezione non dichiara la durata prevista. |

Esempio di diagnostica di errore:

```json
{
  "code": "COURSE_SOURCE_FRONTMATTER_MISSING",
  "severity": "error",
  "message": "...",
  "field": "course.modules[1].lessons[1].source",
  "path": "lessons/hello.md"
}
```

Esempio di avviso senza campo artificiale:

```json
{
  "code": "COURSE_DURATION_UNDECLARED",
  "severity": "warning",
  "message": "..."
}
```

La lista `errors` deve contenere il `message` delle diagnostiche con gravità
`error`; la lista `warnings` deve mantenere lo stesso rapporto per le
avvertenze. La lista `diagnostics` resta la fonte strutturata.

Altri codici già presenti nel runtime devono essere aggiunti a questo catalogo
solo dopo un inventario mirato e un test che ne dimostri la forma.

## Diagnostica del lint dei Knowledge Model

Il lint espone le diagnostiche in due array separati:

- `errors`, per condizioni bloccanti;
- `warnings`, per condizioni non bloccanti.

I codici del lint appartengono alla famiglia del Knowledge Model e non devono
essere confusi con i codici `COURSE_*` della validazione corsi o con
`ExtensionError`. Il codice osservato nei test esistenti è `SC106`.

Questa tranche stabilizza la separazione delle famiglie, ma non amplia la forma
interna degli elementi di lint oltre quanto già esposto dalla CLI.

## Compatibilità e determinismo

Dalla V1:

- `ExtensionDiagnostic` mantiene i quattro campi documentati;
- i rapporti di `build` e `validate` mantengono `error.type`, `message` e
  `diagnostics` nei fallimenti delle estensioni;
- `CourseDiagnostic.code`, `severity` e `message` restano obbligatori;
- `field` e `path` restano opzionali e non devono essere aggiunti artificialmente;
- l'ordine delle diagnostiche resta deterministico;
- `errors`, `warnings` e `diagnostics` non devono essere fusi in un unico array;
- i codici esistenti non possono cambiare significato senza una modifica
  documentata del contratto.

## Verifica locale

Dalla root del repository:

```powershell
python -m py_compile .\tests\test_diagnostic_catalog.py
python -m pytest -q .\tests\test_diagnostic_catalog.py
python -m pytest -q .\tests\test_build_lint_json.py .\tests\test_validate_json.py .\tests\test_course_management.py
```
