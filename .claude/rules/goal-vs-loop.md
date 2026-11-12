---
paths:
  - ".claude/rules/goal-vs-loop.md"
---
# Autonomía: `/goal` vs `/loop` vs subagentes vs agent-teams

> **Cuándo aplicar:** antes de lanzar trabajo autónomo largo, elige el mecanismo correcto.
> Elegir mal cuesta tiempo (loop sin fin) o dinero (teams para algo trivial). Antes de lanzar
> **cualquier** loop, contesta las cinco preguntas (§Las cinco preguntas de todo loop). Para montar un
> `/loop` (sintaxis, criterio de parada, permisos, observabilidad): §`/loop` en detalle. Y al
> decidir si un item de un plan puede ejecutarse **sin supervisión** —un `/goal` o un `/loop` que
> arranca por la tarde y amanece hecho—: §Modo noche.
>
> **NO aplicar:** para saber si una **acción** concreta necesita aprobación — eso es `governance.md`
> §2, que sigue mandando de noche igual que de día · para el encargo de un refactor delegado, que
> tiene sus propios guardarraíles en `refactor-progresivo.md` §A5.
>
> **Relacionado:** `parallelization.md` (§Agent teams, §Sesiones que se hablan, §Pizarra) ·
> `governance.md` §2 y §3.1 · `verification.md` (la escalera de 4 niveles: el Stop hook de §N4 es su
> nivel 3) · `agent-autonomy-ladder.md` §4 · `agent-security.md` (ASI08, ASI10) · `report-kit.md`
> (el campo `nocturno:`) · `ram-pytest.md` · en el template, la skill `claude-code-referencia` §12
> (cómo se comportan `/loop`, `/goal`, el Stop hook y agent teams, con cada fuente y su comprobación).
>
> **Fusionada el 2026-10-20 (LI-28, sub-ola 1.06).** Aquí viven ahora las antiguas
> `loop-workflow.md` (§`/loop` en detalle) y `modo-noche.md` (§Modo noche). El porqué y lo que no se
> trasladó: `_archive/2026-10-19/README.md` §Sub-ola 1.06.
>
> **Puesta al día el 2026-10-21 (sub-ola 2.16; MO-30, MO-67, MO-68, MO-69).** Lo que dice de Claude
> Code sale de la doc oficial descargada el 2026-10-20 a las 23:29 UTC (`code.claude.com/docs/en/`
> `scheduled-tasks`, `goal`, `agents`, `hooks`; lista y sha256 en
> `_archive/2026-10-20/medicion-2.16/fuentes.txt`). Lo que la revisión corrigió: `/loop` **no** es el
> plugin `ralph-loop` y sus tareas caducan a los **7 días**, no a los 3; el tope de 8 del Stop hook
> se reinicia con cada llamada a una tool.

---

## Matriz de decisión

| Necesito… | Mecanismo | Por qué |
|-----------|-----------|---------|
| Trabajar hasta cumplir una **condición verificable** | **`/goal`** | Tras cada turno, **otro modelo** juzga si se cumple; se limpia sola al cumplirse |
| **Re-lanzar** un prompt periódicamente o por auto-ritmo (polling, vigilar una PR, un deploy) | **`/loop`** | Skill integrada: por reloj o al ritmo que elige Claude (1 min-1 h), solo con la sesión abierta; las recurrentes caducan a los 7 días |
| Vigilar un **log, un proceso o un CI** que va soltando líneas | La tool **Monitor** | Un script en segundo plano que le devuelve cada línea: no sondea, y la doc lo da por *a menudo* más eficiente y rápido que repetir un prompt |
| Que corra **sin la sesión abierta** (cada noche, cada hora) | Tarea programada **en la nube** (`/schedule`) o **de Desktop** | `/loop` muere con la terminal; la de la nube va sobre un clon nuevo, con intervalo mínimo de 1 h |
| Trabajo **paralelo independiente**, contexto aislado, sin diálogo | **Subagentes** / worktrees | Reportan al principal; no se hablan entre sí |
| **Varias tareas independientes** que lanzas tú y miras de vez en cuando | **Agent view** (`claude agents`, `claude --bg`) | Una pantalla con todas las sesiones de fondo; cada una que lanzas se mete en su worktree antes de editar (salvo excepciones: una sesión que mandas al fondo con `/background` o `←` sigue editando donde estaba, y una copia de `/fork` puede editar en el sitio). *Research preview* |
| Un **cambio grande** que se parte en trozos iguales (una migración a 200 ficheros) | **`/batch`** | Skill integrada: plan de 5 a 30 unidades y, tras aprobarlo, un subagente en su worktree por unidad. Es un uso empaquetado de subagentes, no otra forma; en casa, solo para migraciones mecánicas y tras `check-ram.sh --explain` (G9-14, decidido el 22-10: `governance.md` §3.1) |
| Trabajo paralelo que **necesita discutirse/desafiarse** entre agentes | **Agent teams** | Sesiones que se mensajean entre sí. Experimental, y **encenderlo cambia la delegación normal** (`parallelization.md` §Agent Teams) |
| Orquestación multi-agente **determinista y repetible** (review/migración/research a escala) | **Workflows** | Script JS que tú controlas; igual cada run, resumible. Ver skill `workflow-creator` |
| Un **flujo de tareas durante días**, que siga con tu máquina apagada | **Projects** (claude.ai/code o Desktop) | Una conversación que abre hilos en paralelo, casi siempre en la nube. Beta pública en Pro y Max; no en Team ni Enterprise |
| Que **dos sesiones tuyas** se enteren de algo | Mensajes entre sesiones | `parallelization.md` §Sesiones que se hablan |

