#!/usr/bin/env python3
"""corpus_lint.py — que el corpus de referencia no envejezca en silencio.

Un corpus de gusto tiene tres formas de pudrirse, y ninguna se ve leyéndolo:

  1. CADUCA. Una referencia de hace tres años enseña a diseñar como hace tres años.
  2. SE VUELVE MONOCULTIVO. Si 7 de 10 referencias son SaaS oscuro, el corpus produce
     exactamente el mismo look genérico que el techo Stripe/Linear/Vercel que retiramos
     por eso mismo (agents/shared/calibration-v2.md §4).
  3. ENGORDA. Sin tope, acaba como acaban los CLAUDE.md: creciendo hasta que nadie lo lee
     entero y por tanto nadie lo usa (rules/self-improvement-loop.md §5).

Este script mide las tres y NO decide ninguna: retirar una entrada es del Usuario.

Desenlaces:
    0  medido, el corpus está sano
    1  medido, hay avisos que atender
    2  NO SE PUDO MEDIR (falta el índice o el manifiesto)

Uso:  python3 .claude/scripts/corpus_lint.py [--json]
"""
import json
import sys
from datetime import date, datetime
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[1]
CORPUS = RAIZ / "resources" / "referencias-diseno"
INDICE = CORPUS / "INDEX.json"
MANIFIESTO = CORPUS / "MANIFEST.tsv"

TOPE_ENTRADAS = 15          # rules/report-kit.md aprendió lo mismo con las pestañas
MESES_CADUCIDAD = 18
CONCENTRACION_MAX = 0.6     # ninguna familia de sector por encima del 60%


def abortar(motivo: str) -> None:
    print(f"⛔ NO SE PUDO MEDIR: {motivo}", file=sys.stderr)
    print("   Un corpus que no se puede auditar no es un corpus sano: es uno sin auditar.",
          file=sys.stderr)
    sys.exit(2)


def meses_desde(iso: str) -> float:
    try:
        d = datetime.strptime(iso if len(iso) > 7 else iso + "-01", "%Y-%m-%d").date()
    except ValueError:
        return -1.0
    return (date.today() - d).days / 30.44


def main() -> int:
    if not INDICE.exists():
        abortar(f"no existe {INDICE.relative_to(RAIZ)}")
    if not MANIFIESTO.exists():
        abortar(f"no existe {MANIFIESTO.relative_to(RAIZ)} — sin huellas no hay procedencia")

    d = json.loads(INDICE.read_text())
    entradas = d["entradas"]
    avisos, datos = [], {}

    # ── 1 · tope ────────────────────────────────────────────────────────────
    datos["entradas"] = len(entradas)
    if len(entradas) > TOPE_ENTRADAS:
        avisos.append(f"el corpus tiene {len(entradas)} entradas y el tope es {TOPE_ENTRADAS}: "
                      f"meter una exige RETIRAR otra, con su razón escrita")

    # ── 2 · caducidad ───────────────────────────────────────────────────────
    viejas = []
    for e in entradas:
        m = meses_desde(e.get("fecha_captura", ""))
        if m > MESES_CADUCIDAD:
            viejas.append(f"{e['id']} ({m:.0f} meses)")
    datos["caducadas"] = viejas
    if viejas:
        avisos.append(f"{len(viejas)} entrada(s) con más de {MESES_CADUCIDAD} meses: "
                      f"{', '.join(viejas)}. Revisar si siguen enseñando algo")

    # ── 3 · concentración ───────────────────────────────────────────────────
    # La familia se saca de la primera palabra del sector: «bienestar · masaje» → bienestar
    familias = {}
    for e in entradas:
        fam = (e.get("sector", "sin sector").split("·")[0]).strip().lower()
        familias[fam] = familias.get(fam, 0) + 1
    datos["familias"] = familias
    total = len(entradas) or 1
    for fam, n in sorted(familias.items(), key=lambda x: -x[1]):
        if n / total > CONCENTRACION_MAX:
            avisos.append(f"MONOCULTIVO: {n} de {total} entradas son «{fam}» ({n/total:.0%}). "
                          f"Un corpus concentrado produce el mismo look genérico que el techo "
                          f"Stripe/Linear/Vercel que se retiró por esto")

    # ── 4 · perfiles cubiertos ──────────────────────────────────────────────
    perfiles = {}
    for e in entradas:
        perfiles[e.get("perfil", "sin perfil")] = perfiles.get(e.get("perfil", "sin perfil"), 0) + 1
    datos["perfiles"] = perfiles
    for p in ("web-cliente", "producto-panel"):
        if perfiles.get(p, 0) < 2:
            avisos.append(f"solo {perfiles.get(p, 0)} referencia(s) de perfil `{p}`: "
                          f"con menos de 2, la regla R-E de Vera no puede exigir citar dos")

    # ── 5 · honestidad: ¿las entradas declaran sus defectos? ────────────────
    sin_defectos = [e["id"] for e in entradas
                    if e.get("veredicto") == "bien" and not e.get("defectos_conocidos")]
    datos["sin_defectos_declarados"] = sin_defectos
    if sin_defectos:
        avisos.append(f"{len(sin_defectos)} entrada(s) marcadas «bien» sin NINGÚN defecto "
                      f"declarado ({', '.join(sin_defectos)}). Ningún diseño real está limpio: "
                      f"o no se ha mirado, o se está vendiendo")

    # ── 6 · integridad: cada fichero del manifiesto sigue ahí ───────────────
    faltan = []
    for linea in MANIFIESTO.read_text().split("\n"):
        if not linea.strip() or linea.startswith("#") or linea.startswith("ruta\t"):
            continue
        ruta = linea.split("\t")[0]
        if not (CORPUS / ruta).exists():
            faltan.append(ruta)
    datos["ficheros_que_faltan"] = faltan
    if faltan:
        avisos.append(f"{len(faltan)} fichero(s) del manifiesto ya no están: {', '.join(faltan[:3])}"
                      f" — las citas que apunten ahí están rotas")

    if "--json" in sys.argv:
        print(json.dumps({"estado_instrumento": "medido", "avisos": avisos, "datos": datos},
                         ensure_ascii=False, indent=1))
    else:
        print(f"corpus_lint · {len(entradas)} entradas · perfiles {perfiles} · familias {familias}")
        for a in avisos:
            print(f"  ⚠ {a}")
        if not avisos:
            print("  ✓ sin avisos: dentro del tope, sin caducar, sin monocultivo y con defectos declarados")
    return 1 if avisos else 0


if __name__ == "__main__":
    sys.exit(main())
