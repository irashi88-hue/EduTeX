# Contratto dell'anteprima del Knowledge Model

Stato: candidato per V1.2
Versione di riferimento: 1.2.0

## Comando

```text
edutex preview SOURCE_FILE
  [--project PROJECT]
  [--config CONFIG]
  [--profile NAME]
```

Il comando genera un file HTML singolo in:

```text
<project_root>/output/preview/<source_file_stem>.html
```

Il percorso stampato dal comando è assoluto.

## Stile

La preview non modifica il file sorgente e non modifica la configurazione
originale del progetto.

L'anteprima usa la configurazione effettiva del progetto:

- `theme.name`;
- `layout.name`;
- estensioni abilitate;
- profilo selezionato con `--profile`, se presente.

L'anteprima forza solo il formato di output a HTML e la destinazione alla
cartella `output/preview`. Non modifica `edutex.config.yaml`, il file sorgente
o l'output della build normale.

## Compatibilità

- `edutex build` non cambia comportamento;
- `edutex lint` e `edutex author validate` non cambiano comportamento;
- il Knowledge Model viene processato con la pipeline Theme/Layout/Build
  esistente;
- una preview valida produce exit code `0`;
- errori di configurazione, asset, parsing o build producono exit code diverso
  da `0` e un messaggio testuale di Click.

## Determinismo

A parità di progetto, profilo e sorgente, il percorso dell'anteprima, il tema e
il layout risolti sono equivalenti. La sorgente originale non viene modificata.
