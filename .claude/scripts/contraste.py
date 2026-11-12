#!/usr/bin/env python3
"""contraste.py — el contraste se MIDE, no se opina. Tres modos y tres desenlaces.

POR QUÉ EXISTE (UX-5, sub-ola 3.64). El template no tenía medidor: Vera y Aitor medían con su
instrumento de navegador o a ojo, y tres proyectos habían escrito el suyo (cold_calling_coach:
parejas declaradas; webs: mide la página, compone transparencias y degradados y encontró 21 pares
bajo AA que nadie había visto). El caso que lo justifica: en elvion, al cambiar `--widget-accent` de
ámbar a teal, el texto navy #243447 sobre la burbuja teal #2f6f8f quedó en 2,29:1 (hace falta 4,5:1)
y solo lo vio Vera en la iteración 11. Una pareja declarada y medida en cada cambio lo habría cazado
en el commit.

MODOS
  --par FG BG [--umbral 4.5]       una pareja suelta (hex, rgb(), hsl(), triplete HSL, oklch(), oklab())
  --tokens design-system.md [--css app.css …]
                                   las parejas de la tabla «Texto | Fondo | Mínimo | Para qué» del
                                   design-system, resolviendo `--token` contra los bloques de código
                                   del mismo fichero y los .css que se pasen (fase 3, motores-de-diseno §F1)
  --dom URL [--anchos 1440,768,390] [--scope SELECTOR]
                                   todo lo pintado, con el compositor de Vera
                                   (agents/vera-art-director/instruments/contrast-compositor.js):
                                   compone alfa y degradados y mide el peor caso (fase 5). Necesita el
                                   python de `preparar_navegador.sh`
  --self-test                      el caso de elvion falla, su gemelo pasa, oklch cuadra con marca-lumi
                                   (sin navegador; para --dom, los fixtures de smoke/diseno/GD-14/
                                   servidos en 127.0.0.1: malo.html da 2,29:1 a los tres anchos)

SALIDA (rules/verification.md §«el instrumento que no puede medir debe ABORTAR»)
  0  medido · todas las parejas (o todo el texto medido) en AA
  1  medido · hay al menos un par bajo su umbral
  2  NO SE PUDO MEDIR: sin tabla de parejas, un token que no resuelve, sin navegador, página vacía,
     o la comprobación de cordura del compositor en falso

QUÉ NO MIDE: el estado hover/foco (hay que provocarlo), texto sobre foto (sale «indeterminado» y el
cero pasa a PARCIAL), ni si el color es la ÚNICA señal (eso lo mira una persona: SC 1.4.1).
Umbrales WCAG 2.2 AA: 4,5:1 texto normal · 3:1 texto grande (≥24 px o ≥18,66 px en negrita) y
componentes de interfaz (SC 1.4.11).
"""
from __future__ import annotations

import argparse
import json
import math
import re
import shutil
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[2]
COMPOSITOR = RAIZ / ".claude" / "agents" / "vera-art-director" / "instruments" / "contrast-compositor.js"
ANCHOS = (1440, 768, 390)


class Unmeasurable(Exception):
    """El instrumento no pudo llegar al sujeto: sale con 2, nunca con 0."""


# ── Color → sRGB (0-255) + alfa ──────────────────────────────────────────────────────────────────
def _num(s: str, escala: float = 1.0) -> float:
    s = s.strip()
    if s.endswith("%"):
        return float(s[:-1]) / 100 * escala
    return float(s)


def _hsl_to_rgb(h: float, s: float, l: float):
    h = (h % 360) / 360
    if s == 0:
        return (l * 255,) * 3

    def f(p, q, t):
        t %= 1
        if t < 1 / 6:
            return p + (q - p) * 6 * t
        if t < 1 / 2:
            return q
        if t < 2 / 3:
            return p + (q - p) * (2 / 3 - t) * 6
        return p
    q = l * (1 + s) if l < 0.5 else l + s - l * s
    p = 2 * l - q
    return tuple(f(p, q, h + d) * 255 for d in (1 / 3, 0, -1 / 3))


