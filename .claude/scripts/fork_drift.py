#!/usr/bin/env python3
"""fork_drift.py — ¿en qué ficheros va un fork por DETRÁS de su original?

POR QUÉ (AN-17). Un fork de un proyecto (una vertical nueva sacada del demo, una copia de referencia,
un worktree que vive semanas) diverge a propósito, y por eso nadie lo compara: revisarlo a mano no
ocurre y fusionar solo es peligroso. Medido el 17-10 en un fork de un mes: le faltaban la traza por
turno, la máscara de datos personales de las trazas, el guardián de repeticiones y el simulador, y
dos ADR suyos describían código que no tenía. Esto no fusiona nada: lista, fichero a fichero, qué
arreglos del original no han llegado.

Reutiliza el clasificador de `template_diff.py` (la misma pregunta, con el template como original):
  FALTA        está en el original y no en el fork                                → ¿portar?
  ATRASADO     el fork tiene una versión VIEJA del original (git lo sabe)         → portar sin miedo
  DIVERGENTE   los dos cambiaron: el fork nunca tuvo la versión actual            → merge a mano
  ADAPTADO     el fork tuvo la versión actual del original y la cambió después   → bien (informativo)
  SIN HISTORIA el original no tiene git: no se puede saber quién va detrás        → mirar a mano
Lo que solo está en el fork se cuenta, no se lista.

Uso:
    fork_drift.py <original> <fork> [--ruta backend/apps/agents --ruta docs/adr] [--ignora '*.lock']
    fork_drift.py <original> <fork> --json
    fork_drift.py --self-test
Exit: 0 nada por detrás · 1 hay FALTA, ATRASADO o DIVERGENTE · 2 una ruta no existe.
Solo lee: git se consulta sin tomar candados (`GIT_OPTIONAL_LOCKS=0`, el de `template_diff.py`).
"""
from __future__ import annotations

import argparse
import fnmatch
import importlib.util
import json
import os
import subprocess
import sys
import tempfile

_spec = importlib.util.spec_from_file_location(
    "template_diff", os.path.join(os.path.dirname(os.path.abspath(__file__)), "template_diff.py"))
td = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(td)

SKIP_DIRS = {".git", "__pycache__", "node_modules", ".venv", "venv", ".mypy_cache", ".pytest_cache",
             "dist", "build", ".next", "worktrees"}
LABEL = {"atrasado": "ATRASADO", "divergente": "DIVERGENTE", "local_posterior": "ADAPTADO",
         "sin_historia": "SIN HISTORIA"}


def files_under(base: str, ignore: list[str]) -> set[str]:
    out = set()
    for dp, dns, fns in os.walk(base):
        dns[:] = [d for d in dns if d not in SKIP_DIRS]
        for fn in fns:
            rel = os.path.relpath(os.path.join(dp, fn), base)
            if fn.endswith((".pyc", ".pyo")) or any(fnmatch.fnmatch(rel, g) for g in ignore):
                continue
            out.add(rel)
    return out


def compare(orig: str, fork: str, rutas: list[str], ignore: list[str]) -> dict:
    res = {"original": orig, "fork": fork, "rutas": [], "solo_fork": 0}
    for r in rutas:
        bo, bf = os.path.join(orig, r), os.path.join(fork, r)
        if not os.path.isdir(bo):
            raise FileNotFoundError(f"no existe en el original: {bo}")
        fo = files_under(bo, ignore)
        ff = files_under(bf, ignore) if os.path.isdir(bf) else set()
        ho, hf = td.Historia(bo), td.Historia(bf) if os.path.isdir(bf) else None
        rows = []
        for rel in sorted(fo):
            po, pf = os.path.join(bo, rel), os.path.join(bf, rel)
            if rel not in ff:
                rows.append({"fichero": os.path.join(r, rel), "tipo": "FALTA"})
                continue
            if td.blob_id(po) == td.blob_id(pf):
                continue
            c = td.clasificar(rel, po, ho, rel, pf, hf)
            rows.append({"fichero": os.path.join(r, rel), "tipo": LABEL[c["tipo"]],
                          "original": c["template"], "fork": c["local"]})
        res["solo_fork"] += len(ff - fo)
        res["rutas"].append({"ruta": r, "filas": rows})
    return res


