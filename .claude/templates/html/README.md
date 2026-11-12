# .claude/templates/html/ — plantillas HTML base ("cómo mostrar las cosas")

Plantillas **self-contained** (CSS/JS inline, sin CDN) que el agente copia y rellena para producir
salida HTML consistente. Comparten los mismos **design tokens** (navy/paper editorial, system fonts).
Conviven con la skill `html-suelto` y la rule `rules/html-output.md`. Listón de calidad:
https://thariqs.github.io/html-effectiveness/

## Plantillas

> **Para el "informe total" de un plan/proyecto/incidencia** (multi-página, decisiones persistentes,
> evidencias base64): usa el **report-kit** — `../report_kit/` + `rules/report-kit.md`. Las plantillas
> de abajo siguen valiendo para piezas sueltas y para el set de /visual-map.

| Archivo | Para qué | Interactiva |
|---------|----------|:-----------:|
| `base.html` | Esqueleto + tokens + helpers (copy/toast). **Punto de partida de cualquier página.** | — |
| `doc-page.html` | Guía / explainer / referencia con nav lateral fija + secciones ancladas. | — |
| `status-report.html` | Status / report / post-mortem (Tier 1): KPIs + tabla + chart + timeline. | — |
| `config-builder.html` | **Constructor de config por proyecto**: toggles de tipo/stack/skills/MCPs/plugins/permisos → **prompt para `/create-agent` + config.json**. Persiste en localStorage; copia/descarga. | ✅ |

> **Archivados el 2026-10-19** (LI-12, `_archive/2026-10-19/templates/`): `plan-dashboard.html`
> (dashboard de plan LITE: kanban + matriz + filtros, localStorage → export JSON/MD),
> `progress-dashboard.html` (Kanban + Gantt + mapa conceptual, con el patrón de tokens HSL crudos
> `pcol()`/`praw()`) y `../speckit_dashboard/` (legacy). Los tres duplicaban el dashboard del
> report-kit, que es la única forma de seguir un plan: `../report_kit/` + `rules/report-kit.md`.

### Set multi-página de planificación visual (`/visual-map`)

Plantillas hermanas que comparten la **misma `.topnav`** (ver `nav-partial.html`) y los tokens de
`base.html`. Forman el plan visual de una tarea grande; cada una se rellena con datos del repo
(a mano o vía el comando **`/visual-map`** → workflow `visual-map-datos.js`, que los genera del código real).

| Archivo | Para qué | Interactiva |
|---------|----------|:-----------:|
| `hub.html` | **Index** del set: hero + tarjetas a cada página + tira de estado de waves + copiar plan. | — |
| `nav-partial.html` | Nav superior compartida (se copia idéntica en cada página, solo cambia `active`). | — |
| `architecture.html` | **Arquitectura**: diagrama de componentes/flujo SVG clicable (`NODES`/`EDGES`). | ✅ |
| `data-model.html` | **Modelo de datos**: entidad-relación SVG clicable, entidad → campos/relaciones (`ENTITIES`/`RELATIONS`). | ✅ |
| `user-flows.html` | **Flujos de usuario**: lista de flujos → recorrido horizontal de pasos (pantalla + endpoint por paso) (`FLOWS`). | ✅ |
| `scope-and-boundaries.html` | **Alcance y límites**: in/out-of-scope + supuestos + riesgos en columnas + diagrama de frontera. | — |
| `integrations.html` | **Integraciones**: cards por servicio externo (dir/auth/status real-mock) + SVG radial sistema-en-el-centro. | ✅ |
| `parallelization.html` | **Paralelización**: swimlanes Tech Lead/worktree/waves + orden de merge. Refleja `rules/parallelization.md`. | ✅ |

> **`/visual-map`** (el comando; su motor es el workflow `/visual-map-datos`) regenera `architecture`/`data-model`/`user-flows` desde
> código real; el hook `flag-visual-staleness.sh` avisa en `PROGRESS.log` si el mapa quedó desfasado.
> Complemento opcional: plugin `playground` (Concept/Code Map). Ver `rules/html-output.md`.

## Cómo usar (skills / agente)

1. Copia la plantilla al destino, p.ej. `.docs/html/<slug>-<fecha>.html` (páginas sueltas) o junto al
   plan (`.docs/plans/<…>/dashboard.html`).
2. Rellena los `[PLACEHOLDERS]` y, en las interactivas, los arrays `META`/`ITEMS`/estado inicial.
3. **No commitees** artefactos generados grandes salvo que aporten (van a `.docs/html/`).
4. Verifica el render: `python3 -m http.server --bind 127.0.0.1` + abrir en browser (por túnel SSH si
   el servidor es remoto; nunca `0.0.0.0`). El favicon 404 es inofensivo.

## Convenciones (no romper)

- Un solo `.html`; CSS y JS **inline**; sin dependencias remotas (offline-friendly).
- Tipografía del sistema; tokens `:root` de `base.html` (no inventar paletas nuevas).
- Las interactivas persisten decisiones en **localStorage** y ofrecen **export** (copy/descarga) —
  el browser no escribe ficheros directamente; el usuario pega el JSON/MD donde corresponda.
- Para output trivial (un sí/no, un párrafo) usa markdown, no HTML.

> Ejemplos vivos (rellenos) en `documentation/`: `estado.html` (generado por `gen_docs.py`) y
> `claude-code/reference.html`. Las páginas a mano `index`, `repo`, `commands` y `settings` se
> retiraron el 2026-10-20 (`_archive/2026-10-20/documentation/`).