def _oklab_to_rgb(L: float, a: float, b: float):
    l_ = L + 0.3963377774 * a + 0.2158037573 * b
    m_ = L - 0.1055613458 * a - 0.0638541728 * b
    s_ = L - 0.0894841775 * a - 1.2914855480 * b
    l, m, s = l_ ** 3, m_ ** 3, s_ ** 3
    lin = (4.0767416621 * l - 3.3077115913 * m + 0.2309699292 * s,
           -1.2684380046 * l + 2.6097574011 * m - 0.3413193965 * s,
           -0.0041960863 * l - 0.7034186147 * m + 1.7076147010 * s)

    def gamma(c):
        c = min(max(c, 0.0), 1.0)          # fuera de gamut se recorta, como hace el navegador al pintar
        return 12.92 * c if c <= 0.0031308 else 1.055 * c ** (1 / 2.4) - 0.055
    return tuple(gamma(c) * 255 for c in lin)


def _args(cuerpo: str):
    alfa = 1.0
    if "/" in cuerpo:
        cuerpo, a = cuerpo.split("/", 1)
        alfa = _num(a)
    partes = [p for p in re.split(r"[\s,]+", cuerpo.strip()) if p]
    return partes, alfa


def to_rgba(valor: str, tokens: dict[str, str] | None = None, _prof: int = 0):
    """Devuelve (r, g, b, alfa) o lanza Unmeasurable. Entiende var(--x) contra `tokens`."""
    v = valor.strip().strip("`").rstrip(";").strip()
    tokens = tokens or {}
    if _prof > 10:
        raise Unmeasurable(f"var() circular en {valor!r}")
    m = re.fullmatch(r"var\(\s*(--[\w-]+)\s*(?:,\s*(.+))?\)", v)
    if m or v.startswith("--"):
        nombre = m.group(1) if m else v
        if nombre in tokens:
            return to_rgba(tokens[nombre], tokens, _prof + 1)
        if m and m.group(2):
            return to_rgba(m.group(2), tokens, _prof + 1)
        raise Unmeasurable(f"el token {nombre} no está definido en lo que se pasó")
    v = v.lower()
    if v.startswith("#"):
        h = v[1:]
        if len(h) in (3, 4):
            h = "".join(c * 2 for c in h)
        if len(h) not in (6, 8) or not re.fullmatch(r"[0-9a-f]+", h):
            raise Unmeasurable(f"hex ilegible: {valor!r}")
        rgb = [int(h[i:i + 2], 16) for i in (0, 2, 4)]
        return (*rgb, int(h[6:8], 16) / 255 if len(h) == 8 else 1.0)
    m = re.fullmatch(r"(rgba?|hsla?|oklch|oklab)\((.*)\)", v)
    if m:
        fn, (p, alfa) = m.group(1), _args(m.group(2))
        if fn.startswith("rgb"):
            if len(p) == 4:
                alfa = _num(p.pop())
            return (*(_num(x, 255) for x in p[:3]), alfa)
        if fn.startswith("hsl"):
            if len(p) == 4:
                alfa = _num(p.pop())
            h = float(p[0].replace("deg", ""))
            return (*_hsl_to_rgb(h, _num(p[1], 1) if "%" in p[1] else float(p[1]) / 100,
                                _num(p[2], 1) if "%" in p[2] else float(p[2]) / 100), alfa)
        L = _num(p[0], 1.0)
        if fn == "oklab":
            return (*_oklab_to_rgb(L, _num(p[1], 0.4), _num(p[2], 0.4)), alfa)
        C, H = _num(p[1], 0.4), float(p[2].replace("deg", ""))
        return (*_oklab_to_rgb(L, C * math.cos(math.radians(H)), C * math.sin(math.radians(H))), alfa)
    # Triplete HSL crudo («210 40% 50%»), el formato de los tokens de shadcn/Tailwind: es un VALOR
    # válido para hsl(var(--x)), no un color. Aquí se mide lo que pintaría hsl(...).
    m = re.fullmatch(r"(-?[\d.]+)(?:deg)?\s+([\d.]+)%\s+([\d.]+)%(?:\s*/\s*([\d.]+%?))?", v)
    if m:
        return (*_hsl_to_rgb(float(m.group(1)), float(m.group(2)) / 100, float(m.group(3)) / 100),
                _num(m.group(4)) if m.group(4) else 1.0)
    nombres = {"white": "#ffffff", "black": "#000000"}
    if v in nombres:
        return to_rgba(nombres[v])
    raise Unmeasurable(f"color que no sé leer: {valor!r}")


