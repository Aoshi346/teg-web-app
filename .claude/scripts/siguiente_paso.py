#!/usr/bin/env python3
"""¿En qué paso estamos y qué hay que teclear ahora? — para quien NO conoce los comandos.

POR QUÉ EXISTE. Petición del Usuario (2026-09-14, T-240): el harness lo va a usar «un usuario que
no sabe los comandos, así que tendrá que guiarle y seguir siempre el proceso entero». Hasta hoy
esa guía era prosa en CLAUDE.md —advisory— y el estado del proceso solo se veía abriendo
`proceso.html`. Esto baja la guía de capa (`rules/layer-decision.md`): un hook la imprime al
arrancar cada sesión y `/siguiente` la imprime cuando se pide.

NO INVENTA NADA. Los 13 estados y su medición son los de `templates/report_kit/gen_proceso.py`
(que a su vez recalcula del disco con `gate_arranque.py`): aquí solo se traduce «el primer estado
que no está cerrado» a una frase, un comando y dónde leer más. Si no se puede medir, lo dice.

    python3 .claude/scripts/siguiente_paso.py            # ≤10 líneas, en cristiano
    python3 .claude/scripts/siguiente_paso.py --json     # para el hook o para otro agente
Exit 0 siempre: es una guía, no un gate. Los gates son gate_arranque.py y flow_state.py.
"""
from __future__ import annotations

import json
import os
import pathlib
import subprocess
import sys

ROOT = pathlib.Path(os.environ.get("CLAUDE_PROJECT_DIR") or os.getcwd()).resolve()
KIT = ROOT / ".claude" / "templates" / "report_kit"

# estado → (qué es, en una frase · el comando exacto · qué deja escrito)
GUIA = {
    "encuadre":   ("Decir en una página qué es esto, para quién y qué NO entra.",
                   "/arrancar", "arranque/00-encuadre.md"),
    "prd":        ("El documento de producto: qué problema resuelve y cómo sabremos que funcionó.",
                   "/arrancar   (fase 1 — el PRD)", "arranque/01-prd.md"),
    "requisitos": ("Cada requisito con sus 11 apartados y sus criterios Dado/Cuando/Entonces.",
                   "/arrancar   (fase 1b — los requisitos)", "arranque/02-requisitos.md"),
    "datos":      ("Las «cosas» del negocio, cómo se relacionan y el recorrido principal.",
                   "/arrancar   (fase 2 — datos y flujos)", "arranque/03-modelo-datos.md · 04-flujos.md"),
    "stack":      ("Con qué se construye, qué se compra hecho, y las decisiones caras (ADR).",
                   "/arrancar   (fase 3 — stack y ADR)", "arranque/05-stack.md · .docs/adr/"),
    "etica":      ("Qué datos personales se tratan y con qué base legal, ANTES de construir.",
                   "/arrancar   (fase 4 — ética y RGPD)", "arranque/06-etica-privacidad.md"),
    "seguridad":  ("Por dónde se entra y las defensas decididas (2FA, límite de intentos, puertos, logs).",
                   "/arrancar   (fase 4b — superficie de ataque)", "arranque/07-superficie.md"),
    "marca":      ("Identidad, paleta, tipografía y logo: los tokens de los que sale todo lo visual.",
                   "/marca", "arranque/10-identidad.md · brand.html · design-system.md"),
    "lowfi":      ("Bocetos en gris: ¿está bien organizada la pantalla? (sin color, con texto real).",
                   "/producto   (si hay ≥2 pantallas)  →  /disenar-pantalla <pantalla> --lowfi",
                   "bocetos/*lowfi*.html"),
    "highfi":     ("La pantalla con los tokens reales y sus 4 estados: con datos, vacía, cargando, error.",
                   "/disenar-pantalla <pantalla>", "bocetos/*.html"),
    "mockup":     ("La aplicación navegable con datos simulados (MSW) y los simuladores en mocks/.",
                   "/nueva-pantalla <pantalla> --mockup", "frontend + mocks/<proveedor>/panel.html"),
    "desarrollo": ("Backend, base de datos y el frontend conectado de verdad, por waves con gates.",
                   "/speckit.plan  →  /speckit.tasks  →  /speckit.implement  →  /speckit.converge",
                   "código + tests + .specify/sessions/<ID>/tasks.md"),
    "qa":         ("Los auditores (Lidia, Vera, Ignacio…) hasta nota media ≥ 9.0, con doble evidencia.",
                   "/qa-loop", ".docs/feedback/qa-loop/<wave>/"),
}


