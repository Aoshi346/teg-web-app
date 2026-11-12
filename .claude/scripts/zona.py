#!/usr/bin/env python3
"""zona.py — ¿en qué zona (verde / amarilla / roja) cae esta ruta, según el mapa que firmó una persona?

POR QUÉ (EQ-D24, sub-ola 3.11). El auditor de impacto y la autonomía del agente necesitan saber dónde
pisan, y ese juicio no se le delega al agente: el mapa lo dibuja y lo firma una persona
(`templates/zonas.yaml` → `.claude/zonas.yaml` del proyecto). Política: `rules/audit-team.md` §9.

Uso:
    zona.py <ruta> [<ruta>…] [--mapa .claude/zonas.yaml] [--json]
    git diff --name-only develop | xargs python3 .claude/scripts/zona.py   # las zonas de un diff

SALIDA. Una línea por ruta (`roja  backend/apps/auth/views.py  ← autenticación y permisos`) y el código
del color MÁS ALTO tocado: 0 verde · 1 amarilla · 3 roja · 2 = no se pudo leer el mapa. Sin mapa, o sin
`firmado_por`, todo es amarillo (exit 1) y se dice: un mapa sin firma no es el juicio de nadie.
Lo que no casa con ninguna regla, amarillo. La primera regla que casa manda.
"""
import argparse
import fnmatch
import json
import os
import sys

CODE = {"verde": 0, "amarilla": 1, "roja": 3}


def load(path):
    try:
        import yaml
    except ImportError:
        print("zona.py necesita PyYAML (pip install pyyaml)", file=sys.stderr)
        sys.exit(2)
    try:
        data = yaml.safe_load(open(path, encoding="utf-8")) or {}
    except FileNotFoundError:
        return None
    except (OSError, yaml.YAMLError) as exc:
        print(f"NO SE PUDO LEER el mapa {path}: {exc}", file=sys.stderr)
        sys.exit(2)
    for z in data.get("zonas") or []:
        if z.get("color") not in CODE:
            print(f"mapa {path}: color {z.get('color')!r} en {z.get('ruta')!r} (verde | amarilla | roja)",
                  file=sys.stderr)
            sys.exit(2)
    return data


def classify(path, data):
    p = path[2:] if path.startswith("./") else path
    for z in (data or {}).get("zonas") or []:
        pat = z.get("ruta", "")
        if fnmatch.fnmatch(p, pat) or (pat.endswith("/**") and (p == pat[:-3] or p.startswith(pat[:-2]))):
            return z["color"], z.get("porque", "")
    return "amarilla", "no casa con ninguna regla del mapa"


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("rutas", nargs="*")
    ap.add_argument("--mapa", default=None)
    ap.add_argument("--json", action="store_true")
    a = ap.parse_args()
    root = os.environ.get("CLAUDE_PROJECT_DIR") or os.getcwd()
    mp = a.mapa or os.path.join(root, ".claude", "zonas.yaml")
    data = load(mp)
    signed = bool(data and str(data.get("firmado_por") or "").strip())
    rutas = a.rutas or [l.strip() for l in sys.stdin if l.strip()]
    rows = []
    for r in rutas:
        rel = os.path.relpath(os.path.realpath(r), os.path.realpath(root)) if os.path.isabs(r) else r
        color, why = classify(rel, data) if signed else ("amarilla", "mapa sin firmar" if data else "sin mapa")
        rows.append({"ruta": rel, "color": color, "porque": why})
    worst = max((CODE[x["color"]] for x in rows), default=CODE["amarilla"] if not signed else 0)
    if a.json:
        print(json.dumps({"mapa": mp, "firmado": signed, "rutas": rows}, ensure_ascii=False, indent=2))
    else:
        if not signed:
            print(f"⚠️  {'mapa sin firmar' if data else 'sin mapa'} ({mp}): todo cuenta como AMARILLO "
                  "hasta que una persona lo dibuje y firme (templates/zonas.yaml)")
        for x in rows:
            print(f"{x['color']:9} {x['ruta']}  ← {x['porque']}")
    return worst


if __name__ == "__main__":
    sys.exit(main())