def over(fg, bg):
    """Compone fg (con alfa) sobre bg opaco."""
    a = fg[3]
    return tuple(fg[i] * a + bg[i] * (1 - a) for i in range(3)) + (1.0,)


def _lum(c) -> float:
    def f(x):
        x /= 255
        return x / 12.92 if x <= 0.04045 else ((x + 0.055) / 1.055) ** 2.4
    return 0.2126 * f(c[0]) + 0.7152 * f(c[1]) + 0.0722 * f(c[2])


def ratio(fg, bg) -> float:
    blanco = (255, 255, 255, 1.0)
    bg = over(bg, blanco) if bg[3] < 1 else bg     # fondo translúcido: sobre blanco, y se avisa
    fg = over(fg, bg) if fg[3] < 1 else fg
    la, lb = _lum(fg), _lum(bg)
    return (max(la, lb) + 0.05) / (min(la, lb) + 0.05)


def measure_pair(fg: str, bg: str, umbral: float, tokens=None, para="") -> dict:
    cf, cb = to_rgba(fg, tokens), to_rgba(bg, tokens)
    r = ratio(cf, cb)
    return {"texto": fg, "fondo": bg, "ratio": round(r, 2), "umbral": umbral, "pasa": r >= umbral,
            "para": para, "fondo_translucido": cb[3] < 1}


# ── --tokens ─────────────────────────────────────────────────────────────────────────────────────
RE_DEF = re.compile(r"(--[\w-]+)\s*:\s*([^;}\n]+)")


def tokens_from(textos: list[str]) -> dict[str, str]:
    out: dict[str, str] = {}
    for t in textos:
        # En un .md solo cuentan los bloques de código: la prosa también menciona «--color-x: …».
        bloques = re.findall(r"```[^\n]*\n(.*?)```", t, re.S) if "```" in t else [t]
        for b in bloques:
            for k, v in RE_DEF.findall(b):
                out[k] = re.sub(r"/\*.*?\*/", "", v).strip()
    return out


def pairs_from(md: str) -> list[tuple[str, str, float, str]]:
    """La tabla cuya cabecera empieza por «| Texto | Fondo |». Mínimo vacío = 4,5."""
    filas, dentro = [], False
    for linea in md.splitlines():
        celdas = [c.strip() for c in linea.strip().strip("|").split("|")] if linea.strip().startswith("|") else None
        if celdas is None:
            dentro = False
            continue
        if not dentro:
            dentro = len(celdas) >= 2 and celdas[0].lower().startswith("texto") and celdas[1].lower().startswith("fondo")
            continue
        if set("".join(celdas)) <= set("-: "):
            continue
        if "PERSONALIZAR" in linea:
            continue
        um = celdas[2].replace(",", ".").replace(":1", "").strip() if len(celdas) > 2 else ""
        filas.append((celdas[0].strip("`"), celdas[1].strip("`"), float(um) if um else 4.5,
                      celdas[3] if len(celdas) > 3 else ""))
    return filas


def tokens_mode(md_path: Path, css: list[Path]) -> tuple[list[dict], list[str]]:
    if not md_path.is_file():
        raise Unmeasurable(f"no existe {md_path}")
    md = md_path.read_text(encoding="utf-8")
    pares = pairs_from(md)
    if not pares:
        raise Unmeasurable(f"{md_path} no tiene tabla «| Texto | Fondo | Mínimo | Para qué |» con filas "
                        "rellenas: sin parejas declaradas no hay nada que medir (plantilla: "
                        "templates/core/design-system.md §2)")
    for c in css:
        if not c.is_file():
            raise Unmeasurable(f"no existe {c}")
    toks = tokens_from([md] + [c.read_text(encoding="utf-8") for c in css])
    res, no_medibles = [], []
    for fg, bg, um, para in pares:
        try:
            res.append(measure_pair(fg, bg, um, toks, para))
        except Unmeasurable as e:
            no_medibles.append(f"{fg} sobre {bg}: {e}")
    return res, no_medibles


