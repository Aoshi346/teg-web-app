#!/usr/bin/env python3
"""guarda_pii_capturas.py — ninguna captura que se entrega sale con datos personales reales.

Cosechado de EvoPreven (sub-ola 2.29 de la revisión integral, SE-42). En EVO-2876 el chequeo de
texto del informe dio «0 nombres» y las capturas llevaban nombres DENTRO de la imagen
(`Analítica ( APELLIDOS, Nombre ) | fecha`, cinco filas): ningún grep ve un nombre dentro de un PNG.
La memoria `pii-dentro-de-capturas` de develop lo dejó escrito: filtrar ANTES de capturar y, aun
así, MIRAR la imagen antes de entregarla, que fue lo que detectó el fallo.

LAS TRES CAPAS, y ninguna basta sola:

  1. Antes de capturar, `screenshot.py` lee el texto visible del DOM —de todos los frames, y el valor
     de los campos de formulario, que no sale en innerText— y DESCARTA la captura (no la guarda, sale
     con 1) si casa un dato personal fuera de la lista blanca.
  2. Opcional, antes de eso, enmascara («•••») el texto de los elementos que digan los `enmascarar`
     del proyecto, salvo lo que está en la lista blanca (el `capture.py` de EVO-2913).
  3. Antes de ENTREGAR, la revisión visual: cada imagen de la carpeta de entrega necesita su entrada
     en `REVISION-CAPTURAS.json` —sha256, quién la miró y cuándo—, y `--comprobar` sale con 1 si
     falta alguna o si la imagen cambió después de mirarla. Mirarla puede hacerlo el agente (abrir el
     PNG con Read); lo que no vale es no mirarla.

CUÁNDO ESTÁ ENCENDIDA en `screenshot.py`: si el proyecto tiene `.claude/pii-capturas.json`, es
delicado (`.claude/proyecto-delicado.md`) o su CONFIGURACION.yaml dice salud o datos reales en
desarrollo, siempre; en los demás, con `--guarda-pii`. No hay bandera
para apagarla en un proyecto delicado: lo que sobre se pone en la lista blanca, con nombre.

QUÉ BUSCA por defecto, con su dígito de control para no gritar con cualquier número: email (salvo
dominios de ejemplo: example.*, *.test, *.invalid, *.localhost, ejemplo.*), DNI y NIE con su letra,
IBAN (módulo 97), número de la Seguridad Social (módulo 97), tarjeta (Luhn), teléfono español y
«APELLIDOS, Nombre» (el de EVO-2876). Cada proyecto añade los suyos en `.claude/pii-capturas.json`:

    {"lista_blanca": ["GARCÍA PRUEBA, Ana", "paciente1@demo.test"],
     "dominios_permitidos": ["evo-demo.es"],
     "patrones": [{"nombre": "id-trabajador", "regex": "\\\\bTRB-(\\\\d{5})\\\\b",
                   "rango_sintetico": [90000, 99999]}],
     "desactivar": {"telefono": "la app enseña el teléfono de la mutua, que es público"},
     "enmascarar": ["td.nombre", "[data-pii]"]}

Un patrón con `rango_sintetico` solo salta fuera del rango (lo de pwlib.py de EVO-2834: aborta si
aparece un identificador fuera del rango sintético). Desactivar uno por defecto pide una razón de 15
caracteres o más.

QUÉ NO VE, y por eso existe la capa 3: lo que está dentro de una imagen, un canvas, un PDF incrustado
o un vídeo; un nombre en minúsculas normales («Ana García») sin un patrón del proyecto que lo
describa; y lo que el navegador pinta con CSS (`content:`). Nunca imprime el dato que encuentra:
solo su tipo y una muestra tapada.

USO
    python3 .claude/scripts/screenshot.py <url> <out.png> [...] --guarda-pii       # la capa 1 y 2
    python3 .claude/scripts/guarda_pii_capturas.py --texto <fichero|->             # revisar un texto
    python3 .claude/scripts/guarda_pii_capturas.py --registrar <carpeta> --por "<quién>" <png…>
    python3 .claude/scripts/guarda_pii_capturas.py --comprobar <carpeta>           # antes de entregar
    python3 .claude/scripts/guarda_pii_capturas.py --autoprueba [--python <py con playwright>]

SALIDA: 0 limpio · 1 hay datos personales, o capturas sin revisar · 2 no se pudo medir (config
inválida, carpeta que no existe).
"""
from __future__ import annotations

