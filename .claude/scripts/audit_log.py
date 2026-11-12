#!/usr/bin/env python3
"""El audit log del harness: dónde vive, verificar su cadena, buscar en él y re-sellarlo (MO-81, SE-4, 2.27).

POR QUÉ. `hooks/audit-log.sh` escribe una línea por herramienta en `~/.claude/audit/<clave>.jsonl` con una
cadena de hashes (`prev` = hash de la anterior, `h` = hash de esta). Un log que nadie puede verificar ni
leer no audita nada, y este no tenía ni lo uno ni lo otro: solo `--verify` del fichero actual. Aquí viven
las cuatro piezas que lo hacen utilizable, y el hook delega en ellas su `--verify`.

LA CLAVE es la RAÍZ DEL REPO PRINCIPAL (`git rev-parse --git-common-dir`), no el nombre de la carpeta:
antes cada worktree escribía en su propio `<carpeta>.jsonl` (los de AMC en `clientes.jsonl`,
`correo.jsonl`…, que chocarían con cualquier otro proyecto con un worktree igual). Fuera de git, la carpeta.

LA ROTACIÓN la hace el hook al escribir: pasado `CLAUDE_AUDIT_MAX_MB` (10 por defecto), el fichero se mueve
a `rotados/<clave>.<fecha>.jsonl` y el nuevo empieza con una línea `_rotation` cuyo `prev` es el último
hash del segmento rotado. La cadena no se corta: `verificar` recorre los segmentos en orden. Los rotados
no se borran (es un log de auditoría): se archivan o se borran a mano.

EL RE-SELLADO (`resellar`) pasa cada valor viejo por `redactar.redact()` y rehace la cadena desde el
génesis, bajo el mismo `flock` que usa el hook y con fichero temporal + rename en la misma carpeta. Pierde
la prueba de no manipulación de lo anterior (aceptado por el Usuario, 18-10) y lo deja escrito: añade una
línea `_reseal` con cuántas líneas había y cuántas se redactaron. NO guarda copia de lo anterior
(decisión del Usuario, 28-10: ni en claro ni cifrada).

Uso:
    audit_log.py ruta [--proyecto DIR]                 # el fichero que le toca a ese proyecto
    audit_log.py verificar [FICHERO…] [--todos]        # 0 íntegra · 1 rota · 2 no se pudo leer
    audit_log.py buscar REGEX [--tool Bash] [--desde AAAA-MM-DD] [--hasta …] [--todos] [--limite N]
    audit_log.py resellar FICHERO… | --todos [--motivo TEXTO]
Por defecto se trabaja sobre el log del proyecto de `--proyecto` (o la carpeta actual). Respeta CLAUDE_AUDIT_DIR.
"""
from __future__ import annotations

import argparse
import fcntl
import hashlib
import json
import os
import re
import subprocess
import sys
import tempfile
from datetime import datetime, timezone
from pathlib import Path

GENESIS = "0" * 64
ROTATED_DIR = "rotados"
FIXED_FIELDS = {"ts", "tool", "prev", "h"}
# la primera línea de un segmento tras rotar (la escribe el hook, no una herramienta); «_rotacion» es el
# nombre que llevó el 28-10, antes de pasarlo a inglés, y se sigue aceptando
ROTATION_TOOLS = {"_rotation", "_rotacion"}


# ------------------------------------------------------------------------------------------- dónde
def audit_dir() -> Path:
    return Path(os.environ.get("CLAUDE_AUDIT_DIR") or Path.home() / ".claude" / "audit")


def key_root(project_dir: str | os.PathLike) -> Path:
    """Raíz del repo PRINCIPAL: la misma para todos sus worktrees. Lo mismo que calcula audit-log.sh."""
    project_dir = str(project_dir)

    def git(*args: str) -> str:
        try:
            r = subprocess.run(["git", "-C", project_dir, *args], capture_output=True, text=True, timeout=10)
        except (OSError, subprocess.TimeoutExpired):
            return ""
        return r.stdout.strip() if r.returncode == 0 else ""

    common = git("rev-parse", "--path-format=absolute", "--git-common-dir")
    if common and os.path.basename(common) == ".git":
        return Path(os.path.dirname(common))
    top = git("rev-parse", "--show-toplevel")  # submódulo, repo con GIT_DIR raro…
    return Path(top or project_dir)


