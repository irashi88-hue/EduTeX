# Contratto dello schema del Content Model

Stato: candidato per V1.2
Versione di riferimento: 1.2.0
Versione dello schema: 1.0.0

## API pubblica

Lo schema è esposto dal modulo `edutex.knowledge`:

```python
from edutex.knowledge import (
    CONTENT_MODEL_SCHEMA_VERSION,
    content_model_schema,
)

schema = content_model_schema()
```

`content_model_schema()` restituisce sempre un nuovo dizionario JSON-safe e
serializzabile con `json.dumps`. La modifica del dizionario restituito non
modifica lo schema delle chiamate successive.

## Dialetto e radice

Lo schema usa JSON Schema Draft 2020-12 e descrive una radice oggetto con:

- `items` obbligatorio e di tipo array;
- `additionalProperties: false` sulla radice e sui tipi di item;
- `$defs.contentNode` per i nodi shortcode;
- `$defs.textBlock` per i blocchi di prosa;
- `$defs.contentItem` come unione dei due tipi.

## ContentNode

Ogni `ContentNode` espone esattamente:

- `node_type`: stringa obbligatoria;
- `subtype`: stringa o `null`, obbligatorio;
- `fields`: array obbligatorio di stringhe;
- `body`: stringa obbligatoria;
- `children`: array obbligatorio di `contentNode` ricorsivi;
- `source_line`: intero obbligatorio maggiore o uguale a zero.

## TextBlock

Ogni `TextBlock` espone esattamente `content`, una stringa obbligatoria.

## Compatibilità

Lo schema descrive la rappresentazione tipizzata dopo il parsing. Non modifica
la sintassi Markdown, la grammatica degli shortcode, il parser o la pipeline di
processing. L'API di query del Content Model resta compatibile e continua a
restituire copie distaccate.

La struttura e l'ordine delle chiavi sono stabili per la serializzazione
JSON deterministica. `$id` contiene la versione pubblica dello schema.
