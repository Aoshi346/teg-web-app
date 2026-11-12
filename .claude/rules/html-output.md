---
paths:
  - ".claude/docs/html/**"
  - ".docs/html/**"
  - ".claude/templates/html/**"
  - ".claude/skills/html-suelto/**"
  - ".claude/skills/pdf-premium/**"
---
# Salida HTML — cuándo entregar un artefacto en vez de markdown

> **Cuándo aplicar:** cuando el output es **espacial** (diffs, diagramas), **comparativo**
> (varias opciones lado a lado), **interactivo** (sliders, drag, toggles) o un **documento
> recurrente** que la gente escanea (status, post-mortem, explainer). Entonces un único `.html`
> autocontenido comunica mucho mejor que un muro de markdown.
>
> **NO aplicar:** respuestas conversacionales, un párrafo, un snippet corto, un sí/no. Markdown
> sigue siendo el default para la mayoría de turnos. HTML es para artefactos que se guardan,
> se comparten o se manipulan.
>
> **Relacionado:** plugin `playground` (ver `MCP_PLUGINS.md`), skill `html-suelto` (antes
> `html-artifact`), **`rules/output-choice.md`** (qué informe usar y cómo se entrega) y
> **`rules/report-kit.md`** (el sistema canónico de informes multi-página).
> **Fuente de la doctrina:** Thariq Shihipar (Claude Code) vía
> `resources/articulos/Claude Code HTML Output_ Why Markdown Lost and How to Switch…html`.

---

## Convención (no negociable)

1. **Un solo archivo `.html`**, autocontenido: CSS y JS **inline desde el primer Write**. Sin CDN,
   sin build, sin dependencias externas, sin `<link>`/`<script src>` remotos, **nunca** un
   `assets/*.css` relativo (aunque sea "temporal"). Debe abrir en cualquier browser offline.
   Check pre-DONE: `grep -L 'stylesheet' *.html` debe listar **todos** los `.html` (ninguno enlaza CSS).
2. **Tipografía del sistema** (`-apple-system, Segoe UI, Roboto…`) — no Google Fonts.
   ⚠️ **Excepción acotada (2026-09-12): los artefactos de MARCA y los BOCETOS** — `brand.html` de la
   skill `marca` y los bocetos de `disenar-pantalla` — **sí pueden cargar la tipografía real**, porque
   su trabajo es precisamente enseñar cómo se va a ver. Esta regla hacía imposible representar un kit
   de marca con tipografía propia, que es el entregable de la fase 1 de `rules/motores-de-diseno.md` Parte F. Dos
   condiciones: **fallback declarado siempre** (sin red se sigue leyendo) y **aviso en la página** de
   que esa fuente es de la marca. Todo lo demás del harness —informes, dashboards, report-kit— sigue
   con tipografía del sistema: tienen que abrir offline.
3. **Botón "copy back"**: todo artefacto incluye un botón que copia algo reutilizable al
   portapapeles (el prompt de configuración, el resultado como markdown, el diff de cambios…).
   El humano queda en el loop: ajusta en el HTML → copia → lo pega de vuelta al agente.
4. **Guardado** en `.docs/html/<slug>-<YYYY-MM-DD>.html` (o en la carpeta del plan, si es de un
   plan). Nunca en la raíz del repo. (`.claude/docs/html/` era el otro destino hasta el 31-10: ORD-4.)
5. **Verificación visual**: tras generarlo, ábrelo (servidor local + Playwright o
   `python3 -m http.server --bind 127.0.0.1`) y confirma render sin errores de consola. El `file://` suele estar
   bloqueado en el MCP de Playwright — levanta `python3 -m http.server --bind 127.0.0.1` y navega a `http://127.0.0.1`.
