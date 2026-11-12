#!/usr/bin/env python3
"""inherit_agent_memory.py — un proyecto nuevo hereda, de solo lectura, la memoria de los agentes de otro.

De dónde sale (AN-12, sub-ola 3.14 de la revisión integral). Un proyecto derivado heredó a mano 9.697
líneas de memoria de 8 agentes de otros dos, en `agents/<x>/herencia/<origen>-memory.md`: la idea
(lo heredado aparte, sin mezclarlo con lo propio) era buena, pero entró sin podar: ficheros de 1.000 y
2.400 líneas que el agente no puede leer enteros. Convención: `rules/memory.md` §3b.

Qué hace: por cada agente que existe en los DOS proyectos y tiene `memory.md` en el origen, copia esa
memoria a `<destino>/.claude/agents/<x>/herencia/<origen>-memory.md` con una cabecera (origen, fecha,
solo lectura). **Se niega** a copiar una memoria de más de `--max-lines` (300): se consolida antes en
el origen (`auto-dream-memory` §B), porque heredar sin podar es heredar el problema.

    python3 .claude/scripts/inherit_agent_memory.py <origen> <destino>            # simulacro
    python3 .claude/scripts/inherit_agent_memory.py <origen> <destino> --apply    # escribe
    python3 .claude/scripts/inherit_agent_memory.py <origen> <destino> --agents vera-art-director
    python3 .claude/scripts/inherit_agent_memory.py --self-test

Salida: 0 todo copiable (o copiado) · 1 alguna memoria pasa del tope (no se copia ninguna) ·
2 ruta sin `.claude/agents/` o nada que heredar. Nunca sobrescribe un `herencia/` que ya exista.

Límites honestos: no limpia datos de cliente (lo heredado es del mismo dueño y se queda en ese
proyecto, no sube al template) ni decide qué lecciones valen: copia lo ya consolidado.
"""
from __future__ import annotations

import argparse
import datetime as dt
import sys
import tempfile
from pathlib import Path

DEFAULT_MAX_LINES = 300

HEADER = """> 🧳 **Herencia de solo lectura** — memoria de `{agent}` en el proyecto `{origin}`, copiada el
> {date}. No se edita: lo que aprendas aquí va a `../memory.md`. Se lee cuando el caso se parece
> (grep por tema), no entera en cada lanzamiento. Convención: `rules/memory.md` §3b.

"""


def plan(origin: Path, dest: Path, agents: list[str] | None, max_lines: int):
    """Lista de (agente, fuente, destino, líneas, ok)."""
    rows = []
    for src in sorted((origin / ".claude" / "agents").glob("*/memory.md")):
        agent = src.parent.name
        if agents and agent not in agents:
            continue
        if not (dest / ".claude" / "agents" / agent).is_dir() and \
                not (dest / ".claude" / "agents" / f"{agent}.md").is_file():
            continue
        n = len(src.read_text(encoding="utf-8", errors="replace").splitlines())
        target = dest / ".claude" / "agents" / agent / "herencia" / f"{origin.name}-memory.md"
        rows.append((agent, src, target, n, n <= max_lines))
    return rows


def run(origin: Path, dest: Path, agents: list[str] | None, max_lines: int, apply: bool) -> int:
    for p in (origin, dest):
        if not (p / ".claude" / "agents").is_dir():
            print(f"⚠️  {p}: no hay .claude/agents/", file=sys.stderr)
            return 2
    rows = plan(origin, dest, agents, max_lines)
    if not rows:
        print("Nada que heredar: ningún agente con memoria está en los dos proyectos.")
        return 2
    too_long = [r for r in rows if not r[4]]
    for agent, _src, target, n, ok in rows:
        state = "existe, no se toca" if target.exists() else ("copiable" if ok else "PASA DEL TOPE")
        print(f"  {'✅' if ok else '❌'} {agent}: {n} líneas → {target.relative_to(dest)} ({state})")
    if too_long:
        print(f"❌ {len(too_long)} memoria(s) de más de {max_lines} líneas: consolídalas en el origen "
              "(auto-dream-memory §B) y repite. No se ha copiado nada.")
        return 1
    if not apply:
        print("Simulacro: añade --apply para escribir.")
        return 0
    today = dt.date.today().isoformat()
    written = 0
    for agent, src, target, _n, _ok in rows:
        if target.exists():
            continue
        written += 1
        target.parent.mkdir(parents=True, exist_ok=True)
        body = src.read_text(encoding="utf-8", errors="replace")
        target.write_text(HEADER.format(agent=agent, origin=src.parents[3].name, date=today) + body,
                          encoding="utf-8")
    print(f"✅ Heredadas {written} memoria(s); {len(rows) - written} ya estaban.")
    return 0


def self_test() -> int:
    ok = True
    with tempfile.TemporaryDirectory() as tmp:
        o, d = Path(tmp) / "origen", Path(tmp) / "destino"
        (o / ".claude/agents/vera").mkdir(parents=True)
        (o / ".claude/agents/solo-origen").mkdir(parents=True)
        (d / ".claude/agents/vera").mkdir(parents=True)
        (o / ".claude/agents/vera/memory.md").write_text("x\n" * (DEFAULT_MAX_LINES + 1))
        (o / ".claude/agents/solo-origen/memory.md").write_text("y\n")
        rc = run(o, d, None, DEFAULT_MAX_LINES, apply=True)
        target = d / ".claude/agents/vera/herencia/origen-memory.md"
        case = rc == 1 and not target.exists()
        print(f"{'✅' if case else '❌'} memoria de más de {DEFAULT_MAX_LINES} → se niega y no copia")
        ok &= case
        (o / ".claude/agents/vera/memory.md").write_text("lección\n")
        rc = run(o, d, None, DEFAULT_MAX_LINES, apply=True)
        text = target.read_text() if target.exists() else ""
        case = rc == 0 and "solo lectura" in text and text.endswith("lección\n")
        case &= not (d / ".claude/agents/solo-origen").exists()
        print(f"{'✅' if case else '❌'} podada → copia con cabecera, solo agentes de los dos lados")
        ok &= case
        target.write_text("propio\n")
        run(o, d, None, DEFAULT_MAX_LINES, apply=True)
        case = target.read_text() == "propio\n"
        print(f"{'✅' if case else '❌'} un herencia/ que ya existe no se sobrescribe")
        ok &= case
    return 0 if ok else 1


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("origin", nargs="?", type=Path)
    ap.add_argument("dest", nargs="?", type=Path)
    ap.add_argument("--agents", nargs="*", help="solo estos agentes")
    ap.add_argument("--max-lines", type=int, default=DEFAULT_MAX_LINES)
    ap.add_argument("--apply", action="store_true")
    ap.add_argument("--self-test", action="store_true")
    a = ap.parse_args()
    if a.self_test:
        return self_test()
    if not (a.origin and a.dest):
        ap.error("hacen falta <origen> y <destino>")
    return run(a.origin.resolve(), a.dest.resolve(), a.agents, a.max_lines, a.apply)


if __name__ == "__main__":
    sys.exit(main())
