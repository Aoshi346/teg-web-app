---
name: "visual-regression"
description: >-
  Usar para detectar cambios visuales NO intencionados antes del merge: baseline de capturas,
  comparación de píxeles y diff marcado, local y sin SaaS. 'regresión visual', '¿ha cambiado algo en
  la UI?', 'compara contra el baseline', 'bendice el baseline', '/visual-regression'. NO usar para:
  juzgar si está BIEN (vera-art-director) ni el comportamiento funcional (los E2E de
  rules/verification.md).
user-invocable: true
metadata:
  version: 1.0.0
  author: Tech Lead Template
  category: qa
  updated: 2026-08-08
---

# visual-regression — baseline local, diff objetivo, bendición explícita

## 📍 Cómo está ahora

La única revisión visual del template es la de **Vera**: experta, pero **subjetiva**, y compara lo
que ve contra lo que ella espera — no contra **cómo se veía ayer**. Un cambio de CSS que rompe otra
página pasa desapercibido si nadie abre esa página.

Ya nos mordió: en el QA de TPL-1 se declararon dos fixes visuales que **en realidad no se habían
aplicado**, y solo se cazaron porque Ignacio re-verificó píxel a píxel **a mano**. Eso no es un
proceso, es suerte.

## 🎯 Qué conseguimos

Detectar **automáticamente** cualquier cambio visual no intencionado entre dos versiones, con
evidencia objetiva, **antes del merge**, sin depender de que un humano se acuerde de mirar cada
página. Y cuando el cambio sí era querido, aceptarlo con un comando en vez de discutirlo.

## 🔧 Cómo funciona

Tres verbos, un script sin dependencias externas más allá de lo que ya usamos (Playwright + Pillow):

```bash
VRT=.claude/skills/visual-regression/vrt.py

python3 $VRT capture --config vrt.json     # captura el estado ACTUAL
python3 $VRT compare --config vrt.json     # lo compara contra el baseline → exit 1 si hay regresión
python3 $VRT bless   --config vrt.json     # promueve current a baseline (el cambio era intencionado)
```

### Configuración (`vrt.json`, junto al proyecto)

```json
{
  "base_url": "http://127.0.0.1:8000",
  "baseline_dir": ".vrt/baseline",
  "current_dir":  ".vrt/current",
  "diff_dir":     ".vrt/diff",
  "threshold_pct": 0.20,
  "channel_tolerance": 12,
  "viewports": { "desktop": [1440, 900], "mobile": [390, 844] },
  "pages": [
    { "name": "home",      "path": "/",          "wait_for": "[data-testid=hero]",
      "mask": [[0, 0, 1440, 64]] },
    { "name": "dashboard", "path": "/dashboard/", "wait_for": "[data-testid=kpi-row]",
      "mask": [[980, 120, 1440, 300]], "threshold_pct": 0.5 }
  ]
}
```

- `mask`: rectángulos `[x1,y1,x2,y2]` que se pintan de negro **en ambas** capturas — es donde vive
  lo dinámico (relojes, "hace 3 min", avatares aleatorios, gráficas animadas).
- `threshold_pct`: se puede afinar por página; el global vale para el resto.
- `channel_tolerance`: por debajo de ese delta por canal es ruido de render (antialias), no cambio.
- El script detecta el binario de Chrome igual que `scripts/screenshot.py` — nunca lo hardcodees.

### Salida real (medida al construir esta skill, viewport 1200×700)

```
$ python3 vrt.py compare --config vrt.json      # tras cambiar el color del CTA de verde a naranja
DIFF  home--desktop.png  0.584% de píxeles distintos (umbral 0.2%)  zona (20, 240, 138, 283)

# comparadas: 1 · regresiones: 1 · diffs en .vrt/diff/
```

El `zona (20, 240, 138, 283)` es exactamente el rectángulo del botón, y `.vrt/diff/home--desktop.png`
es la captura actual con **las zonas cambiadas superpuestas en rojo** y un recuadro alrededor: se
abre y se ve qué cambió, sin interpretar nada. Sin cambios, la misma comparación da `0.000%`.

