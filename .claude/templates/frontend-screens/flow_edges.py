#!/usr/bin/env python3
"""flow_edges.py — el flujo IMPLEMENTADO: qué pantalla enlaza a cuál según el código.

Lee `src/app/screens.ts` (qué página es cada pantalla, por su `load: () => import('../pages/X')`) y
busca en cada página los `hrefTo('ID'…)`. Escribe `src/app/flow.implemented.json`, que `flow.ts`
compara con el flujo diseñado. Una pantalla sin `load` no tiene página y no aporta conexiones.

Límite: ve lo que pasa por `hrefTo` en el fichero de la página, no lo que enlaza un componente
importado. Por eso el mapa dice «en el código, sin diseñar» y «falta en el código», no «roto».

CÓDIGOS: 0 escrito · 1 con --check, el JSON está desfasado · 2 no se pudo (sin screens.ts, o
ninguna pantalla con página).

USO (desde `frontend/`):
    python3 scripts/flow_edges.py              # escribe src/app/flow.implemented.json
    python3 scripts/flow_edges.py --check      # para CI: 1 si el JSON no es el que sale del código
    python3 scripts/flow_edges.py --self-test
"""
from __future__ import annotations

import json
import re
import sys
import tempfile
from pathlib import Path

LOAD = re.compile(r"import\(\s*['\"]([^'\"]+)['\"]\s*\)")
HREF = re.compile(r"hrefTo\(\s*['\"]([A-Z]\w*)['\"]")


def screen_pages(screens_ts: Path) -> dict[str, Path]:
    """{id: fichero de su página} de las pantallas con `load`."""
    text = screens_ts.read_text(encoding="utf-8")
    pages = {}
    for m in re.finditer(r"([A-Z]\w*)\s*:\s*\{([^{}]*)\}", text):
        load = LOAD.search(m.group(2))
        if not load:
            continue
        base = (screens_ts.parent / load.group(1)).resolve()
        for ext in (".tsx", ".ts", ".jsx", ".js"):
            if base.with_suffix(ext).is_file():
                pages[m.group(1)] = base.with_suffix(ext)
                break
    return pages


def edges(src: Path) -> list[list[str]]:
    screens_ts = src / "app" / "screens.ts"
    if not screens_ts.is_file():
        raise FileNotFoundError(f"no está {screens_ts}")
    pages = screen_pages(screens_ts)
    if not pages:
        raise LookupError("ninguna pantalla de screens.ts tiene página (`load`)")
    out = set()
    for sid, page in pages.items():
        for target in HREF.findall(page.read_text(encoding="utf-8")):
            if target != sid:
                out.add((sid, target))
    return [list(e) for e in sorted(out)]


def run(src: Path, check: bool) -> int:
    try:
        found = edges(src)
    except (FileNotFoundError, LookupError) as e:
        print(f"⛔ flow_edges.py NO PUDO: {e}", file=sys.stderr)
        return 2
    target = src / "app" / "flow.implemented.json"
    doc = {"generated_by": "flow_edges.py", "edges": found}
    text = json.dumps(doc, ensure_ascii=False, indent=2) + "\n"
    if check:
        current = target.read_text(encoding="utf-8") if target.is_file() else ""
        if current != text:
            print(f"✗ {target} está desfasado: corre flow_edges.py sin --check")
            return 1
        print(f"✓ {len(found)} conexión(es), al día")
        return 0
    target.write_text(text, encoding="utf-8")
    print(f"flow_edges.py · {len(found)} conexión(es) implementada(s) → {target}")
    return 0


def self_test() -> int:
    with tempfile.TemporaryDirectory() as tmp:
        src = Path(tmp) / "src"
        (src / "app").mkdir(parents=True)
        (src / "pages").mkdir()
        (src / "app" / "screens.ts").write_text(
            "export const SCREENS = {\n"
            "  C01: { path: '/entrar', zone: 'public', name: 'Entrar',\n"
            "         load: () => import('../pages/LoginPage') },\n"
            "  C02: { path: '/hoy', zone: 'app', name: 'Hoy',\n"
            "         load: () => import('../pages/TodayPage') },\n"
            "  C03: { path: '/pedidos/:orderId', zone: 'app', name: 'Pedido' },\n"
            "} as const;\n", encoding="utf-8")
        (src / "pages" / "LoginPage.tsx").write_text("navigate(hrefTo('C02'));\n", encoding="utf-8")
        (src / "pages" / "TodayPage.tsx").write_text(
            "<Link to={hrefTo('C03', { orderId })} /> <Link to={hrefTo(\"C01\")} />\n",
            encoding="utf-8")
        failures = []
        got = edges(src)
        if got != [["C01", "C02"], ["C02", "C01"], ["C02", "C03"]]:
            failures.append(f"conexiones: {got}")
        if run(src, check=True) != 1:
            failures.append("--check sin JSON debía dar 1")
        run(src, check=False)
        if run(src, check=True) != 0:
            failures.append("--check tras escribir debía dar 0")
        (src / "app" / "screens.ts").write_text("export const SCREENS = {} as const;\n")
        if run(src, check=False) != 2:
            failures.append("sin pantallas con página debía dar 2")
    for f in failures:
        print(f"  ✗ {f}")
    print(f"flow_edges.py --self-test: {'FALLA' if failures else 'OK'}")
    return 1 if failures else 0


if __name__ == "__main__":
    args = sys.argv[1:]
    if args[:1] == ["--self-test"]:
        sys.exit(self_test())
    sys.exit(run(Path("src"), check="--check" in args))
