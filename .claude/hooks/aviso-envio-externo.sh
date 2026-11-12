#!/usr/bin/env bash
# ══════════════════════════════════════════════════════════════════════════════════════════════
# aviso-envio-externo.sh — PreToolUse (matcher «Bash|Artifact|mcp__.*»). En un proyecto DELICADO,
# pide confirmación antes de que material del cliente salga a un servicio externo; en los demás,
# avisa de lo que ya se sabe que envía fuera.
#
# POR QUÉ ES UN HOOK Y NO UN PÁRRAFO (rules/layer-decision.md, pregunta 1): mandar el logo, la marca
# o los datos de un cliente a un tercero sin su permiso no se arregla después. Cosechado de fitapp
# (T-070: los generadores de una skill de diseño de terceros mandaban la marca a Gemini, AtlasCloud o
# MuAPI), generalizado en la sub-ola 2.29 de la revisión integral (SE-40). Un marcador explícito
# decide UNA vez por proyecto; preguntar en cada envío a todos los proyectos cansaría y se acabaría
# contestando que sí sin leer.
#
# «DELICADO» = .claude/proyecto-delicado.md existe (su primera línea con texto es el motivo; lo
# rellena la skill `arrancar` en la fase de ética) · o .claude/CONFIGURACION.yaml responde
# `datos_sensibles: salud` o `datos_reales_desarrollo: si-…` · o el perfil de
# .docs/core/design-system.md es `web-cliente` (la marca es de un cliente) · o los documentos de
# arranque hablan de datos de salud.
#
# QUÉ MIRA
#   · lo DECLARADO en .claude/envios-externos.json: cada skill vendorizada que envía fuera declara
#     ahí sus comandos (`comandos`: regex sobre el comando de Bash) o sus tools (`herramientas`:
#     regex sobre el nombre de la tool), con qué sale y adónde (plantilla:
#     templates/envios-externos.json; procedimiento: rules/vendoring.md).
#     Delicado → pregunta. No delicado → deja pasar y avisa (systemMessage), salvo las entradas con
#     `always_ask: true`, que preguntan en cualquier proyecto (los generadores de UI/UX Pro Max, 3.66).
#   · solo en un proyecto delicado, además, lo que envía fuera sin declararlo: `curl`/`wget` que
#     SUBEN algo (-F, -T, --data @fichero…) a un host que no es local, publicar un Artifact (una
#     página en claude.ai) y las tools MCP que suben, crean, comparten o mandan
#     (`mcp__*__upload*`, `__create_file`, `__share*`, `__send*`, `__publish*`…). Pregunta.
#     Las respuestas por el canal de Telegram (la conversación con el propio Usuario), solo si
#     llevan ficheros adjuntos.
#
# LÍMITE HONESTO: mira el texto del comando y el nombre de la tool. Un envío desde dentro de un
# script, o con un cliente que no es curl/wget, no lo ve; un heredoc que solo MENCIONE la ruta de un
# generador hace que pregunte sin necesidad. Sin nadie delante (`claude -p`) el «ask» se queda en
# DENEGADO: medido el 2026-10-21 con Claude Code 2.1.306, el curl salió en `permission_denials`, no se
# ejecutó y el modelo contó el motivo; sin el marcador, el mismo curl corrió
# (_archive/2026-10-20/medicion-2.29/hook/en_vivo.txt). No es una defensa contra quien quiere sacar
# los datos: es el freno para el envío que nadie había visto.
#
# CAMINO RÁPIDO: sin envios-externos.json, una tool que no es Bash/Artifact/mcp__ o un Bash sin
# curl/wget sale 0 sin arrancar python3. FALLA CERRADO (exit 2) si el detector no puede mirar y la entrada parece un envío.
# MODO PRUEBA: --cmd "<comando>" · --tool <nombre> (sin stdin JSON).
# ══════════════════════════════════════════════════════════════════════════════════════════════
set -uo pipefail
DIR="${CLAUDE_PROJECT_DIR:-$(git rev-parse --show-toplevel 2>/dev/null || pwd)}"

if [ "${1:-}" = "--cmd" ]; then
  ENTRADA=$(printf '{"tool_name":"Bash","tool_input":{"command":%s}}' \
    "$(printf '%s' "${2:-}" | python3 -c 'import json,sys; print(json.dumps(sys.stdin.read()))')")
