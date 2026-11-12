#!/usr/bin/env bash
# TesisFar — actualización automática (la lanza el timer tesisfar-update cada 5 minutos).
#
# 1. ¿Hay un commit nuevo en la rama vigilada (master)?          no → sale sin hacer nada
# 2. ¿Su CI en GitHub terminó en verde?                         pendiente → espera · rojo → avisa
# 3. Compila el commit en releases/<sha>, sin tocar lo que está sirviendo.
# 4. Copia la BD → migra → cambia el enlace `current` → reinicia → comprueba que responde.
# 5. Si algo falla en 4: vuelve al release anterior, restaura la copia de la BD y avisa.
#
# Uso: update.sh [--force] [--quiet]
#   --force   despliega aunque el CI no esté en verde (solo para la primera instalación)
set -Eeuo pipefail

BASE="${TESISFAR_BASE:-$HOME/tesisfar}"
KIT="$(cd "$(dirname "$(readlink -f "${BASH_SOURCE[0]}")")" && pwd)"
# shellcheck source=/dev/null
source "$BASE/deploy.conf"   # REPO_URL, BRANCH, GITHUB_REPO, PUBLIC_HOST

FORCE=0
for arg in "$@"; do
  case "$arg" in
    --force) FORCE=1 ;;
    *) echo "opción desconocida: $arg" >&2; exit 2 ;;
  esac
done

REPO="$BASE/repo"
RELEASES="$BASE/releases"
DATA="$BASE/data"
STATE="$BASE/state"
LOGS="$BASE/logs"
BACKUPS="$BASE/backups"
LOG="$LOGS/deploy.log"
KEEP_RELEASES=3
mkdir -p "$RELEASES" "$STATE" "$LOGS" "$BACKUPS"

log() { printf '[%s] %s\n' "$(date '+%F %T')" "$*" | tee -a "$LOG" >&2; }
notify() { python3 "$KIT/notify.py" "$@" || true; }
# Los servicios no deben heredar el candado (fd 9): si lo heredan, el lock no se suelta nunca.
svc() { sudo -n systemctl "$@" 9>&-; }

exec 9>"$STATE/update.lock"
flock -n 9 || exit 0   # ya hay una actualización en marcha

git -C "$REPO" fetch --quiet origin "$BRANCH"
TARGET="$(git -C "$REPO" rev-parse "origin/$BRANCH")"
SHORT="${TARGET:0:7}"
CURRENT=""
[[ -L "$BASE/current" ]] && CURRENT="$(basename "$(readlink -f "$BASE/current")")"

[[ "$TARGET" == "$CURRENT" ]] && exit 0
if (( ! FORCE )) && [[ "$TARGET" == "$(cat "$STATE/failed-sha" 2>/dev/null)" ]]; then
  exit 0   # ya falló: se espera a un commit nuevo
fi

SUBJECT="$(git -C "$REPO" log -1 --format='%s' "$TARGET")"

# ── 2. CI en verde ───────────────────────────────────────────────────────────────────────────
ci_status() {
  curl -fsS --max-time 20 -H "Accept: application/vnd.github+json" \
    "https://api.github.com/repos/$GITHUB_REPO/commits/$TARGET/check-runs?per_page=100" |
    python3 -c '
import json, sys
runs = json.load(sys.stdin).get("check_runs", [])
if not runs or any(r["status"] != "completed" for r in runs):
    print("pending")
elif all(r["conclusion"] in ("success", "skipped", "neutral") for r in runs):
    print("success")
else:
    print("failure")'
}

if (( ! FORCE )); then
  status="$(ci_status 2>/dev/null || echo unknown)"
  case "$status" in
    success) ;;
    failure)
      if [[ "$TARGET" != "$(cat "$STATE/ci-failed-sha" 2>/dev/null)" ]]; then
        echo "$TARGET" >"$STATE/ci-failed-sha"
        log "CI en rojo para $SHORT; no se despliega"
        notify error "CI en rojo: $SHORT no se publica" \
          "El commit $SHORT («$SUBJECT») no pasó los tests en GitHub. El servidor sigue con la versión actual.
Detalle: https://github.com/$GITHUB_REPO/commit/$TARGET"
      fi
      exit 0 ;;
    *) exit 0 ;;   # pendiente o GitHub no responde: se reintenta en 5 minutos
  esac
fi

log "── Desplegando $SHORT («$SUBJECT») sobre ${CURRENT:0:7}"

fail_build() {
  log "Falló la compilación de $SHORT: $1"
  echo "$TARGET" >"$STATE/failed-sha"
  rm -rf "${RELEASES:?}/${TARGET:?}"
  notify error "No se pudo compilar $SHORT" \
    "La versión $SHORT («$SUBJECT») falló al compilar ($1). La web sigue funcionando con la versión anterior.
Últimas líneas del registro:
$(tail -n 25 "$LOG")"
  exit 1
}

