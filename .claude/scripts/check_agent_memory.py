#!/usr/bin/env python3
"""check_agent_memory.py — ¿alguna memoria de agente ha crecido de más, o lleva datos de un cliente?

De dónde sale (EQ-5 y AN-12, sub-ola 3.14 de la revisión integral). Medido el 17-10: en elvion, las
memorias de Iván, Elena y Nadia pasaban de 1.000 líneas, y un agente que «lee SIEMPRE su memoria»
gasta ~15k tokens antes de empezar; `rules/memory.md` §3 pone tope a `MEMORY.md` y a las memorias de
agente no las vigilaba nada. Y las del template eran las de un cliente con un aviso «PLANTILLA»: un
proyecto nuevo arrancaba con mediciones de otro.

Dos comprobaciones:

1. **Tamaño** (en cualquier proyecto): `agents/<x>/memory.md` y cada `agents/<x>/herencia/*.md` de
   más de 300 líneas → aviso con la orden de consolidar (`auto-dream-memory` §B, paso «memorias de
   agente»). Umbral: `--max-lines` o `TL_AGENT_MEMORY_MAX_LINES`.
2. **Datos de cliente** (`--clients`, para el template): ninguna memoria de agente del template
   puede nombrar un proyecto derivado. Los nombres salen de `packs/CONFIGURACION.yaml` (clave y
   carpeta de cada proyecto, sin las palabras genéricas) más `EXTRA_MARKERS`. En el template además
   no puede haber `herencia/`: eso es de un proyecto.

    python3 .claude/scripts/check_agent_memory.py                 # tamaño, en el proyecto actual
    python3 .claude/scripts/check_agent_memory.py --clients       # + nombres de cliente (template)
    python3 .claude/scripts/check_agent_memory.py --quiet         # calla si está todo bien (hook)
    python3 .claude/scripts/check_agent_memory.py --self-test     # casos plantados: rojo y verde

Lo llama `hooks/otto-briefing.sh` al arrancar la sesión (con `--quiet`: calla si nada pasa el tope).
Salida: 0 todo bien · 1 hay avisos · 2 no se pudo medir (no hay `.claude/agents/`).

Límites honestos: la lista de nombres es la de los proyectos que conoce el template; un cliente que
no esté en `CONFIGURACION.yaml` ni en `EXTRA_MARKERS` no se caza. Busca la palabra entera, sin
distinguir mayúsculas.
"""
from __future__ import annotations

import argparse
import os
import re
import sys
import tempfile
from pathlib import Path

DEFAULT_MAX_LINES = 300

# Nombres de cliente que no salen de CONFIGURACION.yaml: productos, tenants y dominios vistos en las
# memorias del template el 31-10.
EXTRA_MARKERS = (
    "elevaiti", "evopreven", "proxera", "lumi", "lummi", "aluminiologo", "caroni",
    "miniretoquepro", "retoquepro", "mini-retoquepro", "musa", "xera", "evo-preven",
    "montcada",
)

# Claves de issue de los trackers de cliente (EVO-2913, ELV-6): delatan al proyecto sin nombrarlo.
ISSUE_KEYS = r"(?:EVO|ELV)-\d+"

# Palabras de las carpetas de proyecto que no identifican a nadie.
GENERIC_WORDS = {
    "develop", "demo", "webs", "company", "accounting", "coach", "cold", "calling", "evo",
    "preven", "quirurgicos", "evolution", "risk", "couple",
}


def project_root() -> Path:
    return Path(os.environ.get("CLAUDE_PROJECT_DIR") or os.getcwd())


def client_markers(template: Path) -> list[str]:
    """Nombres de cliente: claves y carpetas de CONFIGURACION.yaml, partidas, sin lo genérico."""
    names = set(EXTRA_MARKERS)
    cfg = template / ".claude" / "packs" / "CONFIGURACION.yaml"
    if cfg.is_file():
        text = cfg.read_text(encoding="utf-8")
        raw = re.findall(r"^  ([a-z0-9_-]+):\s*$", text, flags=re.M)
        raw += [Path(r).name for r in re.findall(r"^\s+ruta:\s*(\S+)", text, flags=re.M)]
        for item in raw:
            names.add(item.lower())
            for part in re.split(r"[-_]", item.lower()):
                if len(part) >= 3 and part not in GENERIC_WORDS:
                    names.add(part)
    return sorted(n for n in names if n not in GENERIC_WORDS)


def memory_files(root: Path) -> list[tuple[Path, bool]]:
    """(fichero, es_herencia) de cada memoria de agente bajo .claude/agents/."""
    agents = root / ".claude" / "agents"
    out = [(p, False) for p in sorted(agents.glob("*/memory.md"))]
    out += [(p, True) for p in sorted(agents.glob("*/herencia/*.md"))]
    return out


