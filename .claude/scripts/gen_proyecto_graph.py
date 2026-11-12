#!/usr/bin/env python3
"""graph-dataset.json de un PROYECTO real — backend, frontend y agente IA por capas.

POR QUE NO VALE `gen_harness_graph.py`. Aquel mapea el HARNESS: skills, agentes, rules
y sus citas cruzadas. Es el sistema de Claude Code documentandose a si mismo. Cuando lo
que quieres ver es "como esta montado MI proyecto" —modelos, vistas, componentes, el
grafo del agente— ese dataset no responde nada: no contiene una sola linea del proyecto.

POR QUE TAMPOCO UN INDEXADOR GENERICO. Un grafo de llamadas trata igual un modelo Django
que un helper de fechas. Lo que hace legible un proyecto de este stack es la CAPA: si una
pieza es un modelo, una vista, un serializer, un componente o un nodo del grafo. Eso no
sale de un AST generico: sale de las convenciones del framework, que aqui son estables.

QUE PRODUCE. El mismo contrato que `structure.html` y `codigo.html` ya consumen:
    nodes[{id,label,group,kind,files,loc,fan_in,fan_out,desc}]
    edges[{from,to,kind,weight,evidence}]
    communities{<group>: {label,color}}

LIMITES DECLARADOS, y son tres:
  1. Las aristas salen de los IMPORTS, no de las llamadas. Un import es una dependencia
     real y barata de extraer; una llamada dinamica no se ve. Marcadas EXTRACTED.
  2. El frontend se lee con expresiones regulares, no con un parser de TypeScript. Es
     suficiente para agrupar por capa y contar; NO para afirmar nada fino sobre tipos.
  3. La capa se deduce de la RUTA y del contenido. Un proyecto que no siga la convencion
     del framework saldra mal agrupado — y eso, en si mismo, ya es informacion.

USO:
    python3 .claude/scripts/gen_proyecto_graph.py <ruta-del-proyecto> [salida.json] [--max N]
"""
import argparse, ast, json, os, re, subprocess, sys, datetime
from collections import defaultdict
from pathlib import Path

SALTAR = {"migrations", "__pycache__", ".venv", "venv", "node_modules", ".git", "dist",
          "build", "staticfiles", "media", ".mypy_cache", ".pytest_cache", "worktrees",
          ".next", "coverage", "htmlcov", "site-packages",
          # El harness NO es el codigo del proyecto. Meterlo produce el grafo equivocado:
          # 26 rules y 21 skills donde deberia haber modelos y componentes. Para el harness
          # existe `gen_harness_graph.py`, que es otra pregunta.
          ".claude", ".docs", ".specify", ".github"}

# CAPAS. El orden importa: gana la primera que casa.
#   (id, etiqueta, color, patron de RUTA, patron de CONTENIDO opcional)
CAPAS = [
    ("agente-grafo",  "Agente · grafo",      "#7c3aed", r"", r"StateGraph|add_node\(|add_conditional_edges|compile\(checkpointer"),
    ("agente-tool",   "Agente · tools",      "#a855f7", r"tools?/",  r"@tool\b|StructuredTool|Tool\(name="),
    ("agente-estado", "Agente · estado",     "#c084fc", r"", r"class \w*State\(TypedDict|Annotated\[.*add_messages|BaseCheckpointSaver"),
    ("modelo",        "Backend · modelos",   "#15803d", r"models?(/|\.py)", r"models\.Model|models\.\w+Field"),
    ("serializer",    "Backend · serializers","#16a34a", r"serializers?(/|\.py)", r"serializers\.\w*Serializer"),
    ("vista",         "Backend · vistas",    "#0891b2", r"views?(/|\.py)|viewsets?", r"APIView|ViewSet|def get\(|render\("),
    ("tarea",         "Backend · tareas",    "#b45309", r"tasks?(/|\.py)", r"@shared_task|@app\.task|celery"),
    ("servicio",      "Backend · servicios", "#0d9488", r"services?/|utils?(/|\.py)|helpers?/", r""),
    ("api",           "Backend · rutas",     "#0e7490", r"urls?\.py|routers?\.py", r""),
    ("test",          "Tests",               "#9aa1ad", r"tests?/|test_|_test\.", r""),
    ("pagina",        "Frontend · páginas",  "#c2410c", r"pages?/|routes?/|views?/", r""),
    ("componente",    "Frontend · componentes","#ea580c", r"components?/", r""),
    ("estado-fe",     "Frontend · estado",   "#f59e0b", r"stores?/|hooks?/|context/", r""),
    ("cliente-api",   "Frontend · API",      "#d97706", r"api/|services?/|client", r""),
    ("script",        "Scripts y comandos",  "#6b7280", r"^scripts?/|management/commands/|^manage\.py|^run_|\bbin/", r""),
    ("config",        "Configuración",       "#4b5563", r"settings|config|conftest", r""),
    ("entrada",       "Puntos de entrada",   "#374151", r"^(main|app|wsgi|asgi|index|server)\.(py|ts|tsx|js)$", r""),
]
PY_EXT, FE_EXT = {".py"}, {".ts", ".tsx", ".js", ".jsx", ".vue"}
IMPORT_TS = re.compile(r"""^\s*import\s[^'"]*['"]([^'"]+)['"]""", re.M)


