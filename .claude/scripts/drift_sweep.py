#!/usr/bin/env python3
"""drift_sweep.py — sensores de deriva del repo ENTERO, fuera del ciclo del cambio, con delta frente al anterior.

POR QUÉ (EQ-41, sub-ola 3.11). Los controles del template miran el cambio (cierre de wave, pre-merge).
Nadie miraba la deriva del código entero: `hugo-vigilancia-diaria` vigila la superficie expuesta, no el
código, y `bug-sweep` es bajo demanda. Böckeler lo llama «sensores continuos de deriva» y Rick «garbage
collection»: lo rápido antes del commit, lo caro fuera del ciclo. Este barrido es lo caro, y por eso se
programa (capa 5 de `governance.md` §6, con OK), no se mete en cada cambio. Política:
`rules/audit-team.md` §8.

QUÉ MIDE (sin dependencias ni red; todo son CANDIDATOS, no veredictos):
  D1 duplicación   bloques de 6 líneas normalizadas que aparecen en ≥2 sitios (.py .js .jsx .ts .tsx)
  D2 código muerto funciones y clases de nivel superior de Python cuyo nombre no sale en ningún otro
                   sitio del código (ni importado ni llamado). `_privadas`, `test_*` y dunders fuera
  D3 dependencias  requirements*.txt sin versión fijada (`==`), package.json con rangos (^ ~ * latest)
                   y si hay lockfile
  D4 tests         ficheros de test frente a ficheros de código

Uso:
    drift_sweep.py [--root .] [--salida .docs/feedback/deriva] [--json]
Escribe `<salida>/<AAAA-MM-DD>.json` y compara con el informe anterior de esa carpeta: el delta es la
señal (D1 o D2 que suben de una semana a otra), no el número absoluto.

SALIDA. 0 = medido (con o sin candidatos) · 2 = NO SE PUDO MEDIR (no hay código bajo --root). Un barrido
que no encuentra código no es «sin deriva».

LÍMITE HONESTO. D2 por nombre: un nombre que solo se usa por reflexión (`getattr`, URLs de Django por
cadena, entry points) sale como muerto; uno repetido en otro fichero sin relación lo esconde. D1 no ve
duplicación con nombres cambiados. Es el filtro barato que dice dónde mirar; el juicio lo pone quien lee.
"""
import argparse
import ast
import datetime
import hashlib
import json
import os
import re
import sys
from collections import defaultdict

CODE_EXT = {".py", ".js", ".jsx", ".ts", ".tsx"}
SKIP = {".git", "node_modules", "venv", ".venv", "env", "dist", "build", "__pycache__", ".next",
        "migrations", "_archive", "coverage", ".mypy_cache", ".pytest_cache", "vendor", "resources",
        "worktrees", ".docs", "static"}
WINDOW = 6
TEST_RE = re.compile(r"(^|/)(tests?/|test_[^/]*$|[^/]*_test\.py$|[^/]*\.(test|spec)\.[jt]sx?$)")
IDENT = re.compile(r"[A-Za-z_][A-Za-z0-9_]*")


def walk(root):
    for d, dirs, files in os.walk(root):
        dirs[:] = [x for x in dirs if x not in SKIP and not x.startswith(".")]
        for f in files:
            if os.path.splitext(f)[1] in CODE_EXT:
                yield os.path.join(d, f)


def norm_lines(text):
    out = []
    for i, line in enumerate(text.splitlines(), 1):
        s = re.sub(r"\s+", " ", line.strip())
        if len(s) > 3 and not s.startswith(("#", "//", "import ", "from ", "*", "/*")) and s not in ("{", "}", ");"):
            out.append((i, s))
    return out


