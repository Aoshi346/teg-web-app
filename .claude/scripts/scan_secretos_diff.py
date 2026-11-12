#!/usr/bin/env python3
"""¿Entra un SECRETO en este commit? Mira el CONTENIDO de las líneas añadidas (SE-31, 2026-10-22).

`pre-commit-check.sh` miraba NOMBRES de fichero (`.env`, `*.pem`) y la cabecera de una clave
privada. Un `sk-ant-…` pegado dentro de `settings.py` entraba en git sin que nadie dijera nada, y
los agentes hacen `git add -A`. Esto es el gate G1 del plan de ciberseguridad: escanea lo que
AÑADE el commit (no el fichero entero: así no bloquea por lo que ya estaba) y nunca imprime el
valor, solo el tipo, la ruta, la línea y los 4 primeros caracteres (`--redact`).

Si `gitleaks` está en el PATH se usa ADEMÁS de este escáner (`gitleaks protect --staged --redact`),
que sabe de más formatos de los que aquí se listan. No es dependencia: sin él, esto sigue
funcionando. Qué formatos conoce este escáner: AWS, Anthropic, OpenAI, GitHub, Slack, Google, Stripe,
Telegram, JWT, claves privadas, credenciales dentro de una URL y asignaciones `clave = "valor largo
de entropía alta"` a nombres como api_key/secret/token/password.

Cómo se deja pasar un falso positivo, con su razón y a la vista: `# tl-secret-ok: <por qué>` en la
MISMA línea (o `//`, `<!--`). Los valores de aspecto de ejemplo (`xxxx`, `your_…`, `changeme`,
`<…>`, `${…}`) no cuentan.

Límites declarados: no lee ficheros binarios; no mira líneas de más de 4000 caracteres ni nada bajo
`_fixtures/` (adrede: ahí viven los secretos de mentira de los gates); una línea de contenido que
empieza por `++ ` se toma por cabecera de diff y no se escanea; una URL con credenciales hacia un host
llamado `db`, `postgres`, `redis`… se deja pasar (es el compose de desarrollo); no ve un secreto partido en dos líneas ni cifrado en
base64 (salvo JWT); un patrón nuevo de un proveedor que no esté aquí pasa. Es un filtro barato
antes del commit, no un auditor de historia: para el historial, `gitleaks detect`.

Uso:
    scan_secretos_diff.py                  # el diff staged (lo que llama el pre-commit)
    scan_secretos_diff.py --tree [RUTA]    # los ficheros de un árbol (medir falsos positivos)
    scan_secretos_diff.py --stdin          # un diff unificado por stdin (pruebas)
Salida: 0 limpio · 1 hay secreto · 2 NO SE PUDO MEDIR (no hay git / no se pudo leer el diff).
"""
from __future__ import annotations

import math
import os
import re
import shutil
import subprocess
import sys
from pathlib import Path

PATRONES = [
    ("clave AWS", re.compile(r"\b(AKIA|ASIA)[0-9A-Z]{16}\b")),
    ("clave de Anthropic", re.compile(r"\bsk-ant-[A-Za-z0-9_-]{20,}")),
    ("clave de OpenAI", re.compile(r"\bsk-(?:proj-)?[A-Za-z0-9_-]{32,}")),
    ("token de GitHub", re.compile(r"\b(?:gh[pousr]_[A-Za-z0-9]{36,}|github_pat_[A-Za-z0-9_]{50,})")),
    ("token de Slack", re.compile(r"\bxox[baprs]-[A-Za-z0-9-]{10,}")),
    ("clave de Google", re.compile(r"\bAIza[0-9A-Za-z_-]{35}\b")),
    ("clave de Stripe", re.compile(r"\b[sr]k_live_[0-9a-zA-Z]{20,}")),
    ("token de bot de Telegram", re.compile(r"\b\d{8,10}:[A-Za-z0-9_-]{35}\b")),
    ("JWT", re.compile(r"\beyJ[A-Za-z0-9_-]{10,}\.eyJ[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]{10,}")),
    ("clave privada", re.compile(r"-----BEGIN (?:[A-Z]+ )*PRIVATE KEY")),
    ("credenciales en una URL", re.compile(r"\b[a-z][a-z0-9+.-]*://[^/\s:@\"']{2,}:[^/\s:@\"']{6,}@[^\s\"']+")),
]
ASIGNACION = re.compile(
    r"""(?ix)\b([a-z0-9_.-]*(?:api[_-]?key|secret|token|passw(?:or)?d|passwd|auth[_-]?key|private[_-]?key)[a-z0-9_.-]*)
        ["']?\s*[:=]\s*["']([A-Za-z0-9/+_=.:@-]{20,})["']""")
ID_O_HASH = re.compile(r"^(?:[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}|[0-9a-f]{32}|[0-9a-f]{40}|[0-9a-f]{64})$", re.I)
NOMBRE_DE_ID = re.compile(r"(?i)(?:^|[_.-])(?:id|uuid|hash|sha\d*|digest|checksum|etag)(?:$|[_.-])")
EJEMPLO = re.compile(r"(?i)django-insecure|@(?:localhost|127\.0\.0\.1|host\.docker\.internal|db|postgres|"
                     r"redis|rabbitmq|mysql|mongo|minio)(?:[:/?]|$)|x{4,}|your[_-]|change[_-]?me|example|dummy|fake|placeholder|sample|"
                     r"<[^>]*>|\$\{|\{\{|%\(|\*{4,}|\.\.\.|redacted|test[_-]?(?:key|token|secret)|"
                     r"insert|todo|password123|^[a-z]+$|^[0-9]+$|^(.)\1+$")
