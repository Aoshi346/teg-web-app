#!/usr/bin/env python3
"""integration_check.py — el límite con lo de fuera: factoría, simulador y canales (AN-18).

    python3 .claude/patterns/stack/integration_check.py --root backend
    python3 .claude/patterns/stack/integration_check.py --root backend --engine core/workflow core/tools
    python3 .claude/patterns/stack/integration_check.py --self-test

Patrones: `backend-integrations.md` (IC1-IC3) y `backend-channel-adapter.md` (CA1). Por AST, sin
importar nada del proyecto:

  IC1  una integración con `real.py` sin su doble (`mock*.py`, `simulator*.py` o `fake*.py`)
  IC2  código de fuera de `integrations/` (y de sus tests) que importa `<integración>.real|mock`
       directamente: se salta la factoría, y con ella el candado de entorno y la guarda de escritura
  IC3  una integración que `factory.py` no nombra
  CA1  el motor (`--engine`) importa un canal concreto o una integración concreta en vez del contrato

Exit: 0 limpio · 1 hallazgos · 2 no se puede medir (no existe `--root` o su `integrations/`).
Sin `--engine`, CA1 no se mide y lo dice: no es un «0 hallazgos».
Límites: solo imports absolutos y estáticos; no ve `importlib`, `__import__` ni imports relativos.
"""
from __future__ import annotations

import argparse
import ast
import os
import shutil
import sys
import tempfile
import warnings

CONTRACT_MODULES = {"__init__", "base", "dto", "interface", "protocols"}
DOUBLE_PREFIXES = ("mock", "simulator", "fake")


def _py_files(root: str):
    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = [d for d in dirnames if d not in {"node_modules", ".venv", "venv", "__pycache__",
                                                        "migrations", ".git"}]
        for f in filenames:
            if f.endswith(".py"):
                yield os.path.join(dirpath, f)


def _imports(path: str) -> list[tuple[int, str]]:
    try:
        with warnings.catch_warnings():
            warnings.simplefilter("ignore", SyntaxWarning)
            tree = ast.parse(open(path, encoding="utf-8").read(), filename=path)
    except (SyntaxError, UnicodeDecodeError):
        return []
    out: list[tuple[int, str]] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            out += [(node.lineno, a.name) for a in node.names]
        elif isinstance(node, ast.ImportFrom) and node.module and node.level == 0:
            out.append((node.lineno, node.module))
            out += [(node.lineno, f"{node.module}.{a.name}") for a in node.names]
    return out


def _hits(mod: str, targets: tuple[str, ...]) -> bool:
    """El módulo es uno de los objetivos o cuelga de él (`x.real` sí, `x.realtime` no)."""
    return any(mod == t or mod.startswith(t + ".") for t in targets)


def _is_test(rel: str) -> bool:
    parts = rel.replace(os.sep, "/").split("/")
    return "tests" in parts or parts[-1].startswith("test_") or parts[-1] == "conftest.py"


def check(root: str, integrations: str = "integrations", channels: str = "core/channels",
          engine: list[str] | None = None) -> tuple[int, list[str], list[str]]:
    findings: list[str] = []
    notes: list[str] = []
    ipath = os.path.join(root, integrations)
    if not os.path.isdir(root) or not os.path.isdir(ipath):
        return 2, [], [f"no se puede medir: no existe {ipath}"]
    ipkg = integrations.replace("/", ".")
    names = sorted(d for d in os.listdir(ipath)
                   if os.path.isdir(os.path.join(ipath, d)) and d not in {"tests", "__pycache__"})
    factory_src = ""
    if os.path.isfile(os.path.join(ipath, "factory.py")):
        factory_src = open(os.path.join(ipath, "factory.py"), encoding="utf-8").read()
    else:
        findings.append(f"IC3 {integrations}/factory.py no existe: nadie decide real o simulador")
    for name in names:
        files = os.listdir(os.path.join(ipath, name))
        if "real.py" in files and not any(f.startswith(DOUBLE_PREFIXES) for f in files):
            findings.append(f"IC1 {integrations}/{name}: tiene real.py y ningún doble (mock/simulator/fake)")
        if factory_src and name not in factory_src:
            findings.append(f"IC3 {integrations}/{name}: factory.py no la nombra")

    concrete = tuple(f"{ipkg}.{n}.{kind}" for n in names for kind in ("real", "mock"))
    for path in _py_files(root):
        rel = os.path.relpath(path, root)
        if rel.startswith(integrations + os.sep) or _is_test(rel):
            continue
        for line, mod in _imports(path):
            if _hits(mod, concrete):
                findings.append(f"IC2 {rel}:{line} importa {mod}: pasa por la factoría")
                break

    cpath = os.path.join(root, channels)
    cpkg = channels.replace("/", ".")
    concrete_channels: tuple[str, ...] = ()
    if os.path.isdir(cpath):
        concrete_channels = tuple(f"{cpkg}.{f[:-3]}" for f in os.listdir(cpath)
                                  if f.endswith(".py") and f[:-3] not in CONTRACT_MODULES)
    if not engine:
        notes.append("CA1 sin medir: falta --engine (las carpetas del motor)")
    else:
        for e in engine:
            epath = os.path.join(root, e)
            if not os.path.isdir(epath):
                return 2, findings, notes + [f"no se puede medir: no existe {epath}"]
            for path in _py_files(epath):
                rel = os.path.relpath(path, root)
                if _is_test(rel):
                    continue
                for line, mod in _imports(path):
                    if _hits(mod, concrete_channels) or _hits(mod, concrete):
                        findings.append(f"CA1 {rel}:{line} el motor importa {mod}: usa el contrato")
                        break
    return (1 if findings else 0), findings, notes