**Las cinco formas oficiales** de llevar varias tareas a la vez son subagentes, agent view, agent
teams, dynamic workflows y Projects; worktrees, mensajes entre sesiones y `/batch` las apoyan, pero
no son una forma más (doc `agents`, 2026-10-20). Los comandos de sesión que las rodean (`--bg`,
`claude agents`, `/fork`, `/subtask`, `/branch`) están en `harness-gotchas.md` §Los comandos del harness.

**Anchura frente a profundidad (criterio de casa).** Un workflow da **anchura** —lo que no cabe en un
contexto, piezas independientes, decenas o cientos de agentes por ejecución con el plan en el
script (doc `workflows` §When to use a workflow)— y `/goal` da **profundidad**: una sesión larga que no
se desvía porque otro modelo comprueba la condición tras cada turno. Se combinan: cada trabajador de
un workflow con su propia condición de parada. La idea sale de un artículo de opinión (*Dynamic
Workflows vs /goal*, 04-06-2026, revisión integral `r2-medium-jev.md` §A6) que tiene dos errores de
hecho; lo que se adopta es la distinción, sostenida por la doc, no el artículo.

---

## Las cinco preguntas de todo loop — antes de lanzarlo

Un loop sin condición verificable no sabe cuándo parar, y uno que se revisa a sí mismo da por bueno
su propio error. Antes de lanzar un `/goal`, un `/loop`, un `ralph-loop`, un workflow con
«repite hasta» o una tarea programada, se contestan **las cinco**, por escrito en el encargo o en
`PROGRESS.log`. Fuente: *Loop Engineering in Practice* (Rezvani, 14-09-2026), en el resumen del
Usuario (revisión integral, `research/articulos-usuario.md` fila 01); el cruce con el template es de casa.

| # | Pregunta | Qué tiene que contestar | Si no tiene respuesta |
|---|---|---|---|
| 1 | **¿Qué lo arranca?** | Un intervalo (`/loop 10m`), el fin de cada turno (`/goal`, un Stop hook), un evento (Monitor, channels), una hora (tarea programada) o una persona | No es un loop: es una tarea, y se hace una vez |
| 2 | **¿Cuál es la condición verificable de «hecho»?** | Un comando que sale con 0, un contador que llega a cero, `task_progress.py --gate` en verde. En `/goal`, algo que el agente **muestre en la conversación** | No se lanza. Un loop sin parada es un despertador, no un criterio |
| 3 | **¿Quién revisa?** | **Nunca el mismo agente que hizo el trabajo**: un gate determinista, el evaluador de `/goal`, un subagente verificador con contexto limpio y el material crudo delante, o una persona | Se da por bueno a sí mismo y entrega lo equivocado bien testeado |
| 4 | **¿Qué recuerda entre vueltas?** | El estado **en disco**: `PROGRESS.json`, `tasks.md`, el commit, un fichero de la pizarra. Nunca «lo que recuerde la conversación» (se compacta, y un `/loop` reanudado a ritmo propio no vuelve solo) | Cada vuelta redescubre lo mismo o repite lo ya hecho |
| 5 | **¿Qué toca, y con qué permisos?** | Los ficheros o directorios previstos (claims, `parallelization.md` §file claims) y el modo de permisos o la allowlist con que corre | O se para a pedir permiso en cada tool, o —peor— no se para donde debía |

### Uno hace, otro comprueba

La pregunta 3 es la que más se salta, porque «el agente ya corre los tests» parece revisión y no lo
es: corre **sus** tests contra **su** interpretación. Lo que sí cuenta como otro:

- **`/goal`**: lo decide un modelo distinto del que trabaja —*"completion is decided by a fresh model
  rather than the one doing the work"* (doc `goal`)—, pero solo sobre lo que el agente enseñó.
- **Un Stop hook determinista** (`verification.md` nivel 3): un script, no una opinión.
- **Un subagente verificador** (`verification.md` nivel 4) que recibe el diff y los ficheros, no la
  conclusión del otro — si solo recibe la conclusión, es un eco (§Nivel 4, segundo caveat).
- **`/qa-loop`**: los auditores nunca son quienes arreglan (`qa-loop.md` §1b).

---

## `/goal` — trabajar hasta una meta verificable

`/goal` (built-in, **v2.1.139+**) fija una condición de finalización y Claude sigue trabajando
turno tras turno hasta cumplirla, entonces se **auto-limpia**. Tras cada turno, un modelo pequeño y
rápido lee la condición y la conversación y devuelve *no cumplida* (sigue, con la razón como guía),
*cumplida* (se limpia) o *imposible* (se limpia y lo registra). Fuente: doc `goal` (2026-10-20).

- **Úsalo para**: migrar un módulo hasta que todos los call sites compilen y los tests pasen;
  implementar un design doc hasta que se cumplan todos los criterios de aceptación; vaciar una
  cola de issues etiquetados; partir un fichero grande hasta que cada parte baje de X líneas.
- **Clave**: el evaluador juzga **sobre lo que Claude muestra en la conversación** — no ejecuta
  comandos ni lee ficheros por su cuenta. Escribe la condición como algo que el propio output de
  Claude pueda **demostrar** ("los 42 tests de `apps/x` salen verdes y lo pego").
  Fuente: https://code.claude.com/docs/en/goal

```
/goal Migra apps/billing al nuevo cliente de pagos hasta que pytest apps/billing/ -v salga 100% verde
```

### La condición: estado final, comprobación, lo que no se toca y el tope

