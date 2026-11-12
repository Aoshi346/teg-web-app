#!/usr/bin/env bash
# ══════════════════════════════════════════════════════════════════════════════════════════════
# gate-fases-diseno.sh — avisa si se escribe el esquema del backend con el mockup sin cerrar.
#
# POR QUÉ (sub-ola 3.67, UX-6): el orden de fases de rules/motores-de-diseno.md Parte F era
# prosa y en fitapp se invirtió pese a tres normas escritas. La lógica vive en
# scripts/gate_fases_diseno.py (con su --self-test); esto solo la conecta.
#
# MATCHER: `Write|Edit|MultiEdit` (regex sobre el NOMBRE de la tool); la ruta se filtra dentro.
# SOLO AVISA, por decisión del Usuario (1-11): deja pasar y le dice al modelo qué falta
# (additionalContext) y al Usuario (systemMessage). TL_FASES_DISENO=bloquear (exit 2) existe para
# medirlo, pero no se activa en ningún sitio sin una decisión nueva del Usuario.
# NO está registrado en el template (no es un producto): lo registra el proyecto con UI en su
# settings.json.
#
# MODOS: (stdin JSON PreToolUse) · --file <ruta> (para el smoke).
# ══════════════════════════════════════════════════════════════════════════════════════════════
set -uo pipefail

if [ "${1:-}" = "--file" ]; then
  FILE="${2:-}"
else
  command -v jq >/dev/null 2>&1 || exit 0
  FILE=$(cat | jq -r '.tool_input.file_path // empty' 2>/dev/null)
fi
[ -n "$FILE" ] || exit 0
case "$FILE" in *.py) ;; *) exit 0 ;; esac

DIR="${CLAUDE_PROJECT_DIR:-$(git rev-parse --show-toplevel 2>/dev/null || pwd)}"
GATE="$DIR/.claude/scripts/gate_fases_diseno.py"
if [ ! -f "$GATE" ]; then
  echo "gate-fases-diseno: falta gate_fases_diseno.py — NO se comprobó nada" >&2
  exit 0
fi

MSG=$(python3 "$GATE" "$DIR" "$FILE" 2>&1); RC=$?
[ $RC -eq 1 ] || exit 0

if [ "${TL_FASES_DISENO:-}" = "bloquear" ]; then
  echo "BLOQUEADO (gate-fases-diseno): $MSG" >&2
  exit 2
fi
MSG="$MSG" python3 -c 'import json, os
m = os.environ["MSG"]
print(json.dumps({"systemMessage": "Aviso de fases de diseño: " + m,
                  "hookSpecificOutput": {"hookEventName": "PreToolUse",
                                         "additionalContext": "AVISO (gate-fases-diseno): " + m}},
                 ensure_ascii=False))'
exit 0
