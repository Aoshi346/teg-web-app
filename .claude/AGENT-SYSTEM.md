# AGENT-SYSTEM.md — qué tienes y qué usar

> **GENERADO. No editar a mano** — `python3 .claude/scripts/gen_agent_system.py`.
> `--check` sale 1 si está desfasado. Un mapa escrito a mano se desincroniza en tres semanas.
>
> **`INDEX.md` dice qué LEER. Esto dice qué USAR.** Son distintos: el índice rutea documentación,
> este mapa reparte capacidades. Si solo vas a mirar uno estando a punto de trabajar, mira este.

_Inventario real a 2026-11-12: 12 agentes · 39 skills · 15 commands · 8 workflows · 41 hooks · 37 rules._

---

## 1. Qué capa uso

> Un **loop es un nodo de un grafo**: cada capa de abajo no sustituye a la de arriba, la envuelve.

| Necesito… | Capa | Por qué esa y no otra |
|---|---|---|
| Que el modelo **sepa** un dato del proyecto | `CLAUDE.md` | Es contexto, no procedimiento. Y es *advisory*: se puede ignorar. |
| Un **procedimiento** que repetiré ≥3 veces | **Skill** | Su cuerpo carga solo cuando se usa; la `description` es lo que dispara. |
| Que algo ocurra **siempre**, pase lo que pase | **Hook** | Es la única capa que no se puede ignorar. Si duele que se salte, va aquí. |
| Un **juicio independiente** con contexto limpio | **Subagente** | El que hizo el trabajo no es escéptico honesto de sí mismo. |
| **Varios** juicios en paralelo, orquestación repetible | **Workflow** | Determinista, resumible, con presupuesto. Un loop es un nodo de un grafo. |
| Que los agentes **se hablen** entre sí | **agent-teams** | Solo si necesitan REBATIR. Si basta con enterarse → pizarra (`parallelization.md` §Pizarra). |
| Capacidad **empaquetada y versionada** de terceros | **Plugin** | Doc oficial: standalone en `.claude/` para iterar; plugin para compartir/versionar. |
| Acceso **gobernado** a un sistema externo | **MCP** | Scope y permisos explícitos. Nunca un `bash` suelto (`security.md`). |

**La pregunta que decide casi todo** (`rules/layer-decision.md`): *¿qué es lo PEOR que pasa si
Claude lo ignora?* Si la respuesta es «perdemos unos minutos» → prosa. Si es «se rompe algo caro»
→ **hook**. Subir el tono de un párrafo no lo convierte en obligatorio.

---

## 1b. Puertas: quién juzga, en qué orden y con qué topes

El TL es **la sesión principal** (orquesta, hace de arquitecto en plan mode e integra); construyen los
agentes con Edit, en worktree; **juzgan los que no tienen Edit**, y un hook les impide escribir fuera de su
zona. Quien revisa nunca es quien hizo. Orden: plan → código → UI → cierre → producción, sin mezclar
puertas en una ronda. Topes por puerta: **≤5 jueces, ≤3 con navegador, ≤3 rondas** (de la 2ª, solo el
diff); la batería completa, solo en hito de release. Cada P0/P1 de código y UI lo valida un segundo agente.
Detalle: `rules/audit-team.md`.

