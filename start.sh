#!/usr/bin/env bash
set -euo pipefail

# ─── TEG Web App — Start Backend & Frontend in parallel ───
# Usage: ./start.sh [--backend-port 8000] [--frontend-port 3000]
#
# Requires: python3, pip, node, npm

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BACKEND_DIR="$SCRIPT_DIR/backend"
FRONTEND_DIR="$SCRIPT_DIR/frontend"
VENV_DIR="$SCRIPT_DIR/.venv"

BACKEND_PORT=8000
FRONTEND_PORT=3000

# ─── Parse arguments ───
while [[ $# -gt 0 ]]; do
  case "$1" in
    --backend-port)  BACKEND_PORT="$2"; shift 2 ;;
    --frontend-port) FRONTEND_PORT="$2"; shift 2 ;;
    *) echo "Unknown option: $1"; exit 1 ;;
  esac
done

# ─── Colors ───
BLUE='\033[0;34m'
ORANGE='\033[0;33m'
GREEN='\033[0;32m'
RED='\033[0;31m'
NC='\033[0m'

log_blue()   { echo -e "${BLUE}[backend]${NC}  $1"; }
log_orange() { echo -e "${ORANGE}[frontend]${NC} $1"; }
log_green()  { echo -e "${GREEN}✓${NC} $1"; }
log_error()  { echo -e "${RED}✗${NC} $1"; }

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

  # Install dependencies
  log_blue "Installing Python dependencies..."
  pip install --upgrade pip -q
  if [[ -f "$BACKEND_DIR/requirements.txt" ]]; then
    pip install -r "$BACKEND_DIR/requirements.txt" -q
  else
    log_blue "requirements.txt not found, installing minimal deps"
    pip install Django djangorestframework django-cors-headers -q
  fi

  # Run migrations
  log_blue "Running migrations..."
  python "$BACKEND_DIR/manage.py" migrate --run-syncdb 2>&1 | tail -1

  # Start server
  log_blue "Starting Django on http://127.0.0.1:$BACKEND_PORT"
  python "$BACKEND_DIR/manage.py" runserver "127.0.0.1:$BACKEND_PORT" 2>&1 | sed "s/^/  [backend]  /" &
  PIDS+=($!)
}

# ─── Frontend setup ───
start_frontend() {
  log_orange "Setting up frontend..."

  cd "$FRONTEND_DIR"

  # Install node modules if missing
  if [[ ! -d "node_modules" ]]; then
    log_orange "Installing npm dependencies..."
    npm install
  fi

  # Start dev server
  log_orange "Starting Next.js on http://localhost:$FRONTEND_PORT"
  PORT=$FRONTEND_PORT npm run dev 2>&1 | sed "s/^/  [frontend] /" &
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
