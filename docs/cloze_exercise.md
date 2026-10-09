# Esercizio cloze interattivo in HTML

`type: cloze` crea un esercizio di completamento in cui si cliccano parole disponibili per riempire gli spazi di una frase. La guida descrive il comportamento del renderer HTML.

## Esempio

```markdown
::: exercise
title: Completa la frase
type: cloze
sentence: Ich ______ Luca. Anna ______ Maria.
answers:
- heiße
- heißt
- heißen

::: solution
Ich heiße Luca. Anna heißt Maria.
:::
:::
```

Ogni gruppo di almeno due underscore (`__`) in `sentence:` crea uno spazio vuoto. Le prime due voci di `answers:` corrispondono, nell’ordine, ai due spazi; `heißen` è una parola-esca disponibile ma non è la risposta attesa per nessuno dei due.

## Campi e varianti supportati

- `type: cloze` attiva l’esercizio. Sono riconosciuti anche gli alias `type: fill` e `type: fill-in`.
- `sentence:` contiene la frase e i suoi spazi vuoti, rappresentati da sequenze di almeno due underscore.
- `answers:` contiene le parole disponibili. È possibile usare un elenco con trattini oppure valori sulla stessa riga separati da `|`.
- Le risposte sono associate agli spazi in ordine: la prima voce è la soluzione del primo spazio, la seconda quella del secondo e così via.
- Le voci successive al numero di spazi diventano parole-esca, senza uno spazio associato.

Ogni spazio richiede una risposta corrispondente in `answers:`. Se la frase non contiene spazi, o l’elenco è più corto, il renderer non può costruire l’esercizio interattivo. Includi sempre `sentence:` e almeno una risposta per ogni spazio.

## Interazione e verifica

Le parole dell’elenco diventano pulsanti selezionabili. Quando si clicca una parola, viene inserita nel primo spazio ancora vuoto; la stessa voce non può essere usata una seconda volta finché non viene rimossa. Cliccando uno spazio già compilato, la parola torna tra quelle disponibili. I pulsanti permettono di verificare le risposte e azzerare l’esercizio.

Il controllo ignora maiuscole/minuscole e normalizza spazi iniziali, finali o ripetuti. La punteggiatura non viene rimossa: inserisci in `answers:` soltanto la parola o la forma attesa, senza punteggiatura aggiunta.

## Limiti importanti

- Il numero e l’ordine delle risposte in `answers:` determinano le soluzioni: non riordinare l’elenco rispetto agli spazi nella frase.
- Le voci aggiuntive sono distrattori, non risposte alternative per uno spazio.
- Non è supportata una sintassi per più varianti corrette dello stesso spazio. Se un esercizio deve accettare alternative, scegli un tipo di esercizio che le supporti.
- Il blocco `solution`, se presente, può mostrare la soluzione nell’appendice, ma non definisce le risposte usate dal controllo cloze: quelle devono essere in `answers:`.
- La verifica interattiva descritta qui è specifica dell’output HTML.
