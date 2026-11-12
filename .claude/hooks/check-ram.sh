#!/bin/bash
# Hook: PreToolUse — verifica RAM antes de pytest.
#
# ESTE FICHERO ES LA FUENTE ÚNICA de los límites de RAM y concurrencia. Las rules los CITAN
# (`bash .claude/hooks/check-ram.sh --explain`), no los repiten: hasta 2026-09-11 el mismo número
# estaba escrito en cinco rules y en CLAUDE.md, así que cambiarlo obligaba a tocar seis ficheros y
# cualquiera que se olvidara dejaba una norma escrita que ya no era cierta.
#
#   check-ram.sh             → gate. exit 1 si no hay vía libre.
#   check-ram.sh --explain   → imprime los límites de ESTA máquina y sale 0. Para citar desde una rule.
#
# --- Umbral de RAM libre -------------------------------------------------------------------------
# Decisión del Usuario 2026-09-11: max(10% de la RAM total, 3 GB).
# Sustituye a max(20%, 5 GB) (2026-08-08), que en este servidor de 62 GB apartaba 12,4 GB que no
# usaba nadie y bloqueaba trabajo en paralelo legítimo. El porcentaje escala con el hardware; el
# suelo de 3 GB evita que en una máquina de 8 GB el 10% (0,8 GB) deje al sistema sin aire.
#
# --- Tope de sesiones concurrentes EN ESTE REPO --------------------------------------------------
# Decisión del Usuario 2026-09-11: deja de ser el "máximo 3" fijo y se DERIVA de la RAM que queda
# por encima del umbral, a 4 GB por sesión. Aquel 3 venía de una máquina más pequeña, no de una
# medición.
#
# Sutileza que hay que leer antes de "arreglar" la fórmula: `free` $7 (available) YA descuenta lo
# que consumen las sesiones vivas, así que el tope se estrecha solo conforme se llena la máquina —
# es auto-correctivo. No se le suman las sesiones actuales: si se hiciera, el tope sería siempre
# mayor que la cuenta y el check no bloquearía nunca.
#
# Lo que NO se deriva y sigue siendo criterio humano (rules/ram-pytest.md): los agentes con
# NAVEGADOR cuentan ~doble y siguen topados en 3. El hook no puede saber cuáles abren Chrome.
#
# --- Por qué son DOS checks y no uno -------------------------------------------------------------
#   · el umbral protege la RAM de la MÁQUINA — mira `free` global;
#   · el contador protege la CONCURRENCIA EN ESTE REPO — Tech Leads y worktrees de un mismo proyecto.
# Por eso se cuenta por directorio de trabajo. Las sesiones de otros repos consumen RAM, y esa RAM
# ya la vio el primer check. Contarlas aquí (el fallo de antes de 2026-08-26) bloqueaba este repo
# indefinidamente por lo que hacía otro, que es cómo se aprende a saltarse un gate (ASI09).

set -euo pipefail

TOTAL_MB=$(free -m | awk '/Mem:/ {print $2}')
AVAIL_MB=$(free -m | awk '/Mem:/ {print $7}')

MIN_MB=3072                          # suelo absoluto: 3 GB
PCT_MB=$(( TOTAL_MB * 10 / 100 ))    # 10% de la RAM total
THRESHOLD_MB=$(( PCT_MB > MIN_MB ? PCT_MB : MIN_MB ))

MB_PER_SESSION=4096                  # 4 GB por Tech Lead / worktree
# Agentes a la vez DENTRO de una sesión (subagentes y agentes de workflow corren en su proceso): el
# reparto de los 4 GB a 512 MB por agente, que es criterio y no medida (lo que ocupa un comando
# típico: un pytest por módulo, un build). Sale 8 y va a CLAUDE_CODE_MAX_CONCURRENT_SUBAGENTS y
# CLAUDE_CODE_WORKFLOW_MAX_CONCURRENT_AGENTS de settings.json; check_mechanisms.py exige que cuadre
# (sub-ola 2.01, CL-7). Son UN TOPE POR MECANISMO: los agentes de un workflow no cuentan en el de
# subagentes, así que una sesión con subagentes y un workflow a la vez puede pasar de 8. Cambiar uno
# de los dos números obliga a cambiar el settings.
MB_PER_AGENT=512
AGENTS_PER_SESSION=$(( MB_PER_SESSION / MB_PER_AGENT ))
HEADROOM_MB=$(( AVAIL_MB - THRESHOLD_MB ))
MAX_SESSIONS=$(( HEADROOM_MB / MB_PER_SESSION ))
[ "$MAX_SESSIONS" -lt 1 ] && MAX_SESSIONS=1   # suelo: siempre cabe la sesión que está preguntando

