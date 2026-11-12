#!/usr/bin/env python3
"""
Paso 4 — Conciliación. Funde verdicts.json (salida del Paso 2) en items.json:
  por item -> verdict, why, howto, confidence, precision_pct, interpretacion, viewport, anchors,
  after=shots/items/<ID>.jpg, before2=shots/items_pre/<ID>.jpg (si existen), status final.
Recalcula meta.verification y conteos; escribe deltas.json (cambios de estado entre rondas).
Read-only salvo escribir items.json y deltas.json.

Uso:
    python3 reconcile.py <audit_dir>
"""
import json, os, sys
from collections import Counter

V2STATUS = {"done": "done", "partial": "backlog", "notdone": "backlog",
            "blocked": "blocked", "review": "review"}


def load_results(verd):
    vd = json.load(open(verd))
    res = {}
    if isinstance(vd, dict) and "pages" in vd:
        for pg in vd["pages"]:
            for r in pg.get("results", []):
                res[r["id"]] = r
    elif isinstance(vd, list):
        for r in vd:
            res[r["id"]] = r
    return res


def main(audit_dir):
    items_path = os.path.join(audit_dir, "items.json")
    d = json.load(open(items_path))
    items = {it["id"]: it for it in d["items"]}
    results = load_results(os.path.join(audit_dir, "verdicts.json"))

    missing, deltas = [], []
    for iid, it in items.items():
        r = results.get(iid)
        if not r:
            missing.append(iid)
            it.setdefault("verdict", "review")
            it.setdefault("why", "(sin veredicto del workflow; re-verificar a mano)")
            continue
        prev = it.get("status")
        it["prev_status"] = prev
        it["verdict"] = r["verdict"]
        it["why"] = r.get("why", "")
        it["howto"] = r.get("howto", "")
        it["confidence"] = r.get("confidence", "")
        pct = r.get("precision_pct")
        if pct is None:
            pct = {"alta": 95, "media": 80, "baja": 50}.get(r.get("confidence", ""), 60)
        it["precision_pct"] = round(pct)
        it["interpretacion"] = r.get("interpretacion", "")
        it["viewport"] = r.get("viewport", "desktop")
        it["anchor_type"] = r.get("anchor_type", "")
        it["anchor_value"] = r.get("anchor_value", "")
        newst = V2STATUS.get(r["verdict"], "backlog")
        it["status"] = newst
        cap = f"shots/items/{iid}.jpg"
        if os.path.exists(os.path.join(audit_dir, cap)):
            it["after"] = cap
        pre = f"shots/items_pre/{iid}.jpg"
        if os.path.exists(os.path.join(audit_dir, pre)):
            it["before2"] = pre
        fix = f"shots/items_after/{iid}.jpg"
        if os.path.exists(os.path.join(audit_dir, fix)):
            it["after_fix"] = fix
        if prev != newst:
            deltas.append({"id": iid, "from": prev, "to": newst, "verdict": r["verdict"]})

    d["items"] = list(items.values())
    vc = Counter(it.get("verdict", "review") for it in d["items"])
    sc = Counter(it["status"] for it in d["items"])
    d["meta"]["verification"] = {
        "method": "captura masiva Playwright + workflow 1 agente/página (código+vivo) "
                  "+ captura por item + interpretación y % de precisión",
        "verdict_counts": dict(vc), "status_counts": dict(sc),
        "deltas": len(deltas), "missing_verdicts": len(missing),
    }
    d["meta"]["total"] = len(d["items"])
    json.dump(d, open(items_path, "w"), ensure_ascii=False, indent=1)
    json.dump({"deltas": deltas, "missing": missing},
              open(os.path.join(audit_dir, "deltas.json"), "w"), ensure_ascii=False, indent=1)
    print("verdict_counts:", dict(vc))
    print("status_counts :", dict(sc))
    print("deltas:", len(deltas), "| sin veredicto:", len(missing), missing[:10])


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else ".")
