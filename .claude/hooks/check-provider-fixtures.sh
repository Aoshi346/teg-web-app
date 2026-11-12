#!/usr/bin/env bash
# check-provider-fixtures.sh — PreToolUse (matcher «Bash»). OPCIONAL: no viene registrado (AN-19,
# cosechado de cold_calling_coach). Impide correr un test «live» sin la clave real del proveedor.
#
# POR QUÉ. `rules/external-provider-dependency.md` §3 tiene tres respuestas cuando falta una clave
# (degradar / bloquear / rechazar), y la que más se salta es la del medio: medir un umbral (WER,
# latencia, acierto) contra fixtures grabadas y publicarlo como si midiera al proveedor. Esto cierra
# el caso mecánico: un test marcado live corriendo sin credencial. Los tests contra fixtures pasan.
#
# El manifiesto, en el proyecto: `.claude/PROVIDERS.json`
#   {"providers": [{"interface": "stt", "env": "DEEPGRAM_API_KEY"}, …]}
# Sin manifiesto, el hook calla. Solo mira si la variable EXISTE, nunca la lee ni la imprime.
#
# La versión de origen leía `$CLAUDE_TOOL_INPUT` (no existe): aquí, `tool_input.command` de stdin.
# Registro: {"matcher": "Bash", "hooks": [{"type": "command",
#   "command": "bash \"$CLAUDE_PROJECT_DIR/.claude/hooks/check-provider-fixtures.sh\""}]}
set -uo pipefail
INPUT="$(cat)"
case "$INPUT" in *pytest*) ;; *) exit 0 ;; esac
ROOT="${CLAUDE_PROJECT_DIR:-$(pwd)}"
MANIFEST="$ROOT/.claude/PROVIDERS.json"
[ -f "$MANIFEST" ] || exit 0
command -v python3 >/dev/null 2>&1 || exit 0
MISSING=$(printf '%s' "$INPUT" | python3 -c '
import json, os, re, sys
try:
    cmd = (json.loads(sys.stdin.read() or "{}").get("tool_input") or {}).get("command", "")
except ValueError:
    sys.exit(0)
if not re.search(r"\bpytest\b", cmd) or not re.search(r"test_live|--live\b|-m\s+[\x27\x22]?live\b", cmd):
    sys.exit(0)
try:
    data = json.load(open(sys.argv[1], encoding="utf-8"))
except (OSError, ValueError):
    sys.exit(0)
for p in data.get("providers", []):
    if p.get("env") and not os.environ.get(p["env"]):
        print("  " + str(p.get("interface", "?")) + " → falta " + p["env"])
' "$MANIFEST")
[ -z "$MISSING" ] && exit 0
{
  echo "BLOQUEADO: has pedido un test «live» y faltan credenciales reales:"
  echo "$MISSING"
  echo "Una de dos: exporta la clave real, o corre la variante contra fixtures (sin -m live / test_live_*)."
  echo "Lo que no vale: dar por bueno un umbral medido sobre fixtures (external-provider-dependency.md §3)."
} >&2
exit 2
