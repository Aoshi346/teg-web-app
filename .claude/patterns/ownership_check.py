#!/usr/bin/env python3
"""ownership_check.py — capa determinista del contrato de propiedad (AGT-8).

Lee `.claude/patterns/ownership.yaml` y aplica la HERENCIA VERTICAL:
    forbids / needs_approval efectivos = UNIÓN de los de todos los ancestros del fichero
    can_modify efectivo                = INTERSECCIÓN de los de todos los ancestros
    el hijo solo puede ESTRECHAR — si intenta ampliar, es error de config (--lint)

Uso:
    python3 .claude/patterns/ownership_check.py                  # ficheros cambiados (git)
    python3 .claude/patterns/ownership_check.py <ruta> [...]     # ficheros concretos
    python3 .claude/patterns/ownership_check.py --from <scope> [f...]  # + prohibiciones cross-scope
    python3 .claude/patterns/ownership_check.py --lint           # coherencia del contrato
    python3 .claude/patterns/ownership_check.py --explain <ruta> # contrato efectivo + reglas citables

Salida: exit 1 si hay violación de `forbids` (o error de config en --lint); 0 si solo hay avisos.
`--explain` es lo que Rita cita como REGLA DURA, además de sus precedentes medidos.

Parser YAML a mano (sin pyyaml), misma disciplina que scripts/gen_docs.py: el formato de
ownership.yaml es un subconjunto fijo (escalares, listas inline entre corchetes y listas de
strings indentadas). Si el fichero deja de encajar, el error se dice en voz alta, no se adivina.
"""
import os
import re
import subprocess
import sys

ROOT = subprocess.run(["git", "rev-parse", "--show-toplevel"], capture_output=True,
                      text=True).stdout.strip() or os.getcwd()
CONTRACT = os.path.join(ROOT, ".claude", "patterns", "ownership.yaml")
LIST_KEYS = ("can_modify", "forbids", "needs_approval", "depends_on")


# ─────────────────────────── parser ───────────────────────────

def load_scopes(path=CONTRACT):
    if not os.path.exists(path):
        return []
    scopes, cur, in_rules = [], None, False
    for raw in open(path, encoding="utf-8"):
        line = raw.rstrip("\n")
        if not line.strip() or line.lstrip().startswith("#"):
            continue
        m = re.match(r"\s*-\s+path:\s*(.+?)\s*$", line)
        if m:
            cur = {"path": m.group(1).strip().strip('"'), "owns": "", "rules": [],
                   "source": "", **{k: [] for k in LIST_KEYS}}
            scopes.append(cur)
            in_rules = False
            continue
        if cur is None:
            continue
        if re.match(r"\s+rules:\s*$", line):
            in_rules = True
            continue
        m = re.match(r'\s+-\s+"(.*)"\s*$', line)
        if m and in_rules:
            cur["rules"].append(m.group(1))
            continue
        m = re.match(r"\s+(\w+):\s*(.*)$", line)
        if m:
            in_rules = False
            key, val = m.group(1), m.group(2).strip()
            if key in LIST_KEYS:
                cur[key] = [v.strip().strip('"') for v in val.strip("[]").split(",") if v.strip()]
            elif key in ("owns", "source"):
                cur[key] = val.strip('"')
    return scopes


# ─────────────────────────── globs ───────────────────────────

def to_regex(glob):
    """Traduce un glob a regex con semántica de rutas: * no cruza '/', ** sí."""
    out, i = "", 0
    while i < len(glob):
        if glob.startswith("**/", i):
            out += "(?:.*/)?"
            i += 3
        elif glob.startswith("**", i):
            out += ".*"
            i += 2
        elif glob[i] == "*":
            out += "[^/]*"
            i += 1
        elif glob[i] == "?":
            out += "[^/]"
            i += 1
        else:
            out += re.escape(glob[i])
            i += 1
    return re.compile("^" + out + "$")


def matches(glob, path):
    return bool(to_regex(glob).match(path))


def norm(p):
    p = p.replace("\\", "/")
    while p.startswith("./"):
        p = p[2:]
    return "" if p == "." else p


def is_ancestor(scope_path, file_path):
    sp = norm(scope_path)
    return sp == "" or norm(file_path).startswith(sp.rstrip("/") + "/")


# ─────────────────────────── contrato efectivo ───────────────────────────

def effective(file_path, scopes):
    """Herencia vertical: unión de prohibiciones, intersección de permisos."""
    anc = [s for s in scopes if is_ancestor(s["path"], file_path)]
    anc.sort(key=lambda s: len(norm(s["path"])))
    eff = {"scopes": anc, "forbids": [], "needs_approval": [], "rules": [], "can_modify": True}
    for s in anc:
        for key in ("forbids", "needs_approval"):
            eff[key] += [(g, s) for g in s[key]]
        eff["rules"] += [(r, s) for r in s["rules"]]
        # intersección: TODOS los ancestros con can_modify declarado tienen que cubrirlo
        if s["can_modify"] and not any(matches(g, norm(file_path)) for g in s["can_modify"]):
            eff["can_modify"] = False
    return eff


def changed_files():
    cmds = [["git", "diff", "--name-only", "HEAD"],
            ["git", "diff", "--cached", "--name-only"],
            ["git", "ls-files", "--others", "--exclude-standard"]]
    out = set()
    for c in cmds:
        r = subprocess.run(c, capture_output=True, text=True, cwd=ROOT)
        out |= {l.strip() for l in r.stdout.splitlines() if l.strip()}
    return sorted(out)


