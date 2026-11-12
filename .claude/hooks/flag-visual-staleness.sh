#!/bin/bash
# flag-visual-staleness.sh — Stop hook (async, best-effort). NO regenera nada. Siempre exit 0.
# Deja en `.claude/PROGRESS.auto.log`, como mucho UNA vez al día cada una, dos notas:
#   · el mapa visual está posiblemente desfasado: hay código más nuevo que el último
#     architecture*.html (bajo .docs/plans/*/, .docs/html/ o .claude/docs/html/) → corre /visual-map
#   · el grafo de código (graph-dataset.json) está a más de 20 commits de código del HEAD
# `otto-briefing.sh` enseña la primera al arrancar la sesión, si el mapa no se ha regenerado después.
#
# POR QUÉ ASÍ (MO-37 y MO-72, sub-ola 2.13, 2026-10-21). `Stop` salta al final de CADA respuesta.
# Este hook prometía «<2 s» y, medido con el JSON de un Stop (`_archive/2026-10-20/medicion-2.13/`),
# tardaba 42 s de reloj y 39 s de CPU por respuesta en fitapp, 5 s en AMC y 2,7 s en elvion: lanzaba
# un `stat` por cada fichero de backend/frontend/src/apps, incluido un `.venv` de 7.900 ficheros.
# Además escribía la nota en PROGRESS.log y solo la deduplicaba contra la última línea, así que se
# repetía entre las [AUTO]: 106-115 veces en EvoPreven. Y el bloque del grafo estaba dos veces.
# Ahora: una sola pregunta a `find` (¿hay ALGÚN fichero más nuevo que el mapa? → `-newer … -quit`),
# con .venv/venv y compañía podados, y nada si la nota de hoy ya está.

set -uo pipefail

PROJECT_DIR="${CLAUDE_PROJECT_DIR:-$(pwd)}"
LOG_FILE="$PROJECT_DIR/.claude/PROGRESS.auto.log"
DIA=$(date "+%Y-%m-%d")

ya_hoy() {   # ya_hoy <texto fijo de la nota>: ¿está ya en el log con fecha de hoy?
  [ -f "$LOG_FILE" ] && grep -F "[$DIA" "$LOG_FILE" 2>/dev/null | grep -qF "$1"
}
nota() {
  mkdir -p "$(dirname "$LOG_FILE")" 2>/dev/null
  # con segundos: otto-briefing y el propio hook comparan la nota con la hora del mapa
  echo "[$(date "+%Y-%m-%d %H:%M:%S")] NOTA: $1" >> "$LOG_FILE" 2>/dev/null
}
mas_reciente() {   # mas_reciente <patrón> <carpeta>…: el fichero más nuevo que casa (sin mayúsculas)
  python3 - "$@" 2>/dev/null <<'PY'
import fnmatch, os, sys
patron, mejor, t = sys.argv[1].lower(), "", -1.0
for raiz in sys.argv[2:]:
    for d, subdirs, ficheros in os.walk(raiz):
        subdirs[:] = [x for x in subdirs if x not in (".git", "node_modules")]
        for f in ficheros:
            if fnmatch.fnmatch(f.lower(), patron):
                p = os.path.join(d, f)
                try:
                    m = os.stat(p).st_mtime
                except OSError:
                    continue
                if m > t:
                    mejor, t = p, m
print(mejor)
PY
}

# 1) El mapa visual (architecture*.html) frente al código
# Una nota al día… mientras el mapa no se regenere: si se regenera DESPUÉS de la nota de hoy y el
# código vuelve a cambiar, toca otra (si no, el aviso callaba el resto del día con el mapa desfasado).
MARCA_MAPA="mapa visual posiblemente desfasado"
CODE_DIRS=()
for d in backend frontend src apps; do
  [ -d "$PROJECT_DIR/$d" ] && CODE_DIRS+=("$PROJECT_DIR/$d")
