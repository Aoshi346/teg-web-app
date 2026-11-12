#!/usr/bin/env python3
"""incident_cases.py — cada incidente o revert del proyecto, un caso que el auditor de código tiene que cazar.

POR QUÉ (EQ-40, sub-ola 3.11). Probar un auditor con ejemplos inventados mide otra cosa: los incidentes
son la verdad del proyecto. El equipo de Claude Code lo hace así («Any incidents are now an eval»): el
diff que causó un incidente o un revert se guarda como caso, y el revisor tiene que marcarlo. Encaja con
`rules/self-improvement-loop.md` (error repetido → sensor) y con `qa-loop.md` §4b (fixture con la clave
fuera del alcance del auditor). Política: `rules/audit-team.md` §7.

DÓNDE VIVE CADA COSA, y por qué:
  · el diff y el encargo, EN el repo: `.docs/evals/incidentes/<id>/{diff.patch,encargo.md}` (se versionan)
  · la CLAVE (qué fichero y línea tenía que marcar), FUERA: `~/.claude/evals/<proyecto>/incidentes/<id>.json`.
    Si el auditor puede leer la clave, la prueba no mide nada.
  · los resultados, fuera también: `~/.claude/evals/<proyecto>/resultados.jsonl` (telemetría, como el registro)

Uso:
    incident_cases.py add --sha <commit> --marca <fichero>[:<línea>] [--marca …] [--titulo "…"]
        # si <commit> es un revert («This reverts commit X»), el caso es el diff de X, el que rompió
    incident_cases.py list
    incident_cases.py encargo <id>                 # el prompt ciego para el auditor (sin la clave)
    incident_cases.py score <id> <informe> [--agente <nombre>]   # 0 cazado · 1 no cazado · 2 no medible
    incident_cases.py report                       # recall por agente sobre la batería

Raíz: `--root` o la carpeta actual (tiene que ser un repo git). La batería se pasa al auditor de forma
periódica con `/schedule` o un `claude -p` (capa 5 de `governance.md` §6, con aprobación: gasta tokens);
este script no lanza ningún modelo.

LÍMITE HONESTO. `score` mira si el informe NOMBRA el fichero (y la línea, ±5) de la clave: un informe que
lo cita sin entender el fallo cuenta como cazado. Para un juicio fino, se lee el informe; el número es el
filtro barato, como el recall del fixture de `qa-loop.md` §4b.
"""
import argparse
import datetime
import json
import os
import re
import subprocess
import sys

REL = os.path.join(".docs", "evals", "incidentes")


def git(root, *args):
    r = subprocess.run(["git", "-C", root, *args], capture_output=True, text=True)
    if r.returncode != 0:
        raise RuntimeError(r.stderr.strip() or f"git {' '.join(args)} falló")
    return r.stdout


def project_slug(root):
    try:
        common = git(root, "rev-parse", "--path-format=absolute", "--git-common-dir").strip()
        return os.path.basename(os.path.dirname(common)) if common.endswith(".git") else os.path.basename(root)
    except RuntimeError:
        return os.path.basename(root)


def key_dir(root):
    base = os.path.expanduser(os.environ.get("CLAUDE_EVALS_DIR", "~/.claude/evals"))
    return os.path.join(base, project_slug(root))


def cmd_add(a):
    root = a.root
    sha = git(root, "rev-parse", "--verify", a.sha + "^{commit}").strip()
    msg = git(root, "log", "-1", "--format=%B", sha)
    m = re.search(r"This reverts commit ([0-9a-f]{7,40})", msg)
    cause, kind = (git(root, "rev-parse", m.group(1)).strip(), "revert") if m else (sha, "incidente")
    patch = git(root, "show", "--format=", "--no-color", cause)
    if not patch.strip():
        print(f"el commit {cause[:10]} no tiene diff: no hay caso que guardar", file=sys.stderr)
        return 2
    marks = []
    for spec in a.marca:
        f, _, line = spec.partition(":")
        marks.append({"fichero": f, **({"linea": int(line)} if line.isdigit() else {})})
    cid = a.id or f"{datetime.date.today().isoformat()}-{cause[:8]}"
    d = os.path.join(root, REL, cid)
    os.makedirs(d, exist_ok=True)
    open(os.path.join(d, "diff.patch"), "w", encoding="utf-8").write(patch)
    open(os.path.join(d, "encargo.md"), "w", encoding="utf-8").write(prompt_text(cid))
    kd = os.path.join(key_dir(root), "incidentes")
    os.makedirs(kd, mode=0o700, exist_ok=True)
    key = {"id": cid, "tipo": kind, "sha_causa": cause, "sha_revert": sha if m else None,
           "titulo": a.titulo or msg.splitlines()[0][:120], "debe_marcar": marks,
           "creado": datetime.date.today().isoformat()}
    json.dump(key, open(os.path.join(kd, cid + ".json"), "w", encoding="utf-8"), ensure_ascii=False, indent=2)
    print(f"caso {cid} ({kind} de {cause[:10]}): diff en {os.path.relpath(d, root)}/, clave fuera del repo"
          f" ({len(marks)} marca(s))")
    if not marks:
        print("⚠️  sin --marca: el caso no se puede puntuar hasta que la clave diga qué tenía que cazar")
    return 0


