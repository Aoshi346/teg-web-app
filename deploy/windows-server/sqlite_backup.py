#!/usr/bin/env python3
"""Copia consistente de una base SQLite en uso (API de backup de SQLite, válida con WAL).

Uso: sqlite_backup.py <origen.sqlite3> <destino.sqlite3>
Copiar el fichero con cp mientras gunicorn escribe puede dar una copia corrupta; esto no.
"""

import sqlite3
import sys
from pathlib import Path


def main():
    if len(sys.argv) != 3:
        print(__doc__, file=sys.stderr)
        return 2
    source, target = Path(sys.argv[1]), Path(sys.argv[2])
    target.parent.mkdir(parents=True, exist_ok=True)
    tmp = target.with_suffix(target.suffix + ".tmp")
    src = sqlite3.connect(f"file:{source}?mode=ro", uri=True)
    dst = sqlite3.connect(tmp)
    try:
        src.backup(dst)
    finally:
        dst.close()
        src.close()
    check = sqlite3.connect(tmp)
    try:
        if check.execute("PRAGMA integrity_check").fetchone()[0] != "ok":
            raise SystemExit(f"la copia {tmp} no pasa integrity_check")
    finally:
        check.close()
    tmp.replace(target)
    return 0


if __name__ == "__main__":
    sys.exit(main())
