#!/usr/bin/env python3
"""motion_probe.py — mide el MOVIMIENTO de una página. Determinista y reproducible.

EL HUECO QUE CIERRA. Hoy nadie audita el movimiento de nada, y no por descuido: **todas las
capturas del harness son estáticas**, y `skills/visual-regression` arranca el navegador con las
animaciones APAGADAS a propósito (para que su diff no parpadee). Así que la única dimensión que
distingue una web de 2026 de una de 2012 —cómo se mueve— no la mira ningún instrumento, y a Vera
se le pide un juicio sobre algo que no ha podido ver.

QUE DEVUELVE, y por qué cada cosa:
  1. INVENTARIO por elemento: duración, curva, nombre del keyframe, iteraciones. De dos fuentes,
     porque miden cosas distintas: `document.getAnimations()` dice qué se está moviendo AHORA, y
     un barrido de `getComputedStyle` dice qué está DECLARADO (una transición de hover no está
     corriendo al cargar, y es la mitad del sistema de movimiento).
  2. ESTADÍSTICA: mediana y p90 de duración, cuántas pasan de 500 ms, cuántas son bucles
     infinitos, y **cuántas curvas distintas hay**. Más de tres curvas no es riqueza: es que no
     hay sistema de movimiento, hay decisiones sueltas tomadas en momentos distintos.
  3. FOTOGRAMA A MITAD DE TRANSICION, REPRODUCIBLE. Nada de `sleep` y capturar a ver qué sale:
     se pausa cada animación y se le fija `currentTime = duración × N`. Tres fotogramas: t0, t50
     y t100. Lo que eso compra es que el fotograma no sea «donde cayó el sleep»: el estado de la
     animación está PUESTO, no muestreado.

     **Y hasta dónde llega eso, medido en vez de prometido.** Dos corridas seguidas sobre
     `bien/elevaiti-v53.html`, comparando píxel a píxel:

         t100       0,00 %  de píxeles distintos   → sirve para comparar versiones
         sin-js     0,04 %  (557 px, suavizado de fuentes)
         reduced   28 %
         t0        37 %
         t50       46 %     → NO sirven para comparar; sirven para mirar

     El motivo no es la animación: es **qué elementos existían para ser pausados**. El revelado por
     scroll decide eso con milisegundos de diferencia en cada corrida, así que los estados
     intermedios no convergen. El final sí, porque al terminar todo acaba donde tiene que acabar.
     Conclusión operativa: **para diferenciar dos versiones se usa `t100`**; `t0` y `t50` enseñan la
     forma del movimiento y no se meten en un diff. Si lo que hace falta es comparar imágenes de
     verdad, eso ya existe y es `skills/visual-regression`, que corre **con las animaciones
     apagadas** precisamente por esto.
  4. PASADA SIN JS (`java_script_enabled=False`) y ratio de texto visible contra la pasada normal.
     **Esto es GD-01 en vivo**, y es el caso real de `resources/referencias-diseno/mal/
     attomo-digital.html`: una página desplegada donde `initGSAP()` no se llama nunca y todo lo
     que lleva `.reveal` se queda en `opacity:0`.
  5. PASADA CON `prefers-reduced-motion: reduce`: el contenido tiene que seguir completo y las
     duraciones computadas irse a ~0. Una página que ignora esa preferencia marea a quien la pidió
     precisamente porque le sienta mal.
  6. PRESUPUESTO DE MOVIMIENTO: cuántos elementos se animan a la vez en el primer viewport y qué
     parte de la pantalla ocupan.
  7. SALTO DE MAQUETA: la caja de los titulares en t0 contra t100. Si el titular se mueve 200 px
     mientras aparece, lo que el visitante lee cambia de sitio bajo sus ojos.

LOS TRES DESENLACES (rules/verification.md):
    0  medido · sin señales
    1  medido · HAY señales (algún umbral superado)
    2  NO SE PUDO MEDIR (sin navegador, URL inalcanzable, Playwright ausente)
Un cero de aquí significa «se midió y el movimiento está en orden». **Nunca «no encontré
movimiento»**, que es justo la buena noticia falsa que produce un instrumento que no puede mirar.

USO:
    python3 .claude/scripts/motion_probe.py http://127.0.0.1:8899/ --out /tmp/motion
    python3 .claude/scripts/motion_probe.py <url> --out <dir> --viewport 390x844
    python3 .claude/scripts/motion_probe.py <url> --out <dir> --video    # delega en pr_video.py

`file://` suele estar bloqueado: sirve la carpeta con
`python3 -m http.server --bind 127.0.0.1 <puerto>` (el `--bind` NO es opcional — `rules/security.md`).

QUE **NO** MIDE, dicho por delante para que nadie lea de más en sus números:
  · **El jank de verdad.** Un Chrome headless compartiendo una máquina con otras sesiones no es la
    tasa de fotogramas de nadie. Aquí no hay ni una medida de fps, y es deliberado: publicarla
    sería inventar precisión. Para eso hay que medir en el dispositivo real (`bruno-perf-cop`).
  · **Si el movimiento SIGNIFICA algo.** Que las curvas sean tres y las duraciones medianas no
    dice si la animación cuenta algo del producto o solo adorna. Eso es juicio, es de
    `vera-art-director`, y este script solo le pone los números delante para que no tenga que
    adivinarlos.
  · **El movimiento que solo aparece al interactuar** (hover, arrastre, foco). Se detecta que está
    DECLARADO, no se dispara. Para recorrer un flujo, `scripts/pr_video.py --steps`.
"""
from __future__ import annotations

