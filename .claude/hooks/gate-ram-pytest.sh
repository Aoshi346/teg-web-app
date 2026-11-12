#!/usr/bin/env bash
# ══════════════════════════════════════════════════════════════════════════════════════════════
# gate-ram-pytest.sh — hace que `check-ram.sh` dispare de verdad antes de CADA pytest, y solo entonces.
#
# POR QUÉ EXISTE (medido el 2026-09-05, rules/harness-gotchas.md §matchers). En Claude Code 2.1.261
# un hook con `"matcher": "Bash(pytest*)"` NO casa nunca: los matchers de hooks son regex sobre el
# NOMBRE de la tool («Bash», «Write|Edit»); la sintaxis `Tool(patrón)` es de permissions, no de
# hooks. El bloque heredado (y el del template) llevaba sin disparar desde que se escribió — lo que
# protegía la RAM era la regla de correr `bash .claude/hooks/check-ram.sh` a mano. Verde por
# casualidad, no por mecanismo (CLAUDE.md §7).
#
# QUÉ HACE: con matcher `Bash`, lee tool_input.command y, SOLO si el comando LANZA un pytest, llama
# al `check-ram.sh` canónico y traduce su exit 1 a exit 2, que es el único que bloquea en un
# PreToolUse (el 1 es «error no bloqueante»: el pytest habría seguido). El motivo sale por STDERR:
# con un exit 2, Claude Code le enseña al modelo el stderr y descarta el stdout. Un comando que no
# contiene «pytest» sale con 0 sin arrancar python.
#
# «LANZA un pytest» (MO-23, sub-ola 2.04, 2026-10-20). La regex de antes casaba «pytest» detrás de
# cualquier espacio: saltaba con un `echo`, un `grep pytest`, un mensaje de commit o un encargo a otro
# agente que decía «no ejecutes pytest» (musa #41), y no veía `.venv/bin/pytest` ni `bash -c "pytest …"`
# (medido sobre unos 3.000 comandos reales de los transcripts: `_archive/2026-10-20/medicion-2.04/`).
# Ahora el comando se trocea como lo haría la shell (comillas, `;` `&&` `||` `|`, saltos de línea,
# `$( )`, heredocs y comentarios) y:
#   · CUENTA pytest/py.test (también con ruta), `python -m pytest`, y eso mismo detrás de variables
#     (`X=1 pytest`), de envoltorios (`timeout`, `nice`, `env`, `xargs`, `watch`, `uv run`, `poetry run`,
#     `python -m coverage`…), dentro de `bash -c`, `su -c`, `script -c`, `tmux new|send-keys`, `$( )`, un
#     heredoc o un `echo … |` a una shell, `git rebase --exec`, `docker compose exec`, una variable
#     asignada en el mismo comando (`R="poetry run pytest $T"; $R`, expandida una vez y con tope de
#     tamaño), un comando que no conoce (`$PY -m pytest`, `$(…) pytest`, `lab_sh.sh -- bash -c …`) o
#     Python que lo lanza (`pytest.main`, `subprocess.run([… "pytest" …])`, `os.system`: se mira su
#     árbol con `ast`, así que `print("pytest.main()")` no cuenta);
#   · NO CUENTA lo que va de argumento a un comando que no ejecuta nada (`echo`, `grep`, `git`, `pip`,
#     `cat`, `ps`…), un nombre suelto entre comillas, heredocs que escriben un fichero, comentarios, el
#     encargo a otro agente (`codex`, `claude`) ni `ssh` (es otra máquina);
#   · si el comando nombra pytest y EJECUTA un fichero (`bash backend/pt`, `python x.py`, `./run`), lee
#     ese fichero —o el heredoc que lo escribe en el mismo comando— y cuenta si lo lanza; si no lo puede
#     leer, mide: ante la duda, se mide. Un falso positivo solo frena cuando la RAM de verdad no llega;
#     un falso negativo es un OOM.
# Sin python3, si el detector falla o si no decide en 2 s (o el comando está demasiado anidado), cae a
# una regex ancha (cualquier «pytest» suelto): se mide. Límite
# conocido: un pytest dentro de un script que el comando no nombra (`make test`, `bash tests.sh` a
# secas) no se ve, igual que antes.
#
# MODOS: (stdin JSON PreToolUse) · --cmd "<comando>" (smoke) · --detecta "<comando>" (dice «pytest»
# o «no» y sale 0/1, sin medir nada). GATE_RAM_TRACE=<fichero> deja marca de que check-ram llegó a
# correr (para el smoke, que no puede depender de cuánta RAM haya).
# ══════════════════════════════════════════════════════════════════════════════════════════════
set -uo pipefail

