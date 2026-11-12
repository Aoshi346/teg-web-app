#!/usr/bin/env python3
"""governance_mode.py — el modo de autonomía que se aplica YA y se puede deshacer (escritor y juez).

POR QUÉ (AN-19, cosechado de risk-couple). `settings.json` se lee al arrancar la sesión y
`settings_profile.py --perfil` nunca recorta el `deny` (probar «observador» deja el proyecto sin
poder escribir hasta deshacerlo a mano). Hace falta un modo que valga en la sesión en curso y que se
quite con la misma facilidad con que se pone: un fichero de estado que el hook lee en CADA tool call.

    .claude/governance-mode.json   lo escribe este script, lo lee hooks/governance-gate.sh → efecto YA
    .claude/settings.json          NO se toca aquí (la de origen llamaba a settings_profile.py, y eso
                                   es justo lo irreversible); los permisos siguen en settings_profile.py

Modos (los nombres y el sentido, los de `settings_profile.py`; el freno es más estrecho, solo Bash):
  observador  frena todo comando con efecto: git add/commit/checkout/reset…, instalar, docker,
              manage.py, pytest, mkdir/cp/mv/tee/sed -i
  asistido    frena git add/commit, instalar dependencias y docker compose up/down
  estandar    no frena nada aquí (lo de fuera de la máquina ya está en el `deny`)
Un modo con `expira` pasado deja de frenar y lo dice.

Uso:
    governance_mode.py --estado
    governance_mode.py --modo asistido --razon "reviso yo cada commit" [--expira 2026-11-02T08:00]
    governance_mode.py --quitar                    # borra el estado: vuelve a mandar settings.json
    governance_mode.py --juzgar  < evento.json     # lo llama el hook; exit 2 = frena
    governance_mode.py --self-test
"""
from __future__ import annotations

import argparse
import json
import os
import re
import sys
import tempfile
from datetime import datetime

MODES = {
    "observador": r"^\s*(git\s+(add|commit|checkout|switch|restore|reset|rm|mv|merge|rebase|stash)"
                  r"|npm\s+(i|install|ci|run)|pip3?\s+install|poetry\s+(add|install)|uv\s+(add|pip)"
                  r"|docker|python3?\s+manage\.py|pytest|mkdir|touch|cp|mv|rm|tee|sed\s+-i)\b",
    "asistido": r"^\s*(git\s+(add|commit)|npm\s+(i|install|ci)|pip3?\s+install|poetry\s+add|uv\s+add"
                r"|docker\s+compose\s+(up|down))\b",
    "estandar": None,
}
SPLIT = re.compile(r"&&|\|\||;|\||\n|\$\(")


def state_path(root: str) -> str:
    return os.path.join(root, ".claude", "governance-mode.json")


def read_state(root: str) -> dict:
    try:
        with open(state_path(root), encoding="utf-8") as f:
            return json.load(f)
    except (OSError, ValueError):
        return {}


def expired(d: dict) -> bool:
    exp = d.get("expira")
    if not exp:
        return False
    try:
        return datetime.fromisoformat(exp) < datetime.now()
    except ValueError:
        return False


def judge(root: str, event: dict) -> tuple[int, str]:
    d = read_state(root)
    mode = d.get("modo")
    if not mode or expired(d) or event.get("tool_name") != "Bash":
        return 0, ""
    pat = MODES.get(mode)
    cmd = (event.get("tool_input") or {}).get("command", "")
    if not pat or not cmd:
        return 0, ""
    # Cada trozo de la cadena por separado: «cd x && git commit» también es un commit.
    hit = next((p.strip() for p in SPLIT.split(cmd) if re.search(pat, p)), None)
    if not hit:
        return 0, ""
    return 2, (f"BLOQUEADO por el modo de gobernanza «{mode}» (desde {d.get('aplicado', '?')}).\n"
               f"Razón registrada: {d.get('razon', 'sin razón registrada')}\n"
               f"Comando frenado: {hit[:160]}\n"
               "Para seguir: pídeselo al Usuario, o que él cambie el modo:\n"
               "  python3 .claude/scripts/governance_mode.py --modo estandar --razon \"<por qué>\"")