def slug_for(root: Path) -> str:
    return re.sub(r"[^A-Za-z0-9_.-]", "-", root.name) or "proyecto"


def audit_file(project_dir: str | os.PathLike = ".") -> Path:
    """El fichero en el que escribe hooks/audit-log.sh para ese proyecto."""
    return audit_dir() / f"{slug_for(key_root(Path(project_dir).resolve()))}.jsonl"


def segments(current: Path) -> list[Path]:
    """Los segmentos rotados de ese log, del más viejo al más nuevo, y el actual al final."""
    rot = current.parent / ROTATED_DIR
    # solo <clave>.AAAAMMDDTHHMMSSZ.jsonl: con un glob `<clave>.*` el log de `foo` se llevaba los rotados de
    # `foo.bar` (hallazgo del verificador de la 2.27)
    own = re.compile(re.escape(current.stem) + r"\.\d{8}T\d{6}Z\.jsonl")
    old = sorted(p for p in rot.iterdir() if own.fullmatch(p.name)) if rot.is_dir() else []
    return old + ([current] if current.exists() else [])


def all_logs() -> list[Path]:
    return sorted(p for p in audit_dir().glob("*.jsonl") if p.is_file())


# --------------------------------------------------------------------------------------- la cadena
def record_hash(rec: dict) -> str:
    """El hash de una línea: sobre el JSON compacto SIN `h`, con el orden de claves con que se escribió."""
    core = {k: v for k, v in rec.items() if k != "h"}
    return hashlib.sha256(json.dumps(core, ensure_ascii=False, separators=(",", ":")).encode()).hexdigest()


def seal(rec: dict, prev: str) -> dict:
    out = {k: v for k, v in rec.items() if k not in ("prev", "h")}
    out["prev"] = prev
    out["h"] = record_hash(out)
    return out


def dumps(rec: dict) -> str:
    return json.dumps(rec, ensure_ascii=False, separators=(",", ":"))


def verify_segment(path: Path, expected_prev: str | None) -> tuple[bool, int, str, str]:
    """(ok, entradas, mensaje, último hash). `expected_prev` None = no se sabe qué hay antes (segmento
    suelto): se acepta que empiece por una línea `_rotation`."""
    prev, n = (expected_prev or GENESIS), 0
    with open(path, encoding="utf-8") as fh:
        for i, raw in enumerate(fh, 1):
            raw = raw.strip()
            if not raw:
                continue
            try:
                rec = json.loads(raw)
            except json.JSONDecodeError:
                return False, n, f"ROTA en {path}:{i}: JSON inválido", prev
            if record_hash(rec) != rec.get("h"):
                return False, n, f"ROTA en {path}:{i}: la línea fue modificada", prev
            if n == 0 and expected_prev is None and rec.get("tool") in ROTATION_TOOLS:
                prev = rec.get("prev")  # segmento suelto: su primer eslabón apunta al rotado anterior
            if rec.get("prev") != prev:
                return False, n, f"ROTA en {path}:{i}: eslabón perdido (se borró o se coló una línea antes)", prev
            prev, n = rec["h"], n + 1
    return True, n, "", prev


def verify_chain(current: Path, strict: bool = False) -> tuple[bool, str]:
    """Verifica todos los segmentos de un log en orden, con la continuidad entre ellos."""
    segs = segments(current) if current.parent.name != ROTATED_DIR else [current]
    if not segs:
        return True, f"audit-log: no hay log en {current}"
    # El primer segmento disponible puede empezar por una `_rotation` (los anteriores se archivaron a
    # mano): se acepta y se dice. Entre segmentos, la continuidad se exige.
    prev: str | None = None
    total, first_is_rotation = 0, False
    for s in segs:
        if prev is None:
            with open(s, encoding="utf-8") as fh:
                first = fh.readline() or ""
                first_is_rotation = any(f'"tool":"{t}"' in first for t in ROTATION_TOOLS)
        ok, n, msg, prev = verify_segment(s, prev)
        total += n
        if not ok:
            return False, msg
    extra = f" ({len(segs)} segmentos)" if len(segs) > 1 else ""
    if first_is_rotation:
        extra += "; empieza en una rotación: los segmentos anteriores no están en rotados/"
        if strict:
            return False, f"INCOMPLETA (--estricto): {current}{extra}"
    return True, f"OK - cadena integra, {total} entradas en {current}{extra}"


