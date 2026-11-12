#!/usr/bin/env python3
"""contrast_fixture.py — el compositor de contraste de Vera contra una página con defectos contados.

    <python con playwright> .claude/smoke/harvest/contrast_fixture.py [--chromium /usr/bin/chromium-browser] [--js <otro.js>]

Página de juguete (en memoria, sin servidor): un texto gris sobre blanco que FALLA (2,5:1), texto
blanco sobre un degradado oscuro que PASA (el falso positivo que el instrumento existe para evitar),
un fondo `oklab()` con opacidad que PASA y un texto sobre `url()` que tiene que salir como fondo
indeterminado, no como cumplido. Exit 0 si el instrumento da exactamente eso. Abre un navegador:
`check-ram.sh` antes y nunca a la vez que pytest.
"""
from __future__ import annotations

import os
import shutil
import sys

JS = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
                  "agents", "vera-art-director", "instruments", "contrast-compositor.js")
HTML = """<!doctype html><html><head><meta charset="utf-8"><title>f</title></head><body style="margin:0;background:#fff">
<main>
<header style="background:linear-gradient(90deg,#1e3a8a,#1d4ed8);padding:16px">
  <h1 style="color:#fff;font-size:16px;font-weight:400">CABECERA-DEGRADADO</h1></header>
<p style="color:#9ca3af;font-size:16px">GRIS-QUE-FALLA</p>
<div style="background:oklab(0.769729 0.0546647 0.155194 / 0.25);padding:8px">
  <span style="color:#111;font-size:16px">OKLAB-QUE-PASA</span></div>
<div style="background-image:url(data:image/gif;base64,R0lGODlhAQABAAAAACw=);padding:8px">
  <span style="color:#777;font-size:16px">SOBRE-IMAGEN</span></div>
</main></body></html>"""


def main() -> int:
    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        print("NO SE PUDO MEDIR: este python no tiene playwright (usa el del venv de QA)")
        return 2
    exe = None
    if "--chromium" in sys.argv:
        exe = sys.argv[sys.argv.index("--chromium") + 1]
    else:
        exe = shutil.which("chromium-browser") or shutil.which("chromium") or shutil.which("google-chrome")
    js_path = sys.argv[sys.argv.index("--js") + 1] if "--js" in sys.argv else JS
    with open(js_path, encoding="utf-8") as f:
        js = f.read()
    with sync_playwright() as p:
        b = p.chromium.launch(headless=True, executable_path=exe) if exe else p.chromium.launch(headless=True)
        page = b.new_page(viewport={"width": 800, "height": 600})
        errors = []
        page.on("pageerror", lambda e: errors.append(str(e)))
        page.set_content(HTML)
        r = page.evaluate(js)
        b.close()
    fails = [f["txt"] for f in r.get("contraste_fallos", [])]
    indet = [x["txt"] for x in r.get("indeterminados_muestra", [])]
    checks = [
        ("sanity_ok (oklab sobre blanco → rgb(252,231,194))", r.get("sanity_ok") is True),
        ("el gris sobre blanco FALLA", "GRIS-QUE-FALLA" in fails),
        ("el blanco sobre degradado oscuro NO falla (el falso positivo de leer backgroundColor)",
         "CABECERA-DEGRADADO" not in fails),
        ("el texto sobre oklab con opacidad NO falla", "OKLAB-QUE-PASA" not in fails),
        ("el texto sobre url() sale como fondo indeterminado", "SOBRE-IMAGEN" in indet),
        ("sin errores de página", not errors),
    ]
    bad = 0
    for name, ok in checks:
        bad += not ok
        print(f"  {'✓' if ok else '✗'} {name}")
    print(f"  · medidos {r.get('elementos_medidos')} · fallos {fails} · indeterminados {indet}")
    print("OK" if not bad else f"{bad} FALLO(S)")
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