def apply(root: str, mode: str, reason: str, expires: str | None) -> int:
    if mode not in MODES:
        print(f"✗ modo desconocido: {mode}. Válidos: {', '.join(MODES)}", file=sys.stderr)
        return 1
    if not reason.strip():
        print("✗ la razón es obligatoria: un modo sin razón no se puede auditar después", file=sys.stderr)
        return 1
    if expires:
        try:
            datetime.fromisoformat(expires)
        except ValueError:
            print(f"✗ --expira no es una fecha ISO: {expires}", file=sys.stderr)
            return 1
    prev = read_state(root)
    hist = prev.get("historial", [])[-19:]
    if prev.get("modo"):
        hist.append({"modo": prev["modo"], "desde": prev.get("aplicado"), "razon": prev.get("razon")})
    d = {"_doc": "Estado VIVO del modo de autonomía; lo lee hooks/governance-gate.sh en cada tool call. "
                 "Escritor único: scripts/governance_mode.py.",
         "modo": mode, "razon": reason, "aplicado": datetime.now().isoformat(timespec="seconds"),
         "expira": expires, "historial": hist}
    os.makedirs(os.path.dirname(state_path(root)), exist_ok=True)
    with open(state_path(root), "w", encoding="utf-8") as f:
        json.dump(d, f, ensure_ascii=False, indent=2)
    print(f"✓ {state_path(root)} → {mode} (efecto en la próxima tool call si el hook está registrado)")
    return 0


def self_test() -> int:
    root = tempfile.mkdtemp()
    ev = lambda c: {"tool_name": "Bash", "tool_input": {"command": c}}  # noqa: E731
    cases = [("sin estado, commit", None, "git commit -m x", 0)]
    cases += [("observador, ls", "observador", "ls -la", 0),
              ("observador, cd && git commit", "observador", "cd a && git commit -m x", 2),
              ("observador, pytest", "observador", "pytest apps/x", 2),
              ("asistido, git status", "asistido", "git status", 0),
              ("asistido, git add", "asistido", "git add a.py", 2),
              ("asistido, pytest", "asistido", "pytest apps/x", 0),
              ("estandar, git commit", "estandar", "git commit -m x", 0)]
    failures = 0
    for name, mode, cmd, expected in cases:
        if mode:
            apply(root, mode, "prueba", None)
        rc, _ = judge(root, ev(cmd))
        failures += rc != expected
        print(f"  {'✓' if rc == expected else '✗'} {name}: {rc} (esperado {expected})")
    apply(root, "observador", "prueba", "2000-01-01T00:00")
    rc, _ = judge(root, ev("git commit -m x"))
    failures += rc != 0
    print(f"  {'✓' if rc == 0 else '✗'} observador caducado no frena: {rc}")
    os.remove(state_path(root))
    rc, _ = judge(root, ev("git commit -m x"))
    failures += rc != 0
    print(f"  {'✓' if rc == 0 else '✗'} --quitar devuelve el mando a settings.json: {rc}")
    print("self-test:", "OK" if not failures else f"{failures} FALLO(S)")
    return 1 if failures else 0


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--modo")
    ap.add_argument("--razon", default="")
    ap.add_argument("--expira")
    ap.add_argument("--estado", action="store_true")
    ap.add_argument("--quitar", action="store_true")
    ap.add_argument("--juzgar", action="store_true")
    ap.add_argument("--self-test", action="store_true")
    ap.add_argument("--root", default=os.environ.get("CLAUDE_PROJECT_DIR") or os.getcwd())
    a = ap.parse_args()
    if a.self_test:
        return self_test()
    if a.juzgar:
        try:
            event = json.loads(sys.stdin.read() or "{}")
        except ValueError:
            return 0
        rc, msg = judge(a.root, event)
        if msg:
            print(msg, file=sys.stderr)
        return rc
    if a.quitar:
        try:
            os.remove(state_path(a.root))
            print("✓ modo quitado: vuelve a mandar settings.json")
        except FileNotFoundError:
            print("· no había modo declarado")
        return 0
    if a.modo:
        return apply(a.root, a.modo, a.razon, a.expira)
    d = read_state(a.root)
    if not d.get("modo"):
        print("sin declarar: manda settings.json")
    else:
        print(f"{d['modo']} · desde {d.get('aplicado', '?')} · «{d.get('razon', '')}»"
              + (" · CADUCADO, no frena" if expired(d) else ""))
    return 0


if __name__ == "__main__":
    sys.exit(main())
