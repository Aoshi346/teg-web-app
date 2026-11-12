#!/usr/bin/env python3
"""agent_registry.py — qué agente corrió, qué encontró y si sirvió. Fuera del repo, por proyecto.

    agent_registry.py add --proyecto elvion --agente nadia-chatbot-evaluator --fase 2 \
        --trigger "auditoría 8 agentes" --hallazgos 7 --aplicados 5 --nota "midió 88,6 vs 62,9"
    agent_registry.py add ... --puerta codigo --validados 5 --descartados 2   # EQ-19: tras validar la puerta
    agent_registry.py report [--proyecto elvion]     # address-rate y tasa de validados por agente
    agent_registry.py report --todos                 # comparación ENTRE proyectos

POR QUÉ EXISTE, Y POR QUÉ AQUÍ
------------------------------
Hay dos cosas distintas que se confunden todo el rato:

| Qué | Dónde | Por qué ahí |
|---|---|---|
| Lo que el agente **sabe** de este proyecto (`memory.md`, `trend.json`) | **en el repo** | Es conocimiento del proyecto: se versiona y viaja con el clon |
| Lo que el agente **hizo** (cuándo, qué encontró, si se aplicó) | **`~/.claude/registry/`** | Es telemetría. No debe ensuciar el repo, tiene que sobrevivir a un `git clean`, y **solo sirve si es comparable entre proyectos** |

El audit log (`audit-log.sh`) dice *qué tool se usó*. No dice **qué agente corrió, qué encontró y
si sirvió**. Esta es esa segunda capa, y es la que permite contestar la pregunta que de verdad
importa: *¿la plantilla se está adaptando bien, o hay que cambiarla?*

`rules/self-improvement-loop.md` ya dice que un asset asciende a canónico cuando demuestra valor en
**≥2 proyectos**. Esa regla existe y **no se puede aplicar** porque nadie lleva la cuenta. Esto es
la cuenta.

LO QUE ESTE FICHERO NO ES
-------------------------
No es una nota de calidad del agente ni un ranking de personas. El *address-rate* mide **si sus
hallazgos se aplican**, que depende tanto del agente como de quién decide. Un agente con
address-rate bajo puede estar mirando algo que aún no toca; publicarlo como nota de rendimiento es
la forma segura de que alguien empiece a inflar hallazgos fáciles.
"""
import json
import os
import sys
from collections import defaultdict
from datetime import datetime, timezone

BASE = os.path.expanduser(os.environ.get("CLAUDE_REGISTRY_DIR", "~/.claude/registry"))
UMBRAL_N = 10            # menos hallazgos juzgados que esto: la tasa es ruido, no se avisa
UMBRAL_VALIDADOS = 0.5   # por debajo, más de la mitad de lo que emite el juez no aguanta la validación


def ruta(proyecto):
    d = os.path.join(BASE, proyecto)
    os.makedirs(d, exist_ok=True)
    return os.path.join(d, "agentes.jsonl")


def arg(nombre, defecto=None):
    a = sys.argv
    return a[a.index(nombre) + 1] if nombre in a and a.index(nombre) + 1 < len(a) else defecto


def add():
    proyecto = arg("--proyecto")
    if not proyecto:
        sys.stderr.write("falta --proyecto\n")
        return 2
    fila = {
        "fecha": arg("--fecha") or datetime.now(timezone.utc).date().isoformat(),
        "proyecto": proyecto,
        "agente": arg("--agente"),
        "fase": int(arg("--fase", 0) or 0),
        "trigger": arg("--trigger", ""),
        "hallazgos": int(arg("--hallazgos", 0) or 0),
        "aplicados": int(arg("--aplicados", 0) or 0),
        "nota": arg("--nota", ""),
    }
    # EQ-19 (3.11): validados ÷ emitidos lo da el segundo agente de la puerta (rules/audit-team.md §4),
    # y la puerta permite el coste por puerta. Opcionales: una fila sin ellos significa «no se validó».
    for k in ("validados", "descartados"):
        if arg(f"--{k}") is not None:
            fila[k] = int(arg(f"--{k}") or 0)
    if arg("--puerta"):
        fila["puerta"] = arg("--puerta")
    with open(ruta(proyecto), "a", encoding="utf-8") as f:
        f.write(json.dumps(fila, ensure_ascii=False) + "\n")
    print(f"registrado: {fila['agente']} @ {proyecto} ({fila['aplicados']}/{fila['hallazgos']})")
    return 0


