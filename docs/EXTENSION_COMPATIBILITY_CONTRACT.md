# Contratto di compatibilità tra estensione e framework

Stato: candidato per V1.3
Versione di riferimento: 1.3.0

## Ambito

Un manifest di estensione può dichiarare il campo opzionale `framework`. Il
campo esprime quali versioni del framework possono caricare l'estensione.
L'assenza del campo mantiene il comportamento compatibile dei manifest
esistenti: l'estensione viene caricata senza un vincolo aggiuntivo.

La versione corrente del framework è `1.0.0`.

## Sintassi

Il valore deve essere una stringa composta da uno o più comparatori SemVer 2.0.0
stabili separati da virgole:

```yaml
framework: ">=1.0.0,<2.0.0"
```

Sono supportati gli operatori `=`, `>`, `>=`, `<` e `<=`. Un valore senza
operatore equivale a `=`. Non sono introdotti wildcard, OR o intervalli
impliciti in questa tranche.

Esempi validi:

```yaml
framework: ">=1.0.0"
framework: ">=1.0.0,<2.0.0"
framework: "1.0.0"
```

## Validazione

La compatibilità viene verificata durante la lettura del manifest e prima
dell'importazione del modulo. Un vincolo non valido o non soddisfatto produce
`ExtensionError` e impedisce il caricamento dell'estensione.

I manifest esistenti che non dichiarano `framework` restano validi. Il valore dichiarato
viene conservato nel modello `ExtensionManifest` e non modifica `version`,
`target`, `module` o `entrypoint`.

## Determinismo

- ogni clausola deve essere un comparatore SemVer stabile;
- tutte le clausole devono essere soddisfatte;
- la valutazione usa la versione framework `1.0.0` dichiarata dal runtime;
- la validazione avviene prima dell'importazione del modulo;
- lo stesso manifest produce sempre lo stesso esito.
