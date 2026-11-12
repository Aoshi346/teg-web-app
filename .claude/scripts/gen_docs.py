#!/usr/bin/env python3
"""gen_docs.py — genera documentation/estado.html escaneando el repo REAL.

Inventaria skills, agents, rules, workflows, commands, hooks, templates, scripts
y patterns de .claude/ e inyecta el JSON en documentation/estado.template.html
(placeholder EXACTO `const DB = /*__DATA__*/null;`, mismo patrón que la función
inject de .claude/templates/report_kit/build.py).

Uso:  python3 .claude/scripts/gen_docs.py [--check]
      --check: no escribe; sale 1 si documentation/estado.html está desfasado
               respecto al repo (compara ignorando fecha/sha, mismo contrato
               que gen_skill_index.py --check), o si cheatsheet-extended.html no
               es lo que sale de cheatsheet-extended.md.

También genera documentation/cheatsheet-extended.html desde cheatsheet-extended.md
(LI-32, sub-ola 1.07: la chuleta existía en los dos formatos, escritos a mano, y ya se
contradecían). El .md es la única fuente; el HTML lo pinta report_kit/md_to_html.py,
sin dependencias.

Los contadores se mantienen honestos: el estado se REGENERA, no se edita a mano.
"""
import datetime
import json
import re
import subprocess
import sys
import unicodedata
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]  # raíz del repo
CLAUDE = ROOT / ".claude"
DOC = ROOT / "documentation"
TEMPLATE = DOC / "estado.template.html"
OUT = DOC / "estado.html"
PLACEHOLDER = "/*__DATA__*/null"
CHULETA_MD = DOC / "cheatsheet-extended.md"
CHULETA_HTML = DOC / "cheatsheet-extended.html"

# ── Clasificación de skills (copiada de gen_skill_index.py — mantener en sync) ──
GROUPS = [
    ("Meta (crear/mantener agentes y skills)", re.compile(
        r"^(create-agent|check-agent|update-agent|"
        r"skill-authoring|codebase-onboarding|project-setup|"
        r"consolidate-agent-learnings|department-agent-authoring|crear-cliente|crear-flujo|"
        r"fix-tl-issues|flow-tester)$")),
    ("Fundamentos de Claude Code", re.compile(r"^claude-code-referencia$")),
    ("Workflow y proceso", re.compile(
        r"^(prompt-contracts|"
        r"auto-dream-memory|verification-loops|code-review-gate|"
        r"codex-adversarial-review|ux-reviewer|naive-user-playthrough|feedback-audit)$")),
    ("Salida y visual", re.compile(r"^(html-suelto|pdf-premium|documentar|translate-content|code-graph)$")),
    ("Dominio (stack-specific)", re.compile(
        r"^(django-orm|multi-tenant-context|webhook-multi-tenant-validation|vector-db|"
        r"langgraph-debug|connect-external-api)")),
]
SKILL_CATEGORIES = [g[0] for g in GROUPS] + ["Otros"]

# ── Grupos de agentes para la vista "Por tipo" ──
AGENT_PERSONAS = {
    "aitor-a11y-auditor", "bruno-perf-cop", "conrado-cro-auditor", "ignacio-roig",
    "lena-i18n-auditor", "lidia-naive-tester", "marco-qa-breaker", "nadia-chatbot-evaluator",
    "pilar-impacto-produccion", "priya-privacy-auditor",
    "rita-pattern-keeper", "roberto-clean-code", "sofia-pentester",
    "vera-art-director",
}
# Otto salió de aquí el 2026-08-21: es skill, no agente (_archive/2026-08-21/).
# Su carpeta `agents/otto-copilot/` sobrevive, pero solo guarda memoria: no hay .md que agrupar.
# security-qa-bundle salió de aquí el 2026-08-22: no era un agente (sin `name:`, el harness no lo
# cargaba nunca) sino documentación del par Sofía+Marco — archivado en _archive/2026-08-22/.
AGENT_META = {"pol-product-advisor"}
AGENT_GROUPS = ["auditores-persona", "especialistas", "meta"]
AGENT_EXCLUDE = {"README", "_deprecated", "shared", "personas"}

