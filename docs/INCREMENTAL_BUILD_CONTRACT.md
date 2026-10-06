# Contratto della build incrementale

Stato: candidato per V1.4
Versione di riferimento: 1.4.0

## Ambito

La build incrementale usa primitive esplicite e deterministiche per decidere
se un artefatto esistente può essere riutilizzato. Il comportamento è opt-in e
non modifica il percorso di build normale.

## Fingerprint

`compute_build_fingerprint` combina:

- i percorsi assoluti degli input in ordine stabile;
- il contenuto byte per byte dei file esistenti;
- l'indicazione degli input mancanti;
- la stringa di configurazione risolta.

Il fingerprint usa SHA-256. Non usa timestamp o metadata del filesystem, quindi
la stessa sorgente produce lo stesso valore a parità di percorso e
configurazione.

## Cache state

Lo stato contiene esattamente:

```json
{
  "cache_version": "1.0.0",
  "fingerprint": "...",
  "output_path": "..."
}
```

`is_incremental_hit` restituisce `true` solo quando cache version, fingerprint,
percorso dell'output e presenza dell'artefatto coincidono. Cache assente o
invalida non viene considerata un hit.

`write_incremental_state` scrive in modo atomico tramite file temporaneo e
replace, evitando cache parziali.

## Compatibilità

- il normale comando di build resta invariato;
- un cache hit non può riutilizzare un output mancante;
- la modifica di un input o della configurazione invalida il fingerprint;
- lo stato JSON non contiene testo umano o campi variabili;
- una cache corrotta produce un errore esplicito, non un falso hit.
