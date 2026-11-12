#!/usr/bin/env bash
# Smoke de hooks/gate-fases-diseno.sh (sub-ola 3.67, UX-6): el hook entero, por stdin, en un
# proyecto de juguete con React. La lógica la prueba `gate_fases_diseno.py --self-test`; esto prueba
# la conexión: avisa sin bloquear, bloquea con TL_FASES_DISENO=bloquear, calla en un .tsx y anota.
set -uo pipefail
RAIZ="$(cd "$(dirname "$0")/../../.." && pwd)"
HOOK="$RAIZ/.claude/hooks/gate-fases-diseno.sh"
TOY="$(mktemp -d)"
mkdir -p "$TOY/.claude/scripts" "$TOY/frontend"
cp "$RAIZ/.claude/scripts/gate_fases_diseno.py" "$TOY/.claude/scripts/"
echo '{"dependencies": {"react": "19.0.0"}}' > "$TOY/frontend/package.json"
FALLOS=0
ok() { echo "  ✓ $1"; }
ko() { echo "  ✗ $1"; FALLOS=$((FALLOS + 1)); }

MODELO='{"tool_name":"Write","tool_input":{"file_path":"backend/apps/orders/models.py"}}'
OUT=$(echo "$MODELO" | CLAUDE_PROJECT_DIR="$TOY" bash "$HOOK" 2>/dev/null); RC=$?
[ $RC -eq 0 ] && echo "$OUT" | grep -q '"additionalContext"' \
  && ok "models.py con UI y sin mockup: avisa (additionalContext) y deja pasar" \
  || ko "models.py debía avisar con exit 0 (rc=$RC, salida: ${OUT:0:80})"

echo "$MODELO" | TL_FASES_DISENO=bloquear CLAUDE_PROJECT_DIR="$TOY" bash "$HOOK" >/dev/null 2>&1
RC=$?
[ $RC -eq 2 ] && ok "con TL_FASES_DISENO=bloquear: exit 2" || ko "bloquear debía dar 2 (rc=$RC)"

OUT=$(echo '{"tool_input":{"file_path":"frontend/src/App.tsx"}}' \
  | CLAUDE_PROJECT_DIR="$TOY" bash "$HOOK" 2>&1); RC=$?
[ $RC -eq 0 ] && [ -z "$OUT" ] && ok "un .tsx: silencio" || ko "un .tsx debía callar (rc=$RC)"

N=$(wc -l < "$TOY/.docs/diseno/avisos-fases.jsonl" 2>/dev/null || echo 0)
[ "$N" -ge 1 ] && ok "los avisos se anotan para contar falsas alarmas ($N)" \
  || ko "no se anotó el aviso en .docs/diseno/avisos-fases.jsonl"

mkdir -p "$TOY/.docs/diseno"
printf 'cerrado: 2026-11-01\naprobado_por: Miller\n' > "$TOY/.docs/diseno/mockup-cerrado.md"
OUT=$(echo "$MODELO" | CLAUDE_PROJECT_DIR="$TOY" bash "$HOOK" 2>&1); RC=$?
[ $RC -eq 0 ] && [ -z "$OUT" ] && ok "con el mockup cerrado y firmado: silencio" \
  || ko "con el mockup cerrado debía callar (rc=$RC)"

rm -r "$TOY"
if [ $FALLOS -eq 0 ]; then echo "smoke gate-fases-diseno: OK"
else echo "smoke gate-fases-diseno: FALLA ($FALLOS)"; fi
exit $((FALLOS > 0))