### Ciclo completo

```bash
# 1. Primera vez: capturar y bendecir el estado actual como referencia
python3 $VRT capture --config vrt.json && python3 $VRT bless --config vrt.json
git add .vrt/baseline && git commit -m "chore(vrt): baseline inicial"

# 2. Al cerrar una wave (con la app levantada)
python3 $VRT capture --config vrt.json
python3 $VRT compare --config vrt.json || echo "REVISAR .vrt/diff/ antes de mergear"

# 3a. El diff es una regresión  → arréglala y vuelve al paso 2
# 3b. El diff era intencionado  → bendice y commitea el baseline CON el cambio que lo justifica
python3 $VRT bless --config vrt.json --only dashboard    # o sin --only para todo
git add .vrt/baseline && git commit -m "feat(ui): nuevo header — baseline actualizado"
```

**El baseline se commitea con el cambio que lo justifica, nunca en un commit aparte.** Así el
reviewer ve en el mismo diff el código y el efecto visual, y `git log .vrt/baseline` cuenta la
historia visual del proyecto.

## 🧭 Por qué así y no de otra manera

| Alternativa | Por qué no |
|---|---|
| **"Que Vera se fije más"** | No escala: nadie compara 20 páginas píxel a píxel de forma fiable, y **ya vimos que falla** (TPL-1) |
| **SaaS (Applitools, Percy, Chromatic)** | Hacen esto mismo, pero cobran por snapshot y **envían tus capturas a un tercero** |
| **`toHaveScreenshot()` de Playwright** | Válido y equivalente **si el proyecto ya tiene runner de Playwright**: úsalo (ver abajo). El script existe para los que no lo tienen, y para HTML estático del propio harness |

El baseline local es gratis, corre offline y deja **evidencia que no admite discusión**: no es la
opinión de nadie, es un rectángulo rojo sobre un píxel que cambió.

### Si el proyecto ya usa el runner de Playwright

```python
# playwright.config / conftest: mismo concepto, misma disciplina
expect(page).to_have_screenshot("dashboard.png", max_diff_pixel_ratio=0.002,
                                mask=[page.get_by_test_id("last-updated")])
# bendecir: pytest --update-snapshots   /   npx playwright test --update-snapshots
```

Las reglas de abajo (congelar datos, enmascarar, solo páginas clave) aplican igual.

## ⚠️ El límite honesto: falsos positivos con contenido dinámico

Es la razón por la que la mayoría de equipos abandona la regresión visual. Se gestiona así:

1. **Congela los datos.** Seed determinista y reloj fijo (`page.clock.set_fixed_time()`,
   `freezegun`): un baseline con la fecha de hoy caduca mañana. Es literalmente el §1 de
   `rules/verification.md` §Estabilidad E2E — sin estado determinista, esto no funciona.
2. **Enmascara lo que no se puede congelar** (widgets de terceros, mapas, avatares aleatorios) con
   `mask`. Medido: sin máscara, un reloj en la cabecera produce un `0.041%` de diferencia.
3. **Desactiva animaciones**: el script lanza con `reduced_motion="reduce"`; añade además
   `* { animation: none !important; transition: none !important; }` en un CSS de test si hace falta.
4. **Solo páginas clave.** 5-10 páginas que representen los layouts del sitio, no las 40.

> **No subas el umbral para tapar contenido dinámico.** Con el viewport del ejemplo (1200×700 =
> 840.000 px), un umbral del 0,2% son ~1.680 píxeles: **un icono roto de 41×41 pasa desapercibido**.
> Medido en el mismo test: el cambio de color del botón dio 0,584% (detectado) y el reloj 0,041%
> (por debajo del umbral, invisible). El umbral no distingue "dinámico" de "pequeño": para lo
> dinámico se enmascara, y el umbral se deja bajo.

## Cuándo activar

- **Cierre de wave con UI**, antes del `/qa-loop`: primero *"¿cambió algo que no debía?"* (objetivo,
  barato), después *"¿está bien?"* (Vera/Lidia/Ignacio, caro).