| Puerta | Jueces | Gate determinista | Nota |
|---|---|---|---|
| **1 · Plan** | `~~pilar-impacto-produccion~~ ⚠️` · `pol-product-advisor` | `plan-gates.md` (Gate 0b, 0) | Pilar PRE: la foto de impacto antes de escribir código. Pol, opcional |
| **2 · Código** | `~~roberto-clean-code~~ ⚠️` · `marco-qa-breaker` · `~~nadia-chatbot-evaluator~~ ⚠️` · `~~dario-commerce-guardrails~~ ⚠️` | `/code-review` · `gate_auditor.py` | Hasta Roberto: `code-review-gate` + verificador limpio. Nadia y Darío solo si hay bot |
| **3 · UI** | `lidia-naive-tester` · `vera-art-director` · `ignacio-roig` · `aitor-a11y-auditor` · `~~lena-i18n-auditor~~ ⚠️` | `gate_diseno.py` · `/qa-loop` · `gate_auditor.py` | Después de que pase la de código. Aitor/Lena si hay a11y o idiomas |
| **4 · Cierre** | `sofia-pentester` · `priya-privacy-auditor` · `~~pilar-impacto-produccion~~ ⚠️` · `~~nuria-aislamiento-tenant~~ ⚠️` | `smoke/seguridad/correr.sh` · `task_progress.py --gate` | Sofía al final y en staging. Pilar POST cierra el gate. Nuria si es multi-tenant |
| **5 · Producción** | `~~bruno-perf-cop~~ ⚠️` · `~~nadia-chatbot-evaluator~~ ⚠️` | `/deploy` (con OK) | Bruno sobre lo desplegado; Nadia sobre trazas reales si hay bot |

No se crean como agentes un arquitecto, un orquestador ni un SRE: el orquestador-agente mete una capa de
opinión entre el Usuario y el trabajo. `~~tachado~~ ⚠️` = juez previsto que aún no existe.

---

## 2. Si vas a… → esto es lo que tienes

Las cuatro capas juntas, por escenario. `~~tachado~~ ⚠️` = declarado aquí pero **ausente en disco**.

### Arrancar un producto desde cero (definir ANTES de construir)

- **Agentes:** `pol-product-advisor` · `priya-privacy-auditor` · `~~nora-ai-act-auditor~~ ⚠️`
- **Skills:** `arrancar` · `marca` · `producto` · `otto` · `~~cumplimiento-salud~~ ⚠️` · `~~disenar-conversacion~~ ⚠️` · `modelado-amenazas`
- **Comandos:** `/siguiente` · `/marca` · `/schema` · `/visual-map` · `/speckit.plan` · `/speckit.tasks` · `/speckit.converge`
- **Rules:** `plan-gates.md` · `plan-docs-structure.md` · `adr.md` · `verdict-contract.md` · `~~ai-assistant-risk.md~~ ⚠️`

> **Orden recomendado.** **Si no sabes qué toca, `/siguiente`** (mide el proceso y dice el comando). **`arrancar` primero, todo lo demás después.** Las 5 fases en orden: producto (PRD + requisitos con Gherkin) → datos y flujos (el ERD de DISEÑO, antes de que haya código) → stack + C4 + ADR + comprar-o-construir → ética y privacidad ANTES de construir → SpecKit solo para ejecutar. `/speckit.specify` y `/speckit.clarify` quedan fuera: el primero trae orden de *no preguntar*, el segundo solo corre si lo tecleas.

### Cumplimiento legal: RGPD, datos de salud y Reglamento de IA

- **Agentes:** `priya-privacy-auditor` · `~~sara-salud-datos~~ ⚠️` · `~~nora-ai-act-auditor~~ ⚠️`
- **Skills:** `feedback-audit`
- **Workflows:** `~~research-normativo~~ ⚠️`
- **Comandos:** `~~/fairness-audit~~ ⚠️`
- **Rules:** `verdict-contract.md` · `~~ai-assistant-risk.md~~ ⚠️` · `~~fairness-audit.md~~ ⚠️` · `security.md`

> **Orden recomendado.** **Las tres son necesarias y ninguna cubre a las otras**: un chatbot de clinica con IA las necesita las tres. **Priya** el RGPD general y deriva - **Sara** datos de salud Espana (art. 9.3, LOPDGDD, Ley 41/2002) - **Nora** el Reglamento de IA. Las tres PREGUNTAN antes de auditar (la clasificacion depende del USO, no de la arquitectura) y sin respuesta el veredicto es `blocked`. Las tres tienen error_cost FALSE-POSITIVE: ante la duda, `review`. La normativa CADUCA: el calendario del Reglamento de IA cambio el 27-07-2026. Relanza el workflow de research antes de fiarte de la rubrica.