def plan_activo(raiz: pathlib.Path) -> pathlib.Path | None:
    """MISMA regla que build.py y tasks_registry.py: el plan con pending-tasks.md más reciente por
    NOMBRE; si ninguno, el que tenga report.json. Nunca el mtime."""
    planes = raiz / ".docs" / "plans"
    if not planes.is_dir():
        return None
    dirs = sorted(d for d in planes.iterdir() if d.is_dir())
    for marca in ("pending-tasks.md", "report.json"):
        con = [d for d in dirs if (d / marca).exists()]
        if con:
            return sorted(con)[-1]
    return None


def estados(raiz: pathlib.Path, plan: pathlib.Path | None) -> list[dict] | None:
    if not (KIT / "gen_proceso.py").exists():
        return None
    sys.path.insert(0, str(KIT))
    try:
        import gen_proceso as gp  # noqa: E402
    except Exception:            # pragma: no cover — el kit está a medias
        return None
    medido = gp.medir(raiz)
    out = []
    for eid, label, sub, gate, pats in gp.ESTADOS:
        arts = gp.artefactos(raiz, plan, pats) if plan else []
        # La MISMA regla que proceso.html (no se replica: se importa): páginas generadas de oficio y
        # plantillas sin rellenar no son material.
        est = medido.get(gate, "pendiente") if gate else gp.estado_sin_gate(arts)
        out.append({"id": eid, "label": label, "sub": sub, "estado": est,
                    "artefactos": sum(1 for a in arts if gp.es_material(a))})
    return out


def main() -> int:
    quiere_json = "--json" in sys.argv
    plan = plan_activo(ROOT)
    lista = estados(ROOT, plan)
    if lista is None:
        msg = "No encuentro .claude/templates/report_kit/gen_proceso.py: no puedo medir el proceso."
        print(json.dumps({"ok": False, "motivo": msg}) if quiere_json else f"siguiente-paso: {msg}")
        return 0

    cerrados = sum(1 for e in lista if e["estado"] == "cumple")
    # «Actual» = el primer estado sin cerrar y sin material. Un estado con material pero sin gate
    # (no_medible) NO es verde, pero tampoco es el siguiente: se avisa aparte.
    actual = next((e for e in lista if e["estado"] in ("pendiente", "no_cumple")), None)
    con_material = [e for e in lista if e["estado"] == "no_medible"]
    n = lista.index(actual) + 1 if actual else len(lista)

    if quiere_json:
        print(json.dumps({"ok": True, "plan": str(plan.relative_to(ROOT)) if plan else None,
                          "cerrados": cerrados, "total": len(lista),
                          "actual": actual["id"] if actual else None, "n": n,
                          "comando": GUIA[actual["id"]][1] if actual else None,
                          "estados": lista}, ensure_ascii=False))
        return 0

    manual = ROOT / ".docs" / "core" / "manual.html"
    print("🧭 Dónde estamos en el proceso (13 pasos: definir → diseñar → construir → verificar)")
    if actual is None:
        print(f"   Los {len(lista)} pasos están cerrados o con material. Lo que queda es verificar: /qa-loop.")
    else:
        que, cmd, deja = GUIA[actual["id"]]
        print(f"   Paso {n} de {len(lista)}: **{actual['label']}** — {que}")
        print(f"   ▶ Lo que hay que teclear ahora:   {cmd}")
        print(f"   Deja escrito: {deja}")
        if actual["estado"] == "no_cumple":
            print("   ⚠ Este paso tiene documentos pero el gate NO los da por buenos. "
                  "Para ver qué falta: python3 .claude/scripts/gate_arranque.py . --explica")
    if con_material:
        print("   · Con material sin verificar: " + ", ".join(e["label"] for e in con_material))
    if plan is None:
        print("   · Todavía no hay ningún plan en .docs/plans/: /arrancar lo crea.")
    else:
        print(f"   · Cerrados {cerrados}/{len(lista)} · el tablero: {plan.relative_to(ROOT)}/proceso.html"
              f"  (python3 .claude/scripts/abrir_panel.py {plan.relative_to(ROOT)})")
    if manual.exists():
        print("   · Cada paso explicado, con su comando: .docs/core/manual.html")
    print("   · Si dudas, di «/siguiente»: te lo vuelvo a explicar. No hace falta saberse los comandos.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
