#!/bin/bash
# suggest-compact.sh — UserPromptSubmit hook: avisar de la PRESIÓN DE CONTEXTO antes de que el
# harness compacte por su cuenta, en el único sitio desde el que se puede avisar.
#
# POR QUÉ EXISTE
#   Esto era la skill `strategic-compact` (archivada 2026-08-22, item CAP-STRATEGICCO). Una skill
#   es exactamente la capa que NO puede hacer este trabajo: hay que recordarlo cuando el contexto
#   está lleno, o sea justo cuando el modelo deja de acordarse de cargar skills. Y la skill era
#   `user-invocable: false`, sin triggers y sin una sola cita en INDEX.md — no podía dispararse ni
#   queriendo. El porqué medido: `_archive/2026-08-22/README.md`.
#
# POR QUÉ NO ES UN PreToolUse QUE CUENTA LLAMADAS (que es lo que proponía la skill)
#   Habría cobrado latencia en CADA tool call a cambio de un aviso, y `rules/layer-decision.md`
#   avisa justo contra convertir todo en hook. Además contar llamadas es un PROXY: 50 greps de una
#   línea no llenan nada y 3 lecturas de un fichero grande sí. Aquí no se cuenta nada: se LEE el
#   contexto real que recibió el modelo en su último turno, del propio transcript de la sesión.
#
# QUÉ MIDE (dato exacto, no estimación)
#   Cada mensaje `assistant` del transcript trae `message.usage`. La suma
#   input_tokens + cache_read_input_tokens + cache_creation_input_tokens
#   es el tamaño real de la ventana en ese turno. Medido en este repo (2026-08-22):
#     sesión 99837cad… → auto-compact con preTokens=1.001.478, postTokens=28.716,
#                        cumulativeDroppedTokens=972.762, durationMs=113.461
#     sesión 83237e07… → compact MANUAL con preTokens=680.687 → 22.342 (durationMs=134.266)
#   Es decir: dejar que salte solo cuesta ~2 minutos y tira ~970k tokens elegidos por nadie.
#
# POR QUÉ NO USA PreCompact
#   PreCompact dispara CUANDO ya se compacta: tarde para sugerir el momento. Y el reinicio de los
#   avisos no lo necesita: el propio transcript deja un `{"type":"system","subtype":
#   "compact_boundary"}` con su `compactMetadata`, que este hook cuenta para volver a empezar.
#   Un evento menos que cablear y una cosa menos que pueda fallar en silencio (harness-gotchas TPL-21).
#
# LÍMITE HONESTO
#   Esto NO es un gate: es un recordatorio, y un recordatorio no se puede forzar (exit siempre 0).
#   Lo que el hook aporta no es obligación, es MOMENTO — solo el harness sabe cuánto contexto queda.
#   Mismo patrón que `dispatch-hint.sh`, que tampoco obliga a nada y también inyecta texto.
#
# LOS DOS GUARDARRAÍLES (un hook ruidoso acaba desactivado — agent-security.md ASI09)
#   1. UNA vez por banda y por ciclo de compactación. No repite.
#   2. Silencio por debajo del primer umbral: si no hay presión, no dice nada.
#
# Desactivar: quitar su bloque de settings.json, o exportar TL_NO_COMPACT_HINT=1.
# Calibrar:   TL_CONTEXT_LIMIT (tokens) · TL_COMPACT_BANDS (porcentajes, coma) — ver abajo.

[ -n "${TL_NO_COMPACT_HINT:-}" ] && exit 0

# El evento viaja por variable de entorno, NO por la tubería: el heredoc de abajo YA ocupa el stdin
# de python3, así que un `printf | python3 - <<PY` deja a json.load leyendo el propio script.
export TL_HOOK_INPUT="$(cat)"
python3 - <<'PY'
import json, os, sys

def bail():
    sys.exit(0)

try:
    ev = json.loads(os.environ.get("TL_HOOK_INPUT") or "")
except Exception:
    bail()