La de arriba funciona, pero le faltan dos cosas que la doc recomienda y que en un run largo deciden:
**qué no puede cambiar** por el camino y **cuándo rendirse**. Una condición que aguanta muchos turnos
lleva cuatro piezas (doc `goal` §Write an effective condition):

| Pieza | Ejemplo | Sin ella |
|---|---|---|
| **Un estado final medible** | «`pytest apps/billing/` sale 100 % verde» | El evaluador no tiene con qué decir «cumplida» |
| **Cómo se comprueba, dicho** | «…y pegas la salida» · «`npm test` sale con 0» · «`git status` limpio» | Juzga una afirmación del agente, no una salida |
| **Lo que no puede cambiar** | «sin tocar ningún fichero de `tests/`» · «sin `--no-verify`» | La forma más corta de poner verde un test es cambiar el test |
| **El tope** | «o para tras 20 turnos» | Puede girar mientras el evaluador vea progreso |

```
/goal pytest apps/billing/ -v sale 100% verde y pegas la salida; no se modifica ningún fichero de
      apps/billing/tests/ ni se marca nada como skip; o para tras 20 turnos
```

La condición admite hasta **4.000 caracteres**, y el tope es una cláusula más: el agente informa de
cuánto lleva y el evaluador lo juzga desde la conversación (doc `goal` §Write an effective condition).

### Lo que hay que saber antes de dejarlo solo

- **No cambia el modo de permisos.** En Manual sigue preguntando antes de cada tool no permitida;
  para que corra desatendido, en auto mode. Se complementan: *auto mode* aprueba las tools dentro de un
  turno pero no abre otro; `/goal` abre turnos pero no aprueba tools (doc `goal` §Set a goal,
  §Compare ways to keep a session running). Lo que ningún modo aprueba solo sigue siendo
  `governance.md` §2.
- **En `claude -p` corre entero en una invocación**: `claude -p "/goal <condición>"`. Con la salida
  por defecto parece colgado hasta el final; `--output-format stream-json --verbose` lo enseña
  avanzar, y Ctrl+C lo para (doc `goal` §Run non-interactively). Es la capa 5 de `governance.md` §6:
  la monta solo el rol técnico, porque gasta sin nadie mirando.
- **Por dentro es un Stop hook de tipo prompt, de sesión**, y **convive con los Stop hooks que
  tenga `settings.json`** (`/hooks` los lista): todos disparan al final de cada turno (doc `goal`
  §How evaluation works, `hooks` §Stop). Si alguno bloquea, sus continuaciones cuentan para el
  mismo tope de ocho (§N4). Por eso `/goal` no está disponible
  sin confianza en la carpeta, con `disableAllHooks` o con `allowManagedHooksOnly` (doc `goal`
  §Requirements).
- **El evaluador es el modelo pequeño y rápido** configurado. `ANTHROPIC_DEFAULT_HAIKU_MODEL` lo
  cambia, y cambia **también** el alias `haiku` y las tareas de fondo (resúmenes): no se toca solo
  para `/goal` (doc `goal` §Evaluation model and cost).
- **Para solo** cuando se cumple, cuando el evaluador la juzga imposible, o si un turno falla por un
  error que tienes que arreglar tú (credenciales, saldo, ventana que no compacta, modelo no
  disponible). Otros errores reintentan o la pausan. Y si el agente contesta al evaluador **sin usar
  tools** varios turnos seguidos, Claude Code corta el bucle y te devuelve el control con la meta
  puesta (doc `goal` §How evaluation works, §When a turn fails).
- **Subagentes o shells en segundo plano aplazan la evaluación**; a los 30 minutos de espera hay un
  *check-in* (`CLAUDE_CODE_GOAL_CHECKIN_MINUTES`; `0` lo apaga) (doc `goal` §Background work defers evaluation).
- Una meta por sesión. `/goal` sin argumento da el estado (condición, turnos, tokens, última razón),
  `/goal clear` la quita y `/clear` también; al reanudar la sesión, vuelve la meta con los contadores
  a cero (doc `goal` §Use /goal).

## `/loop` — repetir o vigilar hasta criterio de parada

`/loop` es una **skill integrada** de Claude Code (v2.1.71+), **no el plugin `ralph-loop`**:
re-lanza un prompt por intervalo fijo (`/loop 5m …`) o al ritmo que elige Claude tras cada vuelta
(entre 1 minuto y 1 hora). **No converge solo**: define siempre un criterio de parada. Las tareas
recurrentes **caducan a los 7 días** —disparan una última vez y se borran— y solo corren con la
sesión abierta y ociosa (doc `scheduled-tasks` §Seven-day expiry, §Limitations). Requiere permisos
pre-aprobados en settings. Detalle completo: §`/loop` en detalle (abajo).

```
/loop "Comprueba si el deploy terminó; si sí, escribe DONE y para"
```

(Sin intervalo, a propósito: a ritmo propio Claude puede terminar el loop solo, así que «escribe DONE
y para» funciona. Con intervalo fijo —`/loop 60s …`, que además se redondea al minuto— seguiría
disparando hasta que lo canceles: §Criterios de parada.)

## Regla rápida

> ¿Hay un **estado final comprobable**? → `/goal`.
> ¿Es **repetir/vigilar** sin fin natural? → `/loop` (y si es un log o un proceso, Monitor).
> ¿Tiene que correr **sin la sesión abierta**? → tarea programada (nube o Desktop).
> ¿Es **paralelo sin diálogo**? → subagentes/worktrees (o agent view, si lo lanzas y vigilas tú).
> ¿Es **paralelo con diálogo**? → agent-teams.
> Y antes de cualquiera: **las cinco preguntas**.

