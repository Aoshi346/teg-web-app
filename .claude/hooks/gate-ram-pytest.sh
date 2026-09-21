#!/usr/bin/env bash
# ══════════════════════════════════════════════════════════════════════════════════════════════
# gate-ram-pytest.sh — hace que `check-ram.sh` dispare de verdad antes de CADA pytest.
#
# POR QUÉ EXISTE (medido el 2026-09-05, .claude/smoke/README.md § matcher). En Claude Code 2.1.261
# un hook con `"matcher": "Bash(pytest*)"` NO casa nunca: los matchers de hooks son regex sobre el
# NOMBRE de la tool («Bash», «Write|Edit»); la sintaxis `Tool(patrón)` es de permissions, no de
# hooks. El bloque heredado (y el del template) llevaba sin disparar desde que se escribió — lo que
# protegía la RAM era la regla de correr `bash .claude/hooks/check-ram.sh` a mano. Verde por
# casualidad, no por mecanismo (CLAUDE.md §7).
#
# QUÉ HACE: con matcher `Bash`, lee tool_input.command y, SOLO si es un pytest, llama al
# `check-ram.sh` canónico (verbatim del template, no se toca) y traduce su exit 1 a exit 2, que es el
# único que bloquea en un PreToolUse (el 1 es «error no bloqueante»: el pytest habría seguido).
# Cualquier otro comando: exit 0 en milisegundos.
#
# MODOS: (stdin JSON PreToolUse) · --cmd "<comando>" (smoke). GATE_RAM_TRACE=<fichero> deja marca
# de que check-ram llegó a correr (para el smoke, que no puede depender de cuánta RAM haya).
# ══════════════════════════════════════════════════════════════════════════════════════════════
set -uo pipefail
if [ "${1:-}" = "--cmd" ]; then
  CMD="${2:-}"; INPUT=""
else
  command -v jq >/dev/null 2>&1 || exit 0
  INPUT=$(cat)
  CMD=$(printf '%s' "$INPUT" | jq -r '.tool_input.command // empty' 2>/dev/null)
fi
[ -n "$CMD" ] || exit 0
printf '%s' "$CMD" | grep -qE '(^|[;&|[:space:]])(pytest|py\.test)([[:space:]]|$)|python3?[[:space:]]+-m[[:space:]]+pytest' || exit 0
[ -n "${GATE_RAM_TRACE:-}" ] && : > "$GATE_RAM_TRACE"
DIR="${CLAUDE_PROJECT_DIR:-$(git rev-parse --show-toplevel 2>/dev/null || pwd)}"
[ -x "$DIR/.claude/hooks/check-ram.sh" ] || { echo "gate-ram-pytest: falta check-ram.sh — RAM NO medida" >&2; exit 0; }
printf '%s' "$INPUT" | bash "$DIR/.claude/hooks/check-ram.sh"
RC=$?
# check-ram.sh sale con 1 cuando bloquea (así viene del template, verbatim). Para un hook PreToolUse
# solo el exit 2 bloquea: el 1 es «error no bloqueante» y el pytest seguiría adelante. Aquí se traduce.
[ $RC -ne 0 ] && exit 2
exit 0
