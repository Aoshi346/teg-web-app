#!/usr/bin/env python3
"""Gate G1 de secretos en LOGS y documentos: ¿hay una credencial escrita donde no debe? (SE-17, U.06)

POR QUÉ, y en qué se diferencia de `scan_secretos_diff.py`. Aquel mira lo que AÑADE un commit y vive en
el pre-commit. Este mira lo que ya está ESCRITO en los sitios donde el harness vuelca texto del agente o
del Usuario, que no siempre pasan por git: el audit log (`~/.claude/audit/<proyecto>.jsonl`, fuera del
repo a propósito), `PROGRESS.log`, `PROGRESS.auto.log`, los `pending-tasks.md` y `.docs/`. Desde U.06
los hooks redactan en origen con `redactar.py`; este gate es el control de que de verdad no entra nada,
y el inventario de lo que entró antes (lo que se re-sella en la sub-ola 2.27).

Detecta con la MISMA librería que redacta (`redactar.find_secrets`: formatos de proveedor + credenciales
por contexto, sin valores de ejemplo, rutas ni referencias de código), así que lo que el gate señala es
exactamente lo que los hooks habrían tapado. NUNCA imprime el valor, ni un trozo: tipo, ruta, línea y longitud.

Escáner externo. Si `gitleaks` está en el PATH y es la versión FIJADA (`GITLEAKS_PIN`, la misma imagen
que `templates/tools-stack/compose.yml`), se corre además `gitleaks dir --redact` sobre cada objetivo.
Otra versión no se usa: Betterleaks v2 y las próximas de Gitleaks cambian CLI, configuración y formato,
y un escáner que no entendemos no puede decir «limpio». Sin él, el gate funciona igual y lo dice.

Límites declarados: no mira `resources/` (corpus descargados), `_fixtures/` (secretos de mentira de los
gates), `worktrees/` (otras sesiones), ficheros de más de 2 MB o binarios, ni líneas de más de 4000
caracteres (HTML y JSON generados: lo que importa son los logs, de línea corta). El tope de 2 MB no
vale para `.log` ni `.jsonl`, y los documentos saltados por tamaño se cuentan en la salida; una línea marcada `tl-secret-ok: <razón>` no cuenta; lo que
`redactar.py` no reconoce, este gate tampoco lo ve.

Uso:
    gate_secretos.py                          # los objetivos por defecto del proyecto (cwd o --root)
    gate_secretos.py RUTA [RUTA…]             # solo esas rutas (fichero o carpeta)
    gate_secretos.py --since 2026-10-27       # en el audit log, solo las entradas desde esa fecha
    gate_secretos.py --no-audit               # sin el audit log de ~/.claude/audit/
    gate_secretos.py --audit-only --since HOY # solo el audit log (hook Stop, 2.27)
    gate_secretos.py --staged                 # además, el diff staged (delega en scan_secretos_diff.py)
Salida: 0 limpio · 1 hay secreto · 2 NO SE PUDO MEDIR (una ruta pedida no existe o no se pudo leer).
"""
from __future__ import annotations

import argparse
import json
import os
import re
import shutil
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from redactar import find_secrets  # noqa: E402
from scan_secretos_diff import MARCA_OK  # noqa: E402

GITLEAKS_PIN = "8.30.1"  # = docker.io/zricethezav/gitleaks:v8.30.1 en templates/tools-stack/compose.yml
MAX_BYTES = 2_000_000
MAX_LINE = 4000  # como scan_secretos_diff.py: una línea más larga es HTML/JSON generado, no un log
SKIP_DIRS = {".git", "node_modules", ".venv", "venv", "__pycache__", "resources", "_fixtures", "worktrees"}


def default_targets(root: Path) -> list[Path]:
    """Dónde vuelca texto el harness, en el proyecto."""
    targets = [root / ".claude" / "PROGRESS.log", root / ".claude" / "PROGRESS.auto.log",
               root / "PROGRESS.log", root / "pending-tasks.md", root / ".docs"]
    return [t for t in targets if t.exists()]


def audit_log_path(root: Path) -> Path:
    """La misma ruta que calcula `hooks/audit-log.sh`: la clave es la raíz del repo PRINCIPAL (2.27)."""
    from audit_log import audit_file  # noqa: E402  (misma carpeta)
    return audit_file(root)


def iter_files(target: Path):
    if target.is_file():
        yield target
        return
    for dp, dn, fn in os.walk(target):
        dn[:] = [d for d in dn if d not in SKIP_DIRS]
        for f in sorted(fn):
            yield Path(dp) / f


def scan_text_line(rel: str, n: int, line: str) -> list[dict]:
    """Hallazgos de una línea, con la librería de redacción."""
    if len(line) > MAX_LINE or MARCA_OK.search(line):
        return []
    return [{"path": rel, "line": n, "kind": h["kind"], "length": h["length"]} for h in find_secrets(line)]


LOG_SUFFIXES = {".jsonl", ".log"}
SKIPPED_BIG: list[str] = []  # se dice al final: un fichero saltado no es un fichero limpio