import argparse
import json
import shutil
import statistics
import subprocess
import sys
from pathlib import Path

# ── Umbrales. Cada uno con su procedencia: un número sin porqué no se puede discutir ───────────
MS_LARGA = 500          # R8 de `agents/shared/red-flags.sh` ya usa 500 ms como «excesivo»: se
                        # reutiliza en vez de inventar un segundo listón que lo contradiga.
MAX_CURVAS = 3          # más de tres curvas distintas = decisiones sueltas, no un sistema
RATIO_SIN_JS = 0.50     # sin JS se ve menos de la mitad que con JS → el contenido depende del JS
VISIBLE_DEL_DOM = 0.70  # del texto que ESTA en el DOM, cuánto llega a verse. Es la medida que de
                        # verdad caza GD-01: attomo sin JS deja 674 caracteres a la vista y 1.674
                        # escondidos (29 %). No depende de con qué se compare, y por eso no la
                        # engaña una página que esté rota también con el JS puesto.
RATIO_REDUCED = 0.90    # con reduced-motion el contenido tiene que seguir estando
# Empezó en 24 px y marcaba `bien/elevaiti-v53.html`, que se desplaza 26: esa página usa
# `transform: translateY(28px)` en su fade-up y es una referencia APROBADA del corpus. Una regla
# que marca el ejemplo canónico de lo bien hecho está mal planteada, no lo está el ejemplo — es la
# regla de inversión de `rules/refactor-progresivo.md` §4.4 aplicada a un umbral. Un fade-up de
# 20-30 px es el estándar de la casa; lo que se quiere cazar es el titular que cruza media
# pantalla mientras lo lees.
SALTO_MAX_PX = 64
ESPERA_MS = 2500        # tiempo para que la entrada termine antes de inventariar


def find_chrome():
    """Primer navegador del sistema, o None (Playwright usa el suyo).

    Misma detección que `scripts/screenshot.py` y `scripts/pr_video.py`, duplicada a propósito:
    estos scripts se copian sueltos a proyectos derivados y no forman un paquete importable. Si
    cambia una, cambian las tres.
    """
    for n in ("google-chrome", "google-chrome-stable", "chromium-browser", "chromium", "chrome"):
        p = shutil.which(n)
        if p:
            return p
    return None


def abortar(razon, contexto="", destino=None):
    """Sale con 2 y deja dicho POR QUÉ. Jamás un motion.json con ceros que parezca una medición."""
    if destino:
        try:
            (Path(destino) / "motion.json").write_text(json.dumps(
                {"estado_instrumento": "no_medido", "razon_no_medido": razon},
                ensure_ascii=False, indent=1), encoding="utf-8")
        except OSError:
            pass
    print(f"⛔ motion_probe.py NO PUDO MEDIR: {razon}", file=sys.stderr)
    if contexto:
        print(f"   {contexto}", file=sys.stderr)
    print("   Cero animaciones porque no se pudo mirar NO es «esta página no se mueve».",
          file=sys.stderr)
    sys.exit(2)


# ══════════════════════════════════════════════════════════════════════════════════════════════
# El JS que se inyecta. Va en constantes para que se lea entero y se pueda criticar.
# ══════════════════════════════════════════════════════════════════════════════════════════════

# Texto REALMENTE visible: `innerText` respeta `display:none` pero NO `opacity:0`, que es
# justamente cómo se esconde el contenido en el caso de attomo. Sin mirar la opacidad heredada,
# la pasada sin JS diría que el texto está ahí y la página sale en blanco.
JS_TEXTO_VISIBLE = r"""
() => {
  const visible = (el) => {
    let n = el;
    while (n && n.nodeType === 1) {
      const cs = getComputedStyle(n);
      if (cs.display === 'none' || cs.visibility === 'hidden' || parseFloat(cs.opacity) < 0.05)
        return false;
      n = n.parentElement;
    }
    return true;
  };
  let total = 0, oculto = 0;
  document.querySelectorAll('h1,h2,h3,h4,h5,h6,p,li,td,th,figcaption,blockquote,a,button,span')
    .forEach(el => {
      if (el.querySelector('h1,h2,h3,h4,h5,h6,p,li')) return;   // solo hojas: no contar dos veces
      const t = (el.innerText || el.textContent || '').replace(/\s+/g, ' ').trim();
      if (!t) return;
      if (visible(el)) total += t.length; else oculto += t.length;
    });
  return {visible: total, oculto: oculto, titulo: document.title || ''};
}
"""

