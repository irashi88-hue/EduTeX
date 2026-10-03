# Contratto dei controlli di authoring

Stato: candidato per V1.2
Versione di riferimento: 1.2.0

## Comando pubblico

```text
edutex author validate SOURCE_FILE [--format text|json]
```

Il comando è separato da `edutex lint`, il cui contratto resta invariato.
Il formato predefinito è `text`; `json` è destinato a IDE e strumenti esterni.

## Controlli

Il comando verifica:

- frontmatter YAML obbligatorio del Knowledge Model;
- campi obbligatori `id`, `title`, `language`, `level` e `version`;
- parsing e grammatica degli shortcode;
- diagnostica già prodotta dal linter degli shortcode.

Non introduce nuovi shortcode e non modifica il contenuto del file.

## Rapporto JSON

Il rapporto JSON è sempre decodificabile e non contiene prefissi umani:

```json
{
  "authoring": {
    "status": "completed",
    "path": "...",
    "valid": true,
    "metadata": {
      "id": "...",
      "title": "...",
      "language": "...",
      "level": "...",
      "version": "..."
    },
    "errors": [],
    "warnings": [],
    "diagnostics": []
  }
}
```

`path` è assoluto. `metadata` è presente quando il frontmatter è valido.
`errors`, `warnings` e `diagnostics` sono liste di oggetti con almeno
`severity`, `code`, `message` e `path` quando applicabile.

Il comando restituisce exit code `0` se non ci sono errori.
Il comando restituisce exit code `1` quando il file non è valido o non è
leggibile. I warning non bloccano il comando.

## Compatibilità

- `edutex lint` mantiene forma, opzioni e JSON esistenti;
- `edutex validate` mantiene il proprio contratto;
- i Knowledge Model validi esistenti restano validi;
- il rapporto non modifica tema, layout o configurazione di build.
