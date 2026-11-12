#!/bin/bash
# otto-briefing.sh — SessionStart SÍNCRONO. Briefing de Otto sin LLM (<500ms; con el paso del
#   proceso, el de siguiente_paso.py, ~0,1 s más medido en el template — tope 7 s).
# stdout → se inyecta como contexto al arrancar la sesión.
# Wiring en settings.json (hooks.SessionStart, SIN async — la inyección async es poco fiable):
#   { "hooks": [{ "type": "command", "command": ".claude/hooks/otto-briefing.sh", "timeout": 10 }] }
#   (segundos; 10 es lo que registra el template y cubre el tope de 7 s del paso del proceso)
# Diseño: solo lee ficheros locales; degrada en silencio si falta algo; SIEMPRE exit 0.

set -u
cd "${CLAUDE_PROJECT_DIR:-$(pwd)}" 2>/dev/null || exit 0

# ── Dónde estamos en el proceso y qué hay que teclear (antes el hook siguiente-paso.sh) ─────────
# Fusionado aquí el 2026-10-19 (LI-25): eran dos hooks de SessionStart para la misma pregunta, y el
# de proceso solo estaba registrado en dos derivados. Lo que hacía, igual:
#   POR QUÉ EXISTE. El harness lo usa gente que NO conoce los comandos (T-240, 2026-09-14). Que el
#   agente «se acuerde» de decir el siguiente paso es prosa advisory; que lo imprima un hook al
#   arrancar cada sesión es mecanismo (`rules/layer-decision.md`). El contenido lo calcula
#   `scripts/siguiente_paso.py` desde el disco (misma medición que proceso.html); esto solo lo lanza.
#   NO BLOQUEA NADA. Si falta el script o el plan, calla — un hook que estorba se acaba quitando.
#   gate_arranque puede tardar un par de segundos en un plan con documentos: tope de 7 s, y el
#   registro de este hook en settings.json lleva timeout de 10.
proceso() {
  local S=".claude/scripts/siguiente_paso.py"
  [ -f "$S" ] || return 0
  CLAUDE_PROJECT_DIR="$(pwd)" timeout 7 python3 "$S" 2>/dev/null || true
}

# ── Worktrees olvidados (AN-4, sub-ola 3.18) ────────────────────────────────────────────────────
# Calla por debajo de 10 worktrees y 2 GB en .claude/worktrees/; por encima, cuántos, cuánto pesan y
# cuáles ya están mergeados. Solo AVISA: borrar requiere OK (governance.md §2). Tope de 2 s (mirar con
# 1,2 s en paralelo; lo que no da tiempo sale «sin medir»), para que con los 7 s del proceso quepa en el timeout 10.
worktrees() {
  local S=".claude/scripts/worktree_report.py"
  [ -f "$S" ] || return 0
  timeout 2 python3 "$S" --root "$(pwd)" --budget 1.2 2>/dev/null || true
}

# ── Memorias de agente que han crecido de más (EQ-5, sub-ola 3.14) ──────────────────────────────
# Calla si ninguna `agents/<x>/memory.md` ni `herencia/*.md` pasa de 300 líneas; si alguna pasa, la
# nombra con la orden de consolidar. Solo avisa. Tope de 1 s: son unas decenas de ficheros.
memorias() {
  local S=".claude/scripts/check_agent_memory.py"
  [ -f "$S" ] || return 0
  timeout 1 python3 "$S" "$(pwd)" --quiet 2>/dev/null || true
}

OTTO_DIR=".claude/agents/otto-copilot"
[ -d "$OTTO_DIR" ] || { worktrees; memorias; proceso; exit 0; }   # Otto no instalado → worktrees, memorias y el paso del proceso

echo "🅾️ Otto — briefing de sesión"

# 1) Estado del trabajo (PROGRESS.json)
if [ -f PROGRESS.json ] && command -v jq >/dev/null 2>&1; then
  TASK=$(jq -r '.task // empty' PROGRESS.json 2>/dev/null | cut -c1-90)
  STATUS=$(jq -r '.status // empty' PROGRESS.json 2>/dev/null)
  PEND=$(jq '[.checklist[]? | select(.done==false)] | length' PROGRESS.json 2>/dev/null)
  [ -n "$TASK" ] && echo "· Tarea: $TASK [$STATUS] — $PEND items pendientes"
fi

