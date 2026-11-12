#!/usr/bin/env bash
# deny-destructive-migration.sh — PreToolUse (matcher «Write|Edit|MultiEdit»). OPCIONAL: no viene
# registrado; se registra en los proyectos con migraciones (AN-19, cosechado de cold_calling_coach).
# La lógica y su self-test: scripts/deny_destructive_migration.py. Exit 2 = bloquea.
#
# Registro en .claude/settings.json → hooks.PreToolUse:
#   {"matcher": "Write|Edit|MultiEdit", "hooks": [{"type": "command",
#     "command": "bash \"$CLAUDE_PROJECT_DIR/.claude/hooks/deny-destructive-migration.sh\""}]}
set -uo pipefail
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
INPUT="$(cat)"
# Sin python no se puede reconstruir el fichero: red ancha sobre el texto crudo, solo si es migración.
if ! command -v python3 >/dev/null 2>&1; then
  if printf '%s' "$INPUT" | grep -q '/migrations/' \
     && printf '%s' "$INPUT" | grep -qE 'DeleteModel|RemoveField|DROP (TABLE|COLUMN)|TRUNCATE' \
     && ! printf '%s' "$INPUT" | grep -q 'migration-approved-by:'; then
    echo "BLOQUEADO: migración destructiva sin '# migration-approved-by:' (sin python3 para afinar)." >&2
    exit 2
  fi
  exit 0
fi
printf '%s' "$INPUT" | python3 "$HERE/../scripts/deny_destructive_migration.py"
