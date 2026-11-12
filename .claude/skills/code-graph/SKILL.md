---
name: code-graph
description: >-
  Usar cuando haga falta un mapa ESTRUCTURAL y verificable del código: 'grafo del código', 'indexa
  el repo', 'de dónde se llama X', 'qué se rompe si toco Y', 'blast radius', 'who calls X'. Produce
  graph-dataset.json, que alimenta a /visual-map. NO usar para: el set HTML (/visual-map), un
  resumen markdown (/codebase-map) ni el diff de rama (/review-branch).
user-invocable: true
metadata:
  version: 1.0.0
  author: tech-lead-template
  category: workflow
  updated: 2026-08-05
---

# code-graph — el fact base estructural del repo

## Principio

`/visual-map` produce hoy `NODES/EDGES/ENTITIES/RELATIONS` que son **prosa→JSON de un LLM**: los `id` se
reinventan en cada regeneración, las coordenadas x/y se calculan a ojo (`visual-map-datos.js:64-73`) y
`files`/`deps` no se verifican contra el repo. Esta skill introduce una **fuente de hechos determinista**
(AST, local, sin tokens sobre código) y deja al LLM lo que sí sabe hacer.

> **Una sola fuente de hechos (`graph-dataset.json`), tres consumidores.**
> El grafo aporta los **hechos**; el LLM aporta el **significado**.

**Backend intercambiable por diseño.** La skill se llama `code-graph`, no por el nombre de ninguna
herramienta: define un **contrato de entrada** (`graph-dataset.json`) y admite varios extractores
(Graphify vía CLI, repo-map propio estilo aider con tree-sitter+PageRank, u otro). El template **no**
debe quedar acoplado a un proyecto pre-1.0.

## Cuándo activar — y cuándo NO

Disparadores: 'grafo del código', 'indexa el repo', 'de dónde se llama X', 'qué se rompe si toco Y',
'blast radius', 'regenera el grafo', '/code-graph', 'code graph', 'index the repo', 'call graph',
'who calls X', 'impact of changing X'. Produce graph-dataset.json (hechos: nodos, aristas,
fan-in/out con file:line) que ALIMENTA a /visual-map y la pestaña code-graph.html de un plan · NO
confundir con /visual-map (genera el set HTML; esta skill le da los datos), /codebase-map (resumen
markdown) ni /review-branch (diff de rama). PREGUNTA SIEMPRE backend y alcance antes de indexar.

| Activar | NO activar |
|---|---|
| Proyecto con **código real** (Django, React, WordPress…) y ≥ ~100 ficheros | **Este repo (tech-lead-template)**: es config `.claude/` + HTML, no un codebase — el propio doc de Graphify dice que por debajo de unas decenas de ficheros el valor es nulo |
| Gate de plan de una tarea grande (`plan-gates.md`, Gate B) | Cambio de copy/estilo o bugfix de 1-3 archivos |
| Pregunta de impacto: "¿qué se rompe si toco X?" antes de un merge | Cuando basta un `grep` puntual — no indexes un repo para una pregunta |
| Refrescar un grafo obsoleto (sello de git sha desfasado) | Con `pytest` en curso, o si `check-ram.sh` no da vía libre (ver paso 1) |

> ⚠️ **La evidencia NO respalda "mejores respuestas".** El único estudio con n grande
> (arXiv 2603.27277, 31 repos) mide el enfoque de grafo **por debajo** del baseline de exploración de
> ficheros: 83% vs 92% de calidad, a cambio de 10x menos tokens y 2.1x menos tool calls. La ganancia
> defendible es **coste y determinismo**, no precisión. No vendas otra cosa en un informe.

## Paso 0 — preguntar SIEMPRE (AskUserQuestion)

1. **Backend**: extractor externo · repo-map interno · solo re-render con el dataset existente.
2. **Alcance**: qué rutas indexar y qué excluir (worktrees, venv, node_modules, dist, `.docs/`).
3. **Destino**: plan actual (`.docs/plans/<plan>/`) o promoción a `.docs/schemas/`.

Nunca indexes sin confirmar: la indexación es la parte cara y la que puede tumbar el servidor.

## Procedimiento

1. **Pre-flight (BLOQUEANTE — si falla, aborta; nunca "lo intento igual")**
   ```bash
   bash .claude/hooks/check-ram.sh                      # umbral y tope, calculados para esta máquina
   ps aux | grep claude | grep -v grep | wc -l         # < 3
   pgrep -f pytest && echo "ABORTAR: tests en curso"
   ```
   No existe cap de RAM configurable en los extractores conocidos: el control es **tuyo, aquí**.

