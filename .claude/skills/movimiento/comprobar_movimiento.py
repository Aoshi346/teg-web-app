#!/usr/bin/env python3
"""comprobar_movimiento.py — la evidencia con la que se cierra un trabajo de movimiento.

Uso:
    python3 comprobar_movimiento.py <url> [--json salida.json]

Comprueba las cinco cosas que SÍ se pueden medir sin juicio (patterns/diseno/movimiento.md §11):

  1. GD-01 · ¿se ve el contenido con el JS apagado?  ← el fallo más caro y el más mudo
  2. GD-01 · ¿queda algún bloque CON TEXTO en pantalla y en opacidad 0 con el JS corriendo?
  3. GD-05 · ¿hay `prefers-reduced-motion` en CSS **y** la comprobación equivalente en JS?
  4. GD-06 · ¿hay `cursor:none` global?
  5. T18   · ¿los `@keyframes` tienen nombre de METÁFORA o nombre genérico?

Lo que NO comprueba, y hay que decirlo: si la metáfora es la correcta, si el momento
orquestado está donde toca, y si al quitar un reveal la página pierde algo. Eso es juicio
—`vera-art-director` o una persona— y su respuesta no es un número.

Salida: 0 sin hallazgos · 1 hay hallazgos · 2 NO SE PUDO MEDIR (un 2 no es «está bien»).

Doctrina: patterns/diseno/movimiento.md · Skill: skills/movimiento/SKILL.md
"""
import json
import re
import shutil
import sys

# Nombres que sirven para cualquier página del mundo. Un @keyframes llamado así se mueve
# y no dice nada del negocio: es la definición operativa de relleno (movimiento.md §1).
# El contraejemplo del corpus es `bien/elevaiti-v7.html:321` con un `float` a secas.
GENERICOS = {"float", "fade", "fadein", "fadeout", "fadeinup", "fadeindown", "fadeup",
             "pulse", "spin", "rotate", "bounce", "shake", "slide", "slidein", "slideup",
             "slidedown", "shimmer", "glow", "blink", "wiggle", "zoom", "zoomin", "scale",
             "wave", "ripple", "gradient", "gradientshift", "animate", "appear", "reveal"}

JS_PAGINA = r"""
() => {
  const cs = e => getComputedStyle(e);
  const vis = e => { const s = cs(e), r = e.getBoundingClientRect();
    return s.display!=='none' && s.visibility!=='hidden' && r.width>0 && r.height>0; };

  const anims = {}, durs = {};
  [...document.querySelectorAll('*')].filter(vis).forEach(e => {
    const s = cs(e);
    if (s.animationName && s.animationName !== 'none')
      s.animationName.split(',').forEach((n, i) =>
        anims[n.trim()] = (s.animationDuration.split(',')[i] || s.animationDuration).trim());
    if (s.transitionDuration && s.transitionDuration !== '0s')
      durs[s.transitionDuration] = (durs[s.transitionDuration] || 0) + 1;
  });

  let rmCss = false, ciegas = 0;
  [...document.styleSheets].forEach(ss => {
    try { if ([...ss.cssRules].some(r => (r.conditionText||'').includes('prefers-reduced-motion'))) rmCss = true; }
    catch (e) { ciegas++; }
  });

  return {
    animaciones: anims,
    duraciones_transicion: Object.entries(durs).sort((a,b)=>b[1]-a[1]).slice(0,8),
    reduced_motion_css: rmCss ? true : (ciegas ? `no medible (${ciegas} hojas de otro origen)` : false),
    cursor_none_global: cs(document.body).cursor === 'none'
             || cs(document.documentElement).cursor === 'none',
    scripts_en_linea: [...document.scripts].filter(s => !s.src).map(s => s.textContent).join('\n')
  };
}
"""

