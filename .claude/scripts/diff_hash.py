#!/usr/bin/env python3
"""diff_hash.py — el hash del diff y la comprobación de una foto que vive FUERA de git.

QUÉ ES. La pieza común de las fotos de Pilar (`foto_django.py`, `foto_api.py`) y del gate que las
exige (`scripts/gate_impacto.py`, sub-ola 3.06). Define una sola vez:

  · `diff_sha256(repo, base_sha)`: el hash del cambio tal como lo define `auditores-diseno.md` §4.2.
    `git diff <base_sha>` compara el árbol de trabajo con la base, así que el hash no cambia si
    luego se commitea lo mismo; `.docs/` y `.claude/` quedan fuera para que regenerar el informe no
    invalide su propio hash. Los ficheros sin seguimiento entran por nombre y contenido.
  · `check_snapshot(...)`: si la foto que dice `impacto.json` es la que hay en disco.

POR QUÉ LA FOTO FUERA DE GIT CAMBIA LA COMPROBACIÓN (decisión del Usuario 18-10, EQ-D5). Las fotos
llevan ids y viven en `<plan>/impacto/fotos/`, ignorada por git. En otra máquina, o tras clonar,
la foto NO está: eso no es «la foto no coincide», es «aquí no se puede comprobar». Por eso hay tres
desenlaces y no dos, como en el resto de gates de la casa:

    0  la foto está y coincide (sha del fichero y diff_sha256 que grabó al medir)
    1  la foto está y NO coincide (otra foto, o el código cambió después de medir)
    2  la foto no está en esta máquina, o no se lee: no se pudo comprobar, y se dice

USO:
    python3 diff_hash.py diff <repo> <base_ref>          # imprime base_sha y diff_sha256
    python3 diff_hash.py check <foto.json> [--sha S] [--diff-sha D]
    python3 diff_hash.py --self-test

Solo stdlib.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import pathlib
import subprocess
import sys
import tempfile

#: Lo que el hash del diff deja fuera (§4.2): el plan y el harness.
EXCLUDED = (":(exclude).docs", ":(exclude).claude")


class MeasureError(RuntimeError):
    """No se pudo medir: sin git, base inalcanzable, repo inexistente."""


def _git(repo: pathlib.Path, *args: str) -> bytes:
    try:
        out = subprocess.run(["git", "-C", str(repo), *args], capture_output=True, check=False)
    except FileNotFoundError as exc:
        raise MeasureError("no hay git en el PATH") from exc
    if out.returncode != 0:
        raise MeasureError(f"git {' '.join(args[:2])} falló: {out.stderr.decode(errors='replace').strip()}")
    return out.stdout


def repo_root(path: pathlib.Path) -> pathlib.Path:
    """La raíz del repo que contiene `path`."""
    return pathlib.Path(_git(path, "rev-parse", "--show-toplevel").decode().strip())


def merge_base(repo: pathlib.Path, base_ref: str) -> str:
    """`git merge-base HEAD <base_ref>`: el punto de partida del cambio."""
    return _git(repo, "merge-base", "HEAD", base_ref).decode().strip()


def diff_sha256(repo: pathlib.Path, base_sha: str) -> str:
    """Hash del diff del árbol de trabajo contra `base_sha` (definición de §4.2)."""
    h = hashlib.sha256()
    h.update(_git(repo, "-c", "core.fileMode=false", "diff", "--binary", "--no-color",
                  "--no-ext-diff", base_sha, "--", ".", *EXCLUDED))
    untracked = _git(repo, "ls-files", "-z", "--others", "--exclude-standard", "--", ".", *EXCLUDED)
    for name in sorted(n for n in untracked.decode().split("\0") if n):
        h.update(f"{name}\0{file_sha256(repo / name)}\n".encode())
    return h.hexdigest()


def combined_sha256(per_repo: dict[str, str]) -> str:
    """El hash combinado de varios repos: `nombre:diff_sha256\\n` ordenado por nombre."""
    return hashlib.sha256("".join(f"{k}:{per_repo[k]}\n" for k in sorted(per_repo)).encode()).hexdigest()


def file_sha256(path: pathlib.Path) -> str:
    return hashlib.sha256(pathlib.Path(path).read_bytes()).hexdigest()


def is_git_ignored(path: pathlib.Path) -> bool:
    """¿Ignora git esta ruta? (aunque el fichero aún no exista)."""
    path = pathlib.Path(path).resolve()
    probe = path.parent
    while not probe.exists():
        probe = probe.parent
    out = subprocess.run(["git", "-C", str(probe), "check-ignore", "-q", str(path)],
                         capture_output=True, check=False)
    if out.returncode not in (0, 1):
        raise MeasureError(f"git check-ignore no pudo mirar {path}: {out.stderr.decode().strip()}")
    return out.returncode == 0


def check_snapshot(snapshot: pathlib.Path, expected_sha: str | None = None,
                   expected_diff_sha: str | None = None) -> dict:
    """Compara la foto en disco con lo que dice `impacto.json`.

    Devuelve `{"status": "match"|"mismatch"|"missing", "reasons": [...]}`. `missing` es el caso
    normal en una máquina que no midió: la foto está ignorada por git y no viaja.
    """
    snapshot = pathlib.Path(snapshot)
    if not snapshot.is_file():
        return {"status": "missing",
                "reasons": [f"{snapshot} no está en esta máquina (las fotos no van a git): "
                            "no se puede comprobar aquí; se comprueba donde se midió"]}
    reasons = []
    actual_sha = file_sha256(snapshot)
    if expected_sha and actual_sha != expected_sha:
        reasons.append(f"sha256 del fichero {actual_sha[:12]}… ≠ el de impacto.json {expected_sha[:12]}…")
    try:
        recorded = json.loads(snapshot.read_text(encoding="utf-8")).get("diff_sha256")
    except (OSError, ValueError) as exc:
        return {"status": "mismatch", "reasons": reasons + [f"{snapshot} está pero no se lee como JSON: {exc}"]}
    if expected_diff_sha and recorded != expected_diff_sha:
        reasons.append(f"la foto se midió con diff {str(recorded)[:12]}… y el diff esperado es "
                       f"{expected_diff_sha[:12]}…: el código cambió después de medir")
    if not (expected_sha or expected_diff_sha):
        reasons.append("sin --sha ni --diff-sha no hay con qué comparar")
    return {"status": "mismatch" if reasons else "match", "reasons": reasons,
            "sha256": actual_sha, "diff_sha256": recorded}


EXIT_BY_STATUS = {"match": 0, "mismatch": 1, "missing": 2}


def self_test() -> int:
    """Control: un diff vacío, uno con cambio, y las tres salidas de `check`."""
    fails = []
    with tempfile.TemporaryDirectory() as tmp:
        repo = pathlib.Path(tmp)
        run = lambda *a: subprocess.run(["git", "-C", tmp, *a], capture_output=True, check=True)  # noqa: E731
        run("init", "-q")
        run("config", "user.email", "t@t")
        run("config", "user.name", "t")
        (repo / ".gitignore").write_text("fotos/\n")
        (repo / "a.py").write_text("x = 1\n")
        run("add", ".")
        run("commit", "-qm", "base")
        base = merge_base(repo, "HEAD")
        empty = diff_sha256(repo, base)
        (repo / ".docs").mkdir()
        (repo / ".docs" / "plan.md").write_text("no cuenta\n")
        if diff_sha256(repo, base) != empty:
            fails.append(".docs/ cambia el hash y no debe")
        (repo / "a.py").write_text("x = 2\n")
        changed = diff_sha256(repo, base)
        if changed == empty:
            fails.append("un cambio en a.py no cambia el hash")
        (repo / "b.py").write_text("nuevo\n")
        if diff_sha256(repo, base) == changed:
            fails.append("un fichero sin seguimiento no entra en el hash")
        foto = repo / "fotos" / "foto-post.json"
        if not is_git_ignored(foto):
            fails.append("check-ignore no ve fotos/ como ignorada")
        if is_git_ignored(repo / "impacto.json"):
            fails.append("check-ignore da por ignorado lo que no lo está")
        if check_snapshot(foto)["status"] != "missing":
            fails.append("foto ausente no da 'missing'")
        foto.parent.mkdir()
        foto.write_text(json.dumps({"diff_sha256": changed}))
        sha = file_sha256(foto)
        if check_snapshot(foto, sha, changed)["status"] != "match":
            fails.append("foto correcta no da 'match'")
        if check_snapshot(foto, "0" * 64, changed)["status"] != "mismatch":
            fails.append("sha de foto plantado no da 'mismatch'")
        if check_snapshot(foto, sha, empty)["status"] != "mismatch":
            fails.append("diff viejo plantado no da 'mismatch'")
        try:
            merge_base(repo, "no-existe")
            fails.append("una base inalcanzable no da MeasureError")
        except MeasureError:
            pass
    for f in fails:
        print(f"FALLO: {f}")
    print("self-test diff_hash:", "OK" if not fails else f"{len(fails)} fallos")
    return 1 if fails else 0


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    p.add_argument("--self-test", action="store_true")
    sub = p.add_subparsers(dest="cmd")
    d = sub.add_parser("diff", help="base_sha y diff_sha256 de un repo")
    d.add_argument("repo")
    d.add_argument("base_ref")
    c = sub.add_parser("check", help="¿la foto en disco es la que dice impacto.json?")
    c.add_argument("snapshot")
    c.add_argument("--sha", help="post.snapshot_sha256 de impacto.json")
    c.add_argument("--diff-sha", help="diff_sha256 de impacto.json")
    a = p.parse_args(argv)
    if a.self_test:
        return self_test()
    try:
        if a.cmd == "diff":
            repo = pathlib.Path(a.repo)
            base = merge_base(repo, a.base_ref)
            print(json.dumps({"base_sha": base, "diff_sha256": diff_sha256(repo, base)}))
            return 0
        if a.cmd == "check":
            res = check_snapshot(pathlib.Path(a.snapshot), a.sha, a.diff_sha)
            print(json.dumps(res, ensure_ascii=False, indent=1))
            return EXIT_BY_STATUS[res["status"]]
    except (MeasureError, OSError) as exc:
        print(f"NO SE PUDO MEDIR: {exc}", file=sys.stderr)
        return 2
    p.print_help()
    return 2


if __name__ == "__main__":
    sys.exit(main())
