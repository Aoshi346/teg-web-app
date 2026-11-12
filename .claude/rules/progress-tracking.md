---
paths:
  - "PROGRESS.json"
  - ".claude/PROGRESS.log"
  - "**/pending-tasks.md"
  - ".claude/scripts/tasks_registry.py"
  - ".claude/scripts/progress_index.py"
  - ".claude/hooks/capture-task.sh"
---
# PROGRESS.json y PROGRESS.log — formato canónico

> **Cuándo aplicar:** en TODA sesión de trabajo (PROGRESS.json es obligatorio al inicio).
> Consolidada aquí desde CLAUDE.md (poda TPL-1, 2026-08-07). `PROGRESS.json` es la **única fuente
> de verdad de estado** para el Supervisor (`rules/governance.md` §4); el hook
> `validate-progress.sh` (SessionStart) avisa si falta.

## PROGRESS.json — obligatorio, en la raíz del proyecto

Crear AL INICIO de la sesión; actualizar EN VIVO (no en batch):

```json
{
  "task": "Nombre de la tarea principal",
  "status": "in_progress",
  "startedAt": "2026-03-27T09:00:00Z",
  "checklist": [
    {"id": 1, "item": "Analizar código actual", "done": false},
    {"id": 2, "item": "Implementar cambio X", "done": false},
    {"id": 3, "item": "Escribir tests", "done": false},
    {"id": 4, "item": "Verificar con screenshot", "done": false},
    {"id": 5, "item": "Commit y push", "done": false}
  ],
  "completedAt": null,
  "notes": []
}
```

- Marca `"done": true` al completar cada item; añade items si descubres más trabajo.
- Al terminar todo: `"status": "completed"` + `"completedAt"`.
- Si te bloqueas (decisión o recurso externo): `"status": "blocked"` y el porqué como última entrada
  de `notes`. Los valores que se usan: `in_progress` · `blocked` · `completed` (`done` cuenta igual).
- Al pasar a `completed` o `blocked`, el hook Stop `notify-telegram.sh` avisa por Telegram (DONE /
  BLOCKED con la última nota), una vez por estado; si el aviso no llega, lo dice en la sesión.
- Esto permite supervisión automática sin parsear logs: `cat PROGRESS.json | jq '{task,status}'`.

## `pending-tasks.md` — lo que ha PEDIDO el Usuario (automático)

Vive en el plan activo (`.docs/plans/<plan>/pending-tasks.md`) y lo escribe el hook
`capture-task.sh` en **cada** petición. Salvo con datos personales o de salud **reales en desarrollo**
(`datos_reales_desarrollo: si-…` en `CONFIGURACION.yaml`, sub-ola 2.29): ahí no escribe nada,
porque el prompt puede llevarlos, y `ensure_hooks.py` ni lo registra. **Es opt-in por proyecto (MO-19):** solo
registra donde `CONFIGURACION.yaml` trae `capture_task: si`; sin la clave, apagado. Antes de escribir tapa secretos,
correos, IBAN, DNI/NIE y teléfonos (`tasks_registry.redactar`), y **no escribe en un plan cerrado** (el que lleva un
fichero `.cerrado` en su carpeta): sin plan abierto, el destino es `pending-tasks.md` en la raíz. Donde está
encendido no hay que acordarse de nada: el hook corre siempre y además **reinyecta las pendientes** en el contexto
de cada turno.

**Por qué existe.** Palabras del Usuario: *«se te está olvidando todo, yo voy diciéndote cosas y se
van perdiendo»*. Y tenía razón: no había ningún sitio donde quedara escrita cada petición, así que
recordarlas dependía del agente entre veinte tareas — y eso falla siempre, no a veces.

**Es un hook y no una skill a propósito.** Una skill hay que acordarse de invocarla, que es el
mismo fallo otra vez (`rules/layer-decision.md`: si el coste de ignorarlo es alto, baja de capa).

