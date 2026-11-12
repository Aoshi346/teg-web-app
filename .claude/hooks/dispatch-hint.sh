#!/bin/bash
# dispatch-hint.sh — UserPromptSubmit hook: el DESPACHADOR del harness.
#
# POR QUÉ EXISTE
#   El template tenía las piezas y no tenía despachador: al tocar frontend, nadie le decía al
#   agente que existen `disenar-pantalla`, Vera, Aitor o el plugin `frontend-design`. No es que
#   los ignorara — es que en ese momento no sabía que estaban. Este hook inyecta la fila de
#   AGENT-SYSTEM.md que corresponde al dominio del prompt.
#
#   Es la aplicación de rules/layer-decision.md a sí mismo: el Gate 0 de Otto llevaba meses
#   escrito en prosa de CLAUDE.md y por tanto era ignorable. Un hook no lo es.
#
# LOS DOS GUARDARRAÍLES (un hook ruidoso acaba desactivado — agent-security.md ASI09):
#   1. UNA vez por dominio y sesión. No repite.
#   2. Silencio por defecto: si no reconoce el dominio con confianza, no dice nada.
#
# La detección NO vive aquí: vive en gen_agent_system.py --detect, para tener un solo sitio
# que mantener. Este script es solo el cableado.
#
# Desactivar: quitar el bloque UserPromptSubmit de settings.json, o exportar TL_NO_DISPATCH=1.

[ -n "$TL_NO_DISPATCH" ] && exit 0

INPUT=$(cat)
DIR="${CLAUDE_PROJECT_DIR:-$(pwd)}"
GEN="$DIR/.claude/scripts/gen_agent_system.py"
[ -f "$GEN" ] || exit 0

PROMPT=$(printf '%s' "$INPUT" | jq -r '.prompt // empty' 2>/dev/null)
[ -z "$PROMPT" ] && exit 0

# Prompts muy cortos no llevan dominio fiable; no molestamos.
[ "${#PROMPT}" -lt 15 ] && exit 0

SESSION=$(printf '%s' "$INPUT" | jq -r '.session_id // "nosession"' 2>/dev/null)
FICHA=$(python3 "$GEN" --detect "$PROMPT" 2>/dev/null) || exit 0
[ -z "$FICHA" ] && exit 0

# Guardarraíl 1: una vez por (sesión, dominio)
DOMINIO=$(printf '%s' "$FICHA" | head -1 | cut -c1-60 | tr -cd '[:alnum:]')
MARCA="${TMPDIR:-/tmp}/.tl-dispatch-${SESSION}-${DOMINIO}"
[ -f "$MARCA" ] && exit 0
touch "$MARCA" 2>/dev/null

echo "🧭 Dónde estás y qué tienes (de .claude/AGENT-SYSTEM.md — no es obligatorio, es lo que HAY):"
echo ""
printf '%s\n' "$FICHA"

# Gate 0 de plan-gates.md: tarea grande → Otto deja de ser prosa y aparece aquí.
if printf '%s' "$PROMPT" | grep -qiE 'refactor|feature|módulo nuevo|modulo nuevo|arquitectur|migra|rediseñ|reescrib|plan |planifica|speckit'; then
  echo ""
  echo "> ⚠️ Esto pinta a **tarea grande** → \`rules/plan-gates.md\`: primero Gate 0b (enumera lo que"
  echo ">    te falta saber y pregúntalo) y **Gate 0: corre la skill \`/otto\`** antes de comprometer"
  echo ">    el plan. Otto sugiere la jugada de harness; no ejecuta nada."
fi
exit 0