6. **Calidad editorial**: el listón es la galería de referencia (abajo), no "HTML que funciona".
7. **Gotcha de tokens de color**: si defines los tokens como **tripletes HSL crudos**
   (`--ux: 210 80% 52%`), **nunca** los uses directos como color (`style="background:var(--ux)"` →
   color inválido → **transparente**, p.ej. texto blanco sobre blanco). Envuélvelos: `hsl(var(--ux))`.
   En JS expón helpers: `pcol(p)` → `hsl(<triplete>)` (para color directo) y `praw(p)` → el triplete
   (para asignar a otra var, p.ej. `--pc`). Implementación de referencia: el antiguo
   `progress-dashboard.html`, archivado el 2026-10-19 en `_archive/2026-10-19/templates/html/` (LI-12)
   — se consulta, no se copia. (Los tokens **hex** de `base.html` no tienen este riesgo.)

---

## Qué informe usar y cómo se entrega → `rules/output-choice.md`

El catálogo único (las 12 preguntas, el perfil del report-kit, «Lo que pediste y dónde está», el
enlace `http://localhost:<puerto>/…` comprobado con `enlace.py`, 127.0.0.1 + túnel y **nunca un Artifact
de claude.ai**) vive en `rules/output-choice.md` desde la 3.18 (AN-2, AN-D2). Aquí queda solo cómo se
hace bien un HTML suelto.

---

## Los 3 tiers (empieza por Tier 1, sube según se naturalice)

### Tier 1 — Empezar aquí (baja fricción, alto retorno)
| Caso | Qué genera | Demo de referencia |
|------|------------|--------------------|
| **Specs / Planning** | Grid de N enfoques lado a lado, cada uno con su trade-off | `01-exploration-code-approaches` |
| **Status / Reports** | Métricas + qué se hizo / qué se atrasó + chart + timeline coloreado | `11-status-report` |
| **Research / Learning** | Explainer con secciones colapsables, code samples en tabs, glosario | `14/15-research-*` |

### Tier 2 — Alto valor
| Caso | Qué genera | Demo de referencia |
|------|------------|--------------------|
| **Code review / PR writeup** | Diff anotado con notas al margen, tags de severidad, jump links | `03-code-review-pr`, `17-pr-writeup` |
| **Design / Prototypes** | Componente real con sliders para tunear parámetros (easing, etc.) + copy | `07-prototype-animation` |
| **Architecture diagrams** | SVG con nodos clicables (dependencias, hot path) en vez de ASCII | `04-code-understanding`, `13-flowchart-diagram` |

### Tier 3 — Avanzado
| Caso | Qué genera | Demo de referencia |
|------|------------|--------------------|
| **Custom editing interface** | Cards arrastrables (Now/Next/Later/Cut) o toggles, con export | `18-editor-triage-board`, `19-editor-feature-flags` |
| **Prompt tuner** | Editor split: template a la izq con slots resaltados, inputs live a la dcha | `20-editor-prompt-tuner` |
| **Slide deck** | `<section>` + 20 líneas JS = deck navegable por flechas, sin Keynote | `09-slide-deck` |

> **Caso "agent-config editor"** (Tier 3, usado por `create-agent`): toggles de skills/MCPs/plugins
> agrupados por área, con avisos de dependencia (p.ej. Tier 2 ⇒ `code-review-gate`) y botón
> "Exportar prompt". Patrón 1:1 del demo `19-editor-feature-flags`.
> Ejemplo vivo: `.claude/templates/html/config-builder.html`.

### Caso "informe total" (Tier 3 — el sistema canónico para informes de proyecto/plan/incidencia)

**Report-kit** (`.claude/templates/report_kit/` + `rules/report-kit.md`): set multi-página generado
desde un `report.json` único — `index` (resumen + mapa conceptual SVG) · `structure` (grafo del
código, contrato `/code-graph`) · `dashboard` (tareas con goals + evidencias + decisiones
persistentes) · `results` (verdicts con doble evidencia + imágenes base64) · `otto` (copiloto).
Perfiles `proyecto`/`diseño`/`incidencia`/`minimo` deciden qué pestañas lleva. Qué perfil toca:
`rules/output-choice.md` §2. Los casos de abajo siguen valiendo para piezas sueltas.

### Caso "plan dashboard" interactivo → **es el report-kit**, no hay segunda opción

