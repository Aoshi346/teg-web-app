# `feedback_audit/` — auditoría de feedback de cliente contra producción

> ℹ️ **Nota TPL-1 W3:** el patrón de informe con evidencia base64 de este sistema se generalizó en el
> **report-kit** (`report_kit/embed.py` + `results.template.html`, ver `rules/report-kit.md`). Este
> pipeline sigue siendo el canónico para su caso concreto (feedback de cliente verificado contra el
> sitio vivo con el fan-out de `feedback-verify.js`); para informes de proyecto/plan usa el report-kit.

Pipeline reproducible para coger el **feedback de un cliente** (un `.docx`/lista), convertirlo en
**items trazables**, **verificar cada item página-por-página contra el sitio en vivo** (fan-out de
subagentes), y emitir un **informe HTML autocontenido** con evidencia ANTES/ACTUAL/DESPUÉS.

> **Read-only sobre el sitio objetivo.** Las capturas y la auditoría de enlaces NO modifican nada del
> servidor. Solo se escriben ficheros dentro de `<audit_dir>` (items.json, verdicts.json, shots/, informe.html).
> Verifica **únicamente sitios propios/staging** o producción con autorización.

Lo conduce la skill **`feedback-audit`**, que es **la única puerta** (LI-26, 2026-10-19): su §Flujo
es el procedimiento, y este README es la referencia de la carpeta.
El **contrato de veredicto** que devuelven los agentes está en `rules/verdict-contract.md`.

## Estructura de trabajo (`<audit_dir>`)

```
<audit_dir>/
├── pages_config.json      # config: base URL + páginas (code/slug/url)  ← TÚ lo creas
├── items.json             # fuente única: meta + items (lo generan los pasos)
├── work/<CODE>.items.json # items partidos por página (input del workflow)  ← opcional
├── verdicts.json          # salida del workflow (Paso 2)
├── deltas.json            # cambios de estado entre rondas (Paso 4)
├── shots/
│   ├── pages/             # <CODE>-full.jpg · -m.jpg · -s<N>.jpg · <CODE>.dom.json · _links_audit.json
│   ├── items/             # <ID>.jpg (estado ACTUAL)
│   ├── items_pre/         # <ID>.jpg (ANTES, opcional · OUT_SUB=items_pre + PRE_BASE)
│   └── items_after/       # <ID>.jpg (DESPUÉS de aplicar el fix, opcional)
└── informe.html           # entregable autocontenido (base64)
```

## Pasos

El procedimiento —los cinco pasos, y cómo se lanza `feedback-verify.js` con el tool `Workflow`—
está en la skill **`feedback-audit`** (§Flujo y §Paso 4). Antes estaba también aquí, y dos copias
del mismo procedimiento acaban diciendo cosas distintas. Lo que es propio de esta carpeta:

- **`feedback-verify.js`** — el workflow del paso de verificación (1 agente por página →
  `verdicts.json`). Vivía en `.claude/workflows/` como `/feedback-verify`; desde el 2026-10-19 está
  aquí, junto a los scripts a los que da servicio, y lo lanza la skill.
- Para decidir sobre el MISMO `items.json` en un dashboard: report-kit (`rules/report-kit.md`). El
  dashboard legacy `speckit_dashboard/` que se usaba aquí se archivó el 2026-10-19
  (`_archive/2026-10-19/templates/speckit_dashboard/`, LI-12); su skill `/plan-dashboard`, el 2026-08-22.

## Qué parametrizar (nada hardcoded)
- **Base URL y páginas** → `pages_config.json` (`meta.base` + `pages[].slug`/`url`).
- **Binario de Chrome** → autodetección (`google-chrome`→`chromium`→Playwright), igual que
  `.claude/scripts/screenshot.py`. No hardcodear `/usr/bin/google-chrome`.
- **Cabecera del informe y notas** → `items.json` `meta.title/eyebrow/lead/report_notes`.

## Dependencias
- `playwright` (`pip install playwright && playwright install chromium`) para los `capture_*`.
- `Pillow` (opcional) para que `build_report.py` recomprima las imágenes embebidas; sin Pillow el
  informe igual se genera (embebe el JPG tal cual, pesa más).

## Notas
- **Idempotencia**: re-correr `items_from_feedback.py` no duplica items (dedup por texto, difflib).
  `reconcile.py` preserva `prev_status` para los deltas entre rondas.
- **ANTES/DESPUÉS**: para la columna ANTES captura el sitio viejo con
  `OUT_SUB=items_pre PRE_BASE=<url-vieja> python3 $T/capture_items.py $DIR`; para DESPUÉS (tras aplicar
  los cambios) usa `OUT_SUB=items_after`.
- El informe es **autocontenido** (base64, sin CDN): abre offline en cualquier navegador.
