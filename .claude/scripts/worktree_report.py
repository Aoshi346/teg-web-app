#!/usr/bin/env python3
"""worktree_report.py — ¿cuántos worktrees de subagente se han quedado olvidados, y cuánto ocupan?

De dónde sale (AN-4, sub-ola 3.18 de la revisión integral). Los subagentes con `isolation: worktree`
dejan su copia en `.claude/worktrees/` y nadie la limpia. Medido el 17-10: fitapp con 26 worktrees y
7,9 GB; accounting_AMC con 28 (20 `agent-*`) y 2,5 GB; elvion con tres copias viejas. Borrar solo no
se puede (`governance.md` §2: puede haber trabajo sin sincronizar), así que esto AVISA con los datos
delante —cuántos, cuánto pesan y cuáles ya están mergeados— y la limpieza la decide una persona.

Lo llama `hooks/otto-briefing.sh` al arrancar la sesión: calla por debajo de los umbrales y, por
encima, imprime unas líneas. También a mano, y al cerrar una wave (`rules/parallelization.md` §3).

    python3 .claude/scripts/worktree_report.py               # aviso solo si pasa un umbral
    python3 .claude/scripts/worktree_report.py --all         # la lista entera, pase o no
    python3 .claude/scripts/worktree_report.py --max-count 10 --max-gb 2 --base develop
    python3 .claude/scripts/worktree_report.py --self-test   # 10 worktrees de prueba → avisa

Umbrales (o variables `TL_WORKTREE_MAX_COUNT` / `TL_WORKTREE_MAX_GB`): 10 worktrees bajo
`.claude/worktrees/` o 2 GB entre todos. «Mergeado» = el HEAD del worktree ya está en la rama base
(`--base`; por defecto `develop` si existe, si no `main`) y no tiene cambios sin commitear. Un worktree
con cambios sin commitear NUNCA sale como mergeado, aunque su HEAD lo esté.

Límites honestos: `git status`, `merge-base` y `du` corren en paralelo con un tope GLOBAL
(`--budget`, 4 s; el hook le da 1,2): lo que no da tiempo a medir sale «sin medir» o «sin mirar», no
como 0 ni como mergeado. La cuenta de worktrees sale siempre (medido el 31-10: con 14 worktrees, la
versión en serie tardaba 2-3 s y el `timeout 2` del hook la mataba sin decir nada). Solo mira los worktrees bajo
`.claude/worktrees/` (los de los subagentes y `claude -w`), no los que se crean en otra ruta.
Salida: 0 siempre que pueda mirar (avise o no) · 2 si no es un repo git. Un aviso no es un fallo.
"""
from __future__ import annotations

import argparse
import os
import subprocess
import sys
import tempfile
import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

DEFAULT_MAX_COUNT = 10
DEFAULT_MAX_GB = 2.0


def git(cwd: Path, *args: str, timeout: float = 5) -> subprocess.CompletedProcess:
    """Un git con tope; si se pasa, devuelve rc 124 (como `timeout`) en vez de tumbar el script."""
    try:
        return subprocess.run(["git", "-C", str(cwd), *args], capture_output=True, text=True,
                              timeout=max(timeout, 0.05))
    except subprocess.TimeoutExpired:
        return subprocess.CompletedProcess(args, 124, "", "timeout")


def main_root(cwd: Path) -> Path | None:
    """La raíz del repo PRINCIPAL, aunque se lance desde dentro de un worktree."""
    r = git(cwd, "rev-parse", "--path-format=absolute", "--git-common-dir")
    if r.returncode != 0:
        return None
    common = Path(r.stdout.strip())
    return common.parent if common.name == ".git" else common


def list_worktrees(root: Path) -> list[dict]:
    r = git(root, "worktree", "list", "--porcelain")
    out, cur = [], {}
    for line in r.stdout.splitlines() + [""]:
        if not line:
            if cur:
                out.append(cur)
            cur = {}
            continue
        key, _, val = line.partition(" ")
        cur[key] = val or True
    base_dir = (root / ".claude" / "worktrees").resolve()
    return [w for w in out if Path(w["worktree"]).resolve().parent == base_dir]


