#!/usr/bin/env python3
"""sabotage.py — el control negativo hecho paso: rompe el código a propósito y exige que la suite se entere.

POR QUÉ (AN-24, cosechado de cold_calling_coach, que tiene cuatro `sabotaje_*.py`). `code-review-gate`
y `verification.md` piden «verlo fallar»: plantar una violación y comprobar que el test la caza. Pedirlo
en una rúbrica depende de que alguien lo haga; un arnés lo convierte en un comando. Si ningún sabotaje
pone la suite en rojo, los tests miran la forma y no el comportamiento.

Un fichero de sabotajes por suite (JSON, versionado junto a los tests):

    {
      "suite": ["python3", "-m", "pytest", "tests/test_metrics.py", "-q"],
      "cwd": ".",
      "sabotages": [
        {"name": "control — cambio equivalente", "file": "app/metrics.py",
         "find": "if not rows:", "replace": "if len(rows) == 0:", "control": true,
         "why": "si esto rompe, los tests miran la forma y no el comportamiento"},
        {"name": "el ratio pierde el denominador", "file": "app/metrics.py",
         "find": "return hits / total", "replace": "return hits", "why": "un 65 % sin base es medio dato"}
      ]
    }

Cada sabotaje cambia la PRIMERA aparición de `find` por `replace`, corre la suite y restaura el
fichero (también si el proceso revienta: copia en `<fichero>.sabotage-bak`, y si al empezar queda una
de una ejecución anterior, aborta antes de tocar nada). Uno «control» tiene que seguir en VERDE; el
resto tiene que poner la suite en ROJO.

Uso:
    sabotage.py <sabotajes.json>          # exit 0 todos cazados · 1 alguno escapó, obsoleto o suite roja
    sabotage.py <sabotajes.json> --json
    sabotage.py --self-test
RAM: la suite es la del módulo, nunca la entera (`ram-pytest.md`); el arnés la corre una vez por sabotaje.
"""
from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
import tempfile


def green(suite: list[str], cwd: str, timeout: int) -> bool:
    r = subprocess.run(suite, cwd=cwd, capture_output=True, text=True, timeout=timeout)  # noqa: S603
    return r.returncode == 0


def run_spec(spec_path: str, timeout: int = 600) -> dict:
    with open(spec_path, encoding="utf-8") as f:
        spec = json.load(f)
    base = os.path.dirname(os.path.abspath(spec_path))
    cwd = os.path.normpath(os.path.join(base, spec.get("cwd", ".")))
    suite = spec["suite"]
    out = {"spec": spec_path, "baseline_green": None, "results": []}
    sabs = spec.get("sabotages", [])
    for s in sabs:
        bak = os.path.join(cwd, s["file"]) + ".sabotage-bak"
        if os.path.exists(bak):
            out["error"] = f"queda {bak} de una ejecución anterior: restaura el fichero a mano y bórrala"
            return out
    out["baseline_green"] = green(suite, cwd, timeout)
    if not out["baseline_green"]:
        out["error"] = "la suite ya está en ROJO sin sabotear: arréglala antes de medir nada"
        return out
    for s in sabs:
        path = os.path.join(cwd, s["file"])
        control = bool(s.get("control"))
        res = {"name": s["name"], "control": control, "why": s.get("why", "")}
        try:
            with open(path, encoding="utf-8") as f:
                original = f.read()
        except OSError as e:
            res.update(status="obsoleto", detail=f"no se puede leer {s['file']}: {e}")
            out["results"].append(res)
            continue
        if s["find"] not in original:
            res.update(status="obsoleto", detail="el texto a sabotear ya no existe")
            out["results"].append(res)
            continue
        bak = path + ".sabotage-bak"
        shutil.copy2(path, bak)
        try:
            with open(path, "w", encoding="utf-8") as f:
                f.write(original.replace(s["find"], s["replace"], 1))
            still_green = green(suite, cwd, timeout)
        finally:
            shutil.copy2(bak, path)
            os.remove(bak)
        ok = still_green if control else not still_green
        res["status"] = "ok" if ok else ("control-rompio" if control else "escapo")
        out["results"].append(res)
    return out


