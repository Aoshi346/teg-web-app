#!/usr/bin/env python3
"""El puente: los requisitos de `/arrancar` → el `spec.md` de una sesión SpecKit.

POR QUÉ EXISTE. Sin esto, la spec se escribe DOS VECES: una al entrevistar y otra al abrir la
sesión. Y la segunda sale peor, porque se escribe de memoria en vez de con el Usuario delante.

LO QUE DE VERDAD COMPRA, y es el motivo: `spec_lint.py` pasa **por construcción, no por suerte**.
Sus tres errores son E1 (≥15 líneas), E2 (verbo normativo en los requisitos) y E3 (criterios de
aceptación). Los requisitos de `/arrancar` ya traen las tres cosas —la tanda R.1 pregunta «¿esto
DEBE pasar siempre?» justo para forzar el verbo, y los criterios nacen en Gherkin—, así que
derivar la spec de ellos hace imposible el caso que este repo tiene HOY en sus dos sesiones:
specs sin un solo verbo normativo y sin ningún criterio de aceptación.

NO INVENTA NADA. Lo que no esté en los requisitos no aparece en la spec: si falta algo, el arreglo
es volver a `/arrancar`, no escribirlo aquí.

    python3 requisitos_to_spec.py <plan> <sesión>     # escribe <sesión>/spec.md
    python3 requisitos_to_spec.py <plan> <sesión> --check   # solo dice qué saldría
"""
from __future__ import annotations

import argparse
import datetime as dt
import pathlib
import re
import sys


def secciones(txt: str) -> dict[str, str]:
    """Los bloques `## R-n · Título` de 02-requisitos.md."""
    out, actual, buf = {}, None, []
    for l in txt.splitlines():
        m = re.match(r"^##\s+(R-\S+.*)$", l.strip())
        if m:
            if actual:
                out[actual] = "\n".join(buf)
            actual, buf = m.group(1).strip(), []
        elif actual:
            buf.append(l)
    if actual:
        out[actual] = "\n".join(buf)
    return out


def apartado(bloque: str, nombre: str) -> str:
    """El contenido de un apartado `### <nombre>` dentro de un requisito."""
    m = re.search(rf"^#{{3,4}}\s*\d*\.?\s*{re.escape(nombre)}\s*$(.*?)(?=^#{{1,4}} |\Z)",
                  bloque, re.M | re.S | re.I)
    return m.group(1).strip() if m else ""


def gherkin(bloque: str) -> list[str]:
    return [re.sub(r"\s+", " ", m.group(0)).strip()
            for m in re.finditer(r"Dado que[\s\S]{0,400}?entonces[^\n]*", bloque, re.I)]


