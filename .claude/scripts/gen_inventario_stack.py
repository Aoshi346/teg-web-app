#!/usr/bin/env python3
"""inventario-stack.json — QUÉ hay dentro de cada capa, pieza a pieza y con su nombre.

LA DIFERENCIA CON `gen_proyecto_graph.py`. Aquel dice qué MÓDULOS hay y quién importa a
quién: el mapa. Este entra dentro y saca los NOMBRES: cada modelo con sus campos, cada
vista con su modelo, cada componente, cada nodo del grafo, cada tool con su descripcion.
Es lo que hace falta para responder "¿que modelos tenemos?" o "¿que tools ve el bot?",
que un grafo de modulos no contesta.

QUE EXTRAE, y de donde:
  Backend Django   modelos (campos, tipos, relaciones) · serializers · vistas y ViewSets ·
                   tareas Celery · rutas · señales
  Frontend React   componentes · paginas · hooks · stores · llamadas a la API
  Agente LangGraph nodos del grafo · aristas · tools (con su descripcion, que ES el prompt
                   que decide si se llama) · campos del State con su reducer

COMO. Python con AST, que es exacto. TypeScript/TSX con expresiones regulares, que no lo
es: sirve para inventariar y contar, NO para afirmar nada fino sobre tipos. Va declarado
en la salida (`metodo`) para que quien lea el informe sepa de que se fia.

USO:
    python3 .claude/scripts/gen_inventario_stack.py <proyecto> [salida.json]
"""
import argparse, ast, json, re, subprocess, sys, datetime
from collections import defaultdict
from pathlib import Path

SALTAR = {"migrations", "__pycache__", ".venv", "venv", "node_modules", ".git", "dist",
          "build", "staticfiles", "media", ".mypy_cache", ".pytest_cache", "worktrees",
          ".next", "coverage", "htmlcov", "site-packages", ".claude", ".docs", ".specify"}

CAMPO_DJANGO = re.compile(r"models\.(\w+Field|ForeignKey|OneToOneField|ManyToManyField)")
BASE_MODELO = re.compile(r"\bModel\b|\bAbstract\w*\b")
COMP_TSX = re.compile(
    r"(?:export\s+(?:default\s+)?(?:function|const)\s+([A-Z]\w+)|"
    r"(?:function|const)\s+([A-Z]\w+)\s*(?::\s*(?:React\.)?FC|\s*=\s*\())")
HOOK_TS = re.compile(r"(?:export\s+)?(?:function|const)\s+(use[A-Z]\w+)")
RUTA_TS = re.compile(r"""path\s*[:=]\s*['"]([^'"]+)['"]""")


def rel(f, raiz):
    return str(f.relative_to(raiz))


def texto(f):
    try:
        return f.read_text(encoding="utf-8", errors="ignore")
    except Exception:
        return ""


def _nombre(n):
    if isinstance(n, ast.Attribute):
        base = _nombre(n.value)
        return f"{base}.{n.attr}" if base else n.attr
    if isinstance(n, ast.Name):
        return n.id
    if isinstance(n, ast.Call):
        return _nombre(n.func)
    if isinstance(n, ast.Constant):
        return str(n.value)
    if isinstance(n, ast.Subscript):
        return _nombre(n.value)
    return ""


def app_de(ruta: str) -> str:
    partes = Path(ruta).parts
    for marca in ("apps", "backend"):
        if marca in partes:
            i = partes.index(marca)
            if i + 1 < len(partes):
                return partes[i + 1]
    return partes[0] if partes else "-"


