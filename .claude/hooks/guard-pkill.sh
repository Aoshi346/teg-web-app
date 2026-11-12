#!/usr/bin/env bash
# ══════════════════════════════════════════════════════════════════════════════════════════════
# guard-pkill.sh — PreToolUse (matcher «Bash»): bloquea el `pkill -f` que mata la shell que lo lanza.
#
# POR QUÉ EXISTE (MO-53, sub-ola 2.13, 2026-10-21). El Bash de Claude Code lanza cada comando como
# `/bin/bash -c "… eval '<el comando>' …"`: el texto entero del comando está en la línea de órdenes
# de esa shell. `pkill -f <patrón>` compara el patrón con la línea de órdenes de TODOS los procesos;
# se excluye a sí mismo, pero no a la shell que lo lanzó, y el patrón aparece literal en ella. La
# shell muere (exit 144), lo que iba detrás no corre y no hay aviso. Medido en los transcripts de
# esta máquina (sin EvoPreven ni gencat): en las sesiones principales, 40 de 52 comandos con
# `pkill -f` acabaron en exit 144; con los de los subagentes, 99 de 118.
# En EvoPreven dejó un worker parado sin aviso, dos veces (SERGAS-1, 25-09); en evolution quedó la
# memoria «matar por PID, no pkill -f».
#
# QUÉ BLOQUEA (exit 2, el motivo por stderr): `pkill -f|--full <patrón>`, `kill … $(pgrep -f <patrón>)`
# (o con comillas invertidas), el `kill` que recibe los PID de un `pgrep -f` por una variable
# (`pids=$(pgrep -f X); kill $pids`, también con local/export/declare, arrays y copias; `for p in
# $(pgrep -f X)`; `pgrep -f X | while read p`; `done < <(pgrep -f X)`; `readarray`/`mapfile`; en orden:
# la variable que se reasigna a otra cosa deja de contar) y `pgrep -f <patrón> | … | xargs [sudo] kill`,
# cuando el patrón —como
# regex, que es como lo lee pkill— casa con el comando o con lo que se sabe del envoltorio del Bash. También
# detrás de `if/then/do/!/{ /time`, de `sudo/nohup/timeout/env/nice/exec` con sus opciones, dentro de
# `$( … )` y en el argumento de `bash -c` / `sh -c`.
# QUÉ DEJA PASAR: el patrón que no casa consigo mismo (anclado al binario, `'^/srv/app/.venv/bin/celery'`,
# porque la shell empieza por `/bin/bash`; o con corchete, `'[h]ttp.server 8897'`, si tampoco sale en
# el envoltorio); `pkill -x <nombre>` y `pkill <nombre>` sin -f (miran el nombre del proceso);
# `pkill -f -x` (la línea entera tiene que casar); `kill <PID>`, `kill -0`; un patrón con `$`/`` ` ``
# que solo se sabe al ejecutar; lo que va en un heredoc (también el de `git commit -m "$(cat <<'EOF' …)"`;
# no un `<<<` ni un `<<` entre comillas), entre comillas simples o en un comentario; y lo que no mata
# (`pgrep -f` solo, o seguido de `&& kill <PID>`, de `kill "$(cat x.pid)"` o de un `read` de un fichero).
# Con -P/--parent (los hijos de un proceso) o -u/-U de otro usuario, no se mata a sí mismo: deja pasar.
# NO VE: los `export` que los plugins meten en el envoltorio (cambian de una máquina a otra: con el
# plugin de Codex, `pkill -f '[c]odex'` mata la shell y pasa), ni un patrón que llega en una variable,
# ni unos PID que pasan por un fichero (`pgrep -f X > p; kill $(cat p)`).
#
# CAMINO RÁPIDO: si el comando no contiene «pkill» ni «pgrep», sale 0 sin arrancar python3.
# FALLA CERRADO (PV-70/PV-122): sin python3, con el JSON truncado o si el detector revienta, y la
#   entrada trae `pkill`/`pgrep -f`, sale 2 (bloquea) y lo dice. Sin eso, el hook rompía hacia «deja
#   pasar» y `onFailure: "block"` no lo cubría (solo actúa si el script no arranca). Lo que no parece
#   un pkill pasa siempre: una guarda rota que bloqueara todo se acabaría quitando.
# MODO PRUEBA DE ROTURA: TL_GUARDA_SABOTAJE=excepcion hace reventar al detector.
# MODO PRUEBA: guard-pkill.sh --cmd "<comando>" (sin stdin JSON).
# ══════════════════════════════════════════════════════════════════════════════════════════════
set -uo pipefail
ILEGIBLE=0

