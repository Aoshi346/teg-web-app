#!/usr/bin/env python3
"""¿El .gitignore se está comiendo código o fixtures?

    python3 .claude/scripts/check_gitignore.py              # el repo donde estás
    python3 .claude/scripts/check_gitignore.py <repo>       # otro repo
    python3 .claude/scripts/check_gitignore.py --strict   # también falla por lo de (2)
    python3 .claude/scripts/check_gitignore.py --json

Sale con 0 si no hay nada, 1 si git ignora código o fixtures, 2 si no puede medir (no es un repo
git, o git falla): un instrumento que no llega al sujeto no dice «limpio».

POR QUÉ EXISTE (MO-56, sub-ola 2.14). git no avisa de lo que ignora: `git add` de la carpeta padre
no dice nada y el commit sale en verde sin el fichero. Tres casos en derivados:
  · cold_calling_coach: `media/` sin anclar (para la voz de la raíz) se comió `backend/core/media/`,
    código nuevo. De allí sale este script (su `check_gitignore_no_come_codigo.py`), generalizado:
    aquel tenía la lista de carpetas de código escrita a mano para ese repo.
  · accounting_AMC: `*.n43` sin la excepción para los fixtures de tests, y `*.xlsx`, que dejó fuera
    una plantilla.

QUÉ MIRA
  (1) Ficheros en disco que git ignora y que son CÓDIGO (por extensión) o están en una carpeta de
      FIXTURES o PLANTILLAS (cualquier extensión: un `.n43` o un `.xlsx` de prueba también). Eso es
      un fallo. Se salta lo que es basura en cualquier sitio (`node_modules/`, `.venv/`,
      `__pycache__/`, `dist/`, `staticfiles/`, `vendor/`…) y `.docs/`, que no es producto.
  (2) Ficheros que git YA versiona y que casan con una regla de ignorar: hoy están dentro porque
      alguien hizo `git add -f`, pero el hermano que se cree mañana no entrará. Es un aviso; con
      `--strict`, un fallo.
Por cada uno dice qué regla, de qué fichero y en qué línea, y si la regla está sin anclar.

LO QUE SE IGNORA A PROPÓSITO va en `.claude/gitignore-allow.txt`, un patrón glob por línea sobre
la ruta relativa (`resources/vendor/**`, `.docs/resources/**`). Así la excepción queda escrita y
revisable, en vez de ser un parámetro que cada uno pasa de memoria.

LÍMITE: solo ve lo que existe en disco. Si nadie ha creado todavía la carpeta que una regla se
comería, no avisa; avisa el día que alguien la cree, que es cuando importa.
"""
from __future__ import annotations

import fnmatch
import json
import os
import subprocess
import sys
from pathlib import Path

CODE_EXT = {".py", ".pyi", ".ts", ".tsx", ".js", ".jsx", ".mjs", ".cjs", ".vue", ".svelte",
            ".sql", ".sh", ".bash", ".css", ".scss", ".html", ".php", ".go", ".rs", ".java",
            ".kt", ".rb", ".yaml", ".yml", ".toml"}
# Carpetas cuyo contenido es parte del repo aunque la extensión sea de datos (.n43, .xlsx, .json).
FIXTURE_DIRS = {"fixtures", "fixture", "__fixtures__", "testdata", "test_data", "test-data",
                "templates", "plantillas", "seeds", "migrations", "golden"}
# Basura en cualquier profundidad: aquí ignorar es lo correcto y no se mira dentro.
JUNK_DIRS = {"node_modules", ".venv", "venv", "env", "__pycache__", ".pytest_cache",
             ".mypy_cache", ".ruff_cache", ".tox", ".nox", "dist", "build", ".next", ".nuxt",
             ".turbo", ".cache", "coverage", "htmlcov", ".git", ".idea", ".vscode",
             "site-packages", ".parcel-cache", ".svelte-kit", "test-results",
             "playwright-report", ".playwright-mcp", "worktrees",
             # salidas y copias que se ignoran a propósito (medido en AMC y elvion el 27-10:
             # `collectstatic`, volcados de base de datos y librerías de terceros copiadas)
             "staticfiles", ".backups", "backups", "vendor"}
# La documentación y los planes no son producto (la misma exclusión que preguntar_configuracion.py):
# allí se ignoran a propósito los clones de referencia y las páginas con datos de clientes.
SKIP_PREFIXES = (".docs/",)
ALLOW_FILE = ".claude/gitignore-allow.txt"
MAX_LIST = 40


def git(repo: Path, *args: str, stdin: str | None = None) -> subprocess.CompletedProcess:
    # quotePath=off: sin él, una ruta no ASCII (`diseño/`) sale entrecomillada y con escapes, no
    # acaba en `/` ni casa con su regla, y lo ignorado se daba por limpio (verificador de la 2.14)
    return subprocess.run(["git", "-c", "core.quotePath=off", "-C", str(repo), *args], input=stdin,
                          capture_output=True, text=True, timeout=120)


def load_allow(repo: Path) -> list[str]:
    f = repo / ALLOW_FILE
    if not f.is_file():
        return []
    lines = f.read_text(encoding="utf-8", errors="replace").splitlines()
    return [ln.strip() for ln in lines if ln.strip() and not ln.lstrip().startswith("#")]


