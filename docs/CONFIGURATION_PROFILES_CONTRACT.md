# Contratto dei profili di configurazione EduTeX

Stato: candidato per V1.1
Versione di riferimento: 1.1.0

Questo contratto definisce i profili selezionabili dalla configurazione di
progetto. Senza `--profile`, il comportamento esistente resta invariato.

## Definizione nel file YAML

I profili sono dichiarati in `edutex.config.yaml`, nella mappa top-level
`profiles`. La mappa è un involucro di selezione e non fa parte di `EduTexConfig`.

```yaml
build:
  output_format: pdf
  output_dir: output
  output_file: document

profiles:
  web:
    build:
      output_format: html
      output_dir: web
  classroom:
    theme:
      name: dark
```

I nomi devono essere stringhe non vuote, già prive di spazi iniziali o finali.
Ogni profilo deve essere una mappa. Le strutture dei profili sono controllate
anche quando non vengono selezionati; i valori del profilo selezionato sono
validati insieme alla configurazione risultante.

## Merge e validazione

La configurazione base viene copiata e gli override del profilo si applicano con
un override ricorsivo delle mappe. Liste e valori scalari vengono sostituiti
integralmente. L'override applica la configurazione senza ereditarietà tra
profili: ciascun profilo modifica indipendentemente la stessa configurazione
base.

Il profilo è applicato prima della validazione di `EduTexConfig`. Il modello
risultante mantiene le regole e l'immutabilità già previste dalla configurazione.
La selezione non modifica il file YAML né l'oggetto di configurazione base.

Un profilo richiesto ma non definito, una definizione malformata o un override
invalido producono `ConfigurationError`. La chiave top-level `profiles` non è
esposta nel modello runtime.

## Comandi supportati

`--profile NAME` è disponibile per:

- `edutex build`;
- `edutex validate`;
- `edutex inspect`;
- `edutex course build`.

Per `edutex inspect`, quando il profilo è selezionato, il rapporto JSON riporta
il nome in `inspection.configuration.profile`. Senza selezione la forma attuale
resta invariata.

`edutex course build --profile NAME` è valido solo con `--format html`, perché
PDF e LaTeX del corso non usano la configurazione del progetto. Con `--format
pdf` o `--format latex`, il comando rifiuta `--profile` invece di ignorarlo.

## Compatibilità e determinismo

- l'assenza di `--profile` conserva i valori e i rapporti già esistenti;
- le chiavi della configurazione effettiva continuano a essere validate dallo
  schema `EduTexConfig`;
- la precedenza è: configurazione base, poi override del profilo selezionato;
- nomi dei profili case-sensitive;
- il file sorgente non viene modificato durante la selezione;
- gli errori di build e validate mantengono i rispettivi contratti JSON.