| Estado | Significa |
|---|---|
| `[ ]` | pendiente |
| `[>]` | en curso |
| `[~]` | delegada a background — **con el id de la tarea** |
| `[x]` | hecha, con nota de qué se hizo |
| `[!]` | bloqueada o descartada, **con su razón** |

### Los DOS sitios, y no es redundancia

Toda petición del Usuario va **a los dos**, siempre — en este repo y en cualquier proyecto derivado:

| | Dónde se ve | Qué aporta | Qué le falta al otro |
|---|---|---|---|
| **`pending-tasks.md`** | el fichero, en el plan | **persiste entre sesiones**; lo abre una persona | los TODOs mueren con la conversación |
| **Tasks (`TaskCreate`)** | `Ctrl+T` en la terminal | se ve **mientras el agente trabaja**, sin abrir nada | el fichero hay que ir a mirarlo |

**Por eso los dos.** El fichero lo escribe el hook automáticamente; la tarea la crea el TL con
`TaskCreate` al ponerse con ella, y la cierra con `TaskUpdate` (`completed`). Si solo se hace uno
de los dos, se pierde justo la mitad que hacía falta: o no hay rastro mañana, o no se ve hoy.

⚠️ Las tools de Task **vienen desactivadas por defecto** en los modelos recientes. Se activan con
`CLAUDE_CODE_ENABLE_TODO_TOOLS=1` en el `env` de `settings.json`, y `ensure_hooks.py` lo asegura en
cada proyecto — porque `settings.json` no se copia con el template y ponerlo solo aquí no llegaba
a ninguna parte.

**Las tres obligaciones del TL:**

1. **Refinar** al ponerse con ella: el hook guarda el texto crudo (rápido y a prueba de fallos),
   pero una petición con erratas y tres cosas mezcladas se lee mal a los dos días.
   `tasks_registry.py refine <id> "<qué se pide, en claro>"` — conserva el original en un
   comentario, por si el refinado se equivoca.
2. **Marcar al terminar**, con nota: `done <id> --nota "<qué se hizo>"`.
3. **Nunca borrar una línea para "limpiar"**: una tarea que desaparece sin marcarse es una tarea
   perdida, que es justo lo que el fichero impide.

⚠️ **No confundir con `dashboard.md`**, que está en la misma carpeta: aquel son los items del
informe (los escribe el agente desde el análisis); éste son las peticiones del Usuario.

## PROGRESS.log — opcional (notas detalladas)

```
[YYYY-MM-DD HH:MM] TIPO: Descripción
```

Tipos: `INICIO | PROGRESO | BLOQUEADO | ERROR | FIN | NOTA | PLAN | PARALELIZACIÓN`.
El plan de una tarea grande va aquí con tag `[PLAN]` (archivos exactos + por qué + riesgo + orden).

**Lo automático va aparte, a `.claude/PROGRESS.auto.log`** (MO-37, 2026-10-21): la traza de
ficheros tocados (`hooks/auto-progress-log.sh`, `[AUTO] CATEGORÍA: ruta`, solo rutas del proyecto y
una por fichero y día) y las notas de `hooks/flag-visual-staleness.sh` (mapa visual o grafo
desfasados, una al día). Antes iban aquí y tapaban lo humano: en develop eran 143 de 143 líneas, en
fitapp 782 de 911. Las `[AUTO]` que ya estaban en un `PROGRESS.log` se quedan (no se reescribe):
para leer solo lo humano, `grep -v '\] \[AUTO\] ' .claude/PROGRESS.log | tail -30`. El auto log no
se propaga (`template_diff.py` lo salta, como este) y en el template no se versiona (`*.log` en su
`.gitignore`); en un derivado, compruébalo con `git check-ignore .claude/PROGRESS.auto.log` y, si sale
1, añade la ruta a su `.gitignore` (el 21-10 no lo ignoraban AMC, musa, cold_calling_coach ni risk-couple).

## Con SpecKit

El progreso granular vive en `tasks.md` de la sesión (checkboxes ` />x!` EN VIVO —
`rules/speckit-workflow.md` §SpecKit Progress Tracking, gate: `scripts/task_progress.py --gate`). PROGRESS.json
mantiene la vista de tarea/estado global; PROGRESS.log la actividad.

