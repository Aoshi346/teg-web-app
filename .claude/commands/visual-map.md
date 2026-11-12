# /visual-map - Mapa visual del plan (arquitectura + datos + flujos)

Genera (o regenera) el **set de mapas visuales multi-página** del plan a partir del código real:
arquitectura clicable, modelo entidad-relación y flujos de usuario. Todo en HTML autocontenido
(un `.html` por página, CSS/JS inline, **sin CDN**, fuentes de sistema), offline-friendly.

## Cuándo usarlo

- **Tareas grandes** (>3 archivos, feature multi-módulo, refactor) — durante el **gate de plan**,
  antes de comprometer el plan. Ver `.claude/rules/plan-gates.md`.
- Onboarding a un repo que ya tiene código y quieres ver su forma de un vistazo.
- Cuando el hook `flag-visual-staleness.sh` anota en `PROGRESS.log` que el mapa quedó desfasado.

No lo uses para fixes triviales (1-3 archivos): ahí un diff y una frase bastan.

## Qué hace

1. Corre el workflow **`.claude/workflows/visual-map-datos.js`** (`/visual-map-datos`; hasta el
   2026-10-19 se llamaba `visual-map.js` y su nombre chocaba con el de este comando): scout de subsistemas →
   lector por subsistema en paralelo (modelos + rutas) → síntesis. **Aprueba antes de correr**:
   lanza varios subagentes (coste de tokens real).
2. La síntesis emite tres datasets JSON listos para pegar:
   - `NODES` / `EDGES` → `.claude/templates/html/architecture.html`
   - `ENTITIES` / `RELATIONS` → `.claude/templates/html/data-model.html`
   - `FLOWS` → `.claude/templates/html/user-flows.html`
3. El agente copia las plantillas (incluidas `scope-and-boundaries.html`, `integrations.html`,
   `parallelization.html` y el `index.html`/hub), **reemplaza el bloque `EDITA AQUÍ`** con los
   datos reales y rellena los `[PLACEHOLDER]`/`[FECHA]`.
4. Guarda el set en `.docs/plans/<plan>/` (junto al plan SpecKit) o en `.claude/docs/html/`.
5. **Verifica el render**: `python3 -m http.server` + navegar a `http://127.0.0.1` (el `file://`
   suele estar bloqueado). Revisa la consola; confirma que la nav, el SVG y los paneles funcionan.

## Convenciones (no romper)

- Un solo `.html` por página; CSS y JS **inline**; sin dependencias remotas (offline-friendly).
- Tokens `:root` y `.topnav` idénticos a `architecture.html` (no inventar paletas).
- La nav superior se materializa con **`render_nav.py`** desde la fuente única
  `templates/report_kit/nav.json` (marcadores `<!-- NAV:BEGIN/END -->`, perfil del plan).
  **NO copiarla a mano** — `nav-partial.html` queda solo como referencia visual del CSS.
  Detalle: `rules/report-kit.md`.
- Ver `.claude/rules/html-output.md` (caso "mapa de arquitectura/concepto vivo").

## Complemento opcional — plugin `playground`

Si está instalado el plugin **`playground`**, sus vistas **Concept Map** / **Code Map** son un buen
complemento interactivo para explorar el repo sobre la marcha. Es **opcional**: el set de `/visual-map`
es autocontenido y no depende de él. Markdown sigue siendo el default para output trivial.