2. **Aislamiento.** Salida **fuera del workspace** (scratchpad). Si tiene que vivir dentro:
   `graphify-out/` y `graph.json` en `.claudeignore` **y** `.gitignore`. (Esto decía que escribir en el
   workspace invalidaba el prompt cache con un coste 5-10x: no es así, editar ficheros del repo no
   rompe el caché —doc `prompt-caching` §Editing files in your repository, 2026-10-20—; la razón que
   queda es no ensuciar el repo ni el índice. Y `.claudeignore` no tiene efecto en Claude Code —doc
   `permissions`—: para que Claude no lo lea hace falta un deny `Read(...)`.)
   Excluir siempre `worktrees/` — indexarlos multiplica el grafo por ~30.

3. **Build en frío, code-only, sin backend LLM**, medido:
   ```bash
   /usr/bin/time -v <extractor> ... 2>&1 | grep -E "Maximum resident|Elapsed"
   ```
   Registra **RAM pico y wall time en `PROGRESS.log`**. Versión **pineada** y publisher verificado.
   **Full rebuild o nada**: el update incremental de los extractores actuales pierde aristas en
   silencio (clúster de issues abierto) — y un grafo obsoleto es peor que no tener grafo.

4. **Reducción** → `.claude/templates/report_kit/graph_reduce.py`: pliega símbolos a módulo/fichero,
   conserva top-N por fan-in/fan-out, **calcula el layout de forma determinista por comunidad**
   (esto es lo que mata el anti-pattern "líneas que cruzan las cajas" de `plan-docs-structure.md`),
   separa aristas `EXTRACTED` de `INFERRED`, y **capa el tamaño**: ~800 nodos / ~2.000 aristas / < 1MB.

5. **Render** de `code-graph.html` con el dataset inlineado en el bloque `===== EDITA AQUÍ =====`,
   mismo contrato de campos que `architecture.html:101-113` (`id/label/group/desc/files/deps`).

6. **Alimentar `/visual-map`**: pasar `graph-dataset.json` a los seams `visual-map-datos.js:42-53` (Scout),
   `:50-55` (Read) y `:59-68` (Synthesize). El LLM pasa a **etiquetar, agrupar y narrar** — no a
   adivinar estructura. Los `FLOWS` (`{persona, goal, steps}`) siguen siendo suyos: no salen de un AST.

7. **Verificación obligatoria** (`file://` está bloqueado en Playwright):
   `python3 -m http.server --bind 127.0.0.1` + `.claude/scripts/screenshot.py`, consola sin errores, y
   **spot-check manual de 20 aristas** contra el código bajo `rules/verdict-contract.md`.
   **Sin spot-check, el grafo no se publica.**

8. **Sello de frescura**: `git rev-parse HEAD` + fecha + conteos, visible en la página.
   `flag-visual-staleness.sh` compara contra ese sello, no contra el mtime del HTML.

## Gate de adopción (antes de usarlo como fuente en un proyecto)

| Métrica | Umbral |
|---|---|
| Precisión del spot-check | **≥ 18/20** aristas correctas |
| RAM pico | **cabe en una sesión** (la «RAM por sesión» de `check-ram.sh --explain`) |
| Wall time del build en frío | **< 10 min** |
| `graph-dataset.json` | **< 1MB** |

Mide **por stack**: el análisis estático es ciego al **dispatch dinámico**, así que se espera que
falle en WordPress (hooks/filtros) y funcione en Django/JS. Si un stack no pasa el gate, se adopta
solo para los que sí y **se documenta**.

## Anti-patterns

- ❌ Ejecutar los instaladores del extractor (`install`, `claude install`, `hook install`): escriben en
  `~/.claude/skills/`, `~/.claude/settings.json` y `CLAUDE.md`, y meten `PreToolUse` sobre
  `Bash|Grep` y `Read|Glob` — rompen el harness, la regla de caché y el límite de RAM.
- ❌ Salida dentro del workspace sin `.gitignore` → ensucia el repo y el índice (no rompe el caché).
- ❌ Indexar con worktrees activos y sin exclusión → ~x30 nodos, cientos de MB.
- ❌ Usar el update **incremental** como fuente de verdad → pierde aristas en silencio. Full rebuild.
- ❌ Commitear `graph.json` (puede superar el límite de 100MB por blob). Se versiona solo el
  `graph-dataset.json` reducido, como snapshot del plan.
- ❌ Publicar las salidas de documentación propias del extractor (`graph.html`, `wiki/`) como
  entregable → duplican `.docs/`, con otra nav y otros tokens, y no son self-contained.
