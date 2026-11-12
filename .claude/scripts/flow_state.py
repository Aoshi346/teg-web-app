#!/usr/bin/env python3
"""¿Se está siguiendo el flujo? — el estado se DERIVA del disco, no se declara.

POR QUÉ EXISTE. Petición literal del Usuario (2026-09-12): *«me tienes que DEMOSTRAR que se sigue
ese flujo […] que me asegures de que de verdad todo se está cumpliendo»*. Hasta hoy no había forma:
los 7 gates de `rules/plan-gates.md` eran prosa, `spec_lint.py` y `task_progress.py --gate` estaban
sin cablear, y la pestaña que iba a enseñarlo (`flujo.html`) no la generaba nadie.

LA SEPARACIÓN QUE LO HACE HONESTO — tres ficheros y no dos:

  .docs/flow/flow.json      MANIFIESTO. Qué se exige. Escrito a mano. **NO tiene campo «cumple»**:
                            si lo tuviera, sería una casilla que alguien marca, que es justo lo
                            que esto existe para evitar.
  .docs/flow/state.json     DERIVADO del disco y de git. No se edita: `--check` lo caza.
  .docs/flow/waivers.jsonl  Lo que el Usuario decidió saltarse, con razón, alcance y CADUCIDAD.

EL GATE NUNCA LEE `state.json`. Recalcula siempre. Si leyera el estado en vez de medir, sería «un
lector sin emisor» — el fallo que `rules/verification.md` documenta con `uso.py`, que leía una
telemetría que escribía un hook no instalado y contestaba siempre «sin datos».

TRES DESENLACES, NUNCA DOS: cumple · no_cumple · **no_medible**, y el tercero jamás cuenta como
verde. Exit: 0 cumple · 1 violación · 2 no se pudo medir · 3 sin manifiesto.

    python3 .claude/scripts/flow_state.py --init      # materializa el manifiesto
    python3 .claude/scripts/flow_state.py             # informe legible
    python3 .claude/scripts/flow_state.py --write     # reescribe state.json (para el HTML)
    python3 .claude/scripts/flow_state.py --check     # exit 1 si state.json no refleja el disco
    python3 .claude/scripts/flow_state.py --gate      # el veredicto
    python3 .claude/scripts/flow_state.py --verify-waivers
"""
from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import pathlib
import subprocess
import sys

CUMPLE, NO_CUMPLE, NO_MEDIBLE, WAIVED = "cumple", "no_cumple", "no_medible", "waived"
RAZON_MIN = 40
RAZON_VACIA = {"ok", "no aplica", "luego", "-", "n/a", "na", "ya está", "sin razón"}

MANIFIESTO = {
    "version": 1,
    "_doc": ("MANIFIESTO: declara QUÉ se exige. NO declara si se cumple — eso lo deriva "
             "flow_state.py del disco y de git. Si añades aquí un campo de estado, lo has "
             "convertido en una casilla que alguien marca."),
    "umbrales": {"waiver_dias_max": 30, "timeout_gate_s": 60},
    "gates": [
        {"id": "G-ARRANQUE", "fase": "arranque", "bloqueante": True,
         "titulo": "Los documentos base están, y no son la plantilla",
         "prueba": {"tipo": "comando", "cmd": ["python3", ".claude/scripts/gate_arranque.py", "."],
                    "exit_ok": 0, "exit_no_medible": [2, 3, 127]}},
        {"id": "G-WAVE", "fase": "ejecucion", "bloqueante": True,
         "titulo": "Ninguna wave se cierra con casillas abiertas",
         "prueba": {"tipo": "comando_glob", "glob": ".specify/sessions/*/tasks.md",
                    "cmd": ["python3", ".claude/scripts/task_progress.py", "{}", "--gate"],
                    "exit_ok": 0, "exit_no_medible": [2, 127]}},
        {"id": "G-SPEC", "fase": "ejecucion", "bloqueante": False,
         "titulo": "La spec tiene verbo normativo y criterios de aceptación",
         "prueba": {"tipo": "comando_glob", "glob": ".specify/sessions/*/spec.md",
                    "cmd": ["python3", ".claude/scripts/spec_lint.py", "{dir}"],
                    "exit_ok": 0, "exit_no_medible": [2, 127]}},
        {"id": "G-MECANISMOS", "fase": "cierre", "bloqueante": False,
         "titulo": "Ningún mecanismo declarado está roto",
         "prueba": {"tipo": "comando", "cmd": ["python3", ".claude/scripts/check_mechanisms.py"],
                    "exit_ok": 0, "exit_no_medible": [2, 127]}},
        {"id": "G-CORE", "fase": "cierre", "bloqueante": False,
         "titulo": "El índice del core refleja el disco",
         "prueba": {"tipo": "comando", "cmd": ["python3", ".claude/scripts/gen_core.py", "--check"],
                    "exit_ok": 0, "exit_no_medible": [2, 127]}},
    ],
}