### Actualizar o auditar el SISTEMA AI (.claude/) de un proyecto

- **Skills:** `otto` · `~~mapear-sistema~~ ⚠️` · `~~update-agent~~ ⚠️` · `~~check-agent~~ ⚠️` · `code-graph`
- **Workflows:** `~~cruzar-codigo-harness~~ ⚠️`
- **Comandos:** `~~/consolidate-agent-learnings~~ ⚠️`
- **Rules:** `self-improvement-loop.md` · `layer-decision.md` · `governance.md`

> **Orden recomendado.** **mapear ANTES de copiar** → `mapear-sistema` cruza lo que el código ES con lo que el harness TIENE (motor: `scripts/audit_sistema_ia.py`) · con ≥6 candidatos lanza el workflow `cruzar-codigo-harness` para verificarlos en paralelo · **aplicar** → `update-agent` (staging: un solo permiso) · **lo propio del proyecto** vuelve al template por `/consolidate-agent-learnings`. Gate: `audit_sistema_ia.py <proy> --gate`.

### Tocar UI / frontend (diseñar, montar o cambiar una pantalla)

- **Agentes:** `vera-art-director` · `ignacio-roig` · `aitor-a11y-auditor` · `~~conrado-cro-auditor~~ ⚠️` · `lidia-naive-tester` · `desarrollador-frontend`
- **Skills:** `producto` · `marca` · `direcciones-de-arte` · `disenar-pantalla` · `movimiento` · `nueva-pantalla` · `design` · `ux-reviewer` · `visual-regression` · `capturas-responsive` · `naive-user-playthrough` · `html-suelto`
- **Comandos:** `/qa-loop`
- **Plugins/MCP:** `frontend-design ✔ activo (oficial, 71 líneas)` · `superdesign ✔ activo` · `playwright` · `chrome-devtools-mcp ⚠ NO instalado` · `typescript-lsp ⚠ en disco pero DESACTIVADO`
- **Rules:** `motores-de-diseno.md` · `qa-loop.md` · `verification.md` · `html-output.md`

> **Orden recomendado.** **¿landing o panel? El PERFIL decide el camino entero** (`patterns/diseno/perfiles.yaml`): una web de cliente pasa por `direcciones-de-arte` —varios mundos con nombre, galería, y el ranking lo haces TÚ—; un panel va directo a `disenar-pantalla`. · **antes de nada, `python3 .claude/scripts/check_design_login.py`** — si sale 1, el Usuario tiene que teclear `/design-login` para poder comprobar si ya existe un sistema en la web de Claude Design (cierra el 14-12-2026); si sale 2, NO se pudo medir (o la web ya cerró) y no se le manda a ningún login · **si no hay marca (ni identidad, ni paleta, ni tokens), empieza por `marca`** — si no, el boceto sale en grises por diseño · **si son ≥2 pantallas o hay un embudo, `/producto`** · **decidir la forma** → `disenar-pantalla` (2-3 variantes comparables) · **escribirla** → `nueva-pantalla` (molde de 10 ficheros) · **cerrar** → `python3 .claude/scripts/gate_diseno.py <build>` (determinista, va ANTES de gastar un auditor) + screenshot + `ux-reviewer`, y si es wave → `/qa-loop`. · **el gusto vive en `patterns/diseno/` y NUNCA bloquea**; quién manda cuando dos herramientas se contradicen: `rules/motores-de-diseno.md`.

### Backend / API / modelos / queries

- **Agentes:** `desarrollador-backend` · `~~nuria-aislamiento-tenant~~ ⚠️` · `~~pilar-impacto-produccion~~ ⚠️`
- **Skills:** `django-orm` · `migration-integrity-checks` · `~~multi-tenant-context~~ ⚠️` · `escribir-tests`
- **Plugins/MCP:** `pyright-lsp` · `claude-security`
- **Rules:** `ram-pytest.md` · `governance.md` · `verification.md`

