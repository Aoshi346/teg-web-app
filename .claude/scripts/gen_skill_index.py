#!/usr/bin/env python3
"""Genera .claude/skills/README.md desde los frontmatter de las SKILL.md.

Uso:  python3 .claude/scripts/gen_skill_index.py [--check]
      --check: no escribe; sale 1 si el README está desfasado (para verificación).

Mantiene los contadores honestos: el índice se REGENERA, no se edita a mano.
"""
import re, sys, datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]  # .claude/
SKILLS = ROOT / "skills"
OUT = SKILLS / "README.md"

# Clasificación por prefijo/nombre (grupos de lectura, no jerarquía)
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

def frontmatter_desc(path: Path) -> str:
    text = path.read_text(encoding="utf-8", errors="replace")
    m = re.match(r"^---\n(.*?)\n---", text, re.S)
    if not m:
        return "(sin frontmatter)"
    fm = m.group(1)
    # Bloque multilinea (description: | / >): coger las líneas indentadas siguientes
    bm = re.search(r"^description:\s*[|>][+-]?\s*\n((?:[ \t]+.*\n?)+)", fm, re.M)
    if bm:
        desc = " ".join(l.strip() for l in bm.group(1).splitlines() if l.strip())
    else:
        dm = re.search(r'^description:\s*["\']?(.*?)["\']?\s*$', fm, re.M)
        desc = (dm.group(1) if dm else "(sin description)").strip().strip('"').strip("'")
    desc = re.sub(r"\s+", " ", desc)
    return desc[:160] + ("…" if len(desc) > 160 else "")

def main():
    check = "--check" in sys.argv
    skills = sorted(d for d in SKILLS.iterdir() if d.is_dir() and (d / "SKILL.md").exists())
    grouped: dict[str, list] = {g[0]: [] for g in GROUPS}
    grouped["Otros"] = []
    for d in skills:
        for label, rx in GROUPS:
            if rx.match(d.name):
                grouped[label].append(d)
                break
        else:
            grouped["Otros"].append(d)

    lines = [
        "# `.claude/skills/` — índice generado",
        "",
        f"> **{len(skills)} skills** · generado por `.claude/scripts/gen_skill_index.py` "
        f"({datetime.date.today().isoformat()}). **NO editar a mano** — regenerar.",
        "> Routing por tarea: `.claude/INDEX.md` · clase de distribución y criterios por perfil: "
        "`skills/project-setup/references/selection-criteria.md` §Catálogo de distribución.",
        "",
    ]
    for label, items in grouped.items():
        if not items:
            continue
        lines += [f"## {label} ({len(items)})", ""]
        for d in items:
            lines.append(f"- **[{d.name}]({d.name}/SKILL.md)** — {frontmatter_desc(d / 'SKILL.md')}")
        lines.append("")
    content = "\n".join(lines)

    if check:
        current = OUT.read_text(encoding="utf-8") if OUT.exists() else ""
        # Comparar sin la línea de fecha
        strip = lambda s: re.sub(r"\(\d{4}-\d{2}-\d{2}\)", "", s)
        if strip(current) != strip(content):
            print(f"DESFASADO: {OUT} no coincide con las {len(skills)} skills reales")
            sys.exit(1)
        print(f"OK: {len(skills)} skills indexadas")
        return
    OUT.write_text(content, encoding="utf-8")
    print(f"Escrito {OUT} — {len(skills)} skills")

if __name__ == "__main__":
    main()