## Ejecutar una cola de tareas sin parar (antes skill `continue-tasking`)

> Fusionado aquí el 2026-10-19 (LI-9). La skill `continue-tasking` mandaba un `TASKS.md` en la
> raíz como **única** fuente de verdad, y eso contradecía la decisión del Usuario de arriba: las
> peticiones viven en `pending-tasks.md` del plan y se ven con Tasks. Lo que sigue es lo que valía
> de ella, adaptado a esas dos piezas. El original, con el porqué de lo que no se trasladó:
> `_archive/2026-10-19/skills/continue-tasking/` y `_archive/2026-10-19/README.md` §Sub-ola 1.04.

### Cuándo activar

- El Usuario dice "continúa", "sigue", "procede con las tareas".
  ⚠️ La frase sola **no carga** esta rule: entra solo por `paths:`, y `dispatch-hint.sh` no la detecta
  (`gen_agent_system.py --detect` calla, medido el 2026-10-19). Se llega desde `INDEX.md` (fila
  «Arrancar sesión / retomar») o al abrir el `pending-tasks.md` cuyas pendientes reinyecta `capture-task.sh`.
- Hay ≥3 pendientes `[ ]` en `pending-tasks.md`.
- Empieza una sesión de trabajo con un backlog conocido.

### Reglas core

1. **Cada tarea compleja → su sesión SpecKit** (cuándo lo es: `rules/governance.md` §1).
2. **Background-first**: ejecutar en background; el foreground solo coordina y mergea.
3. **La fuente de verdad son `pending-tasks.md` + Tasks** (arriba), no un `TASKS.md`: se actualizan
   antes y después de cada tarea.
4. **Un commit por tarea completada** — no agrupar trabajo de varias tareas en un solo commit.

### 2.bis Tabla de decisión — tamaño de task → modo de ejecución

| Tamaño | Criterio | Dónde | Agentes | SpecKit formal |
|---|---|---|---|---|
| **Pequeña** | <3 archivos · <30 líneas · 1-line fix · respuesta a pregunta | main tree, foreground inline | 0 | No |
| **Mediana** | 1 módulo · 1-2 endpoints · 1 componente · <5 archivos | main tree, 1 agente background | 1 background | Inline en prompt del agent |
| **Grande** | Multi-módulo · >5 archivos · nuevo feature UI+API+tests | main tree, 2 agentes secuenciales (Plan → Impl) | 2 background | Sí, archivos committeados |
| **Grande y arriesgada** | Toca models.py · migrations/ · settings.py · auth · refactor de stores · schema | worktree `worktrees/wt-<name>` branch `feature/<name>` | 2 background en el worktree | Sí, en el worktree |

**Por qué el worktree** en el cuarto caso:
- Aislamiento real: el main tree queda intocable hasta que el worktree esté verde
- Build + verify se corren dentro del worktree (dev server en puerto distinto)
- Si algo explota: `git worktree remove worktrees/wt-<name>` → 0 daño al main tree
- Merge a develop solo tras verify + `/simplify`

La rama existe **solo dentro del worktree** (`rules/code-style.md` §Branches: se trabaja en
`develop`); y borrar un worktree mergeado sigue pidiendo aprobación (`governance.md` §7).

**Cuándo NO hace falta worktree aunque sea grande:**
- Feature nueva totalmente aislada (nuevo endpoint que nadie llama + nuevo componente que nadie renderiza): main tree OK, riesgo = 0
- Refactor interno sin cambios de API ni UI: main tree OK

### Flujo de sesión

```
1. Leer pending-tasks.md (y Tasks, Ctrl+T) — ver estado actual
2. Identificar las [ ] → priorizar por dependencias
3. Marcarla [>] (foreground) o [~] con el id de la tarea (background) · TaskCreate
4. Crear SpecKit session si la tarea es compleja
5. Ejecutar
6. Verificar (tests + build + screenshots si UI)
7. Commitear con el id de la petición (T-NNN) en el mensaje
8. tasks_registry.py done <id> --nota "<qué se hizo>" · TaskUpdate completed
9. Continuar con la siguiente [ ]
```

