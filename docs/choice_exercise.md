# Scelta multipla in HTML

EduTeX supporta esercizi interattivi di scelta multipla nel renderer HTML.
Il parser esistente conserva il corpo dell'esercizio; non sono necessarie nuove
estensioni o modifiche alla sintassi generale degli shortcode.

Per gli esercizi a risposta breve (`type: short_answer`), consulta la guida
[Risposta breve interattiva](short_answer_exercise.md).

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

Il confronto non dipende dall'ordine delle selezioni e normalizza spazi e
maiuscole/minuscole. Per la scelta singola va indicata una sola risposta; per
la scelta multipla, tutte le risposte attese vanno separate con `|`. `answer:`
è obbligatorio e ogni risposta deve corrispondere a un'opzione. Il build HTML
si interrompe con un errore chiaro se la risposta manca, non corrisponde a
un'opzione o viola il tipo di scelta dichiarato.

## Comportamento e accessibilità

- `radio` per scelta singola, `checkbox` per scelta multipla;
- ogni controllo ha `id`, `name`, `value` e label associata;
- il feedback usa `role="status"` e `aria-live="polite"`;
- la logica JavaScript è inline, senza dipendenze esterne;
- LaTeX e gli esercizi non interattivi restano invariati.

## Contratto HTML stabile

Ogni esercizio viene emesso in un wrapper `.choice-exercise` con:

- attributo `data-choice-exercise`;
- `data-answer` contenente un array JSON delle risposte attese; il confronto
  normalizza spazi e maiuscole/minuscole;
- input con `id`, `name`, `value` e label associata;
- feedback `.choice-result` con `role="status"` e `aria-live="polite"`;
- pulsanti per la verifica e il reset.

La classe CSS `.solution-inline`, quando presente, è un collegamento reale
all’appendice delle soluzioni e non deve essere verificata cercando soltanto
una sottostringa nell’intero documento HTML.