def leer(proyecto):
    p = ruta(proyecto)
    if not os.path.exists(p):
        return []
    return [json.loads(l) for l in open(p, encoding="utf-8") if l.strip()]


def report():
    if "--todos" in sys.argv:
        proyectos = sorted(d for d in os.listdir(BASE)) if os.path.isdir(BASE) else []
    else:
        proyectos = [arg("--proyecto") or "elvion"]

    porag = defaultdict(lambda: {"rondas": 0, "hall": 0, "apl": 0, "val": 0, "desc": 0, "proyectos": set()})
    for pr in proyectos:
        for f in leer(pr):
            k = f.get("agente") or "?"
            porag[k]["rondas"] += 1
            porag[k]["hall"] += f.get("hallazgos", 0)
            porag[k]["apl"] += f.get("aplicados", 0)
            porag[k]["val"] += f.get("validados", 0)
            porag[k]["desc"] += f.get("descartados", 0)
            porag[k]["proyectos"].add(f.get("proyecto", pr))

    if not porag:
        print("(sin rondas registradas)")
        return 0

    print(f"{'agente':32} {'rondas':>6} {'hallazgos':>10} {'aplicados':>10} {'rate':>6} {'validados':>10}  proyectos")
    recalibrar = []
    for k, v in sorted(porag.items(), key=lambda x: -x[1]["apl"]):
        rate = f"{100*v['apl']/v['hall']:.0f}%" if v["hall"] else "—"
        juzgados = v["val"] + v["desc"]
        vrate = f"{100*v['val']/juzgados:.0f}%" if juzgados else "—"
        print(f"{k:32} {v['rondas']:>6} {v['hall']:>10} {v['apl']:>10} {rate:>6} {vrate:>10}  "
              f"{','.join(sorted(v['proyectos']))}")
        if juzgados >= UMBRAL_N and v["val"] / juzgados < UMBRAL_VALIDADOS:
            recalibrar.append(f"{k} ({v['val']}/{juzgados})")
    porpuerta = defaultdict(lambda: [0, set(), 0])
    for pr in proyectos:
        for f in leer(pr):
            if f.get("puerta"):
                g = porpuerta[f["puerta"]]
                g[0] += 1
                g[1].add(f.get("agente") or "?")
                g[2] += f.get("hallazgos", 0)
    if porpuerta:
        print()
        print("Por puerta (rondas · jueces distintos · hallazgos); el coste en tokens sale de /usage u OTel:")
        for g, (n, ags, h) in sorted(porpuerta.items()):
            print(f"  {g:12} {n:>4} · {len(ags):>2} · {h:>4}")
    # EQ-19: con N suficiente, una tasa de validados baja es la señal de recalibrar o jubilar al juez.
    print()
    print(f"Validados < {UMBRAL_VALIDADOS:.0%} con ≥{UMBRAL_N} hallazgos juzgados: "
          + (", ".join(recalibrar) if recalibrar else "ninguno")
          + "  → recalibrar con fixture o jubilar (rules/audit-team.md §6)")

    # La señal que justifica el fichero: lo que aparece en 2+ proyectos deja de ser anécdota.
    multi = [k for k, v in porag.items() if len(v["proyectos"]) >= 2]
    print()
    print(f"En ≥2 proyectos ({len(multi)}): " + (", ".join(multi) if multi else "ninguno todavía"))
    print("  → self-improvement-loop.md: un asset asciende a canónico cuando demuestra valor")
    print("    en ≥2 proyectos. Esta lista es la que permite comprobarlo.")
    return 0


if __name__ == "__main__":
    cmd = sys.argv[1] if len(sys.argv) > 1 else "report"
    raise SystemExit({"add": add, "report": report}.get(cmd, report)())
