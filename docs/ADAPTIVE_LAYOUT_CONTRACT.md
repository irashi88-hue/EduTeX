# Contratto di layout adattivo

Stato: candidato per V1.5
Versione di riferimento: 1.5.0

## Scopo

Adeguare spaziatura e interruzioni di pagina alla quantità e alla posizione dei
contenuti, senza cambiare il comportamento dei layout esistenti per impostazione
predefinita.

## Attivazione e schema

L'adattamento e' opt-in tramite `adaptive.enabled: true`. Se la sezione manca o e'
disabilitata, il layout conserva il comportamento corrente.

```yaml
adaptive:
  enabled: true
  rules:
    - node_type: exercise
      min_count: 6
      page_break_every: 4
      spacing_before_mm: 10
```

- `node_type` identifica un tipo concreto; ogni tipo puo' avere una sola regola;
- `min_count` e' il numero minimo totale di elementi di quel tipo per attivare la regola;
- `page_break_every` inserisce un'interruzione prima di ogni occorrenza multipla dell'intervallo, mai prima della prima;
- `spacing_before_mm` e `spacing_after_mm`, se presenti, si applicano agli elementi del tipo corrispondente quando la soglia e' raggiunta.

## Precedenza

I valori espliciti in `placement.<node_type>` prevalgono, anche quando sono `false` o `0`.
La regola adattiva modifica solo i campi non specificati per quel tipo. `_default`
resta un fallback; una regola adattiva specifica puo' specializzarlo per il proprio tipo.

## Validazione e determinismo

- i valori di soglia sono interi positivi; `page_break_every` e' almeno 2;
- le spaziature sono numeri finiti non negativi;
- campi sconosciuti, regole duplicate e regole senza effetti sono errori di layout;
- conteggio e occorrenza seguono l'ordine sorgente del contenuto;
- l'adattamento e' risolto durante Layout Processing, prima del rendering;
- il contenuto e il modello di Theme non vengono modificati.
