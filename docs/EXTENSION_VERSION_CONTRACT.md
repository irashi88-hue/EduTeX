# Contratto della versione delle estensioni

Stato: candidato per V1.3
Versione di riferimento: 1.3.0

## Ambito

Il campo obbligatorio `version` di ogni manifest di estensione viene validato
come stringa SemVer 2.0.0 prima dell'importazione del modulo dell'estensione.
Gli altri campi del manifest (`id`, `name`, `target`, `module` ed
`entrypoint`) mantengono il contratto esistente.

## Formato accettato

Sono accettate:

- versioni stabili, per esempio `1.0.0`;
- versioni prerelease, per esempio `1.0.0-alpha.1`;
- versioni con build metadata, per esempio `1.0.0+build.1`;
- versioni con prerelease e build metadata, per esempio
  `1.0.0-rc.1+build.7`.

La validazione è esatta e non normalizza il valore dichiarato. Non sono
accettati `1.0`, `v1.0.0`, stringhe vuote, valori non stringa o componenti
numerici con zeri iniziali come `01.0.0`.

## Errori

Un manifest con una versione non valida produce `ExtensionError` durante la
lettura del manifest, prima del caricamento o dell'esecuzione del modulo.
Il messaggio identifica il campo `version` e dichiara che il valore deve essere
una stringa SemVer 2.0.0.

I manifest esistenti con versioni come `1.0.0` restano validi. Il valore della
versione viene conservato senza modifica nel modello `ExtensionManifest` e
nell'introspection runtime.

## Determinismo e compatibilità

- la grammatica è quella di SemVer 2.0.0;
- prerelease e build metadata non cambiano il testo serializzato del valore;
- gli identificatori numerici non possono avere zeri iniziali;
- la validazione avviene prima dell'importazione del modulo;
- il contratto non modifica target, module, entrypoint o ordine di caricamento;
- lo stesso valore produce sempre lo stesso esito.

## Verifica locale

Dalla root del repository:

```powershell
python -m py_compile .\src\edutex\extension\versioning.py .\tests\test_extension_version_contract.py
python -m pytest -q .\tests\test_extension_version_contract.py
python -m pytest -q
python .\tools\quality_check.py --verbose
python .\tools\release_smoke.py
```
