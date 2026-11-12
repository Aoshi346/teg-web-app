#!/usr/bin/env python3
"""verificar_precedentes.py — el catálogo de diseño no puede mentir sobre su evidencia.

Comprueba tres cosas distintas, y las tres han fallado alguna vez en este repo:

  1. Que cada precedente `ruta:línea` de `patterns/diseno/catalogo-diseno.yaml` RESUELVE:
     el fichero existe dentro del corpus y esa línea existe y no está vacía. Sin esto, el
     día que alguien recorte un fichero del corpus, el canon empieza a citar el vacío.

  2. Que el `estado` declarado cuadra con la evidencia CONTADA, no con la recordada:
       patron    ≥2 diseños DISTINTOS
       anecdota   1 diseño
       regla      cualquier número, pero exige `por_que_es_regla_y_no_patron` escrito
     Tres ficheros del mismo diseño NO son tres precedentes: son uno.

  3. Que los contraejemplos también resuelven. Un contraejemplo sin línea es una anécdota.

Desenlaces (rules/verification.md §«el instrumento que no puede medir debe ABORTAR»):
    0  medido, todo cuadra
    1  medido, hay fallos                → se listan uno a uno
    2  NO SE PUDO MEDIR (falta el corpus, el catálogo o el índice)

Uso:  python3 .claude/scripts/verificar_precedentes.py [--json]
"""
import json
import re
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[1]          # .claude/
CORPUS = RAIZ / "resources" / "referencias-diseno"
CATALOGO = RAIZ / "patterns" / "diseno" / "catalogo-diseno.yaml"
INDICE = CORPUS / "INDEX.json"

CITA = re.compile(r"^([\w./-]+\.(?:html|css|js)):(\d+)")


def abortar(motivo: str) -> None:
    print(f"⛔ NO SE PUDO MEDIR: {motivo}", file=sys.stderr)
    print("   No se imprime «todo en verde»: no haber podido mirar no es estar bien.", file=sys.stderr)
    sys.exit(2)


def cargar_yaml(ruta: Path):
    try:
        import yaml
    except ImportError:
        abortar("falta PyYAML (pip install pyyaml) — sin él no se puede leer el catálogo")
    return yaml.safe_load(ruta.read_text())


def diseno_de(ruta_rel: str, indice: dict) -> str:
    """A qué entrada del corpus pertenece un fichero. dale-marketing-v4/{html,css,js} = UN diseño."""
    for entrada in indice["entradas"]:
        base = entrada["ruta"].rsplit("/", 1)[0] if "/" in entrada["ruta"] else ""
        if ruta_rel == entrada["ruta"]:
            return entrada["id"]
        if base and base.count("/") >= 1 and ruta_rel.startswith(base + "/"):
            return entrada["id"]
    return f"(desconocido: {ruta_rel})"


def main() -> int:
    for f in (CORPUS, CATALOGO, INDICE):
        if not f.exists():
            abortar(f"no existe {f.relative_to(RAIZ)}")

    catalogo = cargar_yaml(CATALOGO)
    indice = json.loads(INDICE.read_text())
    fallos, avisos, comprobadas = [], [], 0

    for tec in catalogo["tecnicas"]:
        tid = tec["id"]
        disenos = set()

        citas = list(tec.get("precedentes", []))
        for campo in ("contraejemplo",):
            if tec.get(campo):
                citas.append(tec[campo])

        for cita in citas:
            m = CITA.match(cita)
            if not m:
                fallos.append(f"{tid}: «{cita[:60]}» no tiene forma `ruta:línea`")
                continue
            rel, num = m.group(1), int(m.group(2))
            fichero = CORPUS / rel
            comprobadas += 1
            if not fichero.exists():
                fallos.append(f"{tid}: {rel} no existe en el corpus")
                continue
            lineas = fichero.read_text(errors="ignore").split("\n")
            if num > len(lineas):
                fallos.append(f"{tid}: {rel}:{num} — el fichero solo tiene {len(lineas)} líneas")
                continue
            if not lineas[num - 1].strip():
                fallos.append(f"{tid}: {rel}:{num} — la línea está VACÍA")
                continue
            if cita in tec.get("precedentes", []):
                disenos.add(diseno_de(rel, indice))

        estado, n = tec["estado"], len(disenos)
        if estado == "patron" and n < 2:
            fallos.append(
                f"{tid}: declarada `patron` y solo aparece en {n} diseño(s) distinto(s) "
                f"({', '.join(sorted(disenos)) or 'ninguno'}) → es `anecdota`")
        elif estado == "anecdota" and n > 1:
            avisos.append(f"{tid}: declarada `anecdota` pero aparece en {n} diseños → puede subir a `patron`")
        elif estado == "regla" and not tec.get("por_que_es_regla_y_no_patron"):
            fallos.append(f"{tid}: declarada `regla` sin `por_que_es_regla_y_no_patron`")

    if "--json" in sys.argv:
        print(json.dumps({"estado_instrumento": "medido", "citas": comprobadas,
                          "tecnicas": len(catalogo["tecnicas"]),
                          "fallos": fallos, "avisos": avisos}, ensure_ascii=False, indent=1))
    else:
        print(f"verificar_precedentes · {len(catalogo['tecnicas'])} técnicas · {comprobadas} citas comprobadas")
        for a in avisos:
            print(f"  ⚠ {a}")
        if fallos:
            print("\nFALLOS:")
            for f in fallos:
                print(f"  ✗ {f}")
        else:
            print("  ✓ todas las citas resuelven y todos los estados cuadran con la evidencia contada")
    return 1 if fallos else 0


if __name__ == "__main__":
    sys.exit(main())
