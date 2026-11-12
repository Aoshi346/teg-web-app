#!/usr/bin/env bash
# guard-secretos.sh — PreToolUse (matcher «Bash|Read|Grep»): bloquea leer un secreto por ruta + verbo.
#
# Promovido de `examples/` a `hooks/` y registrado en el núcleo el 2026-10-22 (SE-23): dos
# proyectos (elvion-autoparte-demo y -evolution) lo llevaban registrado a mano y el resto no tenía
# nada. Sigue siendo PROTECCIÓN POR RUTAS: el patrón genérico cubre a cualquiera, y las rutas de
# TU proyecto van en RUTAS_PROPIAS (§1) — `scripts/check_harness_seguridad.py` (H4) avisa si están
# vacías o apuntan a rutas que no existen.
#
# QUÉ CUBRE ESTE HOOK QUE LOS `deny` NO (para no duplicar, SE-23):
#   · `deny Read(**/.env*)`, `Read(**/*.pem)`… YA bloquean `Read`, `Edit` y los comandos de fichero que
#     Claude Code reconoce en Bash (`cat`, `head`, `tail`, `sed`, `tee`) sobre esas rutas (doc
#     permissions §Read and Edit; medido en la revisión: boris-skills, verificación #7).
#   · Lo que NO cubren y este hook sí: `grep`/`rg`/`awk`/`strings`/`base64`/`xxd`/`od`/`cp`/`scp`/`curl
#     -d @…`/`nc`/`python3 -c` sobre la ruta; la herramienta `Grep` apuntada a un secreto; rutas FUERA
#     del patrón del deny (`creds/`, `~/.ssh`, `~/.aws`, `.claude/.credentials.json`, `.netrc`,
#     `.git-credentials`); y un workspace al que se le ignoraron las reglas de permisos.
#   · El VOLCADO DEL ENTORNO, que no nombra ninguna ruta: `printenv`, `env` sin orden detrás, `set` a
#     secas, `docker [compose] exec <ctr> env|printenv|set` (también dentro de `sh -c`) y `docker
#     inspect` sin `-f`/`--format` o con `Env` en el formato. Pasan `env VAR=x orden` y
#     `docker inspect -f '{{.State.Health.Status}}'`. No ve `$(printenv)` ni `cat /proc/*/environ`.
#   · Los `deny` de Write/Edit sobre `.env*`, `*.pem`, `*.key`… siguen ahí y este hook no los repite.
#
# SU LÍMITE, escrito aquí para que nadie lo olvide: es una lista de verbos, y las listas de
# verbos SE PUEDEN RODEAR. No es defensa contra alguien que ya tiene root, ni contra quien
# parte la cadena a propósito (`rules/security.md` §"Las tres formas en que un guard falla"), ni contra
# un script que abre el fichero por dentro (`python3 leer.py`). Lo que un heredoc entrecomillado
# (`<<'EOF'`) escribe NO se mira: es prosa, no un comando que lee.
#
# Entrada: JSON de PreToolUse por stdin.   Salida: exit 0 deja pasar · exit 2 BLOQUEA.
# (exit 1 NO bloquea — es "error no bloqueante". Este es el fallo que tuvo check-ram.sh.)
# Si no hay python3 no puede juzgar: deja pasar y lo dice por stderr.
#
#   bash .claude/hooks/guard-secretos.sh --autocomprobar    # ¿está adaptado a este proyecto?

set -uo pipefail

# ── 1. LO QUE HAY QUE ADAPTAR ───────────────────────────────────────────────────────────
# Las dos variables se USAN de verdad más abajo. Si las dejas decorativas —asignadas y nunca
# referenciadas— engañan a quien lea el fichero creyendo que el hook se adapta solo. Pasó:
# un proyecto heredó este hook de otro y sus bloqueos se escribían en el log del proyecto
# de origen, así que auditarlos donde tocaba no encontraba nada.
RAIZ="${GUARD_RAIZ:-${CLAUDE_PROJECT_DIR:-$PWD}}"
LOG="${GUARD_LOG:-$RAIZ/.claude/secretos-bloqueados.log}"

