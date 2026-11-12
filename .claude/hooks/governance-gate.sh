#!/usr/bin/env bash
# governance-gate.sh — PreToolUse (matcher «Bash»). OPCIONAL: no viene registrado, porque un freno
# en PreToolUse cambia todas las sesiones del proyecto y eso lo decide el Usuario (AN-19, cosechado
# de risk-couple). Hace efectivo YA el modo de `.claude/governance-mode.json`; sin ese fichero, calla.
# Escritor y lógica: scripts/governance_mode.py (--modo, --quitar, --estado, --self-test).
# Exit 2 y motivo por stderr: con exit 1 la llamada sigue, y el stdout de un bloqueo se descarta.
#
# Registro: {"matcher": "Bash", "hooks": [{"type": "command",
#   "command": "bash \"$CLAUDE_PROJECT_DIR/.claude/hooks/governance-gate.sh\""}]}
set -uo pipefail
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT="${CLAUDE_PROJECT_DIR:-$(cd "$HERE/../.." && pwd)}"
[ -f "$ROOT/.claude/governance-mode.json" ] || { cat >/dev/null; exit 0; }
command -v python3 >/dev/null 2>&1 || { cat >/dev/null; exit 0; }
python3 "$HERE/../scripts/governance_mode.py" --juzgar --root "$ROOT"