MARCA_OK = re.compile(r"tl-secret-ok\s*:\s*\S+")
# Ficheros donde un hash largo es normal y no un secreto
SALTAR_RUTA = re.compile(r"(?:^|/)_fixtures/|(?:^|/)(?:package-lock\.json|yarn\.lock|pnpm-lock\.yaml|poetry\.lock|"
                         r"Pipfile\.lock|go\.sum|Cargo\.lock|composer\.lock)$|\.(?:min\.js|map|svg|lock)$")


def entropia(s: str) -> float:
    if not s:
        return 0.0
    n = len(s)
    return -sum((s.count(c) / n) * math.log2(s.count(c) / n) for c in set(s))


def mira_linea(ruta: str, n: int, linea: str) -> list[dict]:
    if MARCA_OK.search(linea) or len(linea) > 4000:
        return []
    hallazgos = []
    for tipo, rx in PATRONES:
        for m in rx.finditer(linea):
            v = m.group(0)
            if tipo != "clave privada" and EJEMPLO.search(v):
                continue
            hallazgos.append({"ruta": ruta, "linea": n, "tipo": tipo, "empieza": v[:4]})
    for m in ASIGNACION.finditer(linea):
        v = m.group(2)
        if EJEMPLO.search(v) or v.startswith(("/", "./", "~")) or entropia(v) < 3.5:
            continue
        # un UUID o un sha asignado a `token_id`/`secret_hash` identifica, no autentica
        if ID_O_HASH.match(v) and NOMBRE_DE_ID.search(m.group(1)):
            continue
        # el patrón específico ya lo contó: no duplicar
        if any(h["linea"] == n and h["ruta"] == ruta for h in hallazgos):
            continue
        hallazgos.append({"ruta": ruta, "linea": n, "tipo": f"valor largo asignado a «{m.group(1)}»",
                          "empieza": v[:4]})
    return hallazgos


def lineas_anadidas(diff: str):
    """(ruta, nº de línea, texto) de cada línea AÑADIDA de un diff unificado."""
    ruta, n = "", 0
    for linea in diff.splitlines():
        if linea.startswith("+++ "):
            ruta = linea[4:].removeprefix("b/").strip()
            if ruta == "/dev/null":
                ruta = ""
        elif linea.startswith("@@"):
            m = re.search(r"\+(\d+)", linea)
            n = int(m.group(1)) if m else 0
        elif linea.startswith("+") and not linea.startswith("+++"):
            if ruta and not SALTAR_RUTA.search(ruta):
                yield ruta, n, linea[1:]
            n += 1
        elif not linea.startswith("-"):
            n += 1


def diff_staged() -> str | None:
    try:
        r = subprocess.run(["git", "-c", "core.quotePath=false", "diff", "--cached", "-U0",
                            "--no-color", "--diff-filter=ACMR", "--no-ext-diff"],
                           capture_output=True, text=True, timeout=60, errors="replace")
    except (OSError, subprocess.TimeoutExpired) as e:
        print(f"NO SE PUDO MEDIR: no se pudo pedir el diff a git ({e}).", file=sys.stderr)
        return None
    if r.returncode != 0:
        print(f"NO SE PUDO MEDIR: `git diff --cached` falló.\n{r.stderr.strip()}", file=sys.stderr)
        return None
    return r.stdout


def recorre_arbol(raiz: Path):
    for dp, dn, fn in os.walk(raiz):
        dn[:] = [d for d in dn if d not in {".git", "node_modules", ".venv", "venv", "__pycache__"}]
        for f in fn:
            p = Path(dp) / f
            rel = p.relative_to(raiz).as_posix()
            if SALTAR_RUTA.search(rel):
                continue
            try:
                if p.stat().st_size > 1_000_000:
                    continue
                t = p.read_text(encoding="utf-8")
            except (OSError, UnicodeDecodeError):
                continue
            for i, linea in enumerate(t.splitlines(), 1):
                yield rel, i, linea


def informa(hallazgos: list[dict]) -> None:
    print("BLOQUEADO: parece que el commit mete un SECRETO en el contenido de un fichero:")
    for h in hallazgos[:15]:
        print(f"  {h['ruta']}:{h['linea']}  {h['tipo']}  ({h['empieza']}…, valor redactado)")
    if len(hallazgos) > 15:
        print(f"  … y {len(hallazgos) - 15} más")
    print("Un secreto que entra en git se queda en el historial PARA SIEMPRE: sacarlo después no lo "
          "borra\ny, si ya se publicó, hay que ROTARLO. Pásalo a una variable de entorno / fichero "
          "fuera del repo.\nSi es un falso positivo, déjalo pasar con su razón en la misma línea: "
          "`# tl-secret-ok: <por qué>`.")


def main() -> int:
    a = sys.argv[1:]
    hallazgos: list[dict] = []
    if "--tree" in a:
        resto = [x for x in a if not x.startswith("--")]
        for ruta, n, linea in recorre_arbol(Path(resto[0] if resto else ".").resolve()):
            hallazgos += mira_linea(ruta, n, linea)
    else:
        diff = sys.stdin.read() if "--stdin" in a else diff_staged()
        if diff is None:
            return 2
        for ruta, n, linea in lineas_anadidas(diff):
            hallazgos += mira_linea(ruta, n, linea)
        if "--stdin" not in a and shutil.which("gitleaks"):
            r = subprocess.run(["gitleaks", "protect", "--staged", "--redact", "--no-banner"],
                               capture_output=True, text=True)
            if r.returncode == 1:
                hallazgos.append({"ruta": "(gitleaks)", "linea": 0, "tipo": "ver su salida",
                                  "empieza": "—"})
                print(r.stdout or r.stderr)
    if hallazgos:
        informa(hallazgos)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
