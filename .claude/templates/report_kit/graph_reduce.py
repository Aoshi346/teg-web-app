#!/usr/bin/env python3
"""graph_reduce.py — graph.json (node-link) → graph-dataset.json para structure.html.

Uso:
    python3 graph_reduce.py <graph.json> <salida.json> [--max-nodes 800] [--max-edges 2000]
    python3 graph_reduce.py --fixture <salida.json>        # dataset sintético de demo (F0)

Contrato de salida (el que consume structure.html y alimenta /visual-map — ver skills/code-graph):
  { meta:{source, sha, date, nodes_total, edges_total, reduced:bool},
    nodes:[{id, label, group, kind, files[], loc, fan_in, fan_out, desc}],
    edges:[{from, to, kind, weight, evidence:"EXTRACTED"|"INFERRED"}],
    communities:{<group>:{label, color}} }

Reducción (sin dependencias externas):
 1. Pliega símbolos a nivel módulo/fichero (id estable = ruta del módulo).
 2. Comunidades por label-propagation simple (semilla = primer directorio del path).
 3. LAYOUT PRECALCULADO por comunidad (grid por columnas) → la página no necesita d3 y las
    aristas se enrutan por pasillos (mata el anti-pattern "líneas cruzando cajas").
 4. Cap de tamaño: conserva top-N por (fan_in+fan_out); resto se agrega en un nodo "(+K más)".
 5. Toda arista derivada de import/call directa = EXTRACTED; el resto = INFERRED.
"""
import json
import sys

PALETTE = ["#1b2a4a", "#2563eb", "#6d28d9", "#15803d", "#b45309", "#0e7490", "#be123c", "#4338ca"]


def fixture():
    """Dataset sintético (proyecto Django+React de juguete) para prototipar structure.html sin indexar nada."""
    groups = {
        "api": {"label": "Backend · API", "color": PALETTE[0]},
        "core": {"label": "Backend · Core", "color": PALETTE[3]},
        "front": {"label": "Frontend", "color": PALETTE[1]},
        "infra": {"label": "Infra / config", "color": PALETTE[4]},
    }
    nodes = [
        ("apps/clients/api.py", "clients.api", "api", 210, 3, 2, "ViewSets y serializers de clientes"),
        ("apps/clients/models.py", "clients.models", "core", 140, 5, 1, "Modelo Client + managers"),
        ("apps/billing/api.py", "billing.api", "api", 260, 2, 3, "Endpoints de facturación"),
        ("apps/billing/models.py", "billing.models", "core", 180, 4, 1, "Invoice, Payment"),
        ("apps/billing/services.py", "billing.services", "core", 320, 3, 4, "Lógica de cobro e idempotencia"),
        ("apps/core/auth.py", "core.auth", "core", 90, 6, 0, "JWT + permisos"),
        ("apps/core/utils.py", "core.utils", "core", 75, 7, 0, "slugify, fechas, money"),
        ("frontend/src/store.ts", "store", "front", 150, 4, 2, "Zustand store global"),
        ("frontend/src/api/client.ts", "api.client", "front", 110, 5, 1, "Cliente HTTP tipado"),
        ("frontend/src/pages/Dashboard.tsx", "Dashboard", "front", 240, 0, 4, "Página principal"),
        ("frontend/src/pages/Invoices.tsx", "Invoices", "front", 190, 0, 3, "Listado y detalle de facturas"),
        ("config/settings.py", "settings", "infra", 130, 8, 0, "Django settings"),
        ("config/celery.py", "celery", "infra", 45, 2, 1, "Tareas programadas"),
    ]
    edges = [
        ("apps/clients/api.py", "apps/clients/models.py", "import", "EXTRACTED"),
        ("apps/clients/api.py", "apps/core/auth.py", "import", "EXTRACTED"),
        ("apps/billing/api.py", "apps/billing/services.py", "call", "EXTRACTED"),
        ("apps/billing/services.py", "apps/billing/models.py", "import", "EXTRACTED"),
        ("apps/billing/services.py", "apps/clients/models.py", "import", "EXTRACTED"),
        ("apps/billing/services.py", "apps/core/utils.py", "call", "EXTRACTED"),
        ("apps/billing/api.py", "apps/core/auth.py", "import", "EXTRACTED"),
        ("config/celery.py", "apps/billing/services.py", "call", "EXTRACTED"),
        ("frontend/src/pages/Dashboard.tsx", "frontend/src/store.ts", "import", "EXTRACTED"),
        ("frontend/src/pages/Invoices.tsx", "frontend/src/store.ts", "import", "EXTRACTED"),
        ("frontend/src/store.ts", "frontend/src/api/client.ts", "import", "EXTRACTED"),
        ("frontend/src/api/client.ts", "apps/billing/api.py", "http", "INFERRED"),
        ("frontend/src/api/client.ts", "apps/clients/api.py", "http", "INFERRED"),
        ("apps/clients/models.py", "config/settings.py", "import", "EXTRACTED"),
        ("apps/billing/models.py", "config/settings.py", "import", "EXTRACTED"),
    ]
    ns = [{"id": i, "label": l, "group": g, "kind": "module", "files": [i], "loc": loc,
           "fan_in": fi, "fan_out": fo, "desc": d} for i, l, g, loc, fi, fo, d in nodes]
    es = [{"from": a, "to": b, "kind": k, "weight": 1, "evidence": ev} for a, b, k, ev in edges]
    return {"meta": {"source": "FIXTURE sintético (report_kit/graph_reduce.py --fixture)",
                     "sha": "fixture", "date": "", "nodes_total": len(ns), "edges_total": len(es),
                     "reduced": False},
            "nodes": ns, "edges": es, "communities": groups}