if [ "${1:-}" = "--cmd" ]; then
  CMD="${2:-}"
else
  ENTRADA=$(cat)
  case "$ENTRADA" in *pkill*|*pgrep*) ;; *) exit 0 ;; esac
  CMD=$(printf '%s' "$ENTRADA" | python3 -c 'import json,sys
try:
    print((json.load(sys.stdin).get("tool_input") or {}).get("command") or "", end="")
except Exception:
    sys.exit(3)' 2>/dev/null) || { CMD="$ENTRADA"; ILEGIBLE=1; }   # JSON ilegible o sin python3: texto crudo
fi
case "$CMD" in *pkill*|*pgrep*) ;; *) exit 0 ;; esac
# Red ancha para cuando el detector no puede decidir: un pkill/pgrep con -f (o --full).
RED='pkill|pgrep +(-[a-zA-Z]*f|--full)'
roto() {
  if printf '%s' "$CMD" | grep -Eq "$RED"; then
    echo "guard-pkill ROTO ($1) y el comando lleva pkill/pgrep -f: bloqueado por si acaso (mata la shell, exit 144). Arregla el guard (.claude/hooks/guard-pkill.sh) o usa un PID guardado." >&2
    exit 2
  fi
  exit 0
}
command -v python3 >/dev/null 2>&1 || roto "sin python3"
[ "$ILEGIBLE" = 1 ] && roto "entrada ilegible (JSON truncado o inválido)"
[ "${TL_GUARDA_SABOTAJE:-}" = "excepcion" ] && roto "sabotaje de prueba"

