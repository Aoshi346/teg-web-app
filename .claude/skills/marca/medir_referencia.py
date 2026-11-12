#!/usr/bin/env python3
"""medir_referencia.py — MIDE una referencia visual en vez de describirla de memoria.

Uso:
    python3 medir_referencia.py <url> <salida.json> [ancho] [alto]

Devuelve hechos, no impresiones: familias y tamaños REALES de los nodos de más área,
hex computados ponderados por superficie, radios, sombras, rejillas, y —lo que ninguna
extracción estática ve— qué se MUEVE y qué cambia al hacer scroll.

Tres veredictos, nunca dos (rules/verification.md §el instrumento que no puede medir):
  · un dato medido
  · `false` cuando se miró y no había
  · `"no medible (…)"` cuando el instrumento no pudo llegar al sujeto

Y si lo que cargó es un MURO —página de reto de bot, HTTP ≥ 400, página de error o de bloqueo con
200, un formulario de contraseña que ocupa la pantalla, captcha en una página corta, o casi sin
texto—, el JSON se escribe igual pero lleva `"muro": "<qué se vio>"` y la salida es 2: lo medido es
el muro, no la referencia. Antes salía 0 midiendo la pantalla de login de
McMaster (evolution, improvements #9; MO-24, sub-ola 2.17).

Salida: 0 medida · 2 no se pudo medir (argumentos, sin playwright ni navegador, error, o muro).

Por qué `executable_path`: en esta máquina Playwright NO tiene su Chromium descargado
(`/root/.cache/ms-playwright` no existe) y `/usr/bin/google-chrome` sí. Se detecta igual
que en `.claude/scripts/screenshot.py`, que es la referencia de la casa.

Doctrina: patterns/diseno/ · Skill: skills/marca/SKILL.md (paso 3, references-visual.md)
"""
import json
import re
import shutil
import sys

# ── Lo que se mide dentro de la página ───────────────────────────────────────
JS_MEDIR = r"""
() => {
  const cs = e => getComputedStyle(e);
  const area = e => { const r = e.getBoundingClientRect(); return r.width * r.height; };
  const vis = e => { const s = cs(e), r = e.getBoundingClientRect();
    return s.display !== 'none' && s.visibility !== 'hidden' && r.width > 0 && r.height > 0; };
  const txt = e => (e.textContent || '').trim().replace(/\s+/g, ' ');
  const top = o => Object.entries(o).sort((a,b) => b[1]-a[1]).slice(0,8)
                     .map(([valor, veces]) => ({valor, veces}));

  // TIPOGRAFÍA — ordenada por ÁREA, no por etiqueta: así sale el display de verdad
  // aunque sea un <span>, y no un <h1> escondido de 12px.
  // Se admiten hijos en línea (<br>, <span>, <em>) porque el titular display del
  // corpus los lleva casi siempre: filtrarlos dejaba fuera justo lo que se busca.
  const tipografia = [...document.querySelectorAll('h1,h2,h3,h4,p,a,span,li,button,div,blockquote')]
    .filter(e => vis(e) && txt(e).length > 1 &&
                 [...e.children].every(c => /^(BR|SPAN|EM|I|B|STRONG|A|SMALL|MARK)$/.test(c.tagName)))
    .map(e => ({ tag: e.tagName.toLowerCase(), family: cs(e).fontFamily, size: cs(e).fontSize,
                 weight: cs(e).fontWeight, lh: cs(e).lineHeight, ls: cs(e).letterSpacing,
                 tt: cs(e).textTransform, color: cs(e).color,
                 area: Math.round(area(e)), muestra: txt(e).slice(0, 70) }))
    .sort((a,b) => b.area - a.area).slice(0, 25);

  // COLOR — ponderado por superficie. Un hex del CSS no dice cuánto se ve;
  // esto ordena por cuánta pantalla ocupa, que es lo que percibe una persona.
  const peso = {};
  [...document.querySelectorAll('*')].filter(vis).forEach(e => {
    const s = cs(e), a = area(e);
    [['fondo', s.backgroundColor], ['texto', s.color]].forEach(([rol, v]) => {
      if (!v || v === 'rgba(0, 0, 0, 0)') return;
      const k = rol + '|' + v;
      peso[k] = (peso[k] || 0) + (rol === 'fondo' ? a : a / 20);   // el texto pesa menos
    });
  });
  const colores = Object.entries(peso).sort((a,b) => b[1]-a[1]).slice(0, 18)
    .map(([k, v]) => ({ rol: k.split('|')[0], valor: k.split('|')[1], peso: Math.round(v) }));

  // FORMA — radios, sombras, rejillas y anchos de contenedor
  const radios = {}, sombras = {}, rejillas = [], anchos = {};
  [...document.querySelectorAll('*')].filter(vis).forEach(e => {
    const s = cs(e), r = e.getBoundingClientRect();
    if (s.borderRadius && s.borderRadius !== '0px') radios[s.borderRadius] = (radios[s.borderRadius]||0)+1;
    if (s.boxShadow && s.boxShadow !== 'none')      sombras[s.boxShadow] = (sombras[s.boxShadow]||0)+1;
    if (s.display === 'grid' && r.width > 320)
      rejillas.push({ cols: s.gridTemplateColumns, gap: s.gap, ancho: Math.round(r.width) });
    const w = Math.round(r.width);
    if (w > 600 && w < 1700 && (s.marginLeft === 'auto' || s.maxWidth !== 'none')) anchos[w] = (anchos[w]||0)+1;
  });

  // MOVIMIENTO — lo declarado. El NOMBRE del @keyframes es el dato caro:
  // `floatPlant` dice de qué va el negocio; `float` no dice nada (T18).
  const trans = {}, anims = {};
  [...document.querySelectorAll('*')].filter(vis).forEach(e => {
    const s = cs(e);
    if (s.transitionDuration && s.transitionDuration !== '0s') {
      const k = s.transitionDuration + ' · ' + s.transitionTimingFunction;
      trans[k] = (trans[k]||0)+1;
    }
    if (s.animationName && s.animationName !== 'none') {
      const k = s.animationName + ' · ' + s.animationDuration;
      anims[k] = (anims[k]||0)+1;
    }
  });

  // prefers-reduced-motion: una hoja de otro origen LANZA al leer sus reglas.
  // Eso no es «no lo tiene»: es «no lo pude mirar», y se dice.
  let rmHit = false, rmCiego = 0;
  [...document.styleSheets].forEach(ss => {
    try { if ([...ss.cssRules].some(r => (r.conditionText||'').includes('prefers-reduced-motion'))) rmHit = true; }
    catch (e) { rmCiego++; }
  });

  return {
    url: location.href, titulo: document.title, alto: document.body.scrollHeight,
    tipografia, colores,
    radios: top(radios), sombras: top(sombras), rejillas: rejillas.slice(0, 8), anchos: top(anchos),
    movimiento: {
      transiciones: top(trans), animaciones: top(anims),
      reduced_motion: rmHit ? true : (rmCiego ? `no medible (${rmCiego} hojas de otro origen)` : false),
      cursor_none_global: getComputedStyle(document.body).cursor === 'none'
    }
  };
}
"""

