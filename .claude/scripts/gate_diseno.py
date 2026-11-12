#!/usr/bin/env python3
"""gate_diseno.py — la capa DETERMINISTA del gusto, ANTES de gastar un turno de auditor.

QUE ES. Envuelve al detector de terceros **Impeccable** (`npx impeccable detect --json`) y le
suma las 15 reglas MEDIDAS de esta casa (`GD-01`..`GD-15`), que viven en
`resources/referencias-diseno/anti-patrones.yaml` y no se inventan aquí: cada una apunta al
fichero y la línea del corpus donde el defecto ocurrió de verdad.

POR QUE EXISTE. Vera, Ignacio y Lidia cuestan un turno de modelo cada uno y su criterio es
caro. Preguntarles si una página tiene `cursor:none` global o un token de color que miente es
malgastarlos: eso lo decide un parser sin opinión. El gate se queda con lo comprobable y les
deja lo que de verdad es juicio.

LOS TRES DESENLACES (rules/verification.md §«el instrumento que no puede medir debe ABORTAR»).
Un chequeo NO tiene dos salidas, tiene tres, y colapsarlas destruye justo la información que
hace falta para arreglarlo:

    0  medido · sin hallazgos de reglas en estado 'activo'
    1  medido · HAY hallazgos de reglas 'activo'
    2  NO SE PUDO MEDIR (sin npx, sin red, destino inexistente, corpus ausente)

Un cero de este script significa «se miró y no había»; nunca «no pude mirar». Es la lección de
`red-flags.sh`, que durante meses imprimía «(clean)» apuntando a un directorio que no existía.

ESTADOS. Todas las reglas nacen en `sombra` (cuentan, no bloquean) — `patterns/README.md` §2 y
`rules/refactor-progresivo.md` §4.5. Hoy, por tanto, este gate **no bloquea nada**, y lo dice en
su propia salida en vez de dejar que alguien lo suponga. Promover una regla exige las cinco
condiciones de §4.5, incluida la quinta: la firma un humano, con fecha.

USO:
    python3 .claude/scripts/gate_diseno.py                      # el repo entero, sin el corpus
    python3 .claude/scripts/gate_diseno.py frontend/src --json
    python3 .claude/scripts/gate_diseno.py --sin-impeccable     # offline, DECLARADO en el JSON
    python3 .claude/scripts/gate_diseno.py --self-test          # ¿cazan las reglas su caso?
    python3 .claude/scripts/gate_diseno.py --contra-lienzo .docs/design/lienzo/X.dc.html \
      --tema frontend/src/app.css [--parejas parejas.json]       # ¿el código es el lienzo aprobado?
    python3 .claude/scripts/gate_diseno.py --dom /tmp/dom-pintado  # la página PINTADA, no el .tsx
    python3 .claude/scripts/gate_diseno.py --json | \
      python3 .claude/scripts/pattern_baseline.py check --from - --diff-scope

QUE NO MIDE, dicho por delante:
  · **El movimiento.** Duración, easings, el fotograma a mitad de transición y la pasada sin JS
    son de `scripts/motion_probe.py`, que necesita navegador. Lo que aquí se marca
    `requiere_navegador` se SALTA DECLARÁNDOLO, nunca en silencio.
  · **Si algo es bonito.** Un fichero con cero hallazgos puede ser feísimo. El gate acota lo
    comprobable; el gusto sigue siendo de Vera y de quien paga (`proceso/RANKING.csv` del
    corpus es el recordatorio de que el auto-ranking de un agente no sustituye a ese criterio).
  · **Caracteres invisibles.** Eso ya es `scripts/check_unicode_safety.py` y no se duplica aquí;
    GD-07 mira lo contrario — artefactos VISIBLES del modelo (CJK en un documento latino).
"""
from __future__ import annotations

import argparse
import json
import os
import re
import shutil
import subprocess
import sys
from datetime import date
from pathlib import Path

# GD-14 mide con `contraste.py`, el medidor del template: uno solo, no dos fórmulas que diverjan.
RAIZ_SCRIPTS = Path(__file__).resolve().parent
sys.path.insert(0, str(RAIZ_SCRIPTS))

# ── Impeccable: la versión va PINEADA y grabada en cada JSON ──────────────────────────────────
# Un bump de un detector de terceros cambia lo que cuenta como hallazgo, así que es un bump de
# CALIBRACIÓN: se trata como tal (`rules/qa-loop.md` §4b) y no se acepta a la brava con @latest.
IMPECCABLE_VERSION = "4.6.0"   # el mismo que la skill vendorizada (skills/impeccable)
IMPECCABLE_PKG = f"impeccable@{IMPECCABLE_VERSION}"

# ⚠️ LOS EXIT CODES DE IMPECCABLE ESTAN INVERTIDOS RESPECTO A LOS NUESTROS. Verificado contra
# `impeccable detect --help` (4.1.0) y el README de 4.6.0 (31-10, mismos códigos y `--json`):
#       él:  0 = limpio · 1 = NO pudo escanear · 2 = hay hallazgos
#   nosotros: 0 = limpio · 1 = hay hallazgos    · 2 = NO se pudo medir
# La traducción vive AQUI y en ningún otro sitio del fichero. Si se repartiera, alguien la leería
# al revés y un «no pude escanear» pasaría por «hay hallazgos», o peor, al contrario.
IMP_LIMPIO, IMP_NO_ESCANEO, IMP_HALLAZGOS = 0, 1, 2

RUTA_YAML = "resources/referencias-diseno/anti-patrones.yaml"
BLOQUEAN = {"activo"}          # mismo vocabulario que scripts/pattern_baseline.py
INVERSION_MAX_FICHEROS = 30    # rules/refactor-progresivo.md §4.4

EXT_MIRABLES = {".html", ".htm", ".css", ".scss", ".js", ".jsx", ".ts", ".tsx", ".vue", ".svelte"}
EXCLUIR_SIEMPRE = {".git", "node_modules", "dist", "build", ".next", "__pycache__",
                   ".venv", "venv", "_archive", "coverage", ".cache"}
# El corpus es código VENDORIZADO y ya está medido: barrerlo produce >100 hallazgos que no son
# deuda de nadie. Se mira solo con --incluir-corpus (que es como se valida el propio gate).
EXCLUIR_CORPUS = ("resources/referencias-diseno", ".docs/resources", ".claude/resources")
# Los fixtures del --self-test llevan defectos PLANTADOS a propósito: si entraran en un barrido
# normal, cada corrida del gate reportaría 12 hallazgos que no son deuda de nadie. Se excluyen
# siempre del recorrido de directorios; pasados como fichero explícito (que es como los mira el
# self-test) se siguen leyendo.
EXCLUIR_FIXTURES = (".claude/smoke/diseno", "smoke/diseno")


# ══════════════════════════════════════════════════════════════════════════════════════════════
# Hallazgo — el dialecto de salida NO es nuevo
# ══════════════════════════════════════════════════════════════════════════════════════════════
class Hallazgo:
    """Un hallazgo, en el dialecto que `pattern_baseline.py` ya sabe leer.

    Su `load_findings` acepta `rule`/`id`/`patron_id` y `path`/`file`/`fichero`, más `line`,
    `estado` y `msg`. Emitimos `rule`+`path` para no inventar un tercer dialecto — la regla 1 de
    `patterns/README.md` es que no se inventa un schema más.
    """
    __slots__ = ("rule", "path", "line", "estado", "msg", "severidad", "origen", "snippet")

    def __init__(self, rule, path, line, estado, msg, severidad="P2", origen="propia", snippet=""):
        self.rule, self.path, self.line = rule, path, int(line or 0)
        self.estado, self.msg = estado, msg
        self.severidad, self.origen, self.snippet = severidad, origen, snippet

    def dict(self):
        return {"rule": self.rule, "path": self.path, "line": self.line, "estado": self.estado,
                "msg": self.msg, "severidad": self.severidad, "origen": self.origen,
                "snippet": self.snippet[:200]}


def abortar(razon: str, contexto: str = "") -> None:
    """Sale con 2 y un JSON honesto. NUNCA con 0: no haber mirado no es estar limpio."""
    if ARGS.json:
        json.dump({"version": 1, "generado": date.today().isoformat(),
                   "estado_instrumento": "no_medido", "razon_no_medido": razon,
                   "hallazgos": [], "resumen": {"hallazgos": 0}},
                  sys.stdout, ensure_ascii=False, indent=1)
        print()
    print(f"⛔ gate_diseno.py NO PUDO MEDIR: {razon}", file=sys.stderr)
    if contexto:
        print(f"   {contexto}", file=sys.stderr)
    print("   No se imprime «sin hallazgos»: eso sería una buena noticia inventada.", file=sys.stderr)
    sys.exit(2)


# ══════════════════════════════════════════════════════════════════════════════════════════════
# Parsers mínimos — sin dependencias nuevas
# ══════════════════════════════════════════════════════════════════════════════════════════════
_AT_OPACOS = ("@keyframes", "@-webkit-keyframes", "@-moz-keyframes", "@font-face",
              "@page", "@counter-style", "@property")


def bloques_css(texto: str, es_html: bool, suf: str = ""):
    """Devuelve [(css, linea_inicial)]. En HTML, el contenido de cada <style>.

    Un fichero que no es HTML solo es CSS si su extensión lo dice. Sin esta comprobación, un
    .js entero entraba por el parser de CSS y cada `const x = ...` parecía una declaración rota:
    131 falsos positivos de GD-10 sobre `dale-marketing-v4/script.js`. Salió de correr el gate
    contra el corpus entero, no de leer el código.
    """
    if not es_html:
        return [(texto, 1)] if suf in (".css", ".scss", ".sass", ".less") else []
    out = []
    for m in re.finditer(r"<style\b[^>]*>(.*?)</style>", texto, re.S | re.I):
        out.append((m.group(1), texto.count("\n", 0, m.start(1)) + 1))
    return out


def bloques_js(texto: str, es_html: bool):
    """Devuelve [(js, linea_inicial)]. En HTML, el contenido de cada <script> sin src."""
    if not es_html:
        return [(texto, 1)]
    out = []
    for m in re.finditer(r"<script\b([^>]*)>(.*?)</script>", texto, re.S | re.I):
        if re.search(r"\bsrc\s*=", m.group(1), re.I):
            continue
        out.append((m.group(2), texto.count("\n", 0, m.start(2)) + 1))
    return out


def reglas_css(css: str, linea0: int = 1):
    """Itera (selector, bloque, linea, [at-rules abiertas]) sobre un CSS plano.

    Salta el CONTENIDO de @keyframes y @font-face (sus '0%{...}' no son selectores) y desciende
    dentro de @media/@supports/@layer, que sí contienen reglas. No entiende anidamiento tipo
    SCSS: en un .scss anidado leerá de más, y por eso los hallazgos de esta familia llevan
    siempre el texto que los disparó (`snippet`) para que se puedan contrastar a ojo.
    """
    i, n, linea = 0, len(css), linea0
    buf, hay, sel_linea = [], False, linea0
    ats: list[str] = []
    while i < n:
        c = css[i]
        if c == "\n":
            linea += 1; buf.append(c); i += 1; continue
        if c == "/" and css.startswith("/*", i):
            j = css.find("*/", i + 2)
            j = n if j < 0 else j + 2
            linea += css.count("\n", i, j); i = j; continue
        if c == "{":
            sel = "".join(buf).strip()
            buf, hay = [], False
            if sel.startswith("@"):
                cabeza = sel.split(None, 1)[0].lower()
                if cabeza in _AT_OPACOS:
                    j, prof = i + 1, 1
                    while j < n and prof:
                        if css[j] == "{":
                            prof += 1
                        elif css[j] == "}":
                            prof -= 1
                        j += 1
                    linea += css.count("\n", i, j); i = j; continue
                ats.append(sel); i += 1; continue
            j, prof = i + 1, 1
            while j < n and prof:
                if css[j] == "{":
                    prof += 1
                elif css[j] == "}":
                    prof -= 1
                j += 1
            yield sel, css[i + 1:j - 1], sel_linea, list(ats)
            linea += css.count("\n", i, j); i = j; continue
        if c == "}":
            if ats:
                ats.pop()
            buf, hay = [], False; i += 1; continue
        if not hay and not c.isspace():
            hay, sel_linea = True, linea
        buf.append(c); i += 1


