#!/usr/bin/env bash
# hint-affected-tests.sh — PostToolUse (matcher «Write|Edit|MultiEdit»). OPCIONAL, NO bloquea (AN-19,
# cosechado de cold_calling_coach). Tras tocar el backend de una app Django, recuerda qué módulo de
# pytest correr antes de DONE. Si bloqueara, se aprendería a saltárselo.
#
# La versión de origen leía `$CLAUDE_TOOL_FILE`, que Claude Code no pone: no avisó nunca (elvion #17).
# Aquí: `tool_input.file_path` de stdin, y el aviso como `additionalContext` (en PostToolUse el stdout
# suelto no le llega al modelo).
# Registro: {"matcher": "Write|Edit|MultiEdit", "hooks": [{"type": "command",
#   "command": "bash \"$CLAUDE_PROJECT_DIR/.claude/hooks/hint-affected-tests.sh\""}]}
set -uo pipefail
INPUT="$(cat)"
case "$INPUT" in *apps/*) ;; *) exit 0 ;; esac
command -v python3 >/dev/null 2>&1 || exit 0
printf '%s' "$INPUT" | python3 -c '
import json, re, sys
try:
    f = (json.loads(sys.stdin.read() or "{}").get("tool_input") or {}).get("file_path", "")
except ValueError:
    sys.exit(0)
m = re.search(r"(.*?\bapps/([^/]+))/(models|serializers|services|views|tasks|signals|selectors)\.py$", f)
if not m:
    sys.exit(0)
app = m.group(2)
msg = (f"Tocaste apps/{app}: antes de DONE, bash .claude/hooks/check-ram.sh && "
       f"pytest apps/{app}/ -q --maxfail=3 (por módulo, nunca la suite entera).")
print(json.dumps({"hookSpecificOutput": {"hookEventName": "PostToolUse", "additionalContext": msg}},
                 ensure_ascii=False))
'
exit 0
