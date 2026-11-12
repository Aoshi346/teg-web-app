# core/ — plantillas de `.docs/core/`, la documentación viva del proyecto

Punto de entrada único para entender un sistema entero: de lo visual y resumido arriba, al detalle
abajo. Lo que se puede generar del código **se genera**; lo que no, se escribe una vez y **se
revisa**. El índice muestra la fecha de cada cosa y marca lo que ya no es de fiar.

Convención canónica: `.claude/rules/plan-docs-structure.md` §core. Generador:
`.claude/scripts/gen_core.py`.

## Qué hay aquí

| Fichero | Qué es |
|---|---|
| `core.json` | Manifiesto: qué documentos forman el core, en qué capa y quién los genera. **Sin fechas** — las descubre el generador |
| `index.template.html` | Plantilla del índice. Recibe los datos en `const DB = /*__DATA__*/null;` |
| `overview.md` | Capa 1, se escribe a mano. Frontmatter `reviewed:` obligatorio |
| `ux.md` | Capa 4 (el porqué de la interfaz), se escribe a mano. Frontmatter `reviewed:` obligatorio |
| `design-system.md` | Capa 6, **fundacional**: dónde viven los tokens, qué es intocable. Frontmatter `reviewed:` obligatorio |

## Arrancar el core en un proyecto

```bash
python3 .claude/scripts/gen_core.py --init     # copia core.json + overview.md + ux.md + design-system.md
$EDITOR .docs/core/core.json                   # project, code_dirs y qué documentos aplican
python3 .claude/scripts/gen_core.py            # genera .docs/core/index.html
```

Después, cada vez que se genere o revise algo: `python3 .claude/scripts/gen_core.py`. El índice
**no se edita a mano** — se regenera, que es justo lo que impide que empiece a mentir.

## Promoción: de la foto de un plan a la versión viva

Un plan (`.docs/plans/<fecha>-<slug>/`) es una foto de un momento; el core es el presente. Cuando un
plan genera o actualiza un documento del core, se **promueve**:

```bash
python3 .claude/scripts/gen_core.py --promote architecture .docs/plans/2026-08-07-x/architecture.html
```

La promoción copia el fichero a `.docs/core/` y le estampa el marcador
`<!-- core-meta: date=YYYY-MM-DD sha=abc1234 via=/visual-map -->`. Ese marcador es lo que convierte
la fecha en **declarada** (fiable) en vez de **inferida** de git o del mtime. Mientras un documento
siga apuntando a un plan, el índice lo avisa: el plan se congela y el documento se queda atrás.

## Cómo se decide el estado de cada documento

| Estado | Cuándo |
|---|---|
| **al día** | Existe, tiene fecha y nada la ha invalidado |
| **obsoleto** | Documento generado cuyo código de referencia cambió *después* (comparación por día) |
| **por revisar** | Documento escrito revisado hace más de `review_days`, o antes del último plan cerrado |
| **sin fecha** | Existe pero no dice de cuándo es. **No es fiable** y sale en rojo |
| **falta** | Declarado en `core.json` y el fichero no existe |
| **vacío / no creado** | Sin contenido aún, u opcional no usado. No es alarma |

Origen de la fecha, por orden de fiabilidad: marcador `core-meta` o frontmatter `reviewed:`
(*declarada*) → último commit que tocó el fichero (*git*) → mtime en disco. Las dos últimas se
marcan como **inferidas** en la tarjeta, porque el documento no dice nada de sí mismo.

## Las capas 1-5 describen; la 6 manda

Las cinco primeras capas responden **qué hay**: overview, arquitectura, datos, UX, decisiones. La
capa 6 es de otra naturaleza — son documentos **fundacionales**, del tipo del `constitution.md` de
SpecKit: no describen lo construido, **mandan sobre lo que se va a construir**. Hoy vive ahí el
sistema de diseño (`design-system.md`): dónde está el origen único de los tokens, qué es intocable y
qué es libre.

Por eso el sistema de diseño **no es una sección de `ux.md`**: `ux.md` explica por qué el recorrido
es así (descriptivo, se lee para entender); el sistema de diseño dice con qué se pinta y qué no se
toca (prescriptivo, se lee para obedecer). Mezclarlos hace que la parte que obliga se lea como
contexto opcional.

Cada proyecto declara **el suyo**: el template no impone tokens. Un proyecto sin interfaz lo marca
`"optional": true` con un `question` que empiece por "No aplica:".

## Añadir un documento al core

Una entrada en `docs[]` de `core.json`:

```json
{
  "id": "c4-container", "layer": "arquitectura", "title": "C4 · Contenedores",
  "question": "Qué se despliega y en qué proceso corre cada cosa",
  "origin": "generado", "file": "c4-container.html", "via": "/schema c4-container",
  "optional": true,
  "watch": ["infra/**", "docker-compose*.yml"]
}
```

`origin`: `generado` (envejece con el código) o `escrito` (envejece con el calendario y los planes).
`watch`: pathspecs de git que vigila **este** documento; sin ellos usa los `code_dirs` globales.
`optional: true` hace que su ausencia sea gris en vez de roja.

---

## Fase 2 — lo que está especificado pero NO implementado

La Fase 1 (este generador y este índice) resuelve **enlazar y fechar** lo que ya existe. Lo que
falta es el **ritual de escritura y revisión** de lo que no sale del código:

1. **Gate de cierre de plan.** Al cerrar un plan, contestar tres preguntas: ¿cambió lo que hace el
   sistema (→ `overview.md`)? ¿cambió cómo se usa (→ `ux.md`)? ¿se tomó una decisión cara de
   revertir (→ un ADR)? Si la respuesta es sí y el documento no se tocó, el plan no cierra. Hoy el
   índice ya *detecta* el desfase (marca "por revisar" cuando se cerró un plan después de la última
   revisión), pero nadie lo *obliga*: el gate iría en `rules/plan-gates.md` y su enforcement en un
   hook, no en prosa (`harness-gotchas.md`: CLAUDE.md es advisory).
2. **Contenido del overview y de la UX.** Las plantillas están vacías con `[PERSONALIZAR]` a
   propósito. Rellenarlas es trabajo de cada proyecto, no del template: inventarlo aquí sería
   exactamente el wiki que envejece que se quiere evitar.
3. **`--check` en CI.** `gen_core.py --check` ya devuelve exit 1 si el índice no refleja el disco;
   falta decidir dónde se engancha (hook `Stop`, pre-commit o gate de wave) y con qué severidad.
4. **Promoción automática desde `/visual-map` y `/schema`.** Hoy la promoción es un comando manual
   que el índice te ofrece copiado. Que el propio generador promueva al core al terminar exige tocar
   esos comandos, que son de otro alcance.
