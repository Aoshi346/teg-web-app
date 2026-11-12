---
name: "auto-dream-memory"
description: >-
  Usar al tocar la memoria: traer al retomar ('ponme al día', '/sync-memory'), consolidar
  ('consolida la memoria', 'poda MEMORY.md'), la retro ('/retro') o subir lo aprendido a
  CLAUDE.md ('/weekly-review'); también al cerrar SpecKit o cada 5 sesiones. NO usar para: la
  tarea en curso (progress-tracking.md), una decisión cara de revertir (adr.md) ni qué sobra del
  harness (self-improvement-loop.md §5).
user-invocable: true
metadata:
  version: 1.3.1
  author: Tech Lead Template
  category: workflow
  updated: 2026-10-21
  source: "adapted from boris-dream"
  absorbe: "boris-dream (4 fases) y sync-memory (operación traer) — archivadas 2026-08-22 · retro (§C) y weekly-review (§D) — archivadas 2026-10-19 (LI-9)"
  tech-stack: "ajusta al stack del proyecto"
---

# Memoria — traer, consolidar, revisar la semana y subir a CLAUDE.md

## Cuándo se activa (detalle)

Disparadores: (a) TRAER, al retomar: 'ponme al día', '¿dónde lo dejamos?', 'sincroniza la
memoria', '.ai/memory.md está desactualizado', '/sync-memory', 'catch me up'. (b) CONSOLIDAR, al
cerrar: 'consolida la memoria', 'poda MEMORY.md', 'dream', al cerrar SpecKit, cada 5 sesiones o con
MEMORY.md > 150 líneas. (c) INFORME DE LA SEMANA: 'retro semanal', 'qué se hizo esta semana',
'/retro', 'weekly retro', 'retrospective', 'what did we ship'. (d) PASAR LO APRENDIDO A CLAUDE.md,
con diff y confirmación: 'revisión semanal', 'qué hemos aprendido esta semana', 'actualiza el
CLAUDE.md', 'el CLAUDE.md se ha quedado viejo', 'poda el CLAUDE.md', '/weekly-review', 'weekly
review', 'update CLAUDE.md from memory', 'prune CLAUDE.md' · NO usar para: la tarea en curso ni la
cola de peticiones (rules/progress-tracking.md).

> **La arquitectura no está aquí.** Qué capa es cada fichero, qué se guarda, qué no y los
> disparadores: **`rules/memory.md`**, y es el único sitio. Esta skill es lo que se EJECUTA.

## Las cuatro operaciones

| | **TRAER** (§A) | **CONSOLIDAR** (§B) | **REVISAR LA SEMANA** (§C) | **SUBIR A `CLAUDE.md`** (§D) |
|---|---|---|---|---|
| Cuándo | Al **empezar**: retomas y no sabes dónde lo dejaste | Al **cerrar**: la memoria acumuló ruido | Viernes, cierre de sprint o wave grande, >50 commits sin repaso | Lunes, tras cerrar una sesión SpecKit, o `CLAUDE.md` > 200 líneas |
| Lee | auto-memoria + `git log` + SpecKit + `PROGRESS.json` | `.ai/memory.md` + `MEMORY.md` + `.claude/memory.json` | `git log` de la semana + `PROGRESS.log` (bloqueos) + aprendizajes | auto-memoria + `.ai/memory.md` + `MEMORY.md` + `git log` + `CLAUDE.md` |
| Escribe | `.ai/memory.md` (capa 2) — **y nada más** | `MEMORY.md` y `.claude/memory.json` (capas 3 y 4) | un informe (`.claude/memory/retros/YYYY-WW.md`); una línea sube a `MEMORY.md` | un **diff** a `CLAUDE.md` que **no se aplica sin confirmación** |
| Cuesta | segundos | minutos, y hay que revisar lo que borró | minutos | minutos, y si se aplica a mitad de sesión no rige hasta `/clear`, `/compact` o reiniciar |

Se hacen por separado. Traer al cerrar no consolida nada, y consolidar al empezar poda una memoria
que la sesión que viene todavía va a cambiar. §C y §D comparten fuentes y cadencia, pero no
entregable: §C es un **informe** para leer; §D es un **cambio** a `CLAUDE.md`. Si te piden "la
revisión semanal" sin más, pregunta cuál de los dos.

**Disparadores de consolidar** (fuente única: `rules/memory.md` §3, no los copies a otro sitio):
sesión SpecKit cerrada · 5 sesiones sin consolidar · `MEMORY.md` > 150 líneas · después de un
refactor que mueva o renombre ficheros.

