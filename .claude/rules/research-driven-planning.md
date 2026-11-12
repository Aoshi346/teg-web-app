---
paths:
  - ".specify/sessions/*/plan.md"
  - ".docs/plans/*/plan.md"
  - ".claude/workflows/plan-research.js"
  - ".claude/workflows/research-*.js"
---
# Planificación basada en research — context7 + websearch + /deep-research

> **Cuándo aplicar:** al **planificar** cualquier tarea no trivial (feature multi-archivo, refactor,
> elección de librería/enfoque, due diligence de una dependencia). Antes de comprometer un plan,
> apóyalo en fuentes actuales, no en memoria de entrenamiento.
>
> **Relacionado:** `plan-gates.md`, `goal-vs-loop.md`, skill `workflow-creator`,
> `prompt-contracts`, `governance.md` (autonomía).

---

> **Disparo:** este research se ofrece vía el **gate de plan** de `plan-gates.md` — solo en
> **tareas grandes** (feature/refactor/módulo nuevo), no en cada cambio ni en bugfixes triviales.

## Principio

Un plan es barato de mejorar y caro de re-hacer. La calidad del plan sube mucho cuando se
**verifica contra fuentes** durante la fase de planificación. El conocimiento del modelo tiene
fecha de corte; las librerías, APIs y features cambian. **No planifiques de memoria.**

## Las tres herramientas de research en planning

### 1. context7 MCP — docs de librerías (SIEMPRE para APIs/frameworks)
Para **cualquier** librería, framework, SDK, API o CLI que aparezca en el plan —incluso las que
"conoces" (React, Django, Tailwind, etc.)— consulta context7 para la sintaxis/config/migración
**actual**. Es preferible a websearch para docs de librerías.
```
mcp__context7__resolve-library-id → mcp__context7__query-docs
```
NO usar para: lógica de negocio, refactors, conceptos generales de programación.

### 2. websearch — información reciente / post-cutoff
Para features nuevas, breaking changes, versiones, comparativas de mercado, precios, o cualquier
cosa que pueda haber cambiado tras el corte de conocimiento. Cita las fuentes que uses.

### 3. `/deep-research <pregunta>` — cruzar varias fuentes (workflow bundled)
Cuando la decisión necesita **cross-check entre fuentes** (comparar 3 enfoques, validar un claim
dudoso, due diligence de una dependencia o vendor). `/deep-research` hace fan-out de búsquedas por
ángulos, fetch, verificación adversarial de claims y un informe citado. Es el workflow nativo de
Claude Code (ver skill `workflow-creator`). Útil cuando una sola búsqueda no basta.

> Si la pregunta está **poco acotada**, primero haz 2-3 preguntas de clarificación (presupuesto,
> caso de uso, región…) y luego lanza el research con la versión refinada.

## Split de modelos planner/executor (AGT-1, aprobado 2026-08-07)

**Planifica con el modelo razonador; ejecuta con el rápido.** Es ahorro directo sin pérdida de
calidad — el plan es donde el razonamiento profundo paga; la ejecución de un plan bueno es mecánica.

| Fase | Modelo/effort | Por qué |
|------|---------------|---------|
| Plan de tarea grande, arquitectura, diseño de spec | Opus · `medium` (subir a mano a `high`/`xhigh` solo para un bloque que lo pida, y bajarlo después) | El coste de un plan malo es re-hacer todo; con los 5.5, `medium` ya rinde como el `high` de antes (política de abajo) |
| Ejecución de waves con plan cerrado, ediciones mecánicas, batch | Sonnet u Opus · `low`/`medium` | El plan ya decidió; ejecutar barato |
| Verificación/juez adversarial | modelo distinto al productor si es posible · `high`/`xhigh` | El productor no es escéptico honesto de sí mismo, y el verificador vive de los casos límite |

Aplicación práctica: en workflows, `opts.model`/`opts.effort` por agente (plan caro, ejecutores
baratos); en subagentes, el campo `model:`/`effort:` del frontmatter; en sesión, `/model` + `/effort`
al cambiar de fase. Matiz verificado: **Opus en effort low puede ser más rápido que Sonnet a full
effort** en tareas que requieren criterio — no asumas que "barato" = modelo menor.

## Política de effort ORDINARIA (CL-D4, aprobada el 2026-10-18; sustituye a DEC-7)