- ❌ Afirmar una arista `INFERRED` como hecho verificado → va con `confidence` degradada
  (`rules/verdict-contract.md`).
- ❌ Correr esto sobre el propio `tech-lead-template` → no es un codebase.
- ❌ Prometer "mejores respuestas" → la evidencia dice coste y determinismo, no precisión.

## Ejemplos

**Usuario:** «¿qué se rompe si cambio el serializer de Client?»
→ Pre-flight; si hay dataset fresco (sello == HEAD) responder con fan-in/callers desde
`graph-dataset.json` **citando `file:line`**; si está stale, avisar y ofrecer rebuild antes de responder.

**Usuario:** «genera los mapas del plan» (tarea grande, Gate B de `plan-gates.md`)
→ Paso 0 (backend/alcance/destino) → pipeline 1-8 → `/visual-map` alimentado por el dataset →
comparar contra la versión LLM-only en `visual-diff.html`.

**Usuario:** «indexa el template»
→ **Rechazar con motivo**: no es un codebase; ofrecer hacerlo sobre un proyecto derivado real.

## Integraciones

- **`/visual-map`** — consumidor principal. Esta skill le da los hechos; él produce el set HTML.
- **`/codebase-map`** — hoy **duplica** el pipeline scout→read→synthesize (`codebase-map.js:16-26`,
  `:43-47`, con un `SUBSYS_SCHEMA` casi idéntico al de `visual-map-datos.js:28-39`). Debe degradarse a una
  **vista markdown del mismo fact base**; no añadir un tercer extractor sin resolver esto.
- **`/review-branch` y `code-review-gate`** — el blast radius entra como input del gate `READY_MERGE`
  de `speckit-workflow.md`.
- **`parallelization.html`** — las comunidades del grafo y sus aristas dan los cortes con menos
  acoplamiento: qué worktrees son de verdad independientes y en qué orden mergear.
- **Plugin LSP nativo** (`pyright-lsp`, `typescript-lsp`, `php-lsp`) — **complementario, no rival**:
  LSP da precisión de tipos en vivo tras cada edición; el grafo da mapa estructural persistente.
  Ojo: compite por el mismo presupuesto de RAM.

## Related

- `.claude/rules/plan-docs-structure.md` — dónde vive `code-graph.html` dentro de un plan.
- `.claude/rules/html-output.md` — self-contained, botón "copy back", verificación visual.
- `.claude/rules/verdict-contract.md` — `EXTRACTED`/`INFERRED` mapean a `confidence`.
- `.claude/rules/parallelization.md` — límites de RAM e instancias que hacen bloqueante el paso 1.
## El veredicto sobre graphify, medido en un piloto real (GFY-5 · GFY-6, 2026-08-21)

Se probó sobre un proyecto con código de verdad (`proxera_musa`). **Sí, con tres condiciones, y
ninguna es opcional:**

1. **En frío y bajo demanda. Sin hooks, sin MCP, sin watch.** El incremental tiene fallos abiertos
   upstream y ninguno cerrado: `graphify update` **pierde aristas en silencio** (#2406), nodos
   fantasma tras un merge (#2418), digests obsoletos (#2464) y el MCP **cachea el grafo al arrancar
   y no recarga** (#874). El rebuild completo cuesta **14 segundos**: no hay ninguna razón para
   arriesgarse.
2. **Filtrando la prosa** (`--solo-codigo`). Sin eso el mapa mezcla el README con los modelos —
   medido: 6.457 nodos de prosa de 8.611 al apuntarlo a un `.claude/`.
3. **Sabiendo qué compra: coste y determinismo, NO acierto.** El único estudio con muestra grande
   mide el enfoque de grafo por **debajo** de leer ficheros (83% vs 92% de calidad de respuesta) a
   cambio de 10× menos tokens. Venderlo como «mejores respuestas» es vender lo que el dato no dice.

> **Por qué esto está aquí y no en una nota al pie.** Un grafo obsoleto es **peor que no tener
> grafo**: da respuestas equivocadas con apariencia de estructura, y nadie sospecha de un diagrama.
> Es el mismo motivo por el que se retiraron los dos `structure.html` que enseñaban un Django
> inventado.

**Cuándo NO usarlo, dicho igual de claro:** para una pregunta puntual, `grep` + leer los ficheros da
más calidad. Graphify gana cuando la pregunta es «¿quién llama a esto exactamente?» sobre una pieza
muy acoplada — y cuando esa pregunta **se repite**.

- `_archive/2026-10-19/planes-cerrados/2026-08-05-graphify-adopcion/` — el research completo con el veredicto y sus fuentes.
