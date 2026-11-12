#!/usr/bin/env python3
"""Inventario del repo: qué hay en cada carpeta, cuánto pesa y quién lo cita.

Uso:  python3 .claude/scripts/gen_inventario.py [--json] [--check] [--tasks]
      --json   salida cruda para otro programa
      --check  exit 1 si el inventario guardado no refleja el disco
      --tasks  emite los items en formato tasks.md del report-kit

POR QUÉ EXISTE: un inventario escrito a mano miente en dos semanas — es el fallo que esta
auditoría documentó tres veces (estado.html congelado, contadores del INDEX, skills/README).
Los números salen del disco y de git, no de la memoria de nadie.

La señal que decide casi todo es `refs`: cuántos ficheros de .claude/ citan esa ruta. Una
carpeta con 0 referencias no la abre nadie — ni un humano ni un agente.
"""
import json, os, subprocess, sys, datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
OUT  = ROOT / ".claude" / "inventario.json"
SKIP = {".git", "node_modules", ".venv", "__pycache__"}

def sh(*a):
    try:
        return subprocess.run(a, cwd=ROOT, capture_output=True, text=True, timeout=60).stdout.strip()
    except Exception:
        return ""

def walk(p: Path):
    n = b = 0
    for dirpath, dirnames, filenames in os.walk(p):
        dirnames[:] = [d for d in dirnames if d not in SKIP]
        for f in filenames:
            fp = Path(dirpath) / f
            try:
                b += fp.stat().st_size; n += 1
            except OSError:
                pass
    return n, b

def human(b):
    for u in ("B", "K", "M", "G"):
        if b < 1024: return f"{b:.0f}{u}"
        b /= 1024
    return f"{b:.0f}T"

def refs(name: str) -> int:
    """Ficheros de .claude/ que citan esta ruta. La señal que importa."""
    out = sh("grep", "-rl", "--include=*.md", "--include=*.py", "--include=*.sh",
             "--include=*.json", f"{name}/", ".claude")
    return len([x for x in out.splitlines() if x.strip()])

def entry(path: Path, kind: str):
    rel = path.relative_to(ROOT).as_posix()
    n, b = walk(path) if path.is_dir() else (1, path.stat().st_size)
    tracked = len([x for x in sh("git", "ls-files", rel).splitlines() if x.strip()])
    last = sh("git", "log", "-1", "--format=%as", "--", rel)
    r = refs(rel) if path.is_dir() else len(
        [x for x in sh("grep", "-rl", "--include=*.md", path.name, ".claude").splitlines() if x.strip()])
    # versionados > presentes = hay ficheros borrados que git aún arrastra
    fantasmas = max(0, tracked - n) if path.is_dir() else 0
    return {"path": rel, "kind": kind, "files": n, "bytes": b, "size": human(b),
            "refs": r, "tracked": tracked, "ghost_tracked": fantasmas,
            "last_commit": last or None,
            "age_days": (datetime.date.today() - datetime.date.fromisoformat(last)).days if last else None}

def build():
    items = []
    for p in sorted(ROOT.iterdir()):
        if p.name in SKIP: continue
        if p.is_dir():
            items.append(entry(p, "dir-oculto" if p.name.startswith(".") else "dir"))
        elif p.is_file():
            items.append(entry(p, "fichero"))
    total_f = sum(i["files"] for i in items)
    total_b = sum(i["bytes"] for i in items)
    return {"generated": datetime.date.today().isoformat(),
            "total_files": total_f, "total_size": human(total_b),
            "repo_size_with_git": human(walk(ROOT / ".git")[1] + total_b),
            "items": items}

# Infraestructura del repo: no se decide, se queda. Meterlas como items es ruido.
INTOCABLES = {"README.md", "install.sh", "PROGRESS.json", ".gitignore", ".claudeignore",
              ".worktreeinclude", "CLAUDE.md"}