---

# §A · TRAER — ponerse al día al retomar

> Heredado de esta misma skill (§A) — `sync-memory` se fusionó aquí el 2026-08-22 (archivada el 2026-08-22), que era `user-invocable` y por eso
> esta skill lo es: `/sync-memory` era el punto de entrada y no podía perderse.

**Regla dura: esta operación NO toca `MEMORY.md`.** Escribe `.ai/memory.md` y para. Lo de largo
plazo se decide consolidando (§B), no de pasada al arrancar.

### A.1 · Localizar la auto-memoria — comprobando, no suponiendo

```bash
PROJECT_SLUG=$(pwd | sed 's|/|-|g')
AUTO_MEM="$HOME/.claude/projects/${PROJECT_SLUG}/memory"
ls "$AUTO_MEM"/*.md 2>/dev/null | wc -l     # si da 0, mira el autoMemoryDirectory de settings.json
cat "$AUTO_MEM/MEMORY.md" 2>/dev/null
```

⚠️ Los dos sitios posibles no coinciden en este repo — `rules/memory.md` §4.3 lo mide y explica.
**Se trabaja sobre el directorio que tenga ficheros**, no sobre el que declara la configuración.

### A.2 · Leer el estado real del proyecto

```bash
git log --oneline -10                                  # y mira el SCOPE de cada uno, no solo el título
git diff --name-only HEAD~5..HEAD | head -30
git diff --name-only HEAD                              # lo que está sin commitear
cat PROGRESS.json 2>/dev/null | jq '{task,status}'
grep -E "^\- \[.\]" .specify/sessions/*/tasks.md 2>/dev/null | tail -20
```

### A.3 · Escribir `.ai/memory.md`

```markdown
# Session Memory — <proyecto>
_Última sincronización: YYYY-MM-DD HH:MM_

## Trabajo en progreso
- **SpecKit session:** [ID + wave actual, si aplica]
- **HEAD:** [hash + título]
- **Próximo paso EXACTO:** [el comando o la acción con la que se sigue]

## Lo implementado (commits recientes)
1. **[hash]** — [qué hace de verdad, no el título del commit]

## Decisiones recientes
- [Decisión] — [por qué]

## Gotchas activos
- [Problema] — [workaround]

## Estado de tests
- Backend: [OK / FAIL — módulo] · Frontend: [build pasa? sí/no]
```

Si no hay nada reciente que traer, **se escribe eso mismo**: un fichero que no dice nada es mejor
que uno que insinúa un trabajo en curso que no existe.

---

# §B · CONSOLIDAR — podar y fusionar

## Principio

Después de varias sesiones, `.ai/memory.md` acumula información stale y `MEMORY.md` puede tener referencias rotas. Consolidar es un pass reflexivo para fusionar, podar y actualizar.

## Qué consolidar

### En `.ai/memory.md`
- Actualizar "Próximo paso EXACTO" con el estado real post-sesión
- Eliminar referencias a archivos que ya no existen
- Actualizar estado de SpecKit sessions (wave completada, próxima wave)

### En `MEMORY.md` (long-term)
- Añadir ADRs nuevas descubiertas en las últimas sesiones
- Actualizar "Stack actual" si se añadieron librerías
- Añadir gotchas nuevos del stack
- Eliminar gotchas resueltos
- Actualizar lista de módulos/apps si se añadieron nuevos

### En `.claude/memory.json`
- `last_session` con fecha actual
- `recent_changes` con los últimos cambios
- Limpiar `pending_tasks` si están completadas
- Actualizar `architecture_decisions` con ADRs nuevos

### Memorias de agente (`agents/<x>/memory.md` y `herencia/`)

Disparador: más de **300 líneas** (`rules/memory.md` §3b). Lo avisa `otto-briefing.sh` al arrancar;
a mano, `python3 .claude/scripts/check_agent_memory.py` (0 bien · 1 avisos · 2 sin `agents/`).

1. Leer la memoria entera **antes** de recortar, y apartar lo que dura: calibraciones del agente
   (falsos positivos que cometió y por qué), reglas de método, trampas de herramientas, la fase de
   autonomía con su evidencia, y los hallazgos abiertos.
2. El diario por ronda (v14, v15… o iter-8, iter-9…) se queda en **una tabla de una fila por ronda**
   (fecha · score · delta · qué cambió). El detalle ya está en el `REPORT.md` de cada ronda: se
   enlaza, no se copia.
