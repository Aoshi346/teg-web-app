#!/bin/bash
# audit-log.sh — PostToolUse hook (HAR-6: cadena tamper-evident + fuera del repo)
#
# Escribe una línea JSON por cada tool use significativo. Permite supervisión externa sin
# parsear logs de texto.
#
# DOS PROPIEDADES QUE ANTES NO TENÍA:
#   1. Cadena de hashes: cada línea lleva `prev` (hash de la anterior) y `h` (hash de esta).
#      Borrar o editar una línea rompe la cadena y `--verify` lo detecta.
#   2. Fuera del alcance de edición del agente: por defecto vive en ~/.claude/audit/, NO en el
#      repo. El agente tiene Edit(**)/Write(**) sobre el proyecto; si el log vive dentro, el
#      propio agente auditado puede reescribirlo.
#
# Formato COMPATIBLE con el anterior (ts/tool/cmd|file); `prev` y `h` son campos añadidos.
#
# 3. Redacción en origen (U.06): cada valor pasa por `scripts/redactar.py` antes de truncarse y de
#    hashearse. Los escritos ANTES se re-sellaron en la sub-ola 2.27 (SE-4) con `audit_log.py resellar`;
#    `scripts/gate_secretos.py` es el control de que no queda ninguno.
#
# 4. Clave por repo, cerrojo y rotación (MO-81, 2.27): el fichero es el de la raíz del repo PRINCIPAL
#    (los worktrees comparten log), cada escritura toma flock (sin él, dos sesiones bifurcaban la cadena)
#    y pasado CLAUDE_AUDIT_MAX_MB (10) el fichero va a rotados/ sin cortar la cadena.
#
#   Ubicación:  $CLAUDE_AUDIT_DIR  (default: ~/.claude/audit/<repo principal>.jsonl, rotados en rotados/)
#   Verificar:  bash .claude/hooks/audit-log.sh --verify      (= scripts/audit_log.py verificar)
#   Buscar:     python3 .claude/scripts/audit_log.py buscar 'migrate' --tool Bash --desde 2026-10-01
#   Re-sellar:  python3 .claude/scripts/audit_log.py resellar --todos   (redacta lo viejo, rehace la cadena)
#
# Append-only de verdad (opcional, requiere root una vez):
#   sudo chattr +a ~/.claude/audit/<proyecto>.jsonl
# Sin eso, la cadena es *tamper-evident* (detecta), no *tamper-proof* (impide).
#
# Claude Code pasa la info via stdin como JSON (NO env vars):
# {"tool_name":"Write","tool_input":{"file_path":"..."},"tool_response":{...}}
# OJO: por eso el programa python NO puede ir en un heredoc — el heredoc ocuparía stdin y el
# JSON de la tool nunca llegaría. Se pasa con `python3 -c`.

PROJECT_DIR="${CLAUDE_PROJECT_DIR:-$(pwd)}"
SCRIPTS_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../scripts" 2>/dev/null && pwd)"
# Clave = raíz del REPO PRINCIPAL (MO-81, 2.27): todos los worktrees de un repo escriben en el mismo
# fichero. Antes era el nombre de la carpeta y cada worktree abría el suyo. Fuera de git, la carpeta.
# (La misma cuenta en Python: scripts/audit_log.py key_root.)
KEY_ROOT="$PROJECT_DIR"
_COMMON=$(git -C "$PROJECT_DIR" rev-parse --path-format=absolute --git-common-dir 2>/dev/null)
if [ -n "$_COMMON" ] && [ "$(basename "$_COMMON")" = ".git" ]; then
    KEY_ROOT=$(dirname "$_COMMON")
elif _TOP=$(git -C "$PROJECT_DIR" rev-parse --show-toplevel 2>/dev/null) && [ -n "$_TOP" ]; then
    KEY_ROOT="$_TOP"
