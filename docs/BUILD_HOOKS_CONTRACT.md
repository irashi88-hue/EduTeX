# Contratto degli hook di build

Stato: candidato per V1.4
Versione di riferimento: 1.4.0

## Scopo

Gli hook `pre-build` e `post-build` sono un'estensione **opt-in** del lifecycle
esposto dal `BuildService`. Senza un registry passato esplicitamente, il build
normale percorre il percorso esistente senza hook.

## Regole

- le sole fasi supportate sono `pre-build` e `post-build`;
- l'ordine di registrazione determina l'ordine di esecuzione per ciascuna fase;
- ogni `hook_id` deve essere unico e il registry usato da un build viene congelato;
- il contesto e immutabile e i metadati vengono copiati e resi read-only;
- gli hook pre-build ricevono il percorso di output previsto; quelli post-build il percorso prodotto;
- gli errori non vengono nascosti: `BuildHookError` identifica hook, fase e causa;
- il primo errore interrompe gli hook successivi; un errore post-build non cancella l'artefatto gia prodotto;
- la funzionalita non e attiva se non viene fornito un registry esplicito;
- ordine ed esiti sono deterministici e non dipendono da timestamp o stato globale; la semantica del piano e deterministica a parita di input.
- Il piano e deterministico: input identici producono la stessa sequenza di callback e gli stessi percorsi di output.

## API

`BuildHookRegistry` registra callback `BuildHook` e `BuildService.build(..., hooks=registry)`
li invoca prima e dopo la build. `BuildHookContext` espone root, formato, output e metadati.
`run_build_hooks` consente di eseguire una sequenza isolata nello stesso ordine.

## Compatibilita

La nuova opzione API e opzionale; le chiamate esistenti a `BuildService.build` restano
valide e seguono lo stesso percorso senza hook. Non viene aggiunta un'opzione CLI in questa tranche.
