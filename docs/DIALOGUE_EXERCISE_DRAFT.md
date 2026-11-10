# Esercizio dialogico testuale (dialogue) - bozza

Stato: bozza non normativa. Non modifica il comportamento degli esercizi esistenti.
Fase 1: solo testo. Audio e voce sono rimandati alla fase successiva.
Versione 3: liste nel formato del tipo choice.

## 1. Obiettivo

Permettere a una lezione HTML di proporre un breve dialogo guidato su un tema limitato. Un modello linguistico locale (Ollama) interpreta il ruolo di insegnante, corregge gli errori e fornisce un verdetto indicativo.

## 2. Ambito

Incluso:
- nuovo tipo di esercizio dialogue nel Knowledge Model;
- link facoltativo all'agente Langdock;
- prompt di sistema generato in modo deterministico;
- verdetto testuale con parser;
- fallback stampabile quando il link all'agente non è configurato;
- test previsti.

Escluso:
- audio, sintesi e riconoscimento vocale;
- registrazione delle voci;
- servizi remoti o account;
- salvataggio automatico dei dialoghi.

## 3. Sintassi nel Knowledge Model

Il blocco usa il formato degli esercizi esistenti: contenitore exercise, righe chiave: valore nel corpo, tipo dichiarato con type. Le liste seguono il formato del tipo choice: una chiave senza valore, seguita da righe che iniziano con un trattino.

Esempio:

::: exercise
type: dialogue
title: Dialogo al ristorante
level: A1
language: de
topic: Essen im Restaurant
role: Kellner
goal: Ordinare un pasto completo
max_turns: 8
min_criteria: 3
vocabulary:
- Speisekarte
- bestellen
- Wasser
structures:
- Ich möchte ...
- Ich nehme ...
criteria:
- Saluta e chiede un tavolo
- Ordina almeno un piatto con "Ich möchte" o "Ich nehme"
- Chiede il conto
:::

Regole:
- Chiavi obbligatorie: type, level, language, topic, role, goal, criteria (almeno due voci).
- Chiavi facoltative: title, vocabulary, structures, max_turns, min_criteria.
- Chiavi di lista: vocabulary, structures, criteria. Ogni voce e una riga che inizia con un trattino.
- type deve valere esattamente dialogue, con lo stesso confronto usato per type: choice.
- level ammette A1, A2, B1, B2, C1, C2.
- max_turns e un intero tra 1 e 20, con default 8.
- min_criteria e facoltativo; se assente vale il numero di criteri.
- Nel corpo sono ammesse solo chiavi note, voci di lista e righe vuote. Il testo libero e rifiutato.
- Il blocco non contiene soluzioni annidate in questa fase.
- Il corpo non dichiara un id: l'identificativo e generato dal renderer, come per gli altri esercizi.

## 4. Configurazione

Il collegamento all'agente va nella sezione `dialogue` di `edutex.config.yaml`:

~~~yaml
dialogue:
  langdock_url: https://app.langdock.com/chat?a=ID-DELL-AGENTE
~~~

- `langdock_url` è facoltativo e deve iniziare con `https://`.
- Senza `langdock_url` la pagina mostra solo la traccia per il madrelingua.
- Il valore è personale: non va committato nel repo.
- I campi `enabled`, `endpoint`, `model` e `timeout_seconds` riguardano l'integrazione con Ollama, rinviata (sezione 9).

## 5. Comportamento nella pagina HTML

Ogni esercizio `dialogue` mostra due percorsi:

- **Agente (percorso standard).** Il pulsante "Apri l'agente e copia l'esercizio" copia nel dispositivo il testo dell'esercizio e apre l'agente in una nuova scheda. Se gli appunti non sono disponibili, compare un'area di testo da copiare a mano. Se il browser blocca la scheda, compare il link diretto.
- **Madrelingua (alternativa).** La sezione "Alternativa: parla con un madrelingua" riporta ruolo, obiettivo, tema e criteri, con checkbox per l'autovalutazione. Il verdetto in questo caso lo dà il madrelingua o l'insegnante.

Regole di comportamento:

