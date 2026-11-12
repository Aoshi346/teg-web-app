#!/usr/bin/env python3
"""Screenshot helper con detección robusta del binario de Chrome/Chromium.

Uso:
    python3 .claude/scripts/screenshot.py <url> <out.png> [width] [height] [wait_ms] [flags]

Flags (verificación enriquecida, opcionales):
    --multi          además del full desktop, captura full móvil (390) en <out>-m.<ext>
                     y slices verticales en <out>-s<N>.<ext>
    --dom            vuelca un snapshot ligero del DOM (headings, secciones+bg, anchors) a <out>.dom.json
    --audit-links    audita el status HTTP de los enlaces internos únicos -> <out>.links.json
    --guarda-pii     no guarda la captura si el texto de la página lleva datos personales
                     (siempre encendida si el proyecto tiene .claude/pii-capturas.json o es
                     delicado: .claude/proyecto-delicado.md). Ver guarda_pii_capturas.py

Por qué existe: los snippets de verificación visual suelen hardcodear
`/usr/bin/chromium-browser`, que en algunos servidores NO existe o le falta el
headless shell. Aquí detectamos el primer binario disponible (prefiriendo
google-chrome) y dejamos que Playwright use su propio Chromium si no hay ninguno.

Para auditar muchas páginas a la vez (masivo, paralelo) usa el pipeline
`.claude/templates/feedback_audit/capture_pages.py`; este helper es para 1 página.

Nota: `file://` suele estar bloqueado. Para HTML local, sirve la carpeta con
`python3 -m http.server` y pasa una URL `http://127.0.0.1:<puerto>/...`.
"""
import json
import os
import shutil
import sys
from urllib.parse import urlparse

DOM_JS = r"""
() => {
  const txt = e => (e.textContent || '').trim().replace(/\s+/g,' ').slice(0,160);
  const heads = [...document.querySelectorAll('h1,h2,h3,h4')].map(h => ({
    tag: h.tagName.toLowerCase(), text: txt(h),
    y: Math.round(h.getBoundingClientRect().top + window.scrollY)})).filter(h => h.text);
  const secs = [...document.querySelectorAll('section,header,footer,main,article,.wp-block-group')]
    .slice(0,120).map(s => { const cs = getComputedStyle(s); const r = s.getBoundingClientRect();
      return {tag: s.tagName.toLowerCase(), cls:(s.className||'').toString().slice(0,120),
        bg: cs.backgroundColor, y: Math.round(r.top+window.scrollY), h: Math.round(r.height)};
    }).filter(s => s.h > 40);
  const links = [...document.querySelectorAll('a[href]')].map(a => ({
    text: txt(a).slice(0,60), href: a.getAttribute('href'), abs: a.href,
    y: Math.round(a.getBoundingClientRect().top + window.scrollY)}));
  return {title: document.title, url: location.href, lang: document.documentElement.lang,
    height: document.body.scrollHeight, headings: heads, sections: secs, links: links};
}
"""


def find_chrome():
    """Devuelve el path del primer navegador disponible, o None (Playwright usa el suyo)."""
    for name in ("google-chrome", "google-chrome-stable", "chromium-browser", "chromium", "chrome"):
        path = shutil.which(name)
        if path:
            return path
    return None


def _suffix(out, suf):
    root, ext = os.path.splitext(out)
    return f"{root}{suf}{ext or '.png'}"


# ── guarda de datos personales (sub-ola 2.29, SE-42) ────────────────────────────────────────
def _guarda(flags):
    """(módulo, config) si la guarda tiene que correr; (None, None) si no. Falla cerrada: en un
    proyecto delicado sin la guarda instalada no se captura (exit 2)."""
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    try:
        import guarda_pii_capturas as gp
    except ImportError:
        raiz = os.environ.get("CLAUDE_PROJECT_DIR", os.getcwd())
        conf = os.path.join(raiz, ".claude", "CONFIGURACION.yaml")
        sensible = os.path.exists(conf) and any(
            m in open(conf, encoding="utf-8", errors="replace").read()
            for m in ("datos_sensibles: salud", "datos_reales_desarrollo: si", "datos_reales_desarrollo: sí"))
        if "--guarda-pii" in flags or sensible or any(os.path.exists(os.path.join(raiz, ".claude", f))
                                                      for f in ("pii-capturas.json", "proyecto-delicado.md")):
            print("[screenshot] falta guarda_pii_capturas.py y este proyecto la exige: no capturo",
                  file=sys.stderr)
            sys.exit(2)
        return None, None
    try:
        return gp, gp.activa(flags)
    except gp.ConfigInvalida as e:
        print(f"[screenshot] NO MEDIDO: {e}", file=sys.stderr)
        sys.exit(2)