# 2) Git en una línea
if git rev-parse --git-dir >/dev/null 2>&1; then
  BR=$(git branch --show-current 2>/dev/null)
  DIRTY=$(git status --porcelain 2>/dev/null | wc -l)
  AHEAD=$(git rev-list --count @{u}..HEAD 2>/dev/null || echo "?")
  echo "· Git: $BR · $DIRTY sin commitear · $AHEAD commits sin push"
fi

# 3) tasks.md de la sesión SpecKit activa (la más reciente)
LATEST_TASKS=$(ls -t .specify/sessions/*/tasks.md 2>/dev/null | head -1)
if [ -n "${LATEST_TASKS:-}" ]; then
  # grep -c imprime "0" él solo cuando no hay matches (con exit 1) — no añadir echo, duplicaría
  DOING=$(grep -c '^\- \[>\]' "$LATEST_TASKS" 2>/dev/null || true)
  TODO=$(grep -c '^\- \[ \]' "$LATEST_TASKS" 2>/dev/null || true)
  BLOCK=$(grep -c '^\- \[!\]' "$LATEST_TASKS" 2>/dev/null || true)
  echo "· SpecKit: $(basename "$(dirname "$LATEST_TASKS")") — $DOING en curso · $TODO pendientes · $BLOCK bloqueadas"
fi

# 4) Sugerencias vivas de la memoria de Otto (máx 3, saltando placeholders)
if [ -f "$OTTO_DIR/memory.md" ]; then
  # Dos averías que hacían que esta sección NUNCA mostrara nada. Las encontró y arregló elvion
  # el 2026-08-12; aquí llegan por cosecha inversa el 2026-08-23:
  #   1. el patrón era '^## Sugerencias vivas' y la cabecera puede llevar numeración ('## 7. …')
  #   2. el rango awk '/^## X/,/^## /' se CIERRA EN LA MISMA LÍNEA que lo abre, porque la cabecera
  #      casa también con el patrón de cierre → devolvía 1 línea: la propia cabecera.
  # Comprobado sobre la memoria de Otto de este repo: antes 1 línea, ahora 7 (la tabla entera).
  SUGS=$(awk '/^## .*Sugerencias vivas/{f=1;next} /^## /{f=0} f' "$OTTO_DIR/memory.md" \
        | grep -E '^\| [A-Za-z0-9]' | grep -v '_(vacío)_' | grep -v '^| ID' | head -3)
  if [ -n "$SUGS" ]; then
    echo "· Sugerencias vivas de Otto:"
    echo "$SUGS" | sed 's/^/    /'
  fi
fi

# 5) Aviso de mapa visual desfasado (reusa la señal del hook de staleness si la dejó)
# Desde el 2026-10-21 (MO-37) la nota va a PROGRESS.auto.log; las de antes siguen en PROGRESS.log, y
# se mira en los dos. Y solo se enseña si ningún mapa se regeneró DESPUÉS de la nota: antes salía la
# última de la historia para siempre, aunque el mapa ya estuviera al día.
STALE=$(grep -h "mapa visual posiblemente desfasado" .claude/PROGRESS.log .claude/PROGRESS.auto.log \
          2>/dev/null | sort | tail -1)
if [ -n "$STALE" ]; then
  CUANDO=$(echo "$STALE" | sed -nE 's/^\[([0-9]{4}-[0-9]{2}-[0-9]{2})[T ]([0-9]{2}:[0-9]{2}(:[0-9]{2})?).*/\1 \2/p')
  REGENERADO=""
  if [ -n "$CUANDO" ]; then
    REGENERADO=$(find .docs/plans .docs/html .claude/docs/html -type f -iname '*architecture*.html' \
                   -newermt "$CUANDO" -print -quit 2>/dev/null)
  fi
  [ -z "$REGENERADO" ] && echo "· ⚠ $(echo "$STALE" | sed 's/^\[[^]]*\] NOTA: //')"
fi

echo "· Para el modo guía completo en tareas grandes: Gate 0 de rules/plan-gates.md (corre la skill /otto)"
# AGT-7, cosechado de elvion el 2026-08-23: el modo GROW existía y NUNCA se disparó, porque uno de
# sus disparadores es que el Usuario diga la frase exacta "Otto, guíame" y nadie la conocía. Una
# capacidad que hay que adivinar cómo invocar es una capacidad que no existe: se señaliza aquí.
echo "· ¿Sabes el procedimiento pero no el objetivo? Di \"Otto, guíame\" y te pregunta antes de"
echo "  recomendar (objetivo · realidad · opciones · compromiso), en vez de darte una lista."

worktrees
memorias

# 6) El paso del proceso (antes siguiente-paso.sh): al final, porque es lo que se lee antes de teclear.
proceso
exit 0
