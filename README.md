# 🇩🇪 Grammatica Tedesca A1–B2

> Un manuale completo di grammatica tedesca, scritto in italiano e realizzato interamente in LaTeX.

---

## 📖 Descrizione

Questo progetto nasce con l'obiettivo di realizzare un manuale di grammatica tedesca dal livello **A1** fino al **B2**, pensato principalmente per studenti italiani.

A differenza di una grammatica tradizionale, il manuale segue una progressione didattica, spiegando non solo **come** costruire una frase, ma anche **perché** la lingua tedesca funziona in quel modo.

Ogni capitolo è progettato per essere autonomo e contiene:

- spiegazioni teoriche;
- esempi tradotti;
- errori comuni;
- curiosità linguistiche;
- trucchi mnemonici;
- lessico con articoli;
- esercizi;
- soluzioni.

---

# 🎯 Obiettivi

Il manuale coprirà:

- Livello A1
- Livello A2
- Livello B1
- Livello B2

Seguendo le linee guida del Quadro Comune Europeo di Riferimento (QCER).

---

# 📂 Struttura del progetto

```
Grammatica-Tedesca/
│
├── .git/
├── .gitignore
├── README.md
├── LICENSE
│
├── main.tex
├── preambolo.tex
├── bibliografia.bib
│
├── docs/
│   ├── roadmap.md
│   ├── style-guide.md
│   ├── changelog.md
│   ├── todo.md
│   ├── struttura-libro.md
│   └── convenzioni-latex.md
│
├── capitoli/
│   ├── 00_introduzione.tex
│   ├── 01_alfabeto.tex
│   ├── ...
│
├── lessico/
│   ├── ripasso01.tex
│   ├── ...
│
├── appendici/
│   ├── glossario.tex
│   ├── verbi_forti.tex
│   └── ...
│
├── tabelle/
│   ├── casi.tex
│   ├── verbi_modali.tex
│   └── ...
│
├── immagini/
│   ├── bandiere/
│   ├── diagrammi/
│   └── icone/
│
├── output/
│   └── grammatica.pdf
│
└── tools/
    ├── build.sh
    └── clean.sh
```

---

# 📚 Struttura dei capitoli

Ogni capitolo segue la stessa organizzazione.

1. Scheda del capitolo
2. Introduzione
3. Spiegazione
4. Regole
5. Costruzione della frase
6. Esempi
7. Errori comuni
8. Curiosità
9. Trucco mnemonico
10. Lessico
11. Riassunto
12. Esercizi
13. Soluzioni

---

# 🛠 Requisiti

Per compilare il progetto è consigliato utilizzare:

- TeX Live
- oppure MiKTeX

Compilatore consigliato:

- XeLaTeX

Editor consigliato:

- Visual Studio Code
- Estensione LaTeX Workshop

---

# 🚀 Compilazione

Compilare il progetto eseguendo:

```bash
xelatex main.tex
```

oppure utilizzare la compilazione automatica di LaTeX Workshop.

---

# 🌱 Workflow Git

Il progetto segue una struttura Git semplice.

Branch principali:

- main → versione stabile
- develop → sviluppo

Convenzione dei commit:

```
feat:
fix:
docs:
style:
refactor:
```

Esempi:

```
feat: aggiunto capitolo sui casi

fix: corretti esempi del Perfekt

docs: aggiornato indice
```

---

# 📖 Convenzioni di scrittura

Per mantenere il manuale uniforme vengono seguite alcune regole.

- Un capitolo = un file `.tex`
- Ogni esempio è tradotto in italiano.
- Il lessico viene introdotto gradualmente.
- Ogni nuovo concetto è preceduto dai prerequisiti necessari.
- Le curiosità linguistiche sono evidenziate in appositi riquadri.
- Gli errori tipici degli italiani sono spiegati separatamente.

---

# 📈 Stato del progetto

| Parte | Stato |
|--------|-------|
| Struttura LaTeX | ⏳ |
| A1 | ⏳ |
| A2 | ⏳ |
| B1 | ⏳ |
| B2 | ⏳ |
| Glossario | ⏳ |
| Tabelle finali | ⏳ |

---

# 📜 Licenza

Questo progetto è distribuito secondo la licenza presente nel file `LICENSE`.

---

# 👤 Autore

Progetto ideato da **Luca Raiola**.

Supporto alla progettazione, revisione e sviluppo dei contenuti con ChatGPT.