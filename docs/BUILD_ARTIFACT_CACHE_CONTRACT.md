# Contratto della cache degli artefatti di build

Stato: candidato per V1.4
Versione di riferimento: 1.4.0

## Scopo

`ArtifactCache` e una API **opt-in** che memorizza artefatti completati usando la fingerprint
stabile della build incrementale come chiave. Non attiva la cache da sola e non modifica il
percorso di build esistente.

## Contratto

- una fingerprint e una stringa SHA-256 esadecimale minuscola di 64 caratteri;
- ogni fingerprint identifica al massimo un contenuto: riutilizzarla per byte diversi e un errore;
- i byte dell'artefatto sono copiati in streaming, senza caricare il file intero in memoria;
- i dati e i metadati sono scritti tramite file temporanei e `os.replace` atomica;
- il manifest registra schema, versione, fingerprint, SHA-256 (`sha256`) dell'artefatto e dimensione;
- il ripristino verifica hash e dimensione prima di sostituire la destinazione;
- un cache miss non crea o modifica il file destinazione;
- cache incompleta, corrotta o incompatibile genera `ArtifactCacheError` in modo deterministico;
- i manifest non contengono timestamp o percorsi assoluti della sorgente;
- il comportamento e opt-in, deterministico e indipendente dal formato HTML, LaTeX o PDF.

## API

`store(fingerprint, artifact_path)` salva un artefatto completato e restituisce
`ArtifactCacheResult`. `restore(fingerprint, destination)` restituisce `hit=False` se la
fingerprint non e presente; in caso di hit verifica l'integrita e ripristina il file in modo
atomico. La fingerprint puo essere prodotta da `compute_build_fingerprint`.

## Limiti espliciti

Questa tranche non impone politiche di eviction, limiti di spazio, pulizia automatica o
integrazione obbligatoria nel `BuildService`. Il chiamante abilita la cache passando
esplicitamente la fingerprint e la directory di cache.
