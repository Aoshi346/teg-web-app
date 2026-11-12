---
paths:
  - ".docs/core/**"
  - ".docs/schemas/**"
  - ".docs/plans/index.html"
  - ".docs/adr/README.md"
  - ".claude/scripts/gen_core.py"
  - ".claude/templates/core/**"
---
# Estructura de `.docs/` — planes vivos, esquemas versionados y feedback multi-ronda

> **Cuándo aplicar:** al crear/mantener la documentación visual de un proyecto. Define la convención
> canónica de `.docs/` para que **cada plan** sea una **web de planificación viva** (HTML
> autocontenido, fácil de navegar), los **esquemas de ingeniería** tengan estado actual + historial,
> y `.docs/core/` sea el **punto de entrada único** al sistema — con la frescura de cada documento a
> la vista. Si llegas nuevo a un proyecto y no sabes por dónde empezar: `.docs/core/index.html`.
>
> **Generadores:** `gen_core.py` (el índice del core), `/visual-map` (arquitectura·datos·flujos,
> vivos del código), `/schema` (lean-canvas·C4·casos de uso·user-stories, diseño/negocio),
> **report-kit** (`rules/report-kit.md`: informe + dashboard de decisiones),
> `/qa-loop` (feedback de auditores-persona).
> **Relacionado:** `html-output.md`, `adr.md`, `qa-loop.md`, `speckit-workflow.md`.

---

## Layout canónico de `.docs/`

```
.docs/
├── core/                        # PUNTO DE ENTRADA ÚNICO: el sistema entero, en 5 capas
│   ├── index.html               #   índice generado: qué hay, de cuándo es y qué ya no es fiable
│   ├── core.json                #   manifiesto: qué documentos forman el core (SIN fechas)
│   ├── overview.md · ux.md      #   lo que NO sale del código: se escribe y se revisa
│   ├── core.html + core-*.html  #   el PANEL PERMANENTE del report-kit (PV-3): las capas del
│   │                            #   proyecto, generadas desde el plan ACTIVO y enlazadas desde
│   │                            #   cualquier informe. Aquí porque un plan se cierra y esto no.
│   └── architecture.html · data-model.html · …   # lo generado, PROMOVIDO desde un plan
│
├── adr/                         # decisiones caras de revertir (capa 5 del core) — rules/adr.md
│   ├── README.md · 0001-<slug>.md · 0002-<slug>.md …
│
├── schemas/                     # ESTADO ACTUAL del proyecto (esquemas SIEMPRE al día)
│   ├── index.html               #   estado: qué esquemas hay, versión y "stale" de cada uno
│   ├── schemas.json             #   config canónica (versión actual de cada esquema)
│   ├── lean-canvas.html · c4-context.html · data-model.html · …   # la ÚLTIMA versión de cada uno
│   └── …
│
└── plans/
    ├── index.html               # ÍNDICE GLOBAL de planes (overview + enlaces)
    └── <YYYY-MM-DD-nombre>/      # una carpeta por plan
        ├── index.html           # hub del plan (informe + decisiones + nav)
        ├── STRUCTURE.md · plan.md
        ├── architecture.html · data-model.html · user-flows.html     # /visual-map
        ├── claudecode-configs.html · visual-diff.html · dashboard.html
        ├── schemas/             # la VERSIÓN de los esquemas EN ESE PLAN (snapshot)
        │   ├── schemas.json     #   con la versión capturada
        │   └── *.html
        ├── speckit/             # spec.md · plan.md · tasks.md
        ├── feedback/            # auditores-PERSONA (Lidia/Vera/Ignacio…) y /qa-loop
        │   ├── personas.html · RESULT.md
        │   └── <auditor>/                       # lidia · vera · ignacio · sofia · marco · …
        │       └── <persona>-<short-desc>/       # p.ej. maria-peluquera · diego-pm-saas
        │           ├── feedback.html             # última ronda + selector de rondas + tendencia
        │           ├── trend.json
        │           └── iter-<N>/                 # una carpeta por ronda
        │               ├── REPORT.md · findings.json · screenshots/
        └── feedback-audit/      # /feedback-audit: verificación item-por-item contra el sitio en vivo
            ├── items.json · pages_config.json · verdicts.json · deltas.json
            ├── informe.html     # informe autocontenido (evidencia base64)
            └── shots/{pages,items,items_pre,items_after}/
```

## `.docs/core/` — el punto de entrada único (documentación viva)