def _sh(cmd: list[str], cwd: pathlib.Path, timeout: int):
    """Ejecuta y devuelve (exit, salida). stdout y stderr SEPARADOS y ninguno a /dev/null:
    mandar stderr a la nada colapsa «no hay dato» con «el chequeo se rompió»."""
    try:
        p = subprocess.run(cmd, cwd=cwd, capture_output=True, text=True, timeout=timeout)
        return p.returncode, (p.stdout or "") + (p.stderr or "")
    except FileNotFoundError as e:
        return 127, f"no existe el binario: {e}"
    except subprocess.TimeoutExpired:
        return 124, f"timeout tras {timeout}s"
    except OSError as e:
        return 126, f"no se pudo ejecutar: {e}"


def _waivers(raiz: pathlib.Path, dias_max: int):
    """Lee waivers.jsonl y devuelve {gate_id: waiver} solo con los VÁLIDOS y EN VIGOR."""
    f = raiz / ".docs" / "flow" / "waivers.jsonl"
    vivos, avisos, prev = {}, [], None
    if not f.exists():
        return vivos, avisos
    hoy = dt.date.today()
    for n, linea in enumerate(f.read_text(encoding="utf-8").splitlines(), 1):
        linea = linea.strip()
        if not linea:
            continue
        try:
            w = json.loads(linea)
        except json.JSONDecodeError:
            avisos.append(f"línea {n}: no es JSON válido"); continue
        # La cadena de hashes: borrar una línea de en medio la rompe y se nota.
        if prev is not None and w.get("prev") != prev:
            avisos.append(f"línea {n}: eslabón perdido — alguien borró o reordenó waivers")
        prev = w.get("h")

        razon = (w.get("razon") or "").strip()
        if len(razon) < RAZON_MIN or razon.lower() in RAZON_VACIA:
            avisos.append(f"línea {n} ({w.get('gate')}): razón insuficiente "
                          f"({len(razon)} caracteres, mínimo {RAZON_MIN})"); continue
        alcance = w.get("alcance")
        if not alcance or alcance == "*":
            avisos.append(f"línea {n} ({w.get('gate')}): sin alcance o alcance '*' — "
                          "no existe el waiver global"); continue
        try:
            caduca = dt.date.fromisoformat(w.get("caduca", ""))
        except ValueError:
            avisos.append(f"línea {n} ({w.get('gate')}): sin fecha de caducidad válida"); continue
        if caduca < hoy:
            avisos.append(f"línea {n} ({w.get('gate')}): CADUCÓ el {caduca} — vuelve a bloquear")
            continue
        if (caduca - hoy).days > dias_max:
            avisos.append(f"línea {n} ({w.get('gate')}): caduca en {(caduca - hoy).days} días, "
                          f"máximo {dias_max}"); continue
        if not (w.get("quien") or "").strip():
            avisos.append(f"línea {n} ({w.get('gate')}): sin `quien`"); continue
        w["dias_restantes"] = (caduca - hoy).days
        vivos[w.get("gate")] = w
    return vivos, avisos


