# Contratto del rapporto JSON di `course build`

Stato: candidato per V1.1
Versione di riferimento: 1.1.0

## Separazione delle opzioni

`--format` continua a selezionare il formato dell'artefatto prodotto:
`html`, `latex` o `pdf`.

`--report-format` seleziona invece la rappresentazione del rapporto del
comando:

```text
edutex course build [--format html|latex|pdf]
  [--report-format text|json]
```

Il valore predefinito di `--report-format` è `text`, quindi l'output testuale
precedente resta invariato.

## Rapporto JSON di successo

Con `--report-format json`, il successo ha questa forma:

```json
{
  "course_build": {
    "status": "completed",
    "project_root": "...",
    "manifest": "...",
    "output_format": "html",
    "output": "...",
    "artifacts": ["...", "..."]
  }
}
```

`project_root`, `manifest`, `output` e ogni elemento di `artifacts` sono
percorsi assoluti. `output` deve essere incluso in `artifacts` e ogni percorso
elencato deve identificare un file esistente.

Gli artefatti pubblici sono:

- l'indice e tutte le pagine delle lezioni per un build HTML;
- l'artefatto principale per un build LaTeX o PDF.

I file temporanei generati dal compilatore PDF non fanno parte dell'elenco
pubblico.

## Rapporto JSON di errore

Un errore restituisce exit code `1` e non dichiara artefatti parziali:

```json
{
  "course_build": {
    "status": "failed",
    "error": {
      "type": "CourseBuildError",
      "message": "..."
    }
  }
}
```

`error.type` contiene il nome stabile della classe dell'errore e
`error.message` contiene il messaggio diagnostico. Il JSON non deve essere
mescolato con testo umano estraneo.

## Determinismo

- le chiavi e il loro significato sono stabili;
- i percorsi sono stringhe assolute;
- l'ordine di `artifacts` è l'artefatto principale seguito dalle pagine delle
  lezioni nell'ordine del manifest;
- il formato testuale precedente non cambia quando `--report-format` è omesso.
