#!/usr/bin/env python3
"""gate_auditor.py — ¿esta puerta tuvo un auditor que no era quien hizo el trabajo, dentro de los topes?

POR QUÉ (EQ-1, EQ-D8, EQ-D13; sub-ola 3.11). «Siempre un auditor detrás» era una frase: los auditores se
lanzaban cuando alguien se acordaba, fitapp lanzó 11 jueces dos veces mezclando la puerta de código y la
de UI, y el qa-loop no validaba hallazgo a hallazgo. Este gate lee el ACTA de una puerta (`acta.json`, la
deja el orquestador al cerrarla) y sale ≠ 0 si el principio no se cumplió. Lo exige el cierre de
`/qa-loop` y lo pide `rules/audit-team.md` §1 a todo cierre de wave o sub-ola.

QUÉ COMPRUEBA (cada regla, su id en la salida):
  A1  hay ≥1 auditor y ninguno es el autor (quien revisa no es quien hizo)
  A2  cada auditor tiene su informe en disco y no está vacío (el artefacto, y que contenga algo)
  A3  ≤5 jueces en la puerta y ≤3 con navegador, salvo `hito_release: true` (EQ-D8)
  A4  ≤3 rondas; desde la 2ª, `alcance: "diff"` (re-revisión solo de lo cambiado), salvo hito de release
  A5  en las puertas `codigo` y `ui`, cada hallazgo P0/P1 está validado (`confirmado` o `descartado`) por
      un validador que no es el juez que lo emitió (EQ-D13)
  A6  veredicto declarado (`pass` | `fail` | `blocked`); `pass` con un P0 confirmado abierto es contradicción

SALIDA. 0 = la puerta cumple · 1 = no cumple (lista de reglas rotas) · 2 = no se pudo leer el acta (no es
«cumple»: se arregla el acta). `--ejemplo` imprime un acta mínima válida. `--json` para otro agente.

LÍMITE HONESTO. Comprueba que el acta es coherente y que los informes existen; no que el auditor mirase
bien ni que el autor declarado sea el real (eso lo da el registro del harness: `agent_registry.py`).
"""
import argparse
import json
import os
import sys

GATES = ("plan", "codigo", "ui", "cierre", "produccion")
VERDICTS = ("pass", "fail", "blocked")
VALIDATIONS = ("confirmado", "descartado")
MAX_JUDGES, MAX_BROWSER, MAX_ROUNDS = 5, 3, 3

EXAMPLE = {
    "puerta": "ui",
    "objeto": "a1b2c3d (build congelado)",
    "autor": "sesion-principal",
    "hito_release": False,
    "rondas": [{"n": 1, "alcance": "completo"}, {"n": 2, "alcance": "diff"}],
    "auditores": [
        {"agente": "vera-art-director", "navegador": True,
         "informe": ".docs/feedback/qa-loop/W4/iter-2/vera/REPORT.md"},
        {"agente": "lidia-naive-tester", "navegador": True,
         "informe": ".docs/feedback/qa-loop/W4/iter-2/lidia/REPORT.md"},
    ],
    "hallazgos": [
        {"id": "F-3", "juez": "vera-art-director", "severidad": "P1",
         "validacion": "confirmado", "validador": "verificador-limpio",
         "evidencia": "frontend/src/Card.tsx:42 + captura 390px"},
    ],
    "veredicto": "pass",
}