# El detector, en python3: solo se arranca si el comando contiene «pytest». Sale 10 si lo lanza, 11 si
# no, 12 si no sabe decidirlo a tiempo (más de 2 s o demasiado anidado); cualquier otro código es que
# falló. El comando le llega por el fd 3, no por argv: por argv no caben más de 128 KB (E2BIG).
detector() {
  python3 -I - "$2" 3<<<"$1" <<'PY'
import ast
import os
import re
import signal
import sys

PYTEST = re.compile(r'^(pytest|py\.test|pytest-3)$')
PYTHON = re.compile(r'^(python|pypy)(\d+(\.\d+)*)?$')
PYMOD = ('pytest', 'py.test')
SHELLS = {'bash', 'sh', 'zsh', 'dash', 'ksh'}
ASSIGN = re.compile(r'^[A-Za-z_][A-Za-z0-9_]*\+?=')
RESERVED = {'!', '{', '}', 'if', 'then', 'else', 'elif', 'do', 'while', 'until'}
# envoltorio -> (opciones que llevan argumento, posicionales antes del comando)
WRAP = {
    'env': ({'-u', '--unset', '-C', '--chdir'}, 0), 'time': ({'-f', '--format', '-o', '--output'}, 0),
    'nice': ({'-n', '--adjustment'}, 0), 'ionice': ({'-c', '--class', '-n', '--classdata'}, 0),
    'nohup': (set(), 0), 'exec': ({'-a'}, 0), 'chronic': (set(), 0), 'unbuffer': (set(), 0),
    'sudo': ({'-u', '--user', '-g', '--group', '-h', '--host', '-p', '--prompt', '-C', '-D', '--chdir'}, 0),
    'doas': ({'-u', '-C'}, 0), 'stdbuf': ({'-i', '-o', '-e'}, 0),
    'timeout': ({'-s', '--signal', '-k', '--kill-after'}, 1), 'taskset': (set(), 1),
    'xvfb-run': ({'-n', '--server-num', '-s', '--server-args', '-f', '--auth-file', '-e', '--error-file'}, 0),
    'watch': ({'-n', '--interval'}, 0), 'uvx': ({'--with', '--from', '--python', '-p'}, 0),
    'xargs': ({'-a', '--arg-file', '-d', '--delimiter', '-E', '-I', '-L', '-n', '--max-args', '-P',
               '--max-procs', '-s', '--max-chars'}, 0),
}
# herramienta que lanza con «run» -> opciones con argumento (antes y después de «run»)
RUN = {
    'uv': {'--with', '--with-editable', '--with-requirements', '--python', '-p', '--group', '--extra',
           '--package', '--project', '--directory', '--env-file', '--index', '--only-group', '--no-group'},
    'poetry': {'-C', '--directory', '-P', '--project'}, 'pipenv': set(), 'pdm': {'-p', '--project'},
    'hatch': {'-e', '--env'}, 'rye': set(), 'pixi': {'-e', '--environment', '--manifest-path'},
    'pipx': {'--spec', '--python'}, 'conda': {'-n', '--name', '-p', '--prefix', '--cwd'},
    'mamba': {'-n', '--name', '-p', '--prefix', '--cwd'}, 'micromamba': {'-n', '--name', '-p', '--prefix'},
}
# Comandos cuyos argumentos son texto o ficheros y nunca un comando que se lance: con ellos, «pytest» es
# un dato (grep pytest, git commit -m "…pytest…", pip install pytest, codex exec "no ejecutes pytest").
INERTE = {
    'echo', 'printf', 'grep', 'egrep', 'fgrep', 'zgrep', 'rg', 'ag', 'ack', 'cat', 'tac', 'head', 'tail', 'less',
    'more', 'ls', 'tree', 'which', 'whereis', 'type', 'sed', 'awk', 'gawk', 'jq', 'yq', 'wc', 'diff', 'cmp', 'sort',
    'uniq', 'cut', 'tr', 'tee', 'touch', 'mkdir', 'cp', 'mv', 'rm', 'ln', 'chmod', 'chown', 'stat', 'file', 'du',
    'basename', 'dirname', 'realpath', 'readlink', 'pip', 'pip3', 'vim', 'vi', 'nano', 'curl', 'wget', 'gh',
    'test', '[', '[[', 'read', 'export', 'unset', 'local', 'declare', 'cd', 'true', 'false', ':', 'man',
    'ps', 'pgrep', 'pkill', 'kill', 'killall', 'sleep', 'wait', 'git',
    'ssh', 'scp',       # en otra máquina: no gasta la RAM de esta
    'codex', 'claude',  # el encargo a otro agente es texto; lo que ese agente corra no pasa por este hook
}
CONTENEDOR = {'docker', 'podman', 'docker-compose', 'podman-compose', 'kubectl', 'oc'}
# Al buscar dónde empieza el comando dentro de los argumentos de otro (docker exec web …, lab_sh.sh -- …), lo que
# sigue a uno de estos son argumentos suyos: docker exec web grep pytest. Más corto que INERTE a propósito: `test`
# o `cd` también son nombres de servicio, de perfil o de directorio (docker compose exec test pytest).
MIRAR = {'grep', 'egrep', 'fgrep', 'zgrep', 'rg', 'ag', 'ack', 'echo', 'printf', 'cat', 'tac', 'head', 'tail',
         'less', 'more', 'ls', 'tree', 'which', 'whereis', 'type', 'sed', 'awk', 'gawk', 'jq', 'yq', 'wc', 'pip',
         'pip3', 'ps', 'pgrep', 'pkill', 'git', 'gh'}
# python -m <esto> … corre otro módulo de Python: coverage, perfiladores y depuradores
PY_ENVUELVE = {'coverage', 'cProfile', 'profile', 'trace', 'pdb', 'memray', 'pyinstrument', 'scalene', 'debugpy',
               'viztracer'}
# comandos que ejecutan el texto que va detrás de su -c (su www -c "…", script -qc "…", flock f -c "…")
CON_C = {'su', 'runuser', 'script', 'flock', 'sg'}
TMUX_LANZA = {'new', 'new-session', 'new-window', 'neww', 'split-window', 'splitw', 'send-keys', 'send',
              'respawn-pane', 'respawn-window', 'run-shell', 'run'}
VAR = re.compile(r'^\$\{?([A-Za-z_][A-Za-z0-9_]*)\}?$')
VAR_DEF = re.compile(r'^\$\{([A-Za-z_][A-Za-z0-9_]*):?[-=]([^}]*)\}$')  # ${PYTEST:-pytest}
VAR_REF = re.compile(r'\$\{([A-Za-z_][A-Za-z0-9_]*)(?:(:?[-=+?])([^}]*))?\}|\$([A-Za-z_][A-Za-z0-9_]*)')
TMUX_CON_ARG = {'-s', '-n', '-c', '-t', '-x', '-y', '-F', '-e', '-f', '-l', '-L', '-S', '-N', '-T', '-b'}
# opciones de docker/podman run|exec, compose run|exec y kubectl exec que llevan argumento
CONT_RUN_ARG = {'-e', '--env', '--env-file', '--name', '-w', '--workdir', '-u', '--user', '-v', '--volume', '-p',
                '--publish', '--network', '--net', '--entrypoint', '-l', '--label', '--mount', '-c', '--container',
                '-n', '--namespace', '--platform', '--pull', '-m', '--memory', '--cpus', '--hostname', '-h',
                '--add-host', '--cap-add', '--cap-drop', '--device', '--gpus', '--ipc', '--pid', '--restart',
                '--runtime', '--security-opt', '--shm-size', '--tmpfs', '--ulimit', '--volumes-from', '--index',
                '--detach-keys', '--log-driver', '--log-opt', '--memory-swap', '--label-file', '--cidfile',
                '--dns', '--image', '--profile'}


class Hondo(Exception):
    """Demasiado anidado para decidir: se mide (el bash de fuera cae a la regex ancha)."""
LIMITE = 64 * 1024  # una expansión de variables más grande no se hace: se mide (A='$A $A …'; $A)
# $(which pytest) apps/x: la sustitución da la ruta de pytest
SUB_RUTA = re.compile(r'^(\$\(|`)\s*(which|command\s+-v|type\s+-[pP]|echo|printf|realpath|readlink\s+-f)\s+'
                      r'(?:[^)`]*[^A-Za-z0-9_.-])?(pytest|py\.test)\b')
GIT_CON_ARG = {'-C', '-c', '--git-dir', '--work-tree', '--namespace', '--exec-path'}
# docker <sub> / docker compose <sub> / kubectl <sub>: solo estos lanzan un comando dentro
CONT_LANZA = {'exec', 'run', 'debug'}
CONT_CON_ARG = {'-H', '--host', '--context', '-c', '--config', '-l', '--log-level', '-f', '--file', '-p',
                '--project-name', '--profile', '--env-file', '--project-directory', '--ansi', '--progress', '-n',
                '--namespace', '--kubeconfig', '--cluster', '--user', '-s', '--server'}
# Un script de Python que lanza pytest desde dentro (python - <<EOF … EOF, o un .py que se escribe y se corre)
PY_MAIN = re.compile(r'\bpytest\s*\.\s*main\s*\(|from\s+pytest\s+import\s+[^\n;]*\bmain\b|'
                     r'__import__\(\s*[\'"]pytest[\'"]\s*\)\s*\.\s*main')
PY_LANZA = re.compile(PY_MAIN.pattern + r'|[\'"]-m[\'"]\s*,\s*[\'"]pytest[\'"]|'
                      r'(subprocess|os\.system|os\.popen)\b[^\n]*[\'"\s\[(/]pytest\b')


class Q(str):
    """Una palabra que llevaba comillas: «pytest» entre comillas, suelto, es un dato y no un comando."""


def base(t):
    return t.rsplit('/', 1)[-1]


def sustituciones(texto):
    """Los $(…) y `…` de un texto que la shell expande (un heredoc con delimitador sin comillas)."""
    subs, j, n = [], 0, len(texto)
    while j < n:
        if texto[j] == '\\':
            j += 2
        elif texto.startswith('$((', j):
            k = texto.find('))', j); j = n if k < 0 else k + 2
        elif texto.startswith('$(', j):
            t, sb, j = lex(texto, j + 2, cierre=True); subs.append((t, sb))
        elif texto[j] == '`':
            k = texto.find('`', j + 1); k = n if k < 0 else k
            t, sb, _ = lex(texto[j + 1:k]); subs.append((t, sb)); j = k + 1
        else:
            j += 1
    return subs


def lex(s, i=0, cierre=False):
    """Trocea un comando de shell. Devuelve (tokens, subcomandos, fin). Las comillas se quitan (la palabra
    queda marcada como Q), lo que hay dentro de $(…), `…` y <(…) sale aparte (se ejecuta) y el cuerpo de
    un heredoc va pegado a su comando: es texto, salvo si el comando es una shell."""
    n = len(s)
    toks, subs, pend = [], [], []
    cur, est = [], {'tiene': False, 'q': False}
    prof = 0

    def suelta():
        if est['tiene']:
            txt = ''.join(cur)
            toks.append(('w', Q(txt) if est['q'] else txt))
        del cur[:]
        est['tiene'] = est['q'] = False

    def palabra(txt, q=False):
        cur.append(txt); est['tiene'] = True
        if q:
            est['q'] = True

    def sub_paren(j):
        t, sb, k = lex(s, j, cierre=True)
        subs.append((t, sb))
        return k

    def sub_tilde(j):  # `…` desde j (j apunta tras la primera tilde)
        k = j
        while k < n and s[k] != '`':
            k += 2 if s[k] == '\\' else 1
        t, sb, _ = lex(s[j:k])
        subs.append((t, sb))
        return k + 1

    while i < n:
        c = s[i]
        if c == '\\':
            if s.startswith('\\\n', i):
                i += 2
                continue
            palabra(s[i + 1:i + 2], q=True); i += 2
            continue
        if c == "'":
            j = s.find("'", i + 1); j = n if j < 0 else j
            palabra(s[i + 1:j], q=True); i = j + 1
            continue
        if s.startswith("$'", i):
            j = i + 2
            while j < n and s[j] != "'":
                j += 2 if s[j] == '\\' else 1
            palabra(s[i + 2:j], q=True); i = j + 1
            continue
        if c == '"':
            j = i + 1; buf = []
            while j < n and s[j] != '"':
                if s[j] == '\\':
                    buf.append(s[j + 1:j + 2]); j += 2
                elif s.startswith('$((', j):
                    k = s.find('))', j); k = n if k < 0 else k + 2
                    buf.append(s[j:k]); j = k
                elif s.startswith('$(', j):
                    j0 = j; j = sub_paren(j + 2); buf.append(s[j0:j])
                elif s[j] == '`':
                    j0 = j; j = sub_tilde(j + 1); buf.append(s[j0:j])
                else:
                    buf.append(s[j]); j += 1
            palabra(''.join(buf), q=True); i = j + 1
            continue
        if s.startswith('$((', i):
            k = s.find('))', i); k = n if k < 0 else k + 2
            palabra(s[i:k]); i = k
            continue
        if s.startswith('$(', i) or s.startswith('<(', i) or s.startswith('>(', i):
            i0 = i; i = sub_paren(i + 2); palabra(s[i0:i])
            continue
        if c == '`':
            i0 = i; i = sub_tilde(i + 1); palabra(s[i0:i])
            continue
        if c in ' \t\r':
            suelta(); i += 1
            continue
        if c == '#' and not est['tiene']:
            j = s.find('\n', i); i = n if j < 0 else j
            continue
        if c == '\n':
            suelta(); i += 1
            for caja, delim, tabs, expande in pend:  # el cuerpo de cada heredoc empieza en la línea siguiente
                cuerpo = []
                while i < n:
                    j = s.find('\n', i); j = n if j < 0 else j
                    linea = s[i:j]
                    cmp = linea.lstrip('\t') if tabs else linea
                    if cmp.rstrip() == delim:
                        i = j + 1
                        break
                    if cmp.startswith(delim + ')'):  # $(cat <<EOF … EOF)
                        i += len(linea) - len(cmp) + len(delim)
                        break
                    cuerpo.append(linea); i = j + 1
                texto = '\n'.join(cuerpo)
                caja.append(texto)
                if expande:  # <<EOF sin comillas: la shell ejecuta los $(…) y `…` del cuerpo
                    subs.extend(sustituciones(texto))
            pend = []
            toks.append(('sep', '\n'))
            continue
        if s.startswith('<<', i) and not s.startswith('<<<', i):
            suelta(); j = i + 2; tabs = False; expande = True
            if j < n and s[j] == '-':
                tabs = True; j += 1
            while j < n and s[j] in ' \t':
                j += 1
            d = []
            while j < n and s[j] not in ' \t\n;&|()<>':
                if s[j] in '\'"':
                    k = s.find(s[j], j + 1); k = n if k < 0 else k
                    d.append(s[j + 1:k]); j = k + 1; expande = False
                elif s[j] == '\\':
                    d.append(s[j + 1:j + 2]); j += 2; expande = False
                else:
                    d.append(s[j]); j += 1
            caja = []
            pend.append((caja, ''.join(d), tabs, expande))
            toks.append(('hd', caja)); i = j
            continue
        if c in '<>' or s.startswith('&>', i):
            if est['tiene'] and not est['q'] and ''.join(cur).isdigit():
                del cur[:]; est['tiene'] = False  # el 2 de 2>&1 es un descriptor, no un argumento
            suelta(); j = i + 1
            while j < n and s[j] in '<>&|':
                j += 1
            if s[j - 1] == '&':  # >&2, 2>&1: lo que sigue es un descriptor
                while j < n and (s[j].isdigit() or s[j] == '-'):
                    j += 1
            i = j
            continue
        if c in ';&|':
            suelta(); j = i + 1
            if j < n and s[j] in ';&|':
                j += 1
            toks.append(('sep', s[i:j])); i = j
            continue
        if c == '(':
            suelta(); prof += 1; toks.append(('sep', '(')); i += 1
            continue
        if c == ')':
            suelta()
            if cierre and prof == 0:
                return toks, subs, i + 1
            prof = max(0, prof - 1); toks.append(('sep', ')')); i += 1
            continue
        palabra(c); i += 1
    suelta()
    return toks, subs, i


def comandos(toks):
    """[(palabras, cuerpos de heredoc, separador de delante)] por cada comando simple."""
    out, w, hd, sep = [], [], [], ''
    for t in toks:
        if t[0] == 'w':
            w.append(t[1])
        elif t[0] == 'hd':
            hd.append(t[1])
        else:
            out.append((w, hd, sep)); w, hd, sep = [], [], t[1]
    out.append((w, hd, sep))
    return out


def expande(texto, ctx):
    """Sustituye, en una pasada, las variables que este mismo comando asignó (R="timeout 900 pytest $T"; $R).
    Si el resultado pasara de LIMITE, devuelve el texto sin tocar: una variable que se cita a sí misma no
    puede hacer crecer la expansión (la 2.ª pasada del verificador la llevó a 700 MB)."""
    if '$' not in texto:
        return texto  # (sin variables apuntadas sigue habiendo que resolver ${X:-def})
    tam = [len(texto)]

    def sust(m):
        nom, op, defecto = m.group(1) or m.group(4), m.group(2), m.group(3)
        v = ctx.vars.get(nom)
        if op and (v is None or (op.startswith(':') and v == '')) and op.lstrip(':') in '-=':
            v = defecto  # ${PY:-python3}: si no está asignada, el valor por defecto
        if v is None:
            return m.group(0)
        tam[0] += len(v)
        if tam[0] > LIMITE:
            raise OverflowError
        return v
    try:
        return VAR_REF.sub(sust, texto)
    except OverflowError:
        return texto


def apunta_vars(palabras, ctx):
    for t in palabras:
        if ASSIGN.match(t):
            k, v = t.split('=', 1)
            ctx.vars[k.rstrip('+')] = expande(v, ctx)  # F=$SP/x con SP ya asignada: se guarda resuelta


def py_lanza(codigo):
    """¿Este código de Python lanza pytest? Con su árbol: pytest.main(…), main(…) importado de pytest,
    __import__('pytest').main(…), o subprocess/os.system con pytest como programa. Si no es Python
    válido, la regex de siempre."""
    try:
        arbol = ast.parse(codigo)
    except Exception:
        return PY_LANZA.search(codigo) is not None
    alias_pytest, alias_main, alias_mod, alias_fun = {'pytest'}, set(), {}, {}
    for n in ast.walk(arbol):
        if isinstance(n, ast.Import):
            alias_pytest |= {a.asname or a.name for a in n.names if a.name == 'pytest'}
            alias_mod.update({a.asname: a.name for a in n.names if a.asname and a.name in ('subprocess', 'os')})
        elif isinstance(n, ast.ImportFrom) and n.module == 'pytest':
            alias_main |= {a.asname or a.name for a in n.names if a.name == 'main'}
        elif isinstance(n, ast.ImportFrom) and n.module in ('subprocess', 'os'):
            alias_fun.update({(a.asname or a.name): n.module + '.' + a.name for a in n.names})

    def nombre(f):
        if isinstance(f, ast.Name):
            return f.id
        if isinstance(f, ast.Attribute):
            return nombre(f.value) + '.' + f.attr
        return ''

    def cadenas(x):
        if isinstance(x, (ast.List, ast.Tuple)):
            return [e.value for e in x.elts if isinstance(e, ast.Constant) and isinstance(e.value, str)]
        if isinstance(x, ast.Constant) and isinstance(x.value, str):
            return [x.value]
        if isinstance(x, ast.BinOp) and isinstance(x.op, ast.Add):  # base + ['pytest', '-q']
            return cadenas(x.left) + cadenas(x.right)
        if isinstance(x, ast.Call) and nombre(x.func) in ('shlex.split', 'split') and x.args:
            return [p for c in cadenas(x.args[0]) for p in c.split()]  # shlex.split('pytest apps/x')
        return []
    ejecuta, sueltos = False, []
    for n in ast.walk(arbol):
        if isinstance(n, ast.Assign) and isinstance(n.value, (ast.List, ast.Tuple)):
            c = cadenas(n.value)  # cmd = ['poetry', 'run', 'pytest'], que luego va a subprocess
            if c and detecta(' '.join(c)):
                sueltos.append(c)
        if not isinstance(n, ast.Call):
            continue
        f, nom = n.func, nombre(n.func)
        if nom in alias_fun:
            nom = alias_fun[nom]  # from subprocess import run
        elif nom.split('.')[0] in alias_mod:
            nom = alias_mod[nom.split('.')[0]] + nom[len(nom.split('.')[0]):]  # import subprocess as sp
        if isinstance(f, ast.Attribute) and f.attr == 'main' and (
                (isinstance(f.value, ast.Name) and f.value.id in alias_pytest) or
                (isinstance(f.value, ast.Call) and nombre(f.value.func) == '__import__' and
                 [c for a in f.value.args for c in cadenas(a)] == ['pytest'])):
            return True
        if nom in alias_main:
            return True
        if re.match(r'^(subprocess\.\w+|os\.(system|popen|exec\w*|spawn\w*)|(run|call|Popen|check_call|check_output))$', nom):
            ejecuta = True
            for a in n.args[:1]:
                c = cadenas(a)
                # os.system('pytest apps/x') · subprocess.run(['poetry', 'run', 'pytest', *T]) · [PY, '-m', 'pytest']
                if c and detecta(' '.join(c)):
                    return True
    return ejecuta and bool(sueltos)  # cmd = ['poetry', 'run', 'pytest']; …; subprocess.run(cmd)


def lee_stdin(w):
    """¿Es una shell que lee el script de la entrada estándar (… | bash, … | sh -s)?"""
    i = 0
    while i < len(w) and (w[i] in RESERVED or ASSIGN.match(w[i]) or base(w[i]) in ('sudo', 'env', 'nice', 'timeout')):
        i += 1 if base(w[i]) != 'timeout' else 2
    if i >= len(w) or base(w[i]) not in SHELLS:
        return False
    for a in w[i + 1:]:
        if a.startswith('-') and not a.startswith('--') and 'c' in a[1:]:
            return False
        if not a.startswith('-') and not a.startswith('+'):
            return False
    return True


class Ctx(object):
    """Lo que se ve a lo largo de un comando entero: scripts escritos con un heredoc, ficheros que se ejecutan
    y variables que se asignan (S=/tmp/x; bash $S/t.sh)."""
    def __init__(self):
        self.scripts, self.ficheros, self.vars, self.cwd = [], [], {}, CWD

    def ejecuta(self, tipo, ruta):
        self.ficheros.append((tipo, ruta, self.cwd))


def salta_opts(w, i, con_arg):
    while i < len(w) and w[i].startswith('-') and w[i] != '-':
        if w[i] == '--':
            return i + 1
        i += 2 if w[i] in con_arg else 1
    return i


def guarda_scripts(w, hd, ctx):
    """cat > t.sh <<EOF … EOF: si el texto es un script (.sh/.py o con #!), se apunta por si luego se corre."""
    destinos = [resuelve(a, ctx) for a in w[1:] if not a.startswith('-')]
    for c in hd:
        primera = c.lstrip().split('\n', 1)[0]
        if any(a.endswith(('.sh', '.bash')) for a in w) or (primera.startswith('#!') and 'sh' in primera):
            ctx.scripts.append(('sh', c, destinos))
        elif any(a.endswith('.py') for a in w) or (primera.startswith('#!') and 'python' in primera):
            ctx.scripts.append(('py', c, destinos))


def es_pytest(w, hd, prof, ctx, escanea=True):
    """¿Este comando simple lanza pytest? hd = cuerpos de sus heredocs. Con `escanea`, un comando que no
    se conoce (`$PY`, `make`, `./run.sh`, `lab_sh.sh … --`) se mira por dentro: si en algún punto de sus
    argumentos empieza algo que lanza pytest, cuenta (ante la duda, se mide)."""
    if prof > 8:
        raise Hondo
    i = 0
    while i < len(w):
        t, b = w[i], base(w[i])
        if t in RESERVED or ASSIGN.match(t):
            if ASSIGN.match(t) and escanea:
                apunta_vars([t], ctx)  # R="pytest apps/x" bash -c '$R'
            i += 1
        elif b == 'command':
            if i + 1 < len(w) and w[i + 1] in ('-v', '-V'):
                return False  # command -v pytest: solo pregunta dónde está
            i += 1
        elif b == 'watch':  # watch -n 60 "cd x && pytest": lo que sigue se lo pasa a sh -c
            i = salta_opts(w, i + 1, WRAP['watch'][0])
            return i < len(w) and detecta(expande(' '.join(w[i:]), ctx), prof + 1)
        elif b in WRAP:
            con_arg, npos = WRAP[b]
            i = salta_opts(w, i + 1, con_arg)
            while i < len(w) and ASSIGN.match(w[i]):
                i += 1
            i += npos
        elif b in RUN:
            j = salta_opts(w, i + 1, RUN[b])
            if j >= len(w) or w[j] != 'run':
                return False  # uv pip install pytest, poetry add pytest…
            i = salta_opts(w, j + 1, RUN[b])
            if i < len(w) and b == 'hatch' and ':' in w[i]:
                w = w[:i] + [w[i].split(':', 1)[1]] + w[i + 1:]
        else:
            break
    if i >= len(w):
        apunta_vars(w, ctx)  # S=/tmp/x o R="pytest $T" sin comando detrás: se apuntan para lo que sigue
        return False
    w, cw = w[i:], w[i]
    b = base(cw)
    m, md = VAR.match(cw), VAR_DEF.match(cw)
    if escanea and (m or md):  # solo en posición de comando: en `npm view $PKG`, $PKG es un argumento
        nom = (m or md).group(1)
        valor = ctx.vars.get(nom, md.group(2) if md and nom not in ctx.vars else None)
        v = expande(valor, ctx) if valor is not None else ''
        nuevo = [v] if v.startswith(('$(', '`')) else v.split()  # PT=$(which pytest); $PT apps/x
        if nuevo and nuevo[0] != cw:  # (PY=${PY:-…} sin resolver: no hay avance, se trata como desconocido)
            # $R con R="timeout 900 poetry run pytest $T" asignada en este mismo comando: se mira lo que vale
            return es_pytest(nuevo + list(w[1:]), hd, prof + 1, ctx, escanea)
    if cw.startswith(('$(', '`')):  # el comando lo da una sustitución: $(which pytest) apps/x, $(…) pytest …
        if SUB_RUTA.search(cw) or PYTEST.match(b):  # … o $(git rev-parse --show-toplevel)/.venv/bin/pytest
            return True
        return escanea_args(w, 1, prof, ctx) if escanea else False
    if any(ch.isspace() for ch in cw):
        return False  # una palabra con espacios viene de unas comillas: es texto, no un comando
    if PYTEST.match(b):
        return True
    if b == 'cd' and escanea and len(w) > 1:  # cd backend && bash pt …: las rutas siguientes van desde ahí
        destino = resuelve(w[1], ctx)
        if destino:
            ctx.cwd = destino
    if b == 'git':  # git [-C dir -c k=v --no-pager …] <sub>: rebase --exec, bisect run y submodule foreach lanzan
        k = 1
        while k < len(w) and w[k].startswith('-'):
            k += 2 if w[k] in GIT_CON_ARG else 1
        sub, resto = (w[k] if k < len(w) else ''), w[k + 1:]
        if sub == 'rebase':
            for j, a in enumerate(resto):
                if a in ('--exec', '-x') and j + 1 < len(resto) and detecta(expande(resto[j + 1], ctx), prof + 1):
                    return True
                if a.startswith('--exec=') and detecta(expande(a[7:], ctx), prof + 1):
                    return True
        if sub == 'bisect' and resto[:1] == ['run']:
            return es_pytest(list(resto[1:]), [], prof + 1, ctx, escanea)
        if sub == 'submodule' and 'foreach' in resto:
            j = resto.index('foreach') + 1
            while j < len(resto) and resto[j].startswith('-'):
                j += 1
            return detecta(expande(' '.join(resto[j:]), ctx), prof + 1)
        guarda_scripts(w, hd, ctx)
        return False
    if b in INERTE:
        if b in ('export', 'declare', 'local'):
            apunta_vars(w[1:], ctx)
        if b == ':':  # : ${PYTEST:=pytest}
            for a in w[1:]:
                md2 = re.match(r'^\$\{([A-Za-z_][A-Za-z0-9_]*):?=([^}]*)\}$', a)
                if md2 and not ctx.vars.get(md2.group(1)):  # := asigna si no está o está vacía
                    ctx.vars[md2.group(1)] = expande(md2.group(2), ctx)
        guarda_scripts(w, hd, ctx)
        return False
    if PYTHON.match(b):
        k = 1
        while k < len(w):
            a = w[k]
            if a == '-m' or re.match(r'^-[A-Za-z]*m$', a) or (a.startswith('-m') and not a.startswith('--')):
                mod, resto = (w[k + 1] if k + 1 < len(w) else '', w[k + 2:]) if a.endswith('m') else (a[2:], w[k + 1:])
                if mod in PYMOD:
                    return True
                if mod in PY_ENVUELVE:  # python -m coverage run -m pytest, python -m cProfile -o p -m pytest
                    return any(PYTEST.match(base(x)) for x in resto) or any(
                        x == '-m' and j + 1 < len(resto) and resto[j + 1] in PYMOD for j, x in enumerate(resto))
                return False  # python -m pip install pytest: otro módulo
            if a == '-c':
                return k + 1 < len(w) and py_lanza(w[k + 1])
            if a in ('-W', '-X', '--check-hash-based-pycs'):
                k += 2
            elif a.startswith('-') and a != '-':
                k += 1
            else:
                break
        if k >= len(w) or w[k] == '-':  # el script llega por la entrada estándar (python - <<EOF)
            return any(py_lanza(c) for c in hd)
        ctx.ejecuta('py', w[k])
        return escanea and escanea_args(w, k + 1, prof, ctx)  # python run.py pytest …
    if b == 'coverage':
        resto = w[1:]
        return any(PYTEST.match(base(a)) for a in resto) or any(
            a == '-m' and k + 1 < len(resto) and resto[k + 1] in PYMOD for k, a in enumerate(resto))
    if b in SHELLS:
        k = 1
        while k < len(w):
            a = w[k]
            if a in ('-o', '+o', '-O', '+O', '--rcfile', '--init-file'):
                k += 2
            elif a.startswith('-') and not a.startswith('--') and 'c' in a[1:]:
                return k + 1 < len(w) and detecta(expande(w[k + 1], ctx), prof + 1)  # bash -c "$R"
            elif a.startswith('-') or a.startswith('+'):
                k += 1
            else:
                ctx.ejecuta('sh', a)  # bash script.sh: se mira el script (detecta, al final)
                return False
        return any(detecta(c, prof + 1) for c in hd)  # bash <<EOF … EOF: el cuerpo es un script
    if b in ('source', '.') and escanea:
        if len(w) > 1:
            ctx.ejecuta('sh', w[1])
        return False
    if b == 'eval':
        return detecta(expande(' '.join(w[1:]), ctx), prof + 1)
    if b in CON_C:  # su www -c "…", script -qc "…", flock /tmp/l -c "…"
        for k, a in enumerate(w[1:], 1):
            if (a in ('-c', '--command') or re.match(r'^-[A-Za-z]*c$', a)) and k + 1 < len(w):
                return detecta(expande(w[k + 1], ctx), prof + 1)
    if b == 'tmux':  # tmux new -d '… pytest …', tmux send-keys "…"; tmux rename-window pytest, no
        if len(w) < 2 or w[1] not in TMUX_LANZA:
            return False
        k, args = 2, []
        while k < len(w):  # tmux new -s pytest: «pytest» es el nombre de la sesión
            if w[k].startswith('-') and w[k] != '-':
                k += 2 if w[k] in TMUX_CON_ARG else 1
            else:
                args.append(w[k]); k += 1
        return any(detecta(expande(a, ctx), prof + 1) for a in args)
    if b in CONTENEDOR:  # solo exec/run (docker compose exec test pytest); docker stop pytest, no
        k = 1
        while k < len(w):
            if w[k].startswith('-'):
                k += 2 if w[k] in CONT_CON_ARG else 1
            elif w[k] == 'compose':
                k += 1
            else:
                break
        if k >= len(w) or w[k] not in CONT_LANZA:
            return False
        k += 1
        entrada = None
        while k < len(w) and w[k].startswith('-'):  # docker run --name pytest img …: el nombre no es la orden
            if w[k] == '--':
                break
            if w[k] == '--entrypoint' and k + 1 < len(w):
                entrada = w[k + 1]
            elif w[k].startswith('--entrypoint='):
                entrada = w[k][13:]
            k += 2 if w[k] in CONT_RUN_ARG else 1
        if entrada and (PYTEST.match(base(entrada)) or detecta(expande(entrada, ctx), prof + 1)):
            return True  # docker run --entrypoint pytest img apps/x
        if k < len(w) and w[k] != '--':
            k += 1  # el servicio, contenedor, imagen o pod
        if b in ('kubectl', 'oc') and '--' in w[k:]:
            k = w.index('--', k)  # kubectl exec pod -c pytest -- ls: la orden va tras el --
        if k < len(w) and w[k] == '--':
            k += 1
        return es_pytest(list(w[k:]), [], prof + 1, ctx, escanea=False) or escanea_args(w, k, prof, ctx)
    # Contenedores y comandos que no se conocen: se busca dónde empieza lo que de verdad se lanza.
    if '/' in cw and escanea:
        ctx.ejecuta('?', cw)  # ./run.sh, /opt/x/bin/lanzar: se mira qué es
    if any(py_lanza(c) or detecta(c, prof + 1) for c in hd):
        return True  # $PY - <<EOF … EOF: el cuerpo lanza pytest
    for k, a in enumerate(w[1:] if escanea else (), 1):  # npx nodemon --exec "pytest apps/x"
        if a == '--exec' and k + 1 < len(w) and detecta(expande(w[k + 1], ctx), prof + 1):
            return True
        if a.startswith('--exec=') and detecta(expande(a[7:], ctx), prof + 1):
            return True
    if escanea:
        return escanea_args(w, 1, prof, ctx)
    return False


def escanea_args(w, desde, prof, ctx):
    for k in range(desde, len(w)):
        if base(w[k]) in MIRAR:
            return False  # docker exec web grep pytest: lo que sigue son argumentos de grep
        if isinstance(w[k], Q) and '/' not in w[k]:
            continue  # pgrep -f "pytest": un nombre suelto entre comillas es un dato
        if es_pytest(w[k:], [], prof + 1, ctx, escanea=False):
            return True
    return False


PALABRA = re.compile(r'(^|[^A-Za-z0-9_.-])(pytest|py\.test)([^A-Za-z0-9_.-]|$)')
CWD = os.getcwd()


def lanza_texto(tipo, texto, prof):
    if tipo == '?':  # ./algo: por el #! o, sin él, como script de shell
        primera = texto.split('\n', 1)[0]
        tipo = 'py' if (primera.startswith('#!') and 'python' in primera) else 'sh'
    return detecta(texto, prof + 1) if tipo == 'sh' else py_lanza(texto)


DATOS = ('.md', '.txt', '.json', '.jsonl', '.yaml', '.yml', '.html', '.csv', '.log', '.toml', '.ini', '.cfg')


def resuelve(ruta, ctx, cwd=None):
    ruta = os.path.expanduser(os.path.expandvars(expande(ruta, ctx)))  # F=$SP/x con SP=/tmp/y, en cadena
    return None if '$' in ruta else os.path.normpath(os.path.join(cwd or ctx.cwd, ruta))


def fichero_lanza(tipo, ruta, cwd, ctx, prof):
    """¿El fichero que este comando ejecuta lanza pytest? None si no se puede saber (no existe todavía: lo
    escribe este mismo comando sin que se vea cómo, o la ruta lleva una variable que no se resuelve)."""
    ruta = resuelve(ruta, ctx, cwd)
    if ruta is None:
        return None
    if tipo == '?' and ruta.endswith(DATOS):
        return False  # un fichero de datos no se ejecuta
    for t, c, destinos in ctx.scripts:  # lo escribe un heredoc de este mismo comando: se mira ese texto
        if ruta in destinos:
            return lanza_texto(t if tipo == '?' else tipo, c, prof)
    try:
        if not os.path.isfile(ruta):
            return None
        with open(ruta, 'rb') as fh:
            datos = fh.read(512 * 1024)
    except OSError:
        return None
    if b'\0' in datos[:1024]:
        return False  # un binario: no es un script
    return lanza_texto(tipo, datos.decode('utf-8', 'replace'), prof)


def detecta(cmd, prof=0):
    if prof > 6 or ('pytest' not in cmd and 'py.test' not in cmd):
        return False
    toks, subs, _ = lex(cmd)
    ctx = Ctx()
    if detecta_toks(toks, subs, prof, ctx):
        return True
    if not ctx.ficheros:
        return False  # nada se ejecuta: lo que diga «pytest» era texto
    # Se ejecuta un fichero y el comando nombra pytest. Cuenta si un heredoc de este comando escribe un
    # script que lo lanza (cat > t.sh <<EOF … pytest … EOF; bash t.sh), o si el fichero lo lanza o no se
    # puede leer (lo escribe este mismo comando): ante la duda, se mide.
    if any(lanza_texto(tipo, c, prof) for tipo, c, _ in ctx.scripts):
        return True
    if prof > 0:
        return False  # los ficheros se leen solo desde el comando de arriba
    for tipo, ruta, cwd in ctx.ficheros:
        r = fichero_lanza(tipo, ruta, cwd, ctx, prof)
        if r or (r is None and PALABRA.search(cmd)):
            return True
    return False


def detecta_toks(toks, subs, prof, ctx):
    if any(detecta_toks(t, sb, prof + 1, ctx) for t, sb in subs):
        return True
    cmds = comandos(toks)
    for n, (w, hd, sep) in enumerate(cmds):
        cuerpos = [c for caja in hd for c in caja]
        if es_pytest(w, cuerpos, prof, ctx):
            return True
        if sep in ('|', '|&') and n > 0 and lee_stdin(w):  # echo "pytest x" | bash · cat <<EOF | sh
            pw, phd, _ = cmds[n - 1]
            mv = VAR.match(pw[0]) if pw else None
            if mv and mv.group(1) in ctx.vars:  # CMD="echo pytest"; $CMD | bash
                pw = expande(ctx.vars[mv.group(1)], ctx).split() + list(pw[1:])
            texto = [c for caja in phd for c in caja]
            if pw and base(pw[0]) in ('echo', 'printf'):
                texto.append(' '.join(a for a in pw[1:] if not a.startswith('-')))
            if any(detecta(expande(t, ctx), prof + 1) for t in texto):
                return True
    return False


def _a_tiempo(*_):
    raise Hondo


if len(sys.argv) > 1 and sys.argv[1]:
    CWD = sys.argv[1]
try:  # el comando llega por el fd 3: por argv, más de 128 KB no caben (E2BIG, harness-gotchas.md)
    with os.fdopen(3, encoding='utf-8', errors='surrogateescape') as fh:
        COMANDO = fh.read()
except OSError:
    COMANDO = ''
if COMANDO.endswith('\n'):
    COMANDO = COMANDO[:-1]  # el que añade el <<<
signal.signal(signal.SIGALRM, _a_tiempo)
signal.setitimer(signal.ITIMER_REAL, 2.0)  # entrada hecha para tardar: a los 2 s, se mide
try:
    sys.exit(10 if detecta(COMANDO) else 11)
except (Hondo, RecursionError):
    sys.exit(12)
PY
}

