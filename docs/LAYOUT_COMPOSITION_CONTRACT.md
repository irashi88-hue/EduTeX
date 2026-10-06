# Contratto di composizione dei layout

Stato: candidato per V1.5
Versione di riferimento: 1.5.0

## Scopo

Consentire a un layout di riusare e sovrapporre regole definite da altri layout,
senza cambiare il comportamento degli asset esistenti che non dichiarano `extends`.

## Riferimenti `extends`

- `extends` e' opzionale e accetta un percorso relativo oppure una lista ordinata di percorsi relativi;
- i percorsi sono risolti rispetto al file `layout.yaml` che li dichiara;
- un riferimento a una directory individua il relativo `layout.yaml`;
- i genitori sono applicati nell'ordine dichiarato e il layout attivo viene applicato per ultimo;
- percorsi assoluti, file mancanti, riferimenti duplicati, ciclo di composizione e percorsi fuori da `project_root` sono errori fatali di Layout.

## Regole di composizione

- le mappe vengono unite ricorsivamente;
- per valori scalari o di tipo diverso si applica la precedenza dell'ultimo layer che dichiara il campo;
- le liste sono sostituite interamente, non concatenate: `section_order` conserva cosi' un ordine esplicito;
- `id`, `name` e `version` identificano il layout attivo e non vengono ereditati dai genitori;
- il compositore non modifica gli input e produce lo stesso risultato a parita' di file e ordine.

## Compatibilita' e confini

Un layout senza `extends` mantiene i valori predefiniti e il comportamento precedenti. La composizione avviene prima della conversione in `LayoutModel`; Layout continua a consumare gli asset in sola lettura e non modifica contenuto didattico o stile.
