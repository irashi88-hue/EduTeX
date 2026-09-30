# Scelta multipla in HTML

EduTeX supporta esercizi interattivi di scelta multipla nel renderer HTML.
Il parser esistente conserva il corpo dell'esercizio; non sono necessarie nuove
estensioni o modifiche alla sintassi generale degli shortcode.

## Scelta singola

```markdown
::: exercise
title: Scegli il saluto corretto
type: choice
question: Quale formula significa “buongiorno, al mattino”?
options:
- Hallo
- Guten Morgen
- Tschüss
answer: Guten Morgen
:::
```

Il renderer produce radio button, un feedback immediato e uno stato leggibile
con tecnologie assistive.

## Scelta multipla

Per richiedere più risposte corrette, impostare `multiple: true` e separare le
risposte con `|`:

```markdown
::: exercise
title: Riconosci i saluti informali
type: choice
multiple: true
question: Seleziona tutti i saluti o congedi informali.
options:
- Hallo
- Guten Morgen
- Tschüss
answer: Hallo | Tschüss
:::
```

Il confronto è indipendente dall'ordine delle selezioni e normalizza spazi e
maiuscole/minuscole. Le risposte non configurate non vengono considerate
corrette.

## Comportamento e accessibilità

- `radio` per scelta singola, `checkbox` per scelta multipla;
- ogni controllo ha `id`, `name`, `value` e label associata;
- il feedback usa `role="status"` e `aria-live="polite"`;
- la logica JavaScript è inline, senza dipendenze esterne;
- LaTeX e gli esercizi non interattivi restano invariati.

## Contratto HTML stabile

Ogni esercizio viene emesso in un wrapper `.choice-exercise` con:

- attributo `data-choice-exercise`;
- `data-answer` contenente un array JSON di risposte normalizzate dal confronto;
- input con `id`, `name`, `value` e label associata;
- feedback `.choice-result` con `role="status"` e `aria-live="polite"`;
- pulsanti per la verifica e il reset.

La classe CSS `.solution-inline`, quando presente, è un collegamento reale
all’appendice delle soluzioni e non deve essere verificata cercando soltanto
una sottostringa nell’intero documento HTML.