- Tras un cambio en CSS global, tokens, tema o un componente compartido — el caso exacto en el que
  se rompe una página que nadie va a abrir.
- Al actualizar una dependencia de UI (framework de componentes, Tailwind, fuentes).
- Para **demostrar que un fix visual se aplicó de verdad** (la lección `fix-declarado-no-verificado`).

**NO la actives** con la app a medio construir, ni sobre páginas con contenido inherentemente
variable que no se puede congelar, ni como sustituto de la revisión de Vera: esta skill detecta
**cambio**, no **calidad**. Una página fea con baseline fiel pasa el gate sin problema.

Disparadores: 'regresión visual', 'visual regression', '¿ha cambiado algo en la UI?', 'compara contra el baseline', 'baseline de capturas', 'esto rompió otra página', 'bendice el baseline', '/visual-regression' · Qué hace: baseline de capturas 'bendecidas' de las páginas clave, re-captura al mismo viewport, comparación de píxeles con umbral y diff con las zonas cambiadas marcadas en rojo; incluye el comando para bendecir el nuevo baseline cuando el cambio SÍ era intencionado · NO confundir con vera-art-director (crítica visual subjetiva: juzga si está BIEN; esto detecta si CAMBIÓ) ni con los E2E de rules/verification.md (comportamiento funcional).

## Prerrequisitos y coste

- La app levantada y accesible por HTTP (`file://` está bloqueado: sirve con `python3 -m http.server --bind 127.0.0.1`).
- Chrome/Chromium del sistema o el de Playwright; Pillow.
- **RAM**: abre navegador → cuenta ~doble y no se solapa con `pytest` (ver `rules/ram-pytest.md`).
- Los PNG del baseline pesan: mantenlos en pocas páginas y viewports. Si el repo se hincha, decide
  conscientemente entre versionar el baseline (recomendado: es la referencia) o generarlo en CI
  desde la rama base.

## Anti-patterns

- ❌ Bendecir el baseline "para que pase el gate" sin mirar el diff → el sistema entero deja de valer.
- ❌ Commitear el baseline en un commit aparte del cambio que lo provoca.
- ❌ Subir el umbral hasta que no salte nada (equivale a borrar el gate, y encima en silencio).
- ❌ Baseline capturado con datos de producción o con la fecha del día.
- ❌ Meter las 40 páginas del sitio → lento, ruidoso, se abandona en dos semanas.
- ❌ Mezclar viewports o `device_scale_factor` entre baseline y current → todo sale rojo.
- ❌ Usar esto **en lugar de** Vera: detecta cambio, no calidad (y al revés: Vera no detecta que un
  fix declarado no se aplicó).
- ❌ Correrlo con animaciones activas y culpar a la herramienta del ruido.

## Ejemplos

### User: "he tocado los tokens de color, ¿seguro que no he roto nada?"
TL: levanta la app, `capture` + `compare`. Salen 3 páginas con diff: dos son el cambio buscado (se
abren los PNG de `.vrt/diff/`, se confirma) y la tercera es un botón secundario que quedó ilegible
→ se arregla, se re-compara, y solo entonces `bless` + commit del baseline con el cambio.

### User: "Vera dice que arreglaste el espaciado del hero, pero yo lo veo igual"
TL: `compare` contra el baseline anterior al supuesto fix. Si sale `0.000%`, **el fix no se aplicó**
— evidencia objetiva en una línea, sin discutir capturas. Es el caso TPL-1.

## Related

- `rules/verification.md` §E2E-1 — estado determinista: prerrequisito, no recomendación
- `rules/qa-loop.md` — se corre **antes** del bucle de auditores (objetivo antes que subjetivo)
- `rules/verification.md` — nivel 3/4 del gate: `compare` es un check determinista de Stop hook
- `vera-art-director` (agente) — juzga si está bien; esta skill, si cambió
- `.claude/scripts/screenshot.py` — captura de 1 página con DOM y auditoría de enlaces
- `feedback-audit` — evidencia ANTES/ACTUAL/DESPUÉS embebida en un informe