MOTIVO=$(python3 - 3<<<"$CMD" <<'PY'
import os, re, shlex, sys

cmd = os.fdopen(3).read().rstrip("\n")
# Lo que ve pkill en la línea de órdenes de la shell del Bash de Claude Code (2.1.304, visto con
# `tr '\0' ' ' < /proc/$$/cmdline`): un envoltorio —`/bin/bash -c source ~/.claude/shell-snapshots/…`,
# los `export` que ponen los plugins, `eval '<el comando>'`, `pwd -P >| /tmp/claude-…-cwd`— con el
# comando dentro y cada comilla simple escrita como '"'"'. Los `export` de los plugins cambian de una
# máquina a otra y no se pueden saber desde aquí; lo demás va en la comparación.
EVAL = cmd.replace("'", "'\"'\"'")
LINEA = ("/bin/bash -c source " + os.path.expanduser("~") + "/.claude/shell-snapshots/snapshot-bash-0.sh "
         "2>/dev/null || true && shopt -u extglob 2>/dev/null || true && eval '" + EVAL
         + "' && pwd -P >| /tmp/claude-0-cwd")
TEXTOS = (cmd, EVAL, LINEA)


def casa_consigo(patron, exacto=False):
    try:
        rx = re.compile(patron, re.DOTALL)       # pkill cruza saltos de línea con «.»; Python, sin DOTALL, no
    except re.error:
        return not exacto and any(patron in t for t in TEXTOS)
    if exacto:                                   # -x: tiene que casar con la línea ENTERA de la shell
        return bool(rx.fullmatch(LINEA))
    return any(rx.search(t) for t in TEXTOS)


def contextos(texto, pila=None):
    """Recorre el texto como la shell: para cada posición, ¿está fuera de comillas? Dentro de
    `"…"`, un `$(` abre otra vez un contexto sin comillas (`git commit -m "$(cat <<'EOF' …)"`).
    Devuelve (fuera, pila al final) para poder seguir en la línea siguiente."""
    pila = list(pila or [])
    fuera, i, n = [True] * (len(texto) + 1), 0, len(texto)
    while i < n:
        c = texto[i]
        top = pila[-1] if pila else None
        fuera[i] = top in (None, "(")
        if top == "'":
            if c == "'":
                pila.pop()
        elif top == '"':
            if c == "\\":
                i += 1
            elif c == '"':
                pila.pop()
            elif c == "$" and texto[i + 1:i + 2] == "(":
                pila.append("("); i += 1
        else:
            if c == "\\":
                i += 1
            elif c in "'\"":
                pila.append(c)
            elif c == "$" and texto[i + 1:i + 2] == "(":
                pila.append("("); i += 1
            elif c == "(" and top == "(":
                pila.append("(")
            elif c == ")" and top == "(":
                pila.pop()
        i += 1
    return fuera, pila


def sin_heredocs(texto):
    """Quita el cuerpo de los heredocs: `cat > notas.md <<'EOF' … pkill -f x … EOF` escribe texto,
    no lo ejecuta (la línea de órdenes sí lo lleva: por eso `casa_consigo` mira el comando entero).
    Un heredoc es un `<<` fuera de comillas (o dentro de un `$( )`, aunque este vaya entre comillas
    dobles) y en posición de redirección: no un `<<<` (herestring), ni el de un `print(1 << n)` entre
    comillas, ni el de `$(( 1 << n ))`."""
    out, fin, pila = [], None, []
    for linea in texto.split("\n"):
        if fin is not None:
            if linea.strip() == fin:
                fin = None
            continue
        out.append(linea)
        fuera, pila_fin = contextos(linea, pila)
        for m in re.finditer(r"(?<!<)<<(?!<)-?\s*(['\"]?)([A-Za-z_][A-Za-z0-9_]*)\1", linea):
            antes = linea[:m.start()].rstrip()
            if fuera[m.start()] and not (antes and (antes[-1].isdigit() or antes[-1] == ")")):
                fin = m.group(2)
                break
        pila = pila_fin
    return "\n".join(out)


def sin_comentarios(texto):
    """Un `#` es comentario solo al empezar una palabra y fuera de comillas (`echo a#b`, `…/#ancla`
    y `$#` no lo son)."""
    out, q, i, n = [], None, 0, len(texto)
    while i < n:
        c = texto[i]
        if q:
            out.append(c)
            if c == "\\" and q == '"' and i + 1 < n:
                out.append(texto[i + 1]); i += 2; continue
            if c == q:
                q = None
        elif c in "'\"":
            q = c; out.append(c)
        elif c == "\\" and i + 1 < n:
            out.append(texto[i:i + 2]); i += 2; continue
        elif c == "#" and (i == 0 or texto[i - 1] in " \t\n;&|()"):
            while i < n and texto[i] != "\n":
                i += 1
            continue
        else:
            out.append(c)
        i += 1
    return "".join(out)


SUST = []                                         # el texto de cada $( … ) y `…`, por orden


LIT = []                                          # lo que iba entre comillas simples, apartado


def aparta_sustituciones(texto):
    """Cambia cada `$( … )`, `` `…` `` y `<( … )`/`>( … )` por `__SUSTn__` y guarda su texto en SUST.
    Lo que va entre comillas simples es literal (un `` `pkill -f x` `` en un `-m '…'` no se ejecuta):
    se aparta antes y se devuelve después."""
    fuera, _ = contextos(texto)
    trozos, i = [], 0
    while i < len(texto):
        if texto[i] == "'" and fuera[i]:
            j = texto.find("'", i + 1)
            j = len(texto) - 1 if j < 0 else j
            LIT.append(texto[i:j + 1])
            trozos.append(f"__LIT{len(LIT) - 1}__")
            i = j + 1
        else:
            trozos.append(texto[i]); i += 1
    texto = "".join(trozos)

    def guarda(m):
        SUST.append(m.group(1))
        return f"__SUST{len(SUST) - 1}__"
    while True:
        nuevo = re.sub(r"`([^`]*)`", guarda, re.sub(r"[$<>]\(([^()]*)\)", guarda, texto))
        if nuevo == texto:
            break
        texto = nuevo
    devuelve = lambda t: re.sub(r"__LIT(\d+)__", lambda m: LIT[int(m.group(1))], t)
    for k in range(len(SUST)):
        SUST[k] = devuelve(SUST[k])
    return devuelve(texto)


def simples(texto):
    """Los comandos simples de un texto: [(palabras, separador que lo sigue)]."""
    lex = shlex.shlex(texto, posix=True, punctuation_chars=";&|()\n")
    lex.whitespace = " \t\r"                      # el salto de línea separa comandos, no es espacio
    lex.whitespace_split = True
    lex.commenters = ""                           # los comentarios ya se quitaron, con comillas
    try:
        toks = list(lex)
    except ValueError:                            # comillas sin cerrar: así ni siquiera corre
        return []
    seg, out = [], []
    for t in toks:
        if t and set(t) <= set(";&|()\n"):
            out.append((seg, t)); seg = []
        else:
            seg.append(t)
    out.append((seg, ""))
    return [(s, p) for s, p in out if s]


RESERVADAS = {"if", "then", "else", "elif", "fi", "do", "done", "while", "until", "!", "{", "}", "time"}
ENVOLTORIOS = {  # programa → opciones que llevan valor detrás
    "sudo": {"-u", "-g", "-C", "-D", "-h", "-p", "-r", "-t", "-U"}, "nohup": set(), "command": set(),
    "exec": {"-a"}, "nice": {"-n"}, "timeout": {"-s", "-k", "--signal", "--kill-after"},
    "env": {"-u", "-C", "-S", "--unset", "--chdir"}, "stdbuf": {"-i", "-o", "-e"}, "setsid": set(),
    "ionice": {"-c", "-n", "-p"}, "chrt": set(), "taskset": set()}


def nucleo(seg):
    """La palabra que se ejecuta y sus argumentos, saltando VAR=x, palabras reservadas y envoltorios."""
    seg = list(seg)
    while seg:
        p = os.path.basename(seg[0])
        if seg[0] in RESERVADAS or re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]*=.*", seg[0]):
            seg.pop(0)
            if p == "time" and seg[:1] == ["-p"]:
                seg.pop(0)
        elif p in ENVOLTORIOS:
            con_valor = ENVOLTORIOS[p]
            seg.pop(0)
            while seg and (seg[0].startswith("-") or re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]*=.*", seg[0])):
                o = seg.pop(0)
                if o in con_valor and seg:
                    seg.pop(0)
            if p == "timeout" and seg and re.fullmatch(r"[\d.]+[smhd]?", seg[0]):
                seg.pop(0)
            if p in ("nice", "taskset", "chrt") and seg and re.fullmatch(r"-?\d+|0x[0-9a-f]+", seg[0]):
                seg.pop(0)
        else:
            break
    return (os.path.basename(seg[0]), seg[1:]) if seg else ("", [])