# Lo que DEBERÍA verse ahora y no se ve: en el viewport, con tamaño y con texto, y en opacidad 0.
# El primer intento contaba TODO lo que estuviera en opacidad 0 y no discriminaba —una página larga
# y sana tiene decenas esperando su turno más abajo—: el bueno del corpus daba 60 y el roto 25.
# Acotarlo al viewport es lo que convierte el número en señal (rules/verification.md).
JS_MUDOS = r"""
() => [...document.querySelectorAll('section,header,article,div,h1,h2,h3,p,figure,img,li')]
  .filter(e => { const r = e.getBoundingClientRect(), s = getComputedStyle(e);
    // Se excluye lo que está oculto A PROPÓSITO: clases de utilidad y aria-hidden.
    // Sin esto, `div.hidden` de yessmassage salía como hallazgo y era correcto que estuviera
    // invisible — un falso positivo enseña a ignorar los verdaderos.
    const deliberado = /(^|[\s-])(hidden|sr-only|visually-hidden|screen-reader)([\s-]|$)/i
                         .test((e.className||'').toString())
                       || e.hasAttribute('hidden') || e.getAttribute('aria-hidden') === 'true';
    return !deliberado && r.top < window.innerHeight && r.bottom > 0 && r.width > 60 && r.height > 24
           && parseFloat(s.opacity) === 0 && (e.textContent||'').trim().length > 10; })
  .slice(0, 12)
  .map(e => e.tagName.toLowerCase() + ' · ' + (e.className||'').toString().slice(0,40)
            + ' · ' + (e.textContent||'').trim().replace(/\s+/g,' ').slice(0,50))
"""

# Huella de opacidad/transform/posición, para diferenciar antes y después del scroll
JS_HUELLA = r"""
() => [...document.querySelectorAll('section,header,main,article,div,h1,h2,img,figure,svg')]
  .slice(0, 500)
  .map((e, i) => i + '|' + getComputedStyle(e).opacity + '|' + getComputedStyle(e).transform
                   + '|' + Math.round(e.getBoundingClientRect().top))
  .join('\n')
"""