# ─────────────────────────── comandos ───────────────────────────

def acting_scope_rules(from_path, scopes):
    """Forbids/needs_approval que arrastra QUIEN edita (scope actuante + sus ancestros).

    Es la mitad cross-scope del contrato: '.claude/templates/report_kit/ no toca speckit_dashboard/'
    solo puede comprobarse sabiendo desde dónde se trabaja. Sin --from, solo se aplican las
    prohibiciones que cuelgan del propio fichero cambiado.
    """
    if not from_path:
        return {"forbids": [], "needs_approval": []}
    nf = norm(from_path).rstrip("/") + "/x"
    anc = [s for s in scopes if is_ancestor(s["path"], nf) or norm(s["path"]).rstrip("/") == norm(from_path).rstrip("/")]
    return {"forbids": [(g, s) for s in anc for g in s["forbids"]],
            "needs_approval": [(g, s) for s in anc for g in s["needs_approval"]]}


def cmd_check(files, scopes, from_path=None):
    fail = warn = 0
    acting = acting_scope_rules(from_path, scopes)
    for f in files:
        nf = norm(f)
        eff = effective(nf, scopes)
        for key in ("forbids", "needs_approval"):
            eff[key] += [x for x in acting[key] if x not in eff[key]]
        for glob, s in eff["forbids"]:
            if matches(glob, nf):
                print(f"✗ [PROHIBIDO] {nf} — coincide con forbids '{glob}' del scope '{s['path']}'")
                print(f"   fuente: {s['source']}")
                fail += 1
        for glob, s in eff["needs_approval"]:
            if matches(glob, nf):
                print(f"⚠ [APROBACIÓN] {nf} — '{glob}' del scope '{s['path']}' exige OK explícito")
                print(f"   fuente: {s['source']}")
                warn += 1
        if eff["scopes"] and eff["can_modify"] is False:
            owner = eff["scopes"][-1]["path"]
            print(f"⚠ [FUERA DE SCOPE] {nf} — ningún can_modify del scope '{owner}' lo cubre")
            warn += 1
    if fail:
        print(f"\nownership: {fail} violación(es) de forbids — detalle en .claude/patterns/ownership.yaml")
        return 1
    print(f"ownership: OK ({len(files)} fichero(s), {warn} aviso(s))")
    return 0


def cmd_lint(scopes):
    """El hijo no puede ampliar lo que el padre prohíbe."""
    bad = 0
    if not scopes:
        print("✗ ownership.yaml vacío o ilegible")
        return 1
    for child in scopes:
        for parent in scopes:
            if parent is child or not is_ancestor(parent["path"], child["path"].rstrip("/") + "/x"):
                continue
            for pg in parent["forbids"]:
                for cg in child["can_modify"]:
                    # el hijo permite explícitamente algo que el padre prohíbe de forma literal
                    if cg == pg or (pg.endswith("/**") and cg.startswith(pg[:-2])):
                        print(f"✗ CONFIG: '{child['path']}' permite '{cg}' que '{parent['path']}' prohíbe ('{pg}')")
                        bad += 1
    dups = {s["path"] for s in scopes if [x["path"] for x in scopes].count(s["path"]) > 1}
    for d in dups:
        print(f"✗ CONFIG: scope duplicado '{d}'")
        bad += 1
    for s in scopes:
        if not s["source"]:
            print(f"⚠ CONFIG: scope '{s['path']}' sin `source:` — una regla sin fuente no es citable")
    print("ownership --lint: " + (f"{bad} error(es)" if bad else f"OK ({len(scopes)} scopes)"))
    return 1 if bad else 0


def cmd_explain(path, scopes):
    nf = norm(path)
    eff = effective(nf, scopes)
    if not eff["scopes"]:
        print(f"{nf}: sin scope declarado en ownership.yaml")
        return 0
    print(f"CONTRATO EFECTIVO de {nf}")
    print("  scopes (padre→hijo): " + " → ".join(s["path"] for s in eff["scopes"]))
    owner = eff["scopes"][-1]
    print(f"  owner: {owner['path']} — {owner['owns']}")
    print("  puede modificarlo: " + ("sí" if eff["can_modify"] else "NO (fuera de can_modify)"))
    for glob, s in eff["forbids"]:
        if matches(glob, nf):
            print(f"  PROHIBIDO por '{glob}' ({s['path']})")
    for glob, s in eff["needs_approval"]:
        if matches(glob, nf):
            print(f"  NECESITA APROBACIÓN por '{glob}' ({s['path']})")
    print("  reglas duras citables:")
    for r, s in eff["rules"]:
        print(f"    · {r}   [{s['path']} — {s['source']}]")
    return 0


def main(argv):
    scopes = load_scopes()
    if argv and argv[0] == "--lint":
        return cmd_lint(scopes)
    if argv and argv[0] == "--explain":
        if len(argv) < 2:
            print("uso: ownership_check.py --explain <ruta>")
            return 2
        return cmd_explain(argv[1], scopes)
    from_path = None
    if argv and argv[0] == "--from":
        if len(argv) < 2:
            print("uso: ownership_check.py --from <scope> [ficheros...]")
            return 2
        from_path, argv = argv[1], argv[2:]
    files = argv or changed_files()
    if not files:
        print("ownership: sin ficheros que comprobar")
        return 0
    return cmd_check(files, scopes, from_path)


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