> **Orden recomendado.** **RAM antes de tests** (`check-ram.sh`) · el endpoint nuevo **se llama de verdad** antes de DONE (`verification.md` §Smoke testing) · migración destructiva = aprobación · **multi-tenant con `tenant_id` → G4**: la suite `templates/seguridad-tenant/` (modelos descubiertos, dos tenants por modelo) y `gate_tenant.py` (rol sin BYPASSRLS, RLS forzado, políticas, y las sondas de lectura y de escritura: necesitan el DSN de admin o sale 2) · con migraciones o un manager/permiso compartido, **Pilar** saca la foto antes de programar (`clasificar_migraciones.py --diff <base>`).

### Revisar código / pre-merge / auditar un diff

- **Agentes:** `~~roberto-clean-code~~ ⚠️` · `~~pilar-impacto-produccion~~ ⚠️` · `rita-pattern-keeper` · `ignacio-roig`
- **Skills:** `code-review-gate` · `pattern-gate` · `security-review` · `practices-manifesto`
- **Workflows:** `/review-branch` · `/bug-sweep`
- **Plugins/MCP:** `code-review` · `pr-review-toolkit` · `claude-security`
- **Rules:** `verdict-contract.md` · `audit-team.md` · `trunk-based-flow.md` · `refactor-progresivo.md` · `governance.md`

> **Orden recomendado.** `/review-branch` hace el grafo entero (dimensiones en paralelo + verificación adversarial). El juicio independiente exige **contexto limpio**: no reutilices la sesión que escribió el código.

### Planificar una tarea grande (>3 ficheros, feature, refactor, módulo nuevo)

- **Agentes:** `pol-product-advisor`
- **Skills:** `otto` · `prompt-contracts` · `~~project-setup~~ ⚠️` · `code-graph`
- **Workflows:** `/plan-research`
- **Comandos:** `/visual-map` · `/schema`
- **Rules:** `plan-gates.md` · `speckit-workflow.md` · `research-driven-planning.md` · `report-kit.md` · `adr.md`

> **Orden recomendado.** **Gate 0b** (¿qué me falta saber?) → **Gate 0: corre `/otto`** → gates A/B (research · mapa visual) → C buy-vs-build si es módulo nuevo → D ADR si toca arquitectura → E vía de datos si lee de fuera. **Para que el Usuario vea el informe**: `python3 server.py --port <N>` (escucha en 127.0.0.1) y él abre un túnel: `ssh -N -L <N>:127.0.0.1:<N> root@<servidor>`. Nunca `0.0.0.0`.

### QA / verificar que algo está hecho / cerrar una wave

- **Agentes:** `lidia-naive-tester` · `vera-art-director` · `ignacio-roig` · `marco-qa-breaker` · `sofia-pentester` · `~~pilar-impacto-produccion~~ ⚠️`
- **Skills:** `verification-loops` · `feedback-audit` · `visual-regression` · `capturas-responsive` · `escribir-tests` · `~~eval-estadistica~~ ⚠️` · `code-review-gate`
- **Comandos:** `/qa-loop`
- **Plugins/MCP:** `playwright` · `chrome-devtools-mcp`
- **Rules:** `verification.md` · `verdict-contract.md` · `qa-loop.md` · `audit-team.md`

> **Orden recomendado.** **Doble evidencia obligatoria**: 🔎 código (`file:line`) + 👁 en vivo (DOM/screenshot). Con una sola es `partial`, nunca `done`.

### Cerrar un issue / ¿afecta a algún cliente? / impacto en producción

- **Agentes:** `~~pilar-impacto-produccion~~ ⚠️` · `~~roberto-clean-code~~ ⚠️`
- **Skills:** `migration-integrity-checks` · `verify-ticket` · `code-review-gate`
- **Comandos:** `~~/nuevo-issue~~ ⚠️` · `~~/cerrar-issue~~ ⚠️`
- **Rules:** `verdict-contract.md` · `audit-team.md` · `governance.md` · `~~issue-worktree-flow.md~~ ⚠️`