JS_INVENTARIO = r"""
() => {
  const sel = (el) => {
    if (!el || !el.tagName) return '(sin elemento)';
    const id = el.id ? '#' + el.id : '';
    const cls = (el.className && el.className.toString) ?
      '.' + el.className.toString().trim().split(/\s+/).slice(0, 2).join('.') : '';
    return (el.tagName.toLowerCase() + id + cls).slice(0, 70);
  };
  // (a) lo que se está moviendo AHORA
  const corriendo = document.getAnimations().map(a => {
    let d = 0, iter = 1, easing = '', nombre = '';
    try {
      const ct = a.effect.getComputedTiming();
      d = Number(ct.duration) || 0;
      iter = ct.iterations;
      easing = (a.effect.getTiming().easing) || '';
    } catch (e) {}
    nombre = a.animationName || a.transitionProperty || (a.constructor && a.constructor.name) || '';
    let caja = null;
    try {
      const r = a.effect.target.getBoundingClientRect();
      caja = {x: Math.round(r.x), y: Math.round(r.y), w: Math.round(r.width), h: Math.round(r.height)};
    } catch (e) {}
    return {selector: sel(a.effect && a.effect.target), ms: Math.round(d), iteraciones:
            (iter === Infinity ? 'infinitas' : iter), easing: easing, nombre: String(nombre).slice(0,40),
            caja: caja, estado: a.playState};
  });
  // (b) lo DECLARADO, que incluye lo que solo se dispara al interactuar
  // Partir por comas de NIVEL SUPERIOR. Con un split(',') a pelo, `cubic-bezier(0.4, 0, 0.2, 1)`
  // se rompe en cuatro trozos: el recuento de curvas distintas se infla y el informe imprime
  // basura («cubic-bezier(0.4, 0, 0.2, ease-in-out, 1)»). Lo vio el control negativo, que contó 5
  // curvas donde hay 2.
  const partirComas = (v) => {
    const out = []; let prof = 0, act = '';
    for (const ch of (v || '')) {
      if (ch === '(') prof++;
      else if (ch === ')') prof--;
      if (ch === ',' && prof === 0) { out.push(act.trim()); act = ''; continue; }
      act += ch;
    }
    out.push(act.trim());
    return out.filter(x => x !== '');
  };
  const curvas = {}, declaradas = [];
  document.querySelectorAll('*').forEach(el => {
    const cs = getComputedStyle(el);
    const partes = [];
    const dur = (v) => partirComas(v).map(s => {
      s = s.trim();
      if (s.endsWith('ms')) return parseFloat(s);
      if (s.endsWith('s')) return parseFloat(s) * 1000;
      return 0;
    });
    const td = dur(cs.transitionDuration), ad = dur(cs.animationDuration);
    const tf = partirComas(cs.transitionTimingFunction);
    const af = partirComas(cs.animationTimingFunction);
    td.forEach((ms, i) => { if (ms > 0) { partes.push({tipo: 'transition', ms: ms, easing: tf[i] || tf[0] || ''}); } });
    ad.forEach((ms, i) => { if (ms > 0) { partes.push({tipo: 'animation', ms: ms, easing: af[i] || af[0] || ''}); } });
    partes.forEach(p => {
      if (p.easing) curvas[p.easing] = (curvas[p.easing] || 0) + 1;
      declaradas.push({selector: sel(el), tipo: p.tipo, ms: Math.round(p.ms), easing: p.easing});
    });
  });
  return {corriendo: corriendo, declaradas: declaradas, curvas: curvas,
          viewport: {w: window.innerWidth, h: window.innerHeight}};
}
"""

# El fotograma REPRODUCIBLE: se pausa y se fija el tiempo. Dos corridas dan el mismo PNG, que es
# la única forma de que una captura de algo en movimiento sirva para comparar.
JS_FIJAR = r"""
(pct) => {
  document.getAnimations().forEach(a => {
    try {
      const ct = a.effect.getComputedTiming();
      const d = Number(ct.duration) || 0;      // una iteración: activeDuration es Infinity en bucles
      a.pause();
      a.currentTime = d * pct;
    } catch (e) {}
  });
  return document.getAnimations().length;
}
"""

JS_TITULARES = r"""
() => [...document.querySelectorAll('h1,h2,h3')].slice(0, 12).map(h => {
  const r = h.getBoundingClientRect();
  return {texto: (h.innerText || '').replace(/\s+/g,' ').trim().slice(0, 50),
          x: Math.round(r.x), y: Math.round(r.y + window.scrollY),
          w: Math.round(r.width), h: Math.round(r.height)};
})
"""