def check(acta: dict, base: str):
    errs = []
    gate = acta.get("puerta")
    if gate not in GATES:
        errs.append(("A0", f"`puerta` debe ser una de {', '.join(GATES)} (es {gate!r})"))
    author = (acta.get("autor") or "").strip()
    if not author:
        errs.append(("A1", "falta `autor`: sin saber quién hizo el trabajo no se puede comprobar que revisó otro"))
    auditors = acta.get("auditores") or []
    if not auditors:
        errs.append(("A1", "ningún auditor: la puerta se cerró sin que nadie revisara"))
    release = bool(acta.get("hito_release"))
    names = []
    for a in auditors:
        name = (a.get("agente") or "").strip()
        names.append(name)
        if author and name == author:
            errs.append(("A1", f"«{name}» revisa su propio trabajo"))
        rep = a.get("informe") or ""
        p = rep if os.path.isabs(rep) else os.path.join(base, rep)
        if not rep:
            errs.append(("A2", f"«{name}» sin `informe`"))
        elif not os.path.isfile(p):
            errs.append(("A2", f"el informe de «{name}» no existe: {rep}"))
        elif os.path.getsize(p) < 200:
            errs.append(("A2", f"el informe de «{name}» está casi vacío ({os.path.getsize(p)} B): ¿es un esqueleto?"))
    if not release:
        if len(auditors) > MAX_JUDGES:
            errs.append(("A3", f"{len(auditors)} jueces en una puerta (tope {MAX_JUDGES}; la batería completa, "
                               "solo con `hito_release: true`)"))
        nb = sum(1 for a in auditors if a.get("navegador"))
        if nb > MAX_BROWSER:
            errs.append(("A3", f"{nb} jueces con navegador a la vez (tope {MAX_BROWSER}, por RAM)"))
    rounds = acta.get("rondas") or []
    if not release:
        if len(rounds) > MAX_ROUNDS:
            errs.append(("A4", f"{len(rounds)} rondas (tope {MAX_ROUNDS}): perseguir cada hallazgo lleva a "
                               "sobreingeniería; escala al Usuario"))
        for r in rounds[1:]:
            if r.get("alcance") != "diff":
                errs.append(("A4", f"la ronda {r.get('n', '?')} no es solo sobre el diff (`alcance: \"diff\"`)"))
    open_p0 = False
    for h in acta.get("hallazgos") or []:
        sev, hid = h.get("severidad"), h.get("id", "?")
        if gate in ("codigo", "ui") and sev in ("P0", "P1"):
            v = h.get("validacion")
            if v not in VALIDATIONS:
                errs.append(("A5", f"{hid} ({sev}) sin validar: un segundo agente lo confirma o lo tumba"))
            elif not h.get("validador") or h.get("validador") == h.get("juez"):
                errs.append(("A5", f"{hid}: lo valida el mismo juez que lo emitió"))
            elif v == "confirmado" and not (h.get("evidencia") or "").strip():
                errs.append(("A5", f"{hid} confirmado sin `evidencia` propia del validador (file:line, DOM, salida)"))
        if sev == "P0" and h.get("validacion") != "descartado" and not h.get("cerrado"):
            open_p0 = True
    verdict = acta.get("veredicto")
    if verdict not in VERDICTS:
        errs.append(("A6", f"`veredicto` debe ser {' | '.join(VERDICTS)} (es {verdict!r})"))
    elif verdict == "pass" and open_p0:
        errs.append(("A6", "`pass` con un P0 sin descartar ni cerrar"))
    return errs, names


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("acta", nargs="?", help="ruta al acta.json de la puerta")
    ap.add_argument("--base", help="raíz contra la que se resuelven los informes (por defecto, el proyecto)")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--ejemplo", action="store_true", help="imprime un acta mínima válida")
    a = ap.parse_args()
    if a.ejemplo:
        print(json.dumps(EXAMPLE, ensure_ascii=False, indent=2))
        return 0
    if not a.acta:
        ap.error("falta la ruta del acta (o --ejemplo)")
    try:
        acta = json.load(open(a.acta, encoding="utf-8"))
        if not isinstance(acta, dict):
            raise ValueError("el acta no es un objeto JSON")
    except (OSError, ValueError) as exc:
        print(f"NO SE PUDO LEER el acta {a.acta}: {exc}", file=sys.stderr)
        return 2
    base = a.base or os.environ.get("CLAUDE_PROJECT_DIR") or os.getcwd()
    errs, names = check(acta, base)
    if a.json:
        print(json.dumps({"ok": not errs, "puerta": acta.get("puerta"), "auditores": names,
                          "errores": [{"regla": r, "que": m} for r, m in errs]}, ensure_ascii=False, indent=2))
    elif errs:
        print(f"✗ La puerta «{acta.get('puerta')}» NO cumple «quien revisa no es quien hizo»:")
        for r, m in errs:
            print(f"  {r}  {m}")
        print("Detalle: .claude/rules/audit-team.md")
    else:
        print(f"✓ Puerta «{acta.get('puerta')}»: {len(names)} auditor(es) distintos del autor, dentro de los topes"
              f"{' (hito de release)' if acta.get('hito_release') else ''}.")
    return 1 if errs else 0


if __name__ == "__main__":
    sys.exit(main())