def declaraciones(bloque: str, linea0: int):
    """Itera (propiedad, valor, linea, crudo). La propiedad vacía = fragmento SIN ':' (GD-10).

    Los comentarios se borran ANTES (conservando los saltos de línea, para no descuadrar los
    números). Sin eso, `html{scroll-behavior:auto; /* Lenis handles smooth */}` producía un
    fragmento sin ':' y GD-10 lo denunciaba como declaración rota — un falso positivo que
    encontró el propio gate al correrlo contra el corpus, no una lectura del código.
    """
    bloque = re.sub(r"/\*.*?\*/", lambda m: re.sub(r"[^\n]", " ", m.group(0)), bloque, flags=re.S)
    linea, trozo, ini = linea0, [], linea0
    for ch in bloque + ";":
        if ch == ";":
            crudo = "".join(trozo).strip()
            if crudo:
                if ":" in crudo:
                    p, _, v = crudo.partition(":")
                    yield p.strip().lower(), v.strip(), ini, crudo
                else:
                    yield "", crudo, ini, crudo
            trozo, ini = [], linea
        else:
            trozo.append(ch)
            if ch == "\n":
                linea += 1
                if not "".join(trozo).strip():
                    ini = linea


def args_llamada(texto: str, nombre: str):
    """Itera (args_crudos, linea) de cada `nombre(...)`, casando paréntesis.

    Hace falta porque el caso medido del corpus NO cabe en una regex: el
    `setTimeout(function(){...}, 3200)` de `bien/yessmassage-v7.html:4636` reparte la llamada en
    ocho líneas, así que el delay no está donde una regex de una línea lo buscaría.
    """
    for m in re.finditer(r"\b" + re.escape(nombre) + r"\s*\(", texto):
        i, prof, n = m.end(), 1, len(texto)
        while i < n and prof:
            if texto[i] == "(":
                prof += 1
            elif texto[i] == ")":
                prof -= 1
            i += 1
        yield texto[m.end():i - 1], texto.count("\n", 0, m.start()) + 1


def corta_nivel_superior(s: str) -> list[str]:
    """Parte por comas de NIVEL SUPERIOR (ignora las de dentro de (), [], {} y cadenas)."""
    partes, prof, act, comilla = [], 0, [], ""
    for ch in s:
        if comilla:
            act.append(ch)
            if ch == comilla:
                comilla = ""
            continue
        if ch in "\"'`":
            comilla = ch; act.append(ch); continue
        if ch in "([{":
            prof += 1
        elif ch in ")]}":
            prof -= 1
        if ch == "," and prof == 0:
            partes.append("".join(act)); act = []; continue
        act.append(ch)
    partes.append("".join(act))
    return partes


def sin_comentarios_js(js: str) -> str:
    """Borra comentarios conservando los saltos de línea (los números no se descuadran).

    Existe porque el fixture de GD-01 destapó el fallo: su comentario decía «initReveal se DEFINE
    y no se llama nunca», así que el nombre aparecía DOS veces y la regla —que busca funciones con
    una sola aparición— se callaba. En un fichero real pasa igual con un «// TODO: llamar a
    initGSAP()»: la regla se apagaría justo donde más falta hace.

    Límite declarado: el `//` dentro de una cadena se respeta solo si va tras `:` (las URL). Un
    `const x = "a // b"` perdería el resto de la línea. Se asume: esto cuenta apariciones de un
    identificador, no compila JavaScript.
    """
    # Se sustituye por ESPACIOS, no por nada: la cadena tiene que conservar su longitud además de
    # sus saltos de línea. Con el borrado a secas, los desplazamientos de las coincidencias se
    # calculaban sobre el texto acortado y se usaban contra el original — `initGSAP()` salía en
    # la :1429 cuando está en la :1441. Doce líneas de error en una cita que el informe presenta
    # como exacta: un número creíble y falso es peor que no dar el número.
    js = re.sub(r"/\*.*?\*/", lambda m: re.sub(r"[^\n]", " ", m.group(0)), js, flags=re.S)
    return re.sub(r"(?<!:)//[^\n]*", lambda m: " " * len(m.group(0)), js)


def texto_visible(html: str) -> list[tuple[int, str]]:
    """[(linea, texto)] del contenido visible: fuera de <script>, <style> y comentarios."""
    limpio = re.sub(r"<(script|style)\b[^>]*>.*?</\1>",
                    lambda m: re.sub(r"[^\n]", " ", m.group(0)), html, flags=re.S | re.I)
    limpio = re.sub(r"<!--.*?-->", lambda m: re.sub(r"[^\n]", " ", m.group(0)), limpio, flags=re.S)
    limpio = re.sub(r"<[^>]+>", " ", limpio)
    return [(i + 1, l.strip()) for i, l in enumerate(limpio.split("\n")) if l.strip()]


# ══════════════════════════════════════════════════════════════════════════════════════════════
# GD-04 · color: familia de tono a partir del valor
# ══════════════════════════════════════════════════════════════════════════════════════════════
FAMILIAS = {
    "rojo": (345, 10), "red": (345, 10), "rose": (330, 355), "rosa": (330, 355),
    "pink": (300, 345), "naranja": (15, 45), "orange": (15, 45), "coral": (5, 25),
    "amarillo": (45, 70), "yellow": (45, 70), "gold": (38, 58), "dorado": (38, 58),
    "amber": (30, 50), "lima": (70, 90), "lime": (70, 90), "verde": (80, 165),
    "green": (80, 165), "mint": (140, 175), "menta": (140, 175), "oliva": (60, 95),
    "olive": (60, 95), "teal": (160, 195), "turquesa": (160, 195), "turquoise": (160, 195),
    "cian": (175, 200), "cyan": (175, 200), "azul": (195, 250), "blue": (195, 250),
    "navy": (200, 250), "indigo": (240, 270), "violeta": (255, 285), "violet": (255, 285),
    "purple": (265, 300), "morado": (265, 300), "magenta": (295, 325),
    "marron": (10, 40), "brown": (10, 40), "terracotta": (5, 35), "beige": (20, 60),
    "crema": (20, 60), "cream": (20, 60), "sand": (20, 55), "arena": (20, 55),
}
ACROMATICOS = {"negro", "black", "blanco", "white", "gris", "grey", "gray", "plata", "silver"}


def a_rgb(valor: str):
    v = valor.strip().lower()
    m = re.fullmatch(r"#([0-9a-f]{3})", v)
    if m:
        return tuple(int(c * 2, 16) for c in m.group(1))
    m = re.fullmatch(r"#([0-9a-f]{6})", v)
    if m:
        h = m.group(1)
        return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4))
    m = re.match(r"rgba?\(\s*([0-9.]+)[\s,]+([0-9.]+)[\s,]+([0-9.]+)", v)
    if m:
        return tuple(int(float(g)) for g in m.groups())
    return None


def hsl(rgb):
    r, g, b = (c / 255 for c in rgb)
    mx, mn = max(r, g, b), min(r, g, b)
    l, d = (mx + mn) / 2, mx - mn
    if d == 0:
        return 0.0, 0.0, l
    s = d / (2 - mx - mn) if l > 0.5 else d / (mx + mn)
    if mx == r:
        h = ((g - b) / d) % 6
    elif mx == g:
        h = (b - r) / d + 2
    else:
        h = (r - g) / d + 4
    return h * 60, s, l


# Un nombre de color no delimita una banda exacta: «púrpura», «violeta» y «magenta» se pisan, y
# nadie se pone de acuerdo en dónde acaba cada uno. Con las bandas a pelo salían falsos positivos
# a 3° del borde (`--purple-dim: #7c3aed`, 262°, y `--magenta: #e040fb`, 291°), que son
# exactamente los colores que dicen ser. La regla NO es «¿cae en la banda?» sino «¿está tan lejos
# que es OTRO color?», y por eso hay 30° de margen: `--rose: #5a922d` está a 78° del borde.
TOLERANCIA_TONO = 30.0

# Y una segunda guarda, de CROMA. La saturación HSL engaña en los extremos de luminosidad:
# `--gray-50: #F0F4F8` sale con 36 % de saturación y es, a la vista, gris — sus canales se separan
# 8 puntos sobre 255. Con solo la saturación, las escalas de grises TEÑIDOS (el pan de cada día de
# un design system) salían marcadas como nombres que mienten: 3 falsos positivos en
# `bien/elevaiti-v53.html`. Por debajo de este umbral no se afirma nada: un color casi acromático
# no tiene un tono que se pueda nombrar, así que tampoco se le puede acusar de mentir.
CROMA_MINIMO = 40          # max(r,g,b) - min(r,g,b), sobre 255


def dist_tono(h: float, rango) -> float:
    """Grados que separan `h` de la banda (0 si está dentro). El círculo se cierra en 360."""
    lo, hi = rango
    dentro = (lo <= h <= hi) if lo <= hi else (h >= lo or h <= hi)
    if dentro:
        return 0.0
    d = lambda a, b: min(abs(a - b), 360 - abs(a - b))          # noqa: E731
    return min(d(h, lo), d(h, hi))


def tono_en(h: float, rango) -> bool:
    return dist_tono(h, rango) <= TOLERANCIA_TONO


# ══════════════════════════════════════════════════════════════════════════════════════════════
# Las 15 reglas. NO se inventan aquí: el enunciado, la severidad y el sitio donde el defecto
# ocurrió de verdad viven en `anti-patrones.yaml`. Esto es su implementación, y cada una lleva
# encima el caso MEDIDO que tiene que cazar — si una regla no caza su propio `visto_en`, está
# rota, que es exactamente lo que le pasó a R1 de `red-flags.sh` durante meses.
# ══════════════════════════════════════════════════════════════════════════════════════════════
CHECKS: dict[str, object] = {}
EN_VIVO: dict[str, str] = {}       # mitades que EXIGEN navegador → se saltan DECLARÁNDOLO


def regla(rid, en_vivo=""):
    def deco(fn):
        CHECKS[rid] = fn
        if en_vivo:
            EN_VIVO[rid] = en_vivo
        return fn
    return deco


class Ctx:
    """Todo lo que una regla necesita de un fichero, parseado UNA vez."""
    def __init__(self, path, texto, vars_def, reduced_vecino, focusvis_vecino):
        self.path, self.texto = path, texto
        self.es_html = Path(path).suffix.lower() in (".html", ".htm")
        suf = Path(path).suffix.lower()
        self.css = bloques_css(texto, self.es_html, suf)
        # Un HTML con su <style> dentro y sin hoja local enlazada ES el diseño entero: no hereda
        # nada de sus vecinos de carpeta. Uno que enlaza un .css es una PIEZA de algo mayor y sí.
        # Sin esta distinción, las 9 referencias independientes de `bien/` se tapaban entre ellas
        # y GD-12 marcaba 2 ficheros donde la medición dice 6.
        self.autocontenido = bool(
            self.es_html and re.search(r"<style\b", texto, re.I)
            and not re.search(r"<link[^>]+stylesheet[^>]*href\s*=\s*[\"\']()(?!https?:)", texto, re.I))
        self.js = bloques_js(texto, self.es_html) if self.es_html or \
            Path(path).suffix.lower() in (".js", ".jsx", ".ts", ".tsx", ".vue", ".svelte") else []
        self.visible = texto_visible(texto) if self.es_html else \
            [(i + 1, l.strip()) for i, l in enumerate(texto.split("\n")) if l.strip()]
        self.vars_def = vars_def                  # todas las de ESTE barrido (multi-fichero)
        self.reduced_vecino = reduced_vecino      # ¿algún hermano de carpeta declara reduced-motion?
        self.focusvis_vecino = focusvis_vecino

    def css_todo(self):
        return "\n".join(c for c, _ in self.css)

    def js_todo(self):
        return "\n".join(j for j, _ in self.js)

    def reglas(self):
        for css, l0 in self.css:
            yield from reglas_css(css, l0)


