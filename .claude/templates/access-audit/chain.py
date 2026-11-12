#!/usr/bin/env python3
"""chain.py — seudónimo, verificación de la cadena y ancla del registro de accesos.

Patrón: .claude/patterns/stack/backend-access-audit.md. Va con schema.sql: la forma canónica de
aquí y la del trigger tienen que coincidir carácter a carácter.

    # 1. Exportar (sin driver: psql basta)
    psql -At -c "$(python3 chain.py export-sql)" > eventos.jsonl
    # 2. Verificar la cadena; con --anchors, también contra las cabezas publicadas fuera
    python3 chain.py verify eventos.jsonl [--anchors anclas.json]
    # 3. Cabeza de cada segmento, para publicarla fuera del servidor (el ancla)
    python3 chain.py heads eventos.jsonl > anclas-nuevas.json

Exit: 0 cadena íntegra · 1 hay filas alteradas, huecos o cabezas que no casan con el ancla.
Sin dependencias fuera de la biblioteca estándar.
"""
from __future__ import annotations

import argparse
import hashlib
import hmac
import json
import sys
from collections import defaultdict
from typing import Iterable

GENESIS = "0" * 64
PARTS = ("segment", "seq", "ts", "actor_id", "actor_role", "subject_ref", "resource", "fields",
         "action", "result", "reason", "context")

# El orden de las columnas es el de PARTS; ts con el mismo formato que usa el trigger.
EXPORT_SQL = (
    "SELECT json_build_object('segment', segment::text, 'seq', seq::text, "
    "'ts', to_char(ts AT TIME ZONE 'UTC', 'YYYY-MM-DD\"T\"HH24:MI:SS.US\"Z\"'), "
    "'actor_id', actor_id, 'actor_role', actor_role, 'subject_ref', subject_ref, "
    "'resource', resource, 'fields', fields, 'action', action, 'result', result, "
    "'reason', reason, 'context', context, 'prev_hash', prev_hash, 'hash', hash) "
    "FROM access_event ORDER BY segment, seq"
)


def pseudonym(key: bytes, subject_id: object, kind: str = "subject") -> str:
    """Referencia seudónima de una persona: HMAC con clave, nunca un hash sin clave."""
    digest = hmac.new(key, f"{kind}:{subject_id}".encode(), hashlib.sha256).hexdigest()
    return f"{kind}:{digest[:32]}"


def canon(row: dict) -> str:
    return "|".join(f"{len(str(row[p]))}:{row[p]}" for p in PARTS)


def row_hash(prev_hash: str, row: dict) -> str:
    return hashlib.sha256((prev_hash + canon(row)).encode("utf-8")).hexdigest()


def verify(rows: Iterable[dict], anchors: dict[str, dict] | None = None) -> list[str]:
    """Problemas encontrados; lista vacía = íntegra (y casa con el ancla, si se da)."""
    problems: list[str] = []
    by_segment: dict[str, list[dict]] = defaultdict(list)
    for r in rows:
        by_segment[r["segment"]].append(r)
    for segment, items in sorted(by_segment.items()):
        items.sort(key=lambda r: int(r["seq"]))
        prev = GENESIS
        for expected_seq, r in enumerate(items, start=1):
            if int(r["seq"]) != expected_seq:
                problems.append(f"{segment}: falta la fila {expected_seq} (hay {r['seq']})")
                break
            if r["prev_hash"] != prev:
                problems.append(f"{segment}#{r['seq']}: prev_hash no encadena con la fila anterior")
            if row_hash(r["prev_hash"], r) != r["hash"]:
                problems.append(f"{segment}#{r['seq']}: el contenido no corresponde a su hash")
            prev = r["hash"]
    for segment, head in sorted((anchors or {}).items()):
        items = by_segment.get(segment, [])
        published = {int(r["seq"]): r["hash"] for r in items}
        if published.get(int(head["seq"])) != head["hash"]:
            problems.append(f"{segment}: la fila {head['seq']} no casa con el ancla publicada")
    return problems


def heads(rows: Iterable[dict]) -> dict[str, dict]:
    out: dict[str, dict] = {}
    for r in rows:
        cur = out.get(r["segment"])
        if cur is None or int(r["seq"]) > int(cur["seq"]):
            out[r["segment"]] = {"seq": str(r["seq"]), "hash": r["hash"]}
    return out


def _load(path: str) -> list[dict]:
    with open(path, encoding="utf-8") as f:
        return [json.loads(line) for line in f if line.strip()]


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    sub = ap.add_subparsers(dest="cmd", required=True)
    sub.add_parser("export-sql")
    v = sub.add_parser("verify")
    v.add_argument("rows")
    v.add_argument("--anchors")
    h = sub.add_parser("heads")
    h.add_argument("rows")
    a = ap.parse_args(argv)
    if a.cmd == "export-sql":
        print(EXPORT_SQL)
        return 0
    rows = _load(a.rows)
    if a.cmd == "heads":
        print(json.dumps(heads(rows), indent=1, sort_keys=True))
        return 0
    anchors = json.load(open(a.anchors, encoding="utf-8")) if a.anchors else None
    problems = verify(rows, anchors)
    for p in problems:
        print(f"✗ {p}")
    if not problems:
        print(f"✓ {len(rows)} filas, cadena íntegra" + (" y casa con el ancla" if anchors else ""))
    return 1 if problems else 0


if __name__ == "__main__":
    sys.exit(main())