### Template de prompt para agente background

```
Tarea: T-NNN — [Descripción]

Contexto del proyecto:
- Stack: [stack del proyecto]
- Branch actual: [branch]
- SpecKit session: [ID]/[nombre]

Tareas relacionadas:
- T-[M]: [descripción] → [estado]

Archivos afectados:
- [path/file1] — [qué cambiar]
- [path/file2] — [qué cambiar]

Pasos:
1. [paso 1]
2. [paso 2]
3. [paso 3]

Verificación:
- [ ] Tests pasan: pytest apps/[module]/ -v
- [ ] Build OK: [comando de build]
- [ ] No hay console errors
- [ ] Screenshot si hay UI: /tmp/task-N-verify.png

Al terminar:
- Commitea con rutas explícitas: git commit -m "feat([scope]): [descripción] — T-NNN" -- <ficheros>
- NO marques pending-tasks.md: lo marca el TL al recibir tu resultado (tasks_registry.py done)
- Devuelve: DONE T-NNN + resumen + la evidencia de la verificación
```

El aviso al Usuario lo da el TL por el canal que exista en la máquina (`CLAUDE.md` regla 4,
`rules/communication-fast-ack.md`), no el agente de background.

### Auto-decomposición — el TL es responsable del plan

El user dicta intención, el TL decide tamaño y descomposición según la tabla §2.bis:

- Si la task es **grande o multi-capa** → convertirla en Epic con sub-tareas (`T-NNN.a`, `T-NNN.b`)
- Cada sub-task se dispatch como background agent independiente con su propia SpecKit session
- El TL coordina dependencias (ej: T-097 depende de T-096 → secuencial)
- El TL **pregunta solo lo crítico** (decisiones de diseño irreversibles). Lo demás lo decide y documenta como "asumido X"

### 6.bis. Auto-trigger UX review — tasks que tocan UI

**Si la tarea modificó archivos en `frontend/src/**/*.tsx|jsx|css`**, pasos adicionales obligatorios
(para una wave entera con UI, el cierre es `/qa-loop`: `rules/qa-loop.md`):

1. **Verificación técnica**: correr `npm run typecheck && npm run build`
2. **Si pasa → revisión UX**: lanzar background agent:
   ```
   Eres el agente lidia-naive-tester.
   Persona: [persona naive del proyecto — peluquera, coach, contable...].
   Verifica la feature X de T-NNN.
   URL: [URL del proyecto]
   Lee primero .claude/agents/[persona]/memory.md para contexto histórico.
   Foco: ¿funciona? ¿se entiende? ¿algo regresionó?
   Duración máx: 8 min.
   Al terminar, actualiza la memoria via scripts/[persona]-diff.py
   ```
3. **Si naive-tester escala P0**: la tarea se reabre (`[>]` en `pending-tasks.md`) con nota y link al finding; NO se cierra hasta resolver
4. **Si OK** → hecha, incluir path del REPORT.md en el commit

**Cuándo NO lanzar auto-review:**
- Tasks de backend-only (sin cambios en `frontend/src/`)
- Tasks de infra/config (hooks, settings, migrations)
- Corrección de bugs que el tester ya reportó (el TL evalúa)
- Cuando el user dice explícitamente "sin test [persona]"

### 6.ter. Post-implementación Django OBLIGATORIO — antes de reportar DONE

**Cualquier task que añada/modifique modelos Django o apps DEBE correr antes de DONE** (el check de
migraciones pendientes también está en la skill `verification-loops`):

```bash
# 1. NO puede haber migraciones pendientes
cd backend && python manage.py showmigrations | grep "\[ \]" && echo "❌ PENDIENTES" || echo "✅"

# 2. Si añadiste nueva app Django (INSTALLED_APPS):
python manage.py migrate <app_name>

# 3. Si añadiste dep con migraciones (token_blacklist, axes, etc.):
python manage.py migrate <dep_name>

# 4. Smoke test post-migración:
curl -s -o /dev/null -w "%{http_code}\n" <URL>/api/v1/<endpoint>/   # → 401
curl -s -o /dev/null -w "%{http_code}\n" -X POST \
  -H "Content-Type: application/json" -d '{}' <URL>/api/v1/users/login/  # → 400
```

