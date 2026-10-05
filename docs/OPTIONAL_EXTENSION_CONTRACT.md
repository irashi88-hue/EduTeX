# Contratto delle estensioni opzionali

Stato: candidato per V1.3
Versione di riferimento: 1.3.0

## Dichiarazione

Un manifest può dichiarare:

```yaml
optional: true
```

Il valore predefinito è `false`, quindi i manifest esistenti restano
obbligatori e mantengono il comportamento precedente.

## Fallback controllato

Il chiamante che desidera il fallback usa l'API esplicita
`load_extension_with_fallback`. La funzione legge prima il manifest e quindi
può applicare la regola in modo deterministico:

- un manifest mancante o malformato produce `ExtensionError`, perché non può
dichiarare di essere opzionale;
- un manifest valido con `optional: false` propaga gli errori di caricamento;
- un manifest valido con `optional: true` converte un errore di modulo,
  entrypoint, versione o compatibilità in un `OptionalExtensionResult` con
  `loaded: None` e una `ExtensionDiagnostic` non bloccante;
- un’estensione caricata correttamente produce `loaded` e nessuna diagnostica.

Il fallback non nasconde gli errori: li conserva nella diagnostica con
`phase: loading` e con l'identificativo dell'estensione.

## Compatibilità

La funzionalità non modifica l'ordine delle estensioni, i manifest obbligatori,
`target`, `module`, `entrypoint`, la compatibilità framework o la validazione
SemVer. Il fallback è opt-in e non modifica il normale percorso di build.