Un plan es una **foto de un momento** y con varios planes nadie sabe cuál refleja la realidad.
`core/` es el **presente**: responde al sistema entero en cinco capas, de lo visual y resumido a lo
detallado — (1) overview · (2) arquitectura y estructura · (3) modelo de datos · (4) UX y flujos ·
(5) decisiones (ADR). Generador: **`python3 .claude/scripts/gen_core.py`**; plantillas en
`.claude/templates/core/` (ver su `README.md`).

**El principio que lo sostiene: la doc no debe mentir.** Un wiki mantenido a mano muere en dos
meses, así que aquí lo que puede generarse del código **se genera**, y lo que no **se fecha**:

- **`origin: generado`** (`/visual-map`, `/code-graph`) → envejece con el **código**. Lleva el
  marcador `<!-- core-meta: date=YYYY-MM-DD sha=… via=… -->` y se marca **obsoleto** en cuanto el
  código cambia después de esa fecha.
- **`origin: escrito`** (overview, UX, y los artefactos de `/schema`, que salen de decisiones y no
  de ficheros) → envejece con el **calendario y los planes**. Exige `reviewed: YYYY-MM-DD` en el
  frontmatter. **Sin ese campo el índice lo marca `sin fecha`, en rojo** — para lo escrito a mano no
  vale inferir de git ni del mtime: eso dice cuándo cambiaron los bytes, no cuándo un humano
  confirmó que el contenido sigue siendo cierto.
- **`.docs/core/index.html` NO se edita a mano**: se regenera. Es lo que impide que empiece a mentir.
  `gen_core.py --check` sale con 1 si el índice no refleja el disco.

### Promoción — de la foto del plan al presente

Extiende la regla que ya existía para esquemas (regla 1) a **todo el core**: al cerrar un plan que
generó o tocó un documento del core, se **promueve**.

```bash
python3 .claude/scripts/gen_core.py --promote <doc-id> .docs/plans/<plan>/<fichero>.html
```

La promoción **copia** el fichero a `.docs/core/` y lo sella con la fecha **del origen**, nunca con
la de hoy: promover mueve un documento, no lo rejuvenece. Mientras un documento del core siga
apuntando a un plan, el índice lo avisa ("vive en un plan"), porque ese plan se congelará y el
documento se quedará atrás.

Al cerrar un plan, además, tres preguntas para las capas que no se generan: ¿cambió **qué hace** el
sistema (→ `overview.md`)? ¿cambió **cómo se usa** (→ `ux.md`)? ¿se tomó una decisión **cara de
revertir** (→ un ADR, `rules/adr.md`)? Si la respuesta es sí, se actualiza el documento y su
`reviewed:`. El índice ya detecta el desfase — marca **por revisar** lo escrito cuya última revisión
es anterior al último plan cerrado.

## Reglas

1. **`.docs/schemas/` = verdad viva del proyecto.** Contiene la **última versión** de cada esquema y
   se **actualiza continuamente** (al cerrar un plan que tocó un esquema, se promueve su versión aquí).
   Su `index.html` muestra el estado actual (versión, fecha, si está `stale`).
2. **`.docs/plans/<plan>/schemas/` = versión por plan.** Es el **snapshot** del esquema tal como
   estaba/se decidió en ese plan. Así se ve la **evolución** de cada esquema a través de los planes.
   `schemas.json` lleva el campo `version` (y el plan de origen).
3. **Un `.html` autocontenido por vista** (CSS/JS inline, sin CDN; tokens de `base.html`). Respeta
   `html-output.md`.
4. **Navegación viva (NO se pierde el menú):** TODAS las páginas de un plan llevan la **misma
   `.topnav`**, materializada por **`render_nav.py` desde la fuente única
   `templates/report_kit/nav.json`** (items + **perfiles** `proyecto`/`diseño`/`incidencia`/`minimo` —
   qué pestañas lleva cada tipo de informe; las propias de un proyecto, en `report_kit_local/nav.json`),
   con marcadores idempotentes `<!-- NAV:BEGIN/END -->`,
   prefijo `../` según profundidad y `active` por página. **PROHIBIDA la nav a mano** (fue la causa
   de la divergencia 8-vs-10 items en ~19 ficheros). Detalle: `rules/report-kit.md`.
   Alcance/Integraciones/Paralelización son páginas opcionales fuera de la topnav (enlazadas
   desde `index.html`).
5. **`dashboard.html` interactivo (report-kit):** kanban con **drag&drop**, goals y **galería de
   evidencias** por item, decisiones persistentes (localStorage con clave
   `tlr::<project>::<plan_id>::v1`, o disco vía `server.py`), export JSON/MD. Fuente:
   **`report.json`** generado desde `speckit/tasks.md` por `report_kit/tasks_to_items.py`
   (schema único: `report_kit/item.schema.json`).
