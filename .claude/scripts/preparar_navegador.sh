#!/usr/bin/env bash
# preparar_navegador.sh — deja Playwright de Python listo contra el Chromium del sistema, con una
# captura de prueba que demuestra que funciona. Un comando, el mismo en cada sesión.
#
# Por qué existe (AN-11, sub-ola 3.64): cada sesión redescubría lo mismo en este servidor: el MCP de
# Playwright busca /opt/google/chrome y no arranca, el python del sistema no trae playwright, hay que
# usar un venv, /usr/bin/chromium-browser y --no-sandbox como root. Una memoria dice cómo; un script
# lo hace igual cada vez. Y el venv puede desaparecer (el de /tmp/qa-venv quedó con bin/ vacío):
# por eso no se da por bueno un venv que existe, se le pide que importe playwright y saque la captura.
#
# Uso:
#   bash .claude/scripts/preparar_navegador.sh            # prepara (o reutiliza) y prueba
#   bash .claude/scripts/preparar_navegador.sh --env      # además imprime las dos variables para eval
#   eval "$(bash .claude/scripts/preparar_navegador.sh --env 2>/dev/null | grep '^export ')"
#   bash .claude/scripts/preparar_navegador.sh --venv /ruta/venv
#
# Variables: TL_PLAYWRIGHT_VENV (dónde vive el venv; por defecto ~/.cache/tl-playwright/venv),
#            TL_CHROMIUM (binario a usar; si no, se busca).
# Salida:    0 listo y probado · 2 no se pudo preparar (el motivo y el error entero, nunca recortado).
# No descarga navegadores (PLAYWRIGHT_SKIP_BROWSER_DOWNLOAD=1): usa el del sistema. Instalar
# chromium-browser es una dependencia del sistema y pide aprobación (governance.md §2).
set -u

PLAYWRIGHT_VERSION="1.58.0"   # la que corre en elvion desde septiembre; un bump se prueba con este script
VENV="${TL_PLAYWRIGHT_VENV:-$HOME/.cache/tl-playwright/venv}"
MARCA=".tl-playwright"        # solo se recrea un venv que creó este script
EMIT_ENV=0

while [ $# -gt 0 ]; do
  case "$1" in
    --venv) VENV="$2"; shift 2 ;;
    --env) EMIT_ENV=1; shift ;;
    -h|--help) sed -n '2,22p' "$0"; exit 0 ;;
    *) echo "argumento desconocido: $1" >&2; exit 2 ;;
  esac
done

falla() { echo "NO SE PUDO PREPARAR EL NAVEGADOR: $1" >&2; [ -n "${2:-}" ] && echo "$2" >&2; exit 2; }

# ── 1. El navegador del sistema ────────────────────────────────────────────────────────────────
CHROMIUM="${TL_CHROMIUM:-}"
if [ -z "$CHROMIUM" ]; then
  for c in /usr/bin/chromium-browser /snap/bin/chromium chromium-browser chromium google-chrome google-chrome-stable; do
    p=$(command -v "$c" 2>/dev/null) && { CHROMIUM="$p"; break; }
  done
fi
if [ -n "${TL_CHROMIUM:-}" ] && [ ! -x "$CHROMIUM" ]; then
  falla "TL_CHROMIUM=$TL_CHROMIUM no es un ejecutable."
fi
[ -n "$CHROMIUM" ] && [ -x "$CHROMIUM" ] || \
  falla "no hay Chromium ni Chrome en el sistema." "Instalar chromium-browser es una dependencia del sistema: pide OK (governance.md §2)."

# ── 2. El venv: se reutiliza si IMPORTA playwright, no porque exista ─────────────────────────────
PY="$VENV/bin/python"
if ! "$PY" -c "import playwright" >/dev/null 2>&1; then
  if [ -e "$VENV" ]; then
    [ -f "$VENV/$MARCA" ] || falla "$VENV existe pero no tiene playwright y no lo creó este script." \
      "No se toca un venv ajeno: pasa otro con --venv o TL_PLAYWRIGHT_VENV."
    echo "· el venv $VENV está roto (no importa playwright): se recrea" >&2
    rm -rf -- "$VENV"
  fi
  echo "· creando venv en $VENV con playwright==$PLAYWRIGHT_VERSION (sin descargar navegadores)" >&2
  mkdir -p "$(dirname "$VENV")"
  out=$(python3 -m venv "$VENV" 2>&1) || falla "python3 -m venv falló." "$out"
  touch "$VENV/$MARCA"
  out=$(PLAYWRIGHT_SKIP_BROWSER_DOWNLOAD=1 "$VENV/bin/pip" install -q "playwright==$PLAYWRIGHT_VERSION" 2>&1) \
    || falla "pip install playwright==$PLAYWRIGHT_VERSION falló." "$out"
fi

# ── 3. La prueba: una captura de verdad, no «el import funciona» ───────────────────────────────
TMPDIR_PRUEBA=$(mktemp -d)
trap 'rm -rf -- "$TMPDIR_PRUEBA"' EXIT     # la captura de prueba no se queda en /tmp
SALIDA=$TMPDIR_PRUEBA/prueba.png
out=$("$PY" - "$CHROMIUM" "$SALIDA" 2>&1 <<'PYEOF'
import os, sys
from playwright.sync_api import sync_playwright
exe, png = sys.argv[1], sys.argv[2]
with sync_playwright() as p:
    b = p.chromium.launch(headless=True, executable_path=exe, args=["--no-sandbox"])
    pg = b.new_page(viewport={"width": 390, "height": 300})
    pg.set_content("<h1 style='font:24px sans-serif'>preparar_navegador: ok</h1>")
    txt = pg.inner_text("h1")
    pg.screenshot(path=png)
    b.close()
assert txt == "preparar_navegador: ok", txt
assert os.path.getsize(png) > 500, "captura vacía"
print(f"captura {os.path.getsize(png)} bytes")
PYEOF
) || falla "el venv importa playwright pero no abrió $CHROMIUM o no sacó la captura." "$out"

VER=$("$PY" -c "import importlib.metadata as m; print(m.version('playwright'))")
echo "✓ navegador listo · playwright $VER · $("$CHROMIUM" --version 2>/dev/null | head -1) · $out" >&2
echo "  capturas:  $PY .claude/scripts/screenshot.py <url> <out.png>" >&2
echo "  a11y:      $PY .claude/scripts/auditar_a11y.py <url>" >&2
echo "  contraste: $PY .claude/scripts/contraste.py --dom <url>" >&2
if [ "$EMIT_ENV" = 1 ]; then
  echo "export TL_PLAYWRIGHT_PYTHON=$PY"
  echo "export TL_CHROMIUM=$CHROMIUM"
fi
exit 0
