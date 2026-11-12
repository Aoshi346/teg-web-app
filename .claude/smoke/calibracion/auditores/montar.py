#!/usr/bin/env python3
"""montar.py — arma un repo de calibración para Roberto y Pilar a partir del fixture.

El fixture tiene una base (mini Django de pedidos + pantalla React + grafo LangGraph) y dos
cambios del mismo encargo, con nombre neutro a propósito: uno lleva defectos plantados y el otro
es el control limpio. Cuál es cuál, y qué se plantó, lo dice la clave, que vive FUERA del repo
(`~/.claude/calibracion-diseno/{roberto,pilar}/`, denegada en `settings.json`): si el auditor
puede saberlo, la prueba no mide nada.

Lo que deja en <destino>:
  - un repo git con dos commits: «base» (código + `.docs/plans/ORD-7/plan.md`) y el cambio;
  - `cambio.diff` (el mismo diff, por si el auditor trabaja sin git);
  - con `--python <python con Django>`: `db.sqlite3` migrada y sembrada **en el estado base**
    (la copia sintética sobre la que Pilar mide; nadie migra el cambio).

Desenlaces: 0 montado · 2 no se pudo montar (falta el cambio, el destino no está vacío, git falla).

Uso:  python3 .claude/smoke/calibracion/auditores/montar.py <cambio-a|cambio-b> <destino> [--python <ruta>]
"""
import argparse
import shutil
import subprocess
import sys
from pathlib import Path

FIXTURE = Path(__file__).resolve().parent
GIT_ID = ["-c", "user.name=fixture", "-c", "user.email=fixture@example.invalid",
          "-c", "commit.gpgsign=false"]


def git(dest: Path, *args: str) -> str:
    out = subprocess.run(["git", "-C", str(dest), *GIT_ID, *args],
                         capture_output=True, text=True)
    if out.returncode != 0:
        print(f"⛔ git {' '.join(args)} falló:\n{out.stderr}", file=sys.stderr)
        sys.exit(2)
    return out.stdout.strip()


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("cambio", choices=["cambio-a", "cambio-b"])
    ap.add_argument("destino", type=Path)
    ap.add_argument("--python", help="python con Django para sembrar la sqlite en estado base")
    a = ap.parse_args()

    cambio = FIXTURE / a.cambio
    dest = a.destino.resolve()
    if dest.exists() and any(dest.iterdir()):
        print(f"⛔ NO SE PUDO MONTAR: {dest} no está vacío", file=sys.stderr)
        return 2

    shutil.copytree(FIXTURE / "base", dest, dirs_exist_ok=True,
                    ignore=shutil.ignore_patterns("__pycache__", "db.sqlite3"))
    plan_dir = dest / ".docs" / "plans" / "ORD-7"
    plan_dir.mkdir(parents=True)
    shutil.copy(cambio / "PLAN.md", plan_dir / "plan.md")

    if a.python:
        for cmd in (["migrate", "-v0"], ["loaddata", "seed", "-v0"]):
            r = subprocess.run([a.python, "manage.py", *cmd], cwd=dest, capture_output=True, text=True)
            if r.returncode != 0:
                print(f"⛔ manage.py {' '.join(cmd)} falló:\n{r.stderr}", file=sys.stderr)
                return 2

    git(dest, "init", "-q", "-b", "main")
    git(dest, "add", "-A")
    git(dest, "commit", "-q", "-m", "base: pedidos, pantalla y bot")
    base_sha = git(dest, "rev-parse", "HEAD")

    for f in cambio.rglob("*"):
        if f.is_file() and f.name != "PLAN.md" and "__pycache__" not in f.parts:
            target = dest / f.relative_to(cambio)
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy(f, target)
    git(dest, "add", "-A")
    git(dest, "commit", "-q", "-m", "ORD-7: filtro de pendientes y estado de pedido en el bot")
    (dest / "cambio.diff").write_text(git(dest, "diff", base_sha, "HEAD") + "\n")
    # Fuera del árbol versionado: no ensucia el diff que audita Roberto.
    with open(dest / ".git" / "info" / "exclude", "a") as fh:
        fh.write("cambio.diff\n")

    print(f"repo     {dest}")
    print(f"base_sha {base_sha}")
    print(f"plan     {plan_dir / 'plan.md'}")
    print(f"sqlite   {'sembrada en estado base' if a.python else 'no (sin --python)'}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
