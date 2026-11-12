#!/usr/bin/env python3
"""traer_referencias.py — reconstruye los cuerpos de referencia desde el manifiesto.

El CODIGO de los cuerpos no se versiona (219 MB entre todos). Lo que el repo guarda es
`.claude/patterns/referencia/procedencia.json`: remote + sha por cuerpo. Con eso se reconstruye
cada uno AL COMMIT EXACTO, que es mas preciso que guardar el codigo suelto.

  --check     (default) solo dice que hay, que falta y que esta en otro sha. NO toca nada.
  --traer     clona lo que falte. NUNCA pisa lo que ya existe: si esta en otro sha, avisa.
  --solo <id> limita la operacion a un cuerpo.

Por que no hay --force: pisar un cuerpo que alguien tiene a medio mirar es justo el fallo que
un manifiesto existe para evitar. Si hay que rehacerlo, se borra a mano y se vuelve a traer.
"""
from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[2]
MANIFIESTO = RAIZ / ".claude" / "patterns" / "referencia" / "procedencia.json"


def sha_de(ruta: Path) -> str | None:
    """El sha corto de un repo, o None si no es un repo git POR SI MISMO.

    `git -C` sube por el arbol hasta encontrar un repo, asi que un directorio dentro del
    template devolveria el sha del template — un dato falso que ademas parece fechado.
    """
    top = subprocess.run(["git", "-C", str(ruta), "rev-parse", "--show-toplevel"],
                         capture_output=True, text=True).stdout.strip()
    if not top or Path(top).resolve() != ruta.resolve():
        return None
    return subprocess.run(["git", "-C", str(ruta), "rev-parse", "--short", "HEAD"],
                          capture_output=True, text=True).stdout.strip() or None


def clonar(remote: str, destino: Path, sha: str | None, rama: str | None) -> tuple[bool, str]:
    destino.parent.mkdir(parents=True, exist_ok=True)
    cmd = ["git", "clone", "--quiet"]
    if rama:
        cmd += ["--branch", rama]
    cmd += [remote, str(destino)]
    r = subprocess.run(cmd, capture_output=True, text=True)
    if r.returncode != 0:
        return False, (r.stderr or "").strip().splitlines()[-1] if r.stderr else "clone fallo"
    if sha:
        c = subprocess.run(["git", "-C", str(destino), "checkout", "--quiet", sha],
                           capture_output=True, text=True)
        if c.returncode != 0:
            return False, f"clonado, pero el checkout a {sha} fallo"
    return True, "ok"


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--traer", action="store_true", help="clona lo que falte (por defecto solo informa)")
    ap.add_argument("--solo", metavar="ID", help="limitar a un cuerpo")
    a = ap.parse_args()

    if not MANIFIESTO.is_file():
        print(f"✗ no existe {MANIFIESTO}", file=sys.stderr)
        return 1
    man = json.loads(MANIFIESTO.read_text(encoding="utf-8"))
    cuerpos = man["cuerpos"] + man.get("nuestros_proyectos", [])
    if a.solo:
        cuerpos = [c for c in cuerpos if c["id"] == a.solo]
        if not cuerpos:
            print(f"✗ no hay ningun cuerpo con id '{a.solo}'", file=sys.stderr)
            return 1

    faltan, distintos, ok = [], [], []
    for c in cuerpos:
        ruta = RAIZ / c["ruta"]
        if not ruta.is_dir():
            faltan.append(c)
            continue
        actual, esperado = sha_de(ruta), c.get("sha")
        if esperado and actual and not esperado.startswith(actual) and not actual.startswith(esperado):
            distintos.append((c, actual))
        else:
            ok.append(c)

    print(f"manifiesto: {len(cuerpos)} cuerpos · medido {man.get('medido','?')}\n")
    if ok:
        print(f"✓ EN DISCO Y AL DIA ({len(ok)})")
        for c in ok:
            print(f"    {c['id']:<28} {c.get('sha') or '(sin sha declarado)'}")
    if distintos:
        print(f"\n⚠ EN OTRO SHA ({len(distintos)}) — NO se tocan; decide tu")
        for c, actual in distintos:
            print(f"    {c['id']:<28} disco={actual}  manifiesto={c['sha']}")
    if faltan:
        print(f"\n✗ FALTAN ({len(faltan)})")
        for c in faltan:
            priv = " [PRIVADO — hace falta acceso]" if c.get("privado") else ""
            print(f"    {c['id']:<28} {c['remote']}{priv}")
            if c.get("nota"):
                print(f"      nota: {c['nota'][:100]}")

    if not a.traer:
        if faltan:
            print(f"\n→ para traerlos: python3 {Path(__file__).name} --traer")
        return 0

    if not faltan:
        print("\nnada que traer.")
        return 0
    print(f"\ntrayendo {len(faltan)}…")
    fallos = 0
    for c in faltan:
        destino = RAIZ / c["ruta"]
        bien, msg = clonar(c["remote"], destino, c.get("sha"), c.get("rama"))
        print(f"  {'✓' if bien else '✗'} {c['id']:<28} {msg}")
        fallos += 0 if bien else 1
    if fallos:
        print(f"\n{fallos} fallaron. Los PRIVADOS necesitan acceso al remote; no es un bug del script.")
    return 1 if fallos else 0


if __name__ == "__main__":
    sys.exit(main())
