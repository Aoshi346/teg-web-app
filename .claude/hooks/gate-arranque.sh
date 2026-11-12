#!/usr/bin/env bash
# ══════════════════════════════════════════════════════════════════════════════════════════════
# gate-arranque.sh — no se escribe código de producto sin los documentos base.
#
# POR QUÉ EXISTE. El Usuario preguntó el 2026-09-12 por qué al arrancar un proyecto nadie le
# preguntaba nada. Parte de la respuesta es que los 7 gates de `rules/plan-gates.md` son PROSA —los
# siete— y llevaban meses ignorándose. `rules/layer-decision.md` dice qué hacer con una norma
# escrita que se incumple: no se sube el tono, se BAJA DE CAPA. Esto es la capa.
#
# MATCHER: `Write|Edit|NotebookEdit`, y es regex sobre el NOMBRE de la tool. `Write(src/**)` NO CASA
# NUNCA — esa sintaxis es de `permissions`, no de hooks, y así estuvo el gate de RAM sin disparar
# desde que se escribió. El filtro por ruta va DENTRO, leyendo tool_input.file_path.
#
# EXIT 2 y solo el 2: en un PreToolUse el 1 es «error no bloqueante» y la escritura seguiría.
#
# OPT-IN: solo corre con TL_ARRANQUE=1 (settings.json → env). El template lo deja vacío a
# propósito: este repo es de configuración, no un producto, y el gate bloquearía su propio
# desarrollo. Lo enciende `project-setup` cuando el proyecto SÍ es un producto.
#
# AUTOLIMITACIÓN: a los 2 bloqueos consecutivos se degrada a exit 0 con aviso ruidoso y deja rastro.
# Razón: es mejor degradar en nuestros términos, dejando escrito que se degradó, que insistir hasta
# que el harness anule el hook por su cuenta habiendo quemado turnos. No es una jaula, es un badén.
#
# MODOS: (stdin JSON PreToolUse) · --file <ruta> (para el smoke).
# ══════════════════════════════════════════════════════════════════════════════════════════════
set -uo pipefail

[ "${TL_ARRANQUE:-}" = "1" ] || exit 0

if [ "${1:-}" = "--file" ]; then
  FILE="${2:-}"
else
  command -v jq >/dev/null 2>&1 || exit 0
  FILE=$(cat | jq -r '.tool_input.file_path // .tool_input.notebook_path // empty' 2>/dev/null)
fi
[ -n "$FILE" ] || exit 0

DIR="${CLAUDE_PROJECT_DIR:-$(git rev-parse --show-toplevel 2>/dev/null || pwd)}"

# ── 1 · ¿es código de PRODUCTO? ────────────────────────────────────────────────────────────────
# El harness, la documentación y los scripts del propio proyecto quedan fuera: si no, el gate
# impediría escribir los documentos que él mismo exige, que es la forma más tonta de morir.
#
# Se mira la ruta RELATIVA AL PROYECTO, no la absoluta (MO-61, sub-ola 2.17). Con la absoluta fallaba
# en los dos sentidos, medido en fitapp:
#   · falso positivo: el `.py` de trabajo del scratchpad (`/tmp/claude-0/…/scratchpad/montar_lienzo.py`)
#     contaba como producto; tres bloqueos así degradaron el gate dos veces el 2026-09-29.
#     Lo que está FUERA del proyecto no es su producto.
#   · falso negativo: dentro de un worktree (`<proyecto>/.claude/worktrees/<x>/backend/…`) la ruta
#     casaba con `*/.claude/*` y NINGÚN subagente en worktree pasaba por el gate. El worktree es el
#     proyecto: se le quita ese prefijo y se mira lo que queda.
# Dentro = dentro con los enlaces resueltos O sin resolverlos: `proyecto/compartido -> ../fuera` es
# del proyecto aunque su destino no lo sea (code-review-gate de la 2.17).
REL=""
for ABS in "$(realpath -m -- "$FILE" 2>/dev/null || printf '%s' "$FILE")" \
           "$(realpath -ms -- "$FILE" 2>/dev/null || printf '%s' "$FILE")"; do
  for RAIZ in "$(realpath -m -- "$DIR" 2>/dev/null || printf '%s' "$DIR")" \
              "$(realpath -ms -- "$DIR" 2>/dev/null || printf '%s' "$DIR")"; do
    case "$ABS" in "$RAIZ"/*) REL="${ABS#"$RAIZ"/}"; break 2 ;; esac
  done
done
[ -n "$REL" ] || exit 0
case "$REL" in
  .claude/worktrees/*/*) REL="${REL#.claude/worktrees/*/}" ;;
