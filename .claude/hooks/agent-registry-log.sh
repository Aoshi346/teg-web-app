#!/usr/bin/env bash
# agent-registry-log.sh — PostToolUse[Agent|Task] (y SubagentStop) hook: deja constancia de QUÉ agente corrió.
#
# POR QUÉ EXISTE
#   `agent_registry.py` responde la pregunta que importa —¿este agente sirve para algo?— pero
#   solo si alguien lo alimenta. Y si alimentarlo depende de que el agente o el TL se acuerden,
#   se hará dos veces y luego nunca: es exactamente el caso que `rules/layer-decision.md` manda
#   bajar de capa. Lo que importa va a hook, no a prosa.
#
# QUÉ REGISTRA Y QUÉ NO — la distinción es la mitad del valor
#   ✅ Automático aquí: que el agente X corrió, cuándo y con qué disparador.
#   ❌ NO automático: cuántos hallazgos trajo y cuántos se aplicaron. Eso es CRITERIO —
#      solo una persona (o el TL al cerrar) sabe si un hallazgo se atendió o se descartó.
#      Se completa después:
#        python3 .claude/scripts/agent_registry.py add --proyecto <este-proyecto> \
#            --agente vera-art-director --fase 3 --hallazgos 8 --aplicados 2 --nota "..."
#
#   Un registro con hallazgos=0 significa "corrió y no sabemos si sirvió", NO "no encontró nada".
#   Esa ambigüedad es deliberada y preferible a inventarse un número.
#
# Registrado en settings.json como PostToolUse con matcher «Agent|Task» (en proyectos viejos, SubagentStop). Escribe FUERA del repo:
# ~/.claude/registry/<proyecto>/agentes.jsonl — el agente auditado no reescribe su propio expediente.

set -uo pipefail

PROJECT_DIR="${CLAUDE_PROJECT_DIR:-$(pwd)}"
PROJECT_SLUG="$(basename "$PROJECT_DIR")"
SCRIPT="$PROJECT_DIR/.claude/scripts/agent_registry.py"

[ -f "$SCRIPT" ] || exit 0

PAYLOAD="$(cat 2>/dev/null || true)"
[ -n "$PAYLOAD" ] || exit 0

# El nombre del agente puede venir con distintas claves según la versión del harness. Se prueban
# las conocidas y, si NINGUNA aparece, no se registra: un expediente con "unknown" es peor que
# uno que falta, porque parece cobertura.
AGENTE="$(printf '%s' "$PAYLOAD" | python3 -c '
import json, sys
try:
    d = json.load(sys.stdin)
except Exception:
    sys.exit(0)
if not isinstance(d, dict):
    sys.exit(0)
# PostToolUse[Agent|Task] (el que está registrado) lleva el nombre DENTRO de tool_input; SubagentStop
# lo lleva en la raíz. Hasta 2026-10-22 solo se miraba la raíz y el registro no escribió ni una
# entrada automática (15 líneas, todas manuales, frente a 420 llamadas Agent en audit-log).
ti = d.get("tool_input")
if isinstance(ti, dict):
    v = ti.get("subagent_type")
    if isinstance(v, str) and v.strip():
        print(v.strip()); sys.exit(0)
for k in ("subagent_type", "agent_name", "agent", "subagentType", "agentName", "name", "matcher"):
    v = d.get(k)
    if isinstance(v, str) and v.strip():
        print(v.strip()); break
' 2>/dev/null)"

[ -n "$AGENTE" ] || exit 0

# La fase declarada en la ficha, para que el expediente diga desde qué nivel actuaba el agente.
# Si la ficha no la declara —el caso de los agentes heredados del template— se asume 3, que es el
# default que fija `rules/agent-autonomy-ladder.md` §3.2: lo no declarado opera en sombra.
FICHA="$PROJECT_DIR/.claude/agents/$AGENTE.md"
FASE=3
if [ -f "$FICHA" ]; then
  DECLARADA="$(grep -m1 -oE '^autonomy_phase:[[:space:]]*[0-9]+' "$FICHA" | grep -oE '[0-9]+' || true)"
  [ -n "$DECLARADA" ] && FASE="$DECLARADA"
fi

python3 "$SCRIPT" add \
  --proyecto "$PROJECT_SLUG" \
  --agente   "$AGENTE" \
  --fase     "${FASE:-0}" \
  --trigger  "${AGENT_REGISTRY_TRIGGER:-PostToolUse[Agent] (automático)}" \
  --nota     "pendiente de completar hallazgos/aplicados" >/dev/null 2>&1 || true

exit 0