> **Orden recomendado.** **Pilar PRE** antes de tocar código → `gate_impacto.py <plan> --fase pre` · al cerrar: **Roberto** sobre el diff → **Pilar POST** → `render_impacto.py <plan> --inyectar <informe>` → `gate_impacto.py <plan> --fase post` (en `/cerrar-issue`, `issue_close.py <plan>`, que además exige el informe del issue en su ruta). Exit ≠ 0 → no se propone commit. Los dos en fase 1: el gate bloquea por ausencia, frescura o incoherencia, no por su veredicto.

### Deploy / infraestructura / producción

- **Agentes:** `~~hugo-vigilancia-diaria~~ ⚠️` · `~~bruno-perf-cop~~ ⚠️`
- **Skills:** `~~claude-code-referencia~~ ⚠️`
- **Comandos:** `/deploy`
- **Plugins/MCP:** `claude-security` · `aikido`
- **Rules:** `governance.md` · `agent-security.md` · `verification.md`

> **Orden recomendado.** Deploy a producción **siempre requiere aprobación** (`governance.md` §2). IaC generada por IA: región y sizing explícitos o no se aplica (`agent-security.md` §7) · **G2** antes de desplegar: `gate_deps.py` (vulnerabilidades HIGH+ con arreglo, lockfile, Actions por SHA, scripts de instalación; 2 = no medido, no es verde) y el SBOM como artefacto del release.

### Esto necesita varios agentes (paralelo, orquestación, grafo de agentes)

- **Skills:** `otto` · `~~workflow-creator~~ ⚠️` · `~~claude-code-referencia~~ ⚠️`
- **Workflows:** `/plan-research` · `/review-branch` · `/bug-sweep` · `/codebase-map`
- **Rules:** `parallelization.md` · `goal-vs-loop.md`

> **Orden recomendado.** **Primero el test de independencia** (`parallelization.md` §0): si la respuesta de B cambia según A, es UNA tarea, no dos. Repartir mal cuesta N contextos para una respuesta peor. Después: ¿basta con enterarse? → pizarra. ¿Hace falta rebatir? → teams. ¿Orquestación repetible? → workflow.

### Crear pantallas nuevas: una, un embudo o una webapp entera

- **Agentes:** `pol-product-advisor` · `~~conrado-cro-auditor~~ ⚠️`
- **Skills:** `producto` · `~~business-manager~~ ⚠️` · `disenar-pantalla` · `nueva-pantalla` · `~~disenar-conversacion~~ ⚠️` · `design`
- **Comandos:** `/schema` · `/visual-map`
- **Plugins/MCP:** `frontend-design` · `superdesign`
- **Rules:** `plan-docs-structure.md` · `html-output.md` · `verification.md`

> **Orden recomendado.** **Empieza por `/producto`, no por el código: es el paso 11 de 12.** Recorre objetivo → recorrido con bifurcaciones → mapa de páginas → ficha por pantalla → wireframe. Y **pregunta por CADA pantalla quién la diseña** (🤖 agente · 🤝 a medias · ✍️ tú en el canvas `design`). Los documentos viven en `.docs/core/producto/`.

### Escribir la documentación del proyecto (arquitectura, datos, manual…) y sacarla en PDF

- **Agentes:** `pol-product-advisor` · `priya-privacy-auditor` · `desarrollador-backend` · `sofia-pentester`
- **Skills:** `documentar` · `pdf-premium` · `~~codebase-onboarding~~ ⚠️`
- **Comandos:** `/visual-map` · `/schema`
- **Plugins/MCP:** `playwright`
- **Rules:** `plan-docs-structure.md` · `verification.md` · `html-output.md`

> **Orden recomendado.** **`/documentar`: pregunta primero QUÉ documentos y para QUIÉN** → agentes en paralelo con el bloque común → capturas de la maqueta → Pol (huecos) + Priya (qué no sale) → `construir_pdf.py --separados`, que aborta si un diagrama no se lee. A Drive, el PDF; nunca los `.md`.

