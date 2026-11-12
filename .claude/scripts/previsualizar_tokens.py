#!/usr/bin/env python3
"""previsualizar_tokens.py — la PIEL de cada dirección de arte, puesta sobre el producto real.

POR QUÉ EXISTE (sub-ola 3.67, UX-13). En la fase 1.5 el Usuario rankea direcciones en la galería de
`direcciones-de-arte`, pero no ve cómo quedaría SU producto con cada una. En fitapp (10-17) se hizo
a mano y costó minutos: con Tailwind 4 los tokens son variables CSS, así que basta inyectar un
`<style>` con otros valores en `:root` (y la letra de los titulares) sobre la app ya construida, y
capturar. Sirvió para enseñar A/B/C al socio sobre cinco pantallas con datos reales, sin tocar
código.

QUÉ ENSEÑA Y QUÉ NO. Solo la piel: color, letra, radios, sombras — lo que viva en variables CSS o en
el CSS que traiga la dirección. **No enseña estructura**: una dirección que cambia la composición
(otro hero, otra rejilla) aquí se ve como «la misma pantalla con otros colores». Complementa a la
galería; no la sustituye.

ENTRADAS. Cada `--direccion NOMBRE=FICHERO`:
  · `.css`   se inyecta tal cual (puede traer `:root{…}` y reglas, p. ej. `h1{font-family:…}`).
  · `.json`  `{"--color-marca": "#c2410c", …}` → `:root{…}`.
  · `.html`  la dirección de `direcciones-de-arte`: se toman los tokens de su `:root`.
  Con `--parejas parejas.json` ({token_de_la_direccion: token_del_producto}) se traducen nombres;
  sin él, se aplican los que el producto declara con el mismo nombre.

SALIDA en `--salida`: `<direccion>/<ruta>-<ancho>.png` (más `actual/`, el producto sin tocar),
`index.html` con todas lado a lado y `resumen.json`. Con `--guardar-dom`, además
`<direccion>/dom/<ruta>.html`: el DOM pintado con su CSS en línea, que es lo que mide
`gate_diseno.py --dom` (sobre `.tsx` Impeccable da 0 y por URL no arranca como root).

CÓDIGOS: 0 capturado · 2 NO se pudo (sin Playwright o sin navegador, URL no local sin
`--permitir-remoto`, una ruta que no responde 2xx, o una dirección que no aplica NINGÚN token del
producto: eso no es una previsualización, es la misma captura dos veces).

USO:
    python3 .claude/scripts/previsualizar_tokens.py http://127.0.0.1:5173 \\
      --rutas / /clientes --anchos 1440,390 \\
      --direccion boho=.docs/plans/x/direcciones/a-boho.html \\
      --direccion editorial=.docs/plans/x/direcciones/c-editorial.html \\
      --parejas .docs/plans/x/direcciones/parejas.json --salida /tmp/previa --guardar-dom
    # rutas con sesión: --sesion estado.json  (storage_state de Playwright, guardado tras entrar)

Playwright y el navegador NO se instalan aquí: `scripts/preparar_navegador.sh` (sub-ola 3.64) deja
el entorno listo; en esta máquina, `/usr/bin/chromium-browser` con el Playwright de un venv.
"""
from __future__ import annotations

import argparse
import html
import json
import re
import shutil
import sys
from pathlib import Path
from urllib.parse import urlparse

sys.path.insert(0, str(Path(__file__).resolve().parent))
from gate_diseno import tokens_of  # noqa: E402  (el mismo lector de tokens que --contra-lienzo)

LOCAL_HOSTS = {"127.0.0.1", "localhost", "::1"}

