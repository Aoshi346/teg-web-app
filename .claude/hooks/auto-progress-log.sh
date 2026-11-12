#!/bin/bash
# auto-progress-log.sh — PostToolUse Write|Edit hook (async)
# Deja la traza automática de qué ficheros del proyecto tocó el agente, en `.claude/PROGRESS.auto.log`.
# `.claude/PROGRESS.log` queda para las entradas humanas (PLAN, BLOQUEADO, FIN…), que siguen siendo
# cosa del agente: este hook ya no escribe ahí.
#
# Formato, el de siempre:  [YYYY-MM-DD HH:MM] [AUTO] CATEGORÍA: ruta/relativa/al/proyecto
# Stack-agnostic: categoriza por extensión + ubicación relativa.
#
# POR QUÉ OTRO FICHERO (MO-37, sub-ola 2.13, 2026-10-21). Escribiendo en PROGRESS.log, las líneas
# [AUTO] tapaban las humanas: develop 143 de 143, fitapp 782 de 911, el template 824 de 973 (el
# 21-10), y evolution sin una sola entrada a mano. Además se colaban rutas de FUERA del proyecto
# (593 de las 824 del template: scratchpads, /tmp, otros repos) y la misma ruta salía una vez por
# cada Edit. Ahora: solo rutas dentro de $CLAUDE_PROJECT_DIR, y una línea por fichero y día.
# Lo que ya había en PROGRESS.log se queda donde está (no se reescribe): las [AUTO] viejas conviven
# con las nuevas de aquí, y quien las lea (otto-briefing) mira los dos ficheros.
#
# ⚠️ La entrada llega como JSON por STDIN. `CLAUDE_TOOL_NAME`/`CLAUDE_TOOL_FILE` no existen en
# Claude Code (0 apariciones en el binario 2.1.283): hasta el 2026-09-28 este hook no escribió
# nunca una línea. Se aceptan solo para probarlo a mano, sin stdin.

set -uo pipefail

PROJECT_DIR="${CLAUDE_PROJECT_DIR:-$(pwd)}"
LOG_FILE="$PROJECT_DIR/.claude/PROGRESS.auto.log"

if [ -t 0 ]; then
  ENTRADA=$(python3 -c 'import json,os
print(json.dumps({"tool_name": os.environ.get("CLAUDE_TOOL_NAME", "unknown"),
                  "tool_input": {"file_path": os.environ.get("CLAUDE_TOOL_FILE", "")}}))' 2>/dev/null)
else
  ENTRADA=$(cat)
fi

# tool y ruta RELATIVA al proyecto; vacía si el fichero está fuera de él (o no hay ruta)
# La ruta pasa por el redactor compartido (scripts/redactar.py, U.06) antes de escribirse: un nombre de
# fichero también puede llevar un token pegado. Sin redactor, no se anota nada (falla cerrado).
SCRIPTS_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../scripts" 2>/dev/null && pwd)"
read -r TOOL FILE < <(printf '%s' "$ENTRADA" | python3 -I -c 'import json,os,sys
try:
    if not sys.argv[2]:
        raise ImportError
    sys.path.insert(0, sys.argv[2])
    from redactar import redact
except Exception:
    print("unknown"); sys.exit()
try:
    d = json.load(sys.stdin)
except Exception:
    print("unknown"); sys.exit()
tool = d.get("tool_name") or "unknown"
f = (d.get("tool_input") or {}).get("file_path") or ""
proy = os.path.realpath(sys.argv[1])
rel = ""
if f:
    a = os.path.realpath(f if os.path.isabs(f) else os.path.join(proy, f))
    if a.startswith(proy + os.sep):
        rel = redact(os.path.relpath(a, proy))
print(tool, rel)' "$PROJECT_DIR" "$SCRIPTS_DIR" 2>/dev/null)

# Solo para Write y Edit
case "${TOOL:-}" in
  Write|Edit) ;;
  *) exit 0 ;;
esac

# Sin ruta, o fuera del proyecto: nada que anotar
[ -z "${FILE:-}" ] && exit 0

# Categorizar por path + extensión (orden: más específico → más genérico)
EXT="${FILE##*.}"
CATEGORY="FILE"

case "$FILE" in
  .claude/*)                   exit 0 ;;  # Ignorar cambios internos de config
  .specify/*)                  CATEGORY="SPEC" ;;
  */migrations/*)              CATEGORY="MIGRATION" ;;
  */tests/*|test_*|*_test.*)   CATEGORY="TEST" ;;
  */models.py|*/models/*)      CATEGORY="MODEL" ;;
  */views.py|*/views/*)        CATEGORY="VIEW" ;;
  */serializers.py)            CATEGORY="SERIALIZER" ;;
  */routers/*|*/urls.py)       CATEGORY="ROUTE" ;;
  */pages/*|*/app/*)           CATEGORY="PAGE" ;;
  */components/*)              CATEGORY="COMPONENT" ;;
  */stores/*|*/store/*)        CATEGORY="STORE" ;;
  */hooks/*)                   CATEGORY="HOOK" ;;
  */types/*|*/types.ts|*.d.ts) CATEGORY="TYPES" ;;
  *.md|*.mdx)                  CATEGORY="DOCS" ;;
  *.sql)                       CATEGORY="SQL" ;;
  *)
    case "$EXT" in
      py)          CATEGORY="PY" ;;
      ts|tsx)      CATEGORY="TS" ;;
      js|jsx)      CATEGORY="JS" ;;
      css|scss)    CATEGORY="STYLE" ;;
      yml|yaml)    CATEGORY="CONFIG" ;;
      json)        CATEGORY="JSON" ;;
    esac
    ;;
esac

mkdir -p "$(dirname "$LOG_FILE")"
DIA=$(date "+%Y-%m-%d")
LINEA="[AUTO] $CATEGORY: $FILE"

anota() {
  # Una línea por fichero y día: si hoy ya está, no se repite.
  if [ -f "$LOG_FILE" ] && awk -v d="[$DIA " -v l="$LINEA" \
       'index($0, d) == 1 && substr($0, index($0, "] ") + 2) == l { hay = 1; exit } END { exit !hay }' \
       "$LOG_FILE"; then
    return 0
  fi
  echo "[$(date "+%Y-%m-%d %H:%M")] $LINEA" >> "$LOG_FILE"
}

# El hook es async y dos Edit seguidos corren a la vez: con flock, el «¿ya está?» y el «añade» van
# juntos. Sin flock (macOS), puede colarse algún duplicado; nada más.
if command -v flock >/dev/null 2>&1; then
  ( flock -w 2 9 || exit 0; anota ) 9>>"$LOG_FILE"
else
  anota
fi

exit 0