# ══════════════════════════════════════════════════════════════════════════════════════════════
# Medición
# ══════════════════════════════════════════════════════════════════════════════════════════════
def abrir(p, chrome):
    kw = {"headless": True, "args": ["--no-sandbox"]}
    if chrome:
        kw["executable_path"] = chrome
    return p.chromium.launch(**kw)


def cargar(nav, url, ancho, alto, espera, **ctx_kw):
    """Abre la URL en un contexto nuevo. `wait_until='load'`, NUNCA 'networkidle'.

    El porqué está medido en `rules/harness-gotchas.md`: con un ThreadingHTTPServer —que es lo que
    se usa para servir HTML local— 'networkidle' no llega nunca y la espera agota el tiempo.
    """
    ctx = nav.new_context(viewport={"width": ancho, "height": alto}, **ctx_kw)
    pg = ctx.new_page()
    errores = []
    pg.on("console", lambda m: errores.append(m.text[:160]) if m.type == "error" else None)
    pg.on("pageerror", lambda e: errores.append(f"pageerror: {str(e)[:160]}"))
    resp = pg.goto(url, wait_until="load", timeout=30000)
    # ⚠️ EL ESTADO HTTP SE MIRA, y este es el fallo que el script existía para no cometer.
    # Una prueba de sabotaje contra una URL inexistente devolvía **exit 0 y «sin señales»**: el
    # servidor sirve una página de error, la página de error no tiene animaciones, y el
    # instrumento daba la buena noticia sobre una página que NO EXISTE. Es el caso de manual de
    # `rules/verification.md` — «el instrumento que no puede llegar al sujeto debe ABORTAR, no
    # devolver cero» — cometido dentro del propio script que lo cita en su cabecera.
    if resp is not None and resp.status >= 400:
        ctx.close()
        raise RuntimeError(f"la URL respondió HTTP {resp.status}: se estaría midiendo la página "
                           f"de error, no la página")
    pg.wait_for_timeout(espera)
    return ctx, pg, errores


def recorrer(pg, con_js=True):
    """Baja hasta el final y vuelve arriba. Las TRES pasadas hacen lo mismo, y eso es el punto.

    Casi todo motor de revelado usa IntersectionObserver, así que lo que está bajo la línea de
    flotación sigue en `opacity:0` hasta que alguien baja. Sin recorrer, `bien/elevaiti-v53.html`
    —la referencia SANA, mejora progresiva de manual— salía con «el 75 % del texto oculto»: un P0
    inventado por no haber hecho scroll. Y al arreglarlo solo en la pasada normal, el mismo
    artefacto reapareció en la de `reduced-motion` diciendo que la página pierde el 68 % del
    contenido. Si las pasadas no se recorren IGUAL, sus números no se pueden comparar, que es lo
    único para lo que existen.
    """
    if not con_js:
        # En la pasada sin JavaScript el recorrido NO puede ir por `evaluate`: la función devuelve
        # una promesa que se apoya en `setTimeout`, y sin temporizadores no se resuelve nunca —
        # Playwright acaba con «Execution context was destroyed». Se baja con la RUEDA, que la
        # mueve el navegador y no la página. Hace falta de verdad y no es simetría por simetría:
        # sin JS un IntersectionObserver no puede revelar nada, pero `animation-timeline: view()`
        # es CSS puro y sí se dispara al bajar.
        for _ in range(24):
            pg.mouse.wheel(0, 900)
            pg.wait_for_timeout(80)
        pg.keyboard.press("Home")
        pg.wait_for_timeout(400)
        return
    pg.evaluate("""() => new Promise(r => {
        let y = 0;
        const paso = () => {
          window.scrollTo(0, y);
          y += window.innerHeight * 0.8;
          if (y < document.body.scrollHeight + window.innerHeight) setTimeout(paso, 160);
          else { window.scrollTo(0, 0); setTimeout(r, 300); }
        };
        paso();
    })""")
    pg.wait_for_timeout(400)


def percentil(vals, q):
    if not vals:
        return 0
    vals = sorted(vals)
    i = min(len(vals) - 1, max(0, int(round(q * (len(vals) - 1)))))
    return vals[i]