6. **`feedback/<auditor>/<persona>-<short-desc>/`:** una carpeta por **persona objetivo** del auditor
   (el naive-tester encarna varias: peluquera, coach…). Dentro, **varias rondas** `iter-<N>/`.
   `feedback.html` muestra la última y permite navegar el historial; `trend.json` la evolución;
   `RESULT.md` resume score por persona × ronda. Mismo patrón que `/qa-loop`.
6b. **`feedback-audit/`** (distinto de `feedback/`): la **verificación item-por-item** de `/feedback-audit`
   (no es un auditor-persona, es un verificador que cruza código + sitio en vivo). Contiene `items.json`,
   `verdicts.json`, `informe.html` (evidencia base64) y `shots/`. Veredicto por item según
   `rules/verdict-contract.md`. **No mezclar con `feedback/`** para que ambos puedan convivir en un plan.
7. **`visual-diff.html`** muestra los cambios del plan (nuevo/editado) de forma visual.
8. **Esquemas (`/schema` + `/visual-map`):** siempre **sugieren** por etapa (lifecycle:
   idea→discovery→inception→design→arch→data→code→ux) y el **usuario decide** qué crear/editar.
   Nunca generar el set entero sin pedirlo. Ver el comando `/schema`.

## Scaffolding (qué crea cada generador)

| Generador | Crea/actualiza |
|-----------|----------------|
| **`gen_core.py`** | `.docs/core/index.html` — el punto de entrada único, con la frescura de cada documento. `--init` lo arranca, `--promote` sube un documento de un plan al core |
| **report-kit** (`report_kit/build.py`) | el set base del plan: `index/structure/dashboard/results/otto.html` + `report.json` + nav única. Ver `rules/report-kit.md` |
| `/visual-map` | `architecture/data-model/user-flows.html` (plan) + promueve a `.docs/schemas/` |
| `/schema <id>` | `schemas/<id>.html` (+ `schemas.json`) en el plan; promueve la versión a `.docs/schemas/` |
| `/code-graph` | `graph-dataset.json` (estructura real del código) → alimenta `structure.html` y `/visual-map` |
| ~~`/plan-dashboard`~~ | **Skill archivada el 2026-08-22** — la sustituye el report-kit. El fichero lite `plan-dashboard.html` de `templates/html/` se archivó también, el 2026-10-19 (LI-12) |
| `/qa-loop` | `feedback/<auditor>/<persona>-<desc>/iter-N/` + `RESULT.md` + `trend.json` |
| `/feedback-audit` | `feedback-audit/` → `items.json` · `verdicts.json` · `informe.html` (base64) · `shots/` |

## Anti-patterns
- ❌ Dejar las páginas del Core dentro de `.docs/plans/<plan>/` → mueren con el plan; su sitio es
  `.docs/core/` (`rules/report-kit.md` §Reglas 5a).
- ❌ Confundir `.docs/core/index.html` (índice de frescura, `gen_core.py` de `scripts/`) con
  `.docs/core/core.html` (hub de capas del report-kit): **son dos artefactos con dos generadores**.
  Solapan y conviene unificarlos algún día; mientras tanto, ninguno pisa al otro y `render_nav.py`
  solo toca el segundo.
- ❌ **Editar `.docs/core/index.html` a mano** → deja de reflejar el disco. Se regenera, siempre.
- ❌ **Escribir la fecha de un documento en `core.json`** → sería la fecha que alguien *dijo*, no la
  real. El manifiesto declara estructura; las fechas las descubre el generador.
- ❌ **Sellar con la fecha de hoy un documento generado hace meses** al promoverlo → es exactamente
  la mentira que el core existe para evitar.
- ❌ Dejar `reviewed:` vacío en `overview.md`/`ux.md` y dar por buena la doc → sale en rojo, y con razón.
- ❌ Tratar el core como un wiki y rellenarlo a mano con lo que ya generan `/visual-map` o `/code-graph`.
- ❌ Nav parcial → al navegar "desaparece el menú". Usa SIEMPRE la nav completa.
- ❌ Líneas de diagrama que cruzan por dentro de las cajas → enruta por los pasillos (gutters).
- ❌ Guardar solo la última versión de un esquema y perder el historial → `.docs/schemas/` (actual) +
  `plans/<plan>/schemas/` (versión por plan).
- ❌ Una sola carpeta de feedback sin rondas ni persona → `feedback/<auditor>/<persona>-<desc>/iter-N/`
  (aplica a `feedback/`; la verificación item-por-item de `/feedback-audit` usa `feedback-audit/`, layout aparte).
- ❌ HTML con CDN / no autocontenido (rompe offline).

---

_Rule version: 1.0 · 2026-06-21_
