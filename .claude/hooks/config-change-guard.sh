#!/usr/bin/env bash
# ══════════════════════════════════════════════════════════════════════════════════════════════
# config-change-guard.sh — ConfigChange (SE-47, 2026-10-22). Se dispara cuando, DURANTE la sesión,
# cambia un settings, una skill o una política: el momento en que un agente (o un fichero que leyó)
# intenta bajarse las defensas sin que nadie mire. `audit-incoming-config.sh` solo ve la config al
# ARRANCAR; este ve el cambio EN VIVO y puede pararlo.
#
# Entrada (stdin, JSON): {"hook_event_name":"ConfigChange","source":"project_settings|local_settings|
#   user_settings|policy_settings|skills","file_path":"…"}. Claude Code enseña a los hooks una COPIA
#   del contenido nuevo, y si el cambio se bloquea el fichero real no se toca.
# Salida: exit 2 BLOQUEA el cambio (stderr vuelve al agente) · exit 0 lo deja pasar.
#
# Qué bloquea (`scripts/audit_config.py revisar`): `disableAllHooks`, `skipDangerousModePermissionPrompt`,
#   `enableAllProjectMcpServers: true`, `defaultMode: bypassPermissions`, `ANTHROPIC_BASE_URL`/token en
#   `env`, `apiKeyHelper`, y hooks o skills con `curl|sh`, `/dev/tcp`, shell inversa. NO bloquea lo
#   demás: un hook que no puede distinguir un cambio legítimo de uno malo, y bloquea los dos, se
#   acaba quitando. Política gestionada: no se puede bloquear, solo avisa.
# Su límite, dicho: es un buscador de patrones y se rodea partiendo la cadena. Si el Usuario SÍ quiere
#   el cambio, lo hace él fuera de la sesión (o con la sesión sin este hook).
# Si no hay python3, no puede juzgar: deja pasar y lo dice por stderr (un guard roto que bloqueara TODO
#   se acabaría quitando).
# ══════════════════════════════════════════════════════════════════════════════════════════════
AQUI="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
RAIZ="${CLAUDE_PROJECT_DIR:-$(cd "$AQUI/../.." && pwd)}"
LOG="$RAIZ/.claude/config-changes.log"
ENTRADA="$(cat)"

if ! command -v python3 >/dev/null 2>&1 || [ ! -f "$AQUI/../scripts/audit_config.py" ]; then
  echo "[config-change-guard] sin python3 o sin audit_config.py: no puedo revisar el cambio." >&2
  exit 0
fi

# Un solo python para sacar los dos campos (sin jq: no está en todas las máquinas)
CAMPOS="$(printf '%s' "$ENTRADA" | python3 -c '
import json, sys
try:
    d = json.load(sys.stdin)
except Exception:
    sys.exit(0)
print(d.get("source") or "")
print(d.get("file_path") or "")' 2>/dev/null)"
FUENTE="$(printf '%s\n' "$CAMPOS" | sed -n 1p)"
FICHERO="$(printf '%s\n' "$CAMPOS" | sed -n 2p)"
[ -z "$FICHERO" ] && exit 0

python3 "$AQUI/../scripts/audit_config.py" revisar "$FICHERO" --source "$FUENTE"
RC=$?
if [ "$RC" -eq 2 ]; then
  mkdir -p "$(dirname "$LOG")" 2>/dev/null
  printf '%s\t%s\t%s\tbloqueado\n' "$(date -Is)" "$FUENTE" "$FICHERO" >> "$LOG" 2>/dev/null
fi
exit "$RC"
