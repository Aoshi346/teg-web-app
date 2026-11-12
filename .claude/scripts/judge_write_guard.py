#!/usr/bin/env python3
"""judge_write_guard.py — PreToolUse (Write|Edit|MultiEdit|NotebookEdit|Bash): un juez solo escribe en su zona.

POR QUÉ (EQ-D14, sub-ola 3.11). 24 de los 29 agentes del template se presentan como jueces «sin poder de
escritura» porque no tienen Edit, pero tienen Write y Bash: Write reescribe un fichero entero y Bash hace
`sed -i`. Si el juez puede «arreglar de paso», su veredicto deja de ser independiente. Este hook convierte
«el juez no escribe» en un hecho: un agente cuyo `tools:` NO incluye Edit solo puede escribir en su zona
(`agents/shared/judge-write-zones.json`: `.docs/feedback/`, su carpeta `.claude/agents/<él>/`, `/tmp/` y
las extra de cada uno). Política: `rules/audit-team.md` §5.

QUIÉN ES JUEZ. Lo dice la entrada del hook: Claude Code pasa `agent_type` cuando la tool la llama un
subagente (doc hooks §Hook locations). Juez = existe `.claude/agents/<agent_type>.md` (proyecto o usuario)
con `tools:` declarado y sin Edit/MultiEdit. Sin `agent_type` (la sesión principal), un agente sin fichero
(Explore, general-purpose) o un agente con Edit: no se mira nada, exit 0.

SALIDA. 0 = pasa · 2 = bloqueado, con el motivo por stderr (lo lee el agente). Un fallo interno sale con 3
y decide el envoltorio (`hooks/judge-write-guard.sh`): bloquea solo si la llamada viene de un subagente.

LÍMITE HONESTO. Write/Edit/NotebookEdit se comprueban por ruta real (resolviendo `..` y enlaces): eso es
un hecho. Bash es heurístico: se miran redirecciones (`>`, `>>`), `tee`, `sed -i`/`perl -i`, `cp`/`mv`/
`rm`/`touch`/`truncate`/`ln`/`install`/`mkdir`/`dd of=`, `curl -o`/`wget -O`, `git` que escribe y `patch`,
el código en línea (`python -c`, `python - <<`, `node -e`) que abre ficheros para escribir, lo que va dentro
de `bash -c '…'`/`eval '…'`, y los `cd` del propio comando. Lo que no se ve: un script en fichero que
escribe por su cuenta (`python3 x.py`), rutas o directorios en variables (`> "$F"`, `cd "$D"`), ni un
comando que se construye en tiempo de ejecución. Por eso los
jueces siguen sin Edit y su encargo dice qué no tocan: el hook es la segunda capa, no la única.
"""
import fnmatch
import json
import os
import re
import shlex
import sys

TAG = "judge-write-guard"
EDIT_TOOLS = {"Edit", "MultiEdit", "NotebookEdit"}
FILE_TOOLS = {"Write", "Edit", "MultiEdit", "NotebookEdit"}
WRAP = {"sudo", "env", "nohup", "time", "command", "exec", "nice", "timeout", "stdbuf", "xargs"}
GIT_WRITE = {"add", "commit", "checkout", "switch", "restore", "reset", "apply", "am", "cherry-pick",
             "merge", "rebase", "revert", "stash", "push", "rm", "mv", "clean", "tag", "branch",
             "worktree", "update-index", "filter-branch", "notes", "pull", "fetch", "init", "clone"}
GIT_BRANCH_READ = {"--list", "-l", "-a", "-r", "--show-current", "-v", "-vv", "--contains", "--merged"}
TARGET_ALL = {"rm", "touch", "truncate", "mkdir", "rmdir", "shred", "unlink", "tee", "chmod", "chown"}
TARGET_LAST = {"cp", "mv", "install", "ln", "rsync"}
INLINE = re.compile(r"\b(python3?|node|perl|ruby)\b[^|;&]*?(\s-c\s|\s-e\s|\s-\s*<<|<<)")
WRITE_MARK = re.compile(r"write_text|write_bytes|open\([^)]*['\"][wax]\+?b?['\"]|writeFileSync|"
                        r"appendFileSync|createWriteStream|shutil\.(copy|move)|os\.(remove|rename|unlink)")
PATH_LIT = re.compile(r"['\"]((?:/|\./|\.\./|~/|\.[A-Za-z]|[A-Za-z0-9_-]+/)[^'\"\s]*)['\"]")
HEREDOC = re.compile(r"<<-?\s*(['\"]?)([A-Za-z_][A-Za-z0-9_]*)\1([^\n]*)\n(.*?)\n\s*\2\s*(?:\n|$)", re.S)
REDIR = re.compile(r"(?<![<>&0-9])(?:[0-9]|&)?>>?\|?\s*(?!&)([^\s;|&()<>]+)")