def medir(url, destino: Path, ancho, alto, espera, chrome):
    from playwright.sync_api import sync_playwright

    frames = destino / "frames"
    frames.mkdir(parents=True, exist_ok=True)
    datos = {"url": url, "viewport": f"{ancho}x{alto}", "estado_instrumento": "medido",
             "razon_no_medido": None, "navegador": chrome or "chromium de Playwright"}

    with sync_playwright() as p:
        nav = abrir(p, chrome)
        try:
            # ── 1 · pasada normal ────────────────────────────────────────────────────────────
            ctx, pg, errores = cargar(nav, url, ancho, alto, espera)
            inv = pg.evaluate(JS_INVENTARIO)
            recorrer(pg)
            texto_normal = pg.evaluate(JS_TEXTO_VISIBLE)
            tit0 = None

            # ── 3 · los tres fotogramas, FIJADOS (reproducibles, sin sleep) ─────────────────
            fijados = {}
            for pct, nombre in ((0.0, "t0"), (0.5, "t50"), (1.0, "t100")):
                fijados[nombre] = pg.evaluate(JS_FIJAR, pct)
                pg.wait_for_timeout(60)          # un respiro para que el compositor pinte
                pg.screenshot(path=str(frames / f"{nombre}-{ancho}.png"), full_page=False)
                if nombre == "t0":
                    tit0 = pg.evaluate(JS_TITULARES)
            tit100 = pg.evaluate(JS_TITULARES)
            datos["consola"] = errores[:20]
            ctx.close()

            # ── 4 · pasada SIN JS — esto es GD-01 en vivo ────────────────────────────────────
            ctx2, pg2, _ = cargar(nav, url, ancho, alto, min(espera, 1500),
                                  java_script_enabled=False)
            recorrer(pg2, con_js=False)
            texto_sinjs = pg2.evaluate(JS_TEXTO_VISIBLE)
            pg2.screenshot(path=str(frames / f"sin-js-{ancho}.png"), full_page=False)
            ctx2.close()

            # ── 5 · pasada con prefers-reduced-motion: reduce ────────────────────────────────
            ctx3, pg3, _ = cargar(nav, url, ancho, alto, espera, reduced_motion="reduce")
            inv_red = pg3.evaluate(JS_INVENTARIO)
            recorrer(pg3)
            texto_red = pg3.evaluate(JS_TEXTO_VISIBLE)
            # También se fija aquí. Sin esto, la captura de reduced-motion salía en «donde
            # estuvieran» los bucles infinitos en ese instante y cambiaba entre corridas: medido,
            # dos ejecuciones daban dos PNG distintos. Una captura que no se repite no sirve para
            # comparar, que es lo único para lo que se guarda.
            pg3.evaluate(JS_FIJAR, 1.0)
            pg3.wait_for_timeout(60)
            pg3.screenshot(path=str(frames / f"reduced-{ancho}.png"), full_page=False)
            ctx3.close()
        finally:
            nav.close()

    # ── Estadística ──────────────────────────────────────────────────────────────────────────
    decl = inv["declaradas"]
    ms = [d["ms"] for d in decl if d["ms"] > 0]
    curvas = inv["curvas"]
    infinitas = [a for a in inv["corriendo"] if a.get("iteraciones") == "infinitas"]
    vh = inv["viewport"]["h"]
    en_pantalla = [a for a in inv["corriendo"]
                   if a.get("caja") and a["caja"]["y"] < vh and a["caja"]["h"] > 0]
    area = sum(a["caja"]["w"] * a["caja"]["h"] for a in en_pantalla)

    datos["inventario"] = {
        "animaciones_corriendo": len(inv["corriendo"]),
        "declaraciones_con_movimiento": len(decl),
        "detalle_corriendo": inv["corriendo"][:60],
        "detalle_declaradas": decl[:120],
    }
    # Se separan `transition` y `animation` porque NO miden lo mismo, y mezclarlas hacía que la
    # referencia sana saliera «lenta». Los 500 ms de R8 (`agents/shared/red-flags.sh`) son sobre la
    # RESPUESTA a una interacción: pulsas y tarda. Una entrada de 600 ms no es lentitud, es ritmo —
    # `bien/elevaiti-v53.html` usa `transition: opacity .6s` en su fade-up a propósito. El umbral
    # se aplica solo a la respuesta; la entrada se reporta y no se juzga.
    ms_resp = [d["ms"] for d in decl if d["ms"] > 0 and d["tipo"] == "transition"]
    ms_entr = [d["ms"] for d in decl if d["ms"] > 0 and d["tipo"] == "animation"]
    datos["estadistica"] = {
        "mediana_ms": round(statistics.median(ms)) if ms else 0,
        "p90_ms": percentil(ms, 0.90),
        "respuesta_p90_ms": percentil(ms_resp, 0.90), "respuesta_n": len(ms_resp),
        "entrada_p90_ms": percentil(ms_entr, 0.90), "entrada_n": len(ms_entr),
        "mas_de_500ms": sum(1 for m in ms if m > MS_LARGA),
        "bucles_infinitos": len(infinitas),
        "curvas_distintas": len(curvas),
        "curvas": dict(sorted(curvas.items(), key=lambda kv: -kv[1])),
    }
    datos["presupuesto_movimiento"] = {
        "animaciones_en_primer_viewport": len(en_pantalla),
        "area_animada_px2": area,
        # Puede pasar del 100 %: las cajas se solapan y algunas son más grandes que la pantalla.
        # Es una medida de CUÁNTO se mueve a la vez, no una fracción de superficie.
        "suma_de_areas_vs_viewport_pct": round(100 * area / max(1, ancho * vh), 1),
    }

    # ⚠️ AQUI HUBO UN ERROR DE DISEÑO, y lo destapó correr esto contra el caso conocido.
    # La primera versión medía GD-01 comparando «texto visible sin JS» contra «texto visible CON
    # JS», y sobre `mal/attomo-digital.html` —la página rota de referencia— daba 62 %: no
    # disparaba. El motivo es que ahí la página está rota **en las dos pasadas** (GSAP nunca
    # arranca), así que la comparación era roto-contra-roto y el cociente salía tranquilizador.
    #
    # La medida que sí lo ve estaba en los datos y no se usaba: cuánto del texto que ESTÁ EN EL
    # DOM llega a verse. En attomo sin JS son 674 caracteres visibles y **1.674 escondidos** —el
    # 29 %—, y eso no depende de con qué se compare. Es además la pregunta correcta: «hay texto
    # aquí y no se ve» es el defecto; «se ve menos que con JS» era solo un síntoma.
    tv, ts = texto_normal["visible"], texto_sinjs["visible"]
    en_dom = lambda t: round(t["visible"] / max(1, t["visible"] + t["oculto"]), 3)   # noqa: E731
    datos["sin_js"] = {
        "texto_visible_con_js": tv, "texto_oculto_con_js": texto_normal["oculto"],
        "texto_visible_sin_js": ts, "texto_oculto_sin_js": texto_sinjs["oculto"],
        "visible_del_dom_con_js": en_dom(texto_normal),
        "visible_del_dom_sin_js": en_dom(texto_sinjs),
        "ratio_sin_js_vs_con_js": round(ts / tv, 3) if tv else 0.0,
        "umbral_visible_del_dom": VISIBLE_DEL_DOM, "umbral_comparativo": RATIO_SIN_JS}

    ms_red = [d["ms"] for d in inv_red["declaradas"] if d["ms"] > 0]
    ratio_red = round(texto_red["visible"] / tv, 3) if tv else 0.0
    datos["reduced_motion"] = {
        "declaraciones_con_movimiento": len(ms_red),
        "mediana_ms": round(statistics.median(ms_red)) if ms_red else 0,
        "texto_visible_ratio": ratio_red,
        "animaciones_corriendo": len(inv_red["corriendo"]),
    }

    # ── Salto de maqueta: el titular que se mueve mientras lo lees ───────────────────────────
    saltos = []
    por_texto = {t["texto"]: t for t in (tit0 or [])}
    for t in tit100:
        a = por_texto.get(t["texto"])
        if not a:
            continue
        d = max(abs(a["x"] - t["x"]), abs(a["y"] - t["y"]))
        if d > 0:
            saltos.append({"texto": t["texto"], "desplazamiento_px": d})
    saltos.sort(key=lambda s: -s["desplazamiento_px"])
    datos["salto_de_maqueta"] = {"titulares_comparados": len(tit100), "con_desplazamiento": saltos[:10],
                                 "maximo_px": saltos[0]["desplazamiento_px"] if saltos else 0,
                                 "umbral_px": SALTO_MAX_PX}
    datos["fotogramas"] = {k: f"frames/{k}-{ancho}.png" for k in ("t0", "t50", "t100")} | {
        "sin_js": f"frames/sin-js-{ancho}.png", "reduced": f"frames/reduced-{ancho}.png"}
    return datos