# Sesiones REALES = procesos del BINARIO de Claude Code que consumen RAM de sesión (>200 MB RSS).
# Se reconocen por el ejecutable que corre (argv[0], o el script que corre node/bun), NO por que la
# línea de comandos diga «claude» en algún sitio. Buscando la palabra salían el daemon, los
# bg-pty-host/bg-spare, los `tmux new … claude`, shells cuyo PATH contiene /root/.claude/ (13
# «instancias» donde había 3) y, lo último, los workers de Vite/Vitest de `.claude/worktrees/…`: llevan
# «claude» en la ruta, pasan de 200 MB y su directorio es el repo, así que el gate bloqueó el pytest
# de un TL con «9 sesiones» que eran Vitest (fitapp, 2026-10-07; MO-23, sub-ola 2.04). Cuenta: el
# `claude` nativo (por PATH, por ruta, la extensión del IDE o `…/claude/versions/<v>`) y el node/bun
# que corre `…/claude` o el paquete `@anthropic-ai/claude-code`; sus procesos de servicio, no.
REPO_ROOT=$(git -C "$(dirname "${BASH_SOURCE[0]}")" rev-parse --show-toplevel 2>/dev/null || pwd)

SESSIONS_MACHINE=0
SESSIONS_REPO=0
while read -r rss pid; do
  [ "${rss:-0}" -gt 204800 ] || continue
  SESSIONS_MACHINE=$(( SESSIONS_MACHINE + 1 ))
  cwd=$(readlink "/proc/$pid/cwd" 2>/dev/null || true)
  case "$cwd" in
    "$REPO_ROOT"|"$REPO_ROOT"/*) SESSIONS_REPO=$(( SESSIONS_REPO + 1 )) ;;
  esac
done < <(ps -eo rss=,pid=,args= | awk '
  $3 ~ /(^|\/)claude$/ || $3 ~ /\/claude\/versions\/[^\/]+$/ ||
  ($3 ~ /(^|\/)(node|bun)$/ && ($4 ~ /(^|\/)claude$/ || $4 ~ /@anthropic-ai\/claude-code\//)) {
    if ($0 ~ / (bg-pty-host|bg-spare)( |$)| daemon run( |$)/) next
    print $1, $2
  }')

if [ "${1:-}" = "--explain" ]; then
  cat <<EXPLAIN
Límites de RAM vigentes en esta máquina (fuente: .claude/hooks/check-ram.sh)

  RAM total                 $(( TOTAL_MB / 1024 )) GB
  RAM libre ahora           $(( AVAIL_MB / 1024 )) GB
  Umbral (no bajar de ahí)  $(( THRESHOLD_MB / 1024 )) GB   = max(10% del total, 3 GB)

  RAM por sesión            $(( MB_PER_SESSION / 1024 )) GB
  Tope de sesiones/repo     ${MAX_SESSIONS}       = (libre − umbral) ÷ $(( MB_PER_SESSION / 1024 )) GB, mínimo 1
  Sesiones ahora            ${SESSIONS_REPO} en este repo · ${SESSIONS_MACHINE} en la máquina

  Agentes a la vez          ${AGENTS_PER_SESSION}       = $(( MB_PER_SESSION / 1024 )) GB ÷ ${MB_PER_AGENT} MB por agente (criterio) → tope de subagentes
                                      de la sesión y, aparte, de cada workflow (se suman)

  Agentes con NAVEGADOR: cuentan ~doble y siguen topados en 3 (criterio, no derivado).
  Workers de pytest: máximo 2. Nunca 'pytest' entero, ni -n auto, ni --cov.
EXPLAIN
  exit 0
fi

# El motivo va por stderr: es lo que se ve cuando el bloqueo llega a través de un hook (gate-ram-pytest.sh
# lo reenvía) y también a mano, en la salida de la tool Bash.
if [ "$AVAIL_MB" -lt "$THRESHOLD_MB" ]; then
  {
    echo "BLOCKED: $(( AVAIL_MB / 1024 ))GB RAM libre — mínimo $(( THRESHOLD_MB / 1024 ))GB (10% de $(( TOTAL_MB / 1024 ))GB, suelo 3GB)."
    echo "Espera a que se libere RAM, cierra agentes con navegador, o reduce el scope del test."
  } >&2
  exit 1
fi

if [ "$SESSIONS_REPO" -gt "$MAX_SESSIONS" ]; then
  {
    echo "BLOCKED: ${SESSIONS_REPO} sesiones de Claude Code en este repo — el tope es ${MAX_SESSIONS}."
    echo "Repo: $REPO_ROOT"
    echo "El tope sale de la RAM libre: ($(( AVAIL_MB / 1024 ))GB − $(( THRESHOLD_MB / 1024 ))GB umbral) ÷ $(( MB_PER_SESSION / 1024 ))GB por sesión."
    echo "Espera a que termine alguna, o libera RAM."
  } >&2
  exit 1
fi

# Informativo, NO bloquea: la RAM que consumen ya la ha comprobado el umbral de arriba.
if [ "$SESSIONS_MACHINE" -gt "$MAX_SESSIONS" ]; then
  echo "aviso: ${SESSIONS_MACHINE} sesiones de Claude Code en la máquina (${SESSIONS_REPO} en este repo)." >&2
fi

exit 0
