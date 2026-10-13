# EduTeX Studio: modifica guidata del contenuto delle lezioni

Avvia l'editor locale gia presente:

```powershell
edutex author studio --project .
```

La sezione **Contenuto delle lezioni** consente di scegliere tra blocchi di titolo,
testo, elenco, nota, regola, esempio ed esercizio. Il wizard configura gli esercizi
choice, true/false, cloze, matching, short answer, translation e sentence builder.

Il frontmatter e i blocchi Markdown/shortcode non supportati non vengono mostrati
come sorgente e restano invariati. I contenuti riconosciuti si modificano con campi
visuali. Ogni salvataggio conserva il frontmatter, rifiuta conflitti da modifiche
esterne, valida la lezione prima della scrittura e sostituisce il file in modo
atomico. Correzioni a errori gia presenti non sono impedite: il salvataggio rifiuta
solo nuovi errori di authoring.

L'editor e accessibile solo da loopback e richiede il token temporaneo della sessione.
La prima versione lascia in sola lettura la formattazione inline complessa, tabelle,
blocchi di codice, blocchi personalizzati e shortcode non gestiti. L'editor mostra il
tipo del contenuto e una breve anteprima testuale, quando disponibile, preservando
la sorgente originale senza consentirne la modifica.
