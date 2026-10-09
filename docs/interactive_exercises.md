# Esercizi interattivi in HTML

Questa pagina raccoglie le guide per creare esercizi interattivi nei contenuti EduTeX. Scegli il tipo in base all’attività che vuoi far svolgere; ogni guida descrive i campi supportati, il formato delle risposte e il comportamento della verifica HTML.

## Scegli il tipo di esercizio

| Attività | Tipo | Guida |
| --- | --- | --- |
| Selezionare una o più opzioni da un elenco | `choice` | [Scelta multipla](choice_exercise.md) |
| Scrivere una risposta breve in un campo di testo | `short_answer` | [Risposta breve](short_answer_exercise.md) |
| Tradurre un testo e verificare la traduzione | `translation` | [Traduzione](translation_exercise.md) |
| Completare gli spazi scegliendo parole da un elenco | `cloze` (`fill`, `fill-in`) | [Cloze](cloze_exercise.md) |
| Abbinare parole ed elementi corrispondenti | `matching` | [Abbinamento](matching_exercise.md) |
| Comporre una frase cliccando parole disponibili | `builder` (`sentence-builder`) | [Costruzione della frase](sentence_builder_exercise.md) |
| Valutare affermazioni come vere o false | `true_false` | [Vero o falso](true_false_exercise.md) |

## Indicazioni rapide

- Usa `choice` quando vuoi che la persona scelga tra risposte già mostrate; specifica se è consentita una sola scelta o più scelte.
- Usa `short_answer` per una risposta breve digitata liberamente, per esempio una forma verbale o parole mancanti.
- Usa `translation` quando la consegna richiede di tradurre un testo e vuoi definire le formulazioni accettate.
- Usa `cloze` quando la frase contiene spazi da completare con parole disponibili.
- Usa `matching` per associare due liste, come vocaboli e significati.
- Usa `builder` quando l’obiettivo è ordinare parole o segmenti per comporre una frase.
- Usa `true_false` quando ogni elemento richiede una valutazione binaria.

## Prima di pubblicare

1. Segui la guida specifica del tipo scelto: i campi che definiscono le risposte corrette non sono uguali per tutti gli esercizi.
2. Definisci esplicitamente la risposta attesa o le coppie corrette quando il tipo lo richiede; non presumere che il contenuto del blocco `solution` venga usato automaticamente per la verifica.
3. Verifica che consegna, numero di risposte e ordine siano chiari per chi svolge l’esercizio.
4. Costruisci il corso in HTML e prova l’esercizio nel browser, inclusi i pulsanti di verifica e reset.

## Riferimenti generali

- [Specifiche degli shortcode](SHORTCODE_SPEC.md)
- [Specifiche del Knowledge Model](KNOWLEDGE_MODEL_SPEC.md)