import hashlib
import json
import os
import re
import subprocess
import sys
import tempfile
import threading
from datetime import date
from pathlib import Path

EXIT_OK, EXIT_FALLO, EXIT_NO_MEDIDO = 0, 1, 2
CONFIG = Path(".claude") / "pii-capturas.json"
MARCADOR_DELICADO = Path(".claude") / "proyecto-delicado.md"
REVISION = "REVISION-CAPTURAS.json"
IMAGENES = {".png", ".jpg", ".jpeg", ".webp"}
RAZON_MINIMA = 15
LETRAS_DNI = "TRWAGMYFPDXBNJZSQVHLCKE"
DOMINIOS_EJEMPLO = re.compile(r"(^|\.)(example(\.(com|net|org))?|ejemplo(\.(com|es|org))?|test|invalid|"
                              r"localhost|local)$", re.I)


class ConfigInvalida(Exception):
    """La configuración del proyecto no se puede usar: sale con 2."""


# ── los validadores: un número que no pasa su control no es un dato ─────────────────────────


def _dni(m: re.Match) -> bool:
    s = m.group(0).upper().replace("-", "").replace(" ", "").replace(".", "")
    if s[0] in "XYZ":
        s = str("XYZ".index(s[0])) + s[1:]
    return s[:-1].isdigit() and LETRAS_DNI[int(s[:-1]) % 23] == s[-1]


def _mod97(cadena: str) -> bool:
    try:
        return int("".join(str(int(c, 36)) for c in cadena)) % 97 == 1
    except ValueError:
        return False


def _iban(m: re.Match) -> bool:
    s = re.sub(r"\s", "", m.group(0)).upper()
    return 15 <= len(s) <= 34 and _mod97(s[4:] + s[:4])


def _nss(m: re.Match) -> bool:
    s = re.sub(r"\D", "", m.group(0))
    if len(s) != 12:
        return False
    provincia, numero, control = int(s[:2]), int(s[2:10]), int(s[10:])
    # El control de la TGSS: (provincia·10⁸ + número) mod 97, o provincia·10⁷ si el número < 10⁷.
    base = provincia * 10**8 + numero if numero >= 10**7 else provincia * 10**7 + numero
    return 1 <= provincia <= 99 and base % 97 == control


def _luhn(m: re.Match) -> bool:
    d = [int(c) for c in re.sub(r"\D", "", m.group(0))]
    if not 13 <= len(d) <= 19 or len(set(d)) == 1:
        return False
    total = 0
    for i, n in enumerate(reversed(d)):
        if i % 2:
            n = n * 2 - 9 if n > 4 else n * 2
        total += n
    return total % 10 == 0


def _telefono(m: re.Match) -> bool:
    s = re.sub(r"\D", "", m.group(0))
    if s.startswith("34") and len(s) == 11:
        s = s[2:]
    return len(s) == 9 and s[0] in "6789" and len(set(s)) > 2


def _email(m: re.Match, permitidos: tuple) -> bool:
    dominio = m.group(0).rsplit("@", 1)[-1].lower().rstrip(".")
    if DOMINIOS_EJEMPLO.search(dominio):
        return False
    return not any(dominio == p or dominio.endswith("." + p) for p in permitidos)