esac
case "$REL" in
  .claude/*|.docs/*|.specify/*|scripts/*|*/scripts/*|tests/*|*/tests/*|test/*|*/test/*|*.md|*.json|*.yaml|*.yml|*.txt|*.toml|*.cfg|*.ini|*.lock) exit 0 ;;
esac
case "$REL" in
  *.py|*.js|*.ts|*.tsx|*.jsx|*.vue|*.svelte|*.go|*.rb|*.php|*.java|*.kt|*.rs|*.sql|*.html|*.css|*.scss) ;;
  *) exit 0 ;;
esac

# ── 2 · la exención del Usuario ────────────────────────────────────────────────────────────────
# Badén, no muro: dentro de una sesión NADA distingue un fichero escrito por el Usuario de uno
# escrito por el agente. Lo que la hace real es que caduca, lleva nombre propio y queda en el log.
EX="$DIR/.docs/arranque/EXENCION.md"
if [ -f "$EX" ]; then
  CAD=$(grep -m1 -E '^\s*caduca\s*:' "$EX" | sed -E 's/.*:\s*//' | tr -d '"[:space:]')
  QUIEN=$(grep -m1 -E '^\s*autorizado_por\s*:' "$EX" | sed -E 's/.*:\s*//' | tr -d '"' | xargs)
  MOT=$(sed -n '/^\s*motivo\s*:/,$p' "$EX" | tail -n +2 | tr -d '\n' | xargs)
  HOY=$(date +%F)
  if [ -n "$CAD" ] && [ -n "$QUIEN" ] && [ "${#MOT}" -ge 40 ] && [[ "$CAD" > "$HOY" || "$CAD" == "$HOY" ]]; then
    printf '[%s] EXENCION honrada (gate-arranque): %s · caduca %s · %s\n' \
      "$(date '+%Y-%m-%d %H:%M')" "$QUIEN" "$CAD" "${MOT:0:100}" >> "$DIR/.claude/PROGRESS.log" 2>/dev/null
    exit 0
  fi
  [ -n "$CAD" ] && [[ "$CAD" < "$HOY" ]] && \
    echo "gate-arranque: hay EXENCION.md pero CADUCÓ el $CAD — vuelve a bloquear." >&2
fi

GATE="$DIR/.claude/scripts/gate_arranque.py"
[ -f "$GATE" ] || { echo "gate-arranque: falta gate_arranque.py — NO se comprobó nada" >&2; exit 0; }

OUT=$(python3 "$GATE" "$DIR" --hook --explica 2>&1); RC=$?
[ $RC -eq 0 ] && { rm -f "$DIR/.docs/arranque/.block-count" 2>/dev/null; exit 0; }

# ── 3 · autolimitación ─────────────────────────────────────────────────────────────────────────
CNT_F="$DIR/.docs/arranque/.block-count"
mkdir -p "$(dirname "$CNT_F")" 2>/dev/null
CNT=$(( $(cat "$CNT_F" 2>/dev/null || echo 0) + 1 ))
echo "$CNT" > "$CNT_F" 2>/dev/null
if [ "$CNT" -gt 2 ]; then
  printf '[%s] gate-arranque DEGRADADO tras %s bloqueos: deja pasar %s. El arranque SIGUE incompleto.\n' \
    "$(date '+%Y-%m-%d %H:%M')" "$CNT" "$FILE" >> "$DIR/.claude/PROGRESS.log" 2>/dev/null
  echo "⚠️  gate-arranque: $CNT bloqueos seguidos — DEGRADO a aviso y dejo pasar." >&2
  echo "    El arranque sigue incompleto y queda anotado en PROGRESS.log. No es un aprobado." >&2
  exit 0
fi

# ── 4 · el mensaje: qué falta, qué medida, y cómo se arregla ───────────────────────────────────
cat >&2 <<EOF
╔══════════════════════════════════════════════════════════════════════════════╗
║  BLOQUEADO: vas a escribir código de producto y el arranque no está cerrado.  ║
╚══════════════════════════════════════════════════════════════════════════════╝

  Fichero: $FILE

$OUT

CÓMO SE ARREGLA — una de estas tres:

  1. Sigue el arranque donde lo dejaste:        /arrancar
     Te pregunta por tandas de 3-4. La fase que falta son ~10 minutos.

  2. Si crees que ya está hecho, mira qué le falta exactamente:
         python3 .claude/scripts/gate_arranque.py . --explica

  3. Si esto NO es trabajo de producto —un spike, una prueba que se tira, un fix
     de una línea— el Usuario puede eximirlo. Lo escribe ÉL, en
     .docs/arranque/EXENCION.md:

         autorizado_por: <nombre de una persona>
         caduca: $(date -d '+7 days' +%F 2>/dev/null || date +%F)   # máximo 14 días
         alcance: spike
         motivo: >
           <mínimo 40 caracteres, y se lee>

     ⚠️ Ese fichero lo escribe el USUARIO. Si lo escribes tú, agente, estás saltándote
        el gate con su propio mecanismo de escape: eso no es una excepción, es una avería.
        Cada exención honrada queda anotada en .claude/PROGRESS.log con fecha y motivo.

  Bloqueo $CNT de 2. Al tercero degrado a aviso y dejo pasar, dejando rastro: es mejor
  degradar con el porqué escrito que ser anulado en silencio.
EOF
exit 2
