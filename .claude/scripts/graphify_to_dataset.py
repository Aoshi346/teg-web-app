#!/usr/bin/env python3
"""graphify_to_dataset.py — convierte la salida de graphify al formato que `structure.html` consume.

POR QUÉ EXISTE: graphify extrae el AST de un proyecto con CÓDIGO REAL y produce `graph.json` con su
propio esquema (file_type / relation / community). El report-kit ya sabe pintar un grafo, pero espera
`graph-dataset.json` (group / kind / fan_in / edges.from-to). Este script es el puente, y hace tres
cosas que no son cosméticas:

  1. FILTRA la prosa. En musa el 57% de los nodos son `document` y `rationale`, no código. Un mapa de
     estructura que mezcla prosa con símbolos no es un mapa de estructura. Con --solo-codigo se queda
     con `file_type: code`, que es de lo que trata la página.
  2. REDUCE sin borrar lo importante. Un grafo de 7.846 nodos no se lee: es una pared. Se conserva
     por fan-in (lo más usado = el corazón del sistema) y SIEMPRE los god-nodes, que es justo lo que
     nadie quiere que desaparezca del recorte.
  3. DECLARA el origen. `meta.source = "graphify"` + versión + fecha + sha, para que la página pueda
     decir de cuándo es y con qué se hizo. Un grafo sin fecha empieza a mentir en cuanto cambia el
     código y nadie se entera.

LÍMITE HONESTO: esto refleja lo que graphify extrajo, con los fallos abiertos que ese proyecto tiene
documentados (pierde aristas en silencio tras `update` incremental, #2406). Por eso el flujo
recomendado es rebuild en frío, y por eso `meta.warning` viaja dentro del fichero.

Uso:
  python3 graphify_to_dataset.py <proyecto>/graphify-out/graph.json <destino>/graph-dataset.json \
      [--max 90] [--solo-codigo]
"""
import argparse, collections, json, subprocess, sys
from datetime import date
from pathlib import Path

# graphify agrupa por lenguaje/rol; esto lo traduce al vocabulario de `group` que colorea structure.html
def _grupo(node):
    sf = (node.get("source_file") or "").lower()
    if node.get("file_type") != "code":
        return {"document": "doc", "rationale": "doc", "concept": "doc"}.get(node.get("file_type"), "otro")
    if "/test" in sf or sf.split("/")[-1].startswith("test_"): return "test"
    if "/migrations/" in sf:                                    return "migracion"
    if sf.endswith((".tsx", ".ts", ".jsx", ".js")):             return "frontend"
    if "/integrations/" in sf or "/gateway" in sf:              return "integracion"
    if "/models.py" in sf:                                      return "modelo"
    if "/views.py" in sf or "/serializers.py" in sf:            return "api"
    if "/services/" in sf or "/tasks.py" in sf:                 return "servicio"
    return "backend"

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("origen"); ap.add_argument("destino")
    ap.add_argument("--max", type=int, default=90, help="cuántos nodos conservar (0 = todos)")
    ap.add_argument("--solo-codigo", action="store_true", help="descartar document/rationale/concept")
    a = ap.parse_args()

    g = json.loads(Path(a.origen).read_text())
    nodes = g.get("nodes", [])
    edges = g.get("edges") or g.get("links") or []
    total_n, total_e = len(nodes), len(edges)

    if a.solo_codigo:
        nodes = [n for n in nodes if n.get("file_type") == "code"]
    vivos = {n["id"] for n in nodes}
    edges = [e for e in edges if e.get("source") in vivos and e.get("target") in vivos]

    fan_in, fan_out = collections.Counter(), collections.Counter()
    for e in edges:
        fan_in[e["target"]] += 1; fan_out[e["source"]] += 1

    # el recorte conserva SIEMPRE los más conectados: son los que duelen al tocar
    if a.max and len(nodes) > a.max:
        nodes.sort(key=lambda n: -(fan_in[n["id"]] + fan_out[n["id"]]))
        nodes = nodes[: a.max]
        vivos = {n["id"] for n in nodes}
        edges = [e for e in edges if e["source"] in vivos and e["target"] in vivos]

    out_nodes = [{
        "id": n["id"],
        "label": (n.get("label") or n["id"])[:44],
        "group": _grupo(n), "kind": _grupo(n),
        "files": [n["source_file"]] if n.get("source_file") else [],
        "loc": 0,
        "fan_in": fan_in[n["id"]], "fan_out": fan_out[n["id"]],
        "desc": f"{n.get('source_file','')}{':' + str(n['source_location']) if n.get('source_location') else ''}",
        "community": n.get("community_name") or "",
    } for n in nodes]

    out_edges = [{
        "from": e["source"], "to": e["target"],
        "kind": e.get("relation", "usa"),
        "weight": e.get("weight", 1),
        "evidence": "AST",              # graphify extrae del árbol sintáctico, no de heurística de texto
    } for e in edges]

    # `communities` es un OBJETO {group: {label, color}}, no una lista: structure.html lo indexa
    # como COM[n.group].color. Con una lista salía fill="undefined" y las cajas se pintaban
    # transparentes — el grafo estaba ahí y no se veía.
    PALETA = {
        "backend":     ("Backend",           "#2563eb"),
        "frontend":    ("Frontend",          "#7c3aed"),
        "api":         ("API / vistas",      "#0891b2"),
        "modelo":      ("Modelos",           "#15803d"),
        "servicio":    ("Servicios / tareas", "#c2410c"),
        "integracion": ("Integraciones",     "#b45309"),
        "test":        ("Tests",             "#64748b"),
        "migracion":   ("Migraciones",       "#78716c"),
        "doc":         ("Documentos",        "#a1a1aa"),
        "otro":        ("Otros",             "#94a3b8"),
    }
    comus = collections.Counter(n["group"] for n in out_nodes)
    try:
        sha = subprocess.run(["git", "-C", str(Path(a.origen).parent.parent), "rev-parse", "--short", "HEAD"],
                             capture_output=True, text=True, timeout=5).stdout.strip() or "sin-git"
    except Exception:
        sha = "sin-git"

    Path(a.destino).write_text(json.dumps({
        "meta": {
            "source": "graphify", "generated": date.today().isoformat(), "sha": sha,
            "total_nodos_extraidos": total_n, "total_aristas_extraidas": total_e,
            "mostrados": len(out_nodes), "aristas_mostradas": len(out_edges),
            "filtro": "solo file_type=code" if a.solo_codigo else "todos",
            "warning": ("Extraído por graphify (AST, sin LLM). Rebuild EN FRÍO: el update incremental "
                        "pierde aristas en silencio (issue #2406). Un grafo obsoleto responde mal con "
                        "apariencia de estructura."),
        },
        "nodes": out_nodes, "edges": out_edges,
        "communities": {g: {"label": PALETA.get(g, (g, "#94a3b8"))[0],
                            "color": PALETA.get(g, (g, "#94a3b8"))[1],
                            "size": n}
                        for g, n in comus.most_common()},
    }, ensure_ascii=False, indent=1))

    print(f"  {total_n} nodos extraídos → {len(out_nodes)} mostrados · {len(out_edges)} aristas · {len(comus)} comunidades")
    print(f"  → {a.destino}")

if __name__ == "__main__":
    sys.exit(main())