Para el dashboard de un plan con decisiones que persisten, el sistema es el **report-kit** de arriba
(`rules/report-kit.md`): mismo trabajo, un solo schema y la persistencia con el bug de snapshot ya
arreglado. La skill `/plan-dashboard` que enrutaba aquí **se archivó el 2026-08-22** — llevaba desde
TPL-1 W3 declarando en su propia cabecera que el sistema canónico era otro, y seguir ofreciéndola
mandaba planes nuevos al camino legacy (lo detectó `pol-product-advisor`, hallazgo QS1).

**Ya no queda excepción.** La variante lite de un archivo (`plan-dashboard.html`, en `templates/html/`), su
hermana `progress-dashboard.html` y el sistema LEGACY `speckit_dashboard/` se archivaron el
2026-10-19 en `_archive/2026-10-19/templates/` (LI-12): mantener alternativas invitaba a usarlas y a
que divergieran, y el report-kit cubre lo mismo con decisiones que persisten. Para solo **mirar** un
plan basta el report-kit en modo estático (`build.py` y abrir el HTML, sin servidor: las decisiones
quedan en localStorage, `rules/report-kit.md`). Los dashboards que se
generaron con ellas siguen abriéndose: son autocontenidos.

### Caso "mapa de arquitectura/concepto vivo" (`/visual-map`)

Para tareas grandes (durante el **gate de plan**, ver `rules/plan-gates.md`) genera el **set
multi-página de mapas visuales**: un `.html` autocontenido por página que comparten la misma
`.topnav` y los tokens de `base.html`. Lo orquesta el comando **`/visual-map`**
(`.claude/commands/visual-map.md` → workflow `.claude/workflows/visual-map-datos.js`), que lee el código
real y emite los datasets (`NODES`/`EDGES`, `ENTITIES`/`RELATIONS`, `FLOWS`) listos para pegar en
las plantillas:

- `architecture.html` — diagrama de componentes clicable (SVG data-driven).
- `data-model.html` — entidad-relación (entidades → campos/relaciones).
- `user-flows.html` — flujos de USUARIO paso a paso (pantalla + endpoint por paso).
- `scope-and-boundaries.html` · `integrations.html` · `parallelization.html` — alcance, servicios
  externos y plan de paralelización (swimlanes + orden de merge).
- `index.html`/hub + `nav-partial.html` — índice y nav compartida.

El hook **`flag-visual-staleness.sh`** (Stop) anota en `PROGRESS.log` cuando el código cambia tras
la última regeneración, recordando correr `/visual-map`. **Complemento opcional**: el plugin
`playground` (vistas Concept Map / Code Map) para exploración interactiva sobre la marcha — el set
de `/visual-map` es autocontenido y no depende de él.

### Caso "informe de evidencia" (Tier 1 Reports · imágenes base64) — skill `feedback-audit`

Para un informe que **embebe muchas capturas** (auditoría de feedback, before/after, QA visual), no
enlaces a ficheros: re-comprime cada imagen con Pillow (resize ~820px, quality ~52) y embébela como
`data:image/jpeg;base64` en **un solo HTML** que abre offline (sin servidor, sin CDN). El generador de
referencia es `.claude/templates/feedback_audit/build_report.py` (filtros por estado/página/epic,
botón "copiar pendientes (md)", export PDF vía `window.print()`, tokens de `base.html`). Lo orquesta la
skill **`feedback-audit`**. **Captura enriquecida** para alimentarlo: `scripts/screenshot.py --multi
--dom --audit-links` (1 página) o `templates/feedback_audit/capture_pages.py` (masivo). El veredicto
por item sigue `rules/verdict-contract.md`.

---

## Galería de referencia (listón de calidad)

> **¿Y si el entregable es un PDF?** (propuesta, informe firmable, one-pager): skill **`pdf-premium`**
> — Playwright/Chromium headless con CSS grid moderno y page breaks controlados. Misma filosofía de
> tokens; el HTML sigue siendo el formato para lo interactivo, el PDF para lo imprimible.