def _total(v) -> int:
    return sum(v.values()) if isinstance(v, dict) else int(v or 0)


# ── --dom ────────────────────────────────────────────────────────────────────────────────────────
def dom_mode(url: str, anchos, scope: str | None, chromium: str | None) -> dict:
    try:
        from playwright.sync_api import sync_playwright
    except ImportError as e:
        raise Unmeasurable("este python no trae playwright: corre `bash .claude/scripts/preparar_navegador.sh` "
                        "y lanza contraste.py con el python que imprime") from e
    if not COMPOSITOR.is_file():
        raise Unmeasurable(f"falta el compositor de Vera: {COMPOSITOR}")
    js = COMPOSITOR.read_text(encoding="utf-8")
    exe = chromium or shutil.which("chromium-browser") or shutil.which("chromium") or shutil.which("google-chrome")
    salida = {"url": url, "anchos": {}}
    with sync_playwright() as p:
        kw = {"headless": True, "args": ["--no-sandbox"]}
        if exe:
            kw["executable_path"] = exe
        b = p.chromium.launch(**kw)
        try:
            for w in anchos:
                pg = b.new_page(viewport={"width": w, "height": 900})
                try:
                    resp = pg.goto(url, wait_until="load", timeout=30000)
                except Exception as e:  # noqa: BLE001 — sin servidor no hay página que medir
                    raise Unmeasurable(f"no se pudo abrir {url}: {str(e).splitlines()[0]}") from e
                if resp is not None and resp.status >= 400:
                    raise Unmeasurable(f"{url} responde HTTP {resp.status}: se mediría la página de error")
                if scope:
                    pg.evaluate(f"window.__VERA_SCOPE = {json.dumps(scope)}")
                r = pg.evaluate(js)
                pg.close()
                if not r.get("sanity_ok"):
                    raise Unmeasurable(f"a {w}px la comprobación de cordura del compositor salió en falso "
                                    f"({r.get('sanity')}): la medición no vale")
                if not r.get("scope_ok", True):
                    raise Unmeasurable(f"a {w}px no existe el ámbito {scope!r}")
                salida["anchos"][w] = {
                    "medidos": r.get("elementos_medidos", 0),
                    "fallos": r.get("contraste_fallos", []),
                    "indeterminados": r.get("_indet", 0),
                    # El compositor lo da por causa (opacity, mix-blend, filter, backdrop): se suma.
                    "no_componibles": _total(r.get("no_componibles", 0)),
                }
        finally:
            b.close()
    if not any(a["medidos"] for a in salida["anchos"].values()):
        raise Unmeasurable(f"0 elementos de texto medidos en {url}: la página está vacía o no cargó")
    return salida


# ── --self-test ──────────────────────────────────────────────────────────────────────────────────
def self_test() -> int:
    casos = [
        ("elvion: navy #243447 sobre teal #2f6f8f FALLA a 2,29", measure_pair("#243447", "#2f6f8f", 4.5),
         lambda r: not r["pasa"] and r["ratio"] == 2.29),
        ("elvion antes: navy sobre ámbar #e9a020 PASA a 5,74", measure_pair("#243447", "#e9a020", 4.5),
         lambda r: r["pasa"] and r["ratio"] == 5.74),
        ("blanco sobre navy (la burbuja del bot) PASA", measure_pair("#ffffff", "#243447", 4.5),
         lambda r: r["pasa"]),
        ("marca-lumi: tinta oklch(0.24 0.02 230) sobre la página = 15,27 (lo que declara)",
         measure_pair("oklch(0.24 0.02 230)", "oklch(0.975 0.006 230)", 4.5), lambda r: r["ratio"] == 15.27),
        ("triplete HSL «0 0% 100%» = blanco", measure_pair("0 0% 100%", "#000", 4.5),
         lambda r: r["ratio"] == 21.0),
    ]
    fallos = 0
    for nombre, r, ok in casos:
        bien = ok(r)
        fallos += not bien
        print(f"  {'✓' if bien else '✗'} {nombre} → {r['ratio']}:1")
    try:
        to_rgba("var(--no-existe)", {})
        print("  ✗ un token sin definir debía ser NO MEDIBLE")
        fallos += 1
    except Unmeasurable:
        print("  ✓ un token sin definir es NO MEDIBLE (exit 2), no un cero")
    print(f"{len(casos) + 1 - fallos}/{len(casos) + 1} casos")
    return 1 if fallos else 0