fi
PROJECT_SLUG=$(basename "$KEY_ROOT")
PROJECT_SLUG="${PROJECT_SLUG//[^A-Za-z0-9_.-]/-}"
AUDIT_DIR="${CLAUDE_AUDIT_DIR:-$HOME/.claude/audit}"
AUDIT_FILE="$AUDIT_DIR/${PROJECT_SLUG:-proyecto}.jsonl"
mkdir -p "$AUDIT_DIR" 2>/dev/null

# ---------------------------------------------------------------- verificación de la cadena
# La hace scripts/audit_log.py (recorre también los segmentos rotados). Buscar: `audit_log.py buscar`.
if [ "$1" = "--verify" ]; then
    if [ ! -f "$SCRIPTS_DIR/audit_log.py" ]; then
        echo "audit-log: falta scripts/audit_log.py, no se puede verificar" >&2; exit 2
    fi
    python3 -I "$SCRIPTS_DIR/audit_log.py" verificar "$AUDIT_FILE"
    exit $?
fi

# ---------------------------------------------------------------- registro (una sola pasada)
read -r -d '' LOG_PROG <<'PY'
import fcntl, hashlib, json, os, sys
from datetime import datetime, timezone

GENESIS = "0" * 64
path = sys.argv[1]
# Rotación (MO-81): pasado este tamaño el fichero va a rotados/ y la cadena sigue en uno nuevo.
try:
    MAX_BYTES = int(float(os.environ.get("CLAUDE_AUDIT_MAX_MB", "10")) * 1024 * 1024)
except (ValueError, OverflowError):  # «inf», «1e400»: OverflowError y la línea se perdía
    MAX_BYTES = 0
if MAX_BYTES <= 0:  # 0, negativos o basura: rotaría en cada escritura
    MAX_BYTES = 10 * 1024 * 1024

# Redacción EN ORIGEN (SE-4/SE-17, U.06): el texto se tapa ANTES de truncar y ANTES del hash, así la
# cadena se calcula sobre lo ya redactado y nunca hay que reescribirla para quitar un secreto.
# Fallo cerrado: sin redactor, el valor no se escribe en claro.
try:
    if not sys.argv[2]:
        raise ImportError("sin carpeta de scripts")  # "" sería el cwd: un redactar.py plantado ahí
    # (y el python va con -I: sin -I, `python3 -c` ya pone el cwd en sys.path y un json.py del cwd
    # secuestraba el hook, desde antes de U.06)
    sys.path.insert(0, sys.argv[2])
    from redactar import redact
except Exception:
    def redact(text):
        return "[REDACTED:no-redactor]" if text else text

try:
    d = json.load(sys.stdin)
except Exception:
    sys.exit(0)

tool = d.get("tool_name", "")
if tool not in ("Write", "Edit", "Bash", "Skill", "Task", "Agent"):
    sys.exit(0)

inp = d.get("tool_input", {}) or {}
if tool == "Bash":
    # primero redactar el comando ENTERO y luego cortar: cortando antes, un secreto partido por el
    # corte ya no lo reconoce ninguna regex y queda medio en claro
    key, val = "cmd", redact(inp.get("command", "") or "")[:120]
elif tool == "Skill":
    # QUÉ skill se invoca. Sin esto no se puede saber cuáles se usan y cuáles sobran: el log
    # tenía 13.637 eventos y CERO decían el nombre de una skill (medido 2026-08-21). Decidir
    # qué retirar sin este dato es adivinar — y es el mismo agujero que documentamos para los
    # agentes IA (patterns/stack/agente-observabilidad.md), pero en nuestra propia casa.
    key, val = "skill", (inp.get("skill", "") or inp.get("name", "") or "")[:80]
elif tool in ("Task", "Agent"):
    # QUÉ agente se lanza. De los 45, solo se sabía de 5 y por los ficheros que dejan al correr.
    key, val = "agent", (inp.get("subagent_type", "") or inp.get("description", "") or "")[:80]
else:
    key, val = "file", inp.get("file_path", "") or ""
# la descripción de un agente o una ruta también pueden llevar un token pegado: mismo redactor
val = redact(val) if key != "cmd" else val

