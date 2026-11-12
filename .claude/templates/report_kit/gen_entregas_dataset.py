#!/usr/bin/env python3
"""entregas-dataset.json — qué se ha entregado: ramas, commits y (si hay `gh`) PRs.

POR QUE EXISTE. El informe contaba QUE hay que hacer y QUE se decidio, y no contaba
nada de lo entregado. Verificado antes de escribirlo: en todo el report-kit no habia
ni una pestaña, ni un campo de item, ni una clave de schema sobre PRs, commits, ramas
o diffs. Es lo que un programador le enseña a su supervisor y era justo el hueco.

FUNCIONA SIN `gh`, a proposito. Con git a secas salen ramas, commits, ficheros
tocados y la edad de cada rama -- que es la mitad util. Con `gh` instalado se añaden
estado de revision, checks y comentarios. Instalarlo es dependencia de sistema y se
decide POR PROYECTO (governance.md §2), asi que la pagina dice cual de los dos modos
esta viendo en vez de fingir.

QUE NO HACE: no enseña el diff. Para eso esta el enlace al PR o al commit. La regla
del encargo era "un esquema explicado, y si quieres el codigo te vas al PR".

USO:
    python3 gen_entregas_dataset.py <plan-dir> [--repo <ruta>] [--base develop] [--limite 40]
"""
import argparse, json, os, re, shutil, subprocess, sys, datetime
from pathlib import Path


def git(repo, *args, default=""):
    try:
        r = subprocess.run(["git", "-C", str(repo), *args], capture_output=True,
                           text=True, timeout=60)
        return r.stdout.strip() if r.returncode == 0 else default
    except Exception:
        return default


def url_de_remoto(remoto: str) -> str:
    """git@github.com:org/repo.git y https://github.com/org/repo.git -> https://github.com/org/repo"""
    if not remoto:
        return ""
    m = re.match(r"git@([^:]+):(.+?)(?:\.git)?$", remoto)
    if m:
        return f"https://{m.group(1)}/{m.group(2)}"
    return re.sub(r"\.git$", "", remoto) if remoto.startswith("http") else ""


def prs_con_gh(repo) -> tuple:
    """PRs abiertos si `gh` esta instalado Y autenticado. Las dos cosas se comprueban:
    `gh` presente pero sin auth devuelve error y quedaria una lista vacia que parece
    'no hay PRs' cuando en realidad es 'no he podido mirar'."""
    if not shutil.which("gh"):
        return [], "gh no está instalado"
    try:
        r = subprocess.run(["gh", "pr", "list", "--limit", "30", "--json",
                            "number,title,headRefName,state,isDraft,author,url,"
                            "createdAt,additions,deletions,reviewDecision,statusCheckRollup"],
                           cwd=str(repo), capture_output=True, text=True, timeout=90)
        if r.returncode:
            return [], f"gh falló: {(r.stderr or '').strip()[:120]}"
        return json.loads(r.stdout or "[]"), ""
    except Exception as e:
        return [], f"gh: {e}"


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("plan")
    ap.add_argument("--repo", default=None)
    ap.add_argument("--base", default=None)
    ap.add_argument("--limite", type=int, default=40)
    a = ap.parse_args()

    plan = Path(a.plan).resolve()
    repo = Path(a.repo).resolve() if a.repo else Path(
        git(plan, "rev-parse", "--show-toplevel", default=str(plan)))
    if not (repo / ".git").exists():
        print(f"aviso: {repo} no es un repo git", file=sys.stderr)
        return 1

    actual = git(repo, "rev-parse", "--abbrev-ref", "HEAD")
    base = a.base or next((b for b in ("develop", "main", "master")
                           if git(repo, "rev-parse", "--verify", b)), actual)
    remoto = url_de_remoto(git(repo, "remote", "get-url", "origin"))

    # ramas locales, su edad y su distancia con la base
    ramas = []
    for b in git(repo, "for-each-ref", "--format=%(refname:short)", "refs/heads/").splitlines():
        if not b:
            continue
        mb = git(repo, "merge-base", b, base)
        delante = git(repo, "rev-list", "--count", f"{base}..{b}", default="0")
        detras = git(repo, "rev-list", "--count", f"{b}..{base}", default="0")
        ramas.append({
            "nombre": b, "es_base": b == base, "actual": b == actual,
            "ultimo": git(repo, "log", "-1", "--format=%cI", b),
            "ultimo_rel": git(repo, "log", "-1", "--format=%cr", b),
            "autor": git(repo, "log", "-1", "--format=%an", b),
            "delante": int(delante or 0), "detras": int(detras or 0),
            "desde_rel": git(repo, "log", "-1", "--format=%cr", mb) if mb else "",
        })
    ramas.sort(key=lambda r: (not r["actual"], r["es_base"], r["ultimo"]), reverse=True)

    # commits recientes de la rama actual
    sep = "\x1f"
    fmt = sep.join(["%H", "%h", "%cI", "%cr", "%an", "%s"])
    commits = []
    for ln in git(repo, "log", f"-{a.limite}", f"--format={fmt}", actual).splitlines():
        p = ln.split(sep)
        if len(p) < 6:
            continue
        stat = git(repo, "show", "--stat", "--format=", p[0])
        tocados = [l.split("|")[0].strip() for l in stat.splitlines() if "|" in l]
        m = re.match(r"^(\w+)(?:\(([^)]+)\))?[!]?:\s*(.+)", p[5])
        commits.append({
            "sha": p[0], "corto": p[1], "fecha": p[2], "rel": p[3], "autor": p[4],
            "asunto": p[5], "tipo": (m.group(1) if m else ""), "scope": (m.group(2) if m else ""),
            "titulo": (m.group(3) if m else p[5]),
            "ficheros": tocados[:8], "n_ficheros": len(tocados),
            "url": f"{remoto}/commit/{p[0]}" if remoto else "",
        })

    prs, gh_motivo = prs_con_gh(repo)
    sin_commitear = [l for l in git(repo, "status", "--short").splitlines() if l.strip()]

    data = {
        "meta": {
            "source": "gen_entregas_dataset.py — git" + (" + gh" if prs else ""),
            "date": datetime.date.today().isoformat(),
            "repo": repo.name, "rama_actual": actual, "base": base, "remoto": remoto,
            "modo": "git+gh" if prs else "git",
            "gh_motivo": gh_motivo,
            "n_ramas": len(ramas), "n_commits": len(commits), "n_prs": len(prs),
            "sin_commitear": len(sin_commitear),
        },
        "ramas": ramas, "commits": commits, "prs": prs,
    }
    out = plan / "entregas-dataset.json"
    out.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    m = data["meta"]
    print(f"OK {out}")
    print(f"   {m['n_ramas']} ramas · {m['n_commits']} commits · {m['n_prs']} PRs "
          f"· modo {m['modo']}" + (f" ({gh_motivo})" if gh_motivo else ""))
    return 0


if __name__ == "__main__":
    sys.exit(main())