# ── GD-01 ─────────────────────────────────────────────────────────────────────────────────────
# Caso medido: mal/attomo-digital.html — `async function initGSAP()` en :1441 con UNA SOLA
# aparición en todo el fichero (definida y jamás llamada) + `.reveal{opacity:0}` en :1006 sin
# guarda. La página está DESPLEGADA así y no se ve nada.
# Contraejemplo: bien/elevaiti-v53.html:92-94 — `body.js-ready .fade-up{opacity:0}`. Ahí la
# clase `js-ready` la pone el JS, así que SIN JS la regla nunca aplica y el texto se ve.
RE_INIT = re.compile(
    r"\b(?:async\s+)?function\s+((?:init|setup|start|boot)[A-Za-z0-9_]*)\s*\("
    r"|\b(?:const|let|var)\s+((?:init|setup|start|boot)[A-Za-z0-9_]*)\s*=\s*(?:async\s*)?(?:function|\(|[A-Za-z_])")
GUARDAS_JS = ("js-ready", "js-enabled", "js-on", "has-js", "is-loaded", "loaded", "js ", ".js.", "no-js")


@regla("GD-01", en_vivo="cargar con java_script_enabled=False y medir el ratio de texto visible "
                       "→ scripts/motion_probe.py")
def gd01(c: Ctx):
    # Sin comentarios para CONTAR: una mención en un comentario no es una llamada (ver
    # `sin_comentarios_js`). Y el recuento va sobre TODOS los <script>, porque la llamada puede
    # vivir en uno distinto del de la definición.
    js_todo = sin_comentarios_js(c.js_todo())
    muertas = []
    for js, l0 in c.js:            # para la LÍNEA: cada <script> tiene su propio desplazamiento
        for m in RE_INIT.finditer(sin_comentarios_js(js)):
            nombre = m.group(1) or m.group(2)
            if len(re.findall(r"\b" + re.escape(nombre) + r"\b", js_todo)) == 1:
                muertas.append((nombre, l0 + js.count("\n", 0, m.start())))
    if not muertas:
        return []
    # Ojo con esta extracción: la primera versión pedía un espacio o comilla DELANTE del nombre,
    # así que se comía la primera clase de la lista. En attomo daba igual —hay cientos y alguna
    # casaba—, pero en el fixture de una sola clase (`class="reveal"`) la regla no cazaba su
    # propio caso. Lo destapó el --self-test, no la corrida contra el corpus: es justo la mitad
    # que un recall alto sobre material real no mide.
    clases_marcado = {c2 for grupo in re.findall(r"class\s*=\s*[\"']([^\"']+)[\"']", c.texto)
                      for c2 in grupo.split() if c2}
    ocultas = []
    for sel, bloque, linea, _ats in c.reglas():
        if not re.search(r"opacity\s*:\s*0(?!\.)", bloque):
            continue
        if any(g in sel.lower() for g in GUARDAS_JS):
            continue                                   # guarda de mejora progresiva: correcto
        clases = set(re.findall(r"\.([A-Za-z0-9_-]+)", sel))
        if c.es_html and clases and not (clases & clases_marcado):
            continue                                   # CSS muerto: no oculta nada real
        ocultas.append((sel.strip()[:60], linea))
    if not ocultas:
        return []
    n, ln = muertas[0]
    # De todos los `opacity:0` sin guarda, se cita el que de verdad es CONTENIDO. Medido: en
    # attomo el primero por orden es `.hero-orb` (un adorno borroso, opacity:0 a propósito) y el
    # que importa es `.reveal` en :1006. Citar el adorno haría dudar de un hallazgo correcto.
    # Por PRIORIDAD, no por orden de aparición: `.reveal` antes que `.hero-scroll`, que también
    # casaba con «scroll» y no es contenido — sale de correrlo, no de leerlo.
    prior = (r"reveal", r"fade|slide|appear|animate|in-?view", r"scroll|section|card|text")
    sel, sl = next((o for rx in prior for o in ocultas if re.search(rx, o[0], re.I)), ocultas[0])
    return [Hallazgo("GD-01", c.path, sl, "", severidad="P0", snippet=sel,
                     msg=(f"contenido invisible sin JS: `{n}()` se define en :{ln} y NO SE LLAMA "
                          f"NUNCA (1 sola aparición), y `{sel}` está en opacity:0 sin guarda "
                          f"tipo `body.js-ready` ({len(ocultas)} selector/es así). "
                          f"Contraejemplo: resources/referencias-diseno/bien/elevaiti-v53.html:92-94"))]


# ── GD-02 ─────────────────────────────────────────────────────────────────────────────────────
# Dos mitades, las dos medidas y las dos con forma distinta:
#   a) bien/yessmassage-v7.html:4636-4643 → `setTimeout(function(){loader...}, 3200)`. La llamada
#      ocupa OCHO líneas, así que el delay no cabe en una regex de una línea: hay que casar
#      paréntesis (por eso existe `args_llamada`).
#   b) bien/dale-marketing-v4/script.js:33-44 → barra de progreso FALSA: el porcentaje sale de
#      `Math.random()`, no de ningún evento real. Una barra que se inventa su avance miente.
RE_LOADER = re.compile(r"loader|preloader|splash|loading|overlay|intro-screen|pantalla-carga", re.I)
RE_QUITAR = re.compile(r"classList\.(add|remove)|style\.(display|opacity)|remove\(\)|hidden|fadeOut|gsap\.to", re.I)
RE_BARRA_FALSA = re.compile(r"\b(progress|progreso|carga|loading|percent|porcentaje|pct)\w*\s*="
                            r"[^;\n]{0,120}Math\.random", re.I)


@regla("GD-02", en_vivo="tiempo hasta el primer texto legible")
def gd02(c: Ctx):
    out = []
    for js, l0 in c.js:
        for crudo, ln in args_llamada(js, "setTimeout"):
            partes = corta_nivel_superior(crudo)
            if len(partes) < 2:
                continue
            m = re.search(r"\d+", partes[-1])
            if not m:
                continue
            ms = int(m.group())
            cb = partes[0]
            if ms >= 1000 and RE_LOADER.search(cb) and RE_QUITAR.search(cb):
                out.append(Hallazgo("GD-02", c.path, l0 + ln - 1, "", severidad="P1",
                                    snippet=cb.strip()[:80],
                                    msg=f"loader forzado: el contenido espera {ms/1000:.1f} s a un "
                                        f"setTimeout, no a que algo termine de cargar"))
        for m in RE_BARRA_FALSA.finditer(js):
            out.append(Hallazgo("GD-02", c.path, l0 + js.count("\n", 0, m.start()), "",
                                severidad="P1", snippet=m.group(0)[:80],
                                msg="barra de progreso FALSA: el porcentaje sale de Math.random(), "
                                    "no de ningún evento real de carga"))
    return out


# ── GD-03 ─────────────────────────────────────────────────────────────────────────────────────
# DENSIDAD, nunca presencia: la yaml ya avisa de que una regla por presencia marcaría medio repo
# (regla de inversión, rules/refactor-progresivo.md §4.4).
# Medido sobre los 10 ficheros del corpus (2026-09-18), !important / declaraciones:
#   yessmassage-v7 1,6 %  ·  el resto, TODOS por debajo de 0,71 % (styles.css 0,70 · kalinayoga-v6
#   0,69 · elevaiti-v53 0,70 · attomo 0,52 · consultorpro 0,19 · elevaiti-v2 y kalinayoga-v4 0,0).
# Hay un salto limpio, así que el umbral va en el hueco (1,0 %) y no pegado a un extremo. El
# mínimo absoluto de 10 evita que un fichero de 20 líneas con 2 `!important` dispare.
UMBRAL_IMPORTANT, MINIMO_IMPORTANT = 0.010, 10
RE_DECL = re.compile(r"[-a-zA-Z]+\s*:\s*[^;{}]+[;}]")


@regla("GD-03")
def gd03(c: Ctx):
    css = c.css_todo()
    if not css.strip():
        return []
    n_imp = len(re.findall(r"!\s*important", css, re.I))
    n_decl = len(RE_DECL.findall(css)) or 1
    ratio = n_imp / n_decl
    if n_imp < MINIMO_IMPORTANT or ratio < UMBRAL_IMPORTANT:
        return []
    prim = re.search(r"!\s*important", css, re.I)
    linea = c.css[0][1] + css.count("\n", 0, prim.start()) if prim else 0
    return [Hallazgo("GD-03", c.path, linea, "", severidad="P2",
                     msg=f"capa de parches: {n_imp} !important sobre {n_decl} declaraciones "
                         f"({ratio*100:.1f} %, umbral {UMBRAL_IMPORTANT*100:.0f} %). Un ratio así "
                         f"significa que la cascada ya no se controla, se sobrescribe")]


# ── GD-04 ─────────────────────────────────────────────────────────────────────────────────────
# Caso medido: bien/yessmassage-v7.html:28 `--rose: #5a922d` (tono 93°, un VERDE) y :37
# `--bg: var(--beige)` con `--beige:` sin definir en ninguna parte (0 coincidencias).
# Los `var(--x)` sin definir se contrastan contra las variables de TODO el barrido, no solo las
# del fichero: en un diseño multi-fichero (dale: index.html + styles.css) los tokens se declaran
# en uno y se usan en otro, y mirar fichero a fichero inventaría hallazgos.
RE_VARDEF = re.compile(r"(--[A-Za-z0-9_-]+)\s*:")
RE_VARUSO = re.compile(r"var\(\s*(--[A-Za-z0-9_-]+)")


@regla("GD-04")
def gd04(c: Ctx):
    out = []
    for css, l0 in c.css:
        for m in re.finditer(r"(--[A-Za-z0-9_-]+)\s*:\s*([^;}]+)", css):
            nombre, valor = m.group(1), m.group(2).strip()
            linea = l0 + css.count("\n", 0, m.start())
            palabras = [p for p in re.split(r"[-_]+", nombre.lstrip("-").lower()) if p]
            rgb = a_rgb(valor)
            if not rgb:
                continue
            h, s, lum = hsl(rgb)
            if max(rgb) - min(rgb) < CROMA_MINIMO:
                continue
            for p in palabras:
                if p in FAMILIAS and s >= 0.15 and not tono_en(h, FAMILIAS[p]):
                    out.append(Hallazgo("GD-04", c.path, linea, "", severidad="P1",
                                        snippet=f"{nombre}: {valor}",
                                        msg=f"el nombre del token MIENTE sobre su valor: `{nombre}` "
                                            f"dice «{p}» y {valor} tiene tono {h:.0f}° "
                                            f"(«{p}» vive en {FAMILIAS[p][0]}-{FAMILIAS[p][1]}°, "
                                            f"a {dist_tono(h, FAMILIAS[p]):.0f}° de ahí)"))
                    break
                if p in ACROMATICOS and s >= 0.30:
                    out.append(Hallazgo("GD-04", c.path, linea, "", severidad="P1",
                                        snippet=f"{nombre}: {valor}",
                                        msg=f"`{nombre}` dice «{p}» (acromático) y {valor} tiene "
                                            f"saturación {s*100:.0f} %"))
                    break
        # Una variable sin definir se usa muchas veces (medido: `--white-50` aparece 12 veces en
        # `bien/elevaiti-v5.html`). El defecto es UNO por variable, no doce: se colapsa y se dice
        # cuántas veces, que es lo que de verdad ayuda a decidir si se borra o se define.
        huerfanas: dict[str, list[int]] = {}
        for m in RE_VARUSO.finditer(css):
            v = m.group(1)
            if v not in c.vars_def:
                huerfanas.setdefault(v, []).append(l0 + css.count("\n", 0, m.start()))
        for v, lineas in huerfanas.items():
            out.append(Hallazgo("GD-04", c.path, lineas[0], "", severidad="P1", snippet=f"var({v})",
                                msg=f"`{v}` se usa {len(lineas)} vez/veces y NO SE DEFINE en ningún "
                                    f"fichero del barrido: la propiedad se queda sin valor y el "
                                    f"fallo es MUDO — no hay error, simplemente no se aplica"))
    return out