def capa_de(rel: str, src: str) -> str:
    low = rel.lower()
    for cid, _l, _c, rx_ruta, rx_cont in CAPAS:
        ok_ruta = (not rx_ruta) or re.search(rx_ruta, low)
        ok_cont = (not rx_cont) or re.search(rx_cont, src)
        if rx_ruta and rx_cont:
            if ok_ruta and ok_cont:
                return cid
        elif rx_cont:
            if ok_cont:
                return cid
        elif ok_ruta:
            return cid
    return "otro"


def descripcion(src: str, rel: str) -> str:
    """El docstring o el primer comentario. Si no hay, se dice — no se inventa."""
    if rel.endswith(".py"):
        try:
            d = ast.get_docstring(ast.parse(src))
            if d:
                return " ".join(d.split())[:200]
        except SyntaxError:
            pass
    m = re.search(r"^\s*(?://|/\*|#)\s*(.{10,180})", src, re.M)
    return " ".join(m.group(1).split())[:200] if m else ""


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("proyecto")
    ap.add_argument("salida", nargs="?", default=None)
    ap.add_argument("--max", type=int, default=260, help="tope de nodos (los más acoplados)")
    a = ap.parse_args()
    raiz = Path(a.proyecto).resolve()
    if not raiz.is_dir():
        print(f"no existe: {raiz}", file=sys.stderr)
        return 1

    modulos, por_capa = {}, defaultdict(int)
    aristas = defaultdict(int)
    py_por_mod = {}

    for f in raiz.rglob("*"):
        if not f.is_file() or f.suffix not in (PY_EXT | FE_EXT):
            continue
        rel = str(f.relative_to(raiz))
        if any(p in SALTAR for p in Path(rel).parts):
            continue
        try:
            src = f.read_text(encoding="utf-8", errors="ignore")
        except Exception:
            continue
        if len(src) > 900_000:
            continue
        # el MÓDULO es el directorio: un fichero por nodo hace ilegible el grafo
        mod = str(Path(rel).parent) if Path(rel).parent != Path(".") else Path(rel).stem
        capa = capa_de(rel, src)
        n = modulos.setdefault(mod, {"loc": 0, "files": [], "capas": defaultdict(int), "desc": ""})
        n["loc"] += src.count("\n") + 1
        n["files"].append(rel)
        n["capas"][capa] += 1
        por_capa[capa] += 1
        if not n["desc"]:
            n["desc"] = descripcion(src, rel)
        if f.suffix in PY_EXT:
            py_por_mod.setdefault(mod, []).append((rel, src))
        else:
            for imp in IMPORT_TS.findall(src):
                if imp.startswith("."):                    # solo imports locales
                    dest = os.path.normpath(os.path.join(os.path.dirname(rel), imp))
                    aristas[(mod, str(Path(dest).parent))] += 1

    # imports de Python -> aristas entre módulos
    # Ordenado por longitud DESCENDENTE: gana el prefijo más específico. Con el más corto,
    # `from core.workflow import x` se contaba como import a `core`, y esa carpeta —que tiene
    # dos ficheros— salía como el nodo más acoplado del proyecto con 395 de fan_in.
    raiz_mods = sorted(((m.replace("/", "."), m) for m in modulos),
                       key=lambda kv: -len(kv[0]))
    for mod, ficheros in py_por_mod.items():
        for rel, src in ficheros:
            try:
                arbol = ast.parse(src)
            except SyntaxError:
                continue
            for nod in ast.walk(arbol):
                objetivo = None
                if isinstance(nod, ast.ImportFrom) and nod.module:
                    objetivo = nod.module
                elif isinstance(nod, ast.Import):
                    objetivo = nod.names[0].name if nod.names else None
                if not objetivo:
                    continue
                for punteado, m in raiz_mods:
                    if objetivo.startswith(punteado) and m != mod:
                        aristas[(mod, m)] += 1
                        break

    # La capa del módulo la decide la PRIORIDAD, no la mayoría. Un directorio con veinte
    # ficheros de apoyo y uno que construye el grafo ES el grafo: eso es lo que hay que ver.
    # Con mayoría, `core/workflow` de elvion salía "sin clasificar" porque el StateGraph vive
    # en 1 de sus 9 ficheros — justo el que importa.
    # `test` va al FINAL: un módulo que tiene tests y código es código. Con test arriba,
    # `scripts/` de elvion salía clasificado como tests por los ficheros de prueba que contiene.
    PRIORIDAD = [c[0] for c in CAPAS if c[0] != "test"] + ["test"]

    def capa_del_modulo(capas: dict) -> str:
        for cid in PRIORIDAD:
            if capas.get(cid):
                return cid
        return "otro"

    nodos = []
    for mod, d in modulos.items():
        # Directorios contenedores sin ficheros propios (`apps/`, `core/`) aparecen como destino
        # de imports y falsean el acoplamiento: 472 de fan_in para una carpeta vacía.
        solo_init = all(Path(x).name == "__init__.py" for x in d["files"])
        if (d["loc"] <= 2 and len(d["files"]) <= 1) or solo_init:
            continue
        capa = capa_del_modulo(d["capas"])
        nodos.append({"id": mod, "label": Path(mod).name or mod, "group": capa, "kind": capa,
                      "files": d["files"][:12], "loc": d["loc"],
                      "fan_in": 0, "fan_out": 0, "desc": d["desc"],
                      "n_ficheros": len(d["files"])})
    idx = {n["id"]: n for n in nodos}
    for (a_, b_), w in aristas.items():
        if a_ in idx and b_ in idx:
            idx[a_]["fan_out"] += w
            idx[b_]["fan_in"] += w

    nodos.sort(key=lambda n: -(n["fan_in"] + n["fan_out"] + n["loc"] / 100))
    recortado = len(nodos) > a.max
    if recortado:
        nodos = nodos[:a.max]
    vivos = {n["id"] for n in nodos}
    edges = [{"from": x, "to": y, "kind": "importa", "weight": w, "evidence": "EXTRACTED"}
             for (x, y), w in aristas.items() if x in vivos and y in vivos]

    sha = subprocess.run(["git", "-C", str(raiz), "rev-parse", "--short", "HEAD"],
                         capture_output=True, text=True).stdout.strip()
    coms = {cid: {"label": lab, "color": col} for cid, lab, col, _r, _c in CAPAS
            if any(n["group"] == cid for n in nodos)}
    if any(n["group"] == "otro" for n in nodos):
        coms["otro"] = {"label": "Sin clasificar", "color": "#9aa1ad"}

    data = {"meta": {
        "source": f"gen_proyecto_graph.py — imports + convención de framework · proyecto {raiz.name}",
        "proyecto": raiz.name, "sha": sha,
        "date": datetime.date.today().isoformat(),
        "nodes_total": len(modulos), "edges_total": len(aristas),
        "reduced": recortado,
        "ficheros_por_capa": dict(sorted(por_capa.items(), key=lambda kv: -kv[1])),
    }, "nodes": nodos, "edges": edges, "communities": coms}

    out = Path(a.salida) if a.salida else raiz / "graph-dataset.json"
    out.write_text(json.dumps(data, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"OK {out}")
    print(f"   {len(modulos)} módulos ({len(nodos)} publicados) · {len(aristas)} relaciones · sha {sha or '?'}")
    for c, n in list(data["meta"]["ficheros_por_capa"].items())[:8]:
        print(f"     {c:16} {n:5} ficheros")
    return 0


if __name__ == "__main__":
    sys.exit(main())