path = ev.get("transcript_path") or ""
session = ev.get("session_id") or "nosession"
if not path or not os.path.isfile(path):
    bail()                      # sin transcript no hay medición — se calla, no se inventa

# --- leer el transcript: la cola basta para el último usage; el fichero entero solo si hace falta.
# Medido sobre un .jsonl de 17 MB: cola de 1 MB 25 ms · fichero entero 91 ms (ambos muy por debajo
# del timeout de 30 s que UserPromptSubmit impone a los hooks `command`).
def last_usage(chunk):
    used = None
    for line in chunk:
        if '"usage"' not in line:
            continue
        try:
            o = json.loads(line)
        except Exception:
            continue
        u = (o.get("message") or {}).get("usage")
        if isinstance(u, dict):
            used = (u.get("input_tokens", 0) or 0) \
                 + (u.get("cache_read_input_tokens", 0) or 0) \
                 + (u.get("cache_creation_input_tokens", 0) or 0)
    return used

try:
    size = os.path.getsize(path)
    with open(path, "rb") as f:
        f.seek(max(0, size - 1024 * 1024))
        used = last_usage(f.read().decode("utf-8", "replace").splitlines())
    if used is None and size > 1024 * 1024:
        with open(path, encoding="utf-8", errors="replace") as f:
            used = last_usage(f)
    # Los compact_boundary pueden estar en cualquier punto del fichero: se barre entero, pero solo
    # se parsea la línea que ya contiene la subcadena literal que escribe el harness.
    cycles, meta = 0, None
    with open(path, encoding="utf-8", errors="replace") as f:
        for line in f:
            if '"compact_boundary"' not in line:
                continue
            cycles += 1
            try:
                meta = json.loads(line).get("compactMetadata") or meta
            except Exception:
                pass
except Exception:
    bail()

if not used:
    bail()

# --- el límite de ventana NO viaja en el input del hook. Se LEE del modelo configurado.
#
# POR QUÉ NO SE ADIVINA (medido 2026-09-23). Antes era `1M si used > 200k, si no 200k`, y en una
# sesión `opus[1m]` con 177k dijo «Contexto al 88%» cuando era el 18%: por debajo de 200k TODA sesión
# de 1M se trataba como de 200k. Avisaba en falso a los 140k y 170k y, al cruzar 200k, saltaba al
# ~20% y callaba hasta los 700k. El agente repitió el 88% y recomendó compactar. Un porcentaje falso
# es peor que ninguno: si no se sabe la ventana, se calla.
#
# Orden: TL_CONTEXT_LIMIT (a mano) > ventana de la statusline > modelo del transcript > ANTHROPIC_MODEL > settings.local.json del proyecto >
# settings.json del proyecto > ~/.claude/settings.json. Sufijo `[1m]` → 1M; sin él → 200k.
# Límite conocido: un `/model` o `--model` de ESTA sesión no se escribe en ningún settings y no se ve.
def modelo_configurado():
    m = os.environ.get("ANTHROPIC_MODEL")
    if m:
        return m
    proj = os.environ.get("CLAUDE_PROJECT_DIR") or ev.get("cwd") or ""
    for f in (os.path.join(proj, ".claude", "settings.local.json"),
              os.path.join(proj, ".claude", "settings.json"),
              os.path.expanduser("~/.claude/settings.json")):
        try:
            with open(f, encoding="utf-8") as fh:
                m = json.load(fh).get("model")
        except Exception:
            continue
        if m:
            return m
    return None

# 2026-11-02 (T-197): `[1m]` en el settings ya no basta. Fable/Mythos traen 1M NATIVO sin sufijo y el
# settings decía `opus`: en una sesión Fable con 167k el hook dijo «75 %» cuando el harness daba 18 %.
# Fuente 1 · la ventana que el harness le pasa a la statusline (context_window.context_window_size),
#   que statusline-command.sh deja en /tmp/.claude_ctxwin_<session_id>. Es el dato exacto.
# Fuente 2 · el id del modelo del último mensaje del transcript: familias con 1M nativo.
def ventana_de_statusline():
    try:
        with open(os.path.join("/tmp", f".claude_ctxwin_{session}")) as fh:
            return int(fh.read().strip() or 0)
    except Exception:
        return 0

