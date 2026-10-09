# Esercizio di traduzione interattivo in HTML

`type: translation` crea un esercizio in cui chi studia traduce una frase in un campo di testo e può verificare la risposta nel browser. La guida descrive il comportamento del renderer HTML.

## Esempio essenziale

```markdown
::: exercise
title: Traduci la frase
type: translation
source: Mi chiamo Luca.
answer: Ich heiße Luca. | Ich heisse Luca.

::: solution
Ich heiße Luca.
:::
:::
```

`source:` contiene il testo da tradurre. `answer:` definisce le risposte accettate; per più varianti, separale con `|`. Nell’esempio sono accettate sia la grafia con `ß` sia quella con `ss`.

## Campi supportati

- `type: translation` attiva l’esercizio.
- `source:` contiene il testo da tradurre; `prompt:` è accettato come alias.
- `answer:` definisce una o più risposte corrette; `expected:` è accettato come alias.
- Per indicare più risposte equivalenti, separale con `|`.
- Se mancano sia `answer:` sia `expected:`, il renderer usa la prima riga non vuota del blocco `solution`, se presente.

È consigliato indicare sempre le risposte con `answer:` o `expected:`: il fallback alla soluzione usa una sola riga e non può dedurre eventuali varianti equivalenti.

Le righe non vuote dopo `source:` o `prompt:` e prima di `answer:` o `expected:` vengono aggiunte al testo sorgente. Per esercizi semplici, è preferibile mantenere il testo sorgente su una singola riga.

## Controllo della risposta

Il renderer mostra il testo da tradurre, un campo di risposta multilinea e i pulsanti per verificare o azzerare la risposta. Il controllo ignora le differenze tra maiuscole e minuscole, normalizza gli spazi ripetuti e rimuove la punteggiatura terminale (`.`, `!`, `?`, `…`). Le varianti elencate in `answer:` sono controllate con la stessa normalizzazione.

Non vengono generate automaticamente varianti linguistiche o sinonimi: ogni formulazione che vuoi accettare va elencata esplicitamente, separata da `|`.

## Indicazioni per chi scrive i contenuti

- Scrivi in `source:` soltanto il testo da tradurre; aggiungi eventuali istruzioni nel corpo dell’esercizio, prima del campo sorgente.
- Inserisci tutte le formulazioni corrette che vuoi accettare in `answer:`.
- Usa `solution` per mostrare una soluzione nell’appendice; non affidarti al fallback se esistono più risposte valide.
- La verifica interattiva descritta qui è specifica dell’output HTML.