3. Hallazgos cerrados → una línea en «Áreas validadas»; los repetidos, fusionados con su contador.
4. Lo que sirve para cualquier proyecto se marca para `/consolidate-agent-learnings` (sube al
   template sin datos de cliente); lo propio se queda.
5. `herencia/*.md` no se edita: se poda **al heredar** (paso de `project-setup`) o se borra con OK
   cuando la memoria propia ya cubre lo heredado.
6. Volver a correr el script: la memoria baja de 300 líneas o la excepción se escribe arriba, con fecha.

## Las 4 fases

> Heredado de esta misma skill (§B) — `boris-dream` se fusionó aquí el 2026-08-22 (archivada el 2026-08-22): era **lo único que aquella skill tenía
> y esta no**. El resto —disparadores, qué consolidar, anti-patterns— ya estaba aquí, y sus claves
> de configuración (`autoMemoryEnabled`, `autoMemoryDirectory`) están en `rules/memory.md` §4.3.

Se hacen **en orden**: podar antes de haber leído es cómo se borra lo que importaba.

| # | Fase | Qué se hace | Cómo se sabe que terminó |
|---|---|---|---|
| 1 | **Orientarse** | `ls` del directorio de auto-memoria y leer su `MEMORY.md`; ojear los ficheros por tema | Sabes qué hay antes de tocar nada |
| 2 | **Recoger señal** | Buscar hechos ya caducos: fechas stale, rutas a ficheros que ya no existen, contradicciones con el código de hoy | Tienes una lista de sospechosos, no una impresión |
| 3 | **Consolidar** | Fusionar los duplicados del mismo tema · convertir fechas relativas a absolutas («el jueves pasado» → `2026-03-20`) · borrar lo que la información nueva contradice · actualizar rutas y nombres | Cada hecho vive en un solo sitio y se sostiene solo |
| 4 | **Podar e indexar** | Reconstruir `MEMORY.md` por debajo de las 150 líneas · quitar punteros a ficheros borrados o fusionados · añadir los nuevos · **una línea por entrada, < 150 caracteres** | El índice describe el disco, no lo que había el mes pasado |

**La fase 1 se hace sobre el directorio que TENGA ficheros** (el check está en §A.1): el
`autoMemoryDirectory` que declara `settings.json` y el sitio donde están los hechos no coinciden en
este repo, y por qué no se sabe. Medido y explicado en `rules/memory.md` §4.3.

## Cómo ejecutar el dream manualmente

```bash
# Opción 1: /dream — ❌ NO existe en esta instalación (medido el 2026-08-22, v2.1.240):
#   ls ~/.claude/commands/ | grep -ix dream.md          → 0
#   find ~/.claude/plugins -path '*commands*' -name 'dream*' | wc -l → 0
#   ls .claude/commands/ | grep -i dream                 → 0
# Si tu versión lo trae, `/help` lo dirá. Mientras tanto, se ejecuta a mano (opción 2).

# Opción 2: prompt directo a Claude headless. Con el modo en la orden: sin él, `-p` arranca en
# Manual y deniega las escrituras (el template ya no fija `defaultMode`, CL-D1, 2026-10-21).
# Ojo: `.claude/memory.json` es ruta protegida (`.claude/`) y `acceptEdits` NO la escribe (medido el
# 21-10: MEMORY.md y .ai/memory.md sí, memory.json denegado, también con --allowedTools). El paso 3
# se hace a mano, o se lanza con `--permission-mode auto`, que lo deja al clasificador.
claude -p --permission-mode acceptEdits "
Lee .ai/memory.md, MEMORY.md y .claude/memory.json.
Consolida la memoria de este proyecto:
1. Actualiza MEMORY.md: añade ADRs nuevos, elimina refs obsoletas, max 150 líneas
2. Actualiza .ai/memory.md: deja solo el contexto relevante para la próxima sesión
3. Actualiza .claude/memory.json: last_session=hoy, pending_tasks actualizadas
4. Report: qué añadiste, qué eliminaste, qué actualizaste
"
```

## Qué documentar específicamente en los ADRs

Ejemplos típicos por tipo de proyecto (adapta al tuyo):
- **Librerías añadidas**: por qué X sobre Y — tradeoffs de DX, tamaño, mantenimiento
- **Patterns backend**: por qué ViewSets vs APIViews, signals vs post_save, repos vs services
- **Patterns frontend**: cuándo crear store vs usar local state, cuándo memoizar
- **LLM/AI** (si aplica): qué proveedor y modelo por defecto, qué esfuerzo de razonamiento por tipo de tarea (la temperatura no: `patterns/stack/agente-modelo-y-coste.md`)