def project_root(event: dict) -> str:
    return os.path.realpath(os.environ.get("CLAUDE_PROJECT_DIR") or event.get("cwd") or os.getcwd())


def agent_file(root: str, name: str):
    if not re.fullmatch(r"[A-Za-z0-9_.-]+", name or ""):
        return None
    for base in (os.path.join(root, ".claude", "agents"), os.path.expanduser("~/.claude/agents")):
        p = os.path.join(base, name + ".md")
        if os.path.isfile(p):
            return p
    return None


def declared_tools(path: str):
    """Las tools del frontmatter, o None si no declara `tools:` (hereda todas: no es juez)."""
    text = open(path, encoding="utf-8", errors="replace").read()
    m = re.match(r"\A---\n(.*?)\n---", text, re.S)
    if not m:
        return None
    lines = m.group(1).splitlines()
    for i, line in enumerate(lines):
        if re.match(r"tools\s*:", line):
            val = line.split(":", 1)[1].strip()
            if not val:  # lista YAML en las líneas siguientes
                items = []
                for nxt in lines[i + 1:]:
                    mm = re.match(r"\s*-\s*(.+)", nxt)
                    if not mm:
                        break
                    items.append(mm.group(1))
                val = ",".join(items)
            val = val.strip("[]")
            return {t.strip().strip("'\"").split("(")[0] for t in val.split(",") if t.strip()}
    return None


def zones_for(root: str, agent: str):
    cfg_path = os.path.join(root, ".claude", "agents", "shared", "judge-write-zones.json")
    try:
        cfg = json.load(open(cfg_path, encoding="utf-8"))
    except (OSError, ValueError):
        cfg = {"default": [".docs/feedback/", ".claude/agents/{agent}/", "/tmp/", "/var/tmp/", "/dev/null"]}
    raw = list(cfg.get("default", [])) + list(cfg.get("extra", {}).get(agent, []))
    out = []
    for z in raw:
        z = os.path.expanduser(z.replace("{agent}", agent))
        out.append(z if os.path.isabs(z) else os.path.join(root, z))
    return out


def resolve(root: str, cwd: str, p: str) -> str:
    p = os.path.expanduser(p)
    if not os.path.isabs(p):
        p = os.path.join(cwd or root, p)
    return os.path.realpath(p)


def in_zone(path: str, zones) -> bool:
    for z in zones:
        if "*" in z:
            if fnmatch.fnmatch(path, z.rstrip("/") + "/*"):
                return True
            continue
        zr = os.path.realpath(z.rstrip("/"))
        if z.endswith("/"):
            if path == zr or path.startswith(zr + os.sep):
                return True
        elif path == zr:
            return True
    return False


def strip_quoted(cmd: str) -> str:
    """Quita el cuerpo de los heredocs y lo entrecomillado, para no leer un `>` dentro de un texto.
    Lo que sigue al `<<TAG` en su misma línea (`cat <<E > f`) se conserva: ahí va la redirección."""
    cmd = HEREDOC.sub(lambda m: "<<HEREDOC" + m.group(3) + "\n", cmd)
    return re.sub(r"'[^']*'|\"(?:\\.|[^\"\\])*\"", "''", cmd)


def nested_shells(cmd: str):
    """El texto de `bash -c '…'`, `sh -c "…"` y `eval '…'`: se analiza como un comando más."""
    pat = (r"(?:\b(?:bash|sh|zsh|dash)\s+-[a-z]*c[a-z]*\s+|\beval\s+)"
           r"(?:'([^']*)'|\"((?:\\.|[^\"\\])*)\")")
    for m in re.finditer(pat, cmd):
        yield m.group(1) if m.group(1) is not None else m.group(2)


