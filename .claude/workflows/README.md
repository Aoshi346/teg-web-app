# `.claude/workflows/` — Librería de workflows reutilizables

Workflows = scripts JS deterministas que orquestan subagentes (fan-out / pipeline / loop). Cada
fichero aquí se **auto-registra como comando**: `plan-research.js` → `/plan-research`. Feature
nativa de Claude Code (**v2.1.154+**). Ver skill `workflow-creator` para la guía.

**Disponibilidad:** todos los **planes de pago**, además de la API de Anthropic, Amazon Bedrock,
Google Cloud Agent Platform y Microsoft Foundry. En **Pro** hay que activarlos en la fila
*Dynamic workflows* de `/config`. (Si lees en algún sitio del template que son solo Max/Team/API,
está desactualizado.)

**La keyword de disparo inline es `ultracode`, no `workflow`** — cambió en **v2.1.160**. Pedirlo en
lenguaje natural ("usa un workflow") funciona en ambas versiones.

```text
ultracode: audita todos los endpoints bajo src/routes/ buscando checks de auth que falten
```

La keyword solo cuenta en un prompt **que tecleas tú** (prompt interactivo, panel del IDE, Remote
Control, o SDK que marque el input como humano). NO dispara desde `-p`, desde una tarea programada,
ni desde un webhook o comentario de PR relayado a la conversación.

> **Aprueba antes de correr.** Un workflow lanza varios agentes (coste de tokens real) y corre en
> background; obsérvalo con `/workflows`. Para el modo "siempre vía workflows" está
> `/effort ultracode` — pero **pregunta antes** (ver `rules/research-driven-planning.md`).

## 🔐 Aviso de seguridad — los subagentes del workflow corren en `acceptEdits`

> *"Your permission mode controls only the launch prompt. The subagents the workflow spawns always
> run in `acceptEdits` mode and inherit your tool allowlist, regardless of your session's mode.
> File edits are auto-approved."*

Es decir: **tu modo de permisos solo gobierna el prompt de lanzamiento**. Una vez aprobado el run,
las **ediciones de fichero se auto-aprueban** aunque tu sesión esté en modo `default`. Lo que sigue
pudiendo pararte a mitad son los comandos de shell, web fetches y tools MCP que **no** estén en tu
allowlist (por eso conviene pre-aprobar lo que los agentes van a necesitar antes de un run largo —
y por eso el allowlist hay que podarlo: `rules/self-improvement-loop.md` §5 y, en el template,
`claude-code-referencia` §8.11).

Consecuencia práctica: **aprobar un workflow ≈ aprobar sus ediciones**. Antes de decir que sí,
lee las fases (`View raw script` o `Ctrl+G`). Con `claude -p`, el SDK y `bypassPermissions` no hay
prompt de lanzamiento: el run arranca directamente.

## Incluidos (adáptalos a tu stack — llevan placeholders)

Uno por fichero `*.js` de esta carpeta; `check_mechanisms.py` (`indices_sin_mentiras`) avisa si
hay uno en disco que no esté en esta tabla, o una fila sin su fichero.

