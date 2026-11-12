#!/usr/bin/env python3
"""module_split.py — ¿el reparto por módulos aguanta antes de abrir N frentes?

POR QUÉ (AN-D6, fábrica de módulos de accounting_AMC: 8 módulos en paralelo, 11-09). Repartir por
módulos falla por lo que no se ve: los ficheros que TODOS tocan. Allí, los siete más editados en 120
commits eran registros compartidos (contrato de la API, consultas, tipos, rutas, mocks, CSS); ocho
worktrees contra eso son conflictos de ocho vías. La regla que lo evita es un reparto ESCRITO: cada
fichero caliente es del padre o de un solo módulo. Esto lo comprueba antes de lanzar nada.

El reparto, en el proyecto: `.claude/modules.json`
    {"parent": ["src/types/api.ts", "src/routes.tsx", "package.json", "pyproject.toml", ".claude/**"],
     "modules": {"clients": ["backend/apps/clients/**", "src/pages/Client*.tsx"],
                 "billing": ["backend/apps/billing/**", "src/pages/Invoice*.tsx"]}}
Globs con `fnmatch` (el `*` cruza carpetas). Un fichero del padre lo edita solo la sesión padre; un
módulo que lo necesita lo PIDE y sigue con otra cosa.

Qué sale (exit 1 si hay alguno de los dos primeros):
  SOLAPE      un fichero del repo que reclaman dos módulos              → conflicto seguro
  SIN DUEÑO   un fichero caliente (top N de `git log --name-only`) que no es del padre
              ni de ningún módulo                                        → el próximo registro compartido
  caliente    la tabla de los más tocados, con su dueño                  → informativo

Uso:
    module_split.py [--config .claude/modules.json] [--commits 200] [--top 15] [--root .]
    module_split.py --measure [--commits 200]     # solo la tabla de calientes, sin reparto
    module_split.py --self-test
Puertos, base de datos y Redis por módulo: `scripts/franja.py` (no se duplica aquí).
"""
from __future__ import annotations

import argparse
import collections
import fnmatch
import json
import os
import subprocess
import sys
import tempfile


def git(root: str, *args: str) -> str:
    r = subprocess.run(["git", "-C", root, "-c", "core.quotePath=false", *args],
                       capture_output=True, text=True, env={**os.environ, "GIT_OPTIONAL_LOCKS": "0"})
    if r.returncode != 0:
        raise RuntimeError(r.stderr.strip() or "git falló")
    return r.stdout


def hot_files(root: str, commits: int) -> collections.Counter:
    log = git(root, "log", f"-n{commits}", "--no-merges", "--name-only", "--pretty=format:")
    tracked = set(git(root, "ls-files").splitlines())
    return collections.Counter(ln for ln in log.splitlines() if ln and ln in tracked)


def owners(path: str, cfg: dict) -> list[str]:
    who = ["padre"] if any(fnmatch.fnmatch(path, g) for g in cfg.get("parent", [])) else []
    who += [m for m, globs in cfg.get("modules", {}).items() if any(fnmatch.fnmatch(path, g) for g in globs)]
    return who


def analyse(root: str, cfg: dict, commits: int, top: int) -> dict:
    tracked = git(root, "ls-files").splitlines()
    overlap = {}
    for p in tracked:
        mods = [m for m in owners(p, cfg) if m != "padre"]
        if len(mods) > 1:
            overlap[p] = mods
    hot = hot_files(root, commits).most_common(top)
    rows = [{"fichero": p, "commits": n, "dueño": owners(p, cfg)} for p, n in hot]
    orphan = [r["fichero"] for r in rows if not r["dueño"]]
    return {"solape": overlap, "sin_dueño": orphan, "calientes": rows}


def report(res: dict) -> int:
    print("Ficheros más tocados y su dueño:")
    for r in res["calientes"]:
        d = ", ".join(r["dueño"]) or "— SIN DUEÑO"
        print(f"  {r['commits']:>4}  {r['fichero']}  → {d}")
    for p, mods in sorted(res["solape"].items()):
        print(f"✗ SOLAPE {p}: lo reclaman {', '.join(mods)} → dueño único (padre) o se parte antes")
    for p in res["sin_dueño"]:
        print(f"✗ SIN DUEÑO {p}: caliente y sin dueño en el reparto → al padre, o a un módulo con nombre")
    bad = len(res["solape"]) + len(res["sin_dueño"])
    print("✓ el reparto aguanta" if not bad else f"{bad} problema(s) antes de repartir")
    return 1 if bad else 0


def self_test() -> int:
    d = tempfile.mkdtemp()

    def g(*a):
        subprocess.run(["git", "-C", d, *a], check=True, capture_output=True)

    def w(rel, text):
        os.makedirs(os.path.dirname(os.path.join(d, rel)) or d, exist_ok=True)
        with open(os.path.join(d, rel), "a") as f:
            f.write(text)

    g("init", "-q")
    g("config", "user.email", "t@t")
    g("config", "user.name", "t")
    for i in range(6):
        w("src/api.ts", f"// {i}\n")
        w(f"apps/{'a' if i % 2 else 'b'}/x.py", f"# {i}\n")
        g("add", ".")
        g("commit", "-qm", f"c{i}")
    w("apps/shared/util.py", "x\n")
    g("add", ".")
    g("commit", "-qm", "shared")
    cfg = {"parent": [], "modules": {"a": ["apps/a/**", "apps/shared/**"], "b": ["apps/b/**", "apps/shared/**"]}}
    r1 = analyse(d, cfg, 50, 5)
    cfg2 = {"parent": ["src/api.ts"], "modules": {"a": ["apps/a/**", "apps/shared/**"], "b": ["apps/b/**"]}}
    r2 = analyse(d, cfg2, 50, 5)
    checks = [
        ("apps/shared reclamado por a y b → SOLAPE", "apps/shared/util.py" in r1["solape"]),
        ("src/api.ts caliente y sin dueño → SIN DUEÑO", "src/api.ts" in r1["sin_dueño"]),
        ("api.ts al padre y shared a un módulo → el reparto aguanta", not r2["solape"] and not r2["sin_dueño"]),
        ("el más tocado es src/api.ts (6 commits)", r1["calientes"][0] == {"fichero": "src/api.ts", "commits": 6, "dueño": []}),
    ]
    failures = 0
    for n, ok in checks:
        failures += not ok
        print(f"  {'✓' if ok else '✗'} {n}")
    print("self-test:", "OK" if not failures else f"{failures} FALLO(S)")
    return 1 if failures else 0


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--root", default=".")
    ap.add_argument("--config", default=None)
    ap.add_argument("--commits", type=int, default=200)
    ap.add_argument("--top", type=int, default=15)
    ap.add_argument("--measure", action="store_true")
    ap.add_argument("--self-test", action="store_true")
    a = ap.parse_args()
    if a.self_test:
        return self_test()
    try:
        if a.measure:
            for p, n in hot_files(a.root, a.commits).most_common(a.top):
                print(f"{n:>5}  {p}")
            return 0
        path = a.config or os.path.join(a.root, ".claude", "modules.json")
        with open(path, encoding="utf-8") as f:
            cfg = json.load(f)
        return report(analyse(a.root, cfg, a.commits, a.top))
    except (OSError, ValueError, RuntimeError) as e:
        print(f"✗ no se pudo medir: {e}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(main())