---

## Anti-patterns

- ❌ `/loop` para algo con meta verificable → usa `/goal` (el loop no sabe cuándo parar).
- ❌ `/goal` con una condición que Claude no puede demostrar en la conversación (p.ej. "cuando el
  servidor de prod esté sano" sin que Claude lo muestre) → el evaluador no puede juzgarla.
- ❌ `/goal` sin tope ni restricciones → puede «cumplir» cambiando el test o girar mientras vea
  progreso; lleva siempre «sin tocar X» y «o para tras N turnos».
- ❌ `/loop` sin criterio de parada → corre hasta caducar a los 7 días (y eso es un despertador, no
  una parada).
- ❌ Contar con que un `/loop` siga con la terminal cerrada → se para; mandar la sesión al fondo
  (`/background` o `←`) se lo lleva a una sesión de fondo, y lo que deba correr sin ti es una tarea
  programada.
- ❌ Escribir que `/loop` «expira a los 3 días» o que «es el plugin `ralph-loop`» → las dos cosas son
  falsas (MO-30); `ralph-loop` es otro comando, con otro mecanismo (§`/loop` en detalle).
- ❌ Lanzar un loop sin haber contestado las cinco preguntas, o con un revisor que es el mismo agente.
- ❌ Usar agent-teams cuando un `/goal` en una sola sesión basta (overhead innecesario).

---

## `/loop` en detalle

*Antes `rules/loop-workflow.md`.* **Cuándo:** tareas repetitivas largas, waves de SpecKit sin
decisiones de negocio, polling de estado, batch operations. **No:** tareas con decisiones de diseño
frecuentes, cuando el resultado de un paso cambia el siguiente.

> Corregido el 2026-10-21 (MO-30, sub-ola 2.16), con la doc `scheduled-tasks` del 2026-10-20: esta
> sección describía el plugin `ralph-loop` con el nombre de `/loop` y decía que caducaba a los 3 días.
> Ni una cosa ni la otra: los dos mecanismos están ahora separados aquí abajo.

### Qué es `/loop`

`/loop` es una **skill integrada** (*bundled skill*) que programa el prompt con las tools de cron de
la sesión (`CronCreate`, `CronList`, `CronDelete`). Lo que le das decide cómo se comporta:

| Le das | Ejemplo | Qué hace |
|---|---|---|
| Intervalo y prompt | `/loop 5m comprueba el deploy` | Lo pasa a una expresión cron y lo repite a ese ritmo |
| Solo el prompt | `/loop comprueba el deploy` | Claude elige tras cada vuelta cuánto esperar (1 min-1 h) y dice por qué |
| Nada, o solo el intervalo | `/loop` | Corre el prompt de mantenimiento integrado (seguir lo inacabado, cuidar la PR de la rama, limpieza), o tu `loop.md` del `.claude/` del proyecto si existe |

Cada iteración de un `/loop` bien escrito:
1. Lee el estado actual del proyecto (en disco: pregunta 4)
2. Ejecuta trabajo
3. Commitea / actualiza PROGRESS.json
4. Se vuelve a disparar al siguiente intervalo —o a la espera que elige Claude— hasta que se cumple el
   criterio de parada, lo cancelas o caduca a los 7 días

**No es el plugin `ralph-loop`.** Ese plugin (`/ralph-loop:ralph-loop`, marketplace
`claude-plugins-official`) es un **Stop hook**: cuando Claude intenta terminar el turno, le devuelve
el **mismo prompt**, hasta que escribe la frase de `--completion-promise` o se llega a
`--max-iterations`. No va por reloj ni caduca; su único tope es `--max-iterations` (medido en el
plugin instalado, 2026-10-21: sus ficheros no hablan de días, horas ni caducidad).

| | `/loop` (integrado) | `/ralph-loop:ralph-loop` (plugin) |
|---|---|---|
| Qué dispara la vuelta | El reloj (cron) o la espera que elige Claude | Que Claude intente terminar el turno (Stop hook) |
| Cómo para | `Esc`, cancelarlo, Claude lo da por hecho (a ritmo propio) o 7 días | La frase de `--completion-promise` o `--max-iterations` |
| Sin parada explícita | Caduca a los 7 días | No para nunca: **siempre** `--max-iterations` |
| Para qué | Vigilar, sondear, repasar algo cada X | Iterar sobre la misma tarea hasta que salga |

**Diferencia clave vs `--permission-mode=dontAsk`:**
- `dontAsk` = no pregunta nunca: **deniega** toda tool que habría pedido permiso (solo pasa lo
  pre-aprobado), y no se re-lanza
- `/loop` = se vuelve a disparar en cada ciclo, con el modo de permisos de la sesión

### Instalación

```bash
# /loop viene con Claude Code (skill integrada desde la v2.1.71): no se instala.
# Si no aparece, mira si CLAUDE_CODE_DISABLE_CRON=1 está en el entorno o en settings: apaga /loop
# y las tools de cron, y lo ya programado deja de dispararse.

# El plugin ralph-loop es OTRA cosa (/ralph-loop:ralph-loop) y ese sí se instala:
# /plugin install ralph-loop@claude-plugins-official
```

### Sintaxis

```bash
# Con intervalo fijo (unidades s, m, h, d; los segundos se redondean al minuto, y un intervalo
# que no casa con cron —7m, 90m— se redondea al más cercano, avisando)
/loop 5m /siguiente estado   # cada 5 minutos: rama, cambios, RAM (antes /status)
/loop 30s /check-build    # /check-build es un ejemplo; 30s corre cada minuto

# Auto-pacing (el modelo decide cuándo re-lanzarse, entre 1 min y 1 h)
/loop /my-task-prompt

# Con prompt inline
/loop "Continúa implementando la Wave 2 de BM-POLISH-1 hasta completar todas las tareas de tasks.md"
```

Una skill como prompt solo se ejecuta si Claude puede invocarla sola: las de
`disable-model-invocation: true` (**`/verify` incluida**) y los comandos integrados (`/clear`,
`/model`…) le llegan como texto plano (doc `scheduled-tasks` §Run a prompt repeatedly with /loop).
Y el último ejemplo, «hasta completar todas las tareas», tiene meta verificable: es mejor un `/goal`
(abajo).

### Casos de uso en SpecKit

#### Wave de backend larga (no interactiva)

Tiene estado final comprobable —todas las tareas de la wave en `[x]` con su test— así que es un
`/goal`, no un `/loop`. El texto de la wave es el mismo; lo que cambia es quién decide que terminó:

```bash
/goal "
Lee .specify/sessions/BM-POLISH-1*/tasks.md.
Ejecuta las tareas pendientes de Wave 2 (backend only).
Para cada tarea:
1. Verifica RAM (bash .claude/hooks/check-ram.sh — en verde o no corras tests)
2. Implementa el cambio
3. Escribe tests con pytest backend/apps/[app]/ -v
4. Marca la tarea como [x] en tasks.md
5. Commitea con mensaje descriptivo
Cuando todas las tareas de Wave 2 estén [x], escribe DONE en PROGRESS.log.
Hecho cuando: python3 .claude/scripts/task_progress.py <tasks.md> --gate sale con 0 y pegas la
salida; sin tocar tareas de otras waves; o para tras 30 turnos y escribe BLOCKED en PROGRESS.log.
"
```

Si de verdad quieres que la misma instrucción se repita entera en cada vuelta, eso es el plugin:
`/ralph-loop:ralph-loop "<el mismo texto>" --completion-promise "DONE" --max-iterations 20`.

#### Polling de estado de build

```bash
/loop 60s "
Comprueba si el servidor Django está corriendo (ps aux | grep manage.py).
Si no está corriendo, intenta iniciarlo.
Actualiza PROGRESS.json con el estado.
Si lleva >10 minutos sin arrancar, escribe BLOCKED en PROGRESS.log y para.
"
```

(Con intervalo fijo, «y para» no cancela la tarea: el loop sigue disparando cada minuto hasta que lo
canceles. Si quieres que Claude pueda pararlo, quita el intervalo y deja que marque el ritmo; y si
lo que vigilas es un log o un proceso, pídele la tool Monitor en vez de un `/loop`.)

#### Batch de migraciones

```bash
/loop "
Lista los archivos de migración pendientes en backend/apps/*/migrations/ que no tienen reversa.
Para cada uno, verifica que tiene un método `reverse_sql` o `atomic = False` si hace schema changes.
Añade los que faltan. Commitea cada cambio. Para cuando no queden pendientes.
"
```

(«Para cuando no queden pendientes» es una condición verificable: también encaja como `/goal`, con
el comando que lista las pendientes como comprobación y «o para tras N turnos». Como `/loop` a ritmo
propio funciona porque Claude puede terminarlo solo, pero nadie más que él decide que terminó.)

### Criterios de parada

Un `/loop` para cuando:
1. **Lo cancelas**: `Esc` si es a ritmo propio y está esperando (borra el próximo disparo); las
   tareas que pediste en lenguaje natural se cancelan pidiéndolo («cancela el check del deploy»)
   o con `CronDelete` — `Esc` no las toca
2. **Claude lo da por terminado** (solo a ritmo propio): llama a `ScheduleWakeup` con `stop: true`.
   Si una vuelta acaba sin reprogramar ni parar, queda un despertar de reserva a ~20 minutos, y si
   ese tampoco reprograma, el loop termina
3. **Caduca**: las recurrentes, a los **7 días** de crearlas (disparan una última vez)
4. **Se cierra la sesión**: cerrar la terminal lo para; tras `/background` (o `←`), sigue en la sesión
   de fondo, y desconectarse de una sesión de fondo no la para ni detiene su `/loop` (doc
   `agent-view` §Attach to a session). Qué pasa con un `/loop` en una sesión arrancada con
   `claude --bg`, no está comprobado

Lo que **no** es un criterio de parada de `/loop`: «la frase de parada configurada» y «el límite de
iteraciones» son opciones del plugin `ralph-loop` (`--completion-promise`, `--max-iterations`), no de
`/loop`. Con `/loop`, la frase que escribe el agente solo para si es a ritmo propio y él decide no
reprogramar. Fuente de los cuatro: doc `scheduled-tasks` §Stop a loop, §Seven-day expiry,
§Limitations (2026-10-20).

**Importante:** las tareas recurrentes caducan a los **7 días**, no antes ni después, si no se
interrumpen. Siempre incluir un criterio de parada explícito en el prompt. Y dos cosas que no se
ven: el desfase (*jitter*) retrasa cada disparo hasta la mitad del intervalo, con un máximo de 30
minutos (el de cada 5 minutos no se retrasa), y una hora que pasa con Claude ocupado se dispara una
sola vez al quedar libre, no una por cada intervalo perdido (doc `scheduled-tasks` §How late a
recurring task runs, §Limitations).

### Settings.json — Auto-mode en loop

Para que el loop funcione sin interrupciones, el settings.json debe tener los permisos necesarios
pre-aprobados (`/loop` hereda el modo de permisos de la sesión; doc `scheduled-tasks` §Compare
scheduling options):

```json
{
  "permissions": {
    "allow": [
      "Edit(**)",
      "Write(**)",
      "Bash(git add*)",
      "Bash(git commit*)",
      "Bash(pytest backend/apps/* -v*)",
      "Bash(cd frontend && npm run build*)"
    ]
  }
}
```

Sin estos permisos, el loop se detendrá pidiendo confirmación en cada tool use.

### Observabilidad durante el loop

```bash
# En otra terminal, ver progreso en tiempo real:
watch -n 3 '
  echo "=== PROGRESS ===" && jq -r ".task + \" [\" + .status + \"]\"" PROGRESS.json
  echo "=== LOG ===" && tail -8 .claude/PROGRESS.log
  echo "=== TASKS ===" && grep -E "^\- \[.\]" .specify/sessions/BM-*/tasks.md 2>/dev/null | tail -10
'
```

O usar `scripts/monitor-agent.sh` si existe en el proyecto. Dentro de la sesión, «¿qué tareas
programadas tengo?» lista las de cron con su id y su próximo disparo (`CronList`, con `next run` desde
la v2.1.299), y `/tasks` lo que corre en segundo plano.

### Anti-patterns del loop

- ❌ Loop sin criterio de parada → corre hasta caducar a los 7 días (`/loop`) o no para nunca
  (`ralph-loop` sin `--max-iterations`)
- ❌ Loop sin permisos pre-aprobados → se detiene pidiendo confirmación
- ❌ Loop en tareas que requieren decisión del Usuario → usar human-in-the-loop de SpecKit
- ❌ Loop durante sesión con caché activo sin `/compact` previo → context pollution
- ❌ `/loop` cada minuto para leer un log → la tool Monitor, que no sondea
- ❌ Copiar el `scheduled_tasks.json` de `.claude/` (lo escribe Claude Code cuando la obtención de feature
  flags está apagada) a otro worktree esperando que corran allí → se listan pero no se ejecutan; se
  crean de nuevo en esa carpeta (doc `scheduled-tasks` §Limitations)
- ✅ Hacer `/compact` antes de iniciar un loop largo
- ✅ Incluir siempre criterio de parada explícito en el prompt

### Integración con SpecKit

En `tasks.md`, marcar qué waves son aptas para loop:

```markdown
## Wave 2 — Backend (loop-compatible ✅)
- [ ] Implementar endpoint /api/ai-office/agent-hook/
- [ ] Tests unitarios
- [ ] Migración si aplica

## Wave 3 — Frontend + UX (requiere review 👁️)
- [ ] Componente AgentStatusBadge
- [ ] Integración WebSocket
```

Waves marcadas como `loop-compatible` → lanzar sin supervisión, con `/goal` (lo normal: una wave
tiene estado final) o `/loop` si es vigilancia.
Waves con `requiere review` → ejecutar manualmente con aprobación del Supervisor.

---

## Modo noche — qué se puede dejar corriendo sin nadie mirando

*Antes `rules/modo-noche.md`.* **Cuándo:** al decidir si un item de un plan puede ejecutarse **sin
supervisión** — un `/goal` o un `/loop` que arranca por la tarde y amanece hecho. Define los
criterios de elegibilidad (§N2), lo que **nunca** lo es (§N3), el aparejo mínimo que hay que montar
antes de irse (§N4) y qué se mira por la mañana (§N5). La marca vive en el campo **`nocturno:`** del
report-kit, así que se decide **item por item, en el informe**, no de una vez para todo el plan.
**No:** para elegir el mecanismo (`/goal` vs `/loop` vs subagentes vs teams) — eso es la matriz de
arriba · para saber si una **acción** concreta necesita aprobación (`governance.md` §2) · para el
encargo de un refactor delegado (`refactor-progresivo.md` §A5, el caso particular del refactor
nocturno). **Relacionado:** `agent-autonomy-ladder.md` §4 (lo que no se delega en ningún horario) ·
`agent-security.md` (ASI08 fallos en cascada, ASI10 agentes sueltos) · `report-kit.md` (el campo
`nocturno:` y su badge) · `ram-pytest.md` (el gate que sigue vivo de madrugada).

### N1. La pregunta, y por qué se responde item por item

Un plan no es "nocturno" o "diurno". Dentro del mismo plan conviven una migración de sintaxis a 40
ficheros —que un agente hace mejor que tú a las tres de la mañana— y la decisión de cuánto cobrar
por el plan Pro, que no debería tocar ningún agente a ninguna hora. Marcar el plan entero es lo que
produce las dos malas noches: la que no se aprovecha, y la que amanece con trabajo que hay que tirar.

Por eso la marca es **por item** (`nocturno: si|no|revisar` + razón), y por eso la razón importa
tanto como el valor: al mes nadie recuerda si aquel `si` fue una decisión o un descuido.

> **`si` no significa "seguro". Significa "el coste de que salga mal es asumible y comprobable por
> la mañana".** Nada de lo que hay aquí garantiza que el trabajo esté bien: garantiza que sabrás
> si lo está.

### N1b. La precondición que lo cambia todo: documentación completa = noche posible

**Petición del Usuario, 2026-09-12:** *«cuando todo esté completo y ya se ponga a programar, ya no
tenga que preguntar nada más […] no tiene que haber ningún hueco libre, y que sea solo programar
para yo dejarlo toda la noche. La parte activa es poner toda esta documentación […] y toda la parte
de código ya sea totalmente automática, aplicando el QA loop.»*

Eso reordena esta sección entera, y para mejor. Hasta aquí, «¿esto es nocturno?» se contestaba item
por item con los cinco criterios de §N2. Sigue siendo así, **pero ahora hay una precondición que se
mide sola** y que decide la mitad de las respuestas antes de mirar el item:

> **Un item solo puede ser nocturno si el arranque está cerrado.** Lo que hace que un agente pregunte
> a las tres de la mañana no es su autonomía: es un hueco en la documentación. Sin PRD, sin
> requisitos con su Gherkin, sin modelo de datos y sin diseño decidido, **cualquier** tarea acaba
> topándose con una decisión que no es suya, y entonces o para (y pierdes la noche) o improvisa (y
> pierdes la confianza en el lote).

**Se comprueba, no se supone:**

```bash
python3 .claude/scripts/gate_arranque.py .   # exit 0 · los documentos base están y no son la plantilla
python3 .claude/scripts/flow_state.py .      # exit 0 · los gates del flujo, en verde
```

| Los dos en verde | Alguno en rojo |
|---|---|
| Los criterios de §N2 deciden item por item | **Nada es nocturno todavía.** El trabajo de la noche es cerrar el arranque, y ese sí exige a una persona: son preguntas |
| El QA loop puede correr al cierre sin nadie delante | Un QA loop sobre algo sin criterios de aceptación mide contra nada |

**El corolario que más ahorra, y es el que pidió el Usuario:** la parte cara y despierta es
**escribir la documentación**; la parte barata y desatendida es **ejecutarla**. Invertir una tarde en
`/arrancar` y en el diseño no retrasa el proyecto — es lo que convierte las noches siguientes en
tiempo de trabajo en vez de en tiempo de espera.

⚠️ **Y el límite, dicho antes de que nadie se confíe:** que el gate esté verde significa que los
documentos **existen, tienen contenido propio y están firmados**. No significa que sean correctos —
lo dice el propio `gate_arranque.py` en su cabecera. Un PRD impecable y equivocado deja pasar la
noche igual, y por la mañana habrá cuarenta commits construyendo lo que no era.

### N2. Los cinco criterios — hacen falta **los cinco**

| # | Criterio | La pregunta concreta |
|---|---|---|
| 1 | **Meta verificable por el propio agente** | ¿Puede el agente *demostrar en la conversación* que terminó? Un comando que sale verde, un contador que llega a cero. Si el criterio de "hecho" es "cuando quede bien", no es nocturno |
| 2 | **Gate determinista** | ¿Hay un script con exit ≠ 0 que decide? No una valoración del modelo sobre sí mismo (`verification.md` nivel 3) |
| 3 | **Reversible** | Si sale mal, ¿se deshace con `git checkout`? Lo que toca datos reales, servicios externos o dinero, no |
| 4 | **Sin decisión de negocio ni de producto** | Precios, alcance, contratos de API públicos, texto que ve un cliente: eso es de `governance.md` §2 y de una persona |
| 5 | **El fallo sería ruidoso, no silencioso** | ¿Te enterarías por la mañana? Un backfill que corrompe el 3% de las filas, un cambio de umbral, un texto que sale a cliente: fallan callando, y eso los descalifica aunque cumplan los otros cuatro |

**Cruce con `governance.md` §3.1** (autonomía por tipo de tarea), que es donde está el mejor
predictor: lo **mecánico y verificable** casi siempre cumple los cinco; lo **semi-mecánico** suele
ser `revisar`; la **lógica nueva** es `no` por definición.

Y el límite honesto que ya dice `refactor-progresivo.md` §A1: **sin tests que cubran lo que temes,
la tarea no es verificable por mecánica que parezca.** El guardarraíl es el test, no la etiqueta.
Antes de marcar `si` en algo que se apoya en una suite, comprueba que esa suite **falla** cuando
rompes una línea a propósito; una suite que nunca se ha visto en rojo no es una red.

### N3. Lo que NUNCA es nocturno

- Cualquier acción de la lista de aprobación de `governance.md` §2 — **el horario no la relaja; al
  contrario, es cuando más barato sale saltársela**: deploy a producción, migraciones destructivas,
  merge a `main`, dependencias del sistema, gasto externo, reescritura de historia.
- Las tres clases no delegables de `agent-autonomy-ladder.md` §4: datos confidenciales, urgencias
  sin tiempo de verificar, y riesgo alto con un agente sin rodaje.
- Un agente **estrenándose**. Un `si` presupone historial; el primer run de un agente nuevo se mira.
- Lo que **nadie ha hecho nunca a mano**. Si no sabes cómo se hace despierto, no sabes qué mirar
  por la mañana.
- Un item cuyo gate **no se ha probado**. Un gate que no has visto fallar no es un gate.

### N4. El aparejo mínimo, antes de irse

1. **Criterio de parada explícito.** `/goal` con una condición demostrable en la propia
   conversación, con restricciones y tope («o para tras N turnos»); `/loop` **siempre** con condición
   de salida (sus recurrentes caducan solas a los 7 días, y eso no es un criterio de parada, es un
   despertador). Y un `/loop` **solo corre con la sesión abierta**: para la noche, la sesión va en
   segundo plano con `/background` o el trabajo es una tarea programada. Detalle: arriba (matriz y
   §`/loop` en detalle).
2. **Stop hook determinista** que impida cerrar el turno con el trabajo a medias —
   `verification.md` nivel 3. ⚠️ **Con su límite escrito: el harness anula el hook tras 8 bloqueos
   consecutivos y termina igual — pero el contador vuelve a cero cada vez que el agente llama a una
   tool** (doc `hooks` §Stop input; el tope se sube con `CLAUDE_CODE_STOP_HOOK_BLOCK_CAP`). Así que
   el tope solo corta el bucle mudo: un agente que sigue intentando, con tools, contra un gate
   imposible **no** sale a los ocho — gira hasta el tope de presupuesto o de turnos. Por eso el
   mensaje de bloqueo tiene que decir exactamente qué falta y cómo arreglarlo, el gate tiene que ser
   alcanzable por el propio agente, y el script mira `stop_hook_active`.
3. **Tope de presupuesto y de iteraciones.** Sin él amaneces con el trabajo hecho y la factura
   también (`agent-security.md` ASI08). Con el punto 2, es el único tope de verdad.
4. **Commit en rama. Nunca push ni merge.** Es `governance.md` §2 y no cambia de madrugada.
5. **Aviso al terminar y al bloquearse**, por el canal que **exista** en esa máquina
   (`CLAUDE.md` regla 4). Aquí es Telegram: comprueba antes con
   `python3 .claude/scripts/avisar.py --comprobar` y avisa con `avisar.py "DONE|BLOCKED …"`; el hook
   `notify-telegram.sh` lo manda solo al pasar `PROGRESS.json` a `completed`/`blocked`. Un run que acaba
   en silencio a las 4:00 es un run que descubres a las 11:00.
6. **Un frente por fichero.** Si hay más de un agente vivo, los ficheros se reclaman por escrito
   (`parallelization.md` §file claims). Dos runs nocturnos sobre el mismo módulo no se arreglan en
   el merge: se arreglan no lanzándolos.
7. **Los gates de siempre siguen puestos**: el de RAM antes de cualquier test (`ram-pytest.md`) no
   se desactiva porque no haya nadie mirando — es justo cuando un OOM se come la noche entera.

### N5. Por la mañana

Mirar la **forma** antes que el contenido, que es lo único que se hace de verdad cuando hay 40
commits (el procedimiento completo, con sus comandos, está en `refactor-progresivo.md` §A6):

```bash
git log --oneline <base>..HEAD | wc -l        # ¿cuántos commits, y cuadran con lo pedido?
git diff --stat <base>..HEAD | tail -1        # ¿el volumen es el esperado?
git diff --name-only <base>..HEAD | sort      # ¿tocó solo lo que tenía que tocar?
```

Después: **¿pasó el gate, o lo anuló el harness a los 8 bloqueos?** Es la primera pregunta, porque
distingue "terminó" de "se rindió", y las dos dejan el turno cerrado. Con `/goal`, la misma pregunta
es si la meta salió *cumplida*, *imposible* o cortada por un error (`/goal` sin argumento lo dice).

Y por último, la que ninguna herramienta contesta: abre **dos o tres ficheros al azar** y léelos
enteros. No el diff: el fichero. Es la única forma de ver si quedó mejor o solo distinto.

### N6. Límites honestos

- **Esto es criterio, no mecanismo.** Nada impide marcar `si` en algo que no lo es. El campo
  `nocturno` no bloquea nada por sí solo: hace la decisión **explícita y auditable**, que es
  bastante más de lo que hay hoy, y bastante menos que una garantía.
- **El Stop hook tiene el tope de 8, y no es un techo**: se reinicia con cada tool. Cualquier diseño
  que dependa de bloquear indefinidamente está mal diseñado; cualquiera que cuente con que el tope lo
  corte, también.
- **Un run nocturno bien hecho puede seguir produciendo trabajo peor que el de una persona.** El
  gate detecta lo roto, no lo mediocre — el mismo límite que `refactor-progresivo.md` §A0 declara
  para los refactors delegados.

### Anti-patterns del modo noche

- ❌ Marcar el plan entero como nocturno en vez de item por item.
- ❌ Un `nocturno: si` **sin razón escrita** → al mes es indistinguible de un descuido.
- ❌ Tratar lo **no declarado** como apto. Por eso el dashboard distingue "Sin declarar" de "No
  apto": lo que nadie evaluó no entra.
- ❌ `/loop` sin criterio de parada porque "ya lo miro mañana".
- ❌ Dejar un `/loop` en una terminal que se va a cerrar → no hay noche; o `/background`, o tarea
  programada.
- ❌ Un gate que nunca se ha visto fallar, o que el agente no puede satisfacer.
- ❌ Relajar `governance.md` §2 porque son las cuatro de la mañana y no hay nadie para aprobar.
- ❌ Push o merge de madrugada "porque estaba todo verde".
- ❌ Dos agentes sobre el mismo módulo, en paralelo, sin claims.
- ❌ Estrenar un agente de noche.
- ❌ Levantarse y declarar el éxito porque hay 40 commits y los tests están verdes, sin abrir un
  solo fichero.

---

_Rule version: 2.1 · 2026-10-21 (sub-ola 2.16: MO-30 `/loop` integrado y 7 días, separado de
`ralph-loop`; MO-67 las cinco preguntas y «uno hace, otro comprueba»; MO-68 `/goal` con tope,
restricciones, `-p` y el Stop hook; MO-69 la matriz con las cinco formas; y el tope de 8 que se
reinicia con cada tool). v2.0 · 2026-10-20 (LI-28, sub-ola 1.06): absorbe `loop-workflow.md` (v1.0 ·
2026-04-12) y `modo-noche.md` (v1.0 · 2026-08-08; nació del campo `nocturno:` del report-kit: la marca
necesitaba un criterio detrás, o habría sido un checkbox más). Antes: v1.0 · 2026-05-31._
