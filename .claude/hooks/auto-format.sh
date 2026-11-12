#!/bin/bash
# auto-format.sh — PostToolUse Write|Edit hook
# Auto-formatea archivos Python (ruff) y JS/TS/TSX (prettier) después de editar, SOLO en las líneas
# que difieren del último commit (MO-45, sub-ola 2.14). Antes formateaba el fichero ENTERO: un arreglo
# de 2 líneas en un fichero heredado salía con un diff de cientos, y EvoPreven lo desregistró por
# chocar con su regla de «cambios mínimos».
#
# Modo, por proyecto (`.claude/CONFIGURACION.yaml`, pregunta `auto_format` del cuestionario):
#   lineas-tocadas (por defecto) · fichero-entero (lo de antes) · no (el hook no hace nada)
# Fichero nuevo (sin versionar) o fuera de un repo git: no hay diff que proteger, se formatea entero.
# Cada rango se formatea de abajo arriba, para que reformatear uno no mueva los números del siguiente;
# ruff y prettier amplían el rango a la sentencia completa que lo contiene (no dejan media sentencia).
#
# Timeout: el de settings.json, que va en SEGUNDOS (30 en el template; aquí ponía «3000ms» y
#   el 2026-10-21 siete derivados lo tenían en 3000, que son 50 minutos — MO-55). Si se pasa,
#   se cancela.
# Siempre exit 0 (no bloquea la herramienta)
#
# Stack-agnostic: detecta tools disponibles; si faltan, skip sin error.

set -uo pipefail  # NO -e para que errores no maten el script

PROJECT_DIR="${CLAUDE_PROJECT_DIR:-$(pwd)}"

# ⚠️ Claude Code pasa la entrada del hook como JSON por STDIN. Hasta el 2026-09-28 este hook leía
# `$1` o `CLAUDE_TOOL_FILE`, que Claude Code NO define (0 apariciones en el binario 2.1.283), así
# que salía con 0 en cada edición sin hacer nada — un hook muerto que parecía protección
# (check-agent de elvion-plataforma, 2026-09-26). `$1` se conserva para invocarlo a mano.
FILE_PATH="${1:-}"
if [ -z "$FILE_PATH" ] && [ ! -t 0 ]; then
  FILE_PATH="$(python3 -c 'import json,sys
try: print((json.load(sys.stdin).get("tool_input") or {}).get("file_path") or "")
except Exception: pass' 2>/dev/null)"
fi

# Si no tenemos el path, salir silenciosamente
if [ -z "$FILE_PATH" ]; then
  exit 0
fi