def _revisar_antes(gp, conf, pagina, navegador, donde):
    if conf is None:
        return
    gp.enmascarar(pagina, conf)
    hallados = gp.revisar_pagina(pagina, conf)
    if hallados:
        print(gp.informe(hallados, donde), file=sys.stderr)
        navegador.close()
        sys.exit(1)
# ── fin de la guarda ────────────────────────────────────────────────────────────────────────


def main():
    flags = {a for a in sys.argv[1:] if a.startswith("--")}
    pos = [a for a in sys.argv[1:] if not a.startswith("--")]
    if len(pos) < 2:
        print(__doc__)
        sys.exit(1)
    gp, conf_pii = _guarda(flags)
    url, out = pos[0], pos[1]
    width = int(pos[2]) if len(pos) > 2 else 1440
    height = int(pos[3]) if len(pos) > 3 else 900
    wait_ms = int(pos[4]) if len(pos) > 4 else 3000

    from playwright.sync_api import sync_playwright

    chrome = find_chrome()
    launch_kwargs = {"headless": True, "args": ["--no-sandbox"]}
    if chrome:
        launch_kwargs["executable_path"] = chrome
        print(f"[screenshot] usando {chrome}")
    else:
        print("[screenshot] sin Chrome del sistema; usando el Chromium de Playwright")

    with sync_playwright() as p:
        b = p.chromium.launch(**launch_kwargs)
        pg = b.new_page(viewport={"width": width, "height": height})
        pg.goto(url, wait_until="domcontentloaded", timeout=30000)
        pg.wait_for_timeout(wait_ms)
        _revisar_antes(gp, conf_pii, pg, b, url)
        pg.screenshot(path=out, full_page=True)
        print(f"[screenshot] guardado en {out}")

        dom = pg.evaluate(DOM_JS) if (flags & {"--dom", "--multi", "--audit-links"}) else {}

        if "--dom" in flags:
            dom_path = os.path.splitext(out)[0] + ".dom.json"
            with open(dom_path, "w", encoding="utf-8") as f:
                json.dump(dom, f, ensure_ascii=False, indent=1)
            print(f"[screenshot] DOM -> {dom_path}")

        if "--multi" in flags:
            h = dom.get("height", 0) or 3000
            for i in range(min(8, max(1, (h + 1499) // 1500))):
                pg.evaluate(f"window.scrollTo(0,{i*1500})")
                pg.wait_for_timeout(200)
                pg.screenshot(path=_suffix(out, f"-s{i}"))
            mctx = b.new_context(viewport={"width": 390, "height": 844}, is_mobile=True)
            mpg = mctx.new_page()
            mpg.goto(url, wait_until="domcontentloaded", timeout=30000)
            mpg.wait_for_timeout(wait_ms)
            _revisar_antes(gp, conf_pii, mpg, b, f"{url} (móvil)")
            mpg.screenshot(path=_suffix(out, "-m"), full_page=True)
            mctx.close()
            print(f"[screenshot] multi: móvil {_suffix(out,'-m')} + slices -s<N>")

        if "--audit-links" in flags:
            host = urlparse(url).netloc
            uniq = sorted({l["abs"] for l in dom.get("links", [])
                           if l.get("abs", "").startswith("http") and host in l.get("abs", "")})
            res = {}
            for u in uniq:
                try:
                    res[u] = pg.request.get(u, timeout=20000).status
                except Exception as e:
                    res[u] = f"ERR:{type(e).__name__}"
            with open(f"{os.path.splitext(out)[0]}.links.json", "w", encoding="utf-8") as f:
                json.dump(res, f, ensure_ascii=False, indent=1)
            bad = sum(1 for s in res.values() if s != 200)
            print(f"[screenshot] links: {len(uniq)} únicos, {bad} != 200 -> {os.path.splitext(out)[0]}.links.json")

        b.close()


if __name__ == "__main__":
    main()