# ── Temas (tabla EDITABLE: keywords sobre name+description, case/accent-insensitive) ──
TOPIC_RULES = [
    ("informes-y-visual", ["report-kit", "report_kit", "html", "dashboard", "visual-map",
                           "schema", "pdf", "artifact", "nav", "dataviz", "informe"]),
    ("qa-ux", ["qa-loop", "lidia", "vera", "ignacio", "aitor", "bruno", "conrado", "lena",
               "nadia", "tomas", "ux", "naive", "audit", "feedback", "playthrough"]),
    ("patrones-y-consistencia", ["rita", "roberto", "pattern", "simplify", "code-style"]),
    ("orquestación-y-autonomía", ["workflow", "loop", "goal", "parallel", "agent-team",
                                  "worktree", "subagent", "tasking", "orquesta"]),
    ("memoria-y-sesiones", ["memory", "dream", "compact", "retro", "progress", "sesión"]),
    ("setup-y-meta", ["create-agent", "project-setup", "check-agent", "update-agent", "catalog",
                      "onboarding", "harness", "claude-code", "skill-authoring", "settings",
                      "permissions", "hooks"]),
    ("dominio-stacks", ["django", "vector", "langgraph", "webhook", "tenant", "wordpress",
                        "llm", "orm"]),
    ("seguridad-y-compliance", ["security", "pentest", "privacy", "sofia", "priya",
                                "sandbox", "deploy"]),
    ("multicliente-archivado", ["crear-cliente", "crear-flujo", "flow-tester", "fix-tl",
                               "department", "telegram"]),
    ("código-y-estructura", ["code-graph", "codebase", "graphify", "review-branch",
                             "bug-sweep", "verdict", "verification"]),
]
TOPICS_ORDER = [t for t, _ in TOPIC_RULES] + ["otros"]

# ── Badges por nombre exacto de item ──
BADGES = {
    "report_kit": "CORE", "otto": "CORE", "pol-product-advisor": "CORE",
    "rita-pattern-keeper": "SOMBRA", "roberto-clean-code": "FASE 1",
    "pilar-impacto-produccion": "FASE 1",
    # "speckit_dashboard" y "plan-dashboard" (LEGACY) salieron el 2026-10-19: archivados (LI-12).
}


# ═══════════════ helpers ═══════════════

def read(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="replace")


def strip_accents(s: str) -> str:
    return "".join(c for c in unicodedata.normalize("NFD", s) if not unicodedata.combining(c))


def frontmatter(text: str) -> str:
    m = re.match(r"^---\n(.*?)\n---", text, re.S)
    return m.group(1) if m else ""


def fm_desc(fm: str) -> str:
    """description del frontmatter — lógica copiada de gen_skill_index.frontmatter_desc
    (soporta `description: |` / `>` multilinea), sin el truncado (trunca el HTML)."""
    if not fm:
        return "(sin frontmatter)"
    bm = re.search(r"^description:\s*[|>][+-]?\s*\n((?:[ \t]+.*\n?)+)", fm, re.M)
    if bm:
        desc = " ".join(l.strip() for l in bm.group(1).splitlines() if l.strip())
    else:
        dm = re.search(r'^description:\s*["\']?(.*?)["\']?\s*$', fm, re.M)
        desc = (dm.group(1) if dm else "(sin description)").strip().strip('"').strip("'")
    return re.sub(r"\s+", " ", desc)


def first_sentence(s: str, cap: int = 300) -> str:
    parts = re.split(r"(?<=\.)\s+(?=[A-ZÁÉÍÓÚÑ¿])", s, maxsplit=1)
    out = parts[0].strip()
    return out[:cap - 1] + "…" if len(out) > cap else out


# ═══════════════ colectores ═══════════════

def collect_skills():
    items = []
    for d in sorted((CLAUDE / "skills").iterdir()):
        f = d / "SKILL.md"
        if not d.is_dir() or not f.exists():
            continue
        fm = frontmatter(read(f))
        invocable = not re.search(r"^user-invocable:\s*false\s*$", fm, re.M)
        category = next((label for label, rx in GROUPS if rx.match(d.name)), "Otros")
        items.append({
            "type": "skill", "name": d.name, "desc": fm_desc(fm),
            "path": f".claude/skills/{d.name}/SKILL.md",
            "category": category, "invocable": invocable,
        })
    return items


