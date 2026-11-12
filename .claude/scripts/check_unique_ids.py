#!/usr/bin/env python3
"""check_unique_ids.py — ¿hay dos tareas o dos items con el mismo id?

POR QUÉ (AN-24, cosechado de cold_calling_coach). Allí se colaron dos tareas `W1.08`. Nada falló a
la vista: el informe salió con todas. Lo que se rompe es más caro: el informe empareja las decisiones
del Usuario con los items POR ID, así que una decisión puede pegarse al item equivocado y el informe
dirá que aprobó algo que no miró. Y un `blocks:` hacia un id repetido apunta a los dos.

Mira, bajo la raíz:
  · `.specify/sessions/*/tasks.md` y los `dashboard.md`/`tasks.md` de `.docs/plans/*/`: el id de una
    tarea es el primer `código` de su línea de casilla (lo mismo que lee `tasks_to_items.py`);
  · `.docs/plans/*/report.json`: el campo `id` de `items` (o de la lista raíz).

Uso:
    check_unique_ids.py [--root .]      # exit 0 sin repetidos · 1 con repetidos o un JSON ilegible
    check_unique_ids.py --self-test
"""
from __future__ import annotations

import argparse
import glob
import json
import os
import re
import sys
import tempfile
from collections import Counter

BOX_ID = re.compile(r"^\s*[-*]\s*\[[ xX>!]\]\s*.*?`([^`]+)`")


def ids_md(path: str) -> list[str]:
    with open(path, encoding="utf-8") as f:
        return [m.group(1) for ln in f if (m := BOX_ID.match(ln))]


def ids_json(path: str) -> list[str]:
    with open(path, encoding="utf-8") as f:
        data = json.load(f)
    items = data.get("items", []) if isinstance(data, dict) else data
    return [x.get("id") for x in items if isinstance(x, dict) and x.get("id")]


def scan(root: str) -> tuple[int, list[str]]:
    lines, fails = [], 0
    md = sorted(set(glob.glob(os.path.join(root, ".specify/sessions/*/tasks.md"))
                    + glob.glob(os.path.join(root, ".docs/plans/*/dashboard.md"))
                    + glob.glob(os.path.join(root, ".docs/plans/*/tasks.md"))))
    js = sorted(glob.glob(os.path.join(root, ".docs/plans/*/report.json")))
    for path, reader, unit in [(p, ids_md, "tareas") for p in md] + [(p, ids_json, "items") for p in js]:
        rel = os.path.relpath(path, root)
        try:
            ids = reader(path)
        except (OSError, ValueError) as e:
            fails += 1
            lines.append(f"✗ {rel}: no se puede leer ({e})")
            continue
        dup = {i: n for i, n in Counter(ids).items() if n > 1}
        if dup:
            fails += 1
            lines.append(f"✗ {rel}: ids repetidos → {dup}")
        else:
            lines.append(f"✓ {rel}: {len(ids)} {unit}, ningún id repetido")
    return fails, lines


def self_test() -> int:
    d = tempfile.mkdtemp()
    os.makedirs(os.path.join(d, ".specify/sessions/S1"))
    os.makedirs(os.path.join(d, ".docs/plans/p1"))
    with open(os.path.join(d, ".specify/sessions/S1/tasks.md"), "w") as f:
        f.write("- [ ] `W1.08` grabador\n- [x] `W1.09` x\n")
    with open(os.path.join(d, ".docs/plans/p1/report.json"), "w") as f:
        json.dump({"items": [{"id": "A-1"}, {"id": "A-2"}]}, f)
    f0, _ = scan(d)
    with open(os.path.join(d, ".specify/sessions/S1/tasks.md"), "a") as f:
        f.write("  - [ ] `W1.08` lienzo\n")
    f1, l1 = scan(d)
    ok = f0 == 0 and f1 == 1 and any("W1.08" in x for x in l1)
    print(f"  {'✓' if f0 == 0 else '✗'} sin repetidos → 0 fallos")
    print(f"  {'✓' if f1 == 1 else '✗'} W1.08 plantado dos veces → 1 fallo")
    print("self-test:", "OK" if ok else "FALLO")
    return 0 if ok else 1


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--root", default=".")
    ap.add_argument("--self-test", action="store_true")
    a = ap.parse_args()
    if a.self_test:
        return self_test()
    fails, lines = scan(a.root)
    print("\n".join(lines) or "· nada que mirar (ni tasks.md ni report.json)")
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main())