def prompt_text(cid):
    return (f"# Encargo · caso {cid}\n\n"
            "Revisa este cambio como si llegara en un PR antes del merge: `diff.patch` (en esta carpeta).\n"
            "Abre los ficheros que toca en el repo si lo necesitas. Informa de los defectos que veas con\n"
            "`fichero:línea`, severidad y por qué; si no ves ninguno, dilo. No arregles nada.\n")


def cmd_list(a):
    d = os.path.join(a.root, REL)
    ids = sorted(x for x in os.listdir(d) if os.path.isdir(os.path.join(d, x))) if os.path.isdir(d) else []
    kd = os.path.join(key_dir(a.root), "incidentes")
    if not ids:
        print("(sin casos todavía: añade el primero al cerrar un incidente o un revert)")
    for i in ids:
        k = os.path.join(kd, i + ".json")
        print(f"{i:32} {'clave ✓' if os.path.isfile(k) else 'SIN CLAVE (no puntuable)'}")
    return 0


def cmd_encargo(a):
    p = os.path.join(a.root, REL, a.id, "encargo.md")
    if not os.path.isfile(p):
        print(f"no existe el caso {a.id}", file=sys.stderr)
        return 2
    print(open(p, encoding="utf-8").read() + f"\nRuta del diff: {os.path.join(REL, a.id, 'diff.patch')}")
    return 0


def cmd_score(a):
    kp = os.path.join(key_dir(a.root), "incidentes", a.id + ".json")
    try:
        key = json.load(open(kp, encoding="utf-8"))
        text = open(a.informe, encoding="utf-8", errors="replace").read()
    except (OSError, ValueError) as exc:
        print(f"NO MEDIBLE: {exc}", file=sys.stderr)
        return 2
    if not key.get("debe_marcar"):
        print(f"NO MEDIBLE: la clave de {a.id} no dice qué tenía que cazar (--marca)", file=sys.stderr)
        return 2
    hits = []
    for mk in key["debe_marcar"]:
        f = mk["fichero"]
        names = {f, os.path.basename(f)}
        found = any(n in text for n in names)
        if found and "linea" in mk:
            lines = [int(x) for n in names for x in re.findall(re.escape(n) + r"[:#L ]+(\d+)", text)]
            found = any(abs(x - mk["linea"]) <= 5 for x in lines)
        hits.append(found)
    caught = all(hits)
    rp = os.path.join(key_dir(a.root), "resultados.jsonl")
    with open(rp, "a", encoding="utf-8") as fh:
        fh.write(json.dumps({"fecha": datetime.date.today().isoformat(), "caso": a.id, "agente": a.agente,
                             "cazado": caught, "marcas": len(hits), "acertadas": sum(hits)},
                            ensure_ascii=False) + "\n")
    print(f"{'✓ cazado' if caught else '✗ NO cazado'}: {sum(hits)}/{len(hits)} marca(s) de {a.id}"
          f" ({a.agente or 'agente sin nombre'})")
    return 0 if caught else 1


def cmd_report(a):
    rp = os.path.join(key_dir(a.root), "resultados.jsonl")
    if not os.path.isfile(rp):
        print("(sin resultados: corre `score` tras pasar la batería)")
        return 0
    per = {}
    for line in open(rp, encoding="utf-8"):
        if line.strip():
            r = json.loads(line)
            per.setdefault(r.get("agente") or "?", []).append(r["cazado"])
    for ag, xs in sorted(per.items()):
        print(f"{ag:32} {sum(xs)}/{len(xs)} cazados ({100 * sum(xs) / len(xs):.0f} %)")
    return 0


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--root", default=os.getcwd())
    sub = ap.add_subparsers(dest="cmd", required=True)
    p = sub.add_parser("add")
    p.add_argument("--sha", required=True)
    p.add_argument("--marca", action="append", default=[])
    p.add_argument("--titulo")
    p.add_argument("--id")
    sub.add_parser("list")
    p = sub.add_parser("encargo")
    p.add_argument("id")
    p = sub.add_parser("score")
    p.add_argument("id")
    p.add_argument("informe")
    p.add_argument("--agente", default="")
    sub.add_parser("report")
    a = ap.parse_args()
    a.root = os.path.realpath(a.root)
    try:
        return {"add": cmd_add, "list": cmd_list, "encargo": cmd_encargo,
                "score": cmd_score, "report": cmd_report}[a.cmd](a)
    except RuntimeError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(main())