def python(f, raiz, inv):
    ruta, src = rel(f, raiz), texto(f)
    if not src:
        return
    try:
        arbol = ast.parse(src)
    except SyntaxError:
        return
    app = app_de(ruta)

    for n in ast.walk(arbol):
        # ── MODELOS ────────────────────────────────────────────────────────────
        if isinstance(n, ast.ClassDef):
            bases = [_nombre(b) for b in n.bases]
            es_modelo = any(BASE_MODELO.search(b) for b in bases) and "Serializer" not in " ".join(bases)
            if es_modelo and re.search(r"models?[/.]", ruta):
                campos, rels = [], []
                for s in n.body:
                    if isinstance(s, ast.AnnAssign) and s.target.__class__ is ast.Name:
                        nom = s.target.id
                    elif isinstance(s, ast.Assign) and s.targets and isinstance(s.targets[0], ast.Name):
                        nom = s.targets[0].id
                    else:
                        continue
                    val = _nombre(s.value)
                    m = CAMPO_DJANGO.search(ast.unparse(s.value) if hasattr(ast, "unparse") else val)
                    if not m:
                        continue
                    tipo = m.group(1)
                    campos.append({"nombre": nom, "tipo": tipo})
                    if tipo in ("ForeignKey", "OneToOneField", "ManyToManyField"):
                        arg = ""
                        if isinstance(s.value, ast.Call) and s.value.args:
                            arg = _nombre(s.value.args[0])
                        rels.append({"campo": nom, "tipo": tipo, "hacia": arg})
                inv["modelos"].append({
                    "nombre": n.name, "app": app, "file": ruta, "line": n.lineno,
                    "bases": bases[:3], "campos": campos, "relaciones": rels,
                    "doc": (ast.get_docstring(n) or "").split("\n")[0][:150],
                    "abstracto": any("Abstract" in b for b in bases)})
            elif any("Serializer" in b for b in bases):
                modelo = ""
                for s in ast.walk(n):
                    if isinstance(s, ast.Assign) and s.targets and _nombre(s.targets[0]) == "model":
                        modelo = _nombre(s.value)
                inv["serializers"].append({"nombre": n.name, "app": app, "file": ruta,
                                           "line": n.lineno, "modelo": modelo,
                                           "bases": bases[:2]})
            elif any(re.search(r"ViewSet|APIView|View$|ListView|DetailView|CreateView|UpdateView", b) for b in bases):
                inv["vistas"].append({"nombre": n.name, "app": app, "file": ruta,
                                      "line": n.lineno, "bases": bases[:2],
                                      "doc": (ast.get_docstring(n) or "").split("\n")[0][:150]})
            # ── STATE del agente ───────────────────────────────────────────────
            elif any("TypedDict" in b for b in bases) and re.search(r"[Ss]tate", n.name):
                campos = []
                for s in n.body:
                    if isinstance(s, ast.AnnAssign) and isinstance(s.target, ast.Name):
                        anot = ast.unparse(s.annotation) if hasattr(ast, "unparse") else _nombre(s.annotation)
                        red = ""
                        m = re.search(r"Annotated\[[^,]+,\s*([\w.]+)", anot)
                        if m:
                            red = m.group(1)
                        campos.append({"nombre": s.target.id, "tipo": anot[:90], "reducer": red})
                inv["state"].append({"nombre": n.name, "file": ruta, "line": n.lineno,
                                     "campos": campos, "n_campos": len(campos),
                                     "doc": (ast.get_docstring(n) or "").split("\n")[0][:150]})

        # ── TOOLS ──────────────────────────────────────────────────────────────
        if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef)):
            deco = [_nombre(d) for d in n.decorator_list]
            if any(d.split(".")[-1] == "tool" for d in deco):
                args = [{"nombre": a.arg,
                         "tipo": (ast.unparse(a.annotation)[:60] if a.annotation and hasattr(ast, "unparse") else "")}
                        for a in n.args.args if a.arg not in ("self", "cls")]
                doc = ast.get_docstring(n) or ""
                inv["tools"].append({
                    "nombre": n.name, "file": ruta, "line": n.lineno,
                    "descripcion": " ".join(doc.split())[:260],
                    "args": args, "sin_doc": not doc,
                    "sin_tipos": any(not a["tipo"] for a in args) if args else False,
                    "lanza": any(isinstance(x, ast.Raise) for x in ast.walk(n))})
            if any(d.split(".")[-1] in ("task", "shared_task") for d in deco):
                inv["tareas"].append({"nombre": n.name, "app": app, "file": ruta, "line": n.lineno,
                                      "doc": (ast.get_docstring(n) or "").split("\n")[0][:140]})

        # ── GRAFO: nodos y aristas ─────────────────────────────────────────────
        if isinstance(n, ast.Call):
            fn = _nombre(n.func).split(".")[-1]
            if fn == "add_node" and n.args:
                nom = _nombre(n.args[0])
                inv["nodos"].append({"nombre": nom, "file": ruta, "line": n.lineno})
            elif fn == "add_edge" and len(n.args) >= 2:
                inv["aristas"].append({"de": _nombre(n.args[0]), "a": _nombre(n.args[1]),
                                       "tipo": "fija", "file": ruta, "line": n.lineno})
            elif fn == "add_conditional_edges" and n.args:
                inv["aristas"].append({"de": _nombre(n.args[0]),
                                       "a": (_nombre(n.args[1]) if len(n.args) > 1 else "?"),
                                       "tipo": "condicional", "file": ruta, "line": n.lineno})