# Recoge el CSS de la página (mismo origen) y lo deja en línea; quita scripts y hojas enlazadas.
# Un DOM guardado así se mide sin red y sin que la SPA vuelva a montar.
JS_INLINE_DOM = """() => {
  const css = [];
  for (const sheet of document.styleSheets) {
    try { for (const rule of sheet.cssRules) css.push(rule.cssText); } catch (e) {}
  }
  const clone = document.documentElement.cloneNode(true);
  clone.querySelectorAll('script, link[rel="stylesheet"], link[rel="modulepreload"]')
       .forEach((n) => n.remove());
  const style = document.createElement('style');
  style.setAttribute('data-inline-dom', '');
  style.textContent = css.join('\\n');
  clone.querySelector('head').appendChild(style);
  return '<!doctype html>\\n' + clone.outerHTML;
}"""


# Los tokens que el producto DECLARA, recorriendo también las reglas anidadas: Tailwind 4 deja su
# `@theme` dentro de `@layer theme { :root, :host { … } }`, y una hoja plana no los vería.
JS_PRODUCT_TOKENS = """() => {
  const names = new Set();
  const walk = (rules) => {
    for (const r of rules) {
      if (r.style) for (let i = 0; i < r.style.length; i++)
        if (r.style[i].startsWith('--')) names.add(r.style[i].slice(2));
      if (r.cssRules) walk(r.cssRules);
    }
  };
  for (const s of document.styleSheets) { try { walk(s.cssRules); } catch (e) {} }
  return [...names];
}"""


def has_rules(css: str | None) -> bool:
    """¿Trae el .css algo más que tokens? (p. ej. `h1 { font-family: … }`)."""
    if not css:
        return False
    rest = re.sub(r"/\*.*?\*/", "", css, flags=re.S)
    return bool(re.sub(r":root\s*\{[^}]*\}", "", rest).strip())


def fail(reason: str, hint: str = "") -> None:
    print(f"⛔ previsualizar_tokens.py NO PUDO: {reason}", file=sys.stderr)
    if hint:
        print(f"   {hint}", file=sys.stderr)
    sys.exit(2)


def browser_error(e: Exception) -> str:
    """El error de Playwright ENTERO: la causa suele ir en sus «Browser logs» (verification.md)."""
    lines = [x for x in str(e).splitlines() if x.strip()][:20]
    text = "\n    ".join(lines) or type(e).__name__
    if "Executable doesn't exist" in str(e):
        text += ("\n  → no hay navegador: `scripts/preparar_navegador.sh`, "
                 "o instala chromium-browser")
    return text


def read_direction(path: Path) -> tuple[str | None, dict[str, str]]:
    """(css_literal | None, {token: valor}). El .css va tal cual; .json y .html dan tokens."""
    if not path.is_file():
        fail(f"no existe la dirección {path}")
    text = path.read_text(encoding="utf-8", errors="replace")
    suffix = path.suffix.lower()
    if suffix == ".css":
        tokens = {k: sorted(v)[0] for k, v in tokens_of(text, False).items()}
        return text, tokens
    if suffix == ".json":
        try:
            data = json.loads(text)
        except json.JSONDecodeError as e:
            fail(f"{path} no es JSON válido: {e}")
        if not isinstance(data, dict) or not data:
            fail(f"{path} debe ser un objeto {{\"--token\": \"valor\"}}")
        return None, {k.lstrip("-"): str(v) for k, v in data.items()}
    if suffix in (".html", ".htm"):
        tokens = {}
        for k, values in tokens_of(text, True).items():
            tokens[k] = sorted(values)[0]   # un token con dos valores (claro/oscuro): el primero
        if not tokens:
            fail(f"{path} no declara tokens en su :root", "¿es la dirección o la galería?")
        return None, tokens
    fail(f"{path}: se esperaba .css, .json o .html")
    return None, {}


def slug(route: str) -> str:
    s = re.sub(r"[^A-Za-z0-9]+", "-", route.strip("/")).strip("-")
    return s or "inicio"