def bash_targets(cmd: str, cwd: str, depth: int = 0):
    """(rutas absolutas que el comando escribiría, motivos que bloquean sin ruta).
    Sigue los `cd` del propio comando: una ruta relativa se resuelve desde donde de verdad se escribe."""
    targets, reasons = [], []
    for seg in re.split(r"\|\||&&|;|\||\n|&(?!>)", strip_quoted(cmd)):
        try:
            toks = shlex.split(seg, posix=True)
        except ValueError:
            toks = seg.split()
        while toks and (toks[0] in WRAP or re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]*=.*", toks[0])):
            toks = toks[1:]
        if not toks:
            continue
        here = [m.group(1) for m in REDIR.finditer(seg)]
        name = os.path.basename(toks[0])
        args = [t for t in toks[1:] if not t.startswith("-")]
        if name == "cd":
            dest = args[0] if args else "~"
            if not dest.startswith("$"):
                cwd = os.path.join(cwd, os.path.expanduser(dest))
            continue
        if name in ("curl", "wget"):
            flags = ("-o", "--output") if name == "curl" else ("-O", "--output-document")
            for i, t in enumerate(toks[1:], 1):
                if t in flags and i + 1 < len(toks):
                    here.append(toks[i + 1])
                elif any(t.startswith(f + "=") for f in flags):
                    here.append(t.split("=", 1)[1])
        elif name in ("sed", "perl") and any(t == "-i" or t.startswith("-i") or t == "--in-place"
                                            or t.startswith("--in-place") for t in toks[1:]):
            files = args[1:] if name == "sed" and args else args
            if not files:
                reasons.append(f"`{name} -i` sin fichero visible")
            here.extend(files)
        elif name in TARGET_ALL:
            here.extend(args[1:] if name in ("chmod", "chown") else args)
        elif name in TARGET_LAST and args:
            if "-t" in toks:
                i = toks.index("-t")
                if i + 1 < len(toks):
                    here.append(toks[i + 1])
            else:
                here.append(args[-1])
        elif name == "dd":
            here.extend(t[3:] for t in toks[1:] if t.startswith("of="))
        elif name == "patch":
            reasons.append("`patch` modifica ficheros")
        elif name == "git":
            sub = next((t for t in toks[1:] if not t.startswith("-") and "=" not in t), "")
            if sub == "branch" and (len(toks) == 2 or any(t in GIT_BRANCH_READ for t in toks[2:])):
                continue
            if sub == "stash" and len(toks) > 2 and toks[2] in ("list", "show"):
                continue
            if sub in GIT_WRITE:
                reasons.append(f"`git {sub}` cambia el repo")
        targets.extend(os.path.join(cwd, os.path.expanduser(t)) for t in here if t and not t.startswith("$"))
    if depth < 3:
        for inner in nested_shells(cmd):
            t, r = bash_targets(inner, cwd, depth + 1)
            targets.extend(t)
            reasons.extend(r)
    if INLINE.search(cmd) and WRITE_MARK.search(cmd):
        lits = PATH_LIT.findall(cmd)
        if not lits:
            reasons.append("código en línea que escribe ficheros sin ruta literal que comprobar")
        targets.extend(os.path.join(cwd, os.path.expanduser(t)) for t in lits)
    return targets, reasons


def decide(event: dict) -> int:
    agent = event.get("agent_type") or ""
    if not agent:
        return 0
    root = project_root(event)
    af = agent_file(root, agent)
    if not af:
        return 0
    tools = declared_tools(af)
    if tools is None or tools & EDIT_TOOLS:
        return 0
    zones = zones_for(root, agent)
    tool = event.get("tool_name", "")
    inp = event.get("tool_input") or {}
    cwd = event.get("cwd") or root
    if tool in FILE_TOOLS:
        p = inp.get("file_path") or inp.get("notebook_path") or ""
        if not p:
            return 0
        rp = resolve(root, cwd, p)
        if in_zone(rp, zones):
            return 0
        return block(agent, f"{tool} sobre {rp}", zones, root)
    if tool == "Bash":
        start = cwd if os.path.isabs(cwd) else root
        targets, reasons = bash_targets(inp.get("command", "") or "", start)
        outside = [t for t in (os.path.realpath(x) for x in targets) if not in_zone(t, zones)]
        if reasons or outside:
            what = "; ".join(reasons + [f"escribe en {t}" for t in outside])
            return block(agent, f"Bash: {what}", zones, root)
    return 0


def block(agent: str, what: str, zones, root: str) -> int:
    rel = [os.path.relpath(z, root) if z.startswith(root) else z for z in zones]
    sys.stderr.write(
        f"[{TAG}] BLOQUEADO: «{agent}» es un juez (sin Edit) y {what} queda fuera de su zona.\n"
        f"Un juez informa, no arregla (rules/audit-team.md §5). Zona permitida: {', '.join(rel)}.\n"
        "Escribe el hallazgo en tu REPORT con la propuesta de arreglo; lo aplica quien hizo el trabajo.\n")
    return 2


def main() -> int:
    try:
        event = json.load(sys.stdin)
    except ValueError:
        return 0
    if os.environ.get("TL_JUEZ_SABOTAJE") == "excepcion":
        raise RuntimeError("sabotaje plantado")
    return decide(event)


if __name__ == "__main__":
    try:
        sys.exit(main())
    except SystemExit:
        raise
    except Exception as exc:  # defensive: el envoltorio decide si un fallo interno bloquea
        sys.stderr.write(f"[{TAG}] fallo interno: {exc}\n")
        sys.exit(3)