# --------------------------------------------------------------------------------------- el cerrojo
def open_locked(path: Path, mode: str = "a+b"):
    """Abre el log con flock exclusivo, y comprueba tras el cerrojo que sigue siendo EL fichero: si otro lo
    re-selló o lo rotó mientras se esperaba, el descriptor apunta al viejo y se vuelve a abrir."""
    while True:
        fh = open(path, mode)
        fcntl.flock(fh.fileno(), fcntl.LOCK_EX)
        try:
            if os.fstat(fh.fileno()).st_ino == os.stat(path).st_ino:
                return fh
        except FileNotFoundError:
            pass
        fh.close()


# ------------------------------------------------------------------------------------------ resellar
def _load_redactor():
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    from redactar import redact  # noqa: E402  (falla ruidoso: sin redactor no se re-sella)
    return redact


def _reseal_lines(path: Path, data: bytes, prev: str, redact) -> tuple[list[str], str, int, int]:
    """Redacta cada valor libre y re-encadena. (líneas nuevas, último hash, líneas, líneas redactadas)."""
    lines = [ln for ln in data.decode("utf-8").splitlines() if ln.strip()]
    out, touched = [], 0
    for i, raw in enumerate(lines, 1):
        try:
            rec = json.loads(raw)
        except json.JSONDecodeError as e:
            raise SystemExit(f"{path}:{i}: JSON inválido, no se re-sella nada ({e})")
        changed = False
        for k, v in list(rec.items()):
            if k not in FIXED_FIELDS and isinstance(v, str):
                nv = redact(v)
                if nv != v:
                    rec[k], changed = nv, True
        touched += changed
        rec = seal(rec, prev)
        prev = rec["h"]
        out.append(dumps(rec))
    return out, prev, len(lines), touched


def _write_atomic(path: Path, out: list[str], unchanged=lambda: True) -> bool:
    """Temporal en la MISMA carpeta + fsync + rename (atómico en el mismo sistema de ficheros).
    False si `unchanged()` dice que el original cambió mientras: no se reemplaza nada."""
    fd, tmp = tempfile.mkstemp(prefix=f".{path.name}.", suffix=".tmp", dir=path.parent)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as t:
            t.write("\n".join(out) + "\n")
            t.flush()
            os.fsync(t.fileno())
        os.chmod(tmp, os.stat(path).st_mode & 0o777)
        if not unchanged():
            os.unlink(tmp)
            return False
        os.replace(tmp, path)
    except BaseException:
        if os.path.exists(tmp):
            os.unlink(tmp)
        raise
    dfd = os.open(path.parent, os.O_RDONLY)
    try:
        os.fsync(dfd)
    finally:
        os.close(dfd)
    return True


def reseal(current: Path, reason: str) -> tuple[int, int]:
    """Re-sella un log EN EL SITIO, con sus segmentos rotados en orden. Devuelve (líneas, redactadas).
    Todo bajo el cerrojo del fichero actual, el mismo que toma el hook: mientras dura, el hook espera.
    Sin copia de lo anterior (decisión del Usuario, 28-10)."""
    redact = _load_redactor()
    fh = open_locked(current, "rb")
    try:
        prev, total, touched = GENESIS, 0, 0
        for seg in segments(current)[:-1]:  # los rotados: nadie escribe en ellos
            out, prev, n, k = _reseal_lines(seg, seg.read_bytes(), prev, redact)
            _write_atomic(seg, out)
            total, touched = total + n, touched + k
        data = fh.read()
        while True:
            out, last, n, k = _reseal_lines(current, data, prev, redact)
            mark = seal({"ts": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"), "tool": "_reseal",
                         "lines": total + n, "redacted": touched + k, "reason": reason}, last)
            # un hook de un proyecto derivado que aún no toma el cerrojo puede escribir mientras: si el
            # tamaño cambió entre la lectura y el rename, se relee y se da otra vuelta
            size = len(data)
            if _write_atomic(current, out + [dumps(mark)], lambda: os.stat(current).st_size == size):
                # Lo que un hook sin cerrojo escribió entre la comprobación y el rename quedó en el
                # inodo viejo: se rescata, se redacta y se encadena al final del nuevo.
                fh.seek(size)
                late = fh.read()
                if late.strip():
                    with open_locked(current, "a+b") as new_fh:
                        new_fh.seek(0, os.SEEK_END)
                        new_fh.seek(max(0, new_fh.tell() - 4096))
                        tail = new_fh.read().decode("utf-8", "ignore").strip().splitlines()
                        last_h = json.loads(tail[-1])["h"] if tail else GENESIS
                        extra, _, m, kk = _reseal_lines(current, late, last_h, redact)
                        new_fh.write(("\n".join(extra) + "\n").encode("utf-8"))
                        n, k = n + m, k + kk
                return total + n, touched + k
            fh.seek(0)
            data = fh.read()
    finally:
        fh.close()


