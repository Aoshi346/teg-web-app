#!/usr/bin/env bash
set -euo pipefail

# ─── TEG Web App — Start Backend & Frontend in parallel ───
# Usage: ./start.sh [--backend-port 8000] [--frontend-port 3000] [--turbo] [--clean] [--skip-deps]
#
#   --turbo       Run Next.js with Turbopack dev server instead of Webpack.
#                 Webpack is the default in dev mode (faster chunk compile on this project).
#   --clean       Wipe frontend/.next before starting. Use after ERR_INVALID_HTTP_RESPONSE
#                 or any chunk corruption error.
#   --skip-deps   Skip pip install / npm install checks entirely.
#                 Use when you know deps are up to date and want the fastest boot.
#
# Requires: python3, pip, node, npm

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BACKEND_DIR="$SCRIPT_DIR/backend"
FRONTEND_DIR="$SCRIPT_DIR/frontend"
VENV_DIR="$SCRIPT_DIR/.venv"

BACKEND_PORT=8000
FRONTEND_PORT=3000
FRONTEND_SCRIPT="dev"
CLEAN_NEXT=0
SKIP_DEPS=0

# ─── Parse arguments ───
while [[ $# -gt 0 ]]; do
  case "$1" in
    --backend-port)   BACKEND_PORT="$2"; shift 2 ;;
    --frontend-port)  FRONTEND_PORT="$2"; shift 2 ;;
    --turbo|--turbopack)
      FRONTEND_SCRIPT="dev:turbo"
      shift
      ;;
    --clean)      CLEAN_NEXT=1; shift ;;
    --skip-deps)  SKIP_DEPS=1; shift ;;
    *) echo "Unknown option: $1"; exit 1 ;;
  esac
done

# ─── Colors ───
BLUE='\033[0;34m'
ORANGE='\033[0;33m'
GREEN='\033[0;32m'
RED='\033[0;31m'
MAGENTA='\033[0;35m'
NC='\033[0m'

log_blue()    { echo -e "${BLUE}[backend]${NC}  $1"; }
log_orange()  { echo -e "${ORANGE}[frontend]${NC} $1"; }
log_green()   { echo -e "${GREEN}✓${NC} $1"; }
log_error()   { echo -e "${RED}✗${NC} $1"; }

# ─── Stream tagging (stdout + stderr) ───
# Prefixes every line with a colored tag. Errors (stderr) get a distinct color
# per service so failures are visible even when both streams are interleaved.
#
# Backend:   stdout = blue   [backend]    stderr = red       [backend:err]
# Frontend:  stdout = orange [frontend]   stderr = magenta   [frontend:err]

tag_stream() {
  # $1 = label, $2 = color (ANSI escape)
  local label="$1"
  local color="$2"
  awk -v lbl="$label" -v col="$color" -v nc="$NC" '{
    printf "%s%s%s %s\n", col, lbl, nc, $0
    fflush()
  }'
}

# ─── Cleanup on exit ───
PIDS=()
cleanup() {
  echo ""
  echo "Shutting down..."
  for pid in "${PIDS[@]}"; do
    kill "$pid" 2>/dev/null && wait "$pid" 2>/dev/null || true
  done
  log_green "All processes stopped."
}
trap cleanup EXIT INT TERM

# ─── Dependency hash helpers ───
deps_hash() {
  if [[ -f "$1" ]]; then
    sha256sum "$1" | awk '{print $1}'
  else
    echo "missing"
  fi
}