# ── 3. Compilar el release nuevo sin tocar el que sirve ──────────────────────────────────────
NEW="$RELEASES/$TARGET"
rm -rf "$NEW"
mkdir -p "$NEW"
git -C "$REPO" archive "$TARGET" | tar -x -C "$NEW" || fail_build "git archive"

set -a
# shellcheck source=/dev/null
source "$BASE/tesisfar.env"
set +a

{
  python3 -m venv "$NEW/backend/.venv" &&
  "$NEW/backend/.venv/bin/pip" install --quiet --disable-pip-version-check -r "$NEW/backend/requirements.txt"
} >>"$LOG" 2>&1 || fail_build "dependencias de Python"

(
  cd "$NEW/frontend"
  npm ci --no-audit --no-fund --loglevel=error &&
  # PC de 8 GB: la compilación no pasa de ~1,5 GB mientras la web sigue sirviendo.
  NODE_OPTIONS="${NODE_OPTIONS:---max-old-space-size=1536}" \
    NEXT_PUBLIC_API_URL=/api NEXT_TELEMETRY_DISABLED=1 npm run build
) >>"$LOG" 2>&1 || fail_build "frontend (npm ci / next build)"

# ── 4. Cambiar de versión ────────────────────────────────────────────────────────────────────
health() {
  local _
  for _ in $(seq 1 30); do
    if curl -fs --max-time 5 -o /dev/null -H "Host: $PUBLIC_HOST" http://127.0.0.1:8080/api/csrf/ &&
       curl -fs --max-time 5 -o /dev/null -H "Host: $PUBLIC_HOST" http://127.0.0.1:8080/; then
      return 0
    fi
    sleep 2
  done
  return 1
}

PRE_BACKUP="$BACKUPS/pre-deploy-$(date +%Y%m%d-%H%M%S)-${CURRENT:0:7}.sqlite3"
[[ -f "$DATA/db.sqlite3" ]] && python3 "$KIT/sqlite_backup.py" "$DATA/db.sqlite3" "$PRE_BACKUP"

rollback() {
  log "Volviendo a ${CURRENT:0:7}: $1"
  echo "$TARGET" >"$STATE/failed-sha"
  if [[ -n "$CURRENT" ]]; then
    svc stop tesisfar-backend.service || true
    if [[ -f "$PRE_BACKUP" ]]; then
      cp "$PRE_BACKUP" "$DATA/db.sqlite3"
      rm -f "$DATA/db.sqlite3-wal" "$DATA/db.sqlite3-shm"
    fi
    ln -sfn "$RELEASES/$CURRENT" "$BASE/current.tmp" && mv -Tf "$BASE/current.tmp" "$BASE/current"
    svc start tesisfar-backend.service || true
    svc restart tesisfar-backend.service tesisfar-frontend.service || true
  fi
  local estado="La web sigue con la versión anterior (${CURRENT:0:7})."
  health || estado="⚠️ La versión anterior TAMPOCO responde: hay que revisar el servidor."
  notify error "Falló la actualización a $SHORT — vuelta atrás" \
    "La versión $SHORT («$SUBJECT») falló en: $1.
Se restauró la base de datos de antes de la actualización. $estado
Últimas líneas del registro:
$(tail -n 25 "$LOG")"
  exit 1
}

(
  cd "$NEW/backend"
  .venv/bin/python manage.py collectstatic --noinput -v0 &&
  .venv/bin/python manage.py migrate --noinput
) >>"$LOG" 2>&1 || rollback "migraciones / collectstatic"

ln -sfn "$NEW" "$BASE/current.tmp" && mv -Tf "$BASE/current.tmp" "$BASE/current"
svc restart tesisfar-backend.service tesisfar-frontend.service >>"$LOG" 2>&1 ||
  rollback "reinicio de servicios"
health || rollback "la web no responde tras reiniciar"

rm -f "$STATE/failed-sha" "$STATE/ci-failed-sha"
log "OK: $SHORT en producción"
notify ok "Publicado $SHORT" "Nueva versión en https://$PUBLIC_HOST
$SHORT — $SUBJECT"

# Limpieza: se guardan los $KEEP_RELEASES releases más recientes (incluido el actual).
ls -1dt "$RELEASES"/*/ 2>/dev/null | tail -n +$((KEEP_RELEASES + 1)) | while read -r old; do
  [[ "$(readlink -f "$old")" == "$(readlink -f "$BASE/current")" ]] || rm -rf "$old"
done
ls -1t "$BACKUPS"/pre-deploy-*.sqlite3 2>/dev/null | tail -n +11 | xargs -r rm -f