elif [ "${1:-}" = "--tool" ]; then
  ENTRADA=$(printf '{"tool_name":"%s","tool_input":{}}' "${2:-}")
else
  ENTRADA=$(cat)
fi

if [ ! -f "$DIR/.claude/envios-externos.json" ]; then
  case "$ENTRADA" in
    *'"Artifact"'*|*'"mcp__'*|*curl*|*wget*) ;;
    *) exit 0 ;;
  esac
fi
# FALLA CERRADO (PV-70/PV-122): `onFailure: "block"` solo cubre «el hook no arranca»; un hook que sale 0
# con el detector roto (sin python3, JSON truncado, excepción) deja pasar el envío sin decirlo. Aquí, si
# el detector no puede mirar y la entrada casa con la red ancha (la misma del camino rápido), sale 2.
# Una guarda rota que bloqueara TODO se acabaría quitando: lo que no casa con la red, pasa.
RED='"Artifact"|"mcp__|curl|wget'
roto() {
  if printf '%s' "$ENTRADA" | grep -Eq "$RED"; then
    echo "aviso-envio-externo ROTO ($1) y la entrada casa con un posible envío externo: bloqueado por si acaso. Arregla la guarda (.claude/hooks/aviso-envio-externo.sh) o confirma a mano." >&2
    exit 2
  fi
  exit 0
}
command -v python3 >/dev/null 2>&1 || roto "sin python3"
[ "${TL_GUARDA_SABOTAJE:-}" = "excepcion" ] && roto "sabotaje de prueba"