El apartado ULTRACODE de abajo cubre el caso extremo. Esto cubre el día a día, que es donde se
gasta el presupuesto de verdad. Otto ya recomienda "modelo y effort" en el Gate 0 — este es el
criterio escrito detrás de esa recomendación.

**`medium` por defecto; `high`/`xhigh` solo donde se vive de los casos límite: auditores y
verificadores.** La doc oficial (`code.claude.com/docs/en/model-config` §Adjust effort level, leída el
2026-10-21): Opus, Sonnet y Haiku 5.5 arrancan en `medium`, y *"Opus 5.5 at `medium` matches or exceeds
Opus 5 at `high` on coding and knowledge-work evaluations"*; al pasar de Opus 5, *"start at `medium`
rather than carrying over the level you used on Opus 5"*.

| Para… | Effort | Por qué |
|---|---|---|
| Casi todo: implementar, features y fixes que van a producción, planes, búsquedas, ediciones mecánicas, escribir una skill | **`medium`** (el de serie: no se escribe) | Con los 5.5, `medium` rinde como el `high` de los 5. Lo que protege producción es el verificador, no razonar más al escribir |
| **Auditores y verificadores**: los agentes y skills cuyo trabajo es encontrar el fallo que no da señal, y el subagente que verifica con contexto limpio | **`high`/`xhigh`**: en su frontmatter, o al lanzar el verificador (`effort` del Agent tool o `opts.effort` del workflow) | Su error caro es el falso negativo, y ese vive en los casos límite |
| Un bloque concreto que lo pide (un plan de arquitectura difícil, un bug que no cede) | subir a mano para ese bloque, **y bajarlo al acabar** | Decisión puntual de quien conduce la sesión, no una norma escrita en ningún frontmatter |

**Quién lleva `effort` en su frontmatter** (2026-10-21): los agentes `dario-commerce-guardrails`,
`ivan-agent-runtime`, `nora-ai-act-auditor` y `sara-salud-datos`, y las skills
`feedback-audit`, `cumplimiento-salud` y `langgraph-debug` (`xhigh`) y `modelado-amenazas` (`high`). El
resto, nada: corren al effort de la sesión. `rafa-retrieval-engineer` y las once skills de diseño,
creación y montaje (`arrancar`, `code-graph`, `project-setup`, `skill-authoring`…) que llevaban `xhigh` por
la política de antes (DEC-7, «`xhigh` para todo lo que va a producción», aprobada el 2026-08-07) lo
perdieron en la sub-ola 2.01; `skill-authoring` ya no pide subir a `xhigh` para editar una skill.

Cuatro avisos prácticos:
- **Cambiar el effort a mitad de sesión ya no rompe la caché** con Opus, Sonnet y Haiku 5.5 (y
  Fable 5.1) con suscripción o API key (doc `prompt-caching` §Changing effort level): el ciclo
  «implementar en `low`/`medium` → verificar en `high`» sale barato.
- `/effort <nivel>` tecleado **se guarda como tu defecto** para las sesiones siguientes; `max` vale
  solo para la sesión. Al terminar un bloque caro, **bájalo** (doc `model-config` §Adjust effort level).
- El `effort` del frontmatter de una skill o un subagente manda **mientras está activo**, por encima del
  de la sesión, y no por encima de `CLAUDE_CODE_EFFORT_LEVEL` (misma página). Escribirlo en la prosa de la
  skill **no lo aplica**.
- **Tu `~/.claude/settings.json` gana a esta política para ti**: un `modelSettings` con `effortLevel`
  por modelo es tu defecto en todas tus sesiones. La política dice qué pone el template, no qué eliges tú.

### Coste oculto 1 — auto mode: casi nunca es un coste (corregido el 2026-10-20)

El **auto mode** (Shift+Tab hasta Auto) manda cada permission prompt a un clasificador basado en
modelo en vez de preguntarte. Esta sección decía que eso costaba «~10-15 % de tokens extra»: la
cifra **nunca tuvo fuente**, y la nota de que auto «cuesta algo más» se retiró en la v2.1.228
(2026-08-11, changelog oficial). Hoy, donde la revisión va en el servidor, el clasificador **no se
cobra**; en Pro, Max y Team no aparece nunca el aviso de cobro (doc
`code.claude.com/docs/en/auto-mode-classifier-billing`, leída el 2026-10-20). **Sí cuenta** como
uso cuando la sesión cae al clasificador local: un gateway o proxy entre medias,
`CLAUDE_CODE_AUTO_MODE_SERVER=0`, o una plataforma sin la revisión en servidor (`/status`, fila
**Auto mode server**). Detalle del modo: `code.claude.com/docs/en/permission-modes` y, en el
template, la skill `claude-code-referencia` §8.8-8.10.

