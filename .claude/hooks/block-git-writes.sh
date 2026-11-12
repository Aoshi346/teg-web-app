#!/usr/bin/env bash
# block-git-writes.sh — PreToolUse (matcher «Bash»). OPCIONAL: no viene registrado; se registra en
# los proyectos donde commitea el Usuario (AN-7, cosechado de EvoPreven). Lee `git_commit` y
# `git_merge` de .claude/CONFIGURACION.yaml: con la política de la casa (agente) no bloquea nada.
# La lógica y su self-test: scripts/block_git_writes.py. Exit 2 = bloquea (1 no bloquea: así estuvo
# meses sin hacer nada en EvoPreven).
#
# Registro en .claude/settings.json → hooks.PreToolUse (el matcher es el NOMBRE de la tool, no un
# patrón de permisos):
#   {"matcher": "Bash", "hooks": [{"type": "command",
#     "command": "bash \"$CLAUDE_PROJECT_DIR/.claude/hooks/block-git-writes.sh\""}]}
set -uo pipefail
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
INPUT="$(cat)"
if ! command -v python3 >/dev/null 2>&1; then
  # Sin python: red ancha solo si el proyecto declara que commitea el Usuario.
  CONF="${CLAUDE_PROJECT_DIR:-.}/.claude/CONFIGURACION.yaml"
  if [ -f "$CONF" ] && grep -qE '^[[:space:]]*git_commit:[[:space:]]*"?usuario' "$CONF" \
     && printf '%s' "$INPUT" | grep -qE '\bgit\b[^&|;]*\b(push|commit|merge)\b|\bgh[[:space:]]+pr[[:space:]]+(create|merge)\b'; then
    echo "BLOQUEADO: en este proyecto commitea el Usuario (sin python3 para afinar)." >&2
    exit 2
  fi
  exit 0
fi
printf '%s' "$INPUT" | python3 "$HERE/../scripts/block_git_writes.py"
