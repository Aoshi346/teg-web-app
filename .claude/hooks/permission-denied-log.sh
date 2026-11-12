#!/usr/bin/env bash
# permission-denied-log.sh — PermissionDenied. Registra lo que el clasificador del modo auto deniega y permite un reintento.
# Envoltorio de .claude/scripts/eventos_harness.py permission-denied (cabecera de ese script = límites honestos).
# Sub-ola 2.11 (CL-24/CL-30/CL-39). Falla ABIERTO a propósito: un hook de visibilidad nunca rompe un turno.
F="${CLAUDE_PROJECT_DIR:-.}/.claude/scripts/eventos_harness.py"
[ -f "$F" ] || exit 0   # sin el script, falla abierto (un exit 2 bloquearía la compactación)
exec python3 "$F" permission-denied