### Diseñar o evaluar un agente conversacional / chatbot

- **Agentes:** `~~nadia-chatbot-evaluator~~ ⚠️` · `~~dario-commerce-guardrails~~ ⚠️` · `~~teo-llm-redteam~~ ⚠️` · `~~rafa-retrieval-engineer~~ ⚠️` · `~~ivan-agent-runtime~~ ⚠️` · `~~conrado-cro-auditor~~ ⚠️` · `~~marta-revenue-attribution~~ ⚠️`
- **Skills:** `~~disenar-conversacion~~ ⚠️` · `~~agent-evals~~ ⚠️` · `~~eval-estadistica~~ ⚠️` · `~~vector-db~~ ⚠️` · `~~langgraph-debug~~ ⚠️`
- **Workflows:** `~~/matrix-eval-harness~~ ⚠️`
- **Rules:** `~~fairness-audit.md~~ ⚠️` · `verdict-contract.md`

> **Orden recomendado.** **Diseñar va antes que medir**: `disenar-conversacion` decide persona, fronteras, fallback y qué NO puede prometer, y escribe el **golden set ANTES de construir** — si se fabrica después, el listón se ajusta al resultado. Luego: Darío ataca los guardarraíles, **Teo** hace el red team OWASP LLM (inyección, tools, fugas, gasto), `agent-evals` monta el gate, Nadia mide. **Si el bot pierde la memoria, repite el saludo o ignora una bandera**, no es diseño ni evaluación: es estado y runtime, de **Iván** y de `langgraph-debug`. **Y todo bot lleva G6**: `gate_doble_obediente.py <proyecto> --correr` exige la suite «doble obediente» (`templates/seguridad-bot/`) y la corre: aunque el modelo obedezca la inyección, no puede hacer daño. **Y G5** (`gate_agente_superficie.py`) mira las tools por AST; la ventana de 24 h, los topes de coste y los enlaces están en `templates/canal-bot/`. **Al construirlo**, precio, stock, oferta y efectos los pone el código: `patterns/stack/agente-guardarrailes.md` y `templates/bot-guardrails/`. **Si el bot vende**, qué ofrece y cuándo, el «sí» y la rúbrica los pone `templates/bot-sales/`: Nadia mide la venta (modo venta), Conrado el embudo del chat y Marta cuánto vende, con grupo de control.

### Construir o depurar un agente IA con tools (LangGraph)

- **Agentes:** `~~ivan-agent-runtime~~ ⚠️` · `~~rafa-retrieval-engineer~~ ⚠️` · `~~dario-commerce-guardrails~~ ⚠️` · `~~teo-llm-redteam~~ ⚠️` · `~~bruno-perf-cop~~ ⚠️`
- **Skills:** `~~instrumentar-agente~~ ⚠️` · `~~langgraph-debug~~ ⚠️` · `~~disenar-conversacion~~ ⚠️` · `~~agent-evals~~ ⚠️` · `~~eval-estadistica~~ ⚠️` · `~~vector-db~~ ⚠️`
- **Workflows:** `~~/matrix-eval-harness~~ ⚠️`
- **Plugins/MCP:** `claude-security`
- **Rules:** `verdict-contract.md` · `agent-security.md`

> **Orden recomendado.** **El patrón de casa está en `patterns/stack/agente-observabilidad.md` y `agente-tools.md`** (gate: `pattern_check_agente.py`, en sombra). Lo primero, siempre: **medir qué está apagado** — LangGraph ya graba con el checkpointer y casi nadie lee `get_state_history()`. Las trazas van a **Langfuse autoalojado** (§4 del patrón), no a un SaaS. **Si no recuerda, repite el saludo o ignora una bandera**, es estado: **Iván** y `langgraph-debug` §1-2. Si la tool falla, `langgraph-debug` §4: lo que hace `ToolNode` depende de la versión de `langgraph-prebuilt` (desde la 1.0.2, la excepción tumba el turno). Y una tool es una API cuyo cliente se equivoca: contrato, validación y error devuelto, nunca lanzado. Que una inyección no pueda usarla para hacer daño lo prueba G6 (`templates/seguridad-bot/`).

