#!/usr/bin/env bash
# ══════════════════════════════════════════════════════════════════════════════════════════════
# correr.sh — el porcentaje de contexto de `suggest-compact.sh`, contra el caso que lo rompió.
#
# POR QUÉ. El 2026-09-23 el hook dijo «Contexto al 88%» en una sesión `opus[1m]` que iba al 18%:
# inferia la ventana como `1M si el uso pasa de 200k, si no 200k`, y por debajo de 200k toda sesión
# de 1M se trataba como de 200k. El agente lo repitió y recomendó compactar. Nadie lo vio porque
# ningún test miraba el número. Este lo mira.
#
# SE HA VISTO FALLAR: con HOOK=<la versión anterior> caen C-01, C-04, C-05 y C-06 (pasan 3/7): dan 88%
# donde toca 17% o silencio. Si alguien vuelve a la inferencia vieja, esto grita.
#
# Todo corre sobre fixtures en $TMPDIR, con HOME falso: nunca lee el ~/.claude real.
#
#   bash .claude/smoke/contexto/correr.sh
#   HOOK=/ruta/a/otra/version.sh bash .claude/smoke/contexto/correr.sh   # sabotaje
# ══════════════════════════════════════════════════════════════════════════════════════════════
set -uo pipefail
REPO="$(cd "$(dirname "${BASH_SOURCE[0]}")/../../.." && pwd)"
HOOK="${HOOK:-$REPO/.claude/hooks/suggest-compact.sh}"
TMP="$(mktemp -d "${TMPDIR:-/tmp}/smoke-contexto-XXXXXX")"
trap 'rm -rf "$TMP"' EXIT
mkdir -p "$TMP/home/.claude" "$TMP/proj/.claude" "$TMP/marcas"
OK=0; KO=0

transcript() {   # $1 = tokens usados en el último turno
  printf '{"type":"assistant","message":{"usage":{"input_tokens":%s,"cache_read_input_tokens":0,"cache_creation_input_tokens":0}}}\n' "$1" > "$TMP/t$1.jsonl"
}
transcript 177398; transcript 250000

# caso <id> <descripción> <tokens> <modelo en ~/.claude/settings.json, "" = ninguno> <esperado> [VAR=valor...]
# <esperado> es el porcentaje ("17%") o "SILENCIO". TL_COMPACT_BANDS=1 hace que hable aunque sea poco.
caso() {
  local id="$1" desc="$2" used="$3" modelo="$4" esperado="$5"; shift 5
  if [ -n "$modelo" ]; then printf '{"model":"%s"}\n' "$modelo" > "$TMP/home/.claude/settings.json"
  else echo '{}' > "$TMP/home/.claude/settings.json"; fi
  # PROJ_MODEL=<m> no es una variable del hook: escribe el settings.json DEL PROYECTO del fixture.
  rm -f "$TMP/proj/.claude/settings.json"
  local extra=()
  for a in "$@"; do
    case "$a" in PROJ_MODEL=*) printf '{"model":"%s"}\n' "${a#PROJ_MODEL=}" > "$TMP/proj/.claude/settings.json" ;;
                 *) extra+=("$a") ;; esac
  done
  set -- "${extra[@]+"${extra[@]}"}"
  local out
  out=$(printf '{"transcript_path":"%s","session_id":"%s","cwd":"%s"}' "$TMP/t$used.jsonl" "$id-$RANDOM" "$TMP/proj" \
        | env -u ANTHROPIC_MODEL -u TL_CONTEXT_LIMIT -u TL_NO_COMPACT_HINT HOME="$TMP/home" TMPDIR="$TMP/marcas" \
              CLAUDE_PROJECT_DIR="$TMP/proj" TL_COMPACT_BANDS=1 "$@" bash "$HOOK" 2>&1 | head -1)
  local visto
  if [ -z "$out" ]; then visto="SILENCIO"; else visto=$(printf '%s' "$out" | grep -oE '[0-9]+%' | head -1); fi
  if [ "$visto" = "$esperado" ]; then OK=$((OK+1)); echo "  ✓ $id $desc → $visto"
  else KO=$((KO+1)); echo "  ✗ $id $desc → esperaba $esperado, dio ${visto:-(nada)}  [$out]"; fi
}

echo "═══ suggest-compact.sh — ventana y porcentaje"
caso C-01 "opus[1m] con 177k: es el caso que mintió"          177398 "opus[1m]" "17%"
caso C-02 "opus sin [1m] con 177k: 200k, sí va al 88%"         177398 "opus"     "88%"
caso C-03 "más de 200k sin modelo: solo puede ser 1M"          250000 ""         "25%"
caso C-04 "ANTHROPIC_MODEL manda sobre settings"               177398 "opus"     "17%" ANTHROPIC_MODEL="opus[1m]"
caso C-05 "sin modelo y bajo 200k: no se inventa, calla"       177398 ""         "SILENCIO"
caso C-06 "settings.json del PROYECTO manda sobre el de HOME"  177398 "opus"     "17%" PROJ_MODEL="opus[1m]"
caso C-07 "TL_CONTEXT_LIMIT manda sobre todo"                  177398 "opus[1m]" "88%" TL_CONTEXT_LIMIT=200000

echo
TOT=$((OK+KO))
echo "═══ $OK/$TOT correctos · $KO fallidos"
[ "$KO" -eq 0 ] && echo "    El porcentaje sale de la ventana real, y calla cuando no la sabe." \
                || echo "    ⚠ El hook vuelve a dar un porcentaje que no puede saber (ver C-01 / C-05)."
exit $([ "$KO" -eq 0 ] && echo 0 || echo 1)