def evalua(raiz: pathlib.Path) -> dict:
    man_f = raiz / ".docs" / "flow" / "flow.json"
    if not man_f.exists():
        return {"veredicto": "sin_manifiesto", "exit": 3,
                "por_que": f"no existe {man_f.relative_to(raiz)} — y eso NO significa que se "
                           "cumpla: significa que no hay nada declarado que comprobar. "
                           "Créalo con: flow_state.py --init"}
    try:
        man = json.loads(man_f.read_text(encoding="utf-8"))
    except json.JSONDecodeError as e:
        return {"veredicto": "sin_manifiesto", "exit": 3,
                "por_que": f"flow.json no es JSON válido: {e.msg} (línea {e.lineno})"}

    umb = man.get("umbrales", {})
    timeout = int(umb.get("timeout_gate_s", 60))
    vivos, avisos_w = _waivers(raiz, int(umb.get("waiver_dias_max", 30)))

    res, peor = [], CUMPLE
    for g in man.get("gates", []):
        gid, pr = g["id"], g.get("prueba", {})
        r = {"id": gid, "fase": g.get("fase"), "titulo": g.get("titulo"),
             "bloqueante": bool(g.get("bloqueante"))}

        if gid in vivos:
            w = vivos[gid]
            res.append({**r, "estado": WAIVED, "por_que": w["razon"],
                        "waiver": {k: w.get(k) for k in
                                   ("quien", "caduca", "alcance", "dias_restantes")}})
            continue

        objetivos = ["."]
        if pr.get("tipo") == "comando_glob":
            objetivos = sorted(str(p) for p in raiz.glob(pr["glob"]))
            if not objetivos:
                res.append({**r, "estado": NO_MEDIBLE,
                            "por_que": f"no hay ningún {pr['glob']} — nada que medir, "
                                       "y eso no es un aprobado"})
                if peor == CUMPLE:
                    peor = NO_MEDIBLE
                continue

        peor_g, detalles = CUMPLE, []
        for obj in objetivos:
            cmd = [c.replace("{}", obj).replace("{dir}", str(pathlib.Path(obj).parent))
                   for c in pr["cmd"]]
            rc, out = _sh(cmd, raiz, timeout)
            est = (CUMPLE if rc == pr.get("exit_ok", 0)
                   else NO_MEDIBLE if rc in pr.get("exit_no_medible", []) else NO_CUMPLE)
            detalles.append({"cmd": " ".join(cmd), "exit": rc, "estado": est,
                             "salida": "\n".join(out.strip().splitlines()[:12])})
            if est == NO_CUMPLE:
                peor_g = NO_CUMPLE
            elif est == NO_MEDIBLE and peor_g == CUMPLE:
                peor_g = NO_MEDIBLE
        res.append({**r, "estado": peor_g, "detalles": detalles})
        if peor_g == NO_CUMPLE and g.get("bloqueante"):
            peor = NO_CUMPLE
        elif peor_g == NO_CUMPLE and peor == CUMPLE:
            peor = NO_CUMPLE
        elif peor_g == NO_MEDIBLE and peor == CUMPLE:
            peor = NO_MEDIBLE

    # Un no_medible NUNCA puede dar veredicto verde, aunque no haya ni una violación.
    code = {CUMPLE: 0, NO_CUMPLE: 1, NO_MEDIBLE: 2}[peor]
    cuenta = {}
    for r in res:
        cuenta[r["estado"]] = cuenta.get(r["estado"], 0) + 1
    rama = _sh(["git", "rev-parse", "--abbrev-ref", "HEAD"], raiz, 10)
    sha = _sh(["git", "rev-parse", "--short", "HEAD"], raiz, 10)
    return {
        "_doc": "DERIVADO. No editar: lo reescribe flow_state.py y --check caza la edición a mano.",
        "generado": dt.datetime.now().astimezone().isoformat(timespec="seconds"),
        "generador": "flow_state.py@1",
        "manifiesto_sha": "sha256:" + hashlib.sha256(man_f.read_bytes()).hexdigest()[:16],
        "repo": {"rama": rama[1].strip() if rama[0] == 0 else "?",
                 "sha": sha[1].strip() if sha[0] == 0 else "?"},
        "veredicto": peor, "exit": code, "resumen": cuenta,
        "gates": res,
        "waivers_avisos": avisos_w,
        "limites": [
            "Comprueba FORMA, no corrección: un documento impecable y lleno de disparates pasa.",
            "Un waiver lo puede escribir el agente: dentro de una sesión nada distingue quién "
            "escribió un fichero. Lo que lo acota es que caduca, lleva nombre y queda en el diff.",
        ],
    }


def _huella(est: dict) -> str:
    """Lo que se compara en --check: el veredicto y el estado de cada gate, sin timestamps."""
    base = {"veredicto": est.get("veredicto"),
            "gates": {g["id"]: g["estado"] for g in est.get("gates", [])}}
    return hashlib.sha256(json.dumps(base, sort_keys=True).encode()).hexdigest()


