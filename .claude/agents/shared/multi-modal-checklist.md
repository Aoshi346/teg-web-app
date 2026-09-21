# Multi-modal verification checklist (Playwright)

> Checklist obligatorio para los 3 agentes de audit (Vera, Lidia, Ignacio).
> DOM verification ≠ render verification. Los bugs silenciosos (Tailwind JIT no genera
> una opacity, CSS override invisible, font fallback) solo se detectan mirando
> **computed styles**, no classnames.
>
> Fuente: deep research 2026-04-22

---

## Check 1 — DOM + Computed Style (obligatorio)

Para cada elemento crítico (navbar, CTA primario, hero text):

```js
await page.evaluate(() => {
  const el = document.querySelector('SELECTOR');
  const s = window.getComputedStyle(el);
  return {
    className: el.className,          // lo que dice el DOM
    computedBg: s.backgroundColor,    // lo que renderiza
    computedColor: s.color,
    computedOpacity: s.opacity,
    computedShadow: s.boxShadow,
    computedFontSize: s.fontSize,
    computedFontWeight: s.fontWeight,
    computedLineHeight: s.lineHeight,
  };
});
```

**Reglas de validación:**

- Si `className` incluye `bg-X/N` pero `computedBg === "rgba(0, 0, 0, 0)"`
  → **BUG P0** (Tailwind no generó esa opacity — verificar escala default)
- Si text con `className` `text-jet` pero `computedColor === "rgb(0, 0, 0)"` o `"rgb(255, 255, 255)"`
  → probablemente CSS override — investigar
- Si `computedShadow === "none"` en card/CTA → single-layer shadow o missing shadow
- Si `computedOpacity < 1.0` en elemento no-decorativo → check reducido visibility

## Check 2 — Screenshots multi-posición

Mínimo 8 screenshots por sesión, no solo scrollY=0:

| # | Viewport | scrollY | Propósito |
|---|----------|---------|-----------|
| 1 | 1440×900 | 0 | Hero estado inicial |
| 2 | 1440×900 | 50 | Navbar phase intermedio — **verificar contraste texto** |
| 3 | 1440×900 | 200 | Navbar phase scrolled |
| 4 | 1440×900 | 800 | Transiciones entre secciones |
| 5 | 1440×900 | fin | Footer + último CTA |
| 6 | 390×844 | 0 | Mobile hero |
| 7 | 390×844 | 400 | Mobile scroll medio |
| 8 | 390×844 | fin | Mobile footer |

**Para cada screenshot con navbar**: capturar `getComputedStyle(header)`.
Si `backgroundColor` es `"rgba(0, 0, 0, 0)"` cuando la clase dice `bg-X` → bug
de Tailwind JIT o z-index issue → **P0**.

## Check 3 — Hover / focus states

```js
await page.locator('a[href*="calendly"]').hover();
const hover = await page.evaluate(() => {
  const el = document.querySelector('a[href*="calendly"]');
  const s = window.getComputedStyle(el);
  return { bg: s.backgroundColor, opacity: s.opacity, transform: s.transform };
});
// Validar:
// - opacity delta entre idle y hover entre 0.15-0.25 (>0.3 = clickbait)
// - duration de transición: 200-400ms
```

## Check 4 — Axe accessibility

```js
import { AxeBuilder } from '@axe-core/playwright';

const { violations } = await new AxeBuilder({ page }).analyze();

const critical = violations.filter(v => v.impact === 'critical');
// critical.length === 0 es obligatorio para score >7.0

const serious = violations.filter(v => v.impact === 'serious');
// serious.length < 3 es obligatorio para score >6.5
```

**Si @axe-core/playwright NO está instalado**: skippear este check (documentar
como gap), pero mantener los demás.

## Check 5 — Font rendering

```js
const font = await page.evaluate(() => {
  const h1 = document.querySelector('h1');
  const s = window.getComputedStyle(h1);
  return {
    family: s.fontFamily,
    size: s.fontSize,
    weight: s.fontWeight,
    lineHeight: s.lineHeight,
  };
});
// Validar:
// - fontFamily incluye la fuente esperada (Fraunces, Inter Tight, etc.)
// - No fallback genérico (serif, sans-serif) — significa que el web font no cargó
// - lineHeight ratio 1.1-1.2 para display, 1.5-1.8 para body
```

## Check 6 — Responsive breakpoints

Probar al menos 3 viewports:
- 1920×1080 (desktop grande)
- 1440×900 (desktop estándar)
- 390×844 (mobile iPhone 14 base)

Capturar screenshot full-page en cada uno. Comparar:
- ¿El layout se rompe en alguno?
- ¿Se ven elementos cortados (`overflow: hidden` silencioso)?
- ¿La typography escala con `clamp()` o queda fija?

## Check 7 — Interactive elements real test

Click real (no just verify class) en:
- Cookie accept / reject
- CTA hero primario
- CTA nav
- Menú mobile (si existe)
- Chat bubble
- Primera pregunta del diagnóstico (si hay wizard)
- Al menos 2 items del FAQ

**Por cada click**: verificar que ocurre la acción esperada (modal abierto,
navegación exitosa, formulario desplegado). Si nada ocurre → bug interactivo.

## Check 8 — Console errors durante sesión

```js
const errors = [];
page.on('console', m => { if (m.type() === 'error') errors.push(m.text()); });

// ... ejecutar todas las interacciones ...

// Reportar errors.length y contenido
// 0 errores = pass
// 1+ errores = investigar cada uno (excluir CORS de scripts third-party)
```

---

## Cómo usar este checklist

Los 3 agentes deben:

1. Al comenzar una sesión de audit, ejecutar Check 1-3 como mínimo
2. Si la tarea requiere audit de a11y, ejecutar Check 4
3. Check 5-7 son para auditorías más profundas
4. Check 8 siempre

Documentar en el report de cada agente qué checks ejecutó y qué falló.
Si un check no se pudo ejecutar (ej. axe no instalado) → documentarlo como gap.
