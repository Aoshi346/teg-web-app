#!/bin/bash
# capture-task.sh — UserPromptSubmit: registra CADA petición del Usuario y recuerda las pendientes.
#
# POR QUÉ EXISTE. Palabras del Usuario: «se te está olvidando todo, yo voy diciéndote cosas y se van
# perdiendo». Cierto. Y la causa no era el descuido: no había ningún sitio donde quedara escrita cada
# petición, así que recordarlas dependía del agente entre veinte tareas — y eso falla siempre.
#
# POR QUÉ UN HOOK Y NO UNA SKILL. Una skill hay que acordarse de invocarla, que es el mismo fallo.
# Esto corre SIEMPRE (criterio de capas del template: si el coste de ignorarlo es alto, baja de capa).
#
# DOS COSAS, en este orden:
#   1. Registra la petición en el TASKS.md del PLAN activo (no en la raíz: decisión del Usuario).
#   2. Reinyecta las pendientes en el contexto del turno, para que estén delante y no en la memoria.
#
# LO QUE NO HACE: decidir qué va a background. Eso lo decide el Usuario; el hook solo anota.

DIR="${CLAUDE_PROJECT_DIR:-$(pwd)}"
REG="$DIR/.claude/scripts/tasks_registry.py"
[ -f "$REG" ] || exit 0

PROMPT=$(cat)   # UserPromptSubmit entrega el prompt por stdin

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
ES_SISTEMA=0
printf '%s' "$LIMPIO" | grep -qE '<task-notification>|<system-reminder>|<cross-session-message|\[Cross-session|SYSTEM NOTIFICATION|\[SYSTEM' && ES_SISTEMA=1

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