NATIVO_1M = ("fable", "mythos", "opus-5")
def modelo_del_transcript():
    try:
        with open(path, "rb") as f:
            f.seek(max(0, os.path.getsize(path) - 512 * 1024))
            cola = f.read().decode("utf-8", "replace").splitlines()
    except Exception:
        return None
    for line in reversed(cola):
        if '"model"' not in line or '"assistant"' not in line:
            continue
        try:
            m = (json.loads(line).get("message") or {}).get("model")
        except Exception:
            continue
        if m:
            return m
    return None

try:
    limit = int(os.environ.get("TL_CONTEXT_LIMIT") or 0)
except ValueError:
    limit = 0
if limit <= 0:
    limit = ventana_de_statusline()
if limit <= 0:
    mt = modelo_del_transcript() or ""
    # Fuente 2a · la ventana que la statusline vio para ESTE modelo en cualquier otra sesión.
    try:
        with open(os.path.join("/tmp", ".claude_ctxwin_model_" + mt.replace("/", "_"))) as fh:
            limit = int(fh.read().strip() or 0) if mt else 0
    except Exception:
        limit = 0
    # Fuente 2b · semilla para máquinas sin esa statusline: familias con 1M nativo conocidas.
    if limit <= 0 and (any(k in mt.lower() for k in NATIVO_1M) or "[1m]" in mt.lower()):
        limit = 1_000_000
if limit <= 0:
    modelo = modelo_configurado()
    if used > 200_000:
        limit = 1_000_000          # esto sí es seguro: una ventana de 200k no puede llevar más
    elif modelo:
        limit = 1_000_000 if "[1m]" in modelo.lower() else 200_000
    else:
        bail()                     # ventana desconocida: se calla, no se inventa

try:
    bands = sorted({int(x) for x in (os.environ.get("TL_COMPACT_BANDS") or "70,85").split(",") if x.strip()})
except ValueError:
    bands = [70, 85]

pct = used * 100 // limit
band = None
for b in bands:
    if pct >= b:
        band = b
if band is None:
    bail()                      # sin presión, silencio

# Guardarraíl 1: una vez por (sesión, ciclo de compactación, banda).
tmp = os.environ.get("TMPDIR") or "/tmp"
mark = os.path.join(tmp, f".tl-compact-{session}-{cycles}-{band}")
if os.path.exists(mark):
    bail()
try:
    open(mark, "w").close()
except OSError:
    pass

def es(n):
    return f"{n:,}".replace(",", ".")

queda = limit - used
print(f"🧠 Contexto al **{pct}%** ({es(used)} de ~{es(limit)} tokens; quedan ~{es(queda)}).")
print("")
print("Compactar TÚ en un límite lógico es mejor que dejar que salte solo: el automático corta")
print("donde toque, no donde tiene sentido.")

# El coste NO se cita de memoria: si esta sesión ya compactó, se lee su propio compactMetadata.
if meta:
    trg = "automático" if meta.get("trigger") == "auto" else "manual"
    drop = meta.get("cumulativeDroppedTokens") or 0
    secs = round((meta.get("durationMs") or 0) / 1000)
    veces = "1 vez" if cycles == 1 else f"{cycles} veces"
    print(f"En esta sesión ya ha pasado {veces}: el último fue **{trg}**, se llevó "
          f"**{es(drop)} tokens** y tardó **{secs} s**.")
print("")
print("Buen momento para `/compact <qué conservar>` — y solo si estás en uno de estos puntos:")
print("- acabas de terminar la exploración y vas a empezar a escribir código;")
print("- cerraste una wave / un hito y el siguiente no necesita el detalle del anterior;")
print("- cambias a una tarea que no tiene que ver con la de antes (ahí suele ser `/clear`).")
print("")
print("Si estás a mitad de una operación de varios pasos, **no compactes ahora**: termina el paso.")
PY
exit 0