### Coste oculto 2 — GOTCHA: no encadenes slash commands desde dentro de una skill

**Escribir "corre `/simplify`" en una skill o en `CLAUDE.md` no ejecuta nada.** Es texto que el
agente lee y puede seguir o no: una sugerencia, nunca una cadena garantizada. Esto es cierto
siempre, y es lo único que necesitas recordar.

La versión fuerte del gotcha —*"las skills no pueden invocar slash commands built-in de Claude
Code desde dentro"*— viene de una fuente secundaria y **no la hemos verificado en nuestra versión**;
además el harness ha ido moviendo terreno (los custom commands se fusionaron con las skills, y
`/simplify` aparece hoy en el listado de skills invocables). Trátala como aviso, no como ley: si
montas un pipeline que depende de ese encadenado, **pruébalo** antes de confiar en él.

**Ya nos afecta:** `CLAUDE.md` manda *"/simplify — pre-PR obligatorio"*. Eso funciona solo si el
agente (o el humano) lo teclea en la sesión. Consecuencias:
- Los pipelines tipo `implementar → /simplify → review → PR` son **encadenado manual**, no automático.
- Si quieres que algo ocurra **siempre**, no lo pongas en una cadena de slash commands: bájalo a un
  **hook** (`rules/layer-decision.md`, pregunta 1) o a un script gate con exit ≠ 0.

## Modelo por agente (CL-D15, sub-ola 3.17, 2026-10-31)

**Ningún agente baja de modelo sin una medida que lo respalde.** El `model:` del frontmatter es un
alias (`opus`, `sonnet`, `haiku`): sube de versión solo. El laboratorio que iba a dar la tabla por tipo
de tarea (X-08) se saltó por decisión del Usuario (31-10), y el spike U.02-U.03 midió modelos de los
bots de producto, no agentes del harness. La tabla es el defecto razonado; lo que falta, va dicho.

| Clase de agente | `model:` | Por qué | Sin medir |
|---|---|---|---|
| Auditores cuyo error caro es el falso negativo en un caso límite: `roberto-clean-code`, `pilar-impacto-produccion` (decisión del Usuario, 18-10), `nuria-aislamiento-tenant`, `nora-ai-act-auditor`, `sara-salud-datos`, `teo-llm-redteam`, `dario-commerce-guardrails`, `agent-evals` | `opus` | Lo que no encuentran no da señal (§Política de effort) | si `sonnet` en `high` tiene el mismo recall en su fixture |
| Constructores de criterio en IA: `ivan-agent-runtime`, `rafa-retrieval-engineer` | `opus` | Deciden arquitectura del grafo y del retrieval | acierto y coste frente a `sonnet` |
| El resto (constructores, auditores-persona, QA, negocio) | `sonnet` | Trabajo con criterio pero acotado por su skill o su fichero | acierto, tokens y tiempo frente a `opus` y `haiku` por tipo de tarea |
| `lector-web` (sin `model:`, hereda el de quien lo lanza) | se queda así | Lectura en cuarentena; el workflow fija el modelo | si `haiku` resume igual de fiel (candidato natural) |
| **`haiku`** | **ninguno hoy** | Solo un juez simple (clasificar, triar), y solo si su replay de calibración con fixture (sub-ola 3.07) da **el mismo recall** que con su modelo actual | el replay entero: no hay ninguno hecho |
| `auditor-modelos` (3.61; falso negativo caro: dejar pasar un modelo con fuga) | `opus` | Lo que no encuentra no da señal, como los de la primera fila | si `sonnet` en `high` caza las mismas fugas en `model_audit.py --autoprueba` y en un modelo real |

- **Nunca `haiku` en seguridad ofensiva** (`sofia-pentester`, `teo-llm-redteam`,
  `hugo-vigilancia-diaria`): Haiku 5.5 *«still block[s] penetration testing»* (anuncio oficial de Haiku 5.5).
- **Fast mode** (solo Opus 5.5, 5 y 4.8): hasta 2,5× más rápido, **$8/$40** por millón frente a los
  $4/$20 de Opus 5.5, y **activarlo rompe la caché**. Solo en sesión interactiva corta, donde esperar
  cuesta más que el doble de precio; nunca en subagentes, workflows, `/batch` ni `/loop`. Sin medir: la
  velocidad real en nuestras sesiones.