def build_style(css: str | None, tokens: dict[str, str], pairs: dict[str, str],
                product_tokens: set[str]) -> tuple[str, list[str]]:
    """El <style> a inyectar y la lista de tokens del PRODUCTO que de verdad cambia."""
    applied, decls = [], []
    for name, value in tokens.items():
        target = pairs.get(name, name)
        if target in product_tokens:
            applied.append(target)
            decls.append(f"--{target}: {value} !important;")
    style = (f":root {{ {' '.join(decls)} }}\n" if decls else "") + (css or "")
    return style, sorted(set(applied))


def main(argv: list[str]) -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("url", help="la base del producto, p. ej. http://127.0.0.1:5173")
    ap.add_argument("--direccion", action="append", default=[], metavar="NOMBRE=FICHERO",
                    help="una dirección (.css, .json o .html); se repite")
    ap.add_argument("--rutas", nargs="+", default=["/"], help="rutas a capturar (default: /)")
    ap.add_argument("--anchos", default="1440,390", help="anchos en px, separados por comas")
    ap.add_argument("--parejas", help="JSON {token_de_la_direccion: token_del_producto}")
    ap.add_argument("--salida", required=True, help="carpeta donde se escriben las capturas")
    ap.add_argument("--guardar-dom", action="store_true",
                    help="guarda también el DOM pintado con su CSS (para gate_diseno.py --dom)")
    ap.add_argument("--sesion", help="storage_state de Playwright para rutas con login")
    ap.add_argument("--esperar-ms", type=int, default=1500,
                    help="espera tras «load» para que la SPA monte (default: 1500)")
    ap.add_argument("--permitir-remoto", action="store_true",
                    help="acepta una URL que no es 127.0.0.1/localhost (por defecto, se niega)")
    a = ap.parse_args(argv)

    host = urlparse(a.url).hostname or ""
    if host not in LOCAL_HOSTS and not a.permitir_remoto:
        fail(f"{a.url} no es local", "el producto se sirve en 127.0.0.1 y se llega por túnel "
             "(rules/security.md); --permitir-remoto si de verdad es otro sitio.")
    if not a.direccion:
        fail("falta al menos una --direccion NOMBRE=FICHERO")
    try:
        widths = [int(x) for x in a.anchos.split(",") if x.strip()]
    except ValueError:
        fail(f"--anchos «{a.anchos}» no son números")
    pairs: dict[str, str] = {}
    if a.parejas:
        try:
            raw = json.loads(Path(a.parejas).read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as e:
            fail(f"no puedo leer {a.parejas}: {type(e).__name__}")
        pairs = {k.lstrip("-"): v.lstrip("-") for k, v in raw.items()}
    directions = []
    for item in a.direccion:
        name, _, file = item.partition("=")
        if not name or not file or slug(name).lower() == "actual":
            fail(f"--direccion «{item}»: se espera NOMBRE=FICHERO (y «actual» está reservado)")
        css, tokens = read_direction(Path(file))
        directions.append((slug(name), css, tokens))

    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        fail("falta playwright en este Python",
             "scripts/preparar_navegador.sh lo deja listo (3.64); aquí se usa el de un venv.")
    chrome = (shutil.which("chromium-browser") or shutil.which("chromium")
              or shutil.which("google-chrome") or shutil.which("google-chrome-stable"))
    launch = {"headless": True, "args": ["--no-sandbox"]}
    if chrome:
        launch["executable_path"] = chrome

    out = Path(a.salida)
    out.mkdir(parents=True, exist_ok=True)
    summary = {"url": a.url, "routes": a.rutas, "widths": widths,
               "browser": chrome or "playwright", "directions": {}, "intended": 0, "captured": 0}
    base = a.url.rstrip("/")
    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(**launch)
            ctx_args = {"storage_state": a.sesion} if a.sesion else {}
            for label, css, tokens in [("actual", None, {})] + directions:
                info = {"applied_tokens": [], "screenshots": [], "dom": []}
                summary["directions"][label] = info
                for width in widths:
                    ctx = browser.new_context(viewport={"width": width, "height": 900}, **ctx_args)
                    page = ctx.new_page()
                    for route in a.rutas:
                        summary["intended"] += 1
                        resp = page.goto(base + route, wait_until="load", timeout=45000)
                        if resp is None or not (200 <= resp.status < 300):
                            fail(f"{base + route} respondió {resp.status if resp else 'nada'}",
                                 "una captura de un error no es una previsualización.")
                        page.wait_for_timeout(a.esperar_ms)
                        product = set(page.evaluate(JS_PRODUCT_TOKENS))
                        if label != "actual":
                            style, applied = build_style(css, tokens, pairs, product)
                            if not applied and not has_rules(css):
                                fail(f"la dirección «{label}» no aplica NINGÚN token del producto "
                                     f"en {route} ({len(product)} tokens declarados allí)",
                                     "pasa --parejas con "
                                     "{token_de_la_direccion: token_del_producto}.")
                            info["applied_tokens"] = sorted(set(info["applied_tokens"])
                                                            | set(applied))
                            page.add_style_tag(content=style)
                            page.wait_for_timeout(200)
                        folder = out / label
                        folder.mkdir(parents=True, exist_ok=True)
                        png = folder / f"{slug(route)}-{width}.png"
                        page.screenshot(path=str(png), full_page=True)
                        info["screenshots"].append(str(png.relative_to(out)))
                        summary["captured"] += 1
                        if a.guardar_dom and width == widths[0]:
                            (folder / "dom").mkdir(exist_ok=True)
                            dom = folder / "dom" / f"{slug(route)}.html"
                            dom.write_text(page.evaluate(JS_INLINE_DOM), encoding="utf-8")
                            info["dom"].append(str(dom.relative_to(out)))
                    ctx.close()
            browser.close()
    except SystemExit:
        raise
    except Exception as e:                                     # noqa: BLE001
        fail("el navegador falló", browser_error(e))

    (out / "resumen.json").write_text(json.dumps(summary, ensure_ascii=False, indent=1),
                                      encoding="utf-8")
    rows = []
    for route in a.rutas:
        for width in widths:
            cells = "".join(
                f"<figure><figcaption>{html.escape(lbl)}</figcaption>"
                f"<img src=\"{html.escape(lbl)}/{slug(route)}-{width}.png\" "
                f"alt=\"{html.escape(lbl)} · "
                f"{html.escape(route)} a {width} px\" loading=\"lazy\"></figure>"
                for lbl in summary["directions"])
            rows.append(f"<h2>{html.escape(route)} · {width} px</h2>"
                        f"<div class=\"fila\">{cells}</div>")
    (out / "index.html").write_text(
        "<!doctype html><html lang=es><meta charset=utf-8>"
        "<title>Previsualización de direcciones</title>"
        "<style>body{font-family:system-ui,sans-serif;margin:16px;background:#fafafa;color:#111}"
        ".fila{display:grid;grid-template-columns:repeat(auto-fit,minmax(280px,1fr));gap:12px}"
        "figure{margin:0}img{width:100%;border:1px solid #ddd}figcaption{font-weight:600}</style>"
        "<h1>La piel de cada dirección sobre el producto</h1>"
        "<p>Solo la piel: color, letra y radios. "
        "La estructura es la del producto en todas: para comparar composiciones, la galería de "
        "direcciones-de-arte.</p>" + "".join(rows), encoding="utf-8")
    print(f"previsualizar_tokens.py · {summary['captured']}/{summary['intended']} capturas · "
          f"{len(directions)} dirección(es) + actual · {out}/index.html")
    for label, info in summary["directions"].items():
        if label != "actual":
            print(f"  {label}: {len(info['applied_tokens'])} token(s) del producto cambiados"
                  + (f" · DOM en {label}/dom/" if info["dom"] else ""))
    return 0 if summary["captured"] == summary["intended"] else 2


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