# Rutas de ESTA instalación (relativas o con $RAIZ). Las genéricas (en el detector) protegen a
# cualquiera; las de tu proyecto van aquí y son las que hacen que el guard proteja a propósito
# y no por casualidad. Ejemplos: "$RAIZ/secrets/" · "$RAIZ/backend/.env.prod"
RUTAS_PROPIAS=(
  # "$RAIZ/secrets/"
)

if [ "${1:-}" = "--autocomprobar" ]; then
  n=0; muertas=0
  for r in "${RUTAS_PROPIAS[@]}"; do
    [ -z "$r" ] && continue
    n=$((n+1)); [ -e "${r%/}" ] || { echo "  ruta propia que NO existe aquí: $r"; muertas=$((muertas+1)); }
  done
  if [ "$n" -eq 0 ]; then
    echo "RUTAS_PROPIAS está vacío: este guard protege SOLO por la parte genérica (.env, secrets/, creds/, ~/.ssh…)."
    echo "Eso es protección por casualidad (rules/security.md §3). Añade las rutas de secretos de ESTE proyecto."
    exit 1
  fi
  [ "$muertas" -gt 0 ] && exit 1
  echo "RUTAS_PROPIAS: $n ruta(s), todas existen."; exit 0
fi

# ── 2. EL CHEQUEO ───────────────────────────────────────────────────────────────────────
ENTRADA="$(cat)"
if ! command -v python3 >/dev/null 2>&1; then
  echo "[guard-secretos] sin python3: no puedo juzgar este comando." >&2
  exit 0
fi

PROPIAS=""
for r in "${RUTAS_PROPIAS[@]}"; do [ -n "$r" ] && PROPIAS="$PROPIAS${r}"$'\n'; done

# El detector (python, inline) imprime «ruta-casada» y sale 3 si hay que bloquear; 0 si deja pasar.
# OJO con dónde van las variables: DEBEN anteponerse a `python3`, no a `printf` (hasta el 2026-10-22
# iban a printf, así que RUTAS_PROPIAS nunca llegó al detector).
DETECTOR='import json
import os
import re
import shlex
import sys

try:
    d = json.load(sys.stdin)
except Exception:
    sys.exit(0)
herramienta = d.get("tool_name") or ""
i = d.get("tool_input") or {}
INTERPRETE = re.compile(r"\b(?:python3?|bash|sh|zsh|node|perl|ruby|php)\b")


def sin_prosa(texto):
    """Quita el cuerpo de un heredoc entrecomillado SALVO que se lo coma un intérprete
    (python3 - <<'"'"'EOF'"'"', bash <<'"'"'EOF'"'"': ahí el cuerpo ES código que se ejecuta)."""
    def cambia(m):
        return m.group(0) if INTERPRETE.search(m.group(1)) else m.group(1) + "<<HEREDOC"
    return re.sub(r"([^\n]*?)<<-?\s*([\"'"'"'])?(\w+)\2?[^\n]*\n.*?\n[ \t]*\3[ \t]*(?=\n|$)", cambia,
                  texto, flags=re.S) if re.search(r"<<-?\s*[\"'"'"']", texto) else texto


if herramienta == "Bash":
    texto = sin_prosa(i.get("command") or "")
    texto = re.sub(r"(?m)(?:^|\s)#[^\n]*$", "", texto)          # comentarios de fin de línea
elif herramienta in ("Read", "Grep"):
    texto = " ".join(str(i.get(k) or "") for k in ("file_path", "path", "glob"))
else:
    sys.exit(0)
if not texto.strip():
    sys.exit(0)