# ── GD-05 ─────────────────────────────────────────────────────────────────────────────────────
# Medido: 5 de los 10 ficheros del corpus animan sin declarar reduced-motion (elevaiti-v2,
# elevaiti-v53, elevaiti-v7, kalinayoga-v6 y attomo). El contraejemplo es dale-marketing-v4, que
# lo declara en CSS **y** en JS (styles.css:1423 + script.js:11).
# Se suprime si un HERMANO DE CARPETA lo declara: un diseño repartido en index.html + styles.css
# es una sola pieza, y marcar el HTML por lo que dice su CSS de al lado sería inventar deuda.
@regla("GD-05")
def gd05(c: Ctx):
    css = c.css_todo()
    if not re.search(r"@keyframes|transition\s*:|animation\s*:", css, re.I):
        return []
    if "prefers-reduced-motion" in c.texto or (c.reduced_vecino and not c.autocontenido):
        return []
    m = re.search(r"@keyframes|transition\s*:|animation\s*:", css, re.I)
    return [Hallazgo("GD-05", c.path, c.css[0][1] + css.count("\n", 0, m.start()), "",
                     severidad="P1", snippet=m.group(0),
                     msg="hay animación y CERO bloques prefers-reduced-motion. "
                         "Contraejemplo con las dos capas (CSS y JS): "
                         "resources/referencias-diseno/bien/dale-marketing-v4/styles.css:1423 + script.js:11")]


# ── GD-06 ─────────────────────────────────────────────────────────────────────────────────────
# Caso medido: mal/attomo-digital.html:48 (en `body`) y :315 (en un enlace). Los dos se reportan:
# quitarle el cursor al documento entero es peor, pero quitárselo a un elemento PULSABLE es la
# misma avería — quien no ve el puntero no sabe dónde está.
@regla("GD-06")
def gd06(c: Ctx):
    globales, locales = [], []
    for sel, bloque, linea, _ in c.reglas():
        if not re.search(r"cursor\s*:\s*none", bloque, re.I):
            continue
        (globales if re.search(r"(^|[\s,>+~])(body|html|\*)([\s,>+~:]|$)", sel.strip(), re.I)
         else locales).append((sel.strip()[:40], linea))
    out = [Hallazgo("GD-06", c.path, ln, "", severidad="P1", snippet=sel,
                    msg=f"cursor:none GLOBAL en `{sel}`: el puntero desaparece en toda la página")
           for sel, ln in globales]
    # Los locales se COLAPSAN en uno. Attomo tiene siete y listarlos uno a uno ahoga al hallazgo
    # global, que es el grave: un informe que repite la misma frase siete veces se deja de leer.
    if locales:
        sel, ln = locales[0]
        out.append(Hallazgo("GD-06", c.path, ln, "", severidad="P1", snippet=sel,
                            msg=f"cursor:none en {len(locales)} selector(es) NO globales "
                                f"(el primero, `{sel}`): en esos elementos no se ve el puntero"))
    return out


# ── GD-07 ─────────────────────────────────────────────────────────────────────────────────────
# Absorbe R3 (AI-slop) y R10 (TODO/lorem) de `agents/shared/red-flags.sh`, y añade la mitad que
# allí no estaba: artefactos VISIBLES del modelo. El caso citado —«NexusTech重构ó»— es escritura
# china dentro de una palabra española. No se solapa con `scripts/check_unicode_safety.py`, que
# caza lo INVISIBLE (ancho cero, bidi); esto caza lo que se ve y nadie escribió a propósito.
RE_SLOP = re.compile(r"revolucionar|revolutionary|next-level|game-changing|cutting-edge|"
                     r"transform.{0,12}business|potencia tu|transforma tu|seamlessly|effortlessly|"
                     r"unlock the power|elevate your", re.I)
# ⚠️ `PLACEHOLDER` va en MAYÚSCULAS y sin re.I a propósito. R10 de `red-flags.sh` lo busca sin
# distinguir mayúsculas y por eso marca `::placeholder` (pseudo-elemento CSS) y
# `placeholder="tu@email.com"` (atributo HTML), que son correctos los dos. Lo encontró este gate
# al correrse contra el corpus: dos falsos positivos en attomo, :872 y :1295. Aquí NO se hereda.
# ⚠️ `TODO` solo cuenta como MARCADOR: `TODO:`, `TODO(quien)` o al empezar un comentario. En
# castellano «TODO» en mayúsculas es una palabra («borde de TODO campo de formulario»): fitapp lo
# midió como falso positivo en su hoja de estilos, y el `bueno.html` de GD-07 lo lleva de trampa.
RE_RELLENO = re.compile(r"\bTODO\s*:|\bTODO\([^)\n]{0,40}\)|(?://|#|/\*|<!--)\s*TODO\b|"
                        r"^\s*\*\s*TODO\b|\bFIXME\b|\bXXX\b|(?i:lorem ipsum)|"
                        r"(?<![:\w])PLACEHOLDER(?![\w=])")
RE_CJK = re.compile(r"[぀-ヿ㐀-䶿一-鿿가-힯Ѐ-ӿ]")


@regla("GD-07")
def gd07(c: Ctx):
    out = []
    for linea, txt in c.visible:
        for rx, sev, que in ((RE_SLOP, "P1", "copy de relleno («AI-slop»): frase genérica que no "
                                             "dice nada del producto"),
                             (RE_CJK, "P1", "ARTEFACTO DEL MODELO: escritura no latina suelta en "
                                            "un texto latino")):
            m = rx.search(txt)
            if m:
                out.append(Hallazgo("GD-07", c.path, linea, "", severidad=sev,
                                    snippet=txt[:90], msg=f"{que} — «{m.group(0)}»"))
    for i, l in enumerate(c.texto.split("\n"), 1):
        m = RE_RELLENO.search(l)
        if m:
            out.append(Hallazgo("GD-07", c.path, i, "", severidad="P1", snippet=l.strip()[:90],
                                msg=f"marcador de trabajo sin terminar: «{m.group(0)}»"))
    return out


# ── GD-08 ─────────────────────────────────────────────────────────────────────────────────────
# Caso medido: bien/consultorpro.html:1209 y :2046 («Solo 7 plazas»). El copy de escasez NO es un
# defecto por sí solo — es aceptable SI ES VERDAD. Lo que lo convierte en engaño es que el número
# lo pinte el navegador: entonces se reinicia en cada carga y no cuenta nada. Esa confirmación
# pide DOS cargas en vivo y se declara como no hecha (§requiere_navegador).
RE_ESCASEZ = re.compile(r"solo\s+\d+\s+(plazas|huecos|unidades|sitios)|quedan\s+\d+|"
                        r"plazas disponibles|oferta expira|expires? (in|today)|last chance|"
                        r"última oportunidad|limited time|¡?apúrate!?|solo hoy", re.I)
RE_CONTADOR_JS = re.compile(r"(plazas|spots|seats|quedan|remaining|stock|countdown|cuenta_?atras)"
                            r"[^;\n]{0,80}(Math\.random|Date\.now|new Date|setInterval|--|\+\+)", re.I)
# Las palabras GENÉRICAS de cuenta atrás también las usa un temporizador honrado (el descanso entre
# series de fitapp, medido como falso positivo). Solo cuentan si el
# fichero habla de VENDER; las de inventario (plazas, spots, seats, stock) cuentan siempre.
RE_GENERIC_COUNTER = re.compile(r"quedan|remaining|countdown|cuenta_?atras", re.I)
RE_SALES = re.compile(r"plazas|spots|seats|stock|oferta|offer|descuento|discount|precio|price|"
                      r"comprar|buy now|carrito|\bcart\b|checkout|unidades", re.I)
# Un test describe la conducta con palabras («solo hoy o ayer»): no es copy que vea nadie.
RE_TEST_FILE = re.compile(r"(\.(test|spec)\.[cm]?[jt]sx?$)|(^|/)__tests__/")


@regla("GD-08", en_vivo="dos cargas comparando el valor del contador (si se reinicia, es falso)")
def gd08(c: Ctx):
    out = []
    if RE_TEST_FILE.search(c.path):
        return out
    sells = any(RE_SALES.search(t) for _, t in c.visible)
    for linea, txt in c.visible:
        m = RE_ESCASEZ.search(txt)
        if m:
            out.append(Hallazgo("GD-08", c.path, linea, "", severidad="P0", snippet=txt[:90],
                                msg=f"escasez declarada («{m.group(0)}»): solo es aceptable SI ES "
                                    f"VERDAD. Confirmación viva pendiente (dos cargas)"))
    for js, l0 in c.js:
      for m in RE_CONTADOR_JS.finditer(js):
        if RE_GENERIC_COUNTER.fullmatch(m.group(1)) and not sells:
            continue
        out.append(Hallazgo("GD-08", c.path, l0 + js.count("\n", 0, m.start()), "", severidad="P0",
                            snippet=m.group(0)[:90],
                            msg="el contador de escasez lo calcula el NAVEGADOR: se reinicia en cada "
                                "carga, así que no cuenta nada real"))
    return out


# ── GD-09 ─────────────────────────────────────────────────────────────────────────────────────
# Absorbe R6 de red-flags.sh, que solo miraba .jsx/.tsx. Caso medido: bien/elevaiti-v53.html usa
# emojis como iconos, y el propio documento de marca del cliente lo prohíbe
# (proceso/elevaiti-BRANDING-VISUAL.md).
RE_EMOJI = re.compile("[\U0001F300-\U0001FAFF☀-➿⬀-⯿️\U0001F1E6-\U0001F1FF]")


@regla("GD-09")
def gd09(c: Ctx):
    # Uno por fichero. Medido: sin colapsar, el corpus produce 247 hallazgos de esta sola regla y
    # ahogan a los P0. Un informe que repite 247 veces la misma frase se deja de leer entero, que
    # es el modo de fallo que `patterns/README.md` §2 llama morir de ruido.
    encontrados = [(linea, RE_EMOJI.findall(txt)) for linea, txt in c.visible if RE_EMOJI.search(txt)]
    if not encontrados:
        return []
    linea = encontrados[0][0]
    vistos, todos = [], [e for _, es in encontrados for e in es]
    for e in todos:
        if e not in vistos:
            vistos.append(e)
    return [Hallazgo("GD-09", c.path, linea, "", severidad="P2", snippet="".join(vistos[:12]),
                     msg=f"{len(todos)} emoji(s) como icono en {len(encontrados)} línea(s), desde "
                         f"la :{linea} ({''.join(vistos[:8])}): un emoji lo dibuja el sistema "
                         f"operativo, así que cambia de forma en cada máquina y NO es de la marca")]


# ── GD-10 ─────────────────────────────────────────────────────────────────────────────────────
# Caso citado: `font-family:'Space Grotesk',system-ui;sans-serif;`. El ';' CORTA la declaración,
# así que `sans-serif` queda suelto: el navegador lo descarta en silencio y la pila de respaldo
# desaparece sin que nada falle. Determinista y con falso positivo cero — la yaml la marca como
# la mejor candidata a ser la primera en promocionar.
GENERICAS = {"sans-serif", "serif", "monospace", "cursive", "fantasy", "system-ui", "ui-sans-serif",
             "ui-serif", "ui-monospace", "ui-rounded", "math", "emoji", "fangsong"}


