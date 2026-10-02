# Contratto dell'API di query del Content Model

Stato: candidato per V1.2
Versione di riferimento: 1.2.0

## Scopo

L'API permette a strumenti, integrazioni e front-end di interrogare un
`ContentModel` già processato senza conoscere il parser o modificare il
contenuto educativo.

L'entry point pubblico è:

```python
from edutex.knowledge import ContentQuery, query_content

query = query_content(content_model)
```

Sono esportati pubblicamente `ContentQuery` e `query_content`.

## Semantica

- la query accetta solo un'istanza di `ContentModel`;
- la query crea uno snapshot distaccato del modello;
- i nodi sono restituiti in ordine preorder deterministico;
- l'ordine include i nodi annidati dopo il rispettivo nodo padre;
- ogni risultato è una copia distaccata e non può modificare il modello;
- i `TextBlock` non fanno parte dei risultati delle query di nodi.

## Operazioni

| Operazione | Risultato |
|---|---|
| `all()` | Tutti i `ContentNode`, inclusi quelli annidati. |
| `by_type(value)` | Nodi con `node_type` corrispondente, senza distinzione tra maiuscole e minuscole. |
| `by_subtype(value)` | Nodi con `subtype` non nullo corrispondente. |
| `search(value)` | Nodi in cui il testo appare in tipo, sottotipo, campi o corpo. |
| `count()` | Numero totale dei nodi nello snapshot. |
| `count(value)` | Numero dei nodi del tipo indicato. |

I filtri devono essere stringhe non vuote. Un filtro non valido produce
`ValueError`; un oggetto diverso da `ContentModel` produce `TypeError`.

## Determinismo e compatibilità

Le operazioni non modificano `ContentModel`, `ContentNode` o i relativi figli.
I confronti di tipo, sottotipo e ricerca sono case-insensitive e usano il testo
normalizzato con gli spazi esterni rimossi. La forma di `ContentModel.nodes()` e
`ContentModel.nodes_of_type()` non cambia.

L'API non introduce parsing alternativo, nuove shortcode o cambiamenti al
processamento del Knowledge Model.

## Verifica locale

```powershell
python -m py_compile .\src\edutex\knowledge\query.py
python -m pytest -q .\tests\test_content_model_query_contract.py
python -m pytest -q
python .\tools\quality_check.py --verbose
python .\tools\release_smoke.py
```
