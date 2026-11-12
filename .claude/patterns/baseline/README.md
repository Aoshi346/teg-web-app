# `.claude/patterns/baseline/` — la deuda congelada (el trinquete)

> **Qué es:** un fichero por patrón con la lista de las infracciones que **ya existían** cuando la
> regla se encendió en este proyecto. El gate las conoce y **no las reporta**; solo avisa de lo
> nuevo. Trinquete (*ratchet*) porque solo gira en un sentido: la deuda baja, nunca sube en silencio.
>
> **El procedimiento** (cuándo congelar, en qué orden refactorizar, qué NO se toca nunca y cuándo se
> promueve una regla) vive en **`rules/refactor-progresivo.md`**. Aquí solo está el **formato** y su
> ciclo de vida.
>
> **La herramienta:** `.claude/scripts/pattern_baseline.py` (`freeze` · `check` · `status` ·
> `retire`). Stdlib pura, lee la salida `--json` de cualquier comprobador de la casa.

---

## El fichero

Uno por patrón: **`<patron_id>.json`**. El nombre del fichero debe coincidir con el `patron_id` de
dentro; si no coincide, manda el contenido (la herramienta indexa por `patron_id`, no por nombre —
ver §Gotchas).

```json
{
  "patron_id": "rule-header-cuando-aplicar",
  "frozen_at": "2026-08-07",
  "frozen_by": "pattern_baseline.py freeze --from /tmp/medicion.json",
  "nota": "Deuda aceptada (ratchet). Solo un humano amplía esta lista. Migran por boy-scout.",
  "migradas": [
    {"file": ".claude/rules/security.md", "fecha": "2026-08-08",
     "por": "cabecera añadida por boy-scout durante la adopción; verificado 2026-08-08"}
  ],
  "violations": [
    ".claude/rules/code-style.md",
    ".claude/rules/speckit-progress-tracking.md"
  ]
}
```

| Campo | Obligatorio | Qué es |
|---|---|---|
| `patron_id` | sí | El id de la regla en `catalog.yaml` o en el comprobador del stack |
| `frozen_at` | sí | Fecha de la congelación. Un baseline viejo sin revisar deja de reflejar la realidad |
| `frozen_by` | no | El comando exacto que lo generó — para poder repetir la medición |
| `nota` | sí | Recordatorio del contrato: es deuda aceptada, no permiso |
| `migradas[]` | sí (puede ir vacío) | Historial de lo que **salió** del baseline: `file` · `fecha` · `por`. Es lo que impide que la deuda vuelva a entrar sin que nadie lo note |
| `violations[]` | sí | **La deuda viva.** Rutas relativas a la raíz del repo, en POSIX |
| `aviso_inversion` | no | Lo añade `freeze --force` cuando se congela por encima del umbral de inversión: deja la decisión visible en el diff |

### `violations[]` — la clave es el FICHERO, no la línea

Deliberado. Los números de línea se mueven con cualquier edición de más arriba, así que un baseline
anclado a líneas empieza a mentir en el primer commit.

El precio, dicho en voz alta: **un fichero congelado queda exento de esa regla entero**. Lo que
cierra ese agujero no es afinar el baseline, es `check --diff-scope` — si tocas la línea, se te
juzga la línea (`rules/refactor-progresivo.md` §4.3).

`violations[]` acepta también objetos (`{"file": "...", "nota": "..."}`) por si hace falta anotar un
caso; la herramienta lee las dos formas. La forma canónica es la cadena.

---

## Ciclo de vida

```
medir  →  freeze  →  [ el gate ignora esta deuda ]  →  alguien arregla un fichero  →  retire
                              ↑                                                          │
                              └──────────── status dice cuánto queda ────────────────────┘
```

```bash
# congelar (una vez, al adoptar la regla)
<comprobador> --all --json > /tmp/medicion.json
python3 .claude/scripts/pattern_baseline.py freeze --from /tmp/medicion.json

# el gate del día a día
<comprobador> --json | python3 .claude/scripts/pattern_baseline.py check --from - --diff-scope

# sanear: qué queda y qué ya no infringe
python3 .claude/scripts/pattern_baseline.py status --from /tmp/medicion.json
python3 .claude/scripts/pattern_baseline.py retire --from /tmp/medicion.json --apply
```

**Solo un humano amplía la lista.** Un agente puede medir, proponer y **retirar** (retirar solo
reduce deuda, es seguro); congelar deuda nueva es una decisión con coste y la firma una persona
(`rules/governance.md` §2).

---

## Gotchas verificados

- **El nombre del fichero puede no coincidir con el `patron_id`.** Pasa aquí mismo:
  `rule-header.json` declara `patron_id: rule-header-cuando-aplicar`. La herramienta indexa por el
  **contenido**; si indexara por el nombre, no encontraría este baseline y crearía un duplicado al
  escribir. Para ficheros nuevos, usa `<patron_id>.json` y evita el lío.
- **Dos ficheros con el mismo `patron_id`** → la herramienta se para y pide que dejes uno. Un patrón
  con dos baselines es un patrón sin baseline.
- **`hooks/pattern-check.sh` no distingue `violations` de `migradas`.** Comprueba el baseline con un
  `grep` de la ruta sobre **todo** el fichero, así que un fichero ya migrado le sigue pareciendo
  exento. Es una fuga real del trinquete; el arreglo toca `hooks/` y requiere aprobación
  (`governance.md` §2). Mientras tanto, la comprobación fiable es `pattern_baseline.py check`.
  El arreglo propuesto, para cuando haya aprobación:

  ```bash
  in_baseline(){ python3 -c "import json,sys;d=json.load(open('.claude/patterns/baseline/rule-header.json'));sys.exit(0 if sys.argv[1] in d['violations'] else 1)" "$1"; }
  ```

- **Los dos comprobadores del stack hablan dialectos JSON distintos** (backend: `rule`/`path` ·
  frontend: `id`/`file`). `pattern_baseline.py` normaliza ambos, pero la divergencia sigue ahí y
  está pendiente de unificar por el TL (ya anotada en `patterns/stack/REGLAS.md` §Mitad FRONTEND).

---

## Anti-patterns

- ❌ Editar `violations[]` a mano para quitar una entrada → se pierde el historial; usa `retire`.
- ❌ Re-congelar el baseline entero "para actualizarlo" → crece en silencio y el trinquete gira al
  revés. `freeze` se niega salvo `--replace` explícito.
- ❌ Congelar una regla que marca decenas de sitios → es blanquear una regla mala, no pagar deuda
  (regla de inversión, `patterns/README.md` §2).
- ❌ Un baseline por usuario o fuera de git → una exención que solo existe en una máquina es un
  secreto, no una exención.
- ❌ Anclar entradas a números de línea.
- ❌ Dejar el baseline meses sin `status` → deja de reflejar la realidad y nadie confía en él.

---

_v1.0 · 2026-08-08 · RFC-2._