def senales(d):
    """Traduce los números a señales. Cada una dice qué se midió y contra qué umbral."""
    s, e, st = [], d["estadistica"], d
    sj = d["sin_js"]
    if sj["visible_del_dom_sin_js"] < VISIBLE_DEL_DOM:
        s.append(("P0", "GD-01 en vivo · hay texto y no se ve",
                  f"sin JS, de todo el texto que ESTÁ en el documento solo se ve el "
                  f"{sj['visible_del_dom_sin_js']*100:.0f} % ({sj['texto_visible_sin_js']} "
                  f"caracteres a la vista, {sj['texto_oculto_sin_js']} escondidos en opacity:0 o "
                  f"visibility:hidden; umbral {VISIBLE_DEL_DOM*100:.0f} %). El contenido está y "
                  f"depende de que el JS corra para aparecer"))
    # ⚠️ EL EQUIVALENTE CON JS SE REPORTA Y NO SE JUZGA, y hay que decir por qué.
    # Hubo aquí una señal P0 de «con JS también queda texto oculto». Disparaba sobre
    # `bien/elevaiti-v53.html` a 390 px —una referencia SANA— porque a esa anchura la página es
    # más larga y el recorrido automático no llega a revelarlo todo. O sea: el número no
    # distingue «el motor de revelado está roto» de «mi scroll no llegó hasta ahí», y un
    # instrumento que no puede distinguir esas dos cosas no debe emitir un veredicto sobre ellas
    # (`rules/verification.md`). El dato sigue en el informe y en el JSON, para que una persona lo
    # mire; lo que se retira es la conclusión.
    # La pasada SIN JS no tiene este problema y por eso es la que manda: sin JavaScript no hay
    # nada que revelar, así que lo que se ve es una propiedad estática de la página.
    if sj["ratio_sin_js_vs_con_js"] < RATIO_SIN_JS:
        s.append(("P0", "GD-01 en vivo · comparativo",
                  f"sin JS se ve el {sj['ratio_sin_js_vs_con_js']*100:.0f} % de lo que se ve con "
                  f"JS (umbral {RATIO_SIN_JS*100:.0f} %)"))
    if st["reduced_motion"]["texto_visible_ratio"] < RATIO_REDUCED:
        s.append(("P0", "reduced-motion pierde contenido",
                  f"con `prefers-reduced-motion: reduce` solo queda el "
                  f"{st['reduced_motion']['texto_visible_ratio']*100:.0f} % del texto: quien pide "
                  f"menos movimiento se queda además sin página"))
    elif st["reduced_motion"]["mediana_ms"] > 0 and st["reduced_motion"]["animaciones_corriendo"] > 0:
        s.append(("P1", "reduced-motion IGNORADO",
                  f"con la preferencia puesta siguen corriendo "
                  f"{st['reduced_motion']['animaciones_corriendo']} animación/es y la duración "
                  f"mediana declarada sigue en {st['reduced_motion']['mediana_ms']} ms"))
    if e["curvas_distintas"] > MAX_CURVAS:
        s.append(("P1", "no hay sistema de movimiento",
                  f"{e['curvas_distintas']} curvas distintas (máximo {MAX_CURVAS}): "
                  f"{', '.join(list(e['curvas'])[:6])}. Eso no es riqueza, son decisiones sueltas "
                  f"tomadas en momentos distintos"))
    if e["respuesta_p90_ms"] > MS_LARGA:
        s.append(("P2", "la RESPUESTA va lenta",
                  f"el p90 de las transiciones —lo que tarda en contestar a un clic o un hover— es "
                  f"{e['respuesta_p90_ms']} ms sobre {e['respuesta_n']} declaraciones "
                  f"(umbral {MS_LARGA}). Las entradas van aparte y están en "
                  f"{e['entrada_p90_ms']} ms: esas pueden ser largas a propósito"))
    if d["salto_de_maqueta"]["maximo_px"] > SALTO_MAX_PX:
        peor = d["salto_de_maqueta"]["con_desplazamiento"][0]
        s.append(("P1", "el titular se lee moviéndose",
                  f"«{peor['texto']}» se desplaza {peor['desplazamiento_px']} px entre el inicio y "
                  f"el final de su entrada (umbral {SALTO_MAX_PX})"))
    return s