def allowed(rel: str, allow: list[str]) -> bool:
    return any(fnmatch.fnmatch(rel, pat) or fnmatch.fnmatch(rel + "/", pat) for pat in allow)


def is_junk(rel: str) -> bool:
    if rel.startswith(SKIP_PREFIXES):
        return True
    parts = rel.rstrip("/").split("/")
    return any(p in JUNK_DIRS or p.endswith(".egg-info") for p in parts)


def is_suspicious(rel: str) -> bool:
    """Código por extensión, o cualquier fichero dentro de una carpeta de fixtures o plantillas."""
    parts = rel.split("/")
    if Path(rel).suffix.lower() in CODE_EXT:
        return True
    return any(p.lower() in FIXTURE_DIRS for p in parts[:-1])


def expand_ignored(repo: Path, entries: list[str], allow: list[str]) -> list[str]:
    """`--directory` devuelve carpetas enteras; se baja a ellas salvo si son basura o permitidas."""
    files = []
    for e in entries:
        if is_junk(e) or allowed(e.rstrip("/"), allow):
            continue
        if not e.endswith("/"):
            files.append(e)
            continue
        for root, dirs, names in os.walk(repo / e):
            dirs[:] = [d for d in dirs if d not in JUNK_DIRS and not d.endswith(".egg-info")]
            for n in names:
                rel = (Path(root) / n).relative_to(repo).as_posix()
                if not allowed(rel, allow):
                    files.append(rel)
    return files


def why(repo: Path, paths: list[str]) -> dict[str, dict]:
    """`git check-ignore -v` en lote: regla, fichero y línea de cada ruta."""
    if not paths:
        return {}
    r = git(repo, "check-ignore", "-v", "--no-index", "--stdin", stdin="\n".join(paths))
    out = {}
    for ln in r.stdout.splitlines():
        if "\t" not in ln:
            continue
        src, path = ln.split("\t", 1)
        # formato: <fichero>:<línea>:<patrón>
        bits = src.split(":", 2)
        if len(bits) == 3:
            pat = bits[2]
            out[path] = {"file": bits[0], "line": bits[1], "pattern": pat,
                         "unanchored": not pat.startswith("!") and "/" not in pat.rstrip("/")}
    return out


def main() -> int:
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    strict = "--strict" in sys.argv
    as_json = "--json" in sys.argv
    start = Path(args[0]).resolve() if args else Path.cwd()
    try:
        top = git(start, "rev-parse", "--show-toplevel")
    except (OSError, subprocess.SubprocessError) as e:
        print(f"✗ no puedo medir: git no responde ({e})", file=sys.stderr)
        return 2
    if top.returncode != 0:
        print(f"✗ no puedo medir: {start} no es un repo git", file=sys.stderr)
        return 2
    repo = Path(top.stdout.strip())
    allow = load_allow(repo)

    r1 = git(repo, "ls-files", "--others", "--ignored", "--exclude-standard", "--directory")
    r2 = git(repo, "ls-files", "--cached", "--ignored", "--exclude-standard")
    if r1.returncode != 0 or r2.returncode != 0:
        print(f"✗ no puedo medir: git ls-files falló ({(r1.stderr or r2.stderr).strip()})",
              file=sys.stderr)
        return 2
    # sin duplicados: `--directory` puede listar a la vez una carpeta y un fichero de dentro
    ignored = sorted({p for p in expand_ignored(repo, r1.stdout.splitlines(), allow)
                      if is_suspicious(p)})
    tracked = [p for p in r2.stdout.splitlines()
               if p and not is_junk(p) and not allowed(p, allow)]
    rules = why(repo, ignored + tracked)

    if as_json:
        print(json.dumps({"repo": str(repo), "ignored": [{"path": p, **rules.get(p, {})}
                                                         for p in ignored],
                          "tracked_but_ignored": [{"path": p, **rules.get(p, {})}
                                                  for p in tracked]},
                         ensure_ascii=False, indent=2))
    else:
        def show(lst: list[str]) -> None:
            for p in sorted(lst)[:MAX_LIST]:
                w = rules.get(p)
                if w:
                    tip = "  ← sin anclar: casa a cualquier profundidad" if w["unanchored"] else ""
                    print(f"  · {p}\n      regla `{w['pattern']}` ({w['file']}:{w['line']}){tip}")
                else:
                    print(f"  · {p}")
            if len(lst) > MAX_LIST:
                print(f"  … y {len(lst) - MAX_LIST} más")

        if ignored:
            print(f"✗ {len(ignored)} fichero(s) de código o fixtures que git IGNORA "
                  "(el commit saldría en verde sin ellos):")
            show(ignored)
        if tracked:
            print(f"{'✗' if strict else '·'} {len(tracked)} fichero(s) versionados que casan con "
                  "una regla de ignorar (el próximo hermano no entrará):")
            show(tracked)
        if ignored or tracked:
            print("\n  Arreglo habitual: anclar la regla a su carpeta (`/media/` en vez de `media/`), "
                  "o añadir la\n  excepción (`!tests/fixtures/*.n43`). Lo ignorado a propósito, "
                  f"a {ALLOW_FILE}.")
        else:
            print("✓ git no ignora ningún fichero de código ni de fixtures")
    return 1 if ignored or (strict and tracked) else 0


if __name__ == "__main__":
    sys.exit(main())
