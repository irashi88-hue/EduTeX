# Contratto per sviluppatori di estensioni EduTeX

Stato: candidato per V1.3
Versione di riferimento: 1.3.0

## Scopo

Questo documento descrive il percorso minimo per creare un'estensione EduTeX
compatibile con il runtime pubblico. L'estensione deve essere autonoma,
deterministica e isolata: contribuisce al punto dichiarato senza modificare lo
stato interno del framework.

## Struttura minima

Un'estensione locale contiene un manifest `extension.yaml` e il modulo indicato
da `module`:

```yaml
id: reading_tip
name: Reading tip
version: 1.0.0
framework: ">=1.0.0,<2.0.0"
target: layout.post_structure
module: extension.py
entrypoint: apply
optional: false
```

Campi obbligatori:

- `id`: identificatore stabile, coerente con la configurazione;
- `name`: nome leggibile;
- `version`: versione SemVer 2.0.0;
- `target`: punto di estensione dichiarato;
- `module`: modulo locale o riferimento di import supportato;
- `entrypoint`: callable da eseguire.

Campi opzionali:

- `framework`: vincolo di compatibilità con il framework;
- `optional`: `false` per impostazione predefinita.

## Entrypoint

L'entrypoint deve essere una funzione importabile e callable. L'esempio minimo
è:

```python
def apply(context):
    """Contribute only through the declared extension point."""
    return context
```

Il nome `apply` non è imposto: deve corrispondere al valore `entrypoint` del
manifest. Il callable deve rispettare la firma prevista dal punto `target` e
non deve importare o modificare direttamente lo stato privato di Core,
Configuration, Registry, Resolver, Theme o Layout.

## Lifecycle e diagnostica

Il runtime valida il manifest, la versione, la compatibilità framework e la
callability dell'entrypoint prima della contribuzione. Gli errori delle estensioni obbligatorie producono `ExtensionError`. Le diagnostiche strutturate usano
`ExtensionDiagnostic` con `extension_id`, `point_id`, `phase` e `message`.

Un'estensione con `optional: true` può essere caricata tramite
`load_extension_with_fallback`; in caso di errore produce una diagnostica di
loading e un risultato con `loaded: None`, senza nascondere il messaggio
originale.

## Regole di isolamento

Un'estensione:

- modifica solo il contributo previsto dal proprio punto `target`;
- non riscrive file del progetto durante il processing;
- non modifica la configurazione globale;
- non registra entità duplicate;
- non dipende dall'ordine accidentale degli import;
- non intercetta o sopprime errori di altre estensioni;
- mantiene output e diagnostiche deterministici.

## Compatibilità

I manifest esistenti senza `framework` e senza `optional` restano validi. La validazione
SemVer e la compatibilità estensione/framework avvengono prima dell'import del
modulo. Le nuove estensioni devono documentare il proprio `target`, il valore
di `framework` usato e il comportamento in caso di fallback.