# --------------------------------------------------------------------------------------------- buscar
def search(files: list[Path], pattern: str, tool: str | None, since: str | None, until: str | None,
           limit: int) -> int:
    rx = re.compile(pattern, re.I)
    shown = 0
    for cur in files:
        for seg in segments(cur):
            rel = str(seg).replace(str(Path.home()), "~", 1)
            with open(seg, encoding="utf-8") as fh:
                for i, raw in enumerate(fh, 1):
                    try:
                        rec = json.loads(raw)
                    except json.JSONDecodeError:
                        continue
                    ts = str(rec.get("ts", ""))
                    if (tool and rec.get("tool") != tool) or (since and ts < since) or \
                            (until and ts[:len(until)] > until):
                        continue
                    vals = {k: v for k, v in rec.items() if k not in FIXED_FIELDS}
                    text = " ".join(str(v) for v in vals.values())
                    if rx.search(text):
                        print(f"{ts}  {rec.get('tool', ''):<10} {text}   ({rel}:{i})")
                        shown += 1
                        if shown >= limit:
                            print(f"… tope de {limit} resultados (--limite)")
                            return 0
    if not shown:
        print("sin resultados")
    return 0


# ----------------------------------------------------------------------------------------------- main
def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="El audit log del harness: ruta, verificar, buscar, re-sellar.")
    sub = ap.add_subparsers(dest="cmd", required=True)
    for name in ("ruta", "verificar", "buscar", "resellar"):
        p = sub.add_parser(name)
        p.add_argument("--proyecto", default=".", help="carpeta del proyecto (por defecto, la actual)")
        if name == "verificar":
            p.add_argument("--estricto", dest="strict", action="store_true",
                           help="exit 1 si la cadena no empieza en el génesis (faltan segmentos rotados)")
        if name != "ruta":
            p.add_argument("--todos", action="store_true", help=f"todos los logs de {audit_dir()}")
        if name in ("verificar", "resellar"):
            p.add_argument("ficheros", nargs="*", help="logs concretos (por defecto, el del proyecto)")
        if name == "buscar":
            p.add_argument("patron", help="expresión regular (sin distinguir mayúsculas)")
            p.add_argument("--tool")
            p.add_argument("--desde", help="ts >= AAAA-MM-DD")
            p.add_argument("--hasta", help="ts <= AAAA-MM-DD")
            p.add_argument("--limite", type=int, default=200)
        if name == "resellar":
            p.add_argument("--motivo", dest="reason", default="SE-4 (2.27): valores viejos redactados con redactar.py")
    a = ap.parse_args(argv)

    if a.cmd == "ruta":
        print(audit_file(a.proyecto))
        return 0
    files = [Path(f) for f in getattr(a, "ficheros", [])] or (all_logs() if a.todos else [audit_file(a.proyecto)])

    if a.cmd == "verificar":
        rc = 0
        for f in files:
            if not f.exists() and not segments(f):
                print(f"audit-log: no hay log en {f}")
                rc = max(rc, 2 if getattr(a, "ficheros", []) else 0)
                continue
            try:
                ok, msg = verify_chain(f, a.strict)
            except (OSError, UnicodeDecodeError) as e:
                print(f"NO SE PUDO MEDIR {f}: {e}")
                rc = 2
                continue
            print(msg)
            rc = max(rc, 0 if ok else 1)
        return rc

    if a.cmd == "buscar":
        return search(files, a.patron, a.tool, a.desde, a.hasta, a.limite)

    # resellar
    for f in files:
        if not f.is_file():
            print(f"no existe {f}", file=sys.stderr)
            return 2
    for f in files:
        n, k = reseal(f, a.reason)
        print(f"resellado {f}: {n} líneas, {k} con algún valor redactado")
    return 0


if __name__ == "__main__":
    sys.exit(main())
