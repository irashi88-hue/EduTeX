# Esercizio di costruzione della frase in HTML

`type: builder` crea un’attività in cui si compone una frase cliccando parole disponibili. La guida descrive il comportamento del renderer HTML.

## Esempio

```markdown
::: exercise
title: Costruisci la frase
type: builder
tokens:
- Ich
- heiße
- Luca.
- bin
answer: Ich heiße Luca.

::: solution
Ich heiße Luca.
:::
:::
```

`tokens:` contiene i pezzi che si possono selezionare. `answer:` definisce la frase completa attesa. Nell’esempio `bin` è una parola-esca che non va selezionata.

## Campi e alias supportati

- `type: builder` attiva l’esercizio; è accettato anche `type: sentence-builder`.
- `tokens:` contiene le parole o i segmenti disponibili. Puoi scriverli come elenco Markdown oppure, per esempi brevi, separarli con `|` sulla stessa riga.
- `answer:` contiene la frase corretta, nell’ordine atteso.
- Se `answer:` manca, il renderer usa la prima riga non vuota del blocco `solution`, se presente.

È consigliato definire sempre `answer:` esplicitamente. Il fallback alla soluzione usa una sola riga; inoltre la soluzione serve anche come testo da mostrare nell’appendice, non come elenco di token.

## Interazione e verifica

I token vengono mescolati quando si apre la pagina. Cliccando un token, questo viene aggiunto alla frase nell’ordine selezionato e non può essere riutilizzato finché non lo si rimuove. Cliccando una parola già inserita la si rimuove e la si rende nuovamente disponibile. I pulsanti permettono di verificare la frase o azzerare l’esercizio.

Il controllo ignora differenze tra maiuscole e minuscole e normalizza spazi iniziali, finali o ripetuti. L’ordine delle parole e la punteggiatura fanno parte della risposta: per esempio, mantieni il punto unito all’ultima parola (`Luca.`), non come token separato (`.`).

## Consigli e limiti

- Includi in `tokens:` tutti i pezzi necessari per formare la risposta e gli eventuali distrattori.
- Se una parola deve comparire due volte nella frase, inseriscila due volte come voci distinte in `tokens:`; ogni singolo pulsante può essere usato una volta.
- I token non selezionati non rendono automaticamente errata la frase: viene confrontata la sequenza costruita con `answer:`.
- È prevista una sola frase attesa; non è documentato un formato per risposte alternative separate da `|`.
- La verifica interattiva descritta qui è specifica dell’output HTML.
