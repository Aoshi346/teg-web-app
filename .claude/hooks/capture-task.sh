#!/bin/bash
# capture-task.sh — UserPromptSubmit: registra CADA petición del Usuario y recuerda las pendientes.
#
# POR QUÉ EXISTE. Palabras del Usuario: «se te está olvidando todo, yo voy diciéndote cosas y se van
# perdiendo». Cierto. Y la causa no era el descuido: no había ningún sitio donde quedara escrita cada
# petición, así que recordarlas dependía del agente entre veinte tareas — y eso falla siempre.
#
# POR QUÉ UN HOOK Y NO UNA SKILL. Una skill hay que acordarse de invocarla, que es el mismo fallo.
# Esto corre SIEMPRE (`rules/layer-decision.md`: si el coste de ignorarlo es alto, baja de capa).
#
# DOS COSAS, en este orden:
#   1. Registra la petición en el pending-tasks.md del PLAN activo (no en la raíz: decisión del Usuario).
#   2. Reinyecta las pendientes en el contexto del turno, para que estén delante y no en la memoria.
#
# LO QUE NO HACE: decidir qué va a background. Eso lo decide el Usuario; el hook solo anota.

DIR="${CLAUDE_PROJECT_DIR:-$(pwd)}"
REG="$DIR/.claude/scripts/tasks_registry.py"
[ -f "$REG" ] || exit 0
# Con datos personales o de salud REALES en desarrollo (CONFIGURACION.yaml, sub-ola 2.29, SE-41) no se
# escribe cada prompt en un fichero que leen todas las sesiones: el prompt puede llevar esos datos.
# Lo decidió a mano develop (EvoPreven); aquí es el defecto, aunque el hook siga registrado.
grep -qE "^[[:space:]]*datos_reales_desarrollo:[[:space:]]*[\"']?s[ií]" \
  "$DIR/.claude/CONFIGURACION.yaml" 2>/dev/null && exit 0

# OPT-IN por proyecto (MO-19): solo registra donde CONFIGURACION.yaml lo activa con `capture_task: si`.
# Antes corría en TODO derivado y vertía cada prompt en un fichero compartido; ahora se enciende a
# propósito. Sin el fichero o sin la clave: no registra ni reinyecta nada.
grep -qE "^[[:space:]]*capture_task:[[:space:]]*[\"']?s[ií]" \
  "$DIR/.claude/CONFIGURACION.yaml" 2>/dev/null || exit 0

PROMPT=$(cat)   # UserPromptSubmit entrega el prompt por stdin
# La redacción (secretos + datos personales) la hace `tasks_registry.py add` con la librería compartida
# `scripts/redactar.py` (U.06) ANTES de escribir en pending-tasks.md; si no puede importarla, no registra.

# El prompt puede venir como JSON o como texto plano según el harness: se acepta lo que llegue.
TXT=$(printf '%s' "$PROMPT" | python3 -c "
import json,sys
raw = sys.stdin.read()
try:
    d = json.loads(raw)
    print(d.get('prompt') or d.get('user_prompt') or d.get('text') or raw)
except Exception:
    print(raw)
" 2>/dev/null)

# No se registran los saludos ni las respuestas de una palabra: llenarían el fichero de ruido y
# el ruido es lo que hace que un registro deje de leerse.
LIMPIO=$(printf '%s' "$TXT" | tr -d '\n' | sed 's/^[[:space:]]*//;s/[[:space:]]*$//')
N=${#LIMPIO}
# Las NOTIFICACIONES DEL SISTEMA no son peticiones del Usuario y no deben entrar en el registro:
# ensucian la lista con ruido de máquina y hacen que se deje de leer, que es lo contrario de para
# lo que existe. Se detectan por su envoltorio, que es literal y estable.
# Los INFORMES DE SUBAGENTES también llegan como turno (`<agent-message …>` + «[Subagent hand-back]»)
# y tampoco son peticiones: en aquila-erp (2026-09-30) siete agentes en paralelo metieron nueve
# informes en el registro como si fueran tareas del Usuario.
ES_SISTEMA=0
# Los informes de subagentes (`<agent-message>`, «[Subagent hand-back]») tampoco: se colaban como
# peticiones y se reinyectaban en cada turno (125 en 7 proyectos, 2026-10-17).
printf '%s' "$LIMPIO" | grep -qE '<task-notification>|<system-reminder>|<cross-session-message|\[Cross-session|SYSTEM NOTIFICATION|\[SYSTEM|<agent-message|\[Subagent hand-back\]' && ES_SISTEMA=1

if [ "$ES_SISTEMA" -eq 0 ] && [ "$N" -ge 25 ] && ! printf '%s' "$LIMPIO" | grep -qiE '^(si|no|vale|ok|gracias|sí|dale|perfecto|adelante|correcto)[.! ]*$'; then
    python3 "$REG" add "$LIMPIO" >/dev/null 2>&1
fi

# Recordatorio de lo pendiente. Va a stdout, así que entra en el contexto del turno.
python3 "$REG" list --max 10 2>/dev/null

# Y el recordatorio de refinar: el hook registra el texto CRUDO a propósito —es instantáneo y no
# puede fallar—, pero una petición copiada tal cual, con sus erratas y mezclando tres cosas, se
# lee mal dentro de dos días. Refinar es trabajo del TL al ponerse con ella, y este aviso existe
# porque si no, no se hace.
PEND=$(python3 "$REG" list --max 30 2>/dev/null | grep -c '^  - \[ \]')
if [ "${PEND:-0}" -ge 3 ]; then
  echo "   ↳ y REFLÉJALA en la lista de tareas: TaskCreate al empezarla, TaskUpdate(completed) al cerrarla."
  echo "     Los dos sitios: el fichero persiste entre sesiones, la lista se ve en Ctrl+T mientras trabajas."
  echo "   ↳ al ponerte con una: python3 .claude/scripts/tasks_registry.py refine <id> \"<qué se pide, en claro>\""
  echo "     y al terminarla:     python3 .claude/scripts/tasks_registry.py done <id> --nota \"<qué se hizo>\""
fi

exit 0