def sweep(root):
    files = sorted(walk(root))
    texts = {}
    for p in files:
        try:
            texts[p] = open(p, encoding="utf-8", errors="replace").read()
        except OSError:
            continue
    rel = lambda p: os.path.relpath(p, root)
    # D1
    seen = defaultdict(list)
    for p, t in texts.items():
        if TEST_RE.search(rel(p)):
            continue
        nl = norm_lines(t)
        for k in range(len(nl) - WINDOW + 1):
            h = hashlib.sha1("\n".join(s for _, s in nl[k:k + WINDOW]).encode()).hexdigest()
            seen[h].append((rel(p), nl[k][0]))
    dups = [locs for locs in seen.values() if len({f for f, _ in locs}) >= 2 or len(locs) >= 2]
    # una racha de ventanas solapadas cuenta una vez por par de ficheros
    pairs = defaultdict(int)
    for locs in dups:
        key = tuple(sorted({f for f, _ in locs}))
        pairs[key] += 1
    d1 = {"bloques_duplicados": len(dups),
          "top": [{"ficheros": list(k), "ventanas": n} for k, n in sorted(pairs.items(), key=lambda x: -x[1])[:10]]}
    # D2
    counts = defaultdict(int)
    for t in texts.values():
        for tok in IDENT.findall(t):
            counts[tok] += 1
    dead = []
    for p, t in texts.items():
        if not p.endswith(".py") or TEST_RE.search(rel(p)):
            continue
        try:
            tree = ast.parse(t)
        except SyntaxError:
            continue
        exported = set()
        for node in tree.body:
            if isinstance(node, ast.Assign) and any(getattr(x, "id", "") == "__all__" for x in node.targets):
                exported |= {getattr(e, "value", "") for e in getattr(node.value, "elts", [])}
        for node in tree.body:
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
                n = node.name
                if n.startswith("_") or n.startswith("test") or n in exported or n in ("main", "Meta"):
                    continue
                if counts[n] <= 1:
                    dead.append(f"{rel(p)}:{node.lineno} {n}")
    d2 = {"candidatos": len(dead), "lista": dead[:40]}
    # D3
    unpinned, ranged, locks = [], [], []
    for d, dirs, fs in os.walk(root):
        dirs[:] = [x for x in dirs if x not in SKIP and not x.startswith(".")]
        for f in fs:
            p = os.path.join(d, f)
            if re.fullmatch(r"requirements.*\.txt", f):
                for line in open(p, encoding="utf-8", errors="replace"):
                    s = line.split("#")[0].strip()
                    if s and not s.startswith(("-", "git+", "http")) and "==" not in s:
                        unpinned.append(f"{rel(p)}: {s}")
            elif f == "package.json":
                try:
                    pj = json.load(open(p, encoding="utf-8"))
                except ValueError:
                    continue
                for sec in ("dependencies", "devDependencies"):
                    for name, v in (pj.get(sec) or {}).items():
                        if str(v).startswith(("^", "~", "*", ">")) or v in ("latest", "x"):
                            ranged.append(f"{rel(p)}: {name}@{v}")
            elif f in ("package-lock.json", "yarn.lock", "pnpm-lock.yaml", "poetry.lock", "uv.lock", "Pipfile.lock"):
                locks.append(rel(p))
    d3 = {"sin_fijar": len(unpinned), "con_rango": len(ranged), "lockfiles": locks,
          "ejemplos": (unpinned + ranged)[:20]}
    # D4
    n_test = sum(1 for p in texts if TEST_RE.search(rel(p)))
    d4 = {"ficheros_codigo": len(texts) - n_test, "ficheros_test": n_test}
    return {"fecha": datetime.date.today().isoformat(), "root": root, "ficheros": len(texts),
            "D1_duplicacion": d1, "D2_muerto": d2, "D3_dependencias": d3, "D4_tests": d4}


def delta(cur, prev):
    if not prev:
        return {"anterior": None}
    g = lambda r, a, b: (r.get(a) or {}).get(b, 0)
    return {"anterior": prev.get("fecha"),
            "D1": g(cur, "D1_duplicacion", "bloques_duplicados") - g(prev, "D1_duplicacion", "bloques_duplicados"),
            "D2": g(cur, "D2_muerto", "candidatos") - g(prev, "D2_muerto", "candidatos"),
            "D3": (g(cur, "D3_dependencias", "sin_fijar") + g(cur, "D3_dependencias", "con_rango"))
                  - (g(prev, "D3_dependencias", "sin_fijar") + g(prev, "D3_dependencias", "con_rango")),
            "D4_tests": g(cur, "D4_tests", "ficheros_test") - g(prev, "D4_tests", "ficheros_test")}


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--root", default=os.getcwd())
    ap.add_argument("--salida", default=None, help="carpeta de informes (por defecto <root>/.docs/feedback/deriva)")
    ap.add_argument("--json", action="store_true")
    a = ap.parse_args()
    root = os.path.realpath(a.root)
    rep = sweep(root)
    if rep["ficheros"] == 0:
        print(f"NO SE PUDO MEDIR: no hay código ({', '.join(sorted(CODE_EXT))}) bajo {root}", file=sys.stderr)
        return 2
    out = a.salida or os.path.join(root, ".docs", "feedback", "deriva")
    os.makedirs(out, exist_ok=True)
    prevs = sorted(f for f in os.listdir(out) if re.fullmatch(r"\d{4}-\d{2}-\d{2}\.json", f)
                   and f != rep["fecha"] + ".json")
    prev = json.load(open(os.path.join(out, prevs[-1]), encoding="utf-8")) if prevs else None
    rep["delta"] = delta(rep, prev)
    json.dump(rep, open(os.path.join(out, rep["fecha"] + ".json"), "w", encoding="utf-8"),
              ensure_ascii=False, indent=2)
    if a.json:
        print(json.dumps(rep, ensure_ascii=False, indent=2))
        return 0
    dl = rep["delta"]
    sg = lambda k: "" if dl.get("anterior") is None else f" ({dl[k]:+d} vs {dl['anterior']})"
    print(f"# Deriva · {os.path.basename(root)} · {rep['fecha']} · {rep['ficheros']} ficheros de código")
    print(f"D1 duplicación   {rep['D1_duplicacion']['bloques_duplicados']} bloques de {WINDOW} líneas{sg('D1')}")
    for t in rep["D1_duplicacion"]["top"][:5]:
        print(f"    {t['ventanas']:>4}  {' ↔ '.join(t['ficheros'])}")
    print(f"D2 código muerto {rep['D2_muerto']['candidatos']} candidatos{sg('D2')}")
    for x in rep["D2_muerto"]["lista"][:8]:
        print(f"    {x}")
    d3 = rep["D3_dependencias"]
    print(f"D3 dependencias  {d3['sin_fijar']} sin fijar · {d3['con_rango']} con rango{sg('D3')} · "
          f"lockfiles: {', '.join(d3['lockfiles']) or 'ninguno'}")
    d4 = rep["D4_tests"]
    print(f"D4 tests         {d4['ficheros_test']} de test / {d4['ficheros_codigo']} de código{sg('D4_tests')}")
    print(f"Informe: {os.path.relpath(os.path.join(out, rep['fecha'] + '.json'), root)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