## Ejemplo de ADR bien documentado

```markdown
## Architecture Decisions
- [2026-04-12] ADR-004: @dnd-kit para drag-drop (sobre react-beautiful-dnd) — mejor soporte TypeScript + mantenido activamente
- [2026-03-31] ADR-003: LLMService + RAGService separados — testability: LLM mockeable sin RAG
- [2026-02-01] ADR-001: Zustand sobre Redux — menos boilerplate, mejor DX para equipo pequeño
```

## Anti-patterns

- Dream sin haber usado Claude recientemente (nada que consolidar)
- No verificar el output del dream (puede borrar cosas importantes)
- Dream durante una sesión de trabajo activa (esperar a terminar la tarea)
- Ignorar el dream por meses (memoria se degrada, refs stale se acumulan)

---

# §C · REVISAR LA SEMANA — el informe (antes skill `retro`)

> Fusionada aquí el 2026-10-19 (LI-9). El procedimiento entero —estructura del informe, cómo se
> genera, voz, salida HTML y automatización— está en **`references/retro.md`**: léelo antes de
> escribir la retro.

Lo esencial, para decidir si es esto lo que toca:

1. **Recoge hechos, no impresiones**: `git log` de la semana, bloqueos de `.claude/PROGRESS.log`
   (`BLOQUEADO|BLOCKED`), aprendizajes nuevos. Sin métricas, la retro es opinión.
2. **Escribe el informe** con la estructura fija de la referencia (headline · métricas con su
   delta · qué fue bien · qué no, con commit o ruta · aprendizajes · decisiones · próxima semana ·
   bloqueos) en `.claude/memory/retros/YYYY-WW.md`.
3. **Sube una sola línea** a `MEMORY.md` (capa 3). El informe entero se queda en local.
4. **Voz**: honesta, concreta, sin emojis decorativos, y que apunte a una acción. Una semana mala no
   justifica un cambio estructural: mira la tendencia de 3+ semanas.

# §D · SUBIR LO APRENDIDO A `CLAUDE.md` (antes skill `weekly-review`)

> Fusionada aquí el 2026-10-19 (LI-9). Los pasos, los criterios de qué entra y qué no, y el formato
> del diff están en **`references/claude-md.md`**: léelo antes de proponer nada.

Lo que no se negocia:

1. **Nunca se edita `CLAUDE.md` sin enseñar el diff y tener el sí del Usuario.** Si no hay nada que
   subir, se dice, sin forzar cambios.
2. **Solo sube lo estable**: reglas que se repiten en varias sesiones, gotchas con workaround
   probado, decisiones ya implementadas, comandos que evitan romper algo. Lo efímero se queda en
   `.ai/memory.md`; lo pendiente, en `MEMORY.md`.
3. **A mitad de sesión no se aplica**: una edición de `CLAUDE.md` no rige hasta `/clear`, `/compact` o
   reiniciar; no rompe el caché (`rules/harness-gotchas.md` §Caché, corregido el 2026-10-20).
   Se deja el diff escrito y se aplica al arrancar la siguiente.
4. **Si la norma duele cuando se ignora, no es una línea de `CLAUDE.md`**: es un hook
   (`rules/layer-decision.md`).

## Related

- **`rules/memory.md`** — la arquitectura: qué capa es cada fichero, qué se guarda, qué no, los
  disparadores y los tres mecanismos que no existen. **Es el único sitio donde eso está escrito.**
- `references/claude-md.md` (§D) — lo estable sube a `CLAUDE.md`, con diff y confirmación del Usuario
- `references/retro.md` (§C) — el informe de la semana: mismas fuentes que §D, otro entregable
- `rules/self-improvement-loop.md` §5 — la poda del harness se engancha al cierre de §C/§D
- `rules/adr.md` — el formato de una decisión cara de revertir, antes de que llegue a `MEMORY.md`
- `_archive/2026-08-22/` — `boris-dream` (de donde salen las 4 fases), `sync-memory` (de donde sale
  §A), `boris-memory` y `memory-system`, con el porqué de cada retirada en su `README.md`
- `_archive/2026-10-19/skills/` — `retro` y `weekly-review` tal como eran antes de la fusión
  (§Sub-ola 1.04 del `README.md`)