# ¿Es la referencia, o el muro que hay delante? Lo que se ve, no lo que dice el HTML.
JS_MURO = r"""
() => {
  const vis = e => { const s = getComputedStyle(e), r = e.getBoundingClientRect();
    return s.display !== 'none' && s.visibility !== 'hidden' && r.width > 0 && r.height > 0; };
  // Una página de DESAFÍO (la del reto de Cloudflare o PerimeterX) no es lo mismo que un WIDGET de
  // captcha en el formulario de contacto de una landing normal: lo primero es un muro, lo segundo
  // solo lo es si además casi no hay página (verificadores de la 2.17).
  const desafio = !!document.querySelector('#challenge-form, #challenge-running, ' +
                                           '#cf-challenge-running, #px-captcha') ||
                  typeof window._cf_chl_opt !== 'undefined';
  const widget = [...document.querySelectorAll('iframe')].some(f =>
                   /captcha|challenges\.cloudflare|turnstile|arkoselabs/i.test(f.src || ''))
              || !!document.querySelector('.cf-turnstile, .g-recaptcha, .h-captcha');
  // Un login se mide por lo que OCUPA en la primera pantalla, no por el texto de la página: el
  // acceso de la cabecera de una tienda es una tira; el muro de login, la pantalla entera.
  const vw = window.innerWidth * window.innerHeight;
  let formulario = 0;
  for (const i of document.querySelectorAll('input[type=password]')) {
    if (!vis(i)) continue;
    const r = (i.closest('form') || i.parentElement).getBoundingClientRect();
    const ancho = Math.max(0, Math.min(r.right, window.innerWidth) - Math.max(r.left, 0));
    const alto = Math.max(0, Math.min(r.bottom, window.innerHeight) - Math.max(r.top, 0));
    formulario = Math.max(formulario, ancho * alto / vw);
  }
  const texto = (document.body ? document.body.innerText : '').replace(/\s+/g, ' ').trim();
  // Los titulares a la vista: el aviso de un soft-404 largo va en el h1, no al principio del texto
  // (ahí está la navegación).
  const titulares = [...document.querySelectorAll('h1, h2')].filter(vis).slice(0, 3)
                      .map(h => h.innerText.replace(/\s+/g, ' ').trim().slice(0, 200));
  return { password: [...document.querySelectorAll('input[type=password]')].some(vis),
           texto: texto.length, inicio: texto.slice(0, 400), formulario, desafio, widget,
           titulares };
}
"""
# El título de una página de reto es el título ENTERO («Just a moment...», «Attention Required! |
# Cloudflare», «403 Forbidden»): «Forbidden Planet · cómics», «Forbidden» a secas (un estudio) o «Un
# momento para ti · spa» no lo son. Sin «403»/«429» sueltos: «Modelo 403» no es un muro, y un 403 de
# verdad ya lo caza el estado HTTP.
TITULO_RETO = re.compile(
    r"^\W*(?:(?:\d{3}\W+)?(just a moment|attention required|access denied|acceso denegado|"
    r"un momento|too many requests|verify you are human|are you a robot|no soy un robot)|"
    r"\d{3}\W+forbidden)"
    r"[\W\d]*(?:cloudflare\W*)?$", re.I)
# El aviso de un soft-404 dicho AL VISITANTE: «Vaya, no encontramos esa página», «la página que
# buscas no existe», «we can't find that page». Es un mensaje, no un tema: un artículo sobre diseñar
# páginas de error no habla así (tercera pasada del verificador de la 2.17).
NO_ENCONTRADA = (
    r"no (?:encontramos|hemos (?:podido )?encontra(?:do|r)|podemos encontrar|pudimos encontrar) "
    r"(?:esa|esta|la) p[áa]gina|p[áa]gina que buscas no (?:existe|est[áa])|"
    r"(?:can'?t|cannot|couldn'?t) find (?:that|this|the) page|"
    r"page you(?:'re| are) looking for "
    r"(?:does(?:n'?t| not) exist|(?:could|can)(?:n'?t|not) be found)")
# Una página de error o de bloqueo que responde 200 (soft-404, «Acceso restringido», DDoS-Guard),
# en el título o al principio de una página corta.
ERROR_O_BLOQUEO = re.compile(
    r"p[áa]gina no encontrada|page not found|\b404\b.{0,20}(not found|no encontrad)|"
    r"not found\b.{0,5}$|"
    r"acceso restringido|access restricted|ddos-guard|checking your browser|has been blocked|"
    r"p[áa]gina bloqueada|" + NO_ENCONTRADA, re.I)
