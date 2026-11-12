#!/usr/bin/env python3
"""auditar_a11y.py — axe-core a 1440, 768 y 390 px: el paso determinista antes de opinar.

POR QUÉ EXISTE (UX-1, sub-ola 3.64). Cosechado de accounting_AMC (`scripts/auditar_a11y.py`): allí se
publicó «0 violaciones de WCAG 2.2 AA» midiendo solo a 1440 px, y Vera encontró
`scrollable-region-focusable` a 768 y 390. La cifra no era falsa: era INCOMPLETA. Una pantalla que
se usa en el móvil y no se audita en el móvil no está auditada. Aquí la versión genérica: URL y
credenciales por variable de entorno, nunca en el fichero.

LO QUE NO HACE. Deque, el fabricante de axe, dice que lo automático caza ~57 % de los problemas (dato
suyo, sin réplica independiente). Teclado, orden de foco, lector de pantalla y si el texto alternativo
DICE algo siguen siendo de Aitor. Este script es la base barata, no el veredicto.

USO (con el python de `bash .claude/scripts/preparar_navegador.sh`):
    $PY .claude/scripts/auditar_a11y.py http://127.0.0.1:5173/ http://127.0.0.1:5173/pedidos
    $PY .claude/scripts/auditar_a11y.py <url> --anchos 1440,390 --json > axe.json

Login opcional, solo por entorno (la contraseña nunca en un fichero ni en el historial):
    A11Y_LOGIN_URL=…/login A11Y_USER=… A11Y_PASS=… \
    [A11Y_USER_SEL='input[autocomplete=username]' A11Y_PASS_SEL='input[type=password]'
     A11Y_SUBMIT_SEL='button[type=submit]'] $PY .claude/scripts/auditar_a11y.py <urls…>

SALIDA: 0 medido sin violaciones · 1 hay violaciones · 2 no se pudo medir (sin playwright, axe
alterado, HTTP ≥400, login fallido, o alguna página × ancho sin medir). Cuenta lo medido frente a
lo pretendido: un «0» de 2 páginas de 6 no es un 0.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import shutil
import sys
import urllib.request
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[2]
# axe-core 4.10.2 (MPL-2.0). No va en el repo: pesa 540 KB y el hook de commits frena los >500 KB.
# Se descarga una vez a una caché y se fija por sha256 (el de cdnjs, idéntico byte a byte a la copia
# de accounting_AMC, comprobado el 31-10): si el CDN cambia el fichero, se aborta en vez de medir con
# otro instrumento. TL_AXE_PATH apunta a una copia local (p. ej. node_modules/axe-core/axe.min.js).
AXE_URL = "https://cdnjs.cloudflare.com/ajax/libs/axe-core/4.10.2/axe.min.js"
AXE = Path(os.environ.get("TL_AXE_PATH")
           or Path(os.environ.get("XDG_CACHE_HOME", Path.home() / ".cache")) / "tl-axe" / "axe-4.10.2.min.js")
AXE_SHA256 = "b511cd9dec01c76f4b2ad1723b66b6db37d4c2eb4ed199076e1829d9ee7b75e3"
REGLAS = ["wcag2a", "wcag2aa", "wcag21a", "wcag21aa", "wcag22aa"]
ANCHOS = (1440, 768, 390)


class Unmeasurable(Exception):
    pass


def axe_source() -> str:
    if not AXE.is_file():
        try:
            datos = urllib.request.urlopen(AXE_URL, timeout=30).read()
        except OSError as e:
            raise Unmeasurable(f"no está {AXE} y no se pudo descargar {AXE_URL}: {e}") from e
        if hashlib.sha256(datos).hexdigest() != AXE_SHA256:
            raise Unmeasurable(f"{AXE_URL} ya no es el axe-core 4.10.2 fijado (sha256 distinto)")
        AXE.parent.mkdir(parents=True, exist_ok=True)
        AXE.write_bytes(datos)
    datos = AXE.read_bytes()
    if hashlib.sha256(datos).hexdigest() != AXE_SHA256:
        raise Unmeasurable(f"{AXE} no es el axe-core 4.10.2 fijado (sha256 distinto): no se mide con un "
                        "instrumento que ha cambiado sin que nadie lo decida")
    return datos.decode("utf-8")


def login(pg) -> None:
    url = os.environ.get("A11Y_LOGIN_URL")
    if not url:
        return
    user, clave = os.environ.get("A11Y_USER"), os.environ.get("A11Y_PASS")
    if not user or not clave:
        raise Unmeasurable("A11Y_LOGIN_URL está puesta pero falta A11Y_USER o A11Y_PASS (vacías cuentan como falta)")
    pg.goto(url, wait_until="load", timeout=30000)
    pg.fill(os.environ.get("A11Y_USER_SEL", 'input[autocomplete="username"], input[type="email"], input[name="username"]'), user)
    pg.fill(os.environ.get("A11Y_PASS_SEL", 'input[type="password"]'), clave)
    pg.click(os.environ.get("A11Y_SUBMIT_SEL", 'button[type="submit"]'))
    pg.wait_for_load_state("load")
    if pg.url.rstrip("/") == url.rstrip("/"):
        # Seguir en la pantalla de login es el caso del «0 fallos» que medía el login (verification.md).
        raise Unmeasurable(f"tras el login la página sigue en {url}: se auditaría la pantalla de entrada")


def audit(urls, anchos, chromium=None) -> dict:
    try:
        from playwright.sync_api import sync_playwright
    except ImportError as e:
        raise Unmeasurable("este python no trae playwright: corre `bash .claude/scripts/preparar_navegador.sh` "
                        "y usa el python que imprime") from e
    codigo = axe_source()
    exe = chromium or os.environ.get("TL_CHROMIUM") or shutil.which("chromium-browser") \
        or shutil.which("chromium") or shutil.which("google-chrome")
    res = {"axe": "4.10.2", "reglas": REGLAS, "pretendidas": len(urls) * len(anchos), "medidas": 0,
           "paginas": []}
    with sync_playwright() as p:
        kw = {"headless": True, "args": ["--no-sandbox"]}
        if exe:
            kw["executable_path"] = exe
        nav = p.chromium.launch(**kw)
        try:
            for w in anchos:
                ctx = nav.new_context(viewport={"width": w, "height": 900})
                pg = ctx.new_page()
                login(pg)
                for url in urls:
                    try:
                        resp = pg.goto(url, wait_until="load", timeout=30000)
                    except Exception as e:  # noqa: BLE001 — sin servidor no hay página que medir
                        raise Unmeasurable(f"no se pudo abrir {url}: {str(e).splitlines()[0]}") from e
                    if resp is not None and resp.status >= 400:
                        raise Unmeasurable(f"{url} responde HTTP {resp.status} a {w}px")
                    pg.add_script_tag(content=codigo)
                    r = pg.evaluate("async (t) => await axe.run(document, {runOnly:{type:'tag',values:t}})",
                                    REGLAS)
                    res["medidas"] += 1
                    res["paginas"].append({
                        "url": url, "ancho": w, "pasan": len(r["passes"]),
                        "incompletas": len(r["incomplete"]),
                        "violaciones": [{
                            "id": v["id"], "impacto": v["impact"], "ayuda": v["help"],
                            "wcag": [t for t in v["tags"] if t.startswith("wcag")],
                            "nodos": len(v["nodes"]),
                            "ejemplo": v["nodes"][0]["html"][:160] if v["nodes"] else "",
                        } for v in r["violations"]],
                    })
                ctx.close()
        finally:
            nav.close()
    return res


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("urls", nargs="+")
    ap.add_argument("--anchos", default=",".join(map(str, ANCHOS)))
    ap.add_argument("--chromium")
    ap.add_argument("--json", action="store_true")
    a = ap.parse_args(argv)
    anchos = [int(x) for x in a.anchos.split(",") if x.strip()]
    if 390 not in anchos:
        print("aviso: sin 390 px no se mide el móvil, que es el ancho que más se olvida", file=sys.stderr)
    try:
        r = audit(a.urls, anchos, a.chromium)
    except Unmeasurable as e:
        print(f"NO SE PUDO MEDIR: {e}", file=sys.stderr)
        return 2
    total = sum(len(p["violaciones"]) for p in r["paginas"])
    if a.json:
        print(json.dumps(r, ensure_ascii=False, indent=1))
    else:
        for p in r["paginas"]:
            print(f"  {p['ancho']:>5}px {p['url']} · {len(p['violaciones'])} violación(es) · "
                  f"{p['pasan']} reglas OK · {p['incompletas']} para revisar a mano")
            for v in p["violaciones"]:
                print(f"      [{v['impacto']}] {v['id']} ({v['nodos']} nodos) — {v['ayuda']}")
        print(f"{r['medidas']}/{r['pretendidas']} página×ancho medidas · {total} violación(es) "
              f"· axe-core {r['axe']} ({', '.join(REGLAS)})")
    if r["medidas"] < r["pretendidas"]:
        return 2
    return 1 if total else 0


if __name__ == "__main__":
    sys.exit(main())