def main() -> int:
    ap = argparse.ArgumentParser(description="requisitos → spec.md")
    ap.add_argument("plan"); ap.add_argument("sesion")
    ap.add_argument("--check", action="store_true")
    a = ap.parse_args()
    plan, ses = pathlib.Path(a.plan).resolve(), pathlib.Path(a.sesion).resolve()

    req_f = plan / "arranque" / "02-requisitos.md"
    if not req_f.exists():
        sys.stderr.write(f"ERROR: no existe {req_f}.\n"
                         "  La spec se DERIVA de los requisitos; no se escribe aparte.\n"
                         "  Corre /arrancar fase 1b primero.\n")
        return 3
    req_txt = req_f.read_text(encoding="utf-8")
    prd_f = plan / "arranque" / "01-prd.md"
    prd = prd_f.read_text(encoding="utf-8") if prd_f.exists() else ""

    reqs = secciones(req_txt)
    if not reqs:
        sys.stderr.write("ERROR: ningún requisito con cabecera `## R-n …` en 02-requisitos.md\n")
        return 1

    objetivo = ""
    m = re.search(r"^##\s*(?:El problema|Objetivo|Qué será verdad)[^\n]*\n(.*?)(?=^## |\Z)",
                  prd, re.M | re.S | re.I)
    if m:
        objetivo = re.sub(r"\s+", " ", m.group(1)).strip()[:400]

    L = [f"# Spec — {ses.name}", "",
         f"> **Derivada** de `{req_f.relative_to(plan.parent.parent)}` el {dt.date.today()}.",
         "> No se edita a mano: se corrigen los requisitos y se vuelve a derivar. Lo que no esté",
         "> en ellos no aparece aquí — si falta algo, el sitio de arreglarlo es `/arrancar`.", ""]
    if objetivo:
        L += ["## Objetivo", "", objetivo, ""]

    L += ["## Requisitos funcionales", ""]
    sin_verbo, sin_crit = [], []
    for titulo, bloque in reqs.items():
        L.append(f"### {titulo}")
        L.append("")
        for nom, etiq in (("Qué deja en las manos del usuario", "Entrega"),
                          ("Quién y cuándo", "Actor"),
                          ("Qué hace el usuario", "Acción"),
                          ("Cuál es su entrada", "Entrada"),
                          ("Cuál es la salida", "Salida")):
            v = apartado(bloque, nom)
            if v:
                L.append(f"- **{etiq}**: {re.sub(r'\\s+', ' ', v)[:300]}")
        # El verbo normativo: se conserva la frase que lo lleva, que es la que E2 busca.
        norm = [re.sub(r"\s+", " ", l).strip() for l in bloque.splitlines()
                if re.search(r"\b(DEBE(R[ÁA])?N?|NO DEBE|SHALL|MUST)\b", l)]
        if norm:
            L.append("")
            for n in norm[:4]:
                L.append(f"- {n.lstrip('-* ')}")
        else:
            sin_verbo.append(titulo)
        g = gherkin(bloque)
        if g:
            L += ["", "**Criterios de aceptación**", ""]
            L += [f"- {x}" for x in g]
        else:
            sin_crit.append(titulo)
        L.append("")

    L += ["## Fuera de alcance", ""]
    fa = re.search(r"^##\s*(?:Qué queda fuera|Fuera de alcance)[^\n]*\n(.*?)(?=^## |\Z)",
                   prd, re.M | re.S | re.I)
    L.append(re.sub(r"\s+", " ", fa.group(1)).strip()[:400] if fa
             else "_No declarado en el PRD._ Es un hueco: vuelve a `/arrancar` fase 1.")
    L.append("")

    if sin_verbo or sin_crit:
        L += ["## Avisos de la derivación", ""]
        for t in sin_verbo:
            L.append(f"- ⚠️ `{t}` sin verbo normativo — `spec_lint.py` E2 lo va a marcar. "
                     "Se arregla en el requisito, no aquí.")
        for t in sin_crit:
            L.append(f"- ⚠️ `{t}` sin criterio en Gherkin — `spec_lint.py` E3.")
        L.append("")

    texto = "\n".join(L)
    if a.check:
        print(f"{len(reqs)} requisitos · {len(texto.splitlines())} líneas · "
              f"{len(sin_verbo)} sin verbo · {len(sin_crit)} sin criterio")
        return 1 if (sin_verbo or sin_crit) else 0

    ses.mkdir(parents=True, exist_ok=True)
    out = ses / "spec.md"
    if out.exists() and "**Derivada** de" not in out.read_text(encoding="utf-8"):
        sys.stderr.write(f"ERROR: {out} existe y NO está derivada — la escribió alguien a mano.\n"
                         "  No se pisa: muévela o bórrala tú si de verdad quieres regenerarla.\n")
        return 1
    out.write_text(texto + "\n", encoding="utf-8")
    print(f"OK {out}  ({len(reqs)} requisitos)")
    for t in sin_verbo:
        print(f"   ⚠ {t}: sin verbo normativo (E2)")
    for t in sin_crit:
        print(f"   ⚠ {t}: sin criterio de aceptación (E3)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
