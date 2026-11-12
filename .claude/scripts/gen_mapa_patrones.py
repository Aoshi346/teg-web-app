#!/usr/bin/env python3
"""El mapa patrón → dónde está resuelto en código real. Se REGENERA, no se edita.

POR QUE EXISTE
--------------
Peticion del Usuario: *"se tienen que mirar primero los patrones y luego mirar sus archivos en
caso de que se necesite mas informacion"*. Ese orden ahorra mucho: el patron son 200 lineas con la
regla y el porque; el cuerpo de referencia son miles y hay que traerlo antes.

Y al generarlo salio el dato que lo justifica (2026-08-27): de 40 patrones, **29 no citan ningun
precedente**. `patterns/README.md` exige >=2 precedentes `file:line` o silencio — o sea, 29
patrones afirman y no ensenan donde. Este fichero lo hace visible en vez de dejarlo implicito.

POR QUE ES UN SCRIPT Y NO UN PASO ESCRITO EN LA SKILL
------------------------------------------------------
`rules/layer-decision.md` pregunta 1: si el coste de que se ignore es alto, baja de capa. Un paso
escrito se salta; un script se ejecuta. Y este dato envejece solo — cada patron nuevo sin
precedente empeora el numero sin que nadie lo note.

USO
    python3 gen_mapa_patrones.py [--escribir]
"""
from __future__ import annotations

import argparse
import datetime
import json
import pathlib
import re
import sys

RAIZ = pathlib.Path(__file__).resolve().parents[2]
STACK = RAIZ / ".claude" / "patterns" / "stack"
PROC = RAIZ / ".claude" / "patterns" / "referencia" / "procedencia.json"
DESTINO = RAIZ / ".claude" / "patterns" / "referencia" / "mapa-patrones.yaml"
NO_SON_PATRON = {"README.md", "ARRANQUE.md", "REFERENCIAS.md"}


def construir() -> tuple[str, int, int]:
    proc = json.loads(PROC.read_text(encoding="utf-8"))
    inverso: dict[str, list] = {}
    for c in proc["cuerpos"]:
        for p in c.get("patrones", []):
            inverso.setdefault(p, []).append(c)

    out = [
        "# Mapa: patrón → dónde está resuelto en código real",
        "#",
        "# COMO SE LEE, y el orden importa:",
        "#   1. Se lee el PATRÓN (`patterns/stack/<fichero>`): corto, con la regla y el porqué.",
        "#   2. SOLO si el patrón no basta, se baja al cuerpo de referencia — es caro de leer y",
        "#      hay que traerlo antes (`scripts/traer_referencias.py`).",
        "#",
        "# Lo leen `update-agent` y `gen_tareas_del_harness.py`.",
        "# SE REGENERA, no se edita:  python3 .claude/scripts/gen_mapa_patrones.py --escribir",
        f"generado: {datetime.date.today().isoformat()}",
        "patrones:",
    ]
    ficheros = sorted(p.name for p in STACK.glob("*.md") if p.name not in NO_SON_PATRON)
    con = sin = 0
    for fichero in ficheros:
        txt = (STACK / fichero).read_text(encoding="utf-8", errors="replace")
        m = (re.search(r"^> \*\*Cuándo aplica[^:]*:\*\*\s*(.+)", txt, re.M)
             or re.search(r"^> \*\*Cuándo aplicar[^:]*:\*\*\s*(.+)", txt, re.M))
        cuando = (m.group(1).strip()[:110] if m else "").replace('"', "'")
        cuerpos = inverso.get(fichero, [])
        out.append(f"  - patron: {fichero}")
        out.append(f"    lineas: {len(txt.splitlines())}")
        if cuando:
            out.append(f'    cuando: "{cuando}"')
        if cuerpos:
            con += 1
            out.append("    resuelto_en:")
            for c in cuerpos:
                out.append(f"      - cuerpo: {c['id']}")
                out.append(f"        ruta: {c['ruta']}")
                out.append(f'        ensena: "{c.get("ensena", "")[:100]}"')
                if c.get("privado"):
                    out.append("        privado: true   # hace falta acceso al remote")
        else:
            sin += 1
            out.append("    resuelto_en: []   # SIN precedente — el patrón afirma y no enseña dónde")
    out += ["", f"# {con} patrones con precedente · {sin} SIN precedente · {len(ficheros)} en total"]
    return "\n".join(out) + "\n", con, sin


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--escribir", action="store_true")
    a = ap.parse_args()
    if not PROC.is_file():
        print(f"✗ falta {PROC}", file=sys.stderr)
        return 1
    texto, con, sin = construir()
    print(f"  {con} patrones con precedente · {sin} SIN precedente · {con + sin} en total")
    if sin:
        print(f"  ⚠️ {sin} patrones afirman sin enseñar dónde. patterns/README.md exige >=2 "
              "precedentes file:line o silencio.")
    if a.escribir:
        DESTINO.write_text(texto, encoding="utf-8")
        print(f"  ✓ {DESTINO.relative_to(RAIZ)}")
    else:
        print("  → para escribirlo: --escribir")
    return 0


if __name__ == "__main__":
    sys.exit(main())