def informar(datos, señales, destino: Path):
    e, sj, rm = datos["estadistica"], datos["sin_js"], datos["reduced_motion"]
    print("═" * 78)
    print(f" motion_probe.py · {datos['url']} · {datos['viewport']}")
    print("═" * 78)
    print(f" corriendo al cargar: {datos['inventario']['animaciones_corriendo']}  ·  "
          f"declaraciones con movimiento: {datos['inventario']['declaraciones_con_movimiento']}")
    print(f" duración   mediana {e['mediana_ms']} ms · p90 {e['p90_ms']} ms · "
          f"{e['bucles_infinitos']} bucle(s) infinito(s)")
    print(f"            respuesta (hover/clic) p90 {e['respuesta_p90_ms']} ms en {e['respuesta_n']} "
          f"decl.  ·  entrada p90 {e['entrada_p90_ms']} ms en {e['entrada_n']}")
    print(f" curvas     {e['curvas_distintas']} distintas (máximo sano {MAX_CURVAS}): "
          f"{', '.join(list(e['curvas'])[:5]) or '—'}")
    pm = datos["presupuesto_movimiento"]
    print(f" presupuesto {pm['animaciones_en_primer_viewport']} elemento(s) animados en el primer "
          f"viewport · suma de áreas = {pm['suma_de_areas_vs_viewport_pct']} % del viewport "
          f"(puede pasar de 100: se solapan)")
    print(f" sin JS     se ve el {sj['visible_del_dom_sin_js']*100:.0f} % del texto QUE HAY EN EL "
          f"DOM ({sj['texto_visible_sin_js']} a la vista, {sj['texto_oculto_sin_js']} escondidos)"
          f"  ·  con JS: {sj['visible_del_dom_con_js']*100:.0f} %")
    print(f" reduced    texto {rm['texto_visible_ratio']*100:.0f} % del de la pasada normal "
          f"(≥100 % = no se pierde nada; la comprobación es de una sola cara) · "
          f"{rm['animaciones_corriendo']} animación/es siguen corriendo")
    print(f" maqueta    el titular que más se mueve: {datos['salto_de_maqueta']['maximo_px']} px")
    print("─" * 78)
    if señales:
        for sev, titulo, texto in señales:
            print(f" [{sev}] {titulo}\n       {texto}")
    else:
        print(" Sin señales. Y esto SÍ significa que se midió: sin navegador este script sale con 2,")
        print(" no con 0 (rules/verification.md).")
    print("─" * 78)
    print(f" fotogramas y motion.json en {destino}")
    print(" Lo que estos números NO dicen: si el movimiento SIGNIFICA algo. Eso es juicio, y es de")
    print(" vera-art-director — aquí solo se le ponen los datos delante. Tampoco miden jank real:")
    print(" un headless compartido no es la tasa de fotogramas de nadie.")
    print("═" * 78)