def main() -> int:
    ap = argparse.ArgumentParser(description="Estado derivado del flujo")
    ap.add_argument("proyecto", nargs="?", default=".")
    ap.add_argument("--init", action="store_true")
    ap.add_argument("--write", action="store_true")
    ap.add_argument("--check", action="store_true")
    ap.add_argument("--gate", action="store_true")
    ap.add_argument("--verify-waivers", dest="vw", action="store_true")
    ap.add_argument("--json", dest="as_json", action="store_true")
    a = ap.parse_args()
    raiz = pathlib.Path(a.proyecto).resolve()
    d = raiz / ".docs" / "flow"

    if a.init:
        d.mkdir(parents=True, exist_ok=True)
        f = d / "flow.json"
        if f.exists():
            print(f"· ya existe {f.relative_to(raiz)} — no se toca"); return 0
        man = dict(MANIFIESTO, proyecto=raiz.name)
        f.write_text(json.dumps(man, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        print(f"✓ {f.relative_to(raiz)} — {len(man['gates'])} gates declarados\n"
              "  Adáptalo: un repo de configuración no tiene los mismos gates que un producto.")
        return 0

    est = evalua(raiz)
    if est.get("veredicto") == "sin_manifiesto":
        sys.stderr.write(f"FLUJO · exit 3 — {est['por_que']}\n")
        return 3

    if a.vw:
        av = est["waivers_avisos"]
        print("\n".join("  ⚠ " + x for x in av) if av else "  ✓ waivers coherentes")
        return 1 if av else 0

    if a.write:
        d.mkdir(parents=True, exist_ok=True)
        est_w = dict(est, huella=_huella(est))
        (d / "state.json").write_text(json.dumps(est_w, ensure_ascii=False, indent=2) + "\n",
                                      encoding="utf-8")
        print(f"✓ .docs/flow/state.json — veredicto: {est['veredicto']}")
        return est["exit"]

    if a.check:
        # DOS comprobaciones distintas, y hacen falta las dos. La primera versión solo hacía la
        # segunda, y el sabotaje S-F2 la tumbó: se editaba `veredicto` y `gates[].estado` a mano
        # dejando `huella` intacta, la medición real no había cambiado, las huellas coincidían y
        # --check decía «✓ refleja el disco». Un chequeo que no comprueba lo que dice comprobar es
        # peor que no tenerlo: da verde con el signo bueno (`rules/verification.md`).
        #   INTEGRIDAD — ¿el contenido del fichero cuadra con su propia huella? → edición a mano
        #   FRESCURA   — ¿esa huella es la de la medición de ahora?            → tablero desfasado
        f = d / "state.json"
        if not f.exists():
            sys.stderr.write("--check: no existe state.json. Genéralo con --write.\n"); return 1
        try:
            viejo = json.loads(f.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            sys.stderr.write("--check: state.json no es JSON válido\n"); return 1
        if viejo.get("huella") != _huella(viejo):
            sys.stderr.write("--check: state.json ESTÁ MANIPULADO — su contenido no cuadra con su "
                             "propia huella. Alguien editó el veredicto o el estado de un gate a "
                             "mano. Se regenera con --write; no se edita.\n"); return 1
        if viejo.get("huella") != _huella(est):
            sys.stderr.write("--check: state.json está DESFASADO — el proyecto cambió desde que se "
                             "generó. Regenéralo con --write y mira el diff.\n"); return 1
        print("✓ state.json refleja el disco"); return 0

    if a.as_json:
        print(json.dumps(est, ensure_ascii=False, indent=2)); return est["exit"]

    ic = {CUMPLE: "✓", NO_CUMPLE: "✗", NO_MEDIBLE: "?", WAIVED: "⊘"}
    sal = sys.stderr if est["exit"] else sys.stdout
    print(f"FLUJO · {raiz.name} · rama {est['repo']['rama']} ({est['repo']['sha']})", file=sal)
    for g in est["gates"]:
        print(f"\n  {ic[g['estado']]} {g['id']:14} {g['titulo']}", file=sal)
        if g["estado"] == WAIVED:
            w = g["waiver"]
            print(f"      saltado por {w['quien']} · caduca en {w['dias_restantes']} días "
                  f"· alcance {w['alcance']}\n      razón: {g['por_que']}", file=sal)
        elif g.get("por_que"):
            print(f"      {g['por_que']}", file=sal)
        for det in g.get("detalles", []):
            if det["estado"] != CUMPLE:
                print(f"      $ {det['cmd']}  → exit {det['exit']}", file=sal)
                for l in det["salida"].splitlines()[:4]:
                    print(f"        {l}", file=sal)
    for x in est["waivers_avisos"]:
        print(f"\n  ⚠ waiver: {x}", file=sal)
    print(f"\n  {est['resumen']} · veredicto: {est['veredicto']}", file=sal)
    if est["exit"] == 2:
        print("  exit 2 — hay comprobaciones que NO SE PUDIERON HACER. No es un aprobado.", file=sal)
    return est["exit"]


if __name__ == "__main__":
    sys.exit(main())
