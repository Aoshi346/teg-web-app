#!/usr/bin/env bash
# ══════════════════════════════════════════════════════════════════════════════════════════════
# yolo-politica.sh — UserPromptSubmit: si el modo YOLO del dashboard está activo, se lo dice al
# agente en cada turno.
#
# POR QUÉ EXISTE (T-101). El botón «🚀 Modo yolo» del dashboard guarda la política del plan en
# `report.json → meta.yolo` (qué items, qué clase de trabajo, hasta dónde con git) y, desde T-101,
# cambia además los permisos del proyecto. Pero la POLÍTICA solo servía si alguien copiaba la
# instrucción y la pegaba: ningún mecanismo la leía. Un interruptor que el agente no ve no es un
# interruptor. Esto la inyecta, y calla cuando está apagada.
#
# QUÉ NO HACE: no concede nada. Los permisos los pone settings.json; esto solo informa. Y recuerda
# lo que NO se salta ni con el yolo al máximo (governance.md §2).
#
# NO BLOQUEA: exit 0 siempre. Si falta el plan o el report.json, calla.
# Registro (ensure_hooks.py lo añade):
#   {"type":"command","command":"bash \"$CLAUDE_PROJECT_DIR/.claude/hooks/yolo-politica.sh\""}
# ══════════════════════════════════════════════════════════════════════════════════════════════
set -uo pipefail
cat >/dev/null 2>&1 || true          # el prompt llega por stdin; aquí no se usa
DIR="${CLAUDE_PROJECT_DIR:-$(git rev-parse --show-toplevel 2>/dev/null || pwd)}"
REG="$DIR/.claude/scripts/tasks_registry.py"
[ -f "$REG" ] || exit 0

CLAUDE_PROJECT_DIR="$DIR" timeout 4 python3 - "$REG" <<'PY' 2>/dev/null || true
import importlib.util, json, os, sys
spec = importlib.util.spec_from_file_location("tr", sys.argv[1])
tr = importlib.util.module_from_spec(spec); spec.loader.exec_module(tr)
rj = os.path.join(os.path.dirname(tr.RUTA), "report.json")
if not os.path.exists(rj):
    sys.exit(0)
y = ((json.load(open(rj, encoding="utf-8")).get("meta") or {}).get("yolo") or {})
if not y.get("activo"):
    sys.exit(0)
alc = {"aprobados": "lo aprobado (por ti o recomendado por el revisor)",
       "aprobados-duda": "lo aprobado + lo que el revisor dejó en duda",
       "todo": "cualquier item pendiente"}.get(y.get("alcance"), y.get("alcance"))
tip = {"mecanico": "solo mecánico y verificable", "refactor": "mecánico + refactors con plan previo",
       "todo": "cualquier trabajo, incluida lógica nueva"}.get(y.get("tipo"), y.get("tipo"))
git = "commit por lote en la rama" if y.get("git") == "commit" else "no toca git"
plan = os.path.basename(os.path.dirname(rj))
print(f"🚀 MODO YOLO ACTIVO desde el dashboard ({y.get('actualizado') or '?'}) · plan {plan}: "
      f"alcance {alc} · {tip} · {git}. Ejecuta sin preguntar dentro de eso. "
      "Sigue PROHIBIDO sin aprobación (governance.md §2): push, merge a main, deploy, migraciones "
      "destructivas, borrado de datos, gasto externo y dependencias del sistema.")
PY
exit 0