def grabar_video(url, destino: Path, ejecutar: bool):
    """El vídeo NO se reimplementa: ya existe `scripts/pr_video.py` y graba con Playwright."""
    guion = Path(__file__).parent / "pr_video.py"
    salida = destino / "recorrido.webm"
    cmd = [sys.executable, str(guion), url, str(salida)]
    if not ejecutar:
        print(f"\n Para el vídeo del recorrido:\n   {' '.join(cmd)}")
        return
    if not guion.exists():
        print(f"⚠ no encuentro {guion}: el vídeo se omite (el resto de la medición es válida)",
              file=sys.stderr)
        return
    print(f"\n▸ delegando el vídeo en pr_video.py …")
    r = subprocess.run(cmd, timeout=300)
    print(f"  {'✓ ' + str(salida) if r.returncode == 0 else '⚠ pr_video.py salió con ' + str(r.returncode)}")


def main(argv) -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("url", help="http(s)://… — `file://` suele estar bloqueado")
    ap.add_argument("--out", default="/tmp/motion", help="directorio de salida (default /tmp/motion)")
    ap.add_argument("--viewport", default="1440x900,390x844",
                    help="uno o varios, separados por coma (default: escritorio Y móvil)")
    ap.add_argument("--wait-ms", type=int, default=ESPERA_MS,
                    help=f"espera tras 'load' antes de inventariar (default {ESPERA_MS})")
    ap.add_argument("--video", action="store_true", help="además, graba el recorrido con pr_video.py")
    a = ap.parse_args(argv)

    destino = Path(a.out)
    try:
        destino.mkdir(parents=True, exist_ok=True)
    except OSError as err:
        abortar(f"no puedo crear {destino}: {err}")

    try:
        import playwright  # noqa: F401
    except ImportError:
        abortar("Playwright no está instalado",
                "pip install playwright && playwright install chromium — requiere aprobación del "
                "Usuario (rules/governance.md §2).", destino)

    chrome = find_chrome()
    if not a.url.startswith(("http://", "https://")):
        abortar(f"la URL no es http(s): {a.url}",
                "`file://` suele estar bloqueado. Sirve la carpeta con "
                "`python3 -m http.server --bind 127.0.0.1 <puerto>`.", destino)

    todo, hay_senal = {"version": 1, "estado_instrumento": "medido", "pasadas": {}}, False
    for vp in [v.strip() for v in a.viewport.split(",") if v.strip()]:
        try:
            ancho, alto = (int(x) for x in vp.lower().split("x"))
        except ValueError:
            abortar(f"viewport mal escrito: {vp!r}", "formato: 1440x900", destino)
        try:
            datos = medir(a.url, destino, ancho, alto, a.wait_ms, chrome)
        except Exception as err:                                   # noqa: BLE001
            # Cualquier fallo de medición sale por 2. Un motion.json a medias con ceros parecería
            # una página sin movimiento, que es la mentira que este script existe para no contar.
            abortar(f"la medición falló en {vp}: {type(err).__name__}: {str(err)[:300]}",
                    "¿está la URL viva? ¿el navegador puede arrancar aquí?", destino)
        sen = senales(datos)
        datos["senales"] = [{"severidad": s, "titulo": t, "detalle": d} for s, t, d in sen]
        todo["pasadas"][vp] = datos
        hay_senal = hay_senal or bool(sen)
        informar(datos, sen, destino)

    todo["umbrales"] = {"ms_larga": MS_LARGA, "max_curvas": MAX_CURVAS,
                        "ratio_sin_js": RATIO_SIN_JS, "ratio_reduced": RATIO_REDUCED,
                        "salto_max_px": SALTO_MAX_PX}
    todo["no_mide"] = [
        "el jank real: un headless compartido no es la tasa de fotogramas de ningún dispositivo",
        "si el movimiento significa algo — eso es juicio, y es de vera-art-director",
        "el movimiento que solo se dispara al interactuar: se detecta DECLARADO, no se dispara",
        "si el revelado al hacer scroll está COMPLETO: el recorrido automático no garantiza haber "
        "llegado a todo, así que `visible_del_dom_con_js` se reporta pero NO produce veredicto. "
        "La pasada sin JS sí, porque ahí no hay nada que revelar y la medida es estática",
    ]
    (destino / "motion.json").write_text(json.dumps(todo, ensure_ascii=False, indent=1),
                                         encoding="utf-8")
    grabar_video(a.url, destino, a.video)
    return 1 if hay_senal else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
