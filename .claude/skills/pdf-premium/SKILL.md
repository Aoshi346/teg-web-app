---
name: pdf-premium
description: >-
  Usar cuando haya que entregar un PDF de calidad (propuesta, informe, factura): 'genera un PDF',
  'exporta a PDF', 'PDF premium', '/pdf-premium', 'make a PDF'. Playwright con CSS grid, fuentes
  web, saltos de página y tokens de marca; mejor que wkhtmltopdf. NO usar para: un informe HTML para
  el navegador (html-suelto, rules/report-kit.md) ni leer o editar un PDF existente
  (anthropic-skills:pdf).
user-invocable: true
metadata:
  use-when: "Cuando el proyecto deba entregar un documento PDF de calidad (propuesta, informe, factura, one-pager). Prefiérelo siempre a wkhtmltopdf."
  version: 1.0.0
  author: tech-lead-template
  category: output
  updated: 2026-06-17
  tech-stack: any (HTML/CSS + Playwright)
---

# PDF Premium — PDFs profesionales con Playwright

## Cuándo se activa (detalle)

Disparadores: 'genera un PDF', 'PDF premium', 'exporta a PDF', 'documento en PDF', 'propuesta/informe en PDF', '/pdf-premium', 'make a PDF', 'export to PDF' · Cuándo: el proyecto debe entregar un documento PDF de calidad (propuesta, informe, factura, one-pager, cualquier documento entregable). Prefiérelo siempre a wkhtmltopdf.

Crear PDFs de alta calidad con Playwright (Chromium headless) en lugar de wkhtmltopdf.

## Por qué Playwright > wkhtmltopdf

| wkhtmltopdf | Playwright |
|-------------|------------|
| ❌ CSS moderno parcial (flexbox/grid limitado) | ✅ CSS moderno completo |
| ❌ Fonts web inconsistentes | ✅ Fonts web perfectas |
| ❌ Print media queries problemáticas | ✅ `@media print` fiable |
| ❌ Renders antiguos (Qt WebKit) | ✅ Render como Chrome (pixel-perfect) |

## Método Playwright

```python
from playwright.sync_api import sync_playwright

import shutil
# Detecta el binario (no hardcodear /usr/bin/chromium-browser: en algunos servidores no existe).
chrome = next((shutil.which(n) for n in ("google-chrome","chromium-browser","chromium") if shutil.which(n)), None)
with sync_playwright() as p:
    browser = p.chromium.launch(
        headless=True,
        args=['--no-sandbox'],
        **({'executable_path': chrome} if chrome else {}),  # si None, usa el Chromium de Playwright
    )
    page = browser.new_page()
    page.goto('file:///abs/path/to/document.html', wait_until='networkidle')
    page.wait_for_timeout(2000)  # margen para que carguen las fonts

    page.pdf(
        path='output.pdf',
        format='A4',
        print_background=True,
        margin={'top': '0mm', 'right': '0mm', 'bottom': '0mm', 'left': '0mm'},
        prefer_css_page_size=False,
    )
    browser.close()
```

> ⚠️ Antes de generar, verifica RAM (`bash .claude/hooks/check-ram.sh`) — Chromium headless consume memoria.

## Specs de diseño premium

### Grid (12 columnas, ancho A4)
```css
.container {
  display: grid;
  grid-template-columns: repeat(12, 1fr);
  gap: 20px;
  max-width: 210mm;   /* ancho A4 */
  margin: 0 auto;
  padding: 15mm;      /* safe margins */
}
```

### Tipografía
```css
:root { --font-family: 'Inter', -apple-system, Segoe UI, Roboto, sans-serif; }
h1 { font-size: 36pt; font-weight: 700; line-height: 1.2; margin-bottom: 20pt; }
h2 { font-size: 24pt; font-weight: 600; line-height: 1.3; margin-bottom: 16pt; }
body { font-size: 11pt; line-height: 1.6; color: var(--text); }
```

### Page breaks
```css
.section    { page-break-inside: avoid; break-inside: avoid; }
.page-break { page-break-after: always; break-after: always; }
.cover-page { page-break-after: always; min-height: 297mm; } /* alto A4 */
```

### Layout / cards / dividers
```css
.section { background:#fff; border-radius:12px; padding:40pt; margin-bottom:30pt;
           box-shadow:0 2px 8px rgba(0,0,0,.08); }
.section:nth-child(even) { background: var(--surface-alt); }
.divider { height:1px; background: var(--border); margin:40pt 0; }
.card    { background:#fff; border:1px solid var(--border);
           border-left:4px solid var(--brand-primary); border-radius:8px; padding:24pt; }
.card h3 { color: var(--brand-primary); margin-bottom:12pt; }
svg, .icon { display:block; max-width:100%; height:auto; }
```

## Tokens de marca (PERSONALIZAR por proyecto)

Define los colores de la marca del proyecto. Estos son **placeholders** — sustitúyelos por los
tokens reales del design system (o por los del `tailwind.config`/CSS vars existentes):

```css
:root {
  --brand-primary: #1A56DB;   /* color principal de marca */
  --brand-accent:  #9333EA;   /* acento / CTA */
  --text:          #1F2937;   /* texto principal */
  --surface-alt:   #F3F4F6;   /* fondo alterno de secciones */
  --border:        #E5E7EB;   /* bordes y divisores */
}
```

## Estructura HTML base

```html
<!DOCTYPE html>
<html lang="es">
<head>
  <meta charset="UTF-8">
  <!-- Opción A (online): web font -->
  <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap" rel="stylesheet">
  <!-- Opción B (offline/sin red): omite el <link> y usa la stack del sistema en --font-family -->
  <style>/* CSS vars, grid, typography, page breaks */</style>
</head>
<body>
  <div class="cover-page"><!-- logo, título, subtítulo --></div>
  <div class="section"><!-- contenido --></div>
  <div class="divider"></div>
  <div class="section"><!-- más contenido --></div>
</body>
</html>
```

## Checklist pre-export
1. ✅ Fonts cargadas (web font vía `<link>`/`@import`, o stack de sistema)
2. ✅ CSS variables de marca definidas (tokens reales, no placeholders)
3. ✅ Grid 12-col aplicado
4. ✅ Escalas tipográficas (36/24/11pt) correctas
5. ✅ Page breaks configurados
6. ✅ Margins: 15mm safe area
7. ✅ `print_background=True` en Playwright
8. ✅ Iconos/SVG inline (no imágenes externas cuando sea posible)
9. ✅ Sin notas internas en el HTML de origen: `python3 .claude/scripts/check_internal_notes.py <fuente>.html`
   en 0 (sale con 1 ante un `TODO:`, `REVISAR`, `PLACEHOLDER`, `[PERSONALIZAR]`… visible). Un PDF de
   cliente no se exporta con el 1

## Verificación post-export
```bash
pdfinfo output.pdf                       # metadata (nº páginas, tamaño)
pdftoppm output.pdf review -png -f 1 -l 3  # render a imágenes para revisar
```

## Troubleshooting
- **Fonts no aparecen** → esperar 2-3s tras `networkidle`; verificar `<link>`/`@import`; o usar stack de sistema.
- **Elementos cortados** → `page-break-inside: avoid`, ajustar `min-height`, reducir `margin-bottom`.
- **Colores no imprimen** → `print_background=True` y revisar que `@media print` no los sobrescriba.
- **PDF muy grande** → optimizar imágenes (≤800px), preferir SVG, comprimir con Ghostscript (`gs`).

---

**Regla:** usar Playwright para PDFs premium; wkhtmltopdf solo como fallback.
