# Contratto del catalogo ufficiale delle estensioni

Stato: candidato per V1.3
Versione di riferimento: 1.3.0

## API pubblica

Il catalogo è esposto da `edutex.extension.catalog`:

- `official_extension_catalog()` restituisce le voci ufficiali in ordine
  stabile;
- `get_official_extension(extension_id)` cerca una voce per identificativo;
- `search_official_extensions(query)` cerca in ID, nome, target e descrizione;
- `ExtensionCatalogEntry.to_dict()` produce una rappresentazione JSON detached.

## Voce catalogata

La prima voce ufficiale è:

```json
{
  "id": "reading_tip",
  "name": "Reading tip",
  "version": "1.0.0",
  "framework": ">=1.0.0,<2.0.0",
  "target": "layout.post_structure",
  "optional": false
}
```

Il catalogo è metadata-only: non installa, importa o attiva estensioni e non
modifica il normale percorso di build. L'ordine delle voci e i nomi dei campi
sono parte del contratto pubblico.

Le ricerche sono case-insensitive, preservano l'ordine del catalogo e con query
vuota restituiscono tutte le voci. Un ID non presente restituisce `None`.