| Comando | Qué hace | Args |
|---------|----------|------|
| **`/plan-research`** | Planifica una feature/decisión desde varios ángulos, con research (doc oficial + websearch + código) → 3 drafts → juez → síntesis. **Empieza por aquí.** Lectores en cuarentena; sin pregunta no arranca. | la pregunta/feature a planificar |
| **`/review-branch`** | Review del diff vs base por dimensiones (bugs/seguridad/perf/patrones con Rita/**mantenibilidad** con Roberto) + verificación adversarial de cada finding **contra el código**: el verificador recibe la base y el diff y tiene que citar `observed` (`fichero:línea`); en `mantenibilidad` además **re-ejecuta** cada `evidence[].command` (solo lectura) y el hallazgo se descarta si la salida no cuadra (GRF-6, EQ-D9; prueba: `node .claude/smoke/review-branch/check_evidence.mjs`). Los P0 de Roberto se enseñan pero no bloquean (fase 1). Límites del filtro (cabecera del `.js`): usa la config git del repo revisado y los scripts de la rama revisada. | base ref (default `main`) |
| **`/bug-sweep`** | Barrido de bugs por rondas (loop-until-dry) + verificación multi-lente. Recoge antes los bugs **ya reportados** y al final clasifica todos P0/P1/P2 y devuelve el procedimiento de arreglo (antes el comando `/fix-bugs`, retirado el 2026-10-19). No arregla: arregla el TL. | área/glob (default: todo); `conocidos` = solo los ya reportados, sin barrido |
| **`/visual-map-datos`** | El motor de datos del comando `/visual-map`: scout → lector por subsistema → síntesis de `NODES/EDGES`, `ENTITIES/RELATIONS` y `FLOWS`. Hasta el 2026-10-19 era `visual-map.js` y su nombre chocaba con el del comando. | subsistemas CSV (default: autodescubre) |
| **`/codebase-map`** | Mapa de arquitectura: scout → lector por subsistema → síntesis. Onboarding. | subsistemas CSV (default: autodescubre) |
| **`/matrix-eval-harness`** | Compara N configuraciones (matriz de ejes) contra un set de evaluación → score + verificación adversarial → dashboard HTML con ganador. A/B genérico (modelos, estrategias, prompts, algoritmos). **Paso 0 obligatorio:** antes de la matriz reproduce una cifra conocida; si no sale, devuelve `exit_code: 2` y no gasta en el resto (ver abajo). | `{matrix, eval_set, run_instruction, score_schema, paso0, langfuse}` |
| **`/ejecutar-plan`** | Ejecuta waves aprobadas de una sesión SpecKit —todas, o una sola wave de tareas independientes— verificando cada wave, sin preguntar entre waves (absorbió `/ejecutar-wave`, ver abajo). | sesión, o `{tareas, repo}` para una wave |
| **`/analizar-dudas`** | Investiga a fondo cada item en duda de un informe hasta poder recomendar sí o no, o decir por qué no se puede. | los items en duda |
| **`/cruzar-codigo-harness`** | Verifica uno a uno los candidatos del cruce código↔harness de `mapear-sistema` y emite items decidibles (lo lanza esa skill con ≥6 candidatos). Hasta el 2026-10-21, `auditar-sistema-ia`: no audita ningún sistema de IA (MO-65). | candidatos de `audit_sistema_ia.py` |
| **`/research-normativo`** | Research jurídico con fuente primaria obligatoria (EUR-Lex/BOE/AEPD) y verificación adversarial de cada obligación, antes de construir un auditor de cumplimiento. El dominio es un argumento: `ia-rgpd` (por defecto) o `salud-espana`, que antes era el workflow aparte `/research-salud-espana` (retirado el 2026-10-21, MO-43). | `"salud-espana"` o `{dominio, fecha, contexto}` |
| **`/research-tecnico`** | Investigación técnica que termina en ACCIONES aplicables, no en un resumen: estado, doc oficial, casos reales, alternativas, coste y riesgo, verificado. Hasta el 2026-10-21 era una investigación fija sobre Codex CLI que ignoraba `args`; ahora sin pregunta no arranca. | la pregunta, o `{pregunta, angulos, fecha, repo}` |

### `matrix-eval-harness` — el paso 0 (U.01, 18-10-2026)

Un banco que no reproduce lo que ya sabemos no mide, y comparar variantes con él es tirar el dinero.
Por eso el workflow **no arranca la matriz** sin `args.paso0`:

```js
paso0: { cifra_conocida: 0.018, tolerancia: 0.005, fuente: "informe ronda a (musa)",
         config: { id: "A-actual", model: "…" } }      // config: por defecto la primera de la matriz
paso0: { omitir: "primer banco: no existe cifra previa" } // excepción explícita, queda en el resultado
```

Un agente mide la config de referencia **sin que se le diga el valor esperado**; la comparación con
la tolerancia la hace el JS. Si no cuadra (o el agente falla) devuelve
`{exit_code: 2, abortado: true, paso0}`. Si cuadra, sigue y devuelve `{exit_code: 0, paso0, winner, …}`.
Fuente: `r4-experimentos-propuestos.md` §2.2.2 (patrón 0/1/2). Para correr experimentos de verdad, el
entorno es el laboratorio `/home/experimentos` (clones, red solo a APIs de modelos, `--max-budget-usd`).

**McNemar y Langfuse Experiments (3.39, CB-81).** Cada config devuelve `case_results` (id y si pasó, de
todos los casos) y el JS calcula McNemar emparejado contra la primera de la matriz: el resultado trae
`mcnemar` y `winner_note` («sin diferencia demostrable», «el candidato mejora/empeora» o «sin medir»), y
el panel los copia sin recalcular. Con `args.langfuse = {dataset, run_prefix}`, cada config se guarda
como un run de Experiments del mismo dataset (`environment=test`, evaluador de código por item de
`templates/bot-evals/experiments.py`). Lo prueba `node .claude/smoke/matrix-eval/check_mcnemar.mjs`
(paridad con el Python y el workflow entero con dobles). Sin medir contra un Langfuse real.

> ⚠️ **El nombre del `.js` es el nombre del comando** — no puede colisionar con el de una skill
> `user-invocable` ni con otro comando. Si colisiona, uno tapa al otro y desaparece del listado
> (le pasó a `feedback-audit.js` vs la skill `feedback-audit`; por eso el workflow fue `feedback-verify`).

### Workflows que NO viven aquí, a propósito (LI-26, 2026-10-19)

Cada fichero de esta carpeta es una entrada más en el listado de cada sesión. Cuando un workflow es
**un paso** de una skill y no una puerta propia, vive junto a esa skill y ella lo lanza con el tool
`Workflow` (`scriptPath`, documentado en `code.claude.com/docs/en/agent-sdk/typescript` §Workflow):

| Workflow | Dónde vive | Quién lo lanza |
|---|---|---|
| `feedback-verify.js` (antes `/feedback-verify`) | `.claude/templates/feedback_audit/` | skill `feedback-audit`, paso 4 |
| `translate-pages.js` (antes `/translate-pages`) | `.claude/skills/translate-content/` | skill `translate-content`, paso 3 |

Y `/ejecutar-wave` se fusionó en **`/ejecutar-plan`**: una sola wave se le pasa como `{tareas, repo}`.
No está documentado que `args` llegue a un script lanzado por `scriptPath`: los dos scripts se paran
con un error claro si no les llega, y su skill dice cómo hacerlo a mano.

## Cuarentena y presupuesto — las dos reglas de todo workflow de aquí (MO-74, 2026-10-21)

**Cuarentena: el agente que lee contenido de fuera no puede actuar.** Una página web puede traer
instrucciones escritas para un modelo, y los subagentes de un workflow corren en `acceptEdits` con el
allowlist de la sesión (aviso de arriba; en este template, `Bash(*)`). Por eso, en un workflow que lee
la web, **cada** `agent()` que ve esa página o un resumen de ella va con
`agentType: 'lector-web'` (`.claude/agents/lector-web.md`: `WebSearch`, `WebFetch`, `Read`, `Grep`,
`Glob`; ni shell, ni escritura, ni MCP). Lo aplican `research-tecnico`, `research-normativo` y
`plan-research`, también en sus fases de síntesis: el único que actúa es la sesión que lanzó el run, y
solo ve el resultado. `check_mechanisms.py` (`workflows_en_cuarentena`) da roto si uno de esos tres
tiene un `agent()` sin el lector. Los lectores apuntan en `posible_inyeccion` cualquier página que les
dé órdenes, y el resultado del run la trae.

**Presupuesto: `budget` es el «+500k» del Usuario, y es un techo duro.** `budget.total` es `null` si no
puso ninguno; si lo puso, al llegar a él `agent()` **lanza** (doc del runtime, skill
`workflow-authoring`). Las tres formas que usan los workflows de aquí:

| Forma | Dónde | Qué hace |
|---|---|---|
| **Pre-vuelo** | todos | `if (budget.total && budget.remaining() < 50_000)` → no arranca (`exit_code: 2`) |
| **Escalar la fase cara** | `research-*` (verificación), `plan-research` (drafts y juez), `bug-sweep` (rondas) | si no cabe con la reserva de la síntesis, la fase se recorta y se dice con `log()` |
| **Guarda de la síntesis** | `research-*`, `plan-research` | sin presupuesto para el informe, devuelve lo recogido (`parcial`) en vez de caerse |

Sin `budget.total` mandan los topes fijos de cada script (sus `.slice`, `TOPE_VERIFICAR`, y en
`bug-sweep` un `MAX_ROUNDS = 6` que antes no existía: un área que no se secaba solo paraba en el
tope de agentes por run del runtime). **Ningún tope recorta en silencio**: lo que se queda fuera se cuenta en el resultado.
Probado el 2026-10-21 con los hooks simulados, sin gastar tokens (`_archive/2026-10-20/medicion-2.18/`).

## Patrones documentados (escríbelos on-demand; requieren adaptación)

- **security-sweep** — auditoría por ruta/endpoint → verify OWASP. Mapea a `code-review-gate`
  y a la skill `security-review`. Fan-out por endpoint; verifica cada hallazgo.
- **migrate** — migración a gran escala: descubrir sitios → transformar cada uno (con
  `isolation:'worktree'` para evitar conflictos) → verify por item. Para "500-file migrations".

Pídele a Claude "crea un workflow de security-sweep / migración para este repo" y guárdalo aquí.

## Cómo adaptarlos

1. Abre el `.js` y ajusta las constantes de arriba (DIMENSIONS, FINDERS, ANGLES, SUBSYS, etc.) y
   los prompts a tu proyecto/stack.
2. Pásale input con `args` al lanzarlo (string). Cada script documenta qué espera.
3. Corre como `/<name>` o vía el tool `Workflow`.

## Nota sobre avisos del editor (LSP)

Estos scripts usan **`await` y `return` a nivel top** porque el runtime de Workflow envuelve el
body en una función async. El language server de TS/JS no modela eso y marcará falsos positivos
("top-level return", "unreachable code"). **Son inofensivos** — el runtime los ejecuta
correctamente. No los "arregles" envolviéndolos en una función: romperías la compatibilidad con el
runtime (que inyecta `agent`/`parallel`/`pipeline`/`phase`/`log`/`args`/`budget` en el scope).

## Hooks disponibles en el scope (inyectados por el runtime)

`agent(prompt,{schema,label,phase,model,effort,agentType,isolation})` · `parallel(thunks)` (barrera) ·
`pipeline(items,...stages)` (sin barrera) · `phase(title)` · `log(msg)` · `args` · `budget` ·
`workflow(nombre, args)` (otro workflow como paso, un nivel).
Recuerda: solo `agent()` gasta tokens; el resto es JS determinista tuyo. Límite ≤16 concurrentes /
≤1000 por run; sin input humano a mitad; sin fs/shell directos desde el script.

`agent()` devuelve `null` si paras el agente a mitad o si sufre un error de API irrecuperable, y
`pipeline()` conserva ese `null` en el array de resultados — por eso los scripts terminan en
`.filter(Boolean)`. No lo quites.

## Tamaño del run — `workflowSizeGuideline`

Le dice a Claude **a cuántos agentes apuntar** al escribir un workflow. Es **consejo, no tope**: un
prompt que pida otra escala lo sobrescribe. Requiere v2.1.202+.

| Valor | Agentes a los que apunta |
|---|---|
| `small` | menos de 5 |
| `medium` | menos de 15 |
| `large` | menos de 50 |
| `unrestricted` | sin guía: Claude dimensiona según la tarea |

**Default: `medium`** (desde **v2.1.219**; antes era `unrestricted`). Se cambia en la fila
*Dynamic workflow size* de `/config`, con `/config workflowSizeGuideline=small`, o poniendo la clave
**`workflowSizeGuideline`** en cualquier fichero de settings (v2.1.219+) — el settings **gana** a
`/config`, y mientras exista ahí Claude Code oculta la fila de `/config`.

**Aviso "Large workflow"**: cuando un run programa **más de 25 agentes** o su total de tokens
proyectado pasa de **1,5 M**, aparece en la línea de progreso del panel de tareas (v2.1.203+). Es
**advisory**: no pausa ni limita, solo te señala `/workflows` para que puedas pararlo. Dos matices:
si eliges una size guideline, **su** número de agentes sustituye al umbral de 25; y las sesiones con
**ultracode** no ven el aviso (activarlo ya es optar por runs grandes).

Los topes duros del runtime (≤16 concurrentes, ≤1000 por run) siguen aplicando en cualquier caso.

## 🧩 Regla de diseño: reparte en agentes pequeños (semántica de resume)

Un run parado se puede reanudar, pero **el replay tiene dos reglas** que deciden qué se conserva:

1. Un agente que **seguía corriendo** cuando paraste **no se guarda**: vuelve a empezar.
2. **El replay sigue el orden en que los agentes ARRANCARON.** Los resultados cacheados se cortan
   en el primer agente que no terminó, y **todos los que arrancaron después vuelven a correr,
   aunque hubieran acabado.**

Ejemplo de la doc: el script lanza A, B, C y D en ese orden y paras con B a medias. Al reanudar, A
sale de caché; B se repite porque nunca acabó; **y C y D se repiten también** —arrancaron después
de B— aunque ambos habían terminado antes de que pararas.

> **Consecuencia de diseño (aplica a todos los de esta carpeta):** un workflow que reparte el trabajo en
> **muchos agentes pequeños preserva más progreso** que uno que lo concentra en un agente largo.
> Cuanto más tarda un agente, más ventana hay de pararlo a mitad — y más trabajo posterior arrastra
> al invalidarse. Al escribir o revisar un workflow: parte las fases largas, evita el "agente
> monolito" que hace descubrimiento + transformación + verificación, y pon primero lo más caro y
> estable (así queda cacheado antes de la zona donde probablemente pares).

Ojo también al alcance: **el resume funciona dentro de la MISMA sesión de Claude Code**. Si sales de
Claude Code con un workflow corriendo, la siguiente sesión lo empieza **de cero**.

Se reanuda desde `/workflows` seleccionando el run y pulsando `p`.