@regla("GD-10")
def gd10(c: Ctx):
    out = []
    for _sel, bloque, linea, _ in c.reglas():
        previa = ""
        for prop, valor, ln, crudo in declaraciones(bloque, linea):
            if not prop:
                limpio = valor.strip().strip("'\"").lower()
                if previa == "font-family" or limpio in GENERICAS or \
                        all(t.strip().strip("'\"").lower() in GENERICAS or " " in t
                            for t in valor.split(",")) and limpio:
                    out.append(Hallazgo("GD-10", c.path, ln, "", severidad="P1", snippet=crudo[:80],
                                        msg=f"declaración rota por un ';' de más: «{crudo[:50]}» "
                                            f"queda suelta tras `{previa or 'la anterior'}` y el "
                                            f"navegador la descarta SIN avisar"))
            previa = prop or previa
    return out


# ── GD-11 ─────────────────────────────────────────────────────────────────────────────────────
# Dos casos medidos y distintos:
#   a) bien/kalinayoga-v6.html:2195 → el botón de menú llama a `alert('Menú móvil · Para demo...')`.
#   b) mal/attomo-digital.html → los enlaces se OCULTAN a <=768px y no hay sustituto.
RE_MENU = re.compile(r"men[uú]|nav|burger|hamburg|toggle", re.I)
RE_TOGGLE = re.compile(r"aria-expanded|menu-?toggle|nav-?toggle|burger|hamburg|mobile-?menu|"
                       r"nav-?open|menu-?btn", re.I)
RE_ENLACES_NAV = re.compile(r"\bnav\b|nav-?links?|menu|header\s+ul|\.links\b", re.I)


@regla("GD-11", en_vivo="abrir a 390px con page.on(\"dialog\") y comprobar que el menú se despliega")
def gd11(c: Ctx):
    out = []
    for js, l0 in c.js:
      for crudo, ln in args_llamada(js, "alert"):
        i = js.find(crudo)
        ctx = js[max(0, i - 300): i + 300]
        if RE_MENU.search(crudo) or RE_MENU.search(ctx):
            out.append(Hallazgo("GD-11", c.path, l0 + ln - 1, "", severidad="P1", snippet=crudo[:80],
                                msg="el menú móvil es un alert(): un aviso del navegador no es un "
                                    "menú, y en móvil es la ÚNICA navegación que queda"))
    if not RE_TOGGLE.search(c.texto):
        for sel, bloque, linea, ats in c.reglas():
            anchos = [int(x) for a in ats for x in re.findall(r"max-width\s*:\s*(\d+)px", a)]
            if not anchos or min(anchos) > 768:
                continue
            if re.search(r"display\s*:\s*none", bloque, re.I) and RE_ENLACES_NAV.search(sel):
                out.append(Hallazgo("GD-11", c.path, linea, "", severidad="P1", snippet=sel.strip()[:60],
                                    msg=f"a ≤{min(anchos)}px se oculta `{sel.strip()[:40]}` y en todo "
                                        f"el fichero no hay NINGÚN botón de menú (ni aria-expanded, "
                                        f"ni clase tipo burger/menu-toggle): en móvil no hay "
                                        f"navegación"))
                break
    return out


# ── GD-12 ─────────────────────────────────────────────────────────────────────────────────────
# Medido: marca 6 de los 10 ficheros del corpus (elevaiti-v2, elevaiti-v7, kalinayoga-v4,
# kalinayoga-v6, dale/styles.css y attomo) — exactamente los que la yaml enumera.
# ⚠️ Y ahí está su aviso, que la yaml ya escribe y este código repite para que nadie lo lea de
# pasada: marcar 6 de 9 referencias BUENAS es lo que la regla de inversión manda mirar dos veces.
# Aquí la lectura es la contraria de lo habitual — la regla no está mal planteada; el corpus tiene
# un agujero real de accesibilidad. Antes de promoverla hay que acotarla a elementos interactivos
# y medirla FUERA del corpus.
@regla("GD-12")
def gd12(c: Ctx):
    css = c.css_todo()
    m = re.search(r"outline\s*:\s*(none|0)\b", css, re.I)
    if not m:
        return []
    if "focus-visible" in c.texto or (c.focusvis_vecino and not c.autocontenido):
        return []
    return [Hallazgo("GD-12", c.path, c.css[0][1] + css.count("\n", 0, m.start()), "",
                     severidad="P1", snippet=m.group(0),
                     msg="se quita el outline y NO se repone el foco con :focus-visible: quien "
                         "navega con teclado deja de saber dónde está")]


# ── GD-13 y GD-14: los dos fallos de color que no se ven al escribirlos ───────────────────────
# Necesitan el VALOR de cada token del barrido entero (los tokens viven en index.css y se usan en
# un .tsx), así que `analizar` le pone a cada Ctx `vars_val`: {nombre: {valores distintos}}.
PROPS_COLOR = {"color", "background", "background-color", "border-color", "outline-color",
               "fill", "stroke", "caret-color", "text-decoration-color", "accent-color"}
RE_TRIPLETE = re.compile(r"-?[\d.]+(?:deg)?\s+[\d.]+%\s+[\d.]+%(?:\s*/\s*[\d.]+%?)?")
RE_VAR_SOLO = re.compile(r"var\(\s*(--[A-Za-z0-9_-]+)\s*(?:,[^)]*)?\)")
# Estilos en línea: atributo HTML `style="…"` y objeto JSX `style={{ color: 'var(--x)' }}`.
RE_STYLE_ATTR = re.compile(r"\bstyle\s*=\s*\"([^\"]*)\"|\bstyle\s*=\s*'([^']*)'", re.I)
RE_JSX_PROP = re.compile(r"\b(color|background|backgroundColor|borderColor|outlineColor|fill|stroke)"
                         r"\s*:\s*[\"'`](var\(\s*--[A-Za-z0-9_-]+\s*(?:,[^)]*)?\))[\"'`]")


def _kebab(p: str) -> str:
    return re.sub(r"[A-Z]", lambda m: "-" + m.group(0).lower(), p)


def _usos_color(c: "Ctx"):
    """Itera (propiedad, valor, linea) de cada declaración de color: CSS, style="" y JSX."""
    for _, bloque, linea, _ in c.reglas():
        for p, v, l, _ in declaraciones(bloque, linea):
            if p in PROPS_COLOR:
                yield p, v, l
    for m in RE_STYLE_ATTR.finditer(c.texto):
        cuerpo = m.group(1) or m.group(2) or ""
        for p, v, _, _ in declaraciones(cuerpo, 1):
            if p in PROPS_COLOR:
                yield p, v, c.texto.count("\n", 0, m.start()) + 1
    if Path(c.path).suffix.lower() in (".jsx", ".tsx", ".js", ".ts", ".vue", ".svelte"):
        for m in RE_JSX_PROP.finditer(c.texto):
            yield _kebab(m.group(1)), m.group(2), c.texto.count("\n", 0, m.start()) + 1


# Caso medido: elvion `.claude/improvements_tl.md:73-82` (P0, Vera e Ignacio a la vez): un token
# guarda el color como triplete HSL crudo (`--primary: 210 40% 50%`, el formato de shadcn y del
# patrón Tailwind 4 del template) y se usa tal cual, `color: var(--primary)`. El valor no es un
# color, la declaración es inválida en tiempo de cálculo y la propiedad sale transparente o
# heredada. Sin error en consola. Lo correcto es `hsl(var(--primary))`.
@regla("GD-13")
def gd13(c: Ctx):
    out = []
    vals = getattr(c, "vars_val", {})
    for p, v, l in _usos_color(c):
        m = RE_VAR_SOLO.fullmatch(v.strip().removesuffix("!important").strip())
        if not m:
            continue
        nombre = m.group(1)
        if any(RE_TRIPLETE.fullmatch(x) for x in vals.get(nombre, ())):
            out.append(Hallazgo("GD-13", c.path, l, "", severidad="P0", snippet=f"{p}: {v}",
                                msg=f"`{nombre}` guarda un triplete HSL crudo y aquí se usa como "
                                    f"color entero (`{p}: {v.strip()}`): no es un color, el navegador "
                                    f"descarta la declaración en silencio y sale transparente. "
                                    f"Escribe `hsl(var({nombre}))`"))
    return out


# Caso medido: elvion, Vera iter-11 (`.docs/feedback/qa-loop/WEBAPP-1/iter-11/vera/findings.json`):
# la burbuja del usuario declaraba `background: var(--widget-accent)` + `color: var(--widget-primary)`.
# Al pasar el acento de ámbar a teal, navy #243447 sobre teal #2f6f8f quedó en 2,29:1 y nadie lo
# midió en el commit. Aquí se mide cada regla que declara texto y fondo a la vez, si los dos
# resuelven a UN solo valor en el barrido (con temas, varios valores: lo mide `contraste.py --dom`).
@regla("GD-14", en_vivo="lo heredado y lo pintado por encima → scripts/contraste.py --dom <url>")
def gd14(c: Ctx):
    import contraste  # noqa: PLC0415 — RAIZ_SCRIPTS está en sys.path
    vals = getattr(c, "vars_val", {})

    def resolver(v: str, prof: int = 0):
        v = v.strip().removesuffix("!important").strip()
        m = RE_VAR_SOLO.fullmatch(v)
        if m:
            vs = vals.get(m.group(1), set())
            return resolver(next(iter(vs)), prof + 1) if len(vs) == 1 and prof < 8 else None
        m = re.fullmatch(r"hsla?\(\s*var\(\s*(--[A-Za-z0-9_-]+)\s*\)\s*\)", v)
        if m:
            vs = vals.get(m.group(1), set())
            return next(iter(vs)) if len(vs) == 1 and RE_TRIPLETE.fullmatch(next(iter(vs))) else None
        return v
    out = []
    for sel, bloque, linea, _ in c.reglas():
        decl = {p: (v, l) for p, v, l, _ in declaraciones(bloque, linea)}
        fondo = decl.get("background-color") or decl.get("background")
        if "color" not in decl or not fondo:
            continue
        fg_v, bg_v = resolver(decl["color"][0]), resolver(fondo[0])
        if not fg_v or not bg_v:
            continue
        try:
            fg, bg = contraste.to_rgba(fg_v), contraste.to_rgba(bg_v)
        except contraste.Unmeasurable:
            continue                      # un degradado, una imagen o un color que no sé leer
        if bg[3] < 1:
            continue                      # fondo translúcido: depende de lo de debajo → --dom
        px = re.match(r"([\d.]+)px", decl.get("font-size", ("",))[0] or "")
        negrita = re.match(r"(bold|[7-9]00)", decl.get("font-weight", ("",))[0] or "")
        grande = px and (float(px.group(1)) >= 24 or (float(px.group(1)) >= 18.66 and negrita))
        umbral = 3.0 if grande else 4.5
        r = contraste.ratio(fg, bg)
        if r < umbral:
            out.append(Hallazgo("GD-14", c.path, decl["color"][1], "", severidad="P1",
                                snippet=f"{sel.strip()[:60]} {{ color: {decl['color'][0]}; "
                                        f"background: {fondo[0]} }}",
                                msg=f"`{sel.strip()[:60]}` pinta {fg_v} sobre {bg_v}: {r:.2f}:1, por "
                                    f"debajo de {umbral}:1 (WCAG 2.2 AA, SC 1.4.3)"))
    return out


# ── GD-15 ─────────────────────────────────────────────────────────────────────────────────────
# El presupuesto de la letra de DISPLAY (sub-ola 3.67, UX-20). Medido en fitapp (10-17): 109 usos
# en 77 ficheros; las 12 referencias medidas del sector no usan una condensada DENTRO del
# producto, y Vera, las referencias y el detector coincidieron en que «no parece profesional» era
# la piel. Nace en sombra y SOLO avisa: el tope (≤2 por pantalla) es la propuesta de fitapp, sin
# medir fuera de su caso. En `web-cliente` no aplica: una landing vive de su letra de cartel.
# Se cuentan los USOS en el marcado: la clase en `class`/`className` y la variable en un `style`
# en línea. La definición de la clase y `font-display: swap` de un @font-face no son usos (el
# `bueno.html` los lleva de trampa). Límite: un `h1, h2 { font-family: var(--font-display) }` en
# una hoja cuenta cero, aunque pinte muchos titulares.
RE_ATTRIBUTE = re.compile(r"\b(?:class(?:Name)?|style)\s*=\s*(\"[^\"]*\"|'[^']*'|\{[^}]*\})")
RE_DISPLAY = re.compile(r"(?<![\w-])font-display(?![\w-])|var\(\s*--font-display\b")
DISPLAY_MAX = 2
_PROFILE: dict[str, str | None] = {}