### Configurar el harness (agentes, skills, hooks, plugins, settings)

- **Skills:** `~~project-setup~~ ⚠️` · `~~create-agent~~ ⚠️` · `~~update-agent~~ ⚠️` · `~~check-agent~~ ⚠️` · `~~skill-authoring~~ ⚠️` · `~~claude-code-referencia~~ ⚠️` · `auto-dream-memory` · `otto`
- **Plugins/MCP:** `skill-creator` · `hookify` · `agent-sdk-dev`
- **Rules:** `layer-decision.md` · `agent-security.md` · `agent-autonomy-ladder.md` · `self-improvement-loop.md`

> **Orden recomendado.** **Elige la capa ANTES de escribir** (`layer-decision.md`): si el incumplimiento duele, es un hook, no un párrafo. >3 ficheros en `.claude/` → staging (1 permiso).

---

## 3. Settings según el alcance

| Alcance | Qué cambia |
|---|---|
| **Proyecto normal** | `permissions.allow` amplio para editar/tests · hooks base (RAM, formato, progreso, audit) · `enableAllProjectMcpServers: false` |
| **Con PII / pagos / cliente (tier 2)** | Se empieza **denegando**: `deny` de `.env*`, `~/.ssh`, `~/.aws` · `ask` en push/deploy/migraciones · MCP solo con allowlist explícita · auditores `priya-privacy-auditor` y `sofia-pentester` en el ciclo |
| **Trabajo desatendido / nocturno** | Criterio de parada explícito · **Stop hook** determinista (ojo: el harness lo anula tras 8 bloqueos) · tope de presupuesto e iteraciones · commit sí, **push y merge NO** · ver `rules/goal-vs-loop.md` §Modo noche |
| **Rol no técnico** | Solo la capa de **slash commands**. No abre settings, no escribe prompts. `rules/human-role-layers.md` |

---

## 4. Fundamentos de Claude Code (la referencia del harness)

Son la referencia de *cómo funciona el harness*, no procedimientos de proyecto. Las 8 `boris-*` se retiraron el 2026-10-20: su contenido está en `claude-code-referencia`.

- **Fundamentos del harness (CLAUDE.md, MCP, hooks, subagentes, diagnóstico, contexto):** 
- **Ejecución y autonomía (worktrees, permisos y auto mode, sandbox, mods y plugins):** 
- **Memoria y calidad:** `auto-dream-memory`

---

## 5. Lo que NO se usa, y por qué

Un mapa que solo lista lo bueno hace perder el tiempo dos veces.

| Pieza | Por qué no |
|---|---|
| graphify / grafo del código en ESTE repo | Veredicto 2026-08-05 + piloto medido: es configuración, no un codebase (~120 ficheros de código). Sí es candidato en los derivados con código real. |
| 10 de los 13 auditores-persona (escrito el 2026-08-20) | Nunca han corrido. Cuentan como **checklist, no como cobertura** (`qa-loop.md` §2b). |
| Marketplaces de terceros del catálogo de plugins | `claude-code-workflows`, `dev-gom-plugins`, `ui-ux-pro-max-skill` no están añadidos ni verificados. Antes de instalar: grep anti-inyección de `agent-security.md` §5. |

---

## Anti-patterns

- ❌ Editar este fichero a mano → se regenera y pierdes el cambio. Toca `gen_agent_system.py`.
- ❌ Leer el mapa entero antes de cada tarea → usa `/otto <escenario>` o deja que el hook inyecte la fila.
- ❌ Tratar una fila como obligatoria: es **lo que tienes**, no lo que debes usar. El criterio sigue siendo tuyo.
- ❌ Añadir una pieza al harness y no añadirla aquí → vuelve a ser invisible, que es el fallo que esto arregla.