done
MAPA=""
if [ ${#CODE_DIRS[@]} -gt 0 ]; then
  DIRS_MAPA=()
  for d in "$PROJECT_DIR/.docs/plans" "$PROJECT_DIR/.docs/html" "$PROJECT_DIR/.claude/docs/html"; do
    [ -d "$d" ] && DIRS_MAPA+=("$d")
  done
  [ ${#DIRS_MAPA[@]} -gt 0 ] && MAPA=$(mas_reciente '*architecture*.html' "${DIRS_MAPA[@]}")
fi
if [ -n "$MAPA" ]; then             # sin código conocido o sin mapa generado: nada que comparar
  CUANDO=$( { grep -F "[$DIA" "$LOG_FILE" 2>/dev/null || true; } | grep -F "$MARCA_MAPA" | tail -1 \
            | sed -nE 's/^\[([0-9]{4}-[0-9]{2}-[0-9]{2})[T ]([0-9]{2}:[0-9]{2}(:[0-9]{2})?).*/\1 \2/p')
  if [ -z "$CUANDO" ] || [ -n "$(find "$MAPA" -newermt "$CUANDO" 2>/dev/null)" ]; then
    NUEVO=$(find "${CODE_DIRS[@]}" \( -name node_modules -o -name .git -o -name dist -o -name build \
              -o -name __pycache__ -o -name .venv -o -name venv -o -name .tox -o -name .mypy_cache \
              -o -name .pytest_cache -o -name .ruff_cache -o -name .next -o -name coverage \
              -o -name htmlcov -o -name target \) -prune -o -type f -newer "$MAPA" -print -quit 2>/dev/null)
    [ -n "$NUEVO" ] && nota "$MARCA_MAPA (código cambió tras última regeneración) — corre /visual-map"
  fi
fi

# ─────────────────────────────────────────────────────────────────────────────
# 2) El GRAFO DE CÓDIGO (graph-dataset.json) — añadido el 2026-08-27
#
# Este hook llevaba desde su creación mirando SOLO `architecture*.html`. Medido:
# `grep -c "graph-dataset\|graphify"` sobre este fichero daba 0. O sea, se genera un
# grafo de 13.801 nodos y nada avisa cuando envejece — y un grafo viejo miente sin
# que nadie se entere, que es peor que no tenerlo.
#
# Aquí NO se compara por mtime: el dataset lleva `meta.sha`, el commit con el que se
# generó. Comparar shas dice cuántos commits de CÓDIGO han entrado desde entonces,
# que es la pregunta de verdad. El mtime cambia con un `touch` y no significa nada.
# `head -1` cogía uno cualquiera: en elvion había dos y elegía el de hace 251 commits
# mientras existía uno recién hecho. Se coge el MÁS RECIENTE por mtime. (Hasta el 2026-10-21
# este bloque estaba dos veces: la copia vieja, con `head -1`, corría detrás de la buena.)
# ─────────────────────────────────────────────────────────────────────────────
MARCA_GRAFO="el grafo de código está a"
if [ -d "$PROJECT_DIR/.docs" ] && command -v git >/dev/null 2>&1 && ! ya_hoy "$MARCA_GRAFO"; then
  GD=$(mas_reciente 'graph-dataset.json' "$PROJECT_DIR/.docs")
  if [ -n "$GD" ]; then
    GD_SHA=$(python3 -c '
import json, sys
try: print((json.load(open(sys.argv[1])).get("meta") or {}).get("sha") or "")
except Exception: print("")' "$GD" 2>/dev/null)
    if [ -n "$GD_SHA" ] && git -C "$PROJECT_DIR" cat-file -e "${GD_SHA}^{commit}" 2>/dev/null; then
      # commits que han tocado CÓDIGO desde que se generó el grafo (no docs, no .claude)
      N=$(git -C "$PROJECT_DIR" rev-list --count "${GD_SHA}..HEAD" -- \
            '*.py' '*.ts' '*.tsx' '*.js' '*.jsx' 2>/dev/null || echo 0)
      if [ "${N:-0}" -gt 20 ]; then
        nota "$MARCA_GRAFO $N commits del HEAD (sha $GD_SHA) — regenera con: graphify extract . --code-only --no-viz --no-label --force"
      fi
    fi
  fi
fi

exit 0