def collect_agents():
    items = []
    for f in sorted((CLAUDE / "agents").glob("*.md")):
        if f.stem in AGENT_EXCLUDE:
            continue
        fm = frontmatter(read(f))
        nm = re.search(r"^name:\s*(.+?)\s*$", fm, re.M)
        mm = re.search(r"^model:\s*(.+?)\s*$", fm, re.M)
        name = (nm.group(1).strip().strip('"').strip("'") if nm else f.stem)
        group = ("auditores-persona" if f.stem in AGENT_PERSONAS
                 else "meta" if f.stem in AGENT_META else "especialistas")
        items.append({
            "type": "agent", "name": name, "desc": fm_desc(fm),
            "path": f".claude/agents/{f.name}",
            "model": (mm.group(1).strip() if mm else ""),
            "has_memory": (CLAUDE / "agents" / f.stem).is_dir(),
            "group": group,
        })
    return items


def rule_desc(text: str) -> str:
    lines = text.splitlines()
    for i, l in enumerate(lines):
        m = re.match(r">\s*\*\*Cuándo aplicar:?\*\*:?\s*(.*)", l)
        if m:
            buf = [m.group(1)]
            for l2 in lines[i + 1:]:
                if not l2.startswith(">"):
                    break
                cont = l2.lstrip(">").strip()
                if not cont or cont.startswith("**"):
                    break
                buf.append(cont)
            desc = re.sub(r"\*\*|`", "", " ".join(buf))
            return first_sentence(re.sub(r"\s+", " ", desc).strip())
    h1 = re.search(r"^#\s+(.+?)\s*$", text, re.M)  # primera línea útil: el H1
    if h1:
        return re.sub(r"[*`]", "", h1.group(1)).strip()
    for l in lines:
        if l.strip():
            return re.sub(r"[>#*`]", "", l).strip()
    return "(vacío)"


def collect_rules():
    return [{
        "type": "rule", "name": f.stem, "desc": rule_desc(read(f)),
        "path": f".claude/rules/{f.name}",
    } for f in sorted((CLAUDE / "rules").glob("*.md"))]


def collect_workflows():
    items = []
    for f in sorted((CLAUDE / "workflows").glob("*.js")):
        text = read(f)
        block_m = re.search(r"export const meta\s*=\s*\{(.*?)\n\}", text, re.S)
        block = block_m.group(1) if block_m else ""
        nm = re.search(r"""name:\s*['"]([^'"]+)['"]""", block)
        dm = re.search(r"""description:\s*(['"])(.+?)\1""", block, re.S)
        items.append({
            "type": "workflow", "name": (nm.group(1) if nm else f.stem),
            "desc": re.sub(r"\s+", " ", dm.group(2)).strip() if dm else "(sin meta.description)",
            "path": f".claude/workflows/{f.name}",
        })
    return items


def collect_commands():
    items = []
    for f in sorted((CLAUDE / "commands").glob("*.md")):
        text = read(f)
        h1 = re.search(r"^#\s+(.+?)\s*$", text, re.M)
        if h1:
            desc = h1.group(1).strip()
        else:
            desc = fm_desc(frontmatter(text))
            if desc in ("(sin frontmatter)", "(sin description)"):
                desc = next((l.strip() for l in text.splitlines()
                             if l.strip() and l.strip() != "---"), "(vacío)")
        items.append({
            "type": "command", "name": f.stem, "desc": desc,
            "path": f".claude/commands/{f.name}",
        })
    return items


def hook_events() -> dict:
    """filename → eventos donde está registrado, cruzando con settings.json."""
    events: dict = {}
    settings_path = CLAUDE / "settings.json"
    if not settings_path.exists():
        return events
    try:
        settings = json.loads(read(settings_path))
    except ValueError:
        return events
    for ev, entries in (settings.get("hooks") or {}).items():
        for entry in entries:
            for h in entry.get("hooks", []):
                cmd = h.get("command", "")
                for hf in (CLAUDE / "hooks").glob("*.sh"):
                    if hf.name in cmd:
                        events.setdefault(hf.name, [])
                        if ev not in events[hf.name]:
                            events[hf.name].append(ev)
    return events