CON_VALOR = {"-s", "-u", "-U", "-g", "-G", "-P", "-t", "-F", "-d", "--signal", "--session", "--uid",
             "--euid", "--group", "--pgroup", "--parent", "--terminal", "--pidfile", "--ns", "--nslist",
             "--delimiter", "--runstates", "--cgroup", "-r"}


def patron_de(args):
    """(-f, -x, patrón, filtros) de un pkill/pgrep: el patrón es el primer argumento que no es opción;
    los filtros, los valores de -u/-U/--uid/--euid (usuarios) y de -P/--parent."""
    full = exacto = False
    patron, i, filtros = None, 0, {"usuarios": [], "padre": False}
    while i < len(args):
        a = args[i]
        if a == "--":
            patron = args[i + 1] if i + 1 < len(args) else None
            break
        clave, _, valor = a.partition("=")
        if a in ("-f", "--full"):
            full = True
        elif a in ("-x", "--exact"):
            exacto = True
        elif clave in ("-u", "-U", "--uid", "--euid"):
            filtros["usuarios"] += (valor or (args[i + 1] if i + 1 < len(args) else "")).split(",")
            i += 0 if valor else 1
        elif clave in ("-P", "--parent"):
            filtros["padre"] = True
            i += 0 if valor else 1
        elif a in CON_VALOR:
            i += 1
        elif a.startswith("--"):
            pass
        elif a.startswith("-") and len(a) > 1:
            if re.fullmatch(r"-[A-Za-z]+", a):
                full = full or "f" in a[1:]
                exacto = exacto or "x" in a[1:]
        elif patron is None:
            patron = a
        i += 1
    return full, exacto, patron, filtros


def soy(usuarios):
    """¿Alguno de esos usuarios (nombre o uid) es el que corre esto, que es el de la shell del Bash?"""
    import pwd
    uid = os.getuid()
    try:
        nombre = pwd.getpwuid(uid).pw_name
    except KeyError:
        nombre = ""
    # un usuario que solo se sabe al ejecutar (`-u "$USER"`, `-u "$(id -un)"`) puede ser él: cuenta como sí
    return any(u in (str(uid), nombre) or "$" in u or "__SUST" in u for u in usuarios if u)


