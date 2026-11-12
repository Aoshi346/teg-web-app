#!/bin/bash
# Hook: PreToolUse (matcher "Write|Edit|NotebookEdit") — bloquea escrituras FUERA de una lista
# blanca de directorios.
#
# ⚠️ NO REGISTRADO en settings.json a propósito (ND-3, 2026-08-08). Registrarlo cambia el
#    comportamiento de todas las sesiones y eso requiere aprobación aparte. Para activarlo:
#
#      "hooks": {
#        "PreToolUse": [
#          { "matcher": "Write|Edit|NotebookEdit",
#            "hooks": [{ "type": "command",
#                        "command": "bash \"$CLAUDE_PROJECT_DIR/.claude/hooks/pre-write-guard.sh\"" }] }
#        ]
#      }
#
# POR QUÉ EXISTE
#   `permissions.deny` en settings.json ya bloquea rutas, pero parte del sitio equivocado para un
#   rol no técnico: es una lista de prohibiciones, y es mucho más fácil olvidarse de PROHIBIR algo
#   que olvidarse de PERMITIRLO. Este hook aplica la política al revés —lista blanca— y la aplica
#   por su cuenta: si la plantilla de permisos se despliega con un permiso de más, el hook sigue
#   parando la escritura. Es la segunda capa, no la primera.
#
#   Vale también para NUESTRAS sesiones: acota el radio de una prompt injection que consiga que el
#   agente escriba donde no debe (`rules/agent-security.md` §ASI01/ASI05).
#
# LÍMITE HONESTO
#   Esto cubre las tools de escritura de ficheros. **NO cubre `Bash`**: un `echo … > fichero` o un
#   `sed -i` pasa por delante sin tocar este hook. Para eso hace falta además acotar Bash en
#   `permissions` (la plantilla `settings.nondev-role.json` lo hace: deny de Bash con allowlist
#   estrecha). Un guard de escritura sin Bash acotado da falsa sensación de seguridad.
#
# CONTRATO
#   Claude Code pasa la info por STDIN como JSON, no por variables de entorno:
#     {"tool_name":"Write","tool_input":{"file_path":"/ruta/al/fichero"}, ...}
#   exit 0 = permitido · exit 2 = BLOQUEADO (stderr vuelve al agente como motivo)
#
# CONFIGURACIÓN
#   CLAUDE_WRITE_ALLOW  lista de rutas permitidas separadas por ':' (relativas al proyecto o
#                       absolutas). Si no se define, se usa DEFAULT_ALLOW de abajo.
#   CLAUDE_WRITE_DENY   lista de rutas prohibidas SIEMPRE, aunque caigan dentro de un allow.
#
#   Ejemplo para un rol de marketing:
#     export CLAUDE_WRITE_ALLOW="drafts:content:.docs/marketing"

set -uo pipefail

PROJECT_DIR="${CLAUDE_PROJECT_DIR:-$(pwd)}"

# Por defecto: solo escritorio de trabajo del rol. Ajusta por proyecto vía CLAUDE_WRITE_ALLOW.
DEFAULT_ALLOW="drafts:content:.docs:/tmp"

# Prohibido siempre, aunque una ruta permitida lo contenga. La config que el agente EJECUTA no se
# edita desde una sesión de rol acotado (`rules/agent-security.md` §2: lo security-critical vive en
# el nivel de confianza más alto, nunca lo edita el nivel más bajo).
DEFAULT_DENY=".claude/settings.json:.claude/settings.local.json:.claude/hooks:.mcp.json:.git:.env"

ALLOW_LIST="${CLAUDE_WRITE_ALLOW:-$DEFAULT_ALLOW}"
DENY_LIST="${CLAUDE_WRITE_DENY:-$DEFAULT_DENY}"

# --- extraer el file_path del JSON de stdin -----------------------------------------------------
# Se usa python3 con `-c` (NO heredoc: el heredoc ocuparía stdin y el JSON nunca llegaría — mismo
# gotcha documentado en audit-log.sh).
INPUT=$(cat)
FILE_PATH=$(printf '%s' "$INPUT" | python3 -c '
import json, sys
try:
    d = json.load(sys.stdin)
except Exception:
    print(""); sys.exit(0)
ti = d.get("tool_input") or {}
# Write/Edit usan file_path; NotebookEdit usa notebook_path
print(ti.get("file_path") or ti.get("notebook_path") or "")
' 2>/dev/null)

# Sin ruta que juzgar (tool inesperada o JSON raro) → no es cosa nuestra, dejamos pasar.
[ -z "$FILE_PATH" ] && exit 0

# --- normalizar a ruta absoluta sin symlinks ni ".." --------------------------------------------
# Se resuelve ANTES de comparar: sin esto, `drafts/../../etc/passwd` pasaría el prefijo "drafts".
# El fichero puede no existir todavía (es una escritura), así que se resuelve el directorio padre.
case "$FILE_PATH" in
  /*) ABS="$FILE_PATH" ;;
   *) ABS="$PROJECT_DIR/$FILE_PATH" ;;
esac
PARENT=$(dirname "$ABS")
REAL_PARENT=$(cd "$PARENT" 2>/dev/null && pwd -P) || REAL_PARENT=""
if [ -n "$REAL_PARENT" ]; then
  ABS="$REAL_PARENT/$(basename "$ABS")"
else
  # El directorio padre no existe aún: colapsamos ".." textualmente para no dejar el hueco abierto.
  ABS=$(printf '%s' "$ABS" | python3 -c 'import os,sys; print(os.path.normpath(sys.stdin.read().strip()))')
fi

REAL_PROJECT=$(cd "$PROJECT_DIR" 2>/dev/null && pwd -P) || REAL_PROJECT="$PROJECT_DIR"

# --- helper: ¿está ABS dentro de alguna de las rutas de la lista? -------------------------------
matches_list() {
  local list="$1" entry base
  local IFS=:
  for entry in $list; do
    [ -z "$entry" ] && continue
    case "$entry" in
      /*) base="$entry" ;;
       *) base="$REAL_PROJECT/$entry" ;;
    esac
    base=$(printf '%s' "$base" | python3 -c 'import os,sys; print(os.path.normpath(sys.stdin.read().strip()))')
    # Coincidencia exacta o descendiente (con "/" para que "drafts" no matchee "drafts-privados")
    if [ "$ABS" = "$base" ] || case "$ABS" in "$base"/*) true ;; *) false ;; esac; then
      MATCHED="$entry"
      return 0
    fi
  done
  return 1
}

MATCHED=""

if matches_list "$DENY_LIST"; then
  echo "BLOQUEADO por pre-write-guard: '$FILE_PATH' cae en una ruta PROHIBIDA ('$MATCHED')." >&2
  echo "Esa ruta es configuración que el agente ejecuta; no se edita desde esta sesión." >&2
  echo "Si el cambio hace falta de verdad, pídelo al responsable técnico (rules/human-role-layers.md)." >&2
  exit 2
fi

if matches_list "$ALLOW_LIST"; then
  exit 0
fi

echo "BLOQUEADO por pre-write-guard: '$FILE_PATH' está FUERA de los directorios permitidos." >&2
echo "Permitidos: ${ALLOW_LIST//:/, }" >&2
echo "Escribe dentro de una de esas rutas, o pide al responsable técnico que amplíe" >&2
echo "CLAUDE_WRITE_ALLOW si el trabajo lo necesita de verdad." >&2
exit 2