def project_profile() -> str | None:
    """`web-cliente` | `producto-panel` | None, leído de `.docs/core/design-system.md` §0b."""
    if "v" not in _PROFILE:
        f = RAIZ / ".docs" / "core" / "design-system.md"
        txt = f.read_text(encoding="utf-8", errors="replace")[:20000] if f.is_file() else ""
        m = re.search(r"Perfil\**\s*\|\s*`?(web-cliente|producto-panel)\b", txt)
        _PROFILE["v"] = m.group(1) if m else None
    return _PROFILE["v"]


@regla("GD-15")
def gd15(c: Ctx):
    if project_profile() == "web-cliente" or Path(c.path).suffix.lower() in (".css", ".scss"):
        return []           # la hoja de estilos DEFINE la letra; se cuenta donde se USA
    uses = [(c.texto.count("\n", 0, m.start()) + 1, m.group(1))
            for m in RE_ATTRIBUTE.finditer(c.texto) for _ in RE_DISPLAY.findall(m.group(1))]
    n = len(uses)
    if n <= DISPLAY_MAX:
        return []
    return [Hallazgo("GD-15", c.path, uses[0][0], "", severidad="P2", snippet=uses[0][1][:90],
                     msg=f"{n} usos de la letra de display en una pantalla (presupuesto: "
                         f"≤{DISPLAY_MAX}). En un producto, la letra de cartel en cada "
                         f"título es lo que hace que parezca una plantilla")]


# ══════════════════════════════════════════════════════════════════════════════════════════════
# Waivers — una exención SIN RAZÓN no se honra
# ══════════════════════════════════════════════════════════════════════════════════════════════
# `design-exempt: GD-04 — porque el token lo impone la marca del cliente`
# El separador NO puede ser un guion simple: los identificadores llevan uno dentro (`GD-04`), así
# que `GD-04 - razón` sería ambiguo. Se aceptan «—», «–», «--» y «:». Es el mismo criterio que
# `rules/report-kit.md` fija para el campo `rec:` por la misma razón.
# El cierre del comentario (`*/`, `-->`) es opcional y va en el patrón A PROPÓSITO. Sin él, un
# `/* design-exempt: GD-06 */` no casaba con NINGUNA de las dos alternativas: no se honraba (bien)
# pero tampoco se reportaba como waiver sin razón (mal). O sea, el peor desenlace de los tres —
# alguien escribe una exención, ve que el hallazgo sigue saliendo y no entiende por qué. Lo
# encontró la prueba de sabotaje, no la lectura del código.
RE_WAIVER = re.compile(r"design-exempt\s*:\s*([A-Za-z0-9_,\*\s-]+?)\s*(—|–|--|:)\s*(\S.*)$|"
                       r"design-exempt\s*:\s*([A-Za-z0-9_,\*\s-]+?)\s*(?:\*/|-->)?\s*$", re.M)


def waivers_de(texto: str):
    """Devuelve ({regla: razón}, [reglas sin razón])."""
    con, sin = {}, []
    for m in RE_WAIVER.finditer(texto):
        ids, razon = (m.group(1), m.group(3)) if m.group(1) else (m.group(4), "")
        for rid in re.split(r"[,\s]+", (ids or "").strip()):
            if not rid:
                continue
            # La razón se escribe dentro de un comentario, así que hay que quitarle el cierre:
            # sin esto la razón acababa en «… de la marca */», que es feo en un informe que lee
            # una persona y confuso en el JSON que lee otro script.
            limpia = re.sub(r"\s*(\*/|-->|\*\)|#\s*$)\s*$", "", razon.strip())
            if limpia:
                con[rid] = limpia[:160]
            else:
                sin.append(rid)
    return con, sin


# ══════════════════════════════════════════════════════════════════════════════════════════════
# Recolección de objetivos
# ══════════════════════════════════════════════════════════════════════════════════════════════
def raiz_repo() -> Path:
    try:
        r = subprocess.run(["git", "rev-parse", "--show-toplevel"], capture_output=True,
                           text=True, timeout=10)
        if r.returncode == 0 and r.stdout.strip():
            return Path(r.stdout.strip())
    except Exception:
        pass
    return Path.cwd()


def recoger(objetivos, incluir_corpus):
    ficheros, faltan = [], []
    for o in objetivos:
        p = Path(o)
        if not p.exists():
            faltan.append(o); continue
        if p.is_file():
            ficheros.append(p); continue
        for d, subdirs, nombres in os.walk(p):
            subdirs[:] = [s for s in subdirs if s not in EXCLUIR_SIEMPRE and not s.startswith(".git")]
            for n in nombres:
                f = Path(d) / n
                if f.suffix.lower() not in EXT_MIRABLES:
                    continue
                if any(x in f.as_posix() for x in EXCLUIR_FIXTURES):
                    continue
                if not incluir_corpus and any(x in f.as_posix() for x in EXCLUIR_CORPUS):
                    continue
                ficheros.append(f)
    return sorted(set(ficheros)), faltan


# ══════════════════════════════════════════════════════════════════════════════════════════════
# Impeccable
# ══════════════════════════════════════════════════════════════════════════════════════════════
def correr_impeccable(objetivos, estado):
    """Devuelve (hallazgos, meta). meta['ok'] False = NO se pudo escanear."""
    meta = {"disponible": False, "version_pineada": IMPECCABLE_VERSION, "exit_nativo": None,
            "omitido_por_flag": False, "razon": None, "ok": False, "n": 0}
    if not shutil.which("npx"):
        meta["razon"] = "no hay `npx` en el PATH"
        return [], meta
    try:
        r = subprocess.run(["npx", "--yes", IMPECCABLE_PKG, "detect", "--json", *objetivos],
                           capture_output=True, text=True, timeout=600)
    except subprocess.TimeoutExpired:
        meta["razon"] = "`npx impeccable detect` no respondió en 600 s (¿sin red en la primera "
        meta["razon"] += "descarga?)"
        return [], meta
    except Exception as e:                                   # noqa: BLE001
        meta["razon"] = f"no se pudo lanzar npx: {type(e).__name__}"
        return [], meta
    meta["disponible"], meta["exit_nativo"] = True, r.returncode
    # ⚠️ TRADUCCIÓN DE EXIT CODES — el único sitio del fichero donde ocurre (ver cabecera).
    if r.returncode == IMP_NO_ESCANEO:
        meta["razon"] = ("impeccable no pudo escanear al menos un objetivo (su exit 1). "
                         "Su exit 1 NO significa «hay hallazgos» — eso es su 2.")
        return [], meta
    if r.returncode not in (IMP_LIMPIO, IMP_HALLAZGOS):
        meta["razon"] = f"impeccable devolvió un exit inesperado ({r.returncode})"
        return [], meta
    try:
        datos = json.loads(r.stdout or "[]")
    except json.JSONDecodeError:
        meta["razon"] = "impeccable no devolvió JSON válido en stdout"
        return [], meta
    sev = {"error": "P0", "warning": "P1", "info": "P2"}
    out = []
    for d in datos if isinstance(datos, list) else datos.get("findings", []):
        rid = d.get("antipattern") or d.get("rule") or "sin-id"
        out.append(Hallazgo(f"IMP-{rid}", rel(d.get("file") or "?"), d.get("line") or 0, estado,
                            f"[impeccable] {d.get('name') or rid}: {d.get('snippet') or ''}".strip(),
                            sev.get(str(d.get("severity", "")).lower(), "P2"),
                            "impeccable", d.get("snippet") or ""))
    meta["ok"], meta["n"] = True, len(out)
    return out, meta


def rel(p: str) -> str:
    try:
        return Path(p).resolve().relative_to(RAIZ.resolve()).as_posix()
    except Exception:                                        # noqa: BLE001
        return Path(p).as_posix()


# ══════════════════════════════════════════════════════════════════════════════════════════════
# Barrido
# ══════════════════════════════════════════════════════════════════════════════════════════════
def analizar(ficheros, reglas_yaml, solo=None):
    """Devuelve (hallazgos, waivers_aplicados, waivers_sin_razon, n_leidos)."""
    textos, vars_def = {}, set()
    vars_val: dict[str, set[str]] = {}
    reduced_dir, focus_dir = set(), set()
    for f in ficheros:
        try:
            t = f.read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue
        textos[f] = t
        vars_def |= set(RE_VARDEF.findall(t))
        for nombre, valor in re.findall(r"(--[A-Za-z0-9_-]+)\s*:\s*([^;}\n]+)", t):
            valor = re.sub(r"/\*.*?\*/", "", valor).strip().strip("'\"`,").strip()
            if valor:
                vars_val.setdefault(nombre, set()).add(valor)
        if "prefers-reduced-motion" in t:
            reduced_dir.add(f.parent)
        if "focus-visible" in t:
            focus_dir.add(f.parent)

    hallazgos, aplicados, sin_razon = [], [], []
    for f, t in textos.items():
        ruta = rel(str(f))
        con, sin = waivers_de(t)
        for rid in sin:
            sin_razon.append({"path": ruta, "rule": rid})
        ctx = Ctx(ruta, t, vars_def, f.parent in reduced_dir, f.parent in focus_dir)
        ctx.vars_val = vars_val
        for rid, fn in CHECKS.items():
            if solo and rid not in solo:
                continue
            meta = reglas_yaml.get(rid, {})
            estado = meta.get("estado", "sombra")
            if solo is None and ARGS.solo_activos and estado not in BLOCKEAN_SET:
                continue
            try:
                nuevos = fn(ctx)
            except Exception as e:                            # noqa: BLE001
                # Una regla que revienta NO puede pasar por «sin hallazgos» (verification.md):
                # se convierte en un hallazgo del propio instrumento.
                hallazgos.append(Hallazgo("GATE-ERROR", ruta, 0, "sombra",
                                          f"la regla {rid} falló al analizar este fichero: "
                                          f"{type(e).__name__}: {e}", "P1", "gate"))
                continue
            for h in nuevos:
                if rid in con or "*" in con:
                    aplicados.append({"path": ruta, "rule": rid, "razon": con.get(rid, con.get("*"))})
                    continue
                h.estado = estado
                h.severidad = meta.get("severidad", h.severidad)
                hallazgos.append(h)
    return hallazgos, aplicados, sin_razon, len(textos)


BLOCKEAN_SET = BLOQUEAN


# ══════════════════════════════════════════════════════════════════════════════════════════════
# --contra-lienzo · los tokens del código contra los del lienzo APROBADO (sub-ola 3.67, UX-20)
# ══════════════════════════════════════════════════════════════════════════════════════════════
# Generaliza `risk-couple/.claude/scripts/check_lienzo.py`: allí el 2026-09-03 se rediseñó la app
# de memoria, sin abrir el lienzo, y la paleta acabó siendo una que el Usuario no había aprobado.
# «Abre el lienzo antes de tocar un color» era una norma clara y no sirvió: baja de capa.
#   0 todos los tokens comparables coinciden · 1 alguno diverge o falta en el código · 2 no se pudo
#   medir (falta un fichero, ninguno declara tokens, o no hay ni un token comparable).
RE_TOKEN = re.compile(r"--([A-Za-z0-9_-]+)\s*:\s*([^;{}]+?)\s*(?:;|(?=}))")


