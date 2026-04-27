#!/usr/bin/env bash
# ─── TEG Web App — control wrapper ───
#
# Thin wrapper over the teg-backend / teg-frontend systemd units.
# Keeps the ergonomics of start.sh (one command, readable output) while
# using systemd under the hood so the app survives reboots and SSH logout.
#
# Usage:
#   teg-ctl start           # start backend + frontend
#   teg-ctl stop            # stop both
#   teg-ctl restart         # restart both
#   teg-ctl restart backend # restart only backend (after .env edit)
#   teg-ctl restart frontend
#   teg-ctl status          # pretty status + listening ports
#   teg-ctl logs            # follow combined logs (Ctrl+C to exit)
#   teg-ctl logs backend    # follow only one unit
#   teg-ctl rebuild         # npm run build + restart frontend
#   teg-ctl migrate         # apply migrations + collectstatic, then restart backend
#
# Most subcommands need sudo (systemctl). Run with sudo or as root.

set -euo pipefail

SCRIPT_SRC="$(readlink -f "${BASH_SOURCE[0]}")"
SCRIPT_DIR="$(cd "$(dirname "$SCRIPT_SRC")" && pwd)"
REPO_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
BACKEND_DIR="$REPO_DIR/backend"
FRONTEND_DIR="$REPO_DIR/frontend"
VENV_DIR="$REPO_DIR/.venv"

BACKEND_UNIT="teg-backend"
FRONTEND_UNIT="teg-frontend"
BACKEND_PORT=8100
FRONTEND_PORT=3100

BLUE='\033[0;34m'; ORANGE='\033[0;33m'; GREEN='\033[0;32m'
RED='\033[0;31m'; BOLD='\033[1m'; NC='\033[0m'

log()    { echo -e "${BOLD}▸${NC} $*"; }
ok()     { echo -e "${GREEN}✓${NC} $*"; }
err()    { echo -e "${RED}✗${NC} $*" >&2; }

require_sudo() {
  if [[ $EUID -ne 0 ]]; then
    err "This command needs root. Re-run with: sudo $0 $*"
    exit 1
  fi
}

resolve_units() {
  # Map the optional target arg (backend|frontend|<empty>) to unit names.
  case "${1:-both}" in
    backend)  echo "$BACKEND_UNIT" ;;
    frontend) echo "$FRONTEND_UNIT" ;;
    both|"")  echo "$BACKEND_UNIT $FRONTEND_UNIT" ;;
    *) err "Unknown target '$1' (want: backend | frontend | both)"; exit 1 ;;
  esac
}

cmd_start() {
  require_sudo "$@"
  local units; units=$(resolve_units "${1:-}")
  log "Starting: $units"
  systemctl start $units
  sleep 1
  cmd_status
}

cmd_stop() {
  require_sudo "$@"
  local units; units=$(resolve_units "${1:-}")
  log "Stopping: $units"
  systemctl stop $units
  ok "Stopped. (nginx still runs; $BOLD tesisfar.elevaiti.com $NC will return 502 until you start again.)"
}

cmd_restart() {
  require_sudo "$@"
  local units; units=$(resolve_units "${1:-}")
  log "Restarting: $units"
  systemctl restart $units
  sleep 1
  cmd_status
}

cmd_status() {
  echo
  for unit in $BACKEND_UNIT $FRONTEND_UNIT; do
    local active enabled
    active=$(systemctl is-active "$unit" 2>/dev/null || true)
    enabled=$(systemctl is-enabled "$unit" 2>/dev/null || true)
    if [[ "$active" == "active" ]]; then
      echo -e "${GREEN}●${NC} $unit — ${GREEN}$active${NC} (boot: $enabled)"
    else
      echo -e "${RED}●${NC} $unit — ${RED}$active${NC} (boot: $enabled)"
    fi
  done
  echo
  log "Listening ports:"
  ss -tlnp 2>/dev/null | awk -v b=":$BACKEND_PORT" -v f=":$FRONTEND_PORT" '
    $4 ~ b || $4 ~ f { print "   " $1, $4, $6 }
  ' || true
  echo
  log "Public URL: https://tesisfar.elevaiti.com"
}

cmd_logs() {
  local units; units=$(resolve_units "${1:-}")
  local args=""
  for u in $units; do args+=" -u $u"; done
  log "Following logs (Ctrl+C to exit):$args"
  # shellcheck disable=SC2086
  journalctl $args -f -n 50 --output=short-iso
}

cmd_rebuild() {
  require_sudo "$@"
  log "Rebuilding frontend (npm run build)…"
  cd "$FRONTEND_DIR"
  npm run build
  log "Restarting $FRONTEND_UNIT…"
  systemctl restart "$FRONTEND_UNIT"
  sleep 1
  cmd_status
}

cmd_migrate() {
  require_sudo "$@"
  if [[ ! -d "$VENV_DIR" ]]; then err "venv not found at $VENV_DIR"; exit 1; fi
  log "Applying migrations and collectstatic…"
  # Load backend .env so settings.py sees prod values.
  set -a; source "$BACKEND_DIR/.env"; set +a
  # shellcheck disable=SC1091
  source "$VENV_DIR/bin/activate"
  python "$BACKEND_DIR/manage.py" migrate
  python "$BACKEND_DIR/manage.py" collectstatic --noinput
  log "Restarting $BACKEND_UNIT…"
  systemctl restart "$BACKEND_UNIT"
  sleep 1
  cmd_status
}

usage() {
  # Print the leading '# ...' comment block (stops at first non-comment line).
  awk '/^#!/ { next } /^#/ { sub(/^# ?/, ""); print; next } { exit }' "$0"
}

case "${1:-}" in
  start)    shift; cmd_start   "$@" ;;
  stop)     shift; cmd_stop    "$@" ;;
  restart)  shift; cmd_restart "$@" ;;
  status)   shift; cmd_status  "$@" ;;
  logs)     shift; cmd_logs    "$@" ;;
  rebuild)  shift; cmd_rebuild "$@" ;;
  migrate)  shift; cmd_migrate "$@" ;;
  ""|-h|--help|help) usage ;;
  *) err "Unknown command: $1"; echo; usage; exit 1 ;;
esac
