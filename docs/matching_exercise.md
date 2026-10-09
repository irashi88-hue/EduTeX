# Esercizio di abbinamento interattivo in HTML

`type: matching` crea righe in cui associare ciascuna parola al suo significato. La guida descrive il comportamento del renderer HTML.

## Esempio

```markdown
::: exercise
title: Abbina i saluti al significato
type: matching
words:
- Hallo
- Guten Morgen
- Tschüss
meanings:
- ciao
- buongiorno (al mattino)
- arrivederci

::: solution
Hallo — ciao
Guten Morgen — buongiorno (al mattino)
Tschüss — arrivederci
:::
:::
```

Le coppie corrette sono definite **dall’ordine**: la prima parola corrisponde al primo significato, la seconda al secondo e così via. I significati vengono mescolati tra le opzioni mostrate, così chi svolge l’esercizio deve selezionare l’abbinamento.

## Campi supportati

- `type: matching` attiva l’esercizio.
- `words:` contiene la lista delle parole o degli elementi della colonna sinistra.
- `meanings:` contiene i significati o gli elementi della colonna destra, nello stesso ordine delle parole.
- Le due liste possono essere scritte come elenchi Markdown oppure, per liste brevi, come valori separati da `|` sulla riga del campo.

Usa lo stesso numero di voci in entrambe le liste e allinea con attenzione ogni coppia per posizione. Il renderer crea le righe fino alla lunghezza della lista più corta: le voci di `words:` oltre quel limite non diventano righe. Se non c’è almeno una coppia, l’esercizio interattivo non viene creato.

## Interazione e verifica

Ogni riga presenta una parola e un menu per scegliere il significato. Le opzioni dei menu vengono mescolate all’apertura della pagina; l’ordine di `words:` resta quello scritto nel file. Uno stesso significato non può essere assegnato a più righe. I pulsanti permettono di verificare le selezioni e azzerare l’esercizio; il feedback segnala le righe vuote, errate e corrette.

## Limiti e consigli

- La posizione definisce la soluzione: non riordinare `meanings:` rispetto a `words:`.
- Evita significati duplicati: il controllo impedisce di selezionare lo stesso valore più di una volta nel gruppo.
- Il blocco `solution`, se presente, può mostrare le coppie nell’appendice, ma non determina gli abbinamenti usati dal controllo.
- La verifica interattiva descritta qui è specifica dell’output HTML.