def check(root: Path, max_lines: int, clients: bool) -> tuple[list[str], int]:
    """Devuelve (avisos, ficheros mirados). Sin .claude/agents/ → ([], -1)."""
    if not (root / ".claude" / "agents").is_dir():
        return [], -1
    files = memory_files(root)
    warnings: list[str] = []
    pattern = None
    if clients:
        markers = client_markers(root)
        alternatives = "|".join(map(re.escape, markers)) + "|" + ISSUE_KEYS
        pattern = re.compile(r"(?<![\w-])(" + alternatives + r")(?![\w-])", re.I)
    for path, inherited in files:
        rel = path.relative_to(root)
        lines = path.read_text(encoding="utf-8", errors="replace").splitlines()
        if len(lines) > max_lines:
            warnings.append(f"📏 {rel}: {len(lines)} líneas (tope {max_lines}) → consolidar "
                            "(auto-dream-memory §B, memorias de agente)")
        if clients and inherited:
            warnings.append(f"🧳 {rel}: herencia/ en el template — es de un proyecto, no de la base")
        if pattern:
            hits = [(i, m.group(1)) for i, ln in enumerate(lines, 1) for m in pattern.finditer(ln)]
            if hits:
                sample = ", ".join(f"l.{i} «{w}»" for i, w in hits[:4])
                warnings.append(f"🏷️  {rel}: {len(hits)} nombre(s) de cliente ({sample}"
                                f"{', …' if len(hits) > 4 else ''})")
    return warnings, len(files)


def self_test() -> int:
    """Rojo con los casos plantados y verde con sus gemelos limpios."""
    ok = True
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        (root / ".claude" / "packs").mkdir(parents=True)
        (root / ".claude" / "packs" / "CONFIGURACION.yaml").write_text(
            "proyectos:\n\n  acmebot:\n    ruta: /home/x/acme_tienda-demo\n", encoding="utf-8")
        a = root / ".claude" / "agents"
        (a / "largo").mkdir(parents=True)
        (a / "largo" / "memory.md").write_text("x\n" * (DEFAULT_MAX_LINES + 1), encoding="utf-8")
        (a / "cliente").mkdir()
        (a / "cliente" / "memory.md").write_text("Medido en ACME el 2026-10-01\n", encoding="utf-8")
        (a / "heredado" / "herencia").mkdir(parents=True)
        (a / "heredado" / "herencia" / "otro-memory.md").write_text("ok\n", encoding="utf-8")
        w, _ = check(root, DEFAULT_MAX_LINES, clients=True)
        expected = {"largo": "📏", "cliente": "🏷️", "heredado": "🧳"}
        for agent, icon in expected.items():
            hit = any(icon in x and f"/{agent}/" in x for x in w)
            print(f"{'✅' if hit else '❌'} caso plantado «{agent}» → {icon}")
            ok &= hit
        # Gemelos limpios: en el tope justo, «acmeista» no es «acme», sin --clients no hay herencia.
        (a / "largo" / "memory.md").write_text("x\n" * DEFAULT_MAX_LINES, encoding="utf-8")
        (a / "cliente" / "memory.md").write_text("Un tal acmeista, sin nombre de cliente\n",
                                                 encoding="utf-8")
        w, _ = check(root, DEFAULT_MAX_LINES, clients=False)
        print(f"{'✅' if not w else '❌'} gemelos limpios → sin avisos {w if w else ''}")
        ok &= not w
        w, _ = check(root, DEFAULT_MAX_LINES, clients=True)
        only_inherit = len(w) == 1 and "🧳" in w[0]
        print(f"{'✅' if only_inherit else '❌'} «acmeista» no cuenta como «acme»")
        ok &= only_inherit
    return 0 if ok else 1


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("root", nargs="?", type=Path, help="raíz del proyecto (por defecto, la actual)")
    ap.add_argument("--max-lines", type=int,
                    default=int(os.environ.get("TL_AGENT_MEMORY_MAX_LINES", DEFAULT_MAX_LINES)))
    ap.add_argument("--clients", action="store_true", help="busca nombres de cliente (template)")
    ap.add_argument("--quiet", action="store_true", help="no imprime nada si no hay avisos")
    ap.add_argument("--self-test", action="store_true")
    a = ap.parse_args()
    if a.self_test:
        return self_test()
    root = (a.root or project_root()).resolve()
    warnings, n = check(root, a.max_lines, a.clients)
    if n < 0:
        if not a.quiet:
            print(f"⚠️  {root}: no hay .claude/agents/ — no se pudo medir", file=sys.stderr)
        return 2
    if warnings:
        print(f"🧠 Memorias de agente: {len(warnings)} aviso(s) en {n} fichero(s)")
        for w in warnings:
            print(f"  {w}")
        return 1
    if not a.quiet:
        print(f"✅ Memorias de agente: {n} fichero(s), ninguno pasa de {a.max_lines} líneas"
              + (" ni nombra un cliente" if a.clients else ""))
    return 0


if __name__ == "__main__":
    sys.exit(main())
