#!/bin/bash
# Hook: SessionEnd — Verifica estado al terminar sesión
#
# Hasta el 2026-10-21 estaba en `Stop`, que salta al final de CADA respuesta, no al cerrar: 38-56 ms
# de espera síncrona por respuesta (medido con el JSON de un Stop en el template, AMC, fitapp y elvion;
# `_archive/2026-10-20/medicion-2.13/`) para un aviso que no veía nadie — con exit 0, el stdout de un
# Stop o un SessionEnd va al log de depuración (`claude-code-referencia` §3.4). Lo mismo, visible, lo
# da `otto-briefing.sh` al arrancar la siguiente sesión («N sin commitear · M commits sin push»).

#
# La política de git es un dato del proyecto (MO-16, sub-ola 2.14): si `.claude/CONFIGURACION.yaml`
# responde `git_commit: usuario` (los commits los hace el Usuario, como en EvoPreven), este hook no
# sugiere commitear; da el recuento y dice quién commitea. Antes lo sugería igual, y EvoPreven tuvo que
# desregistrarlo.
COMMITS_BY="agente"
CONF="${CLAUDE_PROJECT_DIR:-.}/.claude/CONFIGURACION.yaml"
if [ -f "$CONF" ] && grep -qE '^[[:space:]]*git_commit:[[:space:]]*"?usuario' "$CONF" 2>/dev/null; then
  COMMITS_BY="usuario"
fi

# Check for uncommitted changes
CHANGES=$(git status --porcelain 2>/dev/null || true)

if [ -n "$CHANGES" ]; then
  CHANGED_COUNT=$(echo "$CHANGES" | wc -l)
  if [ "$COMMITS_BY" = "usuario" ]; then
    echo "INFO: ${CHANGED_COUNT} cambios sin commit. En este proyecto commitea el Usuario (CONFIGURACION.yaml)."
  else
    echo "WARNING: ${CHANGED_COUNT} cambios sin commit detectados."
    echo "Considera hacer commit antes de cerrar la sesión."
  fi
fi

# Check for unpushed commits
UNPUSHED=$(git log @{u}.. --oneline 2>/dev/null || true)

if [ -n "$UNPUSHED" ]; then
  UNPUSHED_COUNT=$(echo "$UNPUSHED" | wc -l)
  echo "INFO: ${UNPUSHED_COUNT} commits sin push."
fi

# Always exit 0 — this is informational, not blocking
exit 0