# En un TITULAR (h1/h2) de una página de cualquier largo, el soft-404 con la navegación entera
# alrededor: el aviso al visitante, o un titular que es SOLO el error («404», «Error 404»,
# «Página no encontrada»). Que lo mencione no basta: «30 diseños de página no encontrada» es una
# referencia. Límite: un soft-404 largo con el aviso fuera del título y de los titulares (en un
# párrafo tras la navegación) se sigue midiendo.
TITULAR_DE_ERROR = re.compile(
    NO_ENCONTRADA + r"|^\W*(?:error\W*)?404\W*$|"
    r"^\W*(?:error\W*)?(?:404\W*)?(?:p[áa]gina no encontrada|page not found)\W*$", re.I)
# Un título de login es el título ENTERO, con la marca delante o detrás como mucho («Iniciar
# sesión», «Sign in to GitHub · GitHub», «Amazon Sign-In»), no uno que contiene la palabra:
# «50 Login screen designs for inspiration» es una referencia de diseño, también con un
# formulario de ejemplo con su contraseña (tercera pasada del verificador de la 2.17: antes salía
# muro). Límite: una galería titulada solo «Login · Dribbble», con un formulario de ejemplo, sigue
# saliendo muro.
TITULO_LOGIN = re.compile(
    # la marca delante es UNA palabra («Amazon Sign-In») o va antes de un separador («Mi cuenta -»)
    r"^\W*(?:[^\s|·—–:]{1,30}\s+|[^|·—–:]{1,30}?\s[|·—–:-]\s*)?"
    r"(?:log[ -]?in|sign[ -]?in|iniciar sesi[óo]n|inicia sesi[óo]n|identif[íi]cate|captcha)"
    r"(?:\s+(?:to|into|en|a)\s+[^|·—–:]{1,30})?"
    r"(?:\s+(?:o|or)\s+(?:reg[íi]str\w*|sign[ -]?up|register|cr[ée]a\w*\s+(?:una|an)\s+"
    r"(?:cuenta|account)))?\s*(?:[|·—–:-].*)?$", re.I)
MIN_TEXTO = 300            # caracteres visibles: por debajo no hay página que medir
CORTA = 1000               # con una contraseña o un captcha a la vista, una página así es el muro
FORMULARIO_MURO = 0.06     # fracción de la primera pantalla: un muro de login ocupa, una tira no


def muro(estado: int | None, titulo: str, senal: dict) -> str | None:
    """La razón si lo cargado es un muro, o None."""
    corta = senal["texto"] < CORTA
    if estado is not None and estado >= 400:
        return f"HTTP {estado}"
    if senal["desafio"]:
        return "página de reto de bot (Cloudflare, PerimeterX)"
    if TITULO_RETO.search(titulo or ""):
        return f"título de página de reto: «{titulo[:60]}»"
    if ERROR_O_BLOQUEO.search(titulo or "") or (corta and ERROR_O_BLOQUEO.search(senal["inicio"])):
        return f"página de error o de bloqueo con HTTP 200: «{(titulo or senal['inicio'])[:60]}»"
    for t in senal.get("titulares", []):
        if TITULAR_DE_ERROR.search(t):
            return f"titular de página de error con HTTP 200: «{t[:60]}»"
    if senal["password"] and (senal["formulario"] >= FORMULARIO_MURO or corta):
        return (f"formulario de contraseña en el {senal['formulario']:.0%} de la primera "
                f"pantalla y {senal['texto']} caracteres: es un login")
    if senal["widget"] and corta:
        return f"captcha a la vista y {senal['texto']} caracteres: es un muro"
    if TITULO_LOGIN.search(titulo or "") and (senal["password"] or senal["widget"]):
        return f"título de login con contraseña o captcha: «{titulo[:60]}»"
    if senal["texto"] < MIN_TEXTO:
        return f"{senal['texto']} caracteres visibles (mínimo {MIN_TEXTO})"
    return None


def error_de_navegador(e: Exception) -> str:
    """El error de Playwright ENTERO (la causa suele ir en sus líneas de «Browser logs»), y la pista
    de instalar solo cuando es eso lo que falta: con una librería del sistema rota, «playwright
    install» no arregla nada (code-review-gate de la 2.17)."""
    lineas = [x for x in str(e).splitlines() if x.strip()][:20]
    texto = "\n    ".join(lineas) or type(e).__name__
    if "Executable doesn't exist" in str(e):
        texto += "\n  → no hay navegador: `playwright install chromium`, o instala chromium-browser"
    return texto