def pick_base(root: Path, wanted: str | None) -> str | None:
    for b in ([wanted] if wanted else ["develop", "main", "master"]):
        if git(root, "rev-parse", "--verify", "--quiet", b).returncode == 0:
            return b
    return None


def du_kb(path: Path, deadline: float) -> int | None:
    left = deadline - time.monotonic()
    if left <= 0.05:
        return None
    try:
        r = subprocess.run(["du", "-sk", str(path)], capture_output=True, text=True, timeout=left)
        return int(r.stdout.split()[0]) if r.stdout else None
    except (subprocess.TimeoutExpired, ValueError, IndexError):
        return None


def _probe(root: Path, w: dict, base: str | None, deadline: float) -> dict:
    path = Path(w["worktree"])
    head = w.get("HEAD", "")
    dirty = None                 # None = sin mirar (no dio tiempo o falló): nunca cuenta como mergeado
    if path.is_dir():
        st = git(path, "status", "--porcelain", timeout=deadline - time.monotonic())
        dirty = bool(st.stdout.strip()) if st.returncode == 0 else None
    merged = False
    if base and head and dirty is False:
        merged = git(root, "merge-base", "--is-ancestor", head, base,
                     timeout=deadline - time.monotonic()).returncode == 0
    return {"name": path.name, "path": str(path), "branch": str(w.get("branch", "")).replace("refs/heads/", ""),
            "agent": path.name.startswith("agent-"), "dirty": dirty, "merged": merged,
            "kb": du_kb(path, deadline) if path.is_dir() else 0, "prunable": "prunable" in w}


def inspect(root: Path, base: str | None, budget: float) -> list[dict]:
    """Tope de tiempo GLOBAL (status, merge-base y du), en paralelo: lo que no da tiempo a mirar sale
    «sin mirar» o «sin medir», y la cuenta de worktrees, que es barata, sale siempre."""
    deadline = time.monotonic() + budget
    wts = list_worktrees(root)
    with ThreadPoolExecutor(max_workers=8) as ex:
        return list(ex.map(lambda w: _probe(root, w, base, deadline), wts))


def report(rows: list[dict], base: str | None, max_count: int, max_gb: float, show_all: bool) -> list[str]:
    total_kb = sum(r["kb"] or 0 for r in rows)
    unmeasured = sum(r["kb"] is None for r in rows)
    gb = total_kb / 1024 / 1024
    over = len(rows) >= max_count or gb >= max_gb
    if not rows or not (over or show_all):
        return []
    merged = [r for r in rows if r["merged"]]
    lines = [f"· ⚠ Worktrees en .claude/worktrees/: {len(rows)} ({sum(r['agent'] for r in rows)} de subagente) · "
             f"{gb:.1f} GB" + (f" (+{unmeasured} sin medir)" if unmeasured else "")
             + f" · umbral {max_count} o {max_gb:g} GB" if over else
             f"· Worktrees en .claude/worktrees/: {len(rows)} · {gb:.1f} GB"]
    if merged:
        lines.append(f"  {len(merged)} ya mergeados en {base} y sin cambios (candidatos a limpiar, CON OK del Usuario):")
        lines += [f"    {r['name']}  ({'sin medir' if r['kb'] is None else str(r['kb'] // 1024) + ' MB'})"
                  for r in merged[:12]]
        if len(merged) > 12:
            lines.append(f"    … y {len(merged) - 12} más (--all para la lista)")
    rest = [r for r in rows if not r["merged"]]
    if show_all and rest:
        lines.append("  sin mergear o con cambios (no se tocan sin mirarlos):")
        lines += [f"    {r['name']}  {'sin mirar (tope de tiempo)' if r['dirty'] is None else 'con cambios' if r['dirty'] else 'sin mergear'}"
                  for r in rest]
    if over:
        lines.append("  Limpiar es `git worktree remove <ruta>` uno a uno tras mirarlo; borrar requiere OK (governance.md §2).")
    return lines


