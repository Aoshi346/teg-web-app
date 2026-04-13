#!/usr/bin/env bash
# Post-edit hook: lint + typecheck the file that was just modified.
#
# Fires on PostToolUse for Edit/Write/MultiEdit.
# Reads the tool input JSON from stdin and dispatches based on file extension.
#
# - .py files  -> ruff check (from backend/)
# - .ts/.tsx   -> eslint + tsc --noEmit (from frontend/)
#
# Exit code 0 = hook OK (tool result still flows through).
# Exit code 2 = hook FAILED (blocks the tool result and shows stderr to Claude).
#
# We use exit 0 even on lint errors — we only want Claude to SEE the problem, not be blocked.
# The lint output goes to stderr which Claude reads as a hook message.

set -u

# Read the JSON event from stdin (Claude Code passes it there)
INPUT="$(cat)"

# Extract file path using python (more portable than jq, which may not be installed)
FILE_PATH="$(python3 -c "
import json, sys
try:
    data = json.loads('''$INPUT''')
    # PostToolUse payload: tool_input may hold file_path, or edits[*].file_path
    ti = data.get('tool_input', {})
    fp = ti.get('file_path')
    if not fp and 'edits' in ti and ti['edits']:
        fp = ti['edits'][0].get('file_path')
    print(fp or '')
except Exception:
    print('')
" 2>/dev/null)"

if [[ -z "$FILE_PATH" ]]; then
  exit 0
fi

# Only act on files inside this repo
REPO_ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
case "$FILE_PATH" in
  "$REPO_ROOT"/*) ;;
  *) exit 0 ;;
esac

REL="${FILE_PATH#$REPO_ROOT/}"

# --- Python files ---
if [[ "$FILE_PATH" == *.py ]]; then
  if [[ "$REL" == backend/* ]]; then
    cd "$REPO_ROOT/backend" || exit 0
    if command -v ruff >/dev/null 2>&1; then
      # Report issues via stderr so Claude sees them; do not block.
      ruff check "${FILE_PATH#$REPO_ROOT/backend/}" 1>&2 || true
    else
      echo "hook: ruff not installed — skipping Python lint for $REL" 1>&2
    fi
  fi
  exit 0
fi

# --- TypeScript / TSX files ---
if [[ "$FILE_PATH" == *.ts || "$FILE_PATH" == *.tsx ]]; then
  if [[ "$REL" == frontend/* ]]; then
    cd "$REPO_ROOT/frontend" || exit 0
    REL_IN_FRONTEND="${FILE_PATH#$REPO_ROOT/frontend/}"

    # ESLint on the single file — fast
    if [[ -x node_modules/.bin/eslint ]]; then
      node_modules/.bin/eslint "$REL_IN_FRONTEND" 1>&2 || true
    else
      echo "hook: eslint not installed — run 'npm install' in frontend/" 1>&2
    fi

    # Type-check the whole project — tsc --noEmit is fast enough incrementally
    if [[ -x node_modules/.bin/tsc ]]; then
      node_modules/.bin/tsc --noEmit 1>&2 || true
    else
      echo "hook: typescript not installed — run 'npm install' in frontend/" 1>&2
    fi
  fi
  exit 0
fi

exit 0
