# Contratto di ottimizzazione build per documenti grandi

Stato: candidato per V1.4
Versione di riferimento: 1.4.0

## Scopo

Ridurre il lavoro e le allocazioni temporanee per documenti grandi durante
l'ordinamento degli elementi e dei blocchi di prosa, senza cambiare il documento
prodotto o le regole di ordinamento.

## Contratto

- i renderer HTML e LaTeX usano `iter_positioned_items` per unire i flussi;
- quando entrambi i flussi sono gia ordinati, `heapq.merge` produce l'ordine in O(n)
  senza materializzare un secondo elenco combinato;
- gli input non ordinati usano un fallback stabile equivalente all'ordinamento storico;
- a parita di posizione, gli elementi precedono i blocchi di prosa come prima;
- il helper e lazy: restituisce gli elementi uno alla volta nel fast path;
- l'ottimizzazione non dipende da formato, timestamp o dimensione minima configurata;
- la semantica, il contenuto e l'ordine finale restano invariati e deterministici;
- il risultato deterministico a parita di input conserva il medesimo contenuto;
- la build normale non richiede flag e nessuna opzione pubblica cambia.

## Complessita

Per input gia ordinati, la fusione e lineare O(n) con memoria ausiliaria O(1)
rispetto al numero di elementi (due flussi). Il fallback mantiene l'ordinamento
stabile precedente per sequenze non ordinate.

## Limiti

Questa tranche ottimizza solo la fusione e l'ordinamento delle sorgenti di contenuto.
Non dichiara una riduzione della memoria totale del documento, che resta influenzata
dalle stringhe renderizzate e dai template completi.
