#!/usr/bin/env bash
# judge-write-guard.sh — PreToolUse (matcher «Write|Edit|MultiEdit|NotebookEdit|Bash»). Envoltorio de
# scripts/judge_write_guard.py: un agente juez (tools: sin Edit) solo escribe en su zona (EQ-D14, 3.11).
# Política: rules/audit-team.md §5 · zonas: agents/shared/judge-write-zones.json.
#
# FALLA ASÍ, A PROPÓSITO:
#   · detector 0 o 2 → se respeta su decisión.
#   · detector roto (≠0/2), ausente o sin python3 → bloquea SOLO si la llamada trae `agent_type` (viene de
#     un subagente, que puede ser un juez); la sesión principal nunca se bloquea por una guarda rota.
# MODO PRUEBA: TL_JUEZ_SABOTAJE=excepcion hace reventar al detector (smoke/jueces/correr.sh).
AQUI="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ENTRADA="$(cat)"
# Vía rápida: sin `agent_type` la llamada es de la sesión principal, que nunca es un juez.
case "$ENTRADA" in *'"agent_type"'*) ;; *) exit 0 ;; esac
RC=99
if command -v python3 >/dev/null 2>&1 && [ -f "$AQUI/../scripts/judge_write_guard.py" ]; then
  printf '%s' "$ENTRADA" | python3 -I "$AQUI/../scripts/judge_write_guard.py"; RC=$?
  if [ "$RC" -eq 0 ] || [ "$RC" -eq 2 ]; then exit "$RC"; fi
fi
if printf '%s' "$ENTRADA" | grep -q '"agent_type" *: *"[^"]'; then
  echo "judge-write-guard ROTA (rc=$RC) y la llamada viene de un subagente: bloqueada por si es un juez. Arregla .claude/scripts/judge_write_guard.py." >&2
  exit 2
fi
exit 0