def self_test() -> int:
    ok = True
    with tempfile.TemporaryDirectory() as d:
        root = Path(d) / "repo"
        root.mkdir()
        env = {**os.environ, "GIT_AUTHOR_NAME": "t", "GIT_AUTHOR_EMAIL": "t@t", "GIT_COMMITTER_NAME": "t",
               "GIT_COMMITTER_EMAIL": "t@t"}
        def g(*a, cwd=root):
            subprocess.run(["git", "-C", str(cwd), *a], check=True, capture_output=True, env=env)
        g("init", "-q", "-b", "develop")
        (root / "a.txt").write_text("a")
        g("add", "a.txt")
        g("commit", "-q", "-m", "a")
        for i in range(10):
            g("worktree", "add", "-q", "-b", f"wt{i}", str(root / ".claude" / "worktrees" / f"agent-{i}"))
        wt9 = root / ".claude" / "worktrees" / "agent-9"
        (wt9 / "b.txt").write_text("b")
        g("add", "b.txt", cwd=wt9)
        g("commit", "-q", "-m", "b", cwd=wt9)            # agent-9: un commit que develop no tiene
        (root / ".claude" / "worktrees" / "agent-8" / "sucio.txt").write_text("x")   # agent-8: cambios
        rows = inspect(root, pick_base(root, None), 4)
        lines = report(rows, "develop", DEFAULT_MAX_COUNT, DEFAULT_MAX_GB, False)
        text = "\n".join(lines)
        if not lines or "10 (10 de subagente)" not in text:
            print(f"✗ self-test: con 10 worktrees debía avisar\n{text}"); ok = False
        if "8 ya mergeados" not in text or "agent-9" in text or "agent-8" in text:
            print(f"✗ self-test: mergeados mal contados (agent-9 sin mergear, agent-8 con cambios)\n{text}"); ok = False
        if report(rows[:9], "develop", DEFAULT_MAX_COUNT, DEFAULT_MAX_GB, False):
            print("✗ self-test: con 9 worktrees y pocos MB no debía avisar"); ok = False
        if not report(rows[:3], "develop", DEFAULT_MAX_COUNT, 0.0000001, False):
            print("✗ self-test: por encima del umbral de GB debía avisar"); ok = False
    print("OK: self-test (control negativo incluido)" if ok else "self-test FALLA")
    return 0 if ok else 1


def main() -> int:
    ap = argparse.ArgumentParser(description="Aviso de worktrees olvidados en .claude/worktrees/")
    ap.add_argument("--root", default=os.environ.get("CLAUDE_PROJECT_DIR") or os.getcwd())
    ap.add_argument("--base", default=None, help="rama contra la que se mira si está mergeado")
    ap.add_argument("--max-count", type=int, default=int(os.environ.get("TL_WORKTREE_MAX_COUNT", DEFAULT_MAX_COUNT)))
    ap.add_argument("--max-gb", type=float, default=float(os.environ.get("TL_WORKTREE_MAX_GB", DEFAULT_MAX_GB)))
    ap.add_argument("--budget", "--du-timeout", dest="budget", type=float, default=4.0,
                    help="segundos en total para mirar los worktrees")
    ap.add_argument("--all", action="store_true", help="la lista entera, aunque no pase umbral")
    ap.add_argument("--self-test", action="store_true")
    a = ap.parse_args()
    if a.self_test:
        return self_test()
    root = main_root(Path(a.root))
    if root is None:
        print(f"✗ no se pudo medir: {a.root} no es un repo git", file=sys.stderr)
        return 2
    base = pick_base(root, a.base)
    for line in report(inspect(root, base, a.budget), base, a.max_count, a.max_gb, a.all):
        print(line)
    return 0


if __name__ == "__main__":
    sys.exit(main())