MAY = "A-ZÁÉÍÓÚÑÜÀÈÒÏÇ"
PATRONES = [
    ("email", re.compile(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}"), "email"),
    ("dni-nie", re.compile(r"(?<![A-Za-z0-9.])[XYZxyz]?(?:\d{7,8}|\d{1,2}\.\d{3}\.\d{3})[- ]?[A-Za-z]"
                           r"(?![A-Za-z0-9])"), _dni),
    ("iban", re.compile(r"(?<![A-Za-z0-9])[A-Z]{2}\d{2}(?:\s?[A-Z0-9]{4}){2,7}(?:\s?[A-Z0-9]{1,3})?"
                        r"(?![A-Za-z0-9])"), _iban),
    # `\w` en el lookbehind: dentro de un IBAN («ES91 2100…») no empieza una tarjeta ni un teléfono.
    ("nss", re.compile(r"(?<![\w.,])\d{2}[ /-]?\d{8}[ /-]?\d{2}(?![\w.,])"), _nss),
    ("tarjeta", re.compile(r"(?<![\w.,])(?:\d[ -]?){12,18}\d(?![\w.,])"), _luhn),
    ("telefono", re.compile(r"(?<![\w.,+])(?:\+34[\s-]?)?[6-9](?:[\s-]?\d){8}(?![\w.,])"), _telefono),
    ("apellidos-nombre", re.compile(rf"(?<![{MAY}\w])[{MAY}]{{2,}}(?:[ -][{MAY}]{{2,}})*,\s*"
                                    rf"[{MAY}][a-záéíóúñüàèòïç]+"), None),
]


def tapar(valor: str) -> str:
    """Una muestra que sirve para encontrarlo en la pantalla y no para leerlo."""
    v = valor.strip()
    if "@" in v:
        usuario, _, dominio = v.partition("@")
        return f"{usuario[:1]}***@{dominio[:1]}***.{dominio.rsplit('.', 1)[-1]}"
    return f"{v[:2]}…({len(v)})"


# ── configuración del proyecto ───────────────────────────────────────────────────────────


def raiz_del_proyecto(desde: Path | None = None) -> Path:
    if os.environ.get("CLAUDE_PROJECT_DIR"):
        return Path(os.environ["CLAUDE_PROJECT_DIR"])
    p = (desde or Path.cwd()).resolve()
    for d in (p, *p.parents):
        if (d / ".claude").is_dir():
            return d
    return p


def cargar_config(raiz: Path) -> dict:
    p = raiz / CONFIG
    if not p.exists():
        return {}
    try:
        d = json.loads(p.read_text(encoding="utf-8"))
    except ValueError as e:
        raise ConfigInvalida(f"{p} no es JSON válido: {e}") from e
    return validar_config(d, str(p))


def validar_config(d: dict, origen: str = "config") -> dict:
    if not isinstance(d, dict):
        raise ConfigInvalida(f"{origen}: no es un objeto JSON")
    nombres = {n for n, _, _ in PATRONES}
    for nombre, razon in (d.get("desactivar") or {}).items():
        if nombre not in nombres:
            raise ConfigInvalida(f"{origen}: desactivar «{nombre}», que no es un patrón por defecto "
                                 f"({', '.join(sorted(nombres))})")
        if len(str(razon or "").strip()) < RAZON_MINIMA:
            raise ConfigInvalida(f"{origen}: desactivar «{nombre}» sin una razón de {RAZON_MINIMA} "
                                 "caracteres o más")
    propios = []
    for p in d.get("patrones") or []:
        try:
            rx = re.compile(p["regex"])
        except (KeyError, TypeError, re.error) as e:
            raise ConfigInvalida(f"{origen}: patrón propio inválido {p!r}: {e}") from e
        rango = p.get("rango_sintetico")
        if rango is not None and (not isinstance(rango, list) or len(rango) != 2 or rx.groups < 1):
            raise ConfigInvalida(f"{origen}: «{p.get('nombre')}»: rango_sintetico es [min, max] y el "
                                 "regex necesita un grupo con el número")
        propios.append((str(p.get("nombre") or "propio"), rx, rango))
    return dict(d, _propios=propios)


def sensible(raiz: Path) -> bool:
    """CONFIGURACION.yaml con datos de salud o datos reales en desarrollo: delicado también para
    la guarda (la misma lectura que aviso-envio-externo.sh)."""
    try:
        conf = (raiz / ".claude" / "CONFIGURACION.yaml").read_text(encoding="utf-8")
    except OSError:
        return False
    return bool(re.search(r"^\s*datos_sensibles:\s*.*\bsalud\b", conf, re.M)
                or re.search(r"""^\s*datos_reales_desarrollo:\s*["']?s[ií]""", conf, re.M))


def activa(flags: set, raiz: Path | None = None) -> dict | None:
    """La config si la guarda tiene que correr en esta captura; None si no."""
    raiz = raiz or raiz_del_proyecto()
    obligada = (raiz / CONFIG).exists() or (raiz / MARCADOR_DELICADO).exists() or sensible(raiz)
    if not obligada and "--guarda-pii" not in flags:
        return None
    return cargar_config(raiz) or {"_propios": []}


# ── revisar un texto ─────────────────────────────────────────────────────────────────────


def revisar(texto: str, config: dict | None = None) -> list[dict]:
    config = config or {}
    blanca = {s.strip().lower() for s in config.get("lista_blanca") or []}
    apagados = set((config.get("desactivar") or {}).keys())
    permitidos = tuple(str(x).lower() for x in config.get("dominios_permitidos") or [])
    hallados, vistos = [], set()
    for nombre, rx, validar in PATRONES:
        if nombre in apagados:
            continue
        for m in rx.finditer(texto):
            valor = m.group(0).strip()
            if valor.lower() in blanca:
                continue
            if validar == "email":
                if not _email(m, permitidos):
                    continue
            elif validar is not None and not validar(m):
                continue
            clave = (nombre, valor)
            if clave not in vistos:
                vistos.add(clave)
                hallados.append(dict(tipo=nombre, muestra=tapar(valor)))
    for nombre, rx, rango in config.get("_propios") or []:
        for m in rx.finditer(texto):
            valor = m.group(0).strip()
            if valor.lower() in blanca:
                continue
            if rango is not None:
                try:
                    if rango[0] <= int(m.group(1)) <= rango[1]:
                        continue
                except (ValueError, TypeError):
                    pass
            if (nombre, valor) not in vistos:
                vistos.add((nombre, valor))
                hallados.append(dict(tipo=nombre, muestra=tapar(valor)))
    return hallados


def informe(hallados: list[dict], donde: str = "la página") -> str:
    tipos = sorted({h["tipo"] for h in hallados})
    lineas = [f"⛔ guarda de datos personales: {len(hallados)} dato(s) en {donde} "
              f"({', '.join(tipos)}). La captura NO se guarda."]
    lineas += [f"   · {h['tipo']}: {h['muestra']}" for h in hallados[:12]]
    if len(hallados) > 12:
        lineas.append(f"   · … y {len(hallados) - 12} más")
    lineas.append("   Si son sintéticos, a la lista blanca de .claude/pii-capturas.json; si son reales, "
                  "filtra la pantalla (otro rango de fechas, datos de prueba) o enmascara con "
                  "«enmascarar». rules/verification.md §3.")
    return "\n".join(lineas)


# ── en el navegador (Playwright) ─────────────────────────────────────────────────────────

JS_TEXTO = r"""() => {
  const partes = [document.title || '', document.body ? document.body.innerText : ''];
  for (const el of document.querySelectorAll('input, textarea, select')) {
    if (['password', 'hidden'].includes((el.type || '').toLowerCase())) continue;
    const v = el.tagName === 'SELECT' ? (el.selectedOptions[0] ? el.selectedOptions[0].text : '')
                                      : (el.value || '');
    if (v) partes.push(v);
    if (el.placeholder) partes.push(el.placeholder);
  }
  return partes.join('\n');
}"""

JS_TAPAR = r"""([selectores, blanca]) => {
  const ok = new Set(blanca.map(s => s.trim().toLowerCase()));
  let n = 0;
  for (const sel of selectores) {
    for (const el of document.querySelectorAll(sel)) {
      const w = document.createTreeWalker(el, NodeFilter.SHOW_TEXT);
      for (let t = w.nextNode(); t; t = w.nextNode()) {
        const v = (t.nodeValue || '').trim();
        if (v && !ok.has(v.toLowerCase())) { t.nodeValue = '•••'; n++; }
      }
      if ('value' in el && el.value && !ok.has(String(el.value).trim().toLowerCase())) {
        el.value = '•••'; n++;
      }
    }
  }
  return n;
}"""


def enmascarar(page, config: dict) -> int:
    selectores = list(config.get("enmascarar") or [])
    if not selectores:
        return 0
    n = 0
    for f in page.frames:
        try:
            n += f.evaluate(JS_TAPAR, [selectores, list(config.get("lista_blanca") or [])])
        except Exception:                                  # noqa: BLE001 — un frame que se fue
            pass
    return n


def revisar_pagina(page, config: dict) -> list[dict]:
    textos = []
    for f in page.frames:
        try:
            textos.append(f.evaluate(JS_TEXTO))
        except Exception as e:                             # noqa: BLE001
            # Un frame que no se puede leer no se da por limpio: se dice.
            textos.append("")
            print(f"[guarda-pii] aviso: no se pudo leer un frame ({type(e).__name__}); su "
                  "contenido queda para la revisión visual", file=sys.stderr)
    return revisar("\n".join(textos), config)


# ── la revisión visual antes de entregar ─────────────────────────────────────────────────


def _sha(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()


def _imagenes(carpeta: Path) -> list[Path]:
    return sorted(p for p in carpeta.rglob("*") if p.is_file() and p.suffix.lower() in IMAGENES)


def registrar(carpeta: Path, por: str, pngs: list[str], nota: str = "") -> int:
    if not carpeta.is_dir():
        print(f"✗ no existe la carpeta {carpeta}", file=sys.stderr)
        return EXIT_NO_MEDIDO
    if len(por.strip()) < 3:
        print("✗ --por: quién miró las capturas (una persona, o el agente que las abrió con Read)",
              file=sys.stderr)
        return EXIT_FALLO
    ruta = carpeta / REVISION
    reg = json.loads(ruta.read_text(encoding="utf-8")) if ruta.exists() else {}
    for x in pngs:
        p = Path(x)
        p = p if p.is_absolute() else Path.cwd() / p
        if not p.is_file():
            print(f"✗ no existe {x}", file=sys.stderr)
            return EXIT_FALLO
        rel = p.resolve().relative_to(carpeta.resolve()).as_posix()
        reg[rel] = dict(sha256=_sha(p), revisado_por=por.strip(), fecha=date.today().isoformat(),
                        nota=nota or "mirada entera: sin datos personales")
    ruta.write_text(json.dumps(reg, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    print(f"✓ {len(pngs)} captura(s) anotadas como revisadas en {ruta}")
    return EXIT_OK


def comprobar(carpeta: Path) -> int:
    if not carpeta.is_dir():
        print(f"✗ NO MEDIDO: no existe la carpeta {carpeta}", file=sys.stderr)
        return EXIT_NO_MEDIDO
    ruta = carpeta / REVISION
    try:
        reg = json.loads(ruta.read_text(encoding="utf-8")) if ruta.exists() else {}
    except ValueError as e:
        print(f"✗ NO MEDIDO: {ruta} no es JSON válido: {e}", file=sys.stderr)
        return EXIT_NO_MEDIDO
    malas = []
    imagenes = _imagenes(carpeta)
    for p in imagenes:
        rel = p.relative_to(carpeta).as_posix()
        e = reg.get(rel)
        if not e:
            malas.append(f"{rel}: nadie la ha mirado")
        elif e.get("sha256") != _sha(p):
            malas.append(f"{rel}: cambió después de mirarla (el sha no cuadra)")
        elif not str(e.get("revisado_por") or "").strip() or not e.get("fecha"):
            malas.append(f"{rel}: la revisión no dice quién ni cuándo")
    if malas:
        print(f"⛔ {len(malas)} de {len(imagenes)} captura(s) sin revisión visual válida:")
        for m in malas:
            print(f"   · {m}")
        print("   Ábrelas (Read), míralas enteras y anótalas: guarda_pii_capturas.py --registrar "
              f"{carpeta} --por \"<quién>\" <png…>")
        return EXIT_FALLO
    print(f"✓ {len(imagenes)} captura(s), todas miradas y sin cambios desde entonces")
    return EXIT_OK


# ── autoprueba ───────────────────────────────────────────────────────────────────────────

CONF_PRUEBA = {
    "lista_blanca": ["GARCÍA PRUEBA, Ana"],
    "dominios_permitidos": ["evo-demo.es"],
    "patrones": [{"nombre": "id-trabajador", "regex": r"\bTRB-(\d{5})\b",
                  "rango_sintetico": [90000, 99999]}],
}
# (nombre, texto, tipos que tienen que salir; vacío = no puede salir nada)
TEXTOS = [
    ("un email de verdad", "Contacto: maria.lopez@gmail.com", {"email"}),
    ("un DNI con su letra", "DNI 12345678Z del trabajador", {"dni-nie"}),
    ("un NIE con su letra", "NIE X1234567L", {"dni-nie"}),
    ("un DNI con puntos", "DNI 12.345.678-Z", {"dni-nie"}),
    ("un IBAN válido", "Cuenta ES91 2100 0418 4502 0005 1332", {"iban"}),
    ("un móvil", "Teléfono: 612 345 678", {"telefono"}),
    ("un fijo con prefijo", "Llamar al +34 912 34 56 78", {"telefono"}),
    ("una tarjeta (Luhn)", "Pago con 4111 1111 1111 1111", {"tarjeta"}),
    ("un NSS válido", "NSS 28 12345678 40", {"nss"}),
    ("«APELLIDOS, Nombre» (EVO-2876)", "Analítica ( GARCÍA LÓPEZ, Ana ) | 2026-09-14",
     {"apellidos-nombre"}),
    ("id propio fuera del rango sintético", "Trabajador TRB-12345", {"id-trabajador"}),
    ("control · email de ejemplo", "ana@example.com y ana@clinica.test", set()),
    ("control · email de un dominio permitido", "soporte@evo-demo.es", set()),
    ("control · DNI con la letra mal", "Ref. 12345678A", set()),
    ("control · IBAN con el control mal", "ES91 2100 0418 4502 0005 1333", set()),
    ("control · un importe no es un teléfono", "Total: 612.345.678 €", set()),
    ("control · un nombre de la lista blanca", "Analítica ( GARCÍA PRUEBA, Ana )", set()),
    ("control · id propio dentro del rango", "Trabajador TRB-90001", set()),
    ("control · una fecha y un código", "EVO-2876 · 2026-09-14 · 10:30", set()),
]

PAGINA = """<!doctype html><meta charset="utf-8"><title>Ficha</title>
<h1>Ficha del trabajador</h1><table><tr><td class="nombre">{nombre}</td><td>TRB-90001</td></tr></table>
<form><label>Correo <input id="correo" value="{correo}"></label></form>"""


def _servir(carpeta: Path):
    from functools import partial
    from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer

    class Callado(SimpleHTTPRequestHandler):
        def log_message(self, *a):  # noqa: D401
            pass

    srv = ThreadingHTTPServer(("127.0.0.1", 0), partial(Callado, directory=str(carpeta)))
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    return srv


def autoprueba(python: str | None) -> int:
    filas = []
    conf = validar_config(CONF_PRUEBA, "autoprueba")
    for nombre, texto, esperados in TEXTOS:
        obtenidos = {h["tipo"] for h in revisar(texto, conf)}
        filas.append((f"texto · {nombre}", obtenidos == esperados,
                      f"esperaba {sorted(esperados) or '—'}, salió {sorted(obtenidos) or '—'}"))
    # encendida sin bandera con una CONFIGURACION sensible (verificador de la 2.29)
    with tempfile.TemporaryDirectory(prefix="guarda-activa-") as t2:
        r2 = Path(t2)
        (r2 / ".claude").mkdir()
        a0 = activa(set(), r2) is None
        (r2 / ".claude" / "CONFIGURACION.yaml").write_text("respuestas:\n  datos_reales_desarrollo: si-salud\n")
        filas.append(("activa · sin nada no corre; con datos reales en desarrollo, sí",
                      a0 and activa(set(), r2) is not None, ""))
    # nunca imprime el dato entero
    h = revisar("maria.lopez@gmail.com", conf)
    filas.append(("texto · la muestra va tapada", bool(h) and "maria.lopez" not in h[0]["muestra"],
                  h[0]["muestra"] if h else "—"))
    for nombre, mala in (("desactivar sin razón", {"desactivar": {"telefono": "no"}}),
                         ("desactivar un patrón que no existe", {"desactivar": {"x": "a" * 20}}),
                         ("rango sin grupo en el regex", {"patrones": [{"regex": "TRB-\\d+",
                                                                        "rango_sintetico": [1, 2]}]})):
        try:
            validar_config(mala, "autoprueba")
            filas.append((f"config · {nombre} → no medido", False, "la aceptó"))
        except ConfigInvalida:
            filas.append((f"config · {nombre} → no medido", True, ""))

    with tempfile.TemporaryDirectory(prefix="guarda-pii-") as tmp:
        tmp = Path(tmp)
        entrega = tmp / "entrega"
        entrega.mkdir()
        png = entrega / "ficha.png"
        png.write_bytes(b"\x89PNG\r\n\x1a\n de juguete")
        import contextlib
        import io

        def rc(fn, *a):
            with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
                return fn(*a)
        filas.append(("revisión · captura que nadie ha mirado → 1", rc(comprobar, entrega) == 1, ""))
        rc(registrar, entrega, "Ana Ruiz", [str(png)])
        filas.append(("revisión · mirada y sin cambios → 0", rc(comprobar, entrega) == 0, ""))
        png.write_bytes(b"\x89PNG\r\n\x1a\n cambiada")
        filas.append(("revisión · cambiada después de mirarla → 1", rc(comprobar, entrega) == 1, ""))
        filas.append(("revisión · sin decir quién → no se anota", rc(registrar, entrega, " ", [str(png)])
                      == 1, ""))
        filas.append(("revisión · carpeta que no existe → 2", rc(comprobar, tmp / "no") == 2, ""))

        if python:
            web = tmp / "web"
            web.mkdir()
            (web / "con-email.html").write_text(PAGINA.format(nombre="GARCÍA PRUEBA, Ana",
                                                              correo="maria.lopez@gmail.com"), "utf-8")
            (web / "limpia.html").write_text(PAGINA.format(nombre="GARCÍA PRUEBA, Ana",
                                                           correo="ana@example.com"), "utf-8")
            (web / "nombre-real.html").write_text(PAGINA.format(nombre="LÓPEZ MARTÍN, Pedro",
                                                                correo="ana@example.com"), "utf-8")
            proyecto = tmp / "proyecto"
            (proyecto / ".claude").mkdir(parents=True)
            (proyecto / ".claude" / "proyecto-delicado.md").write_text(
                "datos de salud de trabajadores (autoprueba)\n", "utf-8")
            srv = _servir(web)
            base = f"http://127.0.0.1:{srv.server_address[1]}"
            shot = Path(__file__).resolve().parent / "screenshot.py"
            try:
                for nombre, pagina, enmascara, rc_esperado in (
                        ("navegador · email falso en un campo del formulario → descartada",
                         "con-email.html", False, 1),
                        ("navegador · «APELLIDOS, Nombre» en una celda → descartada",
                         "nombre-real.html", False, 1),
                        ("navegador · la misma celda enmascarada → se guarda",
                         "nombre-real.html", True, 0),
                        ("navegador · control · página con datos de ejemplo → se guarda",
                         "limpia.html", False, 0)):
                    salida = tmp / f"{pagina}-{int(enmascara)}.png"
                    conf_p = {"enmascarar": ["td.nombre"], "lista_blanca": ["GARCÍA PRUEBA, Ana"]} \
                        if enmascara else {"lista_blanca": ["GARCÍA PRUEBA, Ana"]}
                    (proyecto / ".claude" / "pii-capturas.json").write_text(json.dumps(conf_p), "utf-8")
                    r = subprocess.run([python, str(shot), f"{base}/{pagina}", str(salida), "800", "600",
                                        "300"], cwd=proyecto, capture_output=True, text=True,
                                       env=dict(os.environ, CLAUDE_PROJECT_DIR=str(proyecto)),
                                       timeout=120)
                    guardada = salida.exists()
                    # Un 1 tiene que ser POR la guarda: un navegador que no arranca también da 1 sin png.
                    por_la_guarda = "guarda de datos personales" in r.stderr
                    ok = (r.returncode == rc_esperado and guardada == (rc_esperado == 0)
                          and por_la_guarda == (rc_esperado == 1))
                    det = (r.stderr or r.stdout).strip().splitlines()[-1:] or ["—"]
                    filas.append((nombre, ok, f"exit {r.returncode}, png {'sí' if guardada else 'no'}"
                                              f" · {det[0][:140]}"))
            finally:
                srv.shutdown()
                srv.server_close()
        else:
            filas.append(("navegador · (sin --python con playwright: no probado)", True, "saltado"))
    bien = sum(ok for _, ok, _ in filas)
    print("Guarda de datos personales en capturas · autoprueba\n")
    for n, ok, d in filas:
        print(f"  {'✓' if ok else '✗'} {n}" + ("" if ok or not d else f"\n      {d}"))
    print(f"\n═══ {bien}/{len(filas)} casos como se esperaba")
    return EXIT_OK if bien == len(filas) else EXIT_FALLO


def main(argv=None) -> int:
    argv = list(sys.argv[1:] if argv is None else argv)

    def valor(flag):
        if flag in argv:
            i = argv.index(flag)
            v = argv[i + 1] if i + 1 < len(argv) else None
            del argv[i:i + 2]
            return v
        return None

    try:
        if "--autoprueba" in argv:
            argv.remove("--autoprueba")
            return autoprueba(valor("--python"))
        if "--comprobar" in argv:
            return comprobar(Path(valor("--comprobar") or "."))
        if "--registrar" in argv:
            carpeta = Path(valor("--registrar") or ".")
            por, nota = valor("--por") or "", valor("--nota") or ""
            return registrar(carpeta, por, [a for a in argv if not a.startswith("--")], nota)
        if "--texto" in argv:
            origen = valor("--texto") or "-"
            texto = sys.stdin.read() if origen == "-" else Path(origen).read_text(
                encoding="utf-8", errors="replace")
            hallados = revisar(texto, cargar_config(raiz_del_proyecto()))
            if hallados:
                print(informe(hallados, "el texto").replace("La captura NO se guarda.", ""))
                return EXIT_FALLO
            print("✓ sin datos personales en el texto (lo que va dentro de una imagen no se ve: "
                  "revisión visual)")
            return EXIT_OK
    except ConfigInvalida as e:
        print(f"✗ NO MEDIDO: {e}", file=sys.stderr)
        return EXIT_NO_MEDIDO
    print(__doc__)
    return EXIT_NO_MEDIDO


if __name__ == "__main__":
    sys.exit(main())