def report(out: dict) -> int:
    print(f"sabotajes de {out['spec']}")
    if out.get("error"):
        print(f"✗ {out['error']}")
        return 1
    bad = 0
    for r in out["results"]:
        mark = "✓" if r["status"] == "ok" else "✗"
        bad += r["status"] != "ok"
        tag = "[control] " if r["control"] else ""
        print(f"  {mark} {tag}{r['name']}" + ("" if r["status"] == "ok" else f" — {r['status']}: {r.get('detail') or r['why']}"))
    total = len(out["results"])
    print(f"{total - bad}/{total} como se esperaba")
    return 1 if bad else 0


def self_test() -> int:
    d = tempfile.mkdtemp()
    os.makedirs(os.path.join(d, "app"))
    with open(os.path.join(d, "app", "metrics.py"), "w") as f:
        f.write("def ratio(hits, total):\n    if not total:\n        return 0.0\n    return hits / total\n\n"
                "def label(x):\n    return 'alto' if x > 0.5 else 'bajo'\n")
    with open(os.path.join(d, "test_metrics.py"), "w") as f:
        f.write("import unittest\nfrom app.metrics import ratio\n\n"
                "class T(unittest.TestCase):\n    def test_ratio(self):\n        self.assertEqual(ratio(1, 4), 0.25)\n"
                "    def test_zero(self):\n        self.assertEqual(ratio(1, 0), 0.0)\n")
    open(os.path.join(d, "app", "__init__.py"), "w").close()
    spec = {"suite": [sys.executable, "-m", "unittest", "-q", "test_metrics"], "sabotages": [
        {"name": "control", "file": "app/metrics.py", "find": "if not total:", "replace": "if total == 0:",
         "control": True},
        {"name": "sin denominador", "file": "app/metrics.py", "find": "return hits / total", "replace": "return hits"},
        {"name": "label sin test", "file": "app/metrics.py", "find": "x > 0.5", "replace": "x > 0.9"},
        {"name": "obsoleto", "file": "app/metrics.py", "find": "no existe", "replace": "x"},
    ]}
    sp = os.path.join(d, "sabotages.json")
    with open(sp, "w") as f:
        json.dump(spec, f)
    original = open(os.path.join(d, "app", "metrics.py")).read()
    out = run_spec(sp)
    got = {r["name"]: r["status"] for r in out["results"]}
    want = {"control": "ok", "sin denominador": "ok", "label sin test": "escapo", "obsoleto": "obsoleto"}
    restored = open(os.path.join(d, "app", "metrics.py")).read() == original
    failures = 0
    for k, v in want.items():
        failures += got.get(k) != v
        print(f"  {'✓' if got.get(k) == v else '✗'} {k}: {got.get(k)} (esperado {v})")
    print(f"  {'✓' if restored else '✗'} el fichero queda como estaba")
    failures += not restored
    with open(os.path.join(d, "test_metrics.py"), "a") as f:
        f.write("    def test_roto(self):\n        self.fail('roto')\n")
    rc = report(run_spec(sp))
    print(f"  {'✓' if rc == 1 else '✗'} suite roja de partida → aborta (rc {rc})")
    failures += rc != 1
    print("self-test:", "OK" if not failures else f"{failures} FALLO(S)")
    return 1 if failures else 0


def main() -> int:
    args = sys.argv[1:]
    if "--self-test" in args:
        return self_test()
    if not args:
        print(__doc__)
        return 2
    out = run_spec(args[0])
    if "--json" in args:
        print(json.dumps(out, ensure_ascii=False, indent=2))
        return 1 if out.get("error") or any(r["status"] != "ok" for r in out["results"]) else 0
    return report(out)


if __name__ == "__main__":
    sys.exit(main())