def reduce_graph(src_path, max_nodes=800, max_edges=2000):
    raw = json.load(open(src_path, encoding="utf-8"))
    # node-link de NetworkX: {nodes:[{id,...}], links:[{source,target,...}]}
    raw_nodes = raw.get("nodes", [])
    raw_edges = raw.get("links") or raw.get("edges") or []

    def module_of(nid):
        s = str(nid)
        return s.split("::")[0].split("#")[0]

    mods = {}
    for n in raw_nodes:
        m = module_of(n.get("id"))
        d = mods.setdefault(m, {"id": m, "label": m.split("/")[-1], "kind": "module",
                                "files": [m], "loc": 0, "fan_in": 0, "fan_out": 0,
                                "desc": "", "group": (m.split("/")[0] if "/" in m else "root")})
        d["loc"] += int(n.get("loc", 0) or 0)

    agg = {}
    for e in raw_edges:
        a, b = module_of(e.get("source")), module_of(e.get("target"))
        if a == b or a not in mods or b not in mods:
            continue
        key = (a, b, e.get("kind", "dep"))
        agg[key] = agg.get(key, 0) + 1
    edges = [{"from": a, "to": b, "kind": k, "weight": w,
              "evidence": "EXTRACTED" if k in ("import", "call", "inherit") else "INFERRED"}
             for (a, b, k), w in agg.items()]
    for e in edges:
        mods[e["from"]]["fan_out"] += e["weight"]
        mods[e["to"]]["fan_in"] += e["weight"]

    # comunidades: 3 rondas de label propagation con semilla por primer directorio
    labels = {m: d["group"] for m, d in mods.items()}
    neigh = {}
    for e in edges:
        neigh.setdefault(e["from"], []).append(e["to"])
        neigh.setdefault(e["to"], []).append(e["from"])
    for _ in range(3):
        for m in sorted(mods):
            votes = {}
            for nb in neigh.get(m, []):
                votes[labels[nb]] = votes.get(labels[nb], 0) + 1
            if votes:
                labels[m] = max(sorted(votes), key=lambda k: votes[k])
    for m, d in mods.items():
        d["group"] = labels[m]

    # cap por relevancia
    ranked = sorted(mods.values(), key=lambda d: -(d["fan_in"] + d["fan_out"]))
    keep = {d["id"] for d in ranked[:max_nodes]}
    dropped = len(mods) - len(keep)
    nodes = [d for d in ranked if d["id"] in keep]
    edges = sorted([e for e in edges if e["from"] in keep and e["to"] in keep],
                   key=lambda e: -e["weight"])[:max_edges]
    if dropped > 0:
        nodes.append({"id": "__rest__", "label": f"(+{dropped} módulos más)", "group": "rest",
                      "kind": "aggregate", "files": [], "loc": 0, "fan_in": 0, "fan_out": 0,
                      "desc": "módulos bajo el cap de relevancia — reindexar con --max-nodes mayor"})

    communities = {}
    for i, g in enumerate(sorted({d["group"] for d in nodes})):
        communities[g] = {"label": g, "color": PALETTE[i % len(PALETTE)]}

    return {"meta": {"source": src_path, "sha": raw.get("meta", {}).get("sha", ""),
                     "date": raw.get("meta", {}).get("date", ""),
                     "nodes_total": len(raw_nodes), "edges_total": len(raw_edges),
                     "reduced": dropped > 0},
            "nodes": nodes, "edges": edges, "communities": communities}


def main():
    args = sys.argv[1:]
    if not args:
        sys.exit(__doc__)
    if args[0] == "--fixture":
        out = args[1] if len(args) > 1 else "graph-dataset.json"
        data = fixture()
    else:
        src, out = args[0], (args[1] if len(args) > 1 else "graph-dataset.json")
        mn = int(args[args.index("--max-nodes") + 1]) if "--max-nodes" in args else 800
        me = int(args[args.index("--max-edges") + 1]) if "--max-edges" in args else 2000
        data = reduce_graph(src, mn, me)
    json.dump(data, open(out, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    size = len(json.dumps(data))
    print(f"Escrito {out} — {len(data['nodes'])} nodos, {len(data['edges'])} aristas, {size/1024:.0f}KB"
          + (" ⚠️ >1MB, sube la reducción" if size > 1_000_000 else ""))


if __name__ == "__main__":
    main()
