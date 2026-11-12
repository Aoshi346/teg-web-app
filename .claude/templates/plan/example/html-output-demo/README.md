# Demo — Salida HTML por tiers + plugin Playground

Demostración del patrón de salida HTML (ver `.claude/rules/html-output.md` y la skill
`html-suelto`). Sirve para **probarlo end-to-end** en cualquier proyecto derivado del template.

## Probar el plugin Playground

```bash
# 1. Instalar (marketplace oficial, disponible siempre)
/plugin install playground@claude-plugins-official

# 2. Usarlo
/playground            # elige template: Design / Data Explorer / Concept Map /
                       # Document Critique / Diff Review / Code Map
```

## Probar la skill html-suelto

```
/html-suelto status        # → status report semanal (Tier 1)
/html-suelto architecture  # → diagrama SVG de módulos (Tier 2)
/html-suelto slides        # → deck navegable (Tier 3)
```

El artefacto se guarda en `.docs/html/<slug>-<fecha>.html` y se abre en el browser.

## Muestra incluida

`sample-status-report.html` — un status report Tier-1 **autocontenido** (CSS/JS inline, sin deps,
botón copy-back). Ábrelo directo en el browser o sírvelo:

```bash
cd .claude/templates/plan/example/html-output-demo && python3 -m http.server 8765 --bind 127.0.0.1
# luego abre http://127.0.0.1:8765/sample-status-report.html
```

Otra muestra real del patrón: `.docs/archive/2026-06-claude-docs-html/plan-auditoria-template-2026-05-31.html`
(este mismo plan, renderizado como artefacto HTML).

## Prompts de ejemplo por tier

**Tier 1 · Status**
> Lee el git log de la última semana y produce un status HTML: qué shipeó, qué se atrasó, un chart
> de progreso y un timeline coloreado. Un solo archivo, sin dependencias.

**Tier 1 · Planning**
> Genera 6 enfoques distintos para [feature]. Layout en grid en un único HTML para compararlos
> lado a lado, cada uno etiquetado con su trade-off.

**Tier 2 · PR writeup**
> Crea un HTML que describa este PR: diff real con anotaciones al margen, findings coloreados por
> severidad y jump links. Asume que el reviewer no conoce [área].

**Tier 2 · Architecture**
> Lee el codebase y produce un diagrama HTML de arquitectura: módulos como nodos clicables, entry
> points y hot path resaltado.

**Tier 3 · Editor configurable**
> Hazme un HTML con toggles agrupados por área y un botón "exportar" que copie la selección como
> markdown (patrón `19-editor-feature-flags` de la galería de referencia).

Referencia de calidad: https://thariqs.github.io/html-effectiveness/
