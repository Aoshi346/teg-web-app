#!/usr/bin/env python3
"""check_skills_codex.py — ¿ve Codex las skills que creemos que ve?

MEDIDO el 2026-09-19 con codex-cli 0.128.0: **Codex descarta EN SILENCIO toda skill cuya
`description` pase de 1.024 caracteres** (el límite del estándar abierto de Agent Skills). Ni
error ni aviso: simplemente no aparece. Tres skills de diseño recién escritas eran invisibles
para Codex y visibles para Claude Code, y la única forma de saberlo fue preguntarle a Codex qué
skills tenía. 11 de las 71 del template estaban así.

Comprueba dos cosas, las dos sin gastar un token:
  1. Toda skill servida a Codex (`.agents/skills/*`) tiene `description` ≤ 1.024.
  2. Cada enlace de `.agents/skills/` resuelve a un `SKILL.md` real (un enlace roto también
     desaparece en silencio).

Con `--todas` revisa además todas las de `.claude/skills/`, estén servidas a Codex o no: sirve
para saber cuáles romperían el día que se sirvan.

Desenlaces:  0 todo visible · 1 hay skills que Codex no verá · 2 no se pudo medir
"""
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[2]
LIMITE = 1024


def description(skill_md: Path):
    t = skill_md.read_text(errors="ignore")
    if not t.startswith("---"):
        return None
    try:
        import yaml
        return (yaml.safe_load(t.split("---")[1]) or {}).get("description", "") or ""
    except Exception:
        return None


def main() -> int:
    servidas = RAIZ / ".agents" / "skills"
    fuente = RAIZ / ".claude" / "skills"
    if not fuente.exists():
        print(f"⛔ NO SE PUDO MEDIR: no existe {fuente}", file=sys.stderr)
        return 2
    try:
        import yaml  # noqa: F401
    except ImportError:
        print("⛔ NO SE PUDO MEDIR: falta PyYAML", file=sys.stderr)
        return 2

    fallos = []
    objetivo = sorted(servidas.iterdir()) if servidas.exists() else []
    if "--todas" in sys.argv:
        objetivo = sorted(p for p in fuente.iterdir() if (p / "SKILL.md").exists())

    for p in objetivo:
        md = p / "SKILL.md"
        if not md.exists():
            fallos.append(f"{p.name}: el enlace no resuelve a un SKILL.md — Codex no la verá")
            continue
        d = description(md)
        if d is None:
            fallos.append(f"{p.name}: frontmatter ilegible — Codex no la verá")
        elif len(d) > LIMITE:
            fallos.append(f"{p.name}: description de {len(d)} caracteres (límite {LIMITE}) — "
                          f"Codex la DESCARTA sin avisar")

    ambito = "todas las de .claude/skills" if "--todas" in sys.argv else "las servidas en .agents/skills"
    print(f"check_skills_codex · {len(objetivo)} skills ({ambito})")
    for f in fallos:
        print(f"  ✗ {f}")
    if not fallos:
        print("  ✓ todas visibles para Codex")
    return 1 if fallos else 0


if __name__ == "__main__":
    sys.exit(main())
