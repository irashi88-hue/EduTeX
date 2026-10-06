# Contratto della build multi-formato

Stato: candidato per V1.4
Versione di riferimento: 1.4.0

## Scopo

Il contratto definisce una primitiva **opt-in** per pianificare e produrre piu formati
HTML, LaTeX e PDF nella stessa sessione. Il percorso di build singolo esistente non
viene modificato.

## Regole

- i formati supportati sono `html`, `latex` e `pdf`;
- la selezione e normalizzata in minuscolo e rifiuta formati vuoti, sconosciuti o duplicati;
- l'ordine dichiarato e preservato sia nel piano sia nell'esecuzione;
- ogni formato riceve lo stesso nome base e il suffisso deterministico `.html`, `.tex` o `.pdf`;
- ogni formato viene invocato una sola volta;
- il piano non usa timestamp o metadati del filesystem;
- un errore del builder interrompe la sessione senza mascherare l'errore;
- il comportamento e deterministico a parita di piano e builder;
- la funzionalita resta opt-in e non cambia il build singolo.

## API pubblica

`MultiFormatBuildPlan.create(formats, output_dir, output_file)` costruisce un piano
immutabile. `execute_multi_format(plan, build_one)` invoca `build_one(format, path)`
sequenzialmente e restituisce le destinazioni nello stesso ordine.

## Compatibilita

Il contratto non introduce una nuova opzione CLI e non cambia la configurazione\nesistente: costituisce una base isolata per il successivo collegamento ai renderer.