def se_mata(args):
    """¿Ese pgrep/pkill -f casaría con la shell que lo lanza? Con -P/--parent solo mira los hijos de un
    proceso, y con -u/-U los de otros usuarios no incluyen a la shell: esos no se matan a sí mismos."""
    full, exacto, patron, filtros = patron_de(args)
    if not full or not patron or "$" in patron or "`" in patron or "__SUST" in patron:
        return None
    if filtros["padre"] or (filtros["usuarios"] and not soy(filtros["usuarios"])):
        return None
    return patron if casa_consigo(patron, exacto) else None


def kill_mata(args):
    """`kill` de verdad: no `kill -0` ni `kill -s 0` (solo preguntan) ni `kill -l`."""
    for i, a in enumerate(args):
        if a in ("-0", "-l", "-L") or (a in ("-s", "-n", "--signal") and args[i + 1:i + 2] == ["0"]):
            return False
    return True


def pgrep_que_mata(texto):
    """Un pgrep -f que se mata a sí mismo dentro de este texto (el de una sustitución)."""
    for seg, _ in simples(texto):
        prog, args = nucleo(seg)
        if prog == "pgrep":
            p = se_mata(args)
            if p:
                return p
    return None


def sust_que_mata(tok):
    """Si la palabra lleva una sustitución con un pgrep -f que se mata, su patrón."""
    for n in re.findall(r"__SUST(\d+)__", tok):
        p = pgrep_que_mata(SUST[int(n)])
        if p:
            return p
    return None


DECLARA = {"local", "export", "declare", "typeset", "readonly"}
LEE = {"read", "readarray", "mapfile"}


def asignaciones(seg):
    """[(variable, valor)] de las asignaciones de un segmento: `x=…` al principio, o tras
    local/export/declare/typeset/readonly (con sus opciones); `x=(…)` llega partido por el «(»."""
    out, i = [], 0
    if seg and seg[0] in DECLARA:
        i = 1
        while i < len(seg) and seg[i].startswith("-"):
            i += 1
        for t in seg[i:]:
            m = re.match(r"([A-Za-z_][A-Za-z0-9_]*)=(.*)", t, re.S)
            if m:
                out.append((m.group(1), m.group(2)))
        return out
    for t in seg:
        m = re.match(r"([A-Za-z_][A-Za-z0-9_]*)=(.*)", t, re.S)
        if not m:
            break
        out.append((m.group(1), m.group(2)))
    return out


