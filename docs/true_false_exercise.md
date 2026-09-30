# Esercizi Vero/Falso

EduTeX supporta esercizi interattivi `true_false` nel renderer HTML.

## Sintassi

```markdown
::: exercise
title: Verifica le affermazioni
type: true_false
statement: Berlino è la capitale della Germania.
answer: vero
statement: "Guten Morgen" significa "buonanotte".
answer: falso
statement: "Hallo" è un saluto informale.
answer: true
:::
```

## Contratto

- Più coppie `statement:` + `answer:` possono stare nello stesso blocco.
- Le coppie restano nello stesso ordine nell'HTML.
- `answer: true` e `answer: vero` producono Vero.
- `answer: false` e `answer: falso` producono Falso.
- Il controllo usa radio button semanticamente associati a label.
- La selezione non rivela la correttezza prima della verifica.
- Il pulsante di verifica mostra il conteggio `corrette / totali`.
- Il pulsante di reset cancella selezioni, stati e risultato.
- Coppie incomplete, fuori ordine o con valori non riconosciuti producono una diagnostica neutra.
- Il renderer mantiene `aria-labelledby`, `aria-live`, focus visibile e supporto tastiera.

La generazione resta affidata esclusivamente a:

```powershell
python -m edutex build --project . --config .\edutex.config.yaml
```

Dark mode, indice e layout generale non fanno parte di questa patch.