# ── Volcado del entorno: saca TODAS las claves sin nombrar ningún fichero, así que el detector de
# rutas de abajo no lo ve. Se juzga la palabra en POSICIÓN DE COMANDO de cada tramo, no la mención:
# `env VAR=x orden` ejecuta una orden y pasa; `grep printenv docs/` solo la nombra y pasa.
PREFIXES = {"sudo", "doas", "command", "exec", "nohup", "time", "nice", "stdbuf"}
SHELLS = {"sh", "bash", "zsh", "dash", "ash"}
ASSIGNMENT = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*=")
SEGMENT_SEP = re.compile(r"&&|\|\||;|\||\n")
FORMAT_WITH_ENV = re.compile(r"Env|\.Config\s*\}\}|json\s+\.\s*\}\}|\{\{\s*\.\s*\}\}")


def words(segment):
    try:
        return shlex.split(segment)
    except ValueError:              # comillas abiertas porque el tramo se partió por un | interior
        return [t.strip(chr(34) + chr(39)) for t in segment.split()]


def skip_options(ts, takes_value):
    """Quita las opciones de cabeza; las de `takes_value` se llevan también su valor."""
    while ts and ts[0].startswith("-") and ts[0] != "-":
        t = ts.pop(0)
        if t in takes_value and ts:
            ts.pop(0)
    return ts


def env_dump_in(text):
    for segment in SEGMENT_SEP.split(text):
        r = env_dump(words(segment.strip().lstrip("({ ")))
        if r:
            return r
    return None


def env_dump(ts):
    ts = list(ts)
    while ts and (ASSIGNMENT.match(ts[0]) or os.path.basename(ts[0]) in PREFIXES):
        ts.pop(0)
        skip_options(ts, {"-u", "-g", "-C", "-n", "-o", "-e"})
    if not ts:
        return None
    cmd, rest = os.path.basename(ts[0]), ts[1:]
    if cmd == "printenv":
        return "printenv"
    if cmd == "set" and not rest:
        return "set"
    if cmd == "env":
        while rest and (rest[0].startswith("-") or ASSIGNMENT.match(rest[0])):
            t = rest.pop(0)
            if t in ("-S", "--split-string"):
                return env_dump_in(" ".join(rest)) if rest else None
            if t in ("-u", "--unset", "-C", "--chdir") and rest:
                rest.pop(0)
        return env_dump(rest) if rest else "env"          # sin orden detrás, env imprime el entorno
    if cmd in SHELLS and "-c" in rest:
        i = rest.index("-c")
        return env_dump_in(rest[i + 1]) if i + 1 < len(rest) else None
    if cmd in ("docker", "podman", "docker-compose"):
        rest = skip_options(rest, {"-H", "--host", "-c", "--context", "--config", "-l", "--log-level"})
        if cmd == "docker-compose":
            rest = ["compose"] + rest
        if rest and rest[0] == "compose":
            rest = skip_options(rest[1:], {"-f", "--file", "-p", "--project-name", "--env-file",
                                          "--profile", "--project-directory", "--ansi", "--progress"})
        if rest and rest[0] in ("container", "image"):
            rest = rest[1:]
        if not rest:
            return None
        sub, rest = rest[0], rest[1:]
        if sub == "exec":
            rest = skip_options(rest, {"-u", "--user", "-w", "--workdir", "-e", "--env", "--env-file",
                                       "--detach-keys", "--index"})
            r = env_dump(rest[1:]) if len(rest) > 1 else None      # rest[0] es el contenedor
            return "docker exec … " + r if r else None
        if sub == "inspect":
            fmt = None
            for k, t in enumerate(rest):
                if t in ("-f", "--format") and k + 1 < len(rest):
                    fmt = rest[k + 1]
                elif t.startswith("--format="):
                    fmt = t[len("--format="):]
                elif t.startswith("-f") and len(t) > 2:
                    fmt = t[2:]
            if fmt is None:
                return "docker inspect sin -f"
            if FORMAT_WITH_ENV.search(fmt):
                return "docker inspect con Env en el formato"
    return None


if herramienta == "Bash":
    r = env_dump_in(texto)
    if r:
        print(r)
        sys.exit(4)