def collect_hooks():
    items = []
    registered = hook_events()
    for f in sorted((CLAUDE / "hooks").glob("*.sh")):
        comments = []
        for l in read(f).splitlines()[1:]:  # tras el shebang
            ls = l.strip()
            if ls.startswith("#!"):
                continue
            if ls.startswith("#"):
                c = ls.lstrip("#").strip()
                if c:
                    comments.append(c)
                continue
            if ls == "" and not comments:
                continue
            break
        desc = comments[0] if comments else "(sin comentario)"
        if desc.lower().startswith(f.name.lower()):
            desc = desc[len(f.name):].lstrip(" —–-:").strip()
        if len(desc) < 30 and len(comments) > 1:
            desc = (desc + " — " if desc else "") + comments[1]
        items.append({
            "type": "hook", "name": f.stem, "desc": desc,
            "path": f".claude/hooks/{f.name}",
            "event": " + ".join(registered.get(f.name, [])) or "manual",
        })
    return items


def collect_templates():
    items = []
    for d in sorted((CLAUDE / "templates").iterdir()):
        if not d.is_dir() or d.name == "__pycache__":
            continue
        desc = "(sin README)"
        readme = d / "README.md"
        if readme.exists():
            line = next((l.strip() for l in read(readme).splitlines() if l.strip()), "")
            line = line.lstrip("#").strip()
            # limpiar el prefijo redundante "`<dir>/` — " del propio README
            line = re.sub(r"^`?\.?(\.claude/templates/)?" + re.escape(d.name) + r"/?`?\s*[—–:-]+\s*",
                          "", line).strip()
            desc = line or desc
        items.append({
            "type": "template", "name": d.name, "desc": desc,
            "path": f".claude/templates/{d.name}/",
        })
    return items


def collect_scripts():
    items = []
    for f in sorted((CLAUDE / "scripts").glob("*.py")):
        m = re.search(r'"""(.*?)"""', read(f), re.S)
        desc = "(sin docstring)"
        if m:
            para = m.group(1).strip().split("\n\n")[0]  # primer párrafo del docstring
            desc = re.sub(r"\s+", " ", para).strip()
            if desc.lower().startswith(f.name.lower()):
                desc = desc[len(f.name):].lstrip(" —–-:").strip()
        items.append({
            "type": "script", "name": f.stem, "desc": desc,
            "path": f".claude/scripts/{f.name}",
        })
    return items


def collect_patterns():
    """Parse a mano de patterns/catalog.yaml (línea a línea, SIN pyyaml)."""
    items, cur = [], None
    path = CLAUDE / "patterns" / "catalog.yaml"
    if not path.exists():
        return items
    for line in read(path).splitlines():
        m = re.match(r"\s*-\s+id:\s*(\S+)", line)
        if m:
            cur = {"type": "pattern", "name": m.group(1), "desc": "",
                   "dominancia": "", "estado": "", "pct": None,
                   "path": ".claude/patterns/catalog.yaml"}
            items.append(cur)
            continue
        if cur is None:
            continue
        fm = re.match(r'\s+(enunciado|dominancia|estado):\s*"?([^"#]*?)"?\s*(#.*)?$', line)
        if fm:
            key, val = fm.group(1), fm.group(2).strip()
            if key == "enunciado":
                cur["desc"] = val
            elif key == "dominancia":
                cur["dominancia"] = val
                pm = re.search(r"\((\d+)%\)", val)
                cur["pct"] = int(pm.group(1)) if pm else None
            elif key == "estado":
                cur["estado"] = val
    return items


# ═══════════════ ensamblado ═══════════════

def topics_for(item: dict) -> list:
    hay = strip_accents((item["name"] + " " + item.get("desc", "")).lower())
    ts = [topic for topic, kws in TOPIC_RULES
          if any(strip_accents(k.lower()) in hay for k in kws)]
    return ts or ["otros"]


