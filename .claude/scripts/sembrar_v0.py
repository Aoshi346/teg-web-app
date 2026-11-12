#!/usr/bin/env python3
"""sembrar_v0.py — deja en v0 lo MEDIDO que viajó al copiar el template a un proyecto.

POR QUÉ EXISTE. `template_diff.no_se_siembra()` dice qué no debe viajar (memorias, trend y
suggestions de agentes; catálogo, telemetría y baseline de patrones), pero solo lo aplica al
SEMBRAR con update-agent. Una copia entera del `.claude/` —lo que hace project-setup en un repo
nuevo— se lo salta, y el proyecto nace creyéndose las cifras de otro repo. Pasó en aquila-erp
(`catalog.yaml` con `project: tech-lead-template`) y se evitó a mano, con dos fallos por el camino,
en aiatech-web el 2026-09-28. A mano falla: por eso es un script.

SALVAGUARDA. Solo toca ficheros BYTE A BYTE idénticos a los del template, es decir, que siguen
siendo la copia y no la memoria del proyecto. Lo que el proyecto ya escribió no se toca nunca.
`otto-copilot/memory.md` se deja: la rellena project-setup paso 7 con el mapa del proyecto.

También copia `.specify/` si falta, SIN `sessions/` (son los planes del template).

Uso:
  python3 sembrar_v0.py <proyecto> [--template DIR] [--app NOMBRE] [--dry-run]
Salida: 0 hecho · 2 no puede medir (template ausente o igual al proyecto).
"""
import argparse
import datetime
import filecmp
import json
import os
import shutil
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from template_diff import no_se_siembra  # noqa: E402 — la frontera vive en UN sitio

HOY = datetime.date.today().isoformat()

MEM_V0 = """# Memoria de `{name}`

> Creada el {hoy} en `{app}` · **v0: sin rondas propias todavía** · fase de autonomía **1**.
> **Sin evidencia propia: NO cuenta como cobertura** (`rules/qa-loop.md` §2b).
> La definición del agente viaja del template; esta memoria NO — la del template lleva cifras y
> hallazgos de otros repos (`template_diff.py` · `no_se_siembra`).

## Contexto del proyecto — dónde está (NO se copia aquí)
- `.claude/CLAUDE.md` (sección PROYECTO) y las rules que este agente necesita.

## Lo mío — qué miro yo y qué NO
_(a rellenar en la primera ronda: qué juzgo, mi frontera con los agentes vecinos, y qué error me
sale caro)_

## Mi cola
1. Correr una primera ronda y sustituir esto por observación propia.
2. Registrarla: `python3 .claude/scripts/agent_registry.py add --proyecto {app} --agente {name} …`

## Registro de rondas
_(vacío)_
"""


def v0(rel: str, src: Path, app: str) -> str:
    """Contenido v0 del fichero `rel` (relativo a .claude/), a partir del del template."""
    name = Path(rel).name
    if name == "memory.md":
        return MEM_V0.format(name=Path(rel).parent.name, hoy=HOY, app=app)
    if name == "suggestions.jsonl" or rel == "patterns/telemetry.jsonl":
        return ""
    if name == "trend.json":
        d = json.loads(src.read_text(encoding="utf-8"))
        if "rounds" in d:
            d["rounds"] = []
        if "versions" in d:
            d["versions"] = [{"version": "v0", "date": HOY, "label": "initialization",
                              "findings": {"CRITICAL": 0, "HIGH": 0, "MEDIUM": 0, "LOW": 0},
                              "notes": f"Sembrado en {app}. Primera ronda pendiente."}]
        for k, v in (("app", app), ("last_updated", HOY)):
            if k in d:
                d[k] = v
        return json.dumps(d, ensure_ascii=False, indent=2) + "\n"
    if rel == "patterns/catalog.yaml":
        head = []
        for line in src.read_text(encoding="utf-8").splitlines():
            if not line.startswith("#"):
                break
            head.append(line)
        return "\n".join(head) + (f"\n\nproject: {app}\nmeasured: null   # se mide cuando haya código\n"
                                  "\npatterns: []\n")
    if rel.startswith("patterns/baseline/") and rel.endswith(".json"):
        pid = json.loads(src.read_text(encoding="utf-8")).get("patron_id", Path(rel).stem)
        return json.dumps({"patron_id": pid, "frozen_at": None, "frozen_by": None,
                           "nota": "Sin deuda congelada todavía. Solo un humano amplía esta lista.",
                           "migradas": [], "violations": []}, ensure_ascii=False, indent=2) + "\n"
    if rel.startswith("patterns/") and rel.endswith(".md"):
        return (f"# {Path(rel).stem} · sin medir en {app}\n\nPatrón medido en el template, no aquí. "
                "Se mide cuando haya código (`pattern-gate`).\n")
    return ""


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("proyecto")
    ap.add_argument("--template", default=os.environ.get("TL_TEMPLATE_DIR")
                    or str(Path(__file__).resolve().parents[2]))
    ap.add_argument("--app", help="nombre del proyecto (default: nombre de la carpeta)")
    ap.add_argument("--dry-run", action="store_true")
    a = ap.parse_args()

    proy, tpl = Path(a.proyecto).resolve(), Path(a.template).resolve()
    cp, ct = proy / ".claude", tpl / ".claude"
    if not ct.is_dir() or not cp.is_dir():
        print(f"✗ falta .claude/ en {'template ' + str(tpl) if not ct.is_dir() else 'proyecto ' + str(proy)}"
              " — pasa --template o TL_TEMPLATE_DIR", file=sys.stderr)
        return 2
    if proy == tpl:
        print("✗ template y proyecto son el mismo directorio: no hay nada que resembrar.", file=sys.stderr)
        return 2
    app = a.app or proy.name

    hechos, propios = [], []
    for f in sorted(cp.rglob("*")):
        if not f.is_file() or "__pycache__" in f.parts:
            continue
        rel = f.relative_to(cp).as_posix()
        if not no_se_siembra(rel) or rel == "agents/otto-copilot/memory.md":
            continue
        src = ct / rel
        if not src.is_file() or not filecmp.cmp(f, src, shallow=False):
            propios.append(rel)          # ya es del proyecto: no se toca
            continue
        nuevo = v0(rel, src, app)
        if nuevo == f.read_text(encoding="utf-8"):
            continue                     # el del template ya era v0 (p. ej. personas/_example)
        hechos.append(rel)
        if not a.dry_run:
            f.write_text(nuevo, encoding="utf-8")

    spec = []
    if not (proy / ".specify").exists() and (tpl / ".specify").is_dir():
        spec.append(".specify/ (sin sessions/)")
        if not a.dry_run:
            shutil.copytree(tpl / ".specify", proy / ".specify",
                            ignore=lambda d, n: [x for x in n if Path(d).name == "sessions"])
            (proy / ".specify" / "sessions").mkdir(exist_ok=True)
            (proy / ".specify" / "sessions" / ".gitkeep").touch()

    modo = "(dry-run) " if a.dry_run else ""
    print(f"{modo}sembrar_v0 · {app}: {len(hechos)} ficheros a v0 · {len(propios)} ya propios (intactos)"
          + (f" · copiado {spec[0]}" if spec else ""))
    por_tipo = {}
    for r in hechos:
        k = Path(r).name if r.startswith("agents/") else r.split("/")[1] if r.count("/") > 1 else r
        por_tipo[k] = por_tipo.get(k, 0) + 1
    for k, n in sorted(por_tipo.items()):
        print(f"   {n:3d} × {k}")
    print("   otto-copilot/memory.md: NO se toca — la rellena project-setup paso 7.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