def _strip_media(css: str) -> str:
    """Quita los bloques @media/@supports/@container enteros (con sus llaves anidadas).

    Un tema declara cada token dos veces —claro y, dentro de @media, oscuro—; compararlos todos a
    la vez daría «ambiguo» siempre. Se compara el valor base, que es el que el lienzo dibuja.
    """
    out, i = [], 0
    for m in re.finditer(r"@(media|supports|container)\b[^{]*\{", css):
        if m.start() < i:
            continue
        out.append(css[i:m.start()])
        depth, j = 1, m.end()
        while j < len(css) and depth:
            depth += {"{": 1, "}": -1}.get(css[j], 0)
            j += 1
        i = j
    out.append(css[i:])
    return "".join(out)


def tokens_of(texto: str, es_html: bool) -> dict[str, set[str]]:
    """{token: {valores distintos}} de lo declarado fuera de @media; en un HTML, solo en <style>."""
    css = "\n".join(c for c, _ in bloques_css(texto, es_html)) if es_html else texto
    css = re.sub(r"/\*.*?\*/", " ", css, flags=re.S)
    out: dict[str, set[str]] = {}
    for m in RE_TOKEN.finditer(_strip_media(css)):
        out.setdefault(m.group(1), set()).add(m.group(2).strip())
    return out


def normalize_token(valor: str):
    """Un valor comparable: el color como RGB, y si no, la forma con los números COMO NÚMEROS.

    `0.08` y `0.080` son el mismo croma: compararlos como cadenas dio un falso positivo la primera
    vez que se corrió `check_lienzo.py`, y un gate que grita por un cero de más se aprende a
    ignorar.
    """
    v = re.sub(r"\s+", " ", valor.strip().lower())
    rgb = a_rgb(v)
    if rgb is not None:
        return ("rgb", rgb)
    nums = tuple(round(float(n), 4) for n in re.findall(r"-?\d*\.?\d+", v))
    return ("forma", re.sub(r"-?\d*\.?\d+", "#", v).replace(" ", ""), nums)


