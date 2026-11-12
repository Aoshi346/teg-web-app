#!/usr/bin/env bash
# Smoke: los instrumentos del cruce template↔proyecto ABORTAN cuando no pueden medir
# (rules/verification.md §«El instrumento que no puede medir debe ABORTAR»).
# Caso real, 2026-09-28 en aiatech-web: template_diff.py daba «CORE: al día» comparándose consigo
# mismo, y audit_sistema_ia.py daba «cosechable 184» con un template inexistente. Ambos, exit 0.
set -u
R="$(cd "$(dirname "$0")/../../.." && pwd)"; S="$R/.claude/scripts"; fallos=0
esperar2() { "$@" >/dev/null 2>&1; c=$?; if [ $c -eq 2 ]; then echo "  ok   exit 2 · ${*: -3}"; else echo "  FALLO exit $c (esperaba 2) · $*"; fallos=$((fallos+1)); fi; }
echo "template-ausente:"
esperar2 python3 "$S/template_diff.py"     "$R" --core
esperar2 python3 "$S/template_diff.py"     "$R" --core --template /no/existe
esperar2 python3 "$S/audit_sistema_ia.py"  "$R"
esperar2 python3 "$S/audit_sistema_ia.py"  "$R" --template /no/existe
[ $fallos -eq 0 ] && echo "OK: 4/4 abortan" || { echo "FALLAN $fallos"; exit 1; }