# Cerrojo (2.27): dos sesiones o dos worktrees escribiendo a la vez leían el mismo `prev` y la cadena se
# bifurcaba (medido: 3 roturas así en los logs viejos, mismo segundo, mismo prev). Con flock exclusivo la
# lectura de la cola y la escritura van juntas. Tras el cerrojo se comprueba que el fichero sigue siendo
# el mismo: si audit_log.py lo re-selló o se rotó mientras se esperaba, se reabre.
def lock():
    while True:
        f = open(path, "a+b")
        fcntl.flock(f.fileno(), fcntl.LOCK_EX)
        try:
            if os.fstat(f.fileno()).st_ino == os.stat(path).st_ino:
                return f
        except FileNotFoundError:
            pass
        f.close()


fh = lock()


def last_hash(f):
    """hash de la ultima linea = eslabon previo (leemos solo la cola, no el fichero entero)"""
    try:
        f.seek(0, os.SEEK_END)
        f.seek(max(0, f.tell() - 4096))
        tail = f.read().decode("utf-8", "ignore").strip().splitlines()
        return json.loads(tail[-1]).get("h", GENESIS) if tail else GENESIS
    except (json.JSONDecodeError, IndexError):
        return GENESIS


def sealed(rec):
    core = json.dumps(rec, ensure_ascii=False, separators=(",", ":"))
    rec["h"] = hashlib.sha256(core.encode()).hexdigest()
    return (json.dumps(rec, ensure_ascii=False, separators=(",", ":")) + "\n").encode("utf-8")


now = datetime.now(timezone.utc)
ts = now.strftime("%Y-%m-%dT%H:%M:%SZ")
prev = last_hash(fh)
try:
    if os.fstat(fh.fileno()).st_size >= MAX_BYTES:
        base = os.path.basename(path)[:-len(".jsonl")] if path.endswith(".jsonl") else os.path.basename(path)
        d = os.path.dirname(path)
        os.makedirs(os.path.join(d, "rotados"), exist_ok=True)
        dest = os.path.join(d, "rotados", "%s.%s.jsonl" % (base, now.strftime("%Y%m%dT%H%M%SZ")))
        if not os.path.exists(dest):
            # El nuevo nace YA con su eslabón `_rotation` y entra con un rename atómico: nunca hay un
            # instante sin fichero en el que otra sesión pudiera empezar una cadena desde el génesis.
            tmp = "%s/.%s.rot.%d" % (d, base, os.getpid())
            with open(tmp, "wb") as t:
                t.write(sealed({"ts": ts, "tool": "_rotation", "from": "rotados/" + os.path.basename(dest),
                                "prev": prev}))
            os.link(path, dest)       # el segmento viejo queda en rotados/ (mismo inodo)
            os.replace(tmp, path)     # y el actual pasa a ser el nuevo
            fh.close()                # suelta el cerrojo viejo: los que esperaban ven otro inodo
            fh = lock()
            prev = last_hash(fh)
except OSError:
    pass  # sin rotar no se pierde nada: se sigue escribiendo en el actual

# una última línea sin \n (escritura cortada) pegaría la nueva a ella y rompería la cadena para siempre
try:
    end = fh.seek(0, os.SEEK_END)
    if end:
        fh.seek(end - 1)
        if fh.read(1) != b"\n":
            fh.write(b"\n")
except OSError:
    pass
rec = {"ts": ts, "tool": tool, key: val}
# QUIÉN la llamó (EQ-19, 3.11): `agent_type` llega cuando la tool la usa un subagente; sin él, la sesión
# principal. Es lo que permite contar el trabajo por agente, no solo cuántas veces se lanzó.
if d.get("agent_type"):
    rec["by"] = str(d["agent_type"])[:80]
rec["prev"] = prev
fh.write(sealed(rec))
fh.flush()
fh.close()
PY

python3 -I -c "$LOG_PROG" "$AUDIT_FILE" "$SCRIPTS_DIR"

exit 0