MODO=hook
CWD_CMD="$PWD"
INPUT=""
case "${1:-}" in
  --cmd)     CMD="${2:-}" ;;
  --detecta) MODO=detecta; CMD="${2:-}" ;;
  *)
    INPUT=$(cat)
    if command -v jq >/dev/null 2>&1; then
      CMD=$(printf '%s' "$INPUT" | jq -r '.tool_input.command // empty' 2>/dev/null)
    elif command -v python3 >/dev/null 2>&1; then
      CMD=$(printf '%s' "$INPUT" | python3 -I -c 'import json,sys
try: print(json.load(sys.stdin).get("tool_input", {}).get("command", ""))
except Exception: pass' 2>/dev/null)
    else
      # Sin jq ni python3 no hay forma de leer el comando. FALLA CERRADO (PV-70): si el texto crudo
      # parece un pytest, se bloquea; si no, pasa (una guarda rota que bloqueara todo se quitaría).
      if grep -qE '(^|[^A-Za-z0-9_.-])(pytest|py\.test)([^A-Za-z0-9_.-]|$)' <<<"$INPUT"; then
        echo "gate-ram-pytest: sin jq ni python3 no puedo leer el comando y la entrada menciona pytest: bloqueado por si acaso." >&2
        exit 2
      fi
      exit 0
    fi ;;
esac
# JSON ilegible (truncado) con pytest dentro: CMD sale vacío y el gate dejaba pasar sin medir.
SIN_LEER=0
if [ -z "${CMD:-}" ] && [ -n "${INPUT:-}" ] && grep -qE '(^|[^A-Za-z0-9_.-])(pytest|py\.test)([^A-Za-z0-9_.-]|$)' <<<"$INPUT"; then
  SIN_LEER=1
fi

ES=no
case "${CMD:-}" in
  *pytest*|*py.test*)
    if command -v python3 >/dev/null 2>&1; then
      # El directorio del comando, para leer los scripts que ejecute (`bash backend/pt`)
      if [ -n "${INPUT:-}" ] && command -v jq >/dev/null 2>&1; then
        CWD_CMD=$(printf '%s' "$INPUT" | jq -r '.cwd // empty' 2>/dev/null)
        [ -n "$CWD_CMD" ] || CWD_CMD="$PWD"
      fi
      detector "$CMD" "$CWD_CMD" 2>/dev/null; RC=$?   # si falla, su traza no debe acabar en el aviso
    else
      RC=99
    fi
    case $RC in
      10) ES=pytest ;;
      11) ES=no ;;
      *)  # sin python3 o el detector falló: regex ancha, ante la duda se mide
          # (sin tubería: con pipefail, el SIGPIPE de `printf | grep -q` daba 141 y el pytest pasaba sin medir)
          grep -qE '(^|[^A-Za-z0-9_.-])(pytest|py\.test)([^A-Za-z0-9_.-]|$)' <<<"$CMD" && ES=pytest ;;
    esac ;;