SAL=$(ENTRADA="$ENTRADA" DIR="$DIR" python3 - <<'PY'
import json, os, re, sys
from pathlib import Path

d = Path(os.environ["DIR"])
try:
    e = json.loads(os.environ.get("ENTRADA") or "{}")
except ValueError:
    sys.exit(3)                      # JSON ilegible: el envoltorio decide (falla cerrado si parece envío)
tool = str(e.get("tool_name") or "")
inp = e.get("tool_input") or {}
cmd = str(inp.get("command") or "") if tool == "Bash" else ""


def leer(p, n=None):
    try:
        return p.read_text(encoding="utf-8", errors="replace")[:n]
    except OSError:
        return ""


# ── lo declarado ─────────────────────────────────────────────────────────────────────────
declarado = []
always_ask = []                       # entradas con `always_ask: true`: preguntan en CUALQUIER proyecto
try:
    decl = json.loads(leer(d / ".claude" / "envios-externos.json") or "{}")
except ValueError:
    decl = {}
    print("aviso-envio-externo: .claude/envios-externos.json no es JSON válido; no se mira lo "
          "declarado", file=sys.stderr)
for clave, sujeto in (("comandos", cmd), ("herramientas", tool)):
    for x in decl.get(clave) or []:
        try:
            if sujeto and re.search(str(x.get("patron") or "(?!)"), sujeto):
                declarado.append(f"{x.get('que') or 'material del proyecto'} → "
                                 f"{x.get('adonde') or 'un servicio externo'}")
                if x.get("always_ask") is True:
                    always_ask.append(str(x.get("skill") or "una skill declarada"))
        except re.error:
            print(f"aviso-envio-externo: patrón inválido en envios-externos.json: {x.get('patron')}",
                  file=sys.stderr)

# ── lo que envía fuera sin declararlo (solo cuenta en un proyecto delicado) ───────────────
LOCAL = re.compile(r"(?:https?://)?(?:localhost|127\.\d+\.\d+\.\d+|\[?::1\]?|0\.0\.0\.0)(?::\d+)?(?:/|\s|$|['\"])")
SUBE = re.compile(r"(?:^|\s)(?:-T|--upload-file)(?:\s+|=)[^\s-]|(?:^|\s)(?:-F|--form|--json|--data(?:-binary|-raw|-urlencode)?|-d)"
                  r"(?:\s+|=)['\"]?(?:@|[\w-]+=@|\$\()|--post-file|--body-file")
MCP_ENVIA = re.compile(r"^mcp__.+__(?:upload|create_file|create_design|share|send|publish|post|"
                       r"forward|reply|create_draft|import)", re.I)
sin_declarar = ""
if cmd and re.search(r"\b(curl|wget)\b", cmd) and SUBE.search(cmd):
    urls = re.findall(r"https?://[^\s'\"]+", cmd)
    # curl también acepta un host sin esquema: «curl -F f=@x api.terceros.com/subir»
    urls += ["http://" + h for h in re.findall(r"(?:^|\s)((?:[\w-]+\.)+[a-z]{2,}(?::\d+)?/\S*)", cmd)
             if not re.match(r"[\w-]+\.(?:py|sh|json|txt|csv|png|pdf|zip)\b", h)]
    if urls and not all(LOCAL.match(u + " ") for u in urls):
        sin_declarar = "este comando SUBE un fichero o datos a un host externo"
elif tool == "Artifact" and str(inp.get("action") or "publish") == "publish":
    sin_declarar = "esto publica una página en claude.ai (un Artifact)"
elif tool.startswith("mcp__plugin_telegram_"):
    # El canal es la conversación con el propio Usuario: un texto no sale a un tercero. Un fichero
    # adjunto (una captura, un informe) sí puede llevar datos: ese pregunta.
    if inp.get("files"):
        sin_declarar = f"la respuesta por el canal ({tool}) lleva fichero(s) adjunto(s)"
elif MCP_ENVIA.search(tool):
    sin_declarar = f"la tool {tool} crea, sube o envía contenido a un servicio externo"

if not declarado and not sin_declarar:
    sys.exit(0)

# ── ¿es delicado? ────────────────────────────────────────────────────────────────────────
motivos = []
marcador = d / ".claude" / "proyecto-delicado.md"
if marcador.exists():
    sin_comentarios = re.sub(r"<!--.*?-->", "", leer(marcador), flags=re.S)
    primera = next((ln.strip() for ln in sin_comentarios.splitlines()
                    if ln.strip() and not ln.lstrip().startswith(("#", ">"))), "")
    motivos.append("declarado en .claude/proyecto-delicado.md" + (f": {primera[:200]}" if primera else ""))
conf = leer(d / ".claude" / "CONFIGURACION.yaml")
if re.search(r"^\s*datos_sensibles:\s*.*\bsalud\b", conf, re.M):
    motivos.append("CONFIGURACION.yaml: datos_sensibles incluye salud")
if re.search(r"^\s*datos_reales_desarrollo:\s*[\"']?s[ií]", conf, re.M):
    motivos.append("CONFIGURACION.yaml: hay datos reales en desarrollo")
if re.search(r"Perfil.*web-cliente", leer(d / ".docs" / "core" / "design-system.md", 20000)):
    motivos.append("la marca es de un cliente (perfil web-cliente): hace falta su permiso por "
                   "escrito para mandarla a un tercero")
docs = list((d / ".docs" / "core").glob("*.md")) + list(d.glob(".docs/plans/*/arranque/*.md"))
if any(re.search(r"datos de salud|categor[ií]as especiales de datos", leer(p, 200000), re.I)
       for p in docs[:60]):
    motivos.append("los documentos del proyecto hablan de datos de salud")

que = "; ".join(declarado + ([sin_declarar] if sin_declarar else []))
if motivos:
    razon = (f"⚠️ Proyecto delicado ({' · '.join(motivos)}). Va a salir fuera: {que}. Confírmalo "
             "solo si el dueño de los datos o de la marca lo ha aceptado por escrito.")
    print(json.dumps({"hookSpecificOutput": {"hookEventName": "PreToolUse",
                                             "permissionDecision": "ask",
                                             "permissionDecisionReason": razon}}, ensure_ascii=False))
elif always_ask:
    razon = (f"⚠️ {', '.join(sorted(set(always_ask)))} pide confirmación CADA VEZ (decisión del Usuario, "
             f"`always_ask: true` en envios-externos.json). Va a salir fuera: {que}. No hay DPA con ese "
             "servicio: confírmalo solo si el dueño de la marca lo ha aceptado.")
    print(json.dumps({"hookSpecificOutput": {"hookEventName": "PreToolUse",
                                             "permissionDecision": "ask",
                                             "permissionDecisionReason": razon}}, ensure_ascii=False))
elif declarado:
    print(json.dumps({"systemMessage": f"Aviso: esto envía a un servicio externo: {que}."},
                     ensure_ascii=False))
sys.exit(0)
PY
)
RC=$?
[ "$RC" -ne 0 ] && roto "detector rc=$RC"
[ -n "$SAL" ] && printf '%s\n' "$SAL"
exit 0