**Prohibido** marcar task como DONE si `showmigrations` tiene líneas `[ ]` o si el smoke test no pasa.

> Por qué: añadir app a INSTALLED_APPS sin correr migrate → login 500 → diagnóstico de 30+ min.

### 6.quater. Loop iterativo hasta objetivo (cuando el user lo activa)

**Cuándo aplicar:** tandas de tareas con una métrica objetivo medible (score Vera/Lidia, cobertura
tests, 0 P0s, accesibilidad AA%). Qué herramienta (`/goal`, `/loop`, workflow) lo decide
`rules/goal-vs-loop.md`; el QA de UI tiene su propio tope y su regla de parada en `rules/qa-loop.md`
§6 (3 iteraciones), que mandan sobre el default de aquí.

**Al recibir una tanda relacionada, el TL pregunta UNA vez:**
```
¿Cómo quieres que itere esta tanda?
- LOOP CONTINUO → sigo sin parar hasta cumplir condición. Te reporto cada iter pero NO espero tu OK.
- PAUSA POR ITER → reporto cada iter y ESPERO tu OK para continuar.
- NO LOOP → modo normal (una pasada, reporte, siguiente task).
```

**Definición del loop (si el user dice sí):**
1. **Métrica objetivo** — qué se mide (score rúbrica, cobertura %, 0 P0 restantes)
2. **Umbral de cierre** — cuándo parar (ej: ≥9.5 en ambos agentes, 0 P0s)
3. **Ciclo máximo** — cuántas iteraciones antes de pausar (default: 7)
4. **Agentes de validación** — naive-user, art director, pytest, etc.

**Loop por iteración:**
```
1. Lanzar fix agents en background (paralelo, sin conflicto de archivos)
2. Build + smoke test
3. Lanzar agentes de validación en paralelo
4. Consolidar scores en tasks.md scoreboard
5. Reportar al user (foreground, copy-paste):
   Iter N — Score previo → Score nuevo (+delta) | Commits: <hashes> | Blockers: <top 3> | Next: <qué ataca>
6. Si umbral cumplido → cerrar loop, pedir confirmación al user
7. Si no → siguiente iteración
```

**Reglas de corte automático:**
- **Stalled**: 2 iteraciones sin progreso (delta < 0.1) → pausar, triage con user. No gastar iteraciones a ciegas.
- **Regresión**: si métrica baja ≥0.3 vs iter previa → pausar
- **Ciclo N alcanzado sin umbral** → pausar, presentar scoreboard completo, dejar que user decida

## Anti-patterns

- ❌ Crear PROGRESS.json al final de la sesión "para cumplir" — nace al inicio o no sirve.
- ❌ Actualizarlo en batch al terminar — el Supervisor lo lee DURANTE la sesión.
- ❌ Estado en la conversación pero no en el JSON ("ya casi está") — si no está en el JSON, no existe.
- ❌ Llevar las tareas en un `TASKS.md` en la raíz (lo que mandaba `continue-tasking`) → dos fuentes
  de verdad, y la tarea acaba en la equivocada.
- ❌ Empezar una tarea de la cola sin marcarla primero (`[>]` o `[~]` con su id).
- ❌ Agrupar varias tareas en un solo commit.
- ❌ Usar foreground para todo (desperdiciar paralelismo).
- ❌ Reportar DONE sin verificar (ver `rules/verification.md` · skill `verification-loops`).
- ❌ Continuar si `bash .claude/hooks/check-ram.sh` no da vía libre (verificar antes de cada tarea).
- ❌ No correr `showmigrations` al añadir modelos Django (ver §6.ter).
- ❌ Lanzar loop iterativo sin umbral de cierre definido (loop infinito).
