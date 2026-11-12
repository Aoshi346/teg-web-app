#!/bin/bash
# List all SpecKit sessions

echo "📋 SpecKit Sessions"
echo "==================="
echo ""

if [ -d ".specify/sessions" ]; then
    for dir in .specify/sessions/*/; do
        if [ -d "$dir" ]; then
            SESSION=$(basename "$dir")
            SPEC_EXISTS=$([ -f "${dir}spec.md" ] && echo "✓" || echo "✗")
            PLAN_EXISTS=$([ -f "${dir}plan.md" ] && echo "✓" || echo "✗")
            TASKS_EXISTS=$([ -f "${dir}tasks.md" ] && echo "✓" || echo "✗")
            
            echo "📁 $SESSION"
            echo "   spec: $SPEC_EXISTS | plan: $PLAN_EXISTS | tasks: $TASKS_EXISTS"
            echo ""
        fi
    done
else
    echo "No sessions found. Create one with:"
    echo "  .claude/scripts/new-session.sh PREFIX 'Session Name'"
fi
