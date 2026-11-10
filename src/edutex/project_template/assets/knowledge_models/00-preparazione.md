---
id: preparazione-agente
title: "Preparazione: crea l'agente del dialogo"
language: it
level: A1
version: 1.0.0
description: "Passo di preparazione da completare prima delle lezioni."
author: EduTeX
---

## Perché questo passo

Alcuni esercizi sono dialoghi guidati. Per svolgerli serve un agente di chat con le istruzioni dell'insegnante. Questo passo si fa una sola volta per corso.

## Passo 1: crea l'agente

1. Apri [Langdock](https://app.langdock.com) e crea un nuovo agente. Chiamalo "Dialogo guidato", o come preferisci.
2. Nelle istruzioni dell'agente incolla il testo seguente:

> Sei un insegnante di lingue che svolge esercizi di dialogo guidato.
>
> Quando ricevi un messaggio che inizia con "ESERCIZIO DIALOGO", leggi le istruzioni che seguono e applicale per tutta la conversazione: lingua, ruolo, obiettivo, lessico, strutture, numero massimo di turni e criteri di valutazione.
>
> Se ricevi un messaggio senza il blocco "ESERCIZIO DIALOGO", chiedi allo studente di incollare il testo dell'esercizio dalla pagina del corso.
>
> Dai il verdetto solo quando lo studente scrive VALUTA, oppure quando il dialogo si è concluso naturalmente con il saluto finale. Non dare mai il verdetto a metà dialogo. Quando lo fai, usa il formato indicato nelle istruzioni, come ultime tre righe. Rispondi sempre nella lingua indicata nell'esercizio.

3. Salva l'agente.

## Passo 2: collega l'agente al corso

1. Apri una nuova chat con l'agente e copia il link dalla barra degli indirizzi. Deve iniziare con https://.
2. Incollalo in `edutex.config.yaml`, nella sezione `dialogue`, come valore di `langdock_url`.
3. Ricostruisci il corso con il comando di build.

## Se non puoi creare l'agente

Salta questo passo e lascia `langdock_url` vuoto. Gli esercizi dialogue mostreranno la traccia per svolgere il dialogo con un madrelingua o con un compagno.

## Verifica

Apri una lezione con un esercizio dialogue, premi il pulsante e controlla che il testo venga copiato e che si apra la chat dell'agente.