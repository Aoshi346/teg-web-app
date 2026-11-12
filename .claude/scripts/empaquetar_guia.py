#!/usr/bin/env python3
"""Empaqueta `manual.html` y todo lo que enlaza en UNA carpeta que funciona sola.

POR QUÉ EXISTE. `manual.html` vive en `.docs/core/` y enlaza a `../../.claude/rules/…` y a
`../plans/…/sources/…`. Copiar solo esa carpeta produce una guía con **31 enlaces rotos** — que es
peor que no dársela, porque parece completa. Esto resuelve los enlaces, convierte cada `.md` a una
página HTML legible en el navegador, y deja una carpeta que se abre con doble clic **sin servidor,
sin red y sin instalar nada**.

QUÉ NO HACE: no inventa contenido ni resume. Lo que no esté enlazado desde el manual, no entra.

    python3 .claude/scripts/empaquetar_guia.py [destino]
        Por defecto: `.docs/download/guia-proceso/`, que está IGNORADO en git a propósito —
        es un artefacto derivado (1,1 MB de HTML) que se regenera en un comando, y versionarlo
        metería una copia que envejece en cuanto cambie una rule.
"""
from __future__ import annotations

import pathlib
import re
import shutil
import subprocess
import sys

RAIZ = pathlib.Path(__file__).resolve().parents[2]
MANUAL = RAIZ / ".docs" / "core" / "manual.html"
MD2HTML = RAIZ / ".claude" / "templates" / "report_kit" / "md_to_html.py"


def convertir(src: pathlib.Path, dst: pathlib.Path, titulo: str) -> bool:
    dst.parent.mkdir(parents=True, exist_ok=True)
    r = subprocess.run([sys.executable, str(MD2HTML), str(src), str(dst), titulo],
                       capture_output=True, text=True)
    if r.returncode != 0:
        print(f"   ⚠ no se pudo convertir {src.name}: {r.stderr.strip()[:90]}")
        return False
    return True


def main() -> int:
    destino = pathlib.Path(sys.argv[1]) if len(sys.argv) > 1 else RAIZ / ".docs" / "download" / "guia-proceso"
    if not MANUAL.exists():
        sys.exit(f"ERROR: no existe {MANUAL}. Genéralo antes con gen_manual.py")
    if destino.exists():
        shutil.rmtree(destino)
    (destino / "docs").mkdir(parents=True)

    txt = MANUAL.read_text(encoding="utf-8")
    hrefs = sorted(set(re.findall(r'href="([^"#][^"]*)"', txt)))
    base = MANUAL.parent
    hechos, fallos = {}, []

    for h in hrefs:
        origen = (base / h).resolve()
        if origen.is_dir():
            # Un ejemplo trabajado entero: se copia y sus .md se convierten.
            sub = destino / "docs" / origen.name
            shutil.copytree(origen, sub)
            for md in sub.rglob("*.md"):
                convertir(md, md.with_suffix(".html"), md.stem)
                md.unlink()
            # El índice de la carpeta: si hay brand.html, ese; si no, el README
            entrada = "brand.html" if (sub / "brand.html").exists() else "README.html"
            hechos[h] = f"docs/{origen.name}/{entrada}"
        elif origen.suffix == ".md" and origen.exists():
            out = destino / "docs" / (origen.stem + ".html")
            if convertir(origen, out, origen.stem):
                hechos[h] = f"docs/{out.name}"
            else:
                fallos.append(h)
        elif origen.exists():
            shutil.copy2(origen, destino / "docs" / origen.name)
            hechos[h] = f"docs/{origen.name}"
        else:
            fallos.append(h)

    for viejo, nuevo in hechos.items():
        txt = txt.replace(f'href="{viejo}"', f'href="{nuevo}"')
    # Los enlaces internos entre documentos convertidos también se reescriben
    (destino / "index.html").write_text(txt, encoding="utf-8")

    # Un LÉEME en la raíz, porque quien recibe esto no sabe qué es
    (destino / "LÉEME.txt").write_text(
        "GUÍA DEL PROCESO\n"
        "================\n\n"
        "Abre  index.html  con doble clic. Se ve en cualquier navegador.\n\n"
        "No hace falta internet, ni instalar nada, ni un servidor: la carpeta funciona sola.\n"
        "La carpeta docs/ son los documentos que el manual enlaza; no hace falta abrirlos\n"
        "directamente — se llega a ellos desde el manual.\n\n"
        "Empieza por «Las cinco cosas que hay que saber antes de empezar», y después pulsa\n"
        "el paso 1 en el dibujo.\n", encoding="utf-8")

    # El ZIP al lado: es lo que se descarga de una sola vez. shutil y no `zip`, que no está
    # instalado en este servidor (medido).
    zip_path = shutil.make_archive(str(destino), "zip", str(destino.parent), destino.name)

    n = sum(1 for _ in destino.rglob("*") if _.is_file())
    kb = sum(f.stat().st_size for f in destino.rglob("*") if f.is_file()) // 1024
    print(f"OK {destino}  ({n} ficheros · {kb} KB · {len(hechos)}/{len(hrefs)} enlaces resueltos)")
    print(f"OK {zip_path}  ({pathlib.Path(zip_path).stat().st_size//1024} KB)")
    for f in fallos:
        print(f"   ⚠ sin resolver: {f}")
    return 1 if fallos else 0


if __name__ == "__main__":
    sys.exit(main())