def check_against_canvas(canvas: str, theme: str, pairs_json: str | None) -> int:
    pl, pt = Path(canvas), Path(theme)
    for p, what in ((pl, "el lienzo"), (pt, "el tema")):
        if not p.is_file():
            abortar(f"no está {what} en {p}", "sin los dos ficheros no hay nada que comparar.")
    canvas_tokens = tokens_of(pl.read_text(encoding="utf-8", errors="replace"),
                           pl.suffix.lower() in (".html", ".htm"))
    theme_tokens = tokens_of(pt.read_text(encoding="utf-8", errors="replace"),
                         pt.suffix.lower() in (".html", ".htm"))
    if not canvas_tokens:
        abortar(f"{pl} no declara ningún token (--nombre: valor)", "¿es el artboard de pantalla?")
    if not theme_tokens:
        abortar(f"{pt} no declara ningún token (--nombre: valor)")
    if pairs_json:
        try:
            pairs = json.loads(Path(pairs_json).read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as e:
            abortar(f"no puedo leer las parejas {pairs_json}: {type(e).__name__}")
        if not isinstance(pairs, dict) or not pairs:
            abortar(f"{pairs_json} debe ser un objeto {{token_del_lienzo: token_del_codigo}}")
    else:
        pairs = {t: t for t in canvas_tokens if t in theme_tokens}
        if not pairs:
            abortar("el lienzo y el tema no comparten NINGÚN nombre de token",
                    "pasa --parejas <json> con {token_del_lienzo: token_del_codigo}.")
    diverging, missing, ambiguous, unreferenced = [], [], [], []
    for theirs, ours in pairs.items():
        if theirs not in canvas_tokens:
            unreferenced.append(theirs); continue
        canvas_vals = {normalize_token(v) for v in canvas_tokens[theirs]}
        if len(canvas_vals) > 1:
            ambiguous.append((theirs, sorted(canvas_tokens[theirs]))); continue
        if ours not in theme_tokens:
            missing.append((ours, theirs, next(iter(canvas_tokens[theirs])))); continue
        theme_vals = {normalize_token(v) for v in theme_tokens[ours]}
        if theme_vals != canvas_vals:
            diverging.append((ours, sorted(theme_tokens[ours]), theirs,
                              next(iter(canvas_tokens[theirs]))))
    comparable = len(pairs) - len(unreferenced) - len(ambiguous)
    if comparable == 0:
        abortar("ninguna pareja es comparable (todas ambiguas en el lienzo o el lienzo ya no las "
                "declara)",
                f"ambiguas: {[a for a, _ in ambiguous]} · sin referencia: {unreferenced}")
    code = 1 if (diverging or missing) else 0
    if ARGS.json:
        json.dump({"version": 1, "mode": "contra-lienzo", "generado": date.today().isoformat(),
                   "estado_instrumento": "medido", "canvas": str(pl), "theme": str(pt),
                   "comparable": comparable,
                   "diverging": [{"code": n, "code_value": v, "canvas": s, "canvas_value": w}
                                for n, v, s, w in diverging],
                   "missing_in_code": [{"code": n, "canvas": s, "canvas_value": w}
                                        for n, s, w in missing],
                   "ambiguous_in_canvas": [a for a, _ in ambiguous], "unreferenced": unreferenced},
                  sys.stdout, ensure_ascii=False, indent=1)
        print()
        return code
    print(f"gate_diseno.py --contra-lienzo · {comparable} token(s) comparables · lienzo {pl}")
    for n, v, s, w in diverging:
        print(f"  ✗ --{n}\n      código: {' | '.join(v)}\n      lienzo: {w}  (--{s})")
    for n, s, w in missing:
        print(f"  ✗ falta en el código: --{n}  (el lienzo dice --{s}: {w})")
    for a, vs in ambiguous:
        print(f"  ⚠ --{a} tiene {len(vs)} valores en el lienzo ({' | '.join(vs)}): no se compara. "
              f"¿Hay un artboard de presentación mezclado con los de pantalla?")
    if unreferenced:
        print(f"  ⚠ el lienzo ya no declara: {', '.join(sorted(unreferenced))} — la tabla de "
              "parejas envejeció")
    n_bad = len(diverging) + len(missing)
    print(f"  ✗ {n_bad} token(s) NO coinciden: el lienzo manda." if code
          else "  ✓ coinciden con el lienzo aprobado.")
    return code


# ══════════════════════════════════════════════════════════════════════════════════════════════
# --dom · la página PINTADA, no el código (sub-ola 3.67, UX-20)
# ══════════════════════════════════════════════════════════════════════════════════════════════
# Medido en fitapp (10-15): sobre `.tsx` Impeccable da 0 (Tailwind se resuelve al compilar) y por
# URL no arranca como root. Lo que sí mide es el DOM renderizado guardado con su CSS en línea
# (187 hallazgos en 10 pantallas). Este modo lee esa carpeta —la deja `previsualizar_tokens.py
# --guardar-dom`— y aborta si alguna página es un cascarón sin pintar: medir el `<div id="root">`
# vacío de una SPA y decir «limpio» es el «0 fallos» del arnés que medía la pantalla de login.
DOM_MIN_TEXT = 40


def dom_files(folder: str) -> list[Path]:
    base = Path(folder)
    if not base.is_dir():
        abortar(f"--dom: {folder} no es una carpeta")
    html_files = sorted(f for f in base.rglob("*") if f.suffix.lower() in (".html", ".htm"))
    if not html_files:
        abortar(f"--dom: {folder} no tiene ningún .html",
                "guarda el DOM pintado con "
                "`previsualizar_tokens.py <url> --guardar-dom <carpeta>`.")
    shells = []
    for f in html_files:
        html = f.read_text(encoding="utf-8", errors="replace")
        visible_chars = sum(len(t) for _, t in texto_visible(html))
        if visible_chars < DOM_MIN_TEXT:
            shells.append(f"{f.name} ({visible_chars} car.)")
    if shells:
        abortar(f"--dom: {len(shells)} de {len(html_files)} página(s) son cascarones sin pintar: "
                f"{', '.join(shells[:6])}",
                "se guardaron antes de que la app montara (o la ruta pide sesión). Medir la "
                "mitad y "
                "llamarlo medición entera es la mentira que esto evita.")
    return html_files


def self_test_modes() -> int:
    """Los modos se ven fallar igual que las reglas: cada desenlace con su fixture."""
    base = RAIZ / ".claude" / "smoke" / "diseno-modos"
    if not base.is_dir():
        print(f"  ✗ MODOS  falta {rel(str(base))}: --contra-lienzo y --dom no se prueban")
        return 1
    cases = [
        ("contra-lienzo: tema igual (números con otro formato)", 0,
         ["--contra-lienzo", "lienzo.html", "--tema", "tema-igual.css"]),
        ("contra-lienzo: un color cambiado", 1,
         ["--contra-lienzo", "lienzo.html", "--tema", "tema-distinto.css"]),
        ("contra-lienzo: tema sin tokens", 2,
         ["--contra-lienzo", "lienzo.html", "--tema", "tema-vacio.css"]),
        ("dom: carpeta con un cascarón SPA", 2, ["--dom", "dom-cascaron", "--sin-impeccable"]),
        ("dom: DOM pintado", 0, ["--dom", "dom-pintado", "--sin-impeccable"]),
    ]
    fallos = 0
    for what, expected, argv in cases:
        r = subprocess.run([sys.executable, str(Path(__file__).resolve()), *argv], cwd=base,
                           capture_output=True, text=True, timeout=120)
        ok = r.returncode == expected
        fallos += not ok
        print(f"  {'✓' if ok else '✗'} MODO  {what}: exit {r.returncode}"
              + ("" if ok else f" ← se esperaba {expected} · "
                               f"{(r.stderr or r.stdout).strip()[:160]}"))
    return fallos


# ══════════════════════════════════════════════════════════════════════════════════════════════
# Self-test — las DOS mitades, o la regla no sale de sombra
# ══════════════════════════════════════════════════════════════════════════════════════════════
def self_test(reglas_yaml) -> int:
    """Cada regla tiene que cazar su caso plantado Y callar sobre su gemelo conforme.

    La segunda mitad es la que casi nadie escribe y la que de verdad calibra: un detector que
    dispara siempre también «caza» el fixture malo. Es el aviso de `rules/qa-loop.md` §4b — un
    recall sin su tasa de falsos positivos no dice si el instrumento filtra o solo hace ruido.
    """
    base = RAIZ / ".claude" / "smoke" / "diseno"
    if not base.is_dir():
        abortar(f"no existe {rel(str(base))}", "sin fixtures no se puede probar nada.")
    print("═" * 78)
    print(" gate_diseno.py --self-test · ¿caza cada regla su caso, y calla con el bueno?")
    print("═" * 78)
    fallos, sin_fixture = 0, []
    for rid in sorted(CHECKS):
        d = base / rid
        malo, bueno = d / "malo.html", d / "bueno.html"
        if not malo.exists() or not bueno.exists():
            sin_fixture.append(rid)
            print(f"  ⚠ {rid}  SIN FIXTURE ({'falta malo.html' if not malo.exists() else ''}"
                  f"{' y ' if not malo.exists() and not bueno.exists() else ''}"
                  f"{'falta bueno.html' if not bueno.exists() else ''})"
                  f" → no puede salir de `sombra`")
            fallos += 1
            continue
        # Más gemelos buenos (`bueno.test.ts`…) cuando la trampa no cabe en un HTML: el falso
        # positivo de GD-08 era el NOMBRE de un test, y eso solo se reproduce con un fichero de
        # test.
        good_twins = [bueno] + sorted(f for f in d.glob("bueno.*") if f != bueno)
        hm, _, _, _ = analizar([malo], reglas_yaml, solo={rid})
        hb, _, _, _ = analizar(good_twins, reglas_yaml, solo={rid})
        hm = [h for h in hm if h.rule == rid]
        hb = [h for h in hb if h.rule == rid]
        ok_m, ok_b = len(hm) >= 1, len(hb) == 0
        marca = "✓" if (ok_m and ok_b) else "✗"
        print(f"  {marca} {rid}  malo={len(hm)} hallazgo(s) {'OK' if ok_m else '← NO LO CAZA'}"
              f"   ·   bueno={len(hb)} {'OK' if ok_b else '← FALSO POSITIVO'}")
        if not ok_m:
            print(f"        el fixture malo no dispara: la regla no puede cazar ni su propio caso")
        for h in hb:
            print(f"        FP en {Path(h.path).name}:{h.line} — {h.msg[:100]}")
        if not (ok_m and ok_b):
            fallos += 1
    # Y al revés: una carpeta de fixtures sin regla registrada NO se prueba y no se nota. La lista
    # (CHECKS) se cruza con el disco en las DOS direcciones (rules/verification.md §Tres pautas,
    # MO-64: en AMC 22 tests en disco no corrieron nunca porque su lista no los nombraba).
    # Cualquier carpeta, no solo `GD-NN`: `GD-13-contraste-hover` o `gd-15` sin regla tampoco las
    # prueba nadie (code-review-gate de la 2.17).
    huerfanos = sorted(d.name for d in base.iterdir() if d.is_dir() and d.name not in CHECKS)
    for rid in huerfanos:
        print(f"  ✗ {rid}  FIXTURE SIN REGLA: hay {rel(str(base / rid))}/ y ninguna regla {rid} "
              f"registrada → ese caso no lo prueba nadie")
    mode_failures = self_test_modes()
    fallos_total = fallos + len(huerfanos) + mode_failures
    print("─" * 78)
    total = len(CHECKS)
    print(f" {total - fallos}/{total} reglas pasan las DOS mitades."
          + (f"  Sin fixture: {', '.join(sin_fixture)}" if sin_fixture else "")
          + (f"  Fixtures sin regla: {', '.join(huerfanos)}" if huerfanos else "")
          + (f"  Modos que fallan: {mode_failures}" if mode_failures else ""))
    print(" Recuerda: pasar el self-test NO promueve nada. Salir de `sombra` exige las cinco")
    print(" condiciones de rules/refactor-progresivo.md §4.5, y la quinta la firma un humano.")
    print("═" * 78)
    return 1 if fallos_total else 0


# ══════════════════════════════════════════════════════════════════════════════════════════════
# Salida
# ══════════════════════════════════════════════════════════════════════════════════════════════
def informar(hallazgos, meta_imp, reglas_yaml, n_ficheros, aplicados, sin_razon, inversion):
    por_regla: dict[str, list] = {}
    for h in hallazgos:
        por_regla.setdefault(h.rule, []).append(h)
    activos = [h for h in hallazgos if h.estado in BLOQUEAN]
    print("═" * 78)
    print(f" gate_diseno.py · {n_ficheros} fichero(s) mirados · {len(hallazgos)} hallazgo(s)")
    print(f" impeccable {IMPECCABLE_VERSION}: "
          + ("omitido por --sin-impeccable (DECLARADO)" if meta_imp["omitido_por_flag"]
             else (f"{meta_imp['n']} hallazgo(s), exit nativo {meta_imp['exit_nativo']}"
                   if meta_imp["ok"] else f"NO DISPONIBLE — {meta_imp['razon']}")))
    print("═" * 78)
    for rid in sorted(por_regla):
        hs = por_regla[rid]
        meta = reglas_yaml.get(rid, {})
        est = hs[0].estado or "sombra"
        enun = meta.get("enunciado", "(regla de impeccable)" if rid.startswith("IMP-") else "")
        print(f"\n── {rid} [{est}] {hs[0].severidad} · {len(hs)} hallazgo(s) ──"
              + (f"\n   {enun}" if enun else ""))
        for h in hs[:12]:
            print(f"   {h.path}:{h.line} — {h.msg}")
        if len(hs) > 12:
            print(f"   … y {len(hs) - 12} más (usa --json para verlos todos)")
    if not hallazgos:
        print("\n  Sin hallazgos. Y esto SÍ significa que se miró: el instrumento que no puede")
        print("  medir sale con 2, no con 0 (rules/verification.md).")
    for av in inversion:
        print(f"\n⚠ REGLA DE INVERSIÓN · {av['rule']} marca {av['ficheros']} ficheros "
              f"(> {INVERSION_MAX_FICHEROS}).")
        print("   rules/refactor-progresivo.md §4.4: si una regla marca tantos sitios, lo que está")
        print("   mal es la REGLA, no el código. Acótala o déjala en sombra; no la congeles.")
    if aplicados:
        print(f"\n  {len(aplicados)} waiver(s) aplicados:")
        for w in aplicados[:8]:
            print(f"   {w['path']} · {w['rule']} — {w['razon']}")
    for w in sin_razon:
        print(f"\n⚠ waiver-sin-razon en {w['path']} · {w['rule']}: `design-exempt:` SIN razón tras "
              f"«—» NO se honra.")
    print("\n" + "─" * 78)
    if activos:
        print(f" {len(activos)} hallazgo(s) de reglas en estado ACTIVO → exit 1.")
    else:
        print(f" 0 hallazgos de reglas ACTIVAS → exit 0. Hoy las {len(CHECKS)} reglas nacen en")
        print(" `sombra`: CUENTAN, no bloquean. Nada de esto para un merge todavía.")
    print("─" * 78)
    return 1 if activos else 0


def main(argv) -> int:
    global ARGS, RAIZ
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("objetivos", nargs="*", default=["."], help="ficheros o directorios (default: .)")
    ap.add_argument("--json", action="store_true", help="salida estructurada (encadenable con pattern_baseline.py)")
    ap.add_argument("--sin-impeccable", action="store_true",
                    help="corre SOLO las reglas propias (offline). Queda escrito en el JSON.")
    ap.add_argument("--exigir-impeccable", action="store_true", default=True,
                    help="(por defecto) si impeccable no está, sale con 2 en vez de decir «limpio»")
    ap.add_argument("--incluir-corpus", action="store_true",
                    help="mira también resources/referencias-diseno (excluido por defecto)")
    ap.add_argument("--solo-activos", action="store_true", help="solo reglas en estado `activo`")
    ap.add_argument("--impeccable-estado", default="sombra",
                    help="estado con el que entran los hallazgos de impeccable (default: sombra)")
    ap.add_argument("--self-test", action="store_true",
                    help="corre contra smoke/diseno/ (reglas) y smoke/diseno-modos/ (modos)")
    ap.add_argument("--contra-lienzo", metavar="LIENZO",
                    help="compara los tokens de --tema con los de este lienzo aprobado "
                         "(.html/.css): "
                         "0 coinciden · 1 divergen · 2 no se pudo medir")
    ap.add_argument("--tema", metavar="CSS",
                    help="con --contra-lienzo: el fichero de tokens del código")
    ap.add_argument("--parejas", metavar="JSON",
                    help="con --contra-lienzo: {token_del_lienzo: token_del_codigo}; sin él, "
                         "los de "
                         "igual nombre")
    ap.add_argument("--dom", metavar="CARPETA",
                    help="mide el DOM PINTADO guardado en esa carpeta (previsualizar_tokens.py "
                         "--guardar-dom); 2 si alguna página es un cascarón sin pintar")
    a = ap.parse_args(argv)
    ARGS = a
    RAIZ = raiz_repo()

    # El lienzo no necesita el corpus: es una comparación de dos ficheros del proyecto.
    if a.contra_lienzo or a.tema:
        if not (a.contra_lienzo and a.tema):
            abortar("--contra-lienzo y --tema van juntos")
        return check_against_canvas(a.contra_lienzo, a.tema, a.parejas)

    yml = RAIZ / ".claude" / RUTA_YAML
    if not yml.exists():
        abortar(f"no encuentro {RUTA_YAML}",
                "las reglas GD viven ahí; sin el fichero no hay nada que medir. En un proyecto "
                "derivado lo trae `propagar.py` junto con este script (desde la 3.67); si falta, "
                "cópialo de `.claude/resources/referencias-diseno/` del template.")
    try:
        import yaml as _yaml
    except ImportError:
        abortar("falta PyYAML", "pip install pyyaml — sin él no se pueden leer los estados.")
    doc = _yaml.safe_load(yml.read_text(encoding="utf-8")) or {}
    reglas_yaml = {r["id"]: r for r in doc.get("reglas", [])}
    faltan_impl = sorted(set(reglas_yaml) - set(CHECKS))
    if faltan_impl:
        print(f"⚠ declaradas en la yaml y SIN implementar: {', '.join(faltan_impl)}", file=sys.stderr)

    if a.self_test:
        return self_test(reglas_yaml)

    if a.dom:
        objetivos = [a.dom]
        ficheros, faltan = dom_files(a.dom), []
    else:
        objetivos = a.objetivos or ["."]
        ficheros, faltan = recoger(objetivos, a.incluir_corpus)
    if faltan:
        abortar(f"estos objetivos no existen: {', '.join(faltan)}",
                "es la lección de red-flags.sh: apuntar a un directorio que no está y decir "
                "«(clean)».")
    if not ficheros:
        abortar(f"ningún fichero mirable en {', '.join(objetivos)}",
                f"extensiones que se miran: {' '.join(sorted(EXT_MIRABLES))}. "
                f"¿Querías --incluir-corpus?")

    h_imp, meta_imp = [], {"disponible": False, "version_pineada": IMPECCABLE_VERSION,
                           "exit_nativo": None, "omitido_por_flag": True, "razon":
                           "--sin-impeccable", "ok": False, "n": 0}
    if not a.sin_impeccable:
        objs_imp = [str(f) for f in ficheros] if len(ficheros) <= 400 else list(objetivos)
        h_imp, meta_imp = correr_impeccable(objs_imp, a.impeccable_estado)
        if not meta_imp["ok"] and a.exigir_impeccable:
            abortar(f"impeccable no pudo medir ({meta_imp['razon']})",
                    "Con --sin-impeccable corres SOLO las reglas propias, y queda escrito en el "
                    "JSON. Lo que no se hace es degradar en silencio a «media medición».")

    h_prop, aplicados, sin_razon, n_leidos = analizar(ficheros, reglas_yaml)
    hallazgos = h_prop + h_imp

    inversion = []
    for rid in {h.rule for h in hallazgos}:
        n = len({h.path for h in hallazgos if h.rule == rid})
        if n > INVERSION_MAX_FICHEROS:
            inversion.append({"rule": rid, "ficheros": n})

    codigo = informar(hallazgos, meta_imp, reglas_yaml, n_leidos, aplicados, sin_razon, inversion) \
        if not a.json else (1 if any(h.estado in BLOQUEAN for h in hallazgos) else 0)

    if a.json:
        json.dump({
            "version": 1, "mode": "dom" if a.dom else "codigo",
            "generado": date.today().isoformat(), "estado_instrumento": "medido",
            "razon_no_medido": None,
            "objetivo": objetivos, "incluye_corpus": a.incluir_corpus,
            "impeccable": {k: v for k, v in meta_imp.items() if k != "n"} | {"hallazgos": meta_imp["n"]},
            "reglas_cargadas": {"propias": len(CHECKS), "declaradas_en_yaml": len(reglas_yaml),
                                "sin_implementar": faltan_impl,
                                "corpus": RUTA_YAML, "impeccable": meta_imp["n"]},
            "resumen": {"ficheros_mirados": n_leidos, "hallazgos": len(hallazgos),
                        "de_reglas_activas": sum(1 for h in hallazgos if h.estado in BLOQUEAN),
                        "waivers_aplicados": aplicados, "waivers_sin_razon": sin_razon,
                        "avisos_inversion": inversion,
                        "comprobaciones_en_vivo_NO_hechas": EN_VIVO},
            "hallazgos": [h.dict() for h in hallazgos],
        }, sys.stdout, ensure_ascii=False, indent=1)
        print()
    return codigo


ARGS = argparse.Namespace(json=False, solo_activos=False)
RAIZ = Path.cwd()

if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