- Bajar un agente de modelo: replay de su fixture con el modelo nuevo, recall igual o no baja; se dice en
  el commit. Subirlo no pide medida, pero se dice por qué.

## Escalar la planificación a un workflow

La **planificación** es el mejor punto de entrada a los workflows (el autor del doc reporta specs +
review ~20x más rápidos). Considera un workflow de planning cuando el plan es "duro" y conviene
**draftarlo desde varios ángulos independientes** y luego sintetizar (panel de jueces). El template
trae `.claude/workflows/plan-research.js` (`/plan-research`) como punto de partida.
Sus agentes corren **en cuarentena** (`agentType: 'lector-web'`: leen la web y el repo, sin
shell, escritura ni MCP — tampoco context7), así que la doc de una librería la leen en su web
oficial; context7 sigue siendo la herramienta de **la sesión** que planifica (MO-74, 2026-10-21;
`workflows/README.md` §Cuarentena y presupuesto).

## ⚠️ Política ULTRACODE — preguntar SIEMPRE antes de activar

`/effort ultracode` hace que Claude **planifique y ejecute un workflow para CADA tarea sustancial**
de la sesión. Es potentísimo para exhaustividad, pero **multiplica el coste de tokens**.

**Reglas (no negociables):**
1. El agente **NUNCA** activa ultracode por su cuenta.
2. Si detecta que una tarea se beneficiaría de verdad (planning a escala, migración grande,
   auditoría/review exhaustivo, research profundo), **lo PROPONE y pregunta** antes:
   > "Esto se beneficiaría de **ultracode** (Claude planifica/ejecuta vía workflows multi-agente;
   > resultado más exhaustivo pero **multiplica el coste de tokens**). ¿Lo activo?"
3. Solo se usa con **confirmación explícita** del usuario. Al terminar el bloque de trabajo que lo
   justificaba, recordar desactivarlo si la sesión sigue con tareas pequeñas.
4. Esto es coherente con los approval gates de `governance.md` (gasto/coste = decisión del usuario).

## Checklist de planning (antes de ExitPlanMode / comprometer)

```
[ ] ¿Hay librerías/APIs en el plan? → consultadas en context7
[ ] ¿Hay algo que pudo cambiar tras el cutoff? → websearch con fuentes
[ ] ¿Hay una decisión que necesita cruzar fuentes? → /deep-research
[ ] ¿El plan es "duro"/ambiguo? → considerar plan-research workflow (multi-ángulo)
[ ] ¿La tarea pide ultracode? → PROPONER y preguntar, nunca auto-activar
[ ] ¿El effort es el que toca? → medium por defecto · high/xhigh solo auditores y verificadores
[ ] Plan escrito con prompt-contracts (GOAL/CONSTRAINTS/FORMAT/FAILURE)
    …salvo baja confianza en el enfoque → elicitar primero (`plan-gates.md` §1b)
```

## Anti-patterns

- ❌ Planificar de memoria una integración con una librería sin abrir context7.
- ❌ Afirmar "la API X funciona así" sin verificar (puede haber cambiado).
- ❌ Lanzar `/deep-research` sobre una pregunta vaga sin acotarla antes.
- ❌ Activar ultracode sin avisar del coste → sorpresa en la factura de tokens.
- ❌ Saltarse el research "porque ya lo sé" en decisiones con impacto (deps, arquitectura).
- ❌ Quedarse en `xhigh`/`max` después del bloque que lo justificaba (`/effort` se guarda; `max`, no).
- ❌ Poner `effort: xhigh` en el frontmatter de una skill o un agente que construye: el effort caro va
  donde se verifica (CL-D4). Lo que cubre el código que va a producción es el verificador.
- ❌ Diseñar una cadena que depende de que una skill invoque `/simplify` o `/review` — no puede.

---

_Rule version: 1.3 · 2026-10-31 · §Modelo por agente (CL-D15, sub-ola 3.17: ningún agente baja de
modelo sin medida; fast mode solo en interactivo corto) · v1.2 · 2026-10-21 · política de effort CL-D4 (medium por defecto; high/xhigh solo
auditores y verificadores; sub-ola 2.01) · v1.1 · 2026-05-31 · +política de effort ordinaria, coste de auto mode y gotcha de
slash commands (DEC-7, aprobado 2026-08-07)_
