#!/usr/bin/env bash
# ══════════════════════════════════════════════════════════════════════════════════════════════
# guarda-destructivos.sh — PreToolUse (matcher «Bash|Write|Edit|MultiEdit»). Envoltorio FALLA-CERRADO de
# scripts/guarda_destructivos.py (borrado/git destructivo · BD destructiva · servidor en 0.0.0.0 · `git add -A`
# con otra sesión viva). Política y medición: rules/agent-security.md §5 y
# _archive/2026-10-20/medicion-2.10/README.md.
#
# POR QUÉ UN ENVOLTORIO. `onFailure: "block"` solo cubre «el hook no arranca» (rc 127 o ≠ 0/2). Un hook
# cuyo detector revienta y sale 0 deja pasar todo sin decirlo (medido en la 2.09 con guard-pkill:
# sin python3 → rc 0, JSON truncado → rc 0). Aquí:
#   · el detector (python) sale 0 con su decisión (JSON `ask`, o silencio) o ≠ 0 si se rompió;
#   · si python3 no está, el detector no está o sale ≠ 0 → red ancha (grep) sobre el texto crudo:
#     si el comando casa, exit 2 (bloquea); si no casa, exit 0 (una guarda rota que bloqueara TODO se
#     acabaría quitando);
#   · si este script no llega a arrancar, `onFailure: "block"` en settings.json lo bloquea.
# MODO PRUEBA: TL_GUARDA_SABOTAJE=excepcion hace reventar al detector.
# ══════════════════════════════════════════════════════════════════════════════════════════════
AQUI="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ENTRADA="$(cat)"
# Red ancha: lo que habría que mirar si el detector no puede. Incluye lo nuevo de la 2.10.
BROAD='(rm +-[a-zA-Z]*[rR]|rm +--recursive|reset +--hard|git +clean +-[a-zA-Z]*[fdx]|push .*(-f([ "\\]|$)|--force|\+| :)|branch +(-[a-zA-Z]*D|.*--delete)|checkout +(-f|--force|-- *\.)|switch +(-f|--discard)|restore +.*\.|worktree +remove|filter-branch|reflog +expire|stash +(drop|clear)|rsync .*--del|shred|find .*-delete|migrate|flush|reset_db|sqlflush|dbshell|DROP |TRUNCATE|DELETE +FROM|dropdb|dropDatabase|down +.*-v|--volumes|volume +(rm|prune)|0\.0\.0\.0|http\.server|runserver|--host( |=)(0|::|\*)|--ip( |=)(0|::)|server\.address|-l +tcp|network_mode|--network +host|-p +[0-9]+:[0-9]+|--publish|nc +-[a-z]*l|socat|git +(add|stage) +-[a-zA-Z]*[AuHf]|git +(add|stage) +(\.|:/|\*)|commit +-[a-zA-Z]*a|commit +--all|ports:)'
SAL=""; RC=99
if command -v python3 >/dev/null 2>&1 && [ -f "$AQUI/../scripts/guarda_destructivos.py" ]; then
  SAL="$(printf '%s' "$ENTRADA" | python3 "$AQUI/../scripts/guarda_destructivos.py")"; RC=$?
  if [ "$RC" -eq 0 ]; then
    [ -n "$SAL" ] && printf '%s\n' "$SAL"
    exit 0
  fi
fi
# Detector roto, ausente o sin python3: red ancha.
if printf '%s' "$ENTRADA" | grep -Eiq "$BROAD"; then
  echo "guarda-destructivos ROTA (rc=$RC) o sin python3, y el comando casa con la red ancha: bloqueado por si acaso. Arregla la guarda (.claude/scripts/guarda_destructivos.py) o confirma a mano." >&2
  exit 2
fi
exit 0