# ─── Backend setup ───
start_backend() {
  log_blue "Setting up backend..."

  # Create venv if missing
  if [[ ! -d "$VENV_DIR" ]]; then
    log_blue "Creating virtual environment at $VENV_DIR"
    python3 -m venv "$VENV_DIR"
  fi

  # Activate venv
  source "$VENV_DIR/bin/activate"

  # Install dependencies — only when requirements.txt changed or sentinel missing
  local req_file="$BACKEND_DIR/requirements.txt"
  local sentinel="$VENV_DIR/.deps-hash"

  if [[ $SKIP_DEPS -eq 1 ]]; then
    log_blue "Skipping dependency install (--skip-deps)"
  else
    local current_hash
    current_hash="$(deps_hash "$req_file")"
    local stored_hash=""
    [[ -f "$sentinel" ]] && stored_hash="$(cat "$sentinel")"

    if [[ "$current_hash" != "$stored_hash" ]]; then
      log_blue "requirements.txt changed — installing Python dependencies..."
      pip install --upgrade pip -q
      if [[ -f "$req_file" ]]; then
        pip install -r "$req_file" -q
      else
        log_blue "requirements.txt not found, installing minimal deps"
        pip install Django djangorestframework django-cors-headers -q
      fi
      echo "$current_hash" > "$sentinel"
    else
      log_blue "Dependencies up to date (hash match)"
    fi
  fi

  # Run migrations (idempotent, cheap if nothing pending)
  log_blue "Running migrations..."
  python "$BACKEND_DIR/manage.py" migrate 2>&1 | tail -1

  # Start server — split stdout/stderr into separate colored streams
  log_blue "Starting Django on http://127.0.0.1:$BACKEND_PORT"
  python "$BACKEND_DIR/manage.py" runserver "127.0.0.1:$BACKEND_PORT" \
    > >(tag_stream "  [backend]   " "$BLUE") \
    2> >(tag_stream "  [backend:err]" "$RED") &
  PIDS+=($!)
}

# ─── Frontend setup ───
start_frontend() {
  log_orange "Setting up frontend..."

  cd "$FRONTEND_DIR"

  # Optional .next wipe (fixes ERR_INVALID_HTTP_RESPONSE from stale chunks)
  if [[ $CLEAN_NEXT -eq 1 ]]; then
    log_orange "Cleaning .next cache..."
    rm -rf "$FRONTEND_DIR/.next"
  fi

  # Install node modules when missing or when package-lock changed
  local lock_file="$FRONTEND_DIR/package-lock.json"
  local sentinel="$FRONTEND_DIR/node_modules/.deps-hash"

  if [[ $SKIP_DEPS -eq 1 ]]; then
    log_orange "Skipping npm install (--skip-deps)"
  elif [[ ! -d "node_modules" ]]; then
    log_orange "Installing npm dependencies..."
    npm install
    deps_hash "$lock_file" > "$sentinel"
  else
    local current_hash stored_hash=""
    current_hash="$(deps_hash "$lock_file")"
    [[ -f "$sentinel" ]] && stored_hash="$(cat "$sentinel")"
    if [[ "$current_hash" != "$stored_hash" ]]; then
      log_orange "package-lock.json changed — running npm install..."
      npm install
      echo "$current_hash" > "$sentinel"
    else
      log_orange "Node modules up to date (hash match)"
    fi
  fi

  # Start dev server — split stdout/stderr into separate colored streams
  local bundler_label="Webpack"
  if [[ "$FRONTEND_SCRIPT" == "dev:turbo" ]]; then
    bundler_label="Turbopack"
  fi
  log_orange "Starting Next.js ($bundler_label) on http://localhost:$FRONTEND_PORT"
  PORT=$FRONTEND_PORT npm run "$FRONTEND_SCRIPT" \
    > >(tag_stream "  [frontend]   " "$ORANGE") \
    2> >(tag_stream "  [frontend:err]" "$MAGENTA") &
  PIDS+=($!)
}

# ─── Main ───
echo "╔══════════════════════════════════════╗"
echo "║     TEG Web App — Dev Launcher       ║"
echo "╚══════════════════════════════════════╝"
echo ""

start_backend
start_frontend

echo ""
log_green "Both servers starting..."
log_green "Backend:  http://127.0.0.1:$BACKEND_PORT"
log_green "Frontend: http://localhost:$FRONTEND_PORT"
echo ""
echo "Press Ctrl+C to stop both servers."

# Wait for all background processes
wait
