#!/usr/bin/env bash
# aviso-claude-md.sh — PostToolUse. systemMessage al editar un CLAUDE.md (no rige hasta /clear).
# Envoltorio de .claude/scripts/eventos_harness.py aviso-claude-md (cabecera de ese script = límites honestos).
# Sub-ola 2.11 (CL-24/CL-30/CL-39). Falla ABIERTO a propósito: un hook de visibilidad nunca rompe un turno.
F="${CLAUDE_PROJECT_DIR:-.}/.claude/scripts/eventos_harness.py"
[ -f "$F" ] || exit 0   # sin el script, falla abierto (un exit 2 bloquearía la compactación)
exec python3 "$F" aviso-claude-md
