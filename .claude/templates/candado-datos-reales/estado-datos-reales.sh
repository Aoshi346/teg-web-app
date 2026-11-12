#!/usr/bin/env bash
# SessionStart — enseña el estado del candado de datos reales al abrir la sesión.
#
# Plantilla (templates/candado-datos-reales/). Se copia a .claude/hooks/ y se registra en el
# SessionStart de settings.json (eso pide aprobación: governance.md §2). Cosechado de
# accounting_AMC/.claude/hooks/estado-dpa.sh.
#
# Por qué existe: «sin permiso no se tocan datos reales» es la norma más fácil de incumplir sin
# querer, porque incumplirla no duele hasta que es tarde. Que el estado salga solo al abrir la sesión
# cuesta 50 ms y quita la excusa de «no me acordaba» (rules/layer-decision.md).
set -uo pipefail
cd "${CLAUDE_PROJECT_DIR:-.}" || exit 0
GATE=.claude/scripts/gate_datos_reales.py
[ -f "$GATE" ] || exit 0

if salida=$(python3 "$GATE" --json 2>/dev/null); then
  echo "🔓 Candado de datos reales: VERDE — se puede tocar el alcance acordado."
else
  pend=$(printf '%s' "$salida" | python3 -c '
import json, sys
try:
    d = json.load(sys.stdin)
    n = d.get("pendientes", [])
    print(str(len(n)) + " pendientes: " + ", ".join(n[:3]) + ("…" if len(n) > 3 else ""))
except Exception:
    print("no se pudo leer el estado")
' 2>/dev/null)
  echo "🔒 Candado de datos reales: ROJO (${pend:-no se pudo leer el estado})"
  echo "   → Se trabaja con fixtures/ y mocks/. Detalle: .claude/patterns/stack/backend-candado-datos-reales.md"
fi
exit 0