def scan_file(path: Path, rel: str, since: str | None = None) -> list[dict] | None:
    """None = no se pudo leer. Se lee línea a línea (el audit log pasa de 8 MB). El tope de tamaño vale
    para documentos, NUNCA para logs: un log grande es justo el que más tiene que mirarse.
    Un .jsonl se mira campo a campo (el escapado JSON confunde las regex)."""
    try:
        if path.suffix not in LOG_SUFFIXES and path.stat().st_size > MAX_BYTES:
            SKIPPED_BIG.append(rel)
            return []
        hits: list[dict] = []
        with open(path, encoding="utf-8") as fh:
            for n, raw in enumerate(fh, 1):
                line = raw.rstrip("\n")
                if path.suffix == ".jsonl":
                    try:
                        rec = json.loads(line)
                    except json.JSONDecodeError:
                        rec = None
                    if isinstance(rec, dict):
                        if since and str(rec.get("ts", "")) < since:
                            continue
                        for value in rec.values():
                            if isinstance(value, str):
                                hits += scan_text_line(rel, n, value)
                        continue
                hits += scan_text_line(rel, n, line)
        return hits
    except UnicodeDecodeError:
        return []  # binario: fuera de alcance, declarado
    except OSError:
        return None


def gitleaks_status() -> tuple[bool, str]:
    exe = shutil.which("gitleaks")
    if not exe:
        return False, "gitleaks no está instalado: solo el escáner propio (redactar.py)"
    try:
        out = subprocess.run([exe, "version"], capture_output=True, text=True, timeout=20).stdout.strip()
    except (OSError, subprocess.TimeoutExpired) as e:
        return False, f"gitleaks no responde ({e}): solo el escáner propio"
    if out.lstrip("v") != GITLEAKS_PIN:
        return False, f"gitleaks {out} no es la versión fijada {GITLEAKS_PIN}: no se usa"
    return True, f"gitleaks {GITLEAKS_PIN}"


def run_gitleaks(target: Path) -> bool:
    """True si gitleaks encontró algo (su salida ya va redactada)."""
    r = subprocess.run(["gitleaks", "dir", "--redact", "--no-banner", "--exit-code", "1", str(target)],
                       capture_output=True, text=True)
    if r.returncode == 1:
        print((r.stdout or r.stderr).strip())
        return True
    return False


def main() -> int:
    ap = argparse.ArgumentParser(description="Secretos escritos en logs y documentos del harness.")
    ap.add_argument("paths", nargs="*", help="rutas concretas (por defecto, las del proyecto)")
    ap.add_argument("--root", default=".", help="raíz del proyecto (por defecto, la carpeta actual)")
    ap.add_argument("--since", help="audit log: solo entradas con ts >= esta fecha (YYYY-MM-DD)")
    ap.add_argument("--no-audit", action="store_true", help="no mirar ~/.claude/audit/<proyecto>.jsonl")
    ap.add_argument("--staged", action="store_true", help="además, el diff staged (scan_secretos_diff.py)")
    ap.add_argument("--audit-only", action="store_true",
                    help="solo el audit log del proyecto (lo que corre el hook Stop, 2.27); con --since se "
                         "saltan los segmentos rotados antes de esa fecha")
    a = ap.parse_args()

    root = Path(a.root).resolve()
    if a.paths:
        targets = [Path(p).resolve() for p in a.paths]
        missing = [str(t) for t in targets if not t.exists()]
        if missing:
            print(f"NO SE PUDO MEDIR: no existe {', '.join(missing)}", file=sys.stderr)
            return 2
    else:
        targets = [] if a.audit_only else default_targets(root)
        if not a.no_audit:  # el log del proyecto y sus segmentos rotados (rotados/, 2.27)
            from audit_log import segments  # noqa: E402
            segs = segments(audit_log_path(root))
            if a.since:  # rotados/<clave>.AAAAMMDDTHHMMSSZ.jsonl: lo rotado antes de --since no tiene nada nuevo
                stamp = a.since.replace("-", "")
                segs = [s for s in segs if s.parent.name != "rotados" or s.stem.rsplit(".", 1)[-1][:8] >= stamp]
            targets += segs

    hits: list[dict] = []
    unreadable: list[str] = []
    for target in targets:
        for f in iter_files(target):
            try:
                rel = str(f.relative_to(root))
            except ValueError:
                rel = str(f).replace(os.path.expanduser("~"), "~", 1)
            res = scan_file(f, rel, a.since)
            if res is None:
                unreadable.append(rel)
            else:
                hits += res

    ok, note = gitleaks_status()
    print(f"gate_secretos: {note}", file=sys.stderr)
    external = ok and any(run_gitleaks(t) for t in targets)

    staged_rc = 0
    if a.staged:
        staged_rc = subprocess.run([sys.executable, os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                                                 "scan_secretos_diff.py")]).returncode

    if SKIPPED_BIG:
        print(f"gate_secretos: {len(SKIPPED_BIG)} documento(s) de más de 2 MB sin mirar "
              f"(p. ej. {SKIPPED_BIG[0]})", file=sys.stderr)
    if unreadable:
        print(f"NO SE PUDO MEDIR: no se pudo leer {', '.join(unreadable[:5])}", file=sys.stderr)
        return 2
    if staged_rc == 2:
        return 2
    if hits:
        print(f"SECRETOS ESCRITOS: {len(hits)} línea(s) con patrón de credencial (valores redactados):")
        for h in hits[:30]:
            print(f"  {h['path']}:{h['line']}  {h['kind']}  ({h['length']} caracteres, valor redactado)")
        if len(hits) > 30:
            print(f"  … y {len(hits) - 30} más")
        print("En el audit log: `audit_log.py resellar` lo redacta y rehace la cadena (2.27). Si es un "
              "secreto real, ROTARLO.\nSi es un falso positivo: `tl-secret-ok: <por qué>` en la misma línea.")
    return 1 if (hits or external or staged_rc == 1) else 0


if __name__ == "__main__":
    sys.exit(main())
