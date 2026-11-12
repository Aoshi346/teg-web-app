#!/usr/bin/env python3
"""check_topology.py — ¿los puertos que declara la rule de topología son los que escuchan de verdad?

POR QUÉ (AN-25, cosechado de elvion). Su rule de datastores declaraba seis puertos y cinco eran
falsos; se supo al preparar la migración a otro servidor: una instalación que hubiera seguido la tabla
habría montado un servidor que no habla con sus propias bases. Una tabla de topología escrita a mano
se queda vieja sin avisar; esto la compara con la máquina.

Lee la tabla de la rule (plantilla: `templates/rule-topology.md`): la columna cuyo encabezado contiene
«Puerto host» (o la que diga `--columna`), y saca todos los números de 2-5 cifras de cada celda. Para
cada uno intenta conectar a 127.0.0.1:<puerto>. Solo conecta: no manda nada.

Uso:
    check_topology.py .claude/rules/topologia.md [--columna "Puerto host"] [--host 127.0.0.1]
    check_topology.py --self-test
Exit: 0 todos escuchan · 1 alguno declarado no escucha · 2 no se encontró la tabla (no es un 0).
"""
from __future__ import annotations

import argparse
import re
import socket
import sys
import tempfile

PORT = re.compile(r"\b(\d{2,5})\b")


def declared_ports(text: str, column: str) -> list[tuple[str, int]] | None:
    """Los puertos de la columna `column` de la primera tabla que la tenga (None si ninguna)."""
    blocks, cur = [], []
    for ln in text.splitlines() + [""]:
        if ln.strip().startswith("|"):
            cur.append([c.strip() for c in ln.strip().strip("|").split("|")])
        elif cur:
            blocks.append(cur)
            cur = []
    for rows in blocks:
        hits = [i for i, c in enumerate(rows[0]) if column.lower() in c.lower()]
        if not hits:
            continue
        idx, out = hits[0], []
        for cells in rows[1:]:
            if set("".join(cells)) <= set("-: ") or len(cells) <= idx:
                continue
            name = re.sub(r"[*`]", "", cells[0])
            for m in PORT.finditer(cells[idx]):
                if 1 <= int(m.group(1)) <= 65535:
                    out.append((name, int(m.group(1))))
        return out
    return None


def listening(host: str, port: int) -> bool:
    try:
        with socket.create_connection((host, port), timeout=1.5):
            return True
    except OSError:
        return False


def check(text: str, column: str, host: str) -> tuple[int, list[str]]:
    ports = declared_ports(text, column)
    if not ports:
        return 2, [f"✗ no hay una tabla con puertos en la columna «{column}»: no se puede medir"]
    lines, bad = [], 0
    for name, p in ports:
        ok = listening(host, p)
        bad += not ok
        lines.append(f"  {'✓' if ok else '✗'} {name}: {p}" + ("" if ok else " — declarado y NADIE escucha"))
    lines.append(f"{len(ports) - bad}/{len(ports)} puertos declarados escuchan en {host}")
    return (1 if bad else 0), lines


def self_test() -> int:
    srv = socket.socket()
    srv.bind(("127.0.0.1", 0))
    srv.listen(16)
    up = srv.getsockname()[1]
    free = socket.socket()
    free.bind(("127.0.0.1", 0))
    down = free.getsockname()[1]
    free.close()
    rule = ("| Store | Rol | Puerto host | Puerto contenedor |\n|---|---|---|---|\n"
            f"| **PostgreSQL** | BD | **{up}** | 5432 |\n| Redis | caché | **{down}** | 6379 |\n")
    cases = [
        ("un puerto declarado sin nadie escuchando → 1", rule, 1),
        ("todos escuchan → 0", rule.replace(f"**{down}**", f"**{up}**"), 0),
        ("sin tabla de topología → 2 (no un 0)", "# nada\n", 2),
    ]
    failures = 0
    for name, text, want in cases:
        rc, _ = check(text, "Puerto host", "127.0.0.1")
        failures += rc != want
        print(f"  {'✓' if rc == want else '✗'} {name}: {rc}")
    srv.close()
    print("self-test:", "OK" if not failures else f"{failures} FALLO(S)")
    return 1 if failures else 0


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("rule", nargs="?")
    ap.add_argument("--columna", default="Puerto host")
    ap.add_argument("--host", default="127.0.0.1")
    ap.add_argument("--self-test", action="store_true")
    a = ap.parse_args()
    if a.self_test:
        return self_test()
    if not a.rule:
        ap.error("falta la rule")
    try:
        with open(a.rule, encoding="utf-8") as f:
            text = f.read()
    except OSError as e:
        print(f"✗ no se puede leer {a.rule}: {e}")
        return 2
    rc, lines = check(text, a.columna, a.host)
    print("\n".join(lines))
    return rc


if __name__ == "__main__":
    sys.exit(main())