esac

if [ "$MODO" = detecta ]; then
  echo "$ES"; [ "$ES" = pytest ]; exit $?
fi
[ "$SIN_LEER" = 1 ] && ES=pytest     # entrada ilegible con pytest dentro: ante la duda se mide
[ "$ES" = pytest ] || exit 0

[ -n "${GATE_RAM_TRACE:-}" ] && : > "$GATE_RAM_TRACE"
DIR="${CLAUDE_PROJECT_DIR:-$(git rev-parse --show-toplevel 2>/dev/null || pwd)}"
# -f y no -x: se lanza con `bash`, y una copia sin el bit de ejecución (pasa al copiar entre repos:
# evo-preven-develop-quirurgicos lo tiene así) dejaba el gate diciendo «falta check-ram.sh» y el
# pytest pasaba sin medir.
[ -f "$DIR/.claude/hooks/check-ram.sh" ] || { echo "gate-ram-pytest: falta check-ram.sh — RAM NO medida: pytest bloqueado (falla cerrado)" >&2; exit 2; }
SALIDA=$(bash "$DIR/.claude/hooks/check-ram.sh" 2>&1)
RC=$?
# check-ram.sh sale con 1 cuando bloquea. Para un hook PreToolUse solo el exit 2 bloquea: el 1 es
# «error no bloqueante» y el pytest seguiría adelante. Aquí se traduce, y el porqué va por stderr.
if [ $RC -ne 0 ]; then
  {
    echo "gate-ram-pytest: pytest bloqueado antes de lanzarlo (no es un fallo del test)."
    printf '%s\n' "$SALIDA"
    echo "Límites de esta máquina: bash .claude/hooks/check-ram.sh --explain"
  } >&2
  exit 2
fi
exit 0