def mira(texto, prof=0):
    """Un pkill -f que se mata, o un kill alimentado por un pgrep -f que se mata: directamente
    (`kill $(pgrep -f X)`), por una variable (`pids=$(pgrep -f X); kill $pids`, `for p in
    $(pgrep -f X)`, `pgrep -f X | while read p`, `done < <(pgrep -f X)`, `readarray -t p < <(…)`,
    `pids=($(…))`, `q=$p`) o por `| … | xargs kill`. Las variables se siguen en orden: una que se
    vuelve a asignar con otra cosa deja de contar."""
    if prof > 4:
        return None
    lista = simples(texto)
    nucleos = [nucleo(seg) for seg, _ in lista]
    # ¿lee algún bucle de una sustitución de proceso con un pgrep -f que se mata? (`done < <(pgrep …)`)
    lee_de_pgrep = any(t == "<" and k + 1 < len(seg) and sust_que_mata(seg[k + 1])
                       or (t.startswith("<") and sust_que_mata(t[1:]))
                       for seg, _ in lista for k, t in enumerate(seg))
    # qué segmentos reciben por la tubería la salida de un pgrep -f que se mata
    tras_pgrep, en_tubo = set(), False
    for k, ((seg, sep), (prog, args)) in enumerate(zip(lista, nucleos)):
        if en_tubo:
            tras_pgrep.add(k)
        if prog == "pgrep" and se_mata(args):
            en_tubo = True
        if sep not in ("|", "|&"):
            en_tubo = False
    hay = None
    for (seg, _), (prog, args) in zip(lista, nucleos):
        hay = hay or (se_mata(args) if prog == "pgrep" else None)
        for t in seg:
            hay = hay or sust_que_mata(t)
    sucias = set()

    def ensucia(valor):
        return bool(sust_que_mata(valor)) or any(v in sucias for v in re.findall(r"\$\{?([A-Za-z_][A-Za-z0-9_]*)", valor))

    for k, ((seg, sep), (prog, args)) in enumerate(zip(lista, nucleos)):
        for var, valor in asignaciones(seg):
            if valor == "" and sep == "(" and k + 1 < len(lista):   # x=( $(pgrep …) )
                valor = " ".join(lista[k + 1][0])
            (sucias.add if ensucia(valor) else sucias.discard)(var)
        if prog == "for" and len(args) >= 2 and args[1] == "in":
            (sucias.add if any(ensucia(t) for t in args[2:]) else sucias.discard)(args[0])
        if prog in LEE:
            de_pgrep = (k in tras_pgrep or lee_de_pgrep
                        or any(t == "<" and j + 1 < len(args) and sust_que_mata(args[j + 1])
                               for j, t in enumerate(args)))
            nombres = [a for a in args if re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]*", a)]
            for v in nombres:
                (sucias.add if de_pgrep else sucias.discard)(v)
        if prog == "pkill":
            p = se_mata(args)
            if p:
                return ("pkill -f", p)
        elif prog == "kill" and kill_mata(args):
            for a in args:
                p = sust_que_mata(a)
                if p:
                    return ("kill con pgrep -f", p)
                if any(v in sucias for v in re.findall(r"\$\{?([A-Za-z_][A-Za-z0-9_]*)", a)):
                    return ("kill con pgrep -f", hay)
        elif prog == "pgrep" and se_mata(args):
            j, s = k, sep                              # sigue la tubería: pgrep -f X | head -1 | xargs kill
            while s in ("|", "|&") and j + 1 < len(lista):
                j += 1
                sig, sargs = nucleos[j]
                s = lista[j][1]
                if sig != "xargs":
                    continue
                i = 0
                while i < len(sargs) and sargs[i].startswith("-"):
                    i += 2 if sargs[i] in ("-n", "-I", "-P", "-L", "-d", "-s", "-E", "-a") else 1
                orden, oargs = nucleo(sargs[i:])        # xargs sudo kill, xargs -r kill -9
                if orden == "kill" and kill_mata(oargs):
                    return ("kill con pgrep -f", se_mata(args))
        elif prog in ("bash", "sh", "zsh", "dash", "su") and "-c" in args:
            i = args.index("-c")
            if i + 1 < len(args):
                r = mira(aparta_sustituciones(sin_comentarios(sin_heredocs(args[i + 1]))), prof + 1)
                if r:
                    return r
    return None


principal = aparta_sustituciones(sin_comentarios(sin_heredocs(cmd)))
hallado = mira(principal)
k = 0
while not hallado and k < len(SUST):              # lo que corre dentro de $( … ) también se ejecuta
    hallado = mira(SUST[k]); k += 1

if hallado:
    via, patron = hallado
    print(f"guard-pkill: BLOQUEADO — `{via} {patron!r}` mataría también la shell que lo lanza: el patrón "
          "aparece en la propia línea de órdenes de esa shell (pkill se excluye a sí mismo, no a su "
          "shell). Acaba en exit 144 y lo que va detrás no corre.\n"
          "  Alternativas:\n"
          "   · por PID: guárdalo al lanzar (`cmd & echo $! > .run/x.pid`) y `kill \"$(cat .run/x.pid)\"`\n"
          "   · por nombre exacto del proceso: `pkill -x <nombre>` (mira el nombre, no la línea)\n"
          "   · anclado al binario: `pkill -f '^/ruta/.venv/bin/<binario>'` (la shell empieza por /bin/bash)\n"
          "  Un corchete (`pkill -f '[c]elery'`) vale solo si el patrón tampoco sale en el envoltorio del "
          "Bash (`~/.claude/shell-snapshots/…`, los `export` de los plugins): mira tu línea con "
          "`tr '\\0' ' ' < /proc/$$/cmdline`, y qué caería con `pgrep -af '<el patrón>'`. "
          "Regla: rules/recovery-patterns.md §Parar un proceso.")
PY
)
RC=$?
if [ $RC -ne 0 ]; then
  roto "detector rc=$RC"
fi
if [ -n "$MOTIVO" ]; then
  printf '%s\n' "$MOTIVO" >&2
  exit 2
fi
exit 0
