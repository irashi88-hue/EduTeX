# Risposta breve interattiva in HTML

`type: short_answer` rende un campo di testo verificabile nel browser. Il
renderer mostra sempre un'istruzione generale per inserire e verificare la
risposta e i pulsanti per i caratteri speciali tedeschi `ä ö ü Ä Ö Ü ß`.

## Esempio

```markdown
::: exercise
title: Completa il dialogo
type: short_answer
prompt: Completa il dialogo: — Wie ______ du? — Ich ______ Maria.
response_hint: Scrivi soltanto le due forme mancanti, nell'ordine in cui compaiono, separate da uno spazio (formato: parola1 parola2).
answer: heißt heiße

::: solution
— Wie heißt du?
— Ich heiße Maria.
:::
:::
```

Nel campo di risposta si inseriscono soltanto le due forme, nell'ordine indicato;
non occorre riscrivere il dialogo.

## Campi supportati

- `type: short_answer` attiva il controllo interattivo.
- `prompt:` contiene la domanda o la consegna; è accettato anche `question:`.
- `response_hint:` è facoltativo. Aggiunge un'indicazione specifica sul formato,
  per esempio ordine delle parole, numero di elementi o separatori. Non sostituisce
  la consegna e non dovrebbe rivelare la soluzione.
- `answer:` definisce la risposta attesa; è accettato anche `expected:`.
- Per accettare più risposte equivalenti, separarle con `|`, per esempio
  `answer: Guten Morgen | guten morgen`.

È consigliato dichiarare sempre `answer:` (o `expected:`). Per compatibilità con
contenuti esistenti, se entrambi mancano il renderer usa la prima riga non vuota
del blocco `solution`, quando presente.

## Verifica e accessibilità

Il controllo ignora differenze tra maiuscole e minuscole, normalizza gli spazi e
ignora la punteggiatura terminale. I caratteri speciali sono pulsanti accessibili
associati al campo di risposta; la verifica usa un pulsante dedicato e annuncia
l'esito tramite un'area di stato accessibile.