def report(pares: list[dict], no_medibles: list[str], como_json: bool) -> int:
    malos = [p for p in pares if not p["pasa"]]
    if como_json:
        print(json.dumps({"pares": pares, "no_medibles": no_medibles}, ensure_ascii=False, indent=1))
    else:
        for p in pares:
            marca = "✓" if p["pasa"] else "✗"
            aviso = "  (fondo translúcido: compuesto sobre blanco)" if p["fondo_translucido"] else ""
            print(f"  {marca} {p['ratio']:>5.2f}:1 (mín {p['umbral']}) {p['texto']} sobre {p['fondo']}"
                  f"{' · ' + p['para'] if p['para'] else ''}{aviso}")
        for n in no_medibles:
            print(f"  ? NO MEDIBLE {n}")
        print(f"{len(pares) - len(malos)}/{len(pares)} parejas en AA"
              + (f" · {len(no_medibles)} sin medir" if no_medibles else ""))
    if malos:
        return 1
    return 2 if no_medibles else 0


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    g = ap.add_mutually_exclusive_group(required=True)
    g.add_argument("--par", nargs=2, metavar=("TEXTO", "FONDO"))
    g.add_argument("--tokens", type=Path, metavar="DESIGN_SYSTEM_MD")
    g.add_argument("--dom", metavar="URL")
    g.add_argument("--self-test", action="store_true")
    ap.add_argument("--umbral", type=float, default=4.5)
    ap.add_argument("--css", type=Path, nargs="*", default=[])
    ap.add_argument("--anchos", default=",".join(map(str, ANCHOS)))
    ap.add_argument("--scope")
    ap.add_argument("--chromium")
    ap.add_argument("--json", action="store_true")
    a = ap.parse_args(argv)
    try:
        if a.self_test:
            return self_test()
        if a.par:
            return report([measure_pair(a.par[0], a.par[1], a.umbral)], [], a.json)
        if a.tokens:
            pares, nm = tokens_mode(a.tokens, a.css)
            return report(pares, nm, a.json)
        anchos = [int(x) for x in a.anchos.split(",") if x.strip()]
        r = dom_mode(a.dom, anchos, a.scope, a.chromium)
        total = sum(len(x["fallos"]) for x in r["anchos"].values())
        parcial = any(x["indeterminados"] or x["no_componibles"] for x in r["anchos"].values())
        if a.json:
            print(json.dumps(r, ensure_ascii=False, indent=1))
        else:
            for w, x in r["anchos"].items():
                print(f"  {w:>5}px · {x['medidos']} textos medidos · {len(x['fallos'])} bajo AA"
                      + (f" · {x['indeterminados']} sobre fondo indeterminado" if x["indeterminados"] else "")
                      + (f" · {x['no_componibles']} no componibles" if x["no_componibles"] else ""))
                for f in x["fallos"][:15]:
                    print(f"      ✗ {f['ratio']}:1 (mín {f['umbral']}) «{f['txt']}» {f['fg']} sobre {f['bg']}")
            print(f"{total} textos bajo AA en {len(r['anchos'])} anchos"
                  + (" · cero PARCIAL: hay texto que no se pudo medir contra su fondo real" if parcial and not total else ""))
        return 1 if total else 0
    except Unmeasurable as e:
        print(f"NO SE PUDO MEDIR: {e}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(main())
