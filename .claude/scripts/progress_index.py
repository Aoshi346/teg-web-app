#!/usr/bin/env python3
"""progress_index.py — un PROGRESS.json por plan, y el de la raíz como ÍNDICE DERIVADO.

    python3 .claude/scripts/progress_index.py            # regenera PROGRESS.json (raíz)
    python3 .claude/scripts/progress_index.py --check    # exit 1 si el índice no cuadra con el disco
    python3 .claude/scripts/progress_index.py --dry-run  # enseña lo que escribiría

EL PROBLEMA QUE RESUELVE
------------------------
`PROGRESS.json` se diseñó como fuente única de estado para el Supervisor, y la idea sigue siendo
buena. Lo que caducó es suponer que hay UNA sesión. Con una de desarrollo y otra de marketing
abiertas a la vez, las dos escriben el mismo fichero y **la segunda gana en silencio** — no hay
bloqueo de escritura (`rules/parallelization.md` §P2). Ocurrió: el historial de git de un repo real lleva
tareas de planes sin relación entre sí, y un día el fichero declaraba "plan de marketing
completed" mientras la sesión viva auditaba con ocho agentes.

EL DISEÑO
---------
    .docs/plans/<plan>/PROGRESS.json   ← UN escritor: la sesión dueña de ese plan
    PROGRESS.json  (raíz)              ← ÍNDICE DERIVADO. Se regenera, NUNCA se escribe a mano.

Tres propiedades, y si se rompe una volvemos al mismo sitio una capa más arriba:

1. **Un fichero por escritor.** El directorio del plan *es* el dueño. Nadie escribe en el de otro.
2. **El índice se regenera.** Un índice escrito a mano empieza a mentir en el primer commit —
   mismo principio que `gen_core.py --check` y `render_nav.py --all`.
3. **El contrato del Supervisor no cambia.** La raíz sigue teniendo `.task`, `.status` y
   `.checklist`, que es lo único que leen los hooks (`validate-progress.sh`, `otto-briefing.sh`,
   `pre-commit-check.sh`). Solo que ahora agregan en vez de competir.

MIGRACIÓN
---------
Si la raíz tiene todavía un PROGRESS.json "de sesión" (con su propio checklist) y no hay ningún
plan con el suyo, el script **no lo pisa**: avisa y sale. Primero se mueve a su plan.
"""
import json
import os
import sys
from datetime import datetime, timezone

PLANS = ".docs/plans"
SESIONES = ".specify/sessions"
ROOT = "PROGRESS.json"


def leer(p):
    try:
        with open(p, encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return None


def avance(d):
    ch = d.get("checklist") or []
    return sum(1 for i in ch if i.get("done")), len(ch)


def recoger():
    """Un registro por unidad de trabajo con su propio PROGRESS.json.

    Unidad = un plan de `.docs/plans/` **o** una sesión SpecKit de `.specify/sessions/`. Son las
    dos formas que tiene el trabajo aquí, y las dos tienen un dueño único; lo que importa no es
    dónde vive el fichero, es que **solo lo escriba una sesión**.
    """
    out = []
    for base, etiqueta in ((PLANS, "plan"), (SESIONES, "speckit")):
        if not os.path.isdir(base):
            continue
        for nombre in sorted(os.listdir(base)):
            if nombre.startswith("_"):
                continue
            p = os.path.join(base, nombre, "PROGRESS.json")
            d = leer(p)
            if not d:
                continue
            hecho, total = avance(d)
            out.append({
                "plan": nombre,
                "tipo": etiqueta,
                "ruta": p,
                "task": d.get("task", ""),
                "status": d.get("status", "unknown"),
                "hecho": hecho,
                "total": total,
                "escritor": d.get("escritor"),
                "startedAt": d.get("startedAt"),
                "completedAt": d.get("completedAt"),
                "updatedAt": datetime.fromtimestamp(os.path.getmtime(p), timezone.utc)
                                     .isoformat(timespec="seconds"),
            })
    return out


def construir(planes):
    vivos = [p for p in planes if p["status"] not in ("completed", "done", "cancelled")]
    # El `task` de la raíz describe el conjunto: quien lea solo esa línea tiene que enterarse
    # de que hay varios frentes, no creerse que hay uno.
    if not planes:
        task, status = "sin planes con PROGRESS.json", "unknown"
    elif len(vivos) == 1:
        task, status = f"{vivos[0]['plan']}: {vivos[0]['task']}", vivos[0]["status"]
    elif vivos:
        task = f"{len(vivos)} planes en curso: " + " · ".join(p["plan"] for p in vivos)
        status = "in_progress"
    else:
        task, status = f"{len(planes)} planes, todos cerrados", "completed"

    avisos = []
    if len(vivos) > 1:
        avisos.append(
            f"{len(vivos)} planes en curso a la vez. Cada uno escribe SU PROGRESS.json; "
            "si dos tocan el mismo módulo, declara los ficheros de cada frente "
            "(rules/parallelization.md §file claims).")
    for p in planes:
        if p["total"] == 0:
            avisos.append(f"{p['plan']}: PROGRESS.json sin checklist — no se puede medir avance.")

    return {
        "_generado": "AUTOMÁTICO por .claude/scripts/progress_index.py — NO editar a mano.",
        "_fuente": f"{PLANS}/<plan>/PROGRESS.json (un escritor por fichero)",
        "task": task,
        "status": status,
        "checklist": [
            {"id": i + 1,
             "item": f"[{p['plan']}] {p['task'] or '(sin task)'} — {p['hecho']}/{p['total']}",
             "done": p["status"] in ("completed", "done")}
            for i, p in enumerate(planes)
        ],
        "planes": planes,
        "avisos": avisos,
        "generadoAt": datetime.now(timezone.utc).isoformat(timespec="seconds"),
    }


def main():
    args = sys.argv[1:]
    planes = recoger()

    actual = leer(ROOT)
    # Protección de migración: no pisamos un PROGRESS.json de sesión que nadie ha movido aún.
    if actual and "_generado" not in actual and not planes:
        sys.stderr.write(
            "AVISO: la raíz tiene un PROGRESS.json de sesión y ningún plan tiene el suyo.\n"
            "       No lo piso. Muévelo primero a .docs/plans/<su-plan>/PROGRESS.json.\n")
        return 1

    nuevo = construir(planes)

    if "--dry-run" in args:
        print(json.dumps(nuevo, ensure_ascii=False, indent=2))
        return 0

    if "--check" in args:
        if not actual or "_generado" not in actual:
            sys.stderr.write("PROGRESS.json de la raíz no es un índice generado.\n")
            return 1
        a = json.dumps(actual.get("planes"), sort_keys=True)
        b = json.dumps(nuevo.get("planes"), sort_keys=True)
        if a != b:
            sys.stderr.write("El índice NO refleja el disco. Regenera: progress_index.py\n")
            return 1
        print(f"OK: índice al día ({len(planes)} plan(es))")
        return 0

    with open(ROOT, "w", encoding="utf-8") as f:
        json.dump(nuevo, f, ensure_ascii=False, indent=2)
    print(f"Escrito {ROOT} — {len(planes)} plan(es), status '{nuevo['status']}'")
    for a in nuevo["avisos"]:
        print("  aviso:", a)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