ANTES = r"(?:^|[\s/\"'"'"'@*:<]|if=|post-file=)"
FIN = r"(?=$|[\s\"'"'"'`;|&)<>*])"
home = os.environ.get("HOME_DIR", "") or os.path.expanduser("~")
raiz = (os.environ.get("GUARD_RAIZ_PY") or "").rstrip("/")
H = r"(?:~|\$HOME|\$\{HOME\}|" + re.escape(home) + r")"
# (nombre, regex, clase): clase "contenido" = solo verbos que ponen el contenido delante del modelo;
# "normal" = además los que lo sacan del equipo (curl, scp, nc…)
rutas = [
    ("env", ANTES + r"\.env(?:\.[A-Za-z0-9_-]+)*" + FIN, "normal"),
    (".envrc", ANTES + r"\.envrc" + FIN, "normal"),
    ("secrets/", ANTES + r"[\w./-]*secrets/[\w./-]*", "normal"),
    ("creds/", ANTES + r"[\w./-]*creds/[\w./-]*", "normal"),
    ("credentials.*", ANTES + r"credentials\.(?:json|ya?ml|txt|env|ini)" + FIN, "normal"),
    ("*.pem", r"[\w./~-]+\.pem" + FIN, "normal"),
    ("*.key", r"[\w./~-]+\.key" + FIN, "normal"),
    ("~/.ssh", H + r"/\.ssh(?:/[\w.-]*)?", "contenido"),
    ("~/.aws", H + r"/\.aws(?:/[\w.-]*)?", "contenido"),
    ("~/.docker/config.json", H + r"/\.docker/config\.json", "contenido"),
    ("~/.pgpass", H + r"/\.pgpass", "contenido"),
    ("~/.config/gcloud", H + r"/\.config/gcloud(?:/[\w.-]*)?", "contenido"),
    ("~/.kube/config", H + r"/\.kube/config", "contenido"),
    (".claude/.credentials.json", r"\.claude/\.credentials\.json", "normal"),
    (".netrc", ANTES + r"\.netrc" + FIN, "normal"),
    (".git-credentials", ANTES + r"\.git-credentials" + FIN, "normal"),
]
# Las rutas propias del proyecto: la absoluta y la relativa a la raíz.
for p in filter(None, (os.environ.get("GUARD_PROPIAS") or "").split("\n")):
    p = p.rstrip("/")
    rel = p[len(raiz) + 1:] if raiz and p.startswith(raiz + "/") else p
    for variante in {p, rel}:
        rutas.append((rel + ("/" if os.path.isdir(p) else ""), ANTES + re.escape(variante) + r"(?:/[\w./-]*)?" + FIN,
                      "normal"))

CONTENIDO = (r"cat|head|tail|less|more|grep|egrep|fgrep|rg|awk|sed|strings|base64|xxd|od|hexdump|nl|tac|sort|"
             r"diff|cmp|jq|yq|cut|paste|tr|dd|tee|zcat|bat|view|vi|vim|nano|python3?\s+-c|python3?\s+-|"
             r"node\s+-e|perl\s+-[ne]|ruby\s+-e|git\s+show|git\s+cat-file|xargs\s+cat|tar|gzip|zip|7z|rev|fold")
SALE = r"scp|rsync|curl|wget|nc|ncat|netcat"
# cp/mv sacan una COPIA del secreto a un sitio que luego se lee: solo cuenta si el secreto es el ORIGEN
# (primer argumento), no el destino (`cp .env.example .env` copia la plantilla).
COPIA = re.compile(r"(?:^|[\s;&|(`])(?:/\S*/)?(?:cp|mv|install)\s+((?:-\S+\s+)*)(\S+)")
# Un verbo cuenta si está en el MISMO tramo (entre && || ; |) que la ruta: `docker compose --env-file .env
# up && tail -f app.log` no lee el .env. Con ruta absoluta del verbo (/bin/cat) también.
V_CONT = re.compile(r"(?:^|[\s;&|(`$])(?:/\S*/)?(?:" + CONTENIDO + r")(?:\s|$)|open\s*\(|read_text|readlines|<\s*$|\$\(<")
V_SALE = re.compile(r"(?:^|[\s;&|(`])(?:/\S*/)?(?:" + SALE + r")(?:\s|$)")
CODIGO = re.compile(r"\.(?:tsx?|jsx?|py|md|rst|html|css|vue|svelte|go|rs|java|rb|php)$", re.I)
EJEMPLOS = re.compile(r"(?:example|sample|template|dist)$", re.I)
solo_ruta = herramienta in ("Read", "Grep")
tramos = [texto] if solo_ruta else re.split(r"&&|\|\||;|\||\n", texto)
for tramo in tramos:
    for nombre, rx, clase in rutas:
        for m in re.finditer(rx, tramo):
            token = m.group(0).strip(" \"'"'"'`/=:@*")
            if nombre == "env" and EJEMPLOS.search(token):
                continue
            if nombre in ("secrets/", "creds/") and CODIGO.search(token):
                continue           # src/creds/LoginForm.tsx, docs/secrets/README.md: código y prosa
            copia_origen = False
            if not solo_ruta:
                cm = COPIA.search(tramo)
                copia_origen = bool(cm and cm.start(2) - 1 <= m.start() and m.end() <= cm.end(2) + 1)
            leido = solo_ruta or copia_origen or V_CONT.search(tramo) or re.search(r"<\s*" + re.escape(m.group(0).strip()), tramo)
            if not leido and clase == "normal" and V_SALE.search(tramo):
                leido = True
            if leido:
                print(nombre)
                sys.exit(3)
sys.exit(0)
'
RUTA_CASADA="$(printf '%s' "$ENTRADA" | GUARD_PROPIAS="$PROPIAS" GUARD_RAIZ_PY="$RAIZ" HOME_DIR="$HOME" python3 -c "$DETECTOR" 2>/dev/null; echo "rc=$?")"

RC="${RUTA_CASADA##*rc=}"
RUTA_CASADA="${RUTA_CASADA%rc=*}"; RUTA_CASADA="$(printf '%s' "$RUTA_CASADA" | tr -d '\n')"
if [ "$RC" = "4" ]; then
  mkdir -p "$(dirname "$LOG")" 2>/dev/null
  printf '%s\t%s\n' "$(date -Is)" "volcado de entorno: $RUTA_CASADA" >> "$LOG" 2>/dev/null
  cat >&2 <<EOF
BLOQUEADO: el comando vuelca el entorno ($RUTA_CASADA), y ahí van todas las claves.

  Para comprobar una variable sin enseñarla:
      test -n "\$VAR" && echo puesta || echo vacía
      docker compose exec <srv> sh -c 'test -n "\$VAR" && echo puesta || echo vacía'
  Para el estado de un contenedor:        docker inspect -f '{{.State.Health.Status}}' <ctr>
  Para ejecutar con una variable:         env VAR=valor <orden>   (eso pasa: no vuelca nada)
EOF
  exit 2
fi
[ "$RC" = "3" ] || exit 0

mkdir -p "$(dirname "$LOG")" 2>/dev/null
# Se registra QUÉ ruta casó, no el comando entero: un token pasado por línea de comandos no debe
# acabar en claro en un log (H5 de check_harness_seguridad.py).
printf '%s\t%s\n' "$(date -Is)" "$RUTA_CASADA" >> "$LOG" 2>/dev/null
cat >&2 <<EOF
BLOQUEADO: el comando lee un secreto ($RUTA_CASADA) con un verbo que saca contenido.

  Si necesitas comprobar que EXISTE:      test -s <ruta> · stat <ruta> · ls -la <ruta>
  Si necesitas leerlo de verdad:          hazlo fuera de la sesión, o añade una excepción
                                          a este hook CON SU RAZÓN ESCRITA.

  NO partas la cadena para esquivarme ("\$(echo env)", "\${V:-env}"). Eso no te hace más
  seguro: te deja sin guard y sin que nadie lo sepa. Y suele ser innecesario — este hook
  mira el COMANDO que tecleas, no lo que un script hace por dentro.

  Falso positivo conocido: buscar la CADENA ".env" dentro de un fichero inocente
  (grep -nE '\.env' config.py) también dispara. Salida buena: léelo con Read, no con grep.
EOF
exit 2