def build_db() -> dict:
    items = (collect_skills() + collect_agents() + collect_rules() + collect_workflows()
             + collect_commands() + collect_hooks() + collect_templates()
             + collect_scripts() + collect_patterns())
    for it in items:
        it["topics"] = topics_for(it)
        badge = BADGES.get(it["name"])
        if badge:
            it["badge"] = badge
    counts: dict = {}
    for it in items:
        counts[it["type"]] = counts.get(it["type"], 0) + 1
    try:
        sha = subprocess.run(["git", "rev-parse", "--short", "HEAD"], cwd=ROOT,
                             capture_output=True, text=True).stdout.strip() or "nogit"
    except OSError:
        sha = "nogit"
    return {
        "meta": {"fecha": datetime.date.today().isoformat(), "sha": sha, "counts": counts},
        "items": items,
        "topics": TOPICS_ORDER,
        "skill_categories": SKILL_CATEGORIES,
        "agent_groups": AGENT_GROUPS,
    }


def render(db: dict) -> str:
    """Inyección — mismo patrón que report_kit/build.py::inject."""
    tpl = read(TEMPLATE)
    payload = json.dumps(db, ensure_ascii=False)
    html = tpl.replace(PLACEHOLDER, payload)
    if html == tpl:
        print(f"aviso: {TEMPLATE.name} no tiene placeholder {PLACEHOLDER}")
    return html


def normalize(s: str) -> str:
    """Para --check: ignorar fecha y sha (viven solo en el JSON de meta)."""
    s = re.sub(r'"sha":\s*"[^"]*"', '"sha":""', s)
    s = re.sub(r'"fecha":\s*"[^"]*"', '"fecha":""', s)
    return s


CHULETA_SHELL = """<!doctype html>
<html lang="es">
<!-- GENERADO por .claude/scripts/gen_docs.py desde cheatsheet-extended.md — NO editar a mano: se edita el .md -->
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{title}</title>
<style>{css}</style>
</head>
<body>
<header class="hero"><div class="wrap">
  <p class="eyebrow">Chuleta de Claude Code · generada desde cheatsheet-extended.md</p>
  <h1>{title}</h1>
  <a class="back" href="README.md">← documentation/</a> · <a class="back" href="estado.html">estado del template</a>
</div></header>
<main class="wrap">
{body}
</main>
</body>
</html>
"""


def chuleta() -> str:
    """El HTML de la chuleta, pintado desde su única fuente (el .md)."""
    sys.path.insert(0, str(CLAUDE / "templates" / "report_kit"))
    import md_to_html  # noqa: E402 — vecino del kit, sin dependencias
    md = read(CHULETA_MD)
    m = re.match(r"^\s*#\s+(.+?)\s*\n", md)
    title = m.group(1) if m else "Claude Code Cheat Sheet"
    md = re.sub(r"^\s*#\s+.*?\n", "", md, count=1)
    return CHULETA_SHELL.format(title=md_to_html.html.escape(title, quote=False),
                                css=md_to_html.CSS, body=md_to_html.convert(md))


def main():
    if not TEMPLATE.exists():
        sys.exit(f"ERROR: falta la plantilla {TEMPLATE}")
    db = build_db()
    content = render(db)
    n = len(db["items"])
    hoja = chuleta() if CHULETA_MD.exists() else None
    if "--check" in sys.argv:
        current = read(OUT) if OUT.exists() else ""
        mal = 0
        if normalize(current) != normalize(content):
            print(f"DESFASADO: {OUT} no coincide con el repo real ({n} items)")
            mal = 1
        if hoja is not None and (read(CHULETA_HTML) if CHULETA_HTML.exists() else "") != hoja:
            print(f"DESFASADO: {CHULETA_HTML.name} no es lo que sale de {CHULETA_MD.name}")
            mal = 1
        if mal:
            sys.exit(1)
        print(f"OK: {OUT.name} al día ({n} items)"
              + (f" · {CHULETA_HTML.name} = {CHULETA_MD.name}" if hoja is not None else ""))
        return
    OUT.write_text(content, encoding="utf-8")
    print(f"Escrito {OUT} — {n} items")
    if hoja is not None:
        CHULETA_HTML.write_text(hoja, encoding="utf-8")
        print(f"Escrito {CHULETA_HTML} — desde {CHULETA_MD.name}")


if __name__ == "__main__":
    main()
