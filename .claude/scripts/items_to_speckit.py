#!/usr/bin/env python3
"""items_to_speckit.py — el puente que faltaba: decisiones aprobadas → sesión SpecKit ejecutable.

EL AGUJERO QUE CIERRA. El informe recoge las decisiones del Usuario y las guarda en `report.json`.
Y ahí se quedaban: **no había nada que las convirtiera en trabajo**. El Usuario aprobaba 41 items y
el sistema no se enteraba; si no preguntaba «¿ya lo has hecho?», no se hacía nunca. Es el mismo
fallo que `sources/04-flujo-y-human-in-the-loop.md` declara — «nada comprueba que la parada se
atendió» — pero al revés: la parada se atendió y nadie recogió la respuesta.

QUÉ HACE. Lee los items con `decision: aprobar` y escribe el `tasks.md` de una sesión SpecKit,
agrupados en WAVES que respetan tres cosas:

  1. Los CHOQUES declarados (`choca:`) — dos items que tocan los mismos ficheros no van en la
     misma wave, porque `parallelization.md` §file claims dice que eso no se arregla en el merge.
  2. Las DEPENDENCIAS (`blocks:`) — lo que desbloquea a otros va antes.
  3. El RIESGO — lo reversible y sin dependencias primero, para que las waves tempranas no puedan
     dejar el tronco roto.

Y deja el puente de vuelta: cada tarea lleva su `id` del informe, así que al cerrarla se puede
marcar el item como hecho y el informe deja de mentir.

Uso:
  python3 items_to_speckit.py <plan-dir> --sesion "<ID> - <nombre>" [--dry-run]
"""
import argparse, json, os, re, sys
from collections import defaultdict, OrderedDict
from datetime import date

# El riesgo decide el orden de las waves. No es la severidad: es cuánto cuesta deshacerlo.
def riesgo(it):
    ep = it.get("epic", "")
    t = (it.get("title", "") + " " + str(it.get("desc", ""))).lower()
    if any(k in t for k in ("archivar", "borrar", "retirar", "mover")): return 2   # reversible con git
    if ep in ("CA", "EJ"):                                             return 3   # toca agents/skills
    if any(k in t for k in ("hook", "settings.json", "permiso")):      return 4   # enforcement
    return 1                                                                       # escribir algo nuevo

NOMBRE_WAVE = {
    1: "Wave 1 — escribir lo que falta (sin tocar nada existente)",
    2: "Wave 2 — archivar y ordenar (reversible con git)",
    3: "Wave 3 — cambios de capa (agents/ y skills/)",
    4: "Wave 4 — enforcement (hooks y permisos)",
}

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("plan"); ap.add_argument("--sesion", required=True)
    ap.add_argument("--dry-run", action="store_true")
    a = ap.parse_args()

    rep = json.load(open(os.path.join(a.plan, "report.json"), encoding="utf-8"))
    items = rep["items"]
    ap_items = [i for i in items if i.get("decision") == "aprobar" and i.get("status") != "done"]
    if not ap_items:
        print("  no hay items aprobados pendientes"); return 0

    # choques: si A choca con B, no pueden compartir wave
    choca = defaultdict(set)
    for i in items:
        for c in (i.get("choca") or []):
            choca[i["id"]].add(c); choca[c].add(i["id"])

    waves = OrderedDict()
    for i in sorted(ap_items, key=lambda x: (riesgo(x), x.get("severity", "P9"), x["id"])):
        r = riesgo(i)
        # si choca con alguien ya colocado en esta wave, baja a la siguiente
        while any(o["id"] in choca[i["id"]] for o in waves.get(r, [])):
            r += 1
        waves.setdefault(r, []).append(i)

    hoy = date.today().isoformat()
    out = [f"# {a.sesion}", "",
           f"> Generado por `items_to_speckit.py` desde `{os.path.basename(a.plan)}/report.json` el {hoy}.",
           f"> **{len(ap_items)} items aprobados por el Usuario.** Cada tarea lleva su `id` del informe:",
           "> al cerrarla se marca allí, para que el informe no mienta sobre lo que está hecho.", "",
           "## Setup", "",
           "- [ ] **→ NOTIFICAR:** sesión abierta desde el informe · "
           f"{len(waves)} waves · {len(ap_items)} tareas", ""]

    for r in sorted(waves):
        lote = waves[r]
        out += [f"## {NOMBRE_WAVE.get(r, f'Wave {r}')}", "",
                f"_{len(lote)} tareas · riesgo {r}/4_", ""]
        for i in lote:
            sev = i.get("severity", ""); eff = i.get("effort", "")
            out.append(f"- [ ] `{i['id']}` [{sev}/{eff}] {i['title']}")
            if i.get("goal"):
                out.append(f"  - objetivo: {i['goal']}")
            # el test es lo que permite cerrarla sin preguntar
            mt = i.get("manual_test") or {}
            if mt.get("test"):
                out.append(f"  - verificar: {mt['test']}")
            out.append(f"  - informe: item `{i['id']}` de `{os.path.basename(a.plan)}`")
        out += ["", f"- [ ] **GATE Wave {r}:** `python3 .claude/scripts/task_progress.py <tasks.md> "
                f"--gate --wave \"{NOMBRE_WAVE.get(r, f'Wave {r}')}\"`",
                "- [ ] **→ NOTIFICAR:** wave cerrada · marcar los items en el informe", ""]

    out += ["## Cierre", "",
            "- [ ] Regenerar el informe para que refleje lo hecho",
            "- [ ] **→ NOTIFICAR: READY_COMMIT** — esperar aprobación del Usuario",
            "- [ ] ⏳ **El push es una decisión APARTE** (`governance.md` §2)", ""]

    txt = "\n".join(out)
    if a.dry_run:
        print(txt[:1800] + "\n…"); return 0

    ses_dir = os.path.join(os.getcwd(), ".specify", "sessions", a.sesion)
    os.makedirs(ses_dir, exist_ok=True)
    open(os.path.join(ses_dir, "tasks.md"), "w", encoding="utf-8").write(txt)
    print(f"  OK {ses_dir}/tasks.md — {len(ap_items)} tareas en {len(waves)} waves")
    for r in sorted(waves):
        print(f"     {NOMBRE_WAVE.get(r, r)[:52]:<54} {len(waves[r])}")
    return 0

if __name__ == "__main__":
    sys.exit(main())
