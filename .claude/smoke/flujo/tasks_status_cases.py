#!/usr/bin/env python3
"""Quién manda en `status` al regenerar el informe (MO-D5, sub-ola 2.14).

Decisión del Usuario (18-10): el status lo manda tasks.md / dashboard.md, salvo que el Usuario lo
haya cambiado a mano en el dashboard. Cada caso monta un plan de juguete, regenera con
`tasks_to_items.py`, simula lo que guardaría el dashboard (server.py reescribe `items` y conserva
`meta`) y vuelve a regenerar.

    python3 tasks_status_cases.py <tasks_to_items.py>      # exit 0 si todos dan lo esperado

Con el `tasks_to_items.py` de antes de la 2.14 fallan A y G (el fichero no llegaba al informe).
"""
from __future__ import annotations

import json
import subprocess
import sys
import tempfile
from pathlib import Path


def write_tasks(plan: Path, box: str) -> None:
    (plan / "dashboard.md").write_text(f"# Plan\n## Página\n- [{box}] `T-1` Una tarea\n",
                                       encoding="utf-8")


def generate(script: str, plan: Path) -> None:
    subprocess.run([sys.executable, script, str(plan)], check=True, capture_output=True)


def report(plan: Path) -> dict:
    return json.loads((plan / "report.json").read_text(encoding="utf-8"))


def set_by_hand(plan: Path, status: str, drop_meta: bool = False) -> None:
    """Lo que hace server.py al guardar desde el kanban: reescribe items, conserva meta."""
    data = report(plan)
    data["items"][0]["status"] = status
    if drop_meta:
        data["meta"].pop("tasks_status", None)
    (plan / "report.json").write_text(json.dumps(data), encoding="utf-8")


def run_case(script: str, first: str, by_hand: str | None, second: str,
             drop_meta: bool = False) -> str:
    with tempfile.TemporaryDirectory() as d:
        plan = Path(d)
        write_tasks(plan, first)
        generate(script, plan)
        if by_hand:
            set_by_hand(plan, by_hand, drop_meta)
        write_tasks(plan, second)
        generate(script, plan)
        return report(plan)["items"][0]["status"]


# id · descripción · casilla 1 · cambio a mano · casilla 2 · esperado · sin meta.tasks_status
CASES = [
    ("A", "el autor pasa [ ] a [>] y nadie lo tocó: gana el fichero", " ", None, ">", "doing", False),
    ("B", "el autor marca [x]: gana el fichero", " ", None, "x", "done", False),
    ("C", "el Usuario lo movió a review y el fichero no cambió: se conserva", " ", "review", " ",
     "review", False),
    ("D", "el Usuario lo movió a review y el autor pone [>]: gana el Usuario", " ", "review", ">",
     "review", False),
    ("E", "el Usuario lo movió a review y el autor marca [x]: gana el [x] nuevo", " ", "review", "x",
     "done", False),
    ("F", "report.json de antes (sin la foto) y movido a doing: regla vieja, se conserva", " ",
     "doing", " ", "doing", True),
    ("G", "el autor desmarca [x] a [ ] y nadie lo tocó: gana el fichero", "x", None, " ",
     "backlog", False),
]


def main() -> int:
    if len(sys.argv) != 2:
        print(__doc__)
        return 2
    script = sys.argv[1]
    bad = 0
    for cid, desc, first, by_hand, second, want, drop in CASES:
        got = run_case(script, first, by_hand, second, drop)
        ok = got == want
        bad += not ok
        print(f"  {'✓' if ok else '✗'} {cid} {desc} → {got}" + ("" if ok else f" (esperaba {want})"))
    print(f"{len(CASES) - bad}/{len(CASES)} correctos")
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