def frontend(f, raiz, inv):
    ruta, src = rel(f, raiz), texto(f)
    if not src:
        return
    low = ruta.lower()
    if re.search(r"components?/", low):
        for m in COMP_TSX.finditer(src):
            nom = m.group(1) or m.group(2)
            if nom and not nom.startswith("use"):
                inv["componentes"].append({"nombre": nom, "file": ruta,
                                           "line": src[:m.start()].count("\n") + 1})
    if re.search(r"pages?/|routes?/|views?/", low):
        for m in COMP_TSX.finditer(src):
            nom = m.group(1) or m.group(2)
            if nom:
                inv["paginas"].append({"nombre": nom, "file": ruta,
                                       "line": src[:m.start()].count("\n") + 1,
                                       "rutas": RUTA_TS.findall(src)[:3]})
                break
    for m in HOOK_TS.finditer(src):
        inv["hooks"].append({"nombre": m.group(1), "file": ruta,
                             "line": src[:m.start()].count("\n") + 1})


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("proyecto")
    ap.add_argument("salida", nargs="?")
    a = ap.parse_args()
    raiz = Path(a.proyecto).resolve()
    if not raiz.is_dir():
        print(f"no existe: {raiz}", file=sys.stderr)
        return 1

    inv = defaultdict(list)
    for f in raiz.rglob("*"):
        if not f.is_file():
            continue
        r = f.relative_to(raiz)
        if any(p in SALTAR for p in r.parts):
            continue
        if f.suffix == ".py":
            python(f, raiz, inv)
        elif f.suffix in (".tsx", ".jsx", ".ts") and "test" not in str(r).lower():
            frontend(f, raiz, inv)

    for k in inv:
        inv[k].sort(key=lambda x: (x.get("app", ""), x.get("nombre", "")))
    # dedup de componentes y hooks por (nombre, fichero)
    for k in ("componentes", "hooks", "paginas"):
        visto, out = set(), []
        for x in inv[k]:
            key = (x["nombre"], x["file"])
            if key not in visto:
                visto.add(key); out.append(x)
        inv[k] = out

    # `git -C` SUBE por el arbol hasta encontrar un repo, asi que un cuerpo vendorizado
    # sin .git propio devolvia el sha del repo PADRE — un dato falso que ademas parece
    # fechado. Solo se acepta el sha si `raiz` es el toplevel del repo que lo contiene.
    top = subprocess.run(["git", "-C", str(raiz), "rev-parse", "--show-toplevel"],
                         capture_output=True, text=True).stdout.strip()
    if top and Path(top).resolve() == raiz.resolve():
        sha = subprocess.run(["git", "-C", str(raiz), "rev-parse", "--short", "HEAD"],
                             capture_output=True, text=True).stdout.strip()
    else:
        sha = "(sin git propio)"
    apps = defaultdict(lambda: defaultdict(int))
    for k in ("modelos", "serializers", "vistas", "tareas"):
        for x in inv[k]:
            apps[x.get("app", "-")][k] += 1

    data = {"meta": {
        "source": "gen_inventario_stack.py — AST para Python, expresiones regulares para TS/TSX",
        "metodo": {"python": "AST (exacto)",
                   "typescript": "regex (inventaria y cuenta; NO afirma nada fino sobre tipos)"},
        "proyecto": raiz.name, "sha": sha, "date": datetime.date.today().isoformat(),
        "totales": {k: len(v) for k, v in sorted(inv.items())},
        "apps": {k: dict(v) for k, v in sorted(apps.items())},
    }, **{k: v for k, v in inv.items()}}

    out = Path(a.salida) if a.salida else raiz / "inventario-stack.json"
    out.write_text(json.dumps(data, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"OK {out}")
    for k, v in data["meta"]["totales"].items():
        if v:
            print(f"   {k:14} {v:5}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
