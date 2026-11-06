# Esercizio dialogico testuale (dialogue) - bozza

Stato: bozza non normativa. Non modifica il comportamento degli esercizi esistenti.
Fase 1: solo testo. Audio e voce sono rimandati alla fase successiva.
Versione 2: sintassi allineata al formato reale del Knowledge Model.

## 1. Obiettivo

Permettere a una lezione HTML di proporre un breve dialogo guidato su un tema limitato. Un modello linguistico locale (Ollama) interpreta il ruolo di insegnante, corregge gli errori e fornisce un verdetto indicativo.

## 2. Ambito

Incluso:
- nuovo tipo di esercizio dialogue nel Knowledge Model;
- configurazione facoltativa dell'endpoint;
- prompt di sistema generato in modo deterministico;
- verdetto testuale con parser;
- fallback stampabile quando il modello non e disponibile;
- test previsti.

Escluso:
- audio, sintesi e riconoscimento vocale;
- registrazione delle voci;
- servizi remoti o account;
- salvataggio automatico dei dialoghi.

## 3. Sintassi nel Knowledge Model

Il blocco usa il formato degli esercizi esistenti: contenitore exercise, righe chiave: valore nel corpo, tipo dichiarato con type. Il parser legge un solo valore per riga, quindi le liste sono separate dal simbolo barra verticale, come le risposte alternative del tipo translation.

Esempio:

::: exercise
type: dialogue
title: Dialogo al ristorante
level: A1
language: de
topic: Essen im Restaurant
role: Kellner
goal: Ordinare un pasto completo
vocabulary: Speisekarte | bestellen | Wasser
structures: Ich möchte ... | Ich nehme ...
max_turns: 8
criteria: Saluta e chiede un tavolo | Ordina almeno un piatto con "Ich möchte" o "Ich nehme" | Chiede il conto
min_criteria: 3
:::

Regole:
- Chiavi obbligatorie: type, level, language, topic, role, goal, criteria (almeno due voci).
- Chiavi facoltative: title, vocabulary, structures, max_turns, min_criteria.
- type deve valere esattamente dialogue, con lo stesso confronto usato per type: choice.
- level ammette A1, A2, B1, B2, C1, C2.
- max_turns e un intero tra 1 e 20, con default 8.
- min_criteria e facoltativo; se assente vale il numero di criteri.
- Nel corpo non sono ammesse righe di testo libero: ogni riga deve essere una chiave nota. Motivo: il parser tratta come chiave ogni riga che contiene i due punti.
- Il blocco non contiene soluzioni annidate in questa fase.
- Il corpo non dichiara un id: l'identificativo e generato dal renderer, come per gli altri esercizi.

## 4. Configurazione facoltativa

Sezione opzionale in edutex.config.yaml (formato YAML, come il resto della configurazione):

dialogue:
  enabled: false
  endpoint: http://localhost:11434
  model: nome-del-modello-installato
  timeout_seconds: 60

- Il default e enabled: false: senza configurazione la pagina mostra solo il fallback.
- Non esiste un modello predefinito: va indicato esplicitamente.
- L'unica chiamata di rete consentita e verso endpoint.

## 5. Comportamento nella pagina HTML

- Il pannello mostra tema, ruolo, obiettivo, criteri e il pulsante "Avvia".
- All'avvio il pannello invia una richiesta POST {endpoint}/api/chat con il prompt di sistema e i messaggi dello studente.
- L'output del modello e mostrato solo come testo, mai come HTML.
- Lo stato resta in memoria. Nessuna persistenza automatica.
- Al raggiungimento di max_turns, o con il pulsante "Termina e valuta", il modello produce il verdetto.
- Pulsante facoltativo "Scarica trascrizione" che salva un file di testo sul computer dello studente.
- Avviso visibile: il verdetto e indicativo e non sostituisce la valutazione dell'insegnante.

## 6. Prompt di sistema

Il prompt e generato dai campi dell'esercizio con un template fisso:

- Sei un insegnante di {language} di livello {level}. Parla solo in {language}. Spiega in italiano solo se lo studente non capisce.
- Sei {role}. Limita la conversazione all'obiettivo: {goal}, sul tema {topic}. Se lo studente esce dal tema, riportalo gentilmente.
- Usa il lessico: {vocabulary}. Incoraggia le strutture: {structures}.
- Fai una sola domanda per turno. Non superare {max_turns} turni.
- Correggi gli errori in modo breve: mostra la frase corretta e poi continua.
- Quando ti viene chiesto di valutare, controlla i criteri: {criteria}.
- Formato del verdetto, come ultime tre righe:
  - VERDETTO: SUPERATO oppure VERDETTO: NON SUPERATO
  - CRITERI: n/N
  - una breve motivazione in italiano

Il template deve produrre lo stesso testo per gli stessi campi.

## 7. Parser del verdetto

- Cerca la riga VERDETTO: nelle ultime righe della risposta.
- Se e assente o malformata, mostra "Verdetto non disponibile: serve la valutazione dell'insegnante".
- Il parser non ricalcola i criteri: mostra quanto dichiarato dal modello.

## 8. Fallback

Il fallback e attivo quando enabled e false, l'endpoint non risponde, scade il timeout o il modello non e installato.

In quel caso la pagina mostra tema, ruolo, obiettivo e criteri in forma stampabile, con una checklist di autovalutazione. Nessun errore bloccante e nessuna risorsa esterna.

## 9. Sicurezza e privacy

- Nessuna dipendenza remota nella pagina: la sola chiamata di rete e verso l'endpoint configurato.
- L'output del modello e inserito come testo semplice, senza HTML interpretato.
- Nessun dato viene inviato a terzi. Nessuna persistenza automatica.

## 10. Test previsti per l'implementazione

- Parsing: blocco valido; chiave obbligatoria mancante segnalata; riga di testo libero rifiutata; level e max_turns fuori intervallo rifiutati.
- Rendering: il pannello contiene i dati dell'esercizio; con enabled: false compare solo il fallback.
- Sicurezza: nessun URL remoto diverso dall'endpoint configurato; un input con script non viene eseguito.
- Prompt: stessi campi producono lo stesso prompt.
- Parser del verdetto: casi SUPERATO, NON SUPERATO e verdetto assente.
- Regressione: gli esercizi esistenti (choice, translation, cloze e gli altri) producono lo stesso HTML di prima.

## 11. Domande aperte

- Confermare il separatore | per le liste, oppure usare sezioni dedicate nel blocco.
- Confermare che l'id sia generato dal renderer, oppure dichiarato dall'autore per tracciare i log.
- Soglia di superamento: tutti i criteri oppure min_criteria.
- Il pannello va incluso anche nell'output a file singolo o solo nelle pagine delle lezioni?