**https://thariqs.github.io/html-effectiveness/** — 20 HTML autocontenidos en 9 categorías
(Exploration/Planning · Code Review · Design · Prototyping · Diagrams · Decks · Research ·
Reports · Custom Editors). Cada demo es a su vez un único `.html`. Úsala como vara de medir:
si tu artefacto no se acerca a ese nivel editorial, no está listo.

Companion del post *"The unreasonable effectiveness of HTML"*.

---

## Prompt-templates rápidos (copia y rellena)

- **Planning**: "Genera N enfoques distintos para [X]. Layout en grid en un solo HTML para
  compararlos lado a lado. Etiqueta cada uno con su trade-off."
- **Status**: "Lee [fuentes] y produce un status HTML semanal: qué shipeó, qué se atrasó, un
  chart de progreso y un timeline coloreado. Optimiza para escaneo de lunes por la mañana."
- **PR writeup**: "Crea un HTML que describa este PR: diff real con anotaciones al margen,
  findings coloreados por severidad y jump links. Asume que el reviewer no conoce [área]."
- **Architecture**: "Lee el codebase y produce un diagrama HTML de arquitectura: relaciones entre
  módulos, entry points, hot path resaltado, nodos clicables que muestren dependencias."
- **Slides**: "Convierte [contenido] en un deck HTML navegable por flechas, un solo archivo, sin
  build."

---

## Cuándo HTML es la elección EQUIVOCADA (caveats de la fuente, no negociables)

| Caveat | Qué significa aquí |
|---|---|
| **Los diffs de HTML ensucian el git review** — el downside que la propia fuente reconoce como el mayor | Por eso el report-kit tiene `report.json` como **fuente** y las páginas son **regenerables** (`build.py`): revisa el JSON, no el HTML. No metas lógica solo-en-el-HTML |
| **Coste 2-4x en tokens de salida** | Para una respuesta corta o un sí/no, markdown. El HTML se gana cuando el documento se guarda, se comparte o se manipula |
| **Generación 2-4x más lenta** | No conviertas a HTML lo que el usuario necesita YA en el chat |
| **Los ficheros de CONFIG siguen siendo markdown** | `CLAUDE.md`, `AGENTS.md`, `SKILL.md`, `rules/*.md`, `INDEX.md`: el shift aplica al **output del agente**, NUNCA al **input/config** que humanos escriben y agentes leen |
| **Hand-editing favorece markdown** | Si el humano edita el fichero a mano (en vez de pedírselo al agente), markdown gana |

> **Shareability**: un `.html` autocontenido abre en cualquier navegador, sin visor ni adjuntos. Se
> sirve en `127.0.0.1` y llega por túnel (o se entrega el fichero); **nunca** se publica como Artifact
> de claude.ai ni en un host público sin que el Usuario lo pida (`rules/output-choice.md` §3).

## Anti-patterns

- ❌ HTML con `<script src="https://cdn…">` o Google Fonts → rompe offline, no es autocontenido.
- ❌ Guardar el `.html` en la raíz del repo (ensucia `git status`).
- ❌ Olvidar el botón "copy back" → se rompe el loop humano↔agente.
- ❌ Reportar DONE sin abrir el HTML en un browser y revisar la consola.
- ❌ Entregar un informe que no empieza por «Lo que pediste y dónde está», o dar un enlace sin
  comprobarlo (`enlace.py`) o con una ruta de fichero en vez de `http://localhost:<puerto>/…`.
- ❌ Publicar un informe como Artifact de claude.ai (`rules/output-choice.md` §3).
- ❌ Usar HTML para un sí/no o un párrafo (over-engineering del output).
- ❌ HTML feo "que funciona" → el listón es la galería de referencia, no menos.

---

_Rule version: 1.2 · 2026-10-31 — sub-ola 3.18: «Qué informe usar» pasa a `rules/output-choice.md`;
destino único `.docs/html/`; la skill se llama `html-suelto`. Antes: 1.1 · 2026-10-21 — sub-ola 2.15: §«Qué informe usar» (la tabla de decisión, movida de
`report-kit.md`, MO-78), «Lo que pediste y dónde está» y el enlace localhost comprobado (MO-26).
Antes: 1.0 · 2026-05-31._
