#!/usr/bin/env python3
"""check_internal_notes.py — ninguna nota de trabajo en un entregable que ve un cliente.

De dónde sale (AN-13, sub-ola 3.18 de la revisión integral). webs lo construyó en su `gen_dist.py`
el 13-08-2026, después de que una caja «⚠ REVISAR ANTES DE PUBLICAR» llegara desplegada a la web de
pruebas y la viera el Usuario. Su regla: «nunca notas internas en el artefacto». La prosa no
protege cuando hay prisa; esto sí. Aquí va generalizado para cualquier HTML o texto que salga del
repo hacia un cliente: una web, un PDF de `pdf-premium` (se mira su HTML de origen), un informe.

## Qué mira

El TEXTO VISIBLE: quita `<!-- … -->`, `<script>` y `<style>` (lo que no se ve en pantalla) y mira lo
que queda, más los atributos que sí se leen (`alt`, `title`, `placeholder`, `aria-label` y el
`content` de un `<meta name="description">`). Un `.md` o `.txt` se mira entero.

Marcadores (mayúsculas a propósito: «TODO campo de formulario» es castellano, no una nota; falso
positivo medido en el GD-07 de `gate_diseno.py` en fitapp): `TODO:` · `TODO(` · `FIXME` · `XXX` ·
`REVISAR` · `PENDIENTE:` · `NO PUBLICAR` · `PLACEHOLDER` · `[PERSONALIZAR]` · `TBD` · `lorem ipsum`
· `⚠`. Con `--allow <marcador>` se quita uno (p. ej. `--allow ⚠` si el aviso es parte del contenido).

## Lo que NO hace

No quita nada: dice dónde está y sale con 1. Quitar los comentarios antes de publicar es trabajo
del generador (en webs lo hace `gen_dist.py`); este script es el gate que va detrás. Tampoco ve
texto pintado dentro de una imagen ni el que añade un JavaScript al cargar.

Uso:
    python3 .claude/scripts/check_internal_notes.py dist/                 # carpeta: *.html, *.htm, *.md, *.txt
    python3 .claude/scripts/check_internal_notes.py propuesta.html --allow ⚠
    python3 .claude/scripts/check_internal_notes.py --self-test           # se ve fallar con un TODO plantado

Salida: 0 limpio · 1 hay notas internas visibles · 2 no se pudo medir (ningún fichero en lo que se
le pasa, o no se lee). Una carpeta vacía NO es «limpio» (`rules/verification.md` §El instrumento
que no puede medir).
"""
from __future__ import annotations

import argparse
import html
import re
import sys
import tempfile
from pathlib import Path

EXTENSIONS = (".html", ".htm", ".md", ".txt")
MARKERS = {
    "TODO:": r"\bTODO\s*:",
    "TODO(": r"\bTODO\(",
    "FIXME": r"\bFIXME\b",
    "XXX": r"\bXXX\b",
    "REVISAR": r"\bREVISAR\b",
    "PENDIENTE:": r"\bPENDIENTE\s*:",
    "NO PUBLICAR": r"\bNO PUBLICAR\b",
    "PLACEHOLDER": r"\bPLACEHOLDER\b",
    "[PERSONALIZAR]": r"\[PERSONALIZAR\]",
    "TBD": r"\bTBD\b",
    "lorem ipsum": r"(?i)\blorem ipsum\b",
    "⚠": r"⚠",
}
HIDDEN = re.compile(r"<!--.*?-->|<script\b.*?</script\s*>|<style\b.*?</style\s*>", re.S | re.I)
READ_ATTRS = re.compile(r"""\b(?:alt|title|placeholder|aria-label)\s*=\s*(["'])(.*?)\1""", re.S | re.I)
META_DESC = re.compile(r"""<meta\b[^>]*\bname\s*=\s*["']description["'][^>]*>""", re.I)
META_CONTENT = re.compile(r"""\bcontent\s*=\s*(["'])(.*?)\1""", re.S | re.I)
TAG = re.compile(r"<[^>]+>")


def _blank(match: re.Match) -> str:
    """Sustituye lo oculto por saltos de línea: así los números de línea siguen siendo los del fichero."""
    return "\n" * match.group(0).count("\n")


def visible_lines(text: str, is_html: bool) -> list[tuple[int, str]]:
    if not is_html:
        return list(enumerate(text.splitlines(), 1))
    text = HIDDEN.sub(_blank, text)
    out = []
    for n, line in enumerate(text.splitlines(), 1):
        extras = [m.group(2) for m in READ_ATTRS.finditer(line)]
        for meta in META_DESC.findall(line):
            extras += [m.group(2) for m in META_CONTENT.finditer(meta)]
        body = html.unescape(TAG.sub(" ", line))
        joined = " ".join([body] + [html.unescape(x) for x in extras]).strip()
        if joined:
            out.append((n, joined))
    return out