def _write(base: str, rel: str, text: str = "") -> None:
    path = os.path.join(base, rel)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        f.write(text)


def self_test() -> int:
    good = tempfile.mkdtemp(prefix="ic-")
    for rel, text in {
        "integrations/__init__.py": "", "integrations/base.py": "class ShopGateway: ...\n",
        "integrations/factory.py": "from .shop.real import Real\nfrom .shop.mock import Mock\n# shop\n",
        "integrations/shop/real.py": "", "integrations/shop/mock.py": "",
        "core/channels/base.py": "", "core/channels/dto.py": "", "core/channels/whatsapp.py": "",
        "core/workflow/engine.py": "from core.channels.base import ChannelAdapter\n"
                                   "from integrations.factory import get_shop\n",
        "apps/orders/views.py": "from integrations.factory import get_shop\n",
        "apps/orders/tests/test_x.py": "from integrations.shop.mock import Mock\n",
    }.items():
        _write(good, rel, text)
    sab = [
        ("IC1 sin doble", "integrations/pay/real.py", "", "IC1"),
        ("IC2 vista que importa el real", "apps/orders/tasks.py",
         "from integrations.shop.real import Real\n", "IC2"),
        ("CA1 motor que importa un canal concreto", "core/workflow/route.py",
         "from core.channels.whatsapp import WhatsApp\n", "CA1"),
    ]
    bad = 0
    rc, f, _ = check(good, engine=["core/workflow"])
    ok = rc == 0
    bad += not ok
    print(f"  {'✓' if ok else '✗'} control: repo conforme → 0 (rc={rc}) {f}")
    for name, rel, text, rule in sab:
        d = tempfile.mkdtemp(prefix="ic-")
        shutil.copytree(good, d, dirs_exist_ok=True)
        _write(d, rel, text)
        rc, f, _ = check(d, engine=["core/workflow"])
        shutil.rmtree(d, ignore_errors=True)
        ok = rc == 1 and any(x.startswith(rule) for x in f)
        bad += not ok
        print(f"  {'✓' if ok else '✗'} sabotaje {name} → {rule} (rc={rc})")
    rc, _, notes = check(good)
    ok = rc == 0 and any("sin medir" in n for n in notes)
    bad += not ok
    print(f"  {'✓' if ok else '✗'} sin --engine, CA1 dice «sin medir» (no un cero)")
    rc, _, _ = check(os.path.join(good, "no-existe"))
    bad += rc != 2
    print(f"  {'✓' if rc == 2 else '✗'} raíz inexistente → 2 (rc={rc})")
    shutil.rmtree(good, ignore_errors=True)
    return 1 if bad else 0


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--root", default=".")
    ap.add_argument("--integrations", default="integrations")
    ap.add_argument("--channels", default="core/channels")
    ap.add_argument("--engine", nargs="*", default=[])
    ap.add_argument("--self-test", action="store_true")
    a = ap.parse_args(argv)
    if a.self_test:
        return self_test()
    rc, findings, notes = check(a.root, a.integrations, a.channels, a.engine)
    for f in findings:
        print(f"✗ {f}")
    for n in notes:
        print(f"· {n}")
    if rc == 0:
        print("✓ el límite con lo de fuera está en su sitio")
    return rc


if __name__ == "__main__":
    sys.exit(main())