JS_MUDOS = r"""
() => [...document.querySelectorAll('section,header,article,div,h1,h2,h3,p,figure,li')]
  .filter(e => { const r = e.getBoundingClientRect(), s = getComputedStyle(e);
    // Se excluye lo que está oculto A PROPÓSITO: clases de utilidad y aria-hidden.
    // Sin esto, `div.hidden` de yessmassage salía como hallazgo y era correcto que estuviera
    // invisible — un falso positivo enseña a ignorar los verdaderos.
    const deliberado = /(^|[\s-])(hidden|sr-only|visually-hidden|screen-reader)([\s-]|$)/i
                         .test((e.className||'').toString())
                       || e.hasAttribute('hidden') || e.getAttribute('aria-hidden') === 'true';
    return !deliberado && r.top < window.innerHeight && r.bottom > 0 && r.width > 60 && r.height > 24
           && parseFloat(s.opacity) === 0 && (e.textContent||'').trim().length > 10; })
  .slice(0, 10)
  .map(e => e.tagName.toLowerCase() + '.' + (e.className||'').toString().trim().split(/\s+/).join('.').slice(0,40)
            + ' — “' + (e.textContent||'').trim().replace(/\s+/g,' ').slice(0,45) + '”')
"""


def main():
    if len(sys.argv) < 2:
        print(__doc__)
        return 2
    if len(sys.argv) < 2 or sys.argv[1] in ("-h", "--help"):
        print(__doc__); return 0
    url = sys.argv[1]
    destino = None
    for a in sys.argv[2:]:
        if a.startswith("--json"):
            destino = a.split("=", 1)[1] if "=" in a else sys.argv[sys.argv.index(a) + 1]

    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        print("NO SE PUDO MEDIR: falta playwright", file=sys.stderr)
        return 2

    chrome = (shutil.which("google-chrome") or shutil.which("google-chrome-stable")
              or shutil.which("chromium-browser") or shutil.which("chromium"))
    lanzar = {"headless": True, "args": ["--no-sandbox"]}
    if chrome:
        lanzar["executable_path"] = chrome

    js_externo = []
    try:
        with sync_playwright() as p:
            b = p.chromium.launch(**lanzar)
            pg = b.new_page(viewport={"width": 1440, "height": 900})
            # Capturamos el JS servido: la comprobación de reduced-motion en JS
            # no se ve en ningún estilo computado, solo en el código.
            pg.on("response", lambda r: js_externo.append(_cuerpo(r)) if "javascript" in
                  (r.headers.get("content-type") or "") else None)
            resp = pg.goto(url, wait_until="load", timeout=45000)
            # ── 2026-09-18 · esto analizaba tranquilamente una página de ERROR ──────────────
            # Medido: un servidor viejo ocupaba el puerto y devolvía 404; el comprobador midió
            # la página de error (119 caracteres), no encontró nada raro y dijo «sin hallazgos».
            # Es el fallo de `rules/verification.md`: el instrumento no podía llegar al sujeto y
            # devolvió una buena noticia en vez de abortar.
            if resp is not None and not (200 <= resp.status < 400):
                b.close()
                print(f"NO SE PUDO MEDIR: {url} responde HTTP {resp.status}. "
                      f"No se analiza una página de error como si fuera el diseño.", file=sys.stderr)
                return 2
            pg.wait_for_timeout(2500)
            d = pg.evaluate(JS_PAGINA)
            pg.mouse.wheel(0, 2400)
            pg.wait_for_timeout(1800)
            mudos = pg.evaluate(JS_MUDOS)
            con_js = len(pg.inner_text("body"))
            pgs = b.new_context(java_script_enabled=False).new_page()
            pgs.goto(url, wait_until="load", timeout=45000)
            sin_js = len(pgs.inner_text("body"))
            b.close()
    except Exception as e:
        print(f"NO SE PUDO MEDIR: {type(e).__name__}: {e}", file=sys.stderr)
        return 2

    todo_js = d.pop("scripts_en_linea", "") + "\n" + "\n".join(x for x in js_externo if x)
    rm_js = bool(re.search(r"prefers-reduced-motion", todo_js))

    animaciones = d["animaciones"]
    def raiz(n):
        return re.sub(r"[^a-z]", "", n.lower())
    genericas = [n for n in animaciones if raiz(n) in GENERICOS]
    con_nombre = [n for n in animaciones if raiz(n) not in GENERICOS]

    hallazgos = []
    # ── 2026-09-18 · aquí había un umbral ABSOLUTO (`sin_js < 200`) y medía la cosa
    # equivocada: el TAMAÑO de la página, no el fallo. Marcaba como defecto
    # `templates/diseno/motor-reveal.html`, que es LA implementación de referencia de esta
    # misma regla y se ve perfectamente sin JS — solo que es una demo de 100 caracteres.
    # Un instrumento que marca su propio contraejemplo correcto no discrimina: enseña a
    # ignorarlo. Lo que importa es la PROPORCIÓN de texto que sobrevive sin JS.
    proporcion = (sin_js / con_js) if isinstance(con_js, int) and con_js else None
    if proporcion is not None and proporcion < 0.6:
        hallazgos.append(f"GD-01 · sin JS solo sobrevive el {proporcion:.0%} del texto "
                         f"({sin_js} de {con_js} caracteres): el contenido depende del JS para verse")
    if mudos:
        hallazgos.append(f"GD-01 · {len(mudos)} bloques con texto están en pantalla y en opacidad 0 "
                         f"— hay un reveal que no dispara: {mudos[0]}")
    if d["reduced_motion_css"] is False:
        hallazgos.append("GD-05 · no hay bloque `prefers-reduced-motion` en CSS")
    if animaciones and not rm_js:
        hallazgos.append("GD-05 · hay animación y NINGÚN script mira `prefers-reduced-motion`: "
                         "lo que anima una librería desde JS se salta el bloque de CSS")
    if d["cursor_none_global"]:
        hallazgos.append("GD-06 · `cursor:none` global — si el JS falla no hay puntero en la página")
    if genericas and not con_nombre:
        hallazgos.append(f"T18 · todos los @keyframes tienen nombre genérico ({', '.join(genericas[:4])}): "
                         f"se mueve, pero no dice nada del negocio")

    salida = {"url": url, "sin_js_caracteres": sin_js, "con_js_caracteres": con_js,
              "proporcion_sin_js": round(proporcion, 3) if proporcion is not None else None, "invisibles_en_pantalla": mudos,
              "reduced_motion_css": d["reduced_motion_css"], "reduced_motion_js": rm_js,
              "cursor_none_global": d["cursor_none_global"],
              "animaciones": animaciones,
              "keyframes_con_nombre_propio": con_nombre, "keyframes_genericos": genericas,
              "duraciones_transicion": d["duraciones_transicion"], "hallazgos": hallazgos}
    if destino:
        with open(destino, "w", encoding="utf-8") as f:
            json.dump(salida, f, ensure_ascii=False, indent=2)

    print(f"texto visible · con JS: {con_js} · sin JS: {sin_js}"
          + (f" ({proporcion:.0%} sobrevive)" if proporcion is not None else ""))
    print(f"reduced-motion → CSS: {d['reduced_motion_css']} · JS: {rm_js}")
    print(f"cursor:none global: {d['cursor_none_global']}")
    print(f"@keyframes con nombre propio: {', '.join(con_nombre) or 'ninguno'}")
    print(f"@keyframes genéricos:         {', '.join(genericas) or 'ninguno'}")
    if hallazgos:
        print("\nHALLAZGOS:")
        for h in hallazgos:
            print(f"  ✗ {h}")
        return 1
    print("\nsin hallazgos mecánicos. Lo que falta —si la metáfora es la correcta— es juicio.")
    return 0


def _cuerpo(r):
    try:
        return r.text()
    except Exception:
        return ""


if __name__ == "__main__":
    sys.exit(main())