def scan_file(path: Path, markers: dict[str, re.Pattern]) -> list[tuple[str, int, str, str]]:
    text = path.read_text(encoding="utf-8", errors="replace")
    found = []
    for n, line in visible_lines(text, path.suffix.lower() in (".html", ".htm")):
        for name, rx in markers.items():
            m = rx.search(line)
            if m:
                a = max(0, m.start() - 50)
                found.append((str(path), n, name, line[a:m.end() + 50].strip()))
    return found


def collect(targets: list[str]) -> list[Path]:
    files = []
    for t in targets:
        p = Path(t)
        if p.is_dir():
            files += sorted(f for f in p.rglob("*") if f.is_file() and f.suffix.lower() in EXTENSIONS)
        elif p.is_file():
            files.append(p)
    return files


def run(targets: list[str], allow: list[str]) -> int:
    markers = {k: re.compile(v) for k, v in MARKERS.items() if k not in allow}
    missing = [t for t in targets if not Path(t).exists()]
    if missing:  # una errata en `dist/` no puede pasar en verde porque otra ruta sí existía
        print(f"✗ no se pudo medir: no existe {', '.join(missing)}", file=sys.stderr)
        return 2
    files = collect(targets)
    if not files:
        print(f"✗ no se pudo medir: ningún {'/'.join(EXTENSIONS)} en {' '.join(targets) or '(nada)'}",
              file=sys.stderr)
        return 2
    try:
        hits = [h for f in files for h in scan_file(f, markers)]
    except OSError as exc:
        print(f"✗ no se pudo leer: {exc}", file=sys.stderr)
        return 2
    if not hits:
        print(f"✓ sin notas internas visibles en {len(files)} fichero(s)")
        return 0
    print(f"✗ {len(hits)} nota(s) interna(s) visible(s) en {len(files)} fichero(s) — no se publica así:")
    for f, n, name, ctx in hits:
        print(f"  {f}:{n}  «{name}»  …{ctx}…")
    return 1


def self_test() -> int:
    ok = True
    with tempfile.TemporaryDirectory() as d:
        page = Path(d) / "index.html"
        cases = [
            ("<p>Contrata ya. TODO: poner el precio</p>", 1, "un TODO: visible"),
            ("<!-- TODO: poner el precio --><p>Contrata ya</p>", 0, "un TODO dentro de un comentario"),
            ("<p>TODO campo del formulario es obligatorio</p>", 0, "«TODO campo» en castellano"),
            ('<img src="a.png" alt="PLACEHOLDER">', 1, "un PLACEHOLDER en el alt"),
            ("<style>/* REVISAR contraste */</style><p>Hola</p>", 0, "una nota dentro de <style>"),
            ("<div>⚠ REVISAR ANTES DE PUBLICAR</div>", 1, "la caja que llegó a la web de webs"),
            ('<meta name="description" content="TBD">', 1, "un TBD en la meta description"),
        ]
        for html_text, expected, what in cases:
            page.write_text(f"<!doctype html><html><body>\n{html_text}\n</body></html>\n")
            got = run([d], [])
            if got != expected:
                print(f"✗ self-test: {what} → exit {got}, esperaba {expected}")
                ok = False
        page.write_text("<div>⚠ Aviso de cookies</div>")
        if run([d], ["⚠"]) != 0:
            print("✗ self-test: --allow ⚠ no lo quitó"); ok = False
        page.unlink()
        if run([d], []) != 2:
            print("✗ self-test: una carpeta sin ficheros debe dar 2 (no se pudo medir), no 0"); ok = False
    print("OK: self-test (control negativo incluido)" if ok else "self-test FALLA")
    return 0 if ok else 1


def main() -> int:
    ap = argparse.ArgumentParser(description="Gate: ninguna nota interna en un entregable público.")
    ap.add_argument("targets", nargs="*", help="ficheros o carpetas a mirar")
    ap.add_argument("--allow", action="append", default=[], help="marcador que se permite (repetible)")
    ap.add_argument("--self-test", action="store_true")
    a = ap.parse_args()
    if a.self_test:
        return self_test()
    unknown = [x for x in a.allow if x not in MARKERS]
    if unknown:
        print(f"✗ --allow desconocido: {unknown}; los marcadores son {list(MARKERS)}", file=sys.stderr)
        return 2
    return run(a.targets, a.allow)


if __name__ == "__main__":
    sys.exit(main())
