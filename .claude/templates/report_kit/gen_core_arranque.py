#!/usr/bin/env python3
"""core-arranque.html — la guía de arranque, como capa PERMANENTE del Core.

POR QUE EN EL CORE. `ARRANQUE.md` vive en `patterns/stack/` y se copió a `sources/` de un
plan para que se viera ya. Pero **cómo se monta un proyecto nuevo es de lo más permanente
que hay**: no debe morir cuando ese plan se cierre (regla 5a de `rules/report-kit.md`).

Se RENDERIZA desde la misma fuente, no se duplica: duplicarla a mano la haría divergir del
patrón en el primer cambio, que es exactamente el fallo que este kit evita en todas partes.

USO (misma firma que los demás generadores del core; lo llama build.py):
    python3 gen_core_arranque.py <plan-dir> --out <.docs/core>

OJO si lo corres suelto: escribe la página SIN topnav, igual que sus hermanos. Quien la
pinta es `render_nav.py --scope core`, y build.py lo llama después.
"""
import argparse, subprocess, sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
from md_to_html import render_file        # noqa: E402


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("plan")
    ap.add_argument("--out", required=True)
    a = ap.parse_args()
    plan, out = Path(a.plan).resolve(), Path(a.out).resolve()
    out.mkdir(parents=True, exist_ok=True)

    repo = subprocess.run(["git", "-C", str(plan), "rev-parse", "--show-toplevel"],
                          capture_output=True, text=True).stdout.strip()
    if not repo:
        print("core-arranque: no estamos en un repo git", file=sys.stderr)
        return 1
    fuente = Path(repo) / ".claude" / "patterns" / "stack" / "ARRANQUE.md"
    if not fuente.exists():
        print(f"core-arranque: falta {fuente} — nada que renderizar", file=sys.stderr)
        return 1

    destino = out / "core-arranque.html"
    render_file(str(fuente), str(destino), title="Cómo se monta un proyecto")
    print(f"OK {destino} — desde {fuente.relative_to(repo)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