def veredicto(i):
    """Recomendación con su razón. Nunca una recomendación a secas: sin porqué solo se obedece.

    Devuelve None para lo que NO requiere decisión — eso va a la tabla informativa del
    informe, no a la lista de items. Un informe donde la mitad de las filas son "esto
    obviamente se queda" enseña a hojearlo en vez de a decidirlo.
    """
    if i["kind"] == "dir-oculto" or i["path"] in INTOCABLES:
        return None
    if i["refs"] >= 8:                       # citado por todas partes: está vivo, no se decide
        return None
    r, age, n = i["refs"], i["age_days"] or 0, i["files"]
    if r == 0 and age > 60:
        return ("archivar", f"{n} ficheros, **0 referencias** desde `.claude/` y {age} días sin tocar: "
                            "no lo abre nadie, ni humano ni agente")
    if r == 0:
        return ("revisar", f"0 referencias, pero movido hace {age} días: mirar antes de decidir")
    if r <= 2 and age > 90:
        return ("revisar", f"solo {r} referencia(s) y {age} días sin tocar — candidato a archivar, "
                           "pero conviene ver quién lo cita")
    return ("mantener", f"{r} referencias desde `.claude/`: está en uso")

def main():
    a = sys.argv[1:]
    # Un argumento que no conoce NO escribe (antes `--help` o un typo caían en la rama final y
    # reescribían inventario.json). Solo escribe sin argumentos.
    if "-h" in a or "--help" in a:
        print(__doc__); return 0
    conocidos = {"--json", "--check", "--tasks"}
    raros = [x for x in a if x not in conocidos]
    if raros:
        print(f"gen_inventario: argumento(s) desconocido(s) {raros}; no se escribe nada. "
              f"Válidos: {', '.join(sorted(conocidos))} (o ninguno para regenerar).", file=sys.stderr)
        return 2
    d = build()
    if "--check" in a:
        if not OUT.exists():
            print("no hay inventario guardado", file=sys.stderr); return 1
        old = json.load(open(OUT))
        k = lambda x: {i["path"]: (i["files"], i["tracked"]) for i in x["items"]}
        if k(old) != k(d):
            print("DESFASADO: el inventario no refleja el disco", file=sys.stderr); return 1
        print(f"OK: inventario al día ({d['total_files']} ficheros)"); return 0
    if "--json" in a:
        print(json.dumps(d, indent=2, ensure_ascii=False)); return 0
    if "--tasks" in a:
        for i in d["items"]:
            v = veredicto(i)
            if not v: continue
            rec, razon = v
            sev = "P1" if rec == "archivar" else "P2"
            ident = i["path"].replace("/", "").replace(".", "")[:12].upper()
            print(f"- [ ] `INV-{ident}` [INV/{sev}/S] `{i['path']}` — {i['files']} ficheros · "
                  f"{i['size']} · {i['refs']} refs")
            print(f"  goal: decidir si se queda, se archiva o se retira")
            print(f"  desc: 📍 Cómo está ahora — {i['files']} ficheros, {i['size']}, citado desde "
                  f"**{i['refs']}** ficheros de `.claude/`, {i['tracked']} versionados, último commit "
                  f"{i['last_commit'] or 'nunca'}"
                  + (f", **{i['ghost_tracked']} versionados que ya no existen en disco**" if i["ghost_tracked"] else "")
                  + ".\n"
                  f"    🎯 Qué queremos — una raíz donde todo lo que está, está por algo.\n"
                  f"    🔧 Cómo — `git mv` a `_archive/2026-08-21/` con README del porqué, o dejarlo.\n"
                  f"    🧭 Por qué así — archivar es reversible y `self-improvement-loop.md` §5 exige "
                  f"dejar escrito por qué se retiró algo, o vuelve a nacer en seis meses.")
            print(f"  rec: {'aprobar' if rec == 'archivar' else 'duda'} — {razon}")
            print(f"  nocturno: {'si' if rec == 'archivar' else 'no'} — "
                  f"{'un git mv es reversible y verificable' if rec == 'archivar' else 'exige criterio'}")
        return 0
    OUT.write_text(json.dumps(d, indent=2, ensure_ascii=False) + "\n")
    print(f"Escrito {OUT} — {len(d['items'])} entradas, {d['total_files']} ficheros, {d['total_size']}")
    for i in sorted(d["items"], key=lambda x: -x["bytes"])[:6]:
        print(f"   {i['size']:>6}  {i['path']:<22} {i['refs']:>3} refs")
    return 0

if __name__ == "__main__":
    sys.exit(main())
