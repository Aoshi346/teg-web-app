#!/bin/bash
# audit-incoming-config.sh — SessionStart hook (HAR-3)
#
# Audita la configuración EJECUTABLE que llega con el repo: `.claude/settings.json`,
# `.claude/settings.local.json` y `.mcp.json` — incluidos los de repos vendorizados en
# `resources/`. Nuestro flujo ES el vector: copiamos `.claude/` entre proyectos
# (skill create-agent, paso 3: staging) y vendorizamos repos de GitHub.
#
# Modelo de amenaza: CVE-2025-59536 (hooks del repo ejecutándose antes del diálogo de confianza
# + auto-aprobación de MCP del proyecto) y CVE-2026-21852 (override de ANTHROPIC_BASE_URL/apiUrl
# que filtra la API key). Detalle: .claude/rules/agent-security.md
#
# SE-47 (2026-10-22): la cobertura ya no se limita a settings y .mcp.json. Los hooks (`.claude/hooks/`),
# las skills, los agentes, los comandos y los plugins (`.claude-plugin/`) ejecutan código igual y no
# cambian `settings.json`: un hook manipulado pasaba sin aviso (ASI05). De esa parte se encarga
# `scripts/audit_config.py` (huella por fichero, qué cambió, patrones fuertes y débiles); la de
# settings/.mcp sigue aquí, con su filtro de reglas de permiso. Su huella es otra (`.incoming-config-
# ejecutables.tsv`) para no pisar la de settings.
#
# NO BLOQUEA: avisa por stdout y sale 0 siempre. Es un pattern-matcher, no un muro.
# Solo grita cuando la config ha CAMBIADO desde la última sesión (evita fatiga de alerta).

ROOT="${CLAUDE_PROJECT_DIR:-$(pwd)}"
BASELINE="$ROOT/.claude/.incoming-config.sha256"
TAG="[audit-incoming-config]"

# --- 0. Hooks, skills, agentes, comandos y plugins (SE-47)
AUDIT_PY="$ROOT/.claude/scripts/audit_config.py"
if command -v python3 >/dev/null 2>&1 && [ -f "$AUDIT_PY" ]; then
    if [ "$1" = "--force" ]; then FORCE=--force; else FORCE=""; fi
    python3 "$AUDIT_PY" auditar --root "$ROOT" --baseline "$ROOT/.claude/.incoming-config-ejecutables.tsv" $FORCE
fi

# --- 1. Recolectar los ficheros de config ejecutable (búsqueda acotada: rápido en repos grandes)
FILES=$(find "$ROOT" -maxdepth 4 \
    \( -name .git -o -name node_modules -o -name venv -o -name .venv -o -name dist -o -name build \) -prune -o \
    \( -name '.mcp.json' -o -path '*/.claude/settings.json' -o -path '*/.claude/settings.local.json' \) \
    -print 2>/dev/null)

[ -z "$FILES" ] && exit 0

# --- 2. ¿Ha cambiado algo desde la última sesión?
CURRENT=$(echo "$FILES" | xargs sha256sum 2>/dev/null | sha256sum | cut -d' ' -f1)
PREVIOUS=$(cat "$BASELINE" 2>/dev/null)
mkdir -p "$(dirname "$BASELINE")" && echo "$CURRENT" > "$BASELINE"

UNCHANGED=0
[ "$CURRENT" = "$PREVIOUS" ] && UNCHANGED=1

# --- 3. Escanear patrones de riesgo
# NOTA: las líneas que son REGLAS DE PERMISO (`"Bash(curl* | bash*)"` en un allow/ask/deny) son
# política, no ejecución — se filtran o el propio deny baseline del template se autodenuncia
# cada sesión. Lo que sí ejecuta: los `"command"` de hooks y los `"command"`/`"args"` de MCP.
NOT_A_RULE='"(Bash|Read|Write|Edit|WebFetch|Agent)\('

# Una pasada de grep por patrón sobre TODOS los ficheros (no una por fichero): 5 procesos, no 5×N.
mapfile -t TARGETS <<< "$FILES"

scan() { # scan <etiqueta> <regex> <nota> [filtrar-reglas]
    local out
    out=$(grep -nHE "$2" "${TARGETS[@]}" 2>/dev/null)
    [ -n "$4" ] && out=$(echo "$out" | grep -vE "$NOT_A_RULE")
    # Ni las notas (`"_comment…"`) ni una clave puesta a false son una defensa bajada
    out=$(echo "$out" | grep -vE '^[^:]*:[0-9]+:[[:space:]]*"_(comment|nota)|enableAllProjectMcpServers"[[:space:]]*:[[:space:]]*false')
    [ -z "$out" ] && return 0
    echo "$out" | sed "s|^$ROOT/||" | while IFS= read -r hit; do
        [ -n "$hit" ] && echo "  $1  $hit${3:+  <- $3}"
    done
}

FINDINGS=$(
    # ejecución remota de código
    scan RCE '(curl|wget)[^"]*\|[[:space:]]*(ba)?sh' '' filtrar
    # auto-aprobación de servidores MCP del proyecto (parte de CVE-2025-59536)
    scan MCP 'enableAllProjectMcpServers' 'auto-aprueba los MCP del repo'
    # redirección de la API / credenciales (CVE-2026-21852)
    scan API 'ANTHROPIC_BASE_URL|ANTHROPIC_AUTH_TOKEN|ANTHROPIC_API_KEY|"apiUrl"|apiKeyHelper' 'redirige/expone credenciales' filtrar
    # hooks con egress: solo líneas de comando de hook (evita falsos positivos de la allowlist)
    scan NET '"command"[^"]*"[^"]*(curl|wget|nc |ncat|scp |ssh |/dev/tcp)' 'hook que sale a red'
    # desactivación de las defensas
    scan PRM 'dangerously-skip-permissions|"bypassPermissions"|"disableAllHooks"' 'baja las defensas' filtrar
)

# --- 4. Reportar
if [ -z "$FINDINGS" ]; then
    [ "$UNCHANGED" = "0" ] && echo "$TAG config entrante revisada, sin patrones de riesgo ($(echo "$FILES" | wc -l) ficheros)."
    exit 0
fi

if [ "$UNCHANGED" = "1" ]; then
    echo "$TAG $(echo "$FINDINGS" | wc -l) aviso(s) ya conocido(s), sin cambios desde la última sesión."
    echo "$TAG revisar de nuevo: bash .claude/hooks/audit-incoming-config.sh --force"
    [ "$1" != "--force" ] && exit 0
fi

echo "$TAG ⚠️  CONFIG EJECUTABLE CON PATRONES DE RIESGO — revísala antes de trabajar:"
echo "$FINDINGS"
echo "$TAG  RCE=ejecución remota · MCP=auto-aprobación · API=credenciales · NET=egress · PRM=permisos"
echo "$TAG  Contexto y qué hacer: .claude/rules/agent-security.md §4"

exit 0