def main():
    if len(sys.argv) < 3:
        print(__doc__)
        sys.exit(2)
    url, salida = sys.argv[1], sys.argv[2]
    ancho = int(sys.argv[3]) if len(sys.argv) > 3 else 1440
    alto = int(sys.argv[4]) if len(sys.argv) > 4 else 900

    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        print("NO SE PUDO MEDIR: falta playwright", file=sys.stderr)
        sys.exit(2)

    chrome = (shutil.which("google-chrome") or shutil.which("google-chrome-stable")
              or shutil.which("chromium-browser") or shutil.which("chromium"))
    lanzar = {"headless": True, "args": ["--no-sandbox"]}
    if chrome:
        lanzar["executable_path"] = chrome

    try:
      with sync_playwright() as p:
        b = p.chromium.launch(**lanzar)
        pg = b.new_page(viewport={"width": ancho, "height": alto})
        resp = pg.goto(url, wait_until="load", timeout=45000)
        pg.wait_for_timeout(2500)

        d = pg.evaluate(JS_MEDIR)
        d["navegador"] = chrome or "chromium de playwright"
        d["estado_http"] = resp.status if resp else None
        d["muro"] = muro(d["estado_http"], d.get("titulo", ""), pg.evaluate(JS_MURO))

        # Qué CAMBIA al bajar. Es lo único que distingue un reveal real
        # de un CSS que lo declara y nunca se dispara (el caso attomo).
        antes = pg.evaluate(JS_HUELLA)
        pg.mouse.wheel(0, max(2000, d["alto"] // 3))
        pg.wait_for_timeout(1800)
        despues = pg.evaluate(JS_HUELLA)
        cambios = [x for a, x in zip(antes.split("\n"), despues.split("\n"))
                   if a.split("|")[1:3] != x.split("|")[1:3]]
        # En pantalla AHORA, con texto, y en opacidad 0: con el JS corriendo eso es un
        # reveal declarado que nunca dispara. Es el caso attomo (GD-01).
        mudos = pg.evaluate(JS_MUDOS)
        d["al_hacer_scroll"] = {"elementos_que_cambian": len(cambios), "muestra": cambios[:10],
                                "invisibles_en_pantalla": len(mudos), "cuales": mudos}

        # Con el JS apagado: ¿sigue habiendo página? (T11b / GD-01)
        try:
            pg2 = b.new_context(java_script_enabled=False).new_page()
            pg2.goto(url, wait_until="load", timeout=45000)
            d["sin_js"] = {"caracteres_visibles": len(pg2.inner_text("body"))}
        except Exception as e:
            d["sin_js"] = {"caracteres_visibles": f"no medible ({type(e).__name__})"}
        b.close()
    except Exception as e:
        # Un fallo aquí NO es «la referencia no tiene nada»: es que no se pudo mirar.
        # Colapsar los dos casos es el modo de fallo de rules/verification.md.
        # La caché de Playwright desaparece a mitad de sesión (AMC, improvements #6): que lo diga.
        print(f"NO SE PUDO MEDIR {url}: {type(e).__name__}:\n    {error_de_navegador(e)}",
              file=sys.stderr)
        sys.exit(2)

    with open(salida, "w", encoding="utf-8") as f:
        json.dump(d, f, ensure_ascii=False, indent=2)

    if d["muro"]:
        print(f"NO SE PUDO MEDIR {url}: muro: {d['muro']} — lo medido es el muro, no la referencia "
              f"(el JSON queda en {salida} con `muro`)", file=sys.stderr)
        sys.exit(2)

    t = d["tipografia"][0] if d["tipografia"] else {}
    anim = ", ".join(a["valor"] for a in d["movimiento"]["animaciones"][:3]) or "ninguna"
    print(f"{d['titulo'][:60]}")
    print(f"  display   {t.get('size','?')} · {t.get('family','?')[:40]} · lh {t.get('lh','?')}")
    print(f"  fondo     {d['colores'][0]['valor'] if d['colores'] else '?'}")
    print(f"  @keyframes {anim}")
    mudos = d['al_hacer_scroll']['invisibles_en_pantalla']
    if mudos:
        print(f"  ⚠ {mudos} bloques CON TEXTO están en pantalla y en opacidad 0 — "
              f"reveal que no dispara (GD-01): {d['al_hacer_scroll']['cuales'][0][:60]}")
    print(f"  al bajar cambian {d['al_hacer_scroll']['elementos_que_cambian']} elementos "
          f"· sin JS {d['sin_js']['caracteres_visibles']} car. "
          f"· reduced-motion {d['movimiento']['reduced_motion']}")
    print(f"  → {salida}")


if __name__ == "__main__":
    main()
