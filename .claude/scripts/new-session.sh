#!/bin/bash
# Creates a new SpecKit session with templates
# Vive en .claude/scripts/ desde el 2026-10-20 (antes en scripts/ de la raíz, que no viajaba a los
# derivados con .claude/). Se ejecuta desde la raíz del proyecto: las rutas .specify/ son relativas.

if [ -z "$1" ] || [ -z "$2" ]; then
    echo "Usage: .claude/scripts/new-session.sh <PREFIX> <NAME>   (desde la raíz del proyecto)"
    echo "Example: .claude/scripts/new-session.sh BM 'Mejoras generales'"
    exit 1
fi

PREFIX=$1
NAME=$2

# Find next number for this prefix
LAST_NUM=$(ls -d .specify/sessions/${PREFIX}-* 2>/dev/null | sed "s/.*${PREFIX}-\([0-9]*\).*/\1/" | sort -n | tail -1)
NEXT_NUM=$((${LAST_NUM:-0} + 1))

SESSION_ID="${PREFIX}-${NEXT_NUM}"
SESSION_DIR=".specify/sessions/${SESSION_ID} - ${NAME}"

# Create session directory
mkdir -p "$SESSION_DIR"

# Copy templates
cp .specify/templates/spec-template.md "$SESSION_DIR/spec.md"
cp .specify/templates/plan-template.md "$SESSION_DIR/plan.md"
cp .specify/templates/tasks-template.md "$SESSION_DIR/tasks.md"

# Replace placeholders
sed -i "s/\[NOMBRE DE LA SESIÓN\]/${NAME}/g" "$SESSION_DIR"/*.md
sed -i "s/\[ID\]/${SESSION_ID}/g" "$SESSION_DIR"/*.md
sed -i "s/YYYY-MM-DD/$(date +%Y-%m-%d)/g" "$SESSION_DIR"/*.md

echo "✅ Session created: $SESSION_DIR"
echo ""
echo "Next steps:"
echo "1. Edit spec.md with requirements"
echo "2. Create plan.md with technical approach"
echo "3. Create tasks.md with actionable items"
echo "4. Implement following tasks.md"