# Normalizar path absoluto
if [[ "$FILE_PATH" != /* ]]; then
  FILE_PATH="$PROJECT_DIR/$FILE_PATH"
fi

# Verificar que el archivo existe
if [ ! -f "$FILE_PATH" ]; then
  exit 0
fi

# Determinar tipo de archivo y formatear
EXT="${FILE_PATH##*.}"
case "$EXT" in py|js|jsx|ts|tsx|css) ;; *) exit 0 ;; esac

# ── MO-45: qué modo pide el proyecto y qué líneas se tocaron ──────────────────────────────────────
MODE="lineas-tocadas"
CONF="$PROJECT_DIR/.claude/CONFIGURACION.yaml"
if [ -f "$CONF" ]; then
  M="$(grep -E '^[[:space:]]*auto_format:' "$CONF" 2>/dev/null | head -1 | sed -E 's/^[^:]*:[[:space:]]*"?([a-z-]+).*/\1/')"
  case "$M" in no|fichero-entero|lineas-tocadas) MODE="$M" ;; esac
fi
[ "$MODE" = "no" ] && exit 0

# RANGES: una línea por bloque cambiado, «inicio fin_exclusivo offset_inicio offset_fin» (líneas
# 1-based; offsets en unidades UTF-16, para prettier), ya en orden de abajo arriba. WHOLE=1 = entero.
WHOLE=0
RANGES=""
FILE_DIR="$(dirname "$FILE_PATH")"
if [ "$MODE" = "fichero-entero" ]; then
  WHOLE=1
elif ! git -C "$FILE_DIR" ls-files --error-unmatch -- "$FILE_PATH" >/dev/null 2>&1; then
  WHOLE=1   # sin versionar o sin repo: todo el fichero es nuevo
elif ! git -C "$FILE_DIR" rev-parse -q --verify HEAD >/dev/null 2>&1; then
  WHOLE=1   # repo sin ningún commit: no hay con qué comparar, todo es nuevo
else
  RANGES="$(git -C "$FILE_DIR" diff -U0 --no-color --no-ext-diff HEAD -- "$FILE_PATH" 2>/dev/null \
    | python3 -c '
import re, sys
spans = []
for ln in sys.stdin:
    m = re.match(r"@@ -\S+ \+(\d+)(?:,(\d+))? @@", ln)
    if m and int(m.group(2) or 1):      # ",0" = solo se borraron líneas: nada nuevo que formatear
        a = int(m.group(1))
        spans.append((a, a + int(m.group(2) or 1)))
text = open(sys.argv[1], encoding="utf-8", errors="surrogateescape").read()
# prettier cuenta los offsets en unidades UTF-16 (un emoji son 2), no en caracteres de Python
starts, pos = [0], 0
for ch in text:
    pos += 2 if ord(ch) > 0xFFFF else 1
    if ch == "\n":
        starts.append(pos)
off = lambda n: starts[n - 1] if n - 1 < len(starts) else pos
for a, b in sorted(spans, reverse=True):
    print(a, b, off(a), off(b))
' "$FILE_PATH" 2>/dev/null)"
  [ -z "$RANGES" ] && exit 0   # sin cambios frente al último commit (o sin poder medirlos): no se toca
fi

case "$EXT" in
  py)
    # Solo FORMATO, nunca `ruff check --fix`: un agente escribe un fichero en varias ediciones, y
    # el autofix de «import sin usar» borraría el import de la primera antes de que la segunda lo
    # use. Formatear no cambia el significado; arreglar sí, y eso lo decide quien escribe.
    # El ruff del PROYECTO primero (venv o poetry): en esta máquina no hay ruff en el PATH.
    RUFF=""
    if [ -x "$PROJECT_DIR/.venv/bin/ruff" ]; then RUFF="$PROJECT_DIR/.venv/bin/ruff"
    elif [ -f "$PROJECT_DIR/pyproject.toml" ] && grep -q '^ruff' "$PROJECT_DIR/pyproject.toml" 2>/dev/null \
         && command -v poetry &> /dev/null; then RUFF="poetry --directory $PROJECT_DIR run ruff"
    elif command -v ruff &> /dev/null; then RUFF="ruff"
    fi
    if [ -n "$RUFF" ]; then
      if [ "$WHOLE" = 1 ]; then
        timeout 20 $RUFF format --quiet "$FILE_PATH" 2>/dev/null || true
      else
        # `--range=A-B`: de la línea A al principio de la B (fin exclusivo)
        while read -r A B _ _; do
          timeout 20 $RUFF format --quiet --range="$A-$B" "$FILE_PATH" 2>/dev/null || true
        done <<< "$RANGES"
      fi
    elif command -v black &> /dev/null; then
      if [ "$WHOLE" = 1 ]; then
        black --quiet "$FILE_PATH" 2>/dev/null || true
      else
        # `--line-ranges` es inclusivo y existe desde black 23.11; uno más viejo falla y no toca nada
        while read -r A B _ _; do
          black --quiet --line-ranges="$A-$((B - 1))" "$FILE_PATH" 2>/dev/null || true
        done <<< "$RANGES"
      fi
    fi
    ;;
  js|jsx|ts|tsx|css)
    # Sin .md ni .json: prettier reescribiría las rules y los registros del harness en cada
    # edición, y el diff real quedaría enterrado bajo el de formato.
    # JS/TS/React/etc: prettier
    # Busca prettier en: node_modules locales > frontend/node_modules > global
    PRETTIER=""
    if [ -x "$PROJECT_DIR/node_modules/.bin/prettier" ]; then
      PRETTIER="$PROJECT_DIR/node_modules/.bin/prettier"
    elif [ -x "$PROJECT_DIR/frontend/node_modules/.bin/prettier" ]; then
      PRETTIER="$PROJECT_DIR/frontend/node_modules/.bin/prettier"
    elif command -v prettier &> /dev/null; then
      PRETTIER="prettier"
    elif command -v npx &> /dev/null; then
      PRETTIER="npx --no-install prettier"
    fi
    if [ -n "$PRETTIER" ]; then
      if [ "$WHOLE" = 1 ]; then
        $PRETTIER --write "$FILE_PATH" 2>/dev/null || true
      else
        # offsets en caracteres; prettier amplía el rango a las sentencias que lo contienen
        while read -r _ _ C D; do
          $PRETTIER --write --range-start="$C" --range-end="$D" "$FILE_PATH" 2>/dev/null || true
        done <<< "$RANGES"
      fi
    fi
    ;;
  *)
    # Otros archivos: no formatear
    ;;
esac

exit 0
