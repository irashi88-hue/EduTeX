# Contratto della raccolta dei contenuti del corso

Stato: candidato per V1.2
Versione di riferimento: 1.2.0

## Sorgenti di verità

La struttura del corso e l'ordine delle lezioni sono definiti da `course.yaml`.
Ogni `lesson.source` punta a un Knowledge Model Markdown.

`edutex.config.yaml` resta separato e continua a definire formato, tema, layout,
output ed estensioni dell'intero progetto. La raccolta dei contenuti non
introduce una seconda configurazione di stile.

## API pubblica

```python
from edutex.course import (
    CourseContentCollection,
    CourseContentEntry,
    load_course_content,
)

collection = load_course_content(course_yaml, project_root)
```

`load_course_content()` valida il manifest, carica e processa tutti i Knowledge
Model collegati, quindi restituisce una `CourseContentCollection`.

## Ordine e accesso

- `collection.ids` restituisce gli ID delle lezioni nell'ordine del manifest;
- `collection.all()` restituisce tutte le voci nell'ordine del manifest;
- `collection.get(lesson_id)` restituisce una voce o `None`;
- `collection[lesson_id]` restituisce una voce o solleva `KeyError`;
- `len(collection)` restituisce il numero di lezioni;
- ogni voce espone `lesson_id`, `title`, `source_path`, `meta` e `content`;
- `source_path` è assoluto;
- i risultati sono copie distaccate e non modificano la raccolta interna.

## Errori

Un manifest non valido o un Knowledge Model non leggibile produce
`CourseBuildError`. L'errore identifica la lezione interessata quando il
problema avviene durante il caricamento del contenuto.

## Compatibilità

- un progetto con una sola lezione mantiene il comportamento precedente;
- `edutex.config.yaml` non cambia forma;
- `course.yaml` resta l'unica fonte dell'ordine e dei collegamenti alle lezioni;
- `course build` continua a produrre gli stessi artefatti e lo stesso stile;
- la raccolta è un'API Python aggiuntiva e non modifica il parser degli
  shortcode.
