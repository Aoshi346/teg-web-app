#!/usr/bin/env bash
# warn-plans-outside-repo.sh — PostToolUse (Write|Edit). Al escribir un .md en ~/.claude/plans/ avisa
# de que vive fuera del repo y da la ruta de .docs/plans/ donde conservarlo (AN-14, sub-ola 3.18; en
# musa un research que solo vivía ahí se sobrescribió). Envoltorio de eventos_harness.py
# warn-plans-outside-repo. Falla ABIERTO: un hook de aviso nunca rompe un turno.
# Camino rápido: sin «/plans/» en la entrada, sale 0 sin arrancar python3.
F="${CLAUDE_PROJECT_DIR:-.}/.claude/scripts/eventos_harness.py"
[ -f "$F" ] || exit 0
IN=$(cat)
case "$IN" in
  *'/plans/'*) ;;
  *) exit 0 ;;
esac
printf '%s' "$IN" | python3 "$F" warn-plans-outside-repo 2>/dev/null
exit 0