def behind(res: dict) -> int:
    return sum(f["tipo"] in ("FALTA", "ATRASADO", "DIVERGENTE") for r in res["rutas"] for f in r["filas"])


def show(res: dict) -> None:
    print(f"original {res['original']}\nfork     {res['fork']}")
    order = ["FALTA", "ATRASADO", "DIVERGENTE", "SIN HISTORIA", "ADAPTADO"]
    for r in res["rutas"]:
        rows = sorted(r["filas"], key=lambda f: (order.index(f["tipo"]), f["fichero"]))
        print(f"\n· {r['ruta']}: {len(rows)} distintos")
        for f in rows:
            dates = f"  (original {f['original']} · fork {f['fork']})" if "original" in f else ""
            print(f"  {f['tipo']:<12} {f['fichero']}{dates}")
    n = behind(res)
    print(f"\n{n} fichero(s) en los que el fork va por detrás o diverge · {res['solo_fork']} solo en el fork")


def self_test() -> int:
    d = tempfile.mkdtemp()
    o, f = os.path.join(d, "orig"), os.path.join(d, "fork")

    def g(cwd, *a):
        subprocess.run(["git", "-C", cwd, *a], check=True, capture_output=True)

    def w(path, text):
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "w") as fh:
            fh.write(text)

    os.makedirs(o)
    g(o, "init", "-q")
    g(o, "config", "user.email", "t@t")
    g(o, "config", "user.name", "t")
    for n in ("a", "d", "e", "f"):
        w(os.path.join(o, "agent", f"{n}.py"), f"{n} v1\n")
    g(o, "add", ".")
    g(o, "commit", "-qm", "v1")
    subprocess.run(["git", "clone", "-q", o, f], check=True, capture_output=True)
    g(f, "config", "user.email", "t@t")
    g(f, "config", "user.name", "t")
    w(os.path.join(o, "agent", "a.py"), "a v2: el arreglo\n")
    w(os.path.join(o, "agent", "b.py"), "b nuevo: pii_mask\n")
    w(os.path.join(o, "agent", "d.py"), "d v2 del original\n")
    g(o, "add", ".")
    g(o, "commit", "-qm", "v2")
    w(os.path.join(f, "agent", "d.py"), "d v1 cambiado en el fork\n")
    w(os.path.join(f, "agent", "f.py"), "f adaptado al fork\n")
    w(os.path.join(f, "agent", "c.py"), "solo del fork\n")
    g(f, "add", ".")
    g(f, "commit", "-qm", "fork")
    res = compare(o, f, ["agent"], [])
    got = {os.path.basename(x["fichero"]): x["tipo"] for x in res["rutas"][0]["filas"]}
    want = {"a.py": "ATRASADO", "b.py": "FALTA", "d.py": "DIVERGENTE", "f.py": "ADAPTADO"}
    failures = 0
    for k, v in want.items():
        failures += got.get(k) != v
        print(f"  {'✓' if got.get(k) == v else '✗'} {k}: {got.get(k)} (esperado {v})")
    ok_same = "e.py" not in got
    print(f"  {'✓' if ok_same else '✗'} e.py igual en los dos → no sale")
    ok_fork_only = res["solo_fork"] == 1
    print(f"  {'✓' if ok_fork_only else '✗'} c.py solo en el fork → se cuenta ({res['solo_fork']})")
    failures += (not ok_same) + (not ok_fork_only) + (behind(res) != 3)
    print("self-test:", "OK" if not failures else f"{failures} FALLO(S)")
    return 1 if failures else 0


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("original", nargs="?")
    ap.add_argument("fork", nargs="?")
    ap.add_argument("--ruta", action="append", default=[])
    ap.add_argument("--ignora", action="append", default=[])
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--self-test", action="store_true")
    a = ap.parse_args()
    if a.self_test:
        return self_test()
    if not (a.original and a.fork):
        ap.error("faltan <original> y <fork>")
    try:
        res = compare(os.path.abspath(a.original), os.path.abspath(a.fork), a.ruta or ["."], a.ignora)
    except FileNotFoundError as e:
        print(f"✗ {e}", file=sys.stderr)
        return 2
    if a.json:
        print(json.dumps(res, ensure_ascii=False, indent=2))
    else:
        show(res)
    return 1 if behind(res) else 0


if __name__ == "__main__":
    sys.exit(main())