- La pagina non effettua chiamate di rete: il link all'agente è solo un collegamento.
- Il testo dell'esercizio viene escapato: nessun contenuto dell'autore è interpretato come HTML.
- Le conversazioni avvengono in Langdock, non nella pagina. Non c'è trascrizione automatica.

## 6. Istruzioni dell'agente

Le istruzioni generali dell'agente si incollano una sola volta nella configurazione dell'agente in Langdock:

~~~text
Sei un insegnante di lingue che svolge esercizi di dialogo guidato.

Quando ricevi un messaggio che inizia con "ESERCIZIO DIALOGO", leggi le istruzioni che seguono e applicale per tutta la conversazione: lingua, ruolo, obiettivo, lessico, strutture, numero massimo di turni e criteri di valutazione.

Se ricevi un messaggio senza il blocco "ESERCIZIO DIALOGO", chiedi allo studente di incollare il testo dell'esercizio dalla pagina del corso.

Dai il verdetto solo quando lo studente scrive VALUTA, oppure quando il dialogo si è concluso naturalmente con il saluto finale. Non dare mai il verdetto a metà dialogo. Quando lo fai, usa il formato indicato nelle istruzioni, come ultime tre righe. Rispondi sempre nella lingua indicata nell'esercizio.
~~~

## 7. Testo copiato e prompt

Il testo copiato è composto da:

- la riga `[ESERCIZIO DIALOGO: titolo]`;
- il prompt generato da `build_system_prompt` a partire dai campi dell'esercizio;
- la regola di chiusura;
- la frase di avvio nella lingua dell'esercizio.

Il prompt segue un template fisso, quindi gli stessi campi producono sempre lo stesso testo. La regola di chiusura impone questi comportamenti:

- non dare il verdetto a metà dialogo;
- dare il verdetto solo su richiesta con VALUTA, oppure a fine dialogo;
- usare come ultime tre righe il formato `VERDETTO:`, `CRITERI:` e una motivazione breve.

Il limite di turni è una regola per l'agente. La pagina non lo conta e non lo verifica.

## 8. Verdetto

Il verdetto è prodotto dall'agente e mostrato nella chat. La pagina non lo legge. Il parser `parse_verdict` resta disponibile per usi futuri.

Il verdetto è indicativo e non sostituisce la valutazione dell'insegnante.

## 9. Percorsi non standard (rinviati)

L'integrazione con Ollama, attivabile con `enabled: true`, mostra un pannello che chiama un endpoint locale. Non è il percorso standard ed è rinviata per questioni di prestazioni: la GPU AMD RX 5700 non viene usata in modo affidabile da Ollama su Windows. Il codice resta nel repo, ma non è documentato come supportato.

## 10. Errori e fallback

- Link non `https://`: la pagina mostra un errore visibile e non crea il pulsante.
- Esercizio non valido: la pagina mostra l'elenco degli errori di parsing.
- Lint: il tipo `dialogue` è riconosciuto e la regola sulla soluzione annidata non si applica. Il lint non verifica ancora i campi obbligatori: gli errori compaiono nella pagina.

## 11. Sicurezza e privacy

- Nessuna chiave API nella pagina e nel repo.
- Il link all'agente è personale e non va committato.
- Le conversazioni passano dai server di Langdock. Se gli studenti sono minorenni o i dati sono di un istituto, verificare con il responsabile privacy prima dell'uso.

## 12. Test

I test di riferimento sono:

- `tests/unit/test_dialogue_contract.py`: parsing;
- `tests/unit/test_dialogue_config_contract.py`: configurazione;
- `tests/unit/test_dialogue_render_contract.py`: rendering con Ollama, rinviato ma ancora verde;
- `tests/unit/test_dialogue_handoff_contract.py`: percorso agente e madrelingua, sicurezza del link, testo copiato e regola di chiusura.

## 13. Domande aperte

- Il lint dovrebbe validare i campi obbligatori del dialogo?
- Serve un contatore dei turni verificabile, oppure la regola per l'agente è sufficiente?
- Quando si introdurrà la voce, il percorso con l'agente resterà lo standard?