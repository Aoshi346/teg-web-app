#!/usr/bin/env bash
# task-completed-gate.sh — TaskCompleted. Gate de waves: una tarea «Wave N» no se cierra con casillas abiertas (exit 2).
# Envoltorio de .claude/scripts/eventos_harness.py task-completed (cabecera de ese script = límites honestos).
# Sub-ola 2.11 (CL-24/CL-30/CL-39). Falla ABIERTO a propósito: un hook de visibilidad nunca rompe un turno.
F="${CLAUDE_PROJECT_DIR:-.}/.claude/scripts/eventos_harness.py"
[ -f "$F" ] || exit 0   # sin el script, falla abierto: no bloquea todas las tareas
exec python3 "$F" task-completed
