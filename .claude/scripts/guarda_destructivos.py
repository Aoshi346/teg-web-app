#!/usr/bin/env python3
"""guarda_destructivos.py — hook PreToolUse (Bash|Write|Edit|MultiEdit): cuatro guardas en un solo proceso.

  A  borrado y git destructivo   rm -r, find -delete, rsync --delete, shred, git reset --hard / clean / branch -D /
                                 checkout . / push --force / stash clear...
  B  BD destructiva              migrate, flush, reset_db, sqlflush|dbshell, DROP/TRUNCATE/DELETE sin WHERE,
                                 dropdb, docker compose down -v, prisma/rails/artisan/alembic...
  C  servidor expuesto           0.0.0.0 en cualquier flag de escucha, http.server sin --bind, docker -p sin
                                 127.0.0.1, compose con ports sin 127.0.0.1 o network_mode: host
  D  git add -A / commit -a      con otra sesión de Claude viva EN EL MISMO repo y ficheros sucios que esta
                                 sesión no tocó (Collision Guard hecho hook)

Origen: experimento X-04 de la sub-ola 2.09 (el hook propio ganó a los mods de comunidad y al Blast Radius
oficial) y su re-medición en la 2.10. Medición y límites: _archive/2026-10-20/medicion-2.10/README.md.
Política de mods: rules/agent-security.md §5.

SALIDA. `ask` (JSON permissionDecision): decide el humano, con el motivo y el radio. Sin nada que decir,
silencio y exit 0. Con `claude -p` (nadie delante) un `ask` queda en DENEGADO: es lo que se quiere.
Este script NUNCA sale con 2: un fallo interno sale con 3 y es el envoltorio (hooks/guarda-destructivos.sh) quien
decide, con una regex ancha sobre el texto crudo, si bloquea. Así una guarda rota falla CERRADA donde importa
y no bloquea los turnos benignos.

LÍMITE HONESTO. Es una red de seguridad que lee el TEXTO del comando, no un permiso. Lo que se esconde
(variables, scripts, `python -c "os.system(...)"`, `$(...)` no literales) se pasa. Lo que no hace falta que
nadie decida (rm -r bajo /tmp) se deja pasar. Los defaults implícitos (`next dev`, `streamlit run` sin
`--server.address`) no se ven: solo se marca lo que se escribe.
"""
import json
import os
import posixpath
import re
import shlex
import signal
import subprocess
import sys

TAG = "guarda-destructivos"
WRAP = {"sudo", "doas", "env", "nohup", "time", "command", "exec", "nice", "xargs", "timeout", "stdbuf",
        "ionice", "setsid", "builtin"}
# flags de cada envoltorio que se comen el argumento siguiente
WRAP_VAL = {"sudo": {"-u", "-g", "-h", "-p", "-C", "-D", "-R", "-r", "-t", "-U", "-T"},
            "doas": {"-u", "-C"}, "env": {"-u", "-C", "-S"}, "nice": {"-n"},
            "timeout": {"-s", "-k", "--signal", "--kill-after"}, "stdbuf": set(), "ionice": {"-c", "-n", "-p"},
            "xargs": {"-I", "-n", "-P", "-d", "-L", "-E", "-s", "-a", "-J"}, "time": {"-f", "-o"}}
KW = {"then", "do", "else", "if", "elif", "while", "until", "!", "{", "(", "&&"}
SHELLS = {"bash", "sh", "zsh", "dash", "ksh"}
SAFE_TMP = ("/tmp/", "/var/tmp/", "/dev/shm/")
LOOP = ("127.0.0.1", "localhost", "::1", "[::1]")
ABIERTO = ("0.0.0.0", "::", "[::]", "0", "*", "")
# comandos que solo MUESTRAN texto: una «0.0.0.0» ahí no es un servidor
TEXTO = {"echo", "printf", "cat", "grep", "egrep", "fgrep", "rg", "ag", "sed", "awk", "head", "tail", "less", "more",
         "ls", "find", "diff", "wc", "tee", "man", "which", "type", "git", "curl", "wget", "http", "https", "ping",
         "nmap", "dig", "host", "nslookup", "traceroute", "python-dotenv", "jq", "sort", "uniq", "cut", "tr", "xargs-echo",
         "test", "[", "[[", "export", "unset", "set", "alias", "source", ".", "true", "false", "pytest", "ruff", "black",
         "mypy", "npm-test", "touch", "mkdir", "cp", "mv", "ln", "chmod", "chown", "stat", "file", "realpath",
         "dirname", "basename", "date", "pwd", "cd", "pushd", "popd", "read", "readlink", "ss", "netstat", "lsof"}
DB_CLIENTS = {"psql", "mysql", "mariadb", "sqlite3", "sqlite", "mongosh", "mongo", "redis-cli", "cqlsh",
              "clickhouse-client", "sqlcmd", "usql", "pgcli", "mycli", "litecli", "dbshell"}
# SQL destructivo (se mira el texto entero del comando cuando hay un cliente de BD)
SQL_DESTR = re.compile(
    r"\b(DROP\s+(TABLE|DATABASE|SCHEMA|INDEX|VIEW|ROLE|USER|COLLECTION|KEYSPACE|TRIGGER|SEQUENCE)|TRUNCATE|"
    r"ALTER\s+TABLE\s+\S+\s+DROP|FLUSHALL|FLUSHDB|dropDatabase|\.drop\s*\(|deleteMany\s*\(\s*\{\s*\}\s*\)|"
    r"DELETE\s+FROM\s+\S+)", re.I)
BD_HERRAMIENTAS = [  # (regex sobre el trozo, descripción)
    (r"\b(prisma|npx\s+prisma)\b.*\b(migrate\s+(dev|deploy|reset)|db\s+(push|execute))\b", "prisma migrate/db push"),
    (r"\bprisma\b.*\bmigrate\s+reset\b", "prisma migrate reset"),
    (r"\b(rails|rake|bin/rails|bundle\s+exec\s+rake)\s+db:(migrate(?!:status)|drop|reset|rollback|schema:load|setup|seed:replant)\b",
     "rails/rake db:*"),
    (r"\bartisan\s+(migrate:(fresh|reset|rollback|refresh)|db:wipe|migrate)(?!:status)\b(?!.*--pretend)", "artisan migrate"),
    (r"\b(knex|sequelize|sequelize-cli|typeorm|drizzle-kit|diesel|sqlx|goose|supabase|flyway|liquibase)\b.*"
     r"\b(migrate(:latest|:rollback|\s+run|)|db:(migrate|drop)|schema:drop|push|drop|database\s+(reset|drop)|db\s+reset|clean)\b",
     "herramienta de migraciones/BD"),
    (r"\bflask\s+db\s+(upgrade|downgrade)\b", "flask db upgrade/downgrade"),
    (r"\bmysqladmin\b.*\b(drop|flush-.*)\b", "mysqladmin drop"),
    (r"\bpg_restore\b.*(\s-c\b|--clean)", "pg_restore --clean"),
    (r"\b(dropdb|dropuser|dropdb\.exe)\b", "dropdb/dropuser"),
    (r"\bdocker\s+volume\s+(rm|prune)\b", "docker volume rm/prune (datos)"),
    (r"\bdocker\s+system\s+prune\b.*--volumes", "docker system prune --volumes (datos)"),
    (r"\b(docker[- ]compose|docker\s+compose)\b.*\b(down|rm)\b.*(\s-v\b|--volumes|\s-\w*v\w*\b)", "docker compose down -v (borra volúmenes)"),
]


class Roto(Exception):
    pass


def _alarma(*_):
    raise Roto("timeout interno")


def sale_ask(razon):
    print(json.dumps({"hookSpecificOutput": {"hookEventName": "PreToolUse", "permissionDecision": "ask",
                                             "permissionDecisionReason": (TAG + ": " + razon)[:1800]}},
                     ensure_ascii=False))
    sys.exit(0)


# ───────────────────────────── troceado ─────────────────────────────
def parte(cmd):
    """Divide en [seg, sep, seg, sep, …] por && || ; | salto-de-línea &, SIN partir lo que va entre comillas
    ni dentro de $( )."""
    out, cur, i, n, q, prof = [], [], 0, len(cmd), None, 0
    while i < n:
        ch = cmd[i]
        if q:
            cur.append(ch)
            if ch == "\\" and q == '"' and i + 1 < n:
                cur.append(cmd[i + 1])
                i += 1
            elif ch == q:
                q = None
        elif ch == "\\" and i + 1 < n:
            cur.append(ch)
            cur.append(cmd[i + 1])
            i += 1
        elif ch in "'\"":
            q = ch
            cur.append(ch)
        elif cmd[i:i + 2] == "$(":
            prof += 1
            cur.append("$(")
            i += 1
        elif ch == ")" and prof:
            prof -= 1
            cur.append(ch)
        elif prof:
            cur.append(ch)
        else:
            op = None
            if cmd[i:i + 2] in ("&&", "||"):
                op = cmd[i:i + 2]
            elif ch in ";|\n":
                op = ch
            elif ch == "&" and (i + 1 >= n or cmd[i + 1] != "&") and (i == 0 or cmd[i - 1] not in "<>&"):
                op = "&"
            if op:
                out.append("".join(cur))
                out.append(op)
                cur = []
                i += len(op) - 1
            else:
                cur.append(ch)
        i += 1
    out.append("".join(cur))
    return out


def _limpia(t):
    """Quita ( { ) } pegados al principio/final de las palabras de control."""
    if t and t[0] not in ("(", "{") and t[0][:1] in "({" and len(t[0]) > 1 and not t[0].startswith("(("):
        t = [t[0].lstrip("({")] + t[1:]
    if t and t[-1].endswith((")", "}")) and len(t[-1]) > 1 and "(" not in t[-1]:
        t = t[:-1] + [t[-1].rstrip(")}")]
    return [x for x in t if x != ""]


def trozos(cmd, prof=0):
    """Trocea como lo haría la shell: ; && || | \\n &, y entra en $( ), `…`, bash -c "…", eval, ssh host "…",
    heredocs que alimentan a una shell y echo/printf que acaban en `| sh`."""
    out = []
    if prof > 5:
        return out
    if cmd.count("<<") > 12:  # límite declarado: con tantos «<<» no se interpretan heredocs (coste cuadrático)
        cmd = cmd.replace("<<", "< <")
    activo = re.sub(r"<<-?\s*(['\"])(\w+)\1[^\n]*\n.*?\n\s*\2\s*(?:\n|$)", " \n", cmd, flags=re.S)  # heredoc entrecomillado: inerte
    activo = re.sub(r"'[^']*'", "''", activo)  # entre comillas simples la shell no expande nada
    for m in re.finditer(r"\$\(([^()]*)\)|`([^`]*)`", activo):
        out += trozos(m.group(1) or m.group(2), prof + 1)
    for m in re.finditer(r"\b(?:ba|z|da|k)?sh\b[^\n<|;&]*<<-?\s*(['\"]?)(\w+)\1[^\n]*\n(.*?)\n\s*\2\s*(?:\n|$)", cmd, flags=re.S):
        out += trozos(m.group(3), prof + 1)
    cmd2 = re.sub(r"<<-?\s*(['\"]?)(\w+)\1[^\n]*\n.*?\n\s*\2\s*(\n|$)", " \n", cmd, flags=re.S)
    partes = parte(cmd2)
    for i in range(0, len(partes), 2):
        seg = partes[i].strip()
        sep = partes[i + 1] if i + 1 < len(partes) else ""
        if not seg:
            continue
        try:
            t = shlex.split(seg, posix=True)
        except ValueError:
            t = seg.split()
        t = _limpia(t)
        if not t:
            continue
        out.append(t)
        j = palabra_orden(t)
        if j >= len(t):
            continue
        base = os.path.basename(t[j])
        # bash -c "…"  (también -lc, -ic, y detrás de docker exec / kubectl exec / uv run…)
        for q_ in range(len(t)):
            if os.path.basename(t[q_]) in SHELLS:
                k = next((n for n in range(q_ + 1, len(t)) if re.match(r"^-[a-z]*c[a-z]*$", t[n])), None)
                if k is not None and k + 1 < len(t):
                    out += trozos(t[k + 1], prof + 1)
                    break
        if base == "eval":
            out += trozos(" ".join(t[j + 1:]), prof + 1)
        elif base == "su" and "-c" in t:
            k = t.index("-c")
            if k + 1 < len(t):
                out += trozos(t[k + 1], prof + 1)
        elif base == "ssh":
            args = t[j + 1:]
            k = 0
            while k < len(args) and args[k].startswith("-"):
                k += 2 if args[k] in ("-p", "-i", "-l", "-o", "-F", "-J", "-L", "-R", "-D", "-b", "-c", "-E", "-S") else 1
            if k + 1 < len(args):  # args[k] es el host
                out += trozos(" ".join(args[k + 1:]), prof + 1)
        # echo/printf '…' | sh   → lo que se imprime es la orden
        if base in ("echo", "printf") and sep == "|" and i + 2 < len(partes):
            try:
                sig = shlex.split(partes[i + 2].strip())
            except ValueError:
                sig = partes[i + 2].split()
            sig = _limpia(sig)
            jj = palabra_orden(sig) if sig else 0
            if sig and jj < len(sig) and os.path.basename(sig[jj]) in SHELLS and "-c" not in sig:
                out += trozos(" ".join(t[j + 1:]), prof + 1)
    return out


def palabra_orden(t):
    """Índice de la palabra que es la orden de verdad, saltando asignaciones, envoltorios y palabras de control."""
    i = 0
    while i < len(t):
        w = t[i]
        if w in KW or re.match(r"^[A-Za-z_]\w*=", w):
            i += 1
        elif w in WRAP:
            i += 1
            val = WRAP_VAL.get(w, set())
            while i < len(t) and t[i].startswith("-"):
                i += 2 if t[i] in val else 1
            if w == "timeout" and i < len(t) and re.match(r"^\d", t[i]):
                i += 1
            while i < len(t) and w in ("sudo", "doas", "env", "nice", "nohup") and re.match(r"^[A-Za-z_]\w*=", t[i]):
                i += 1
        else:
            break
    return i


def _norm(p):
    return posixpath.normpath(p) if p else p


def _tmp_seguro(o):
    n = _norm(o)
    return n is not None and not any(c in n for c in "$*?~`") and (n + "/").startswith(SAFE_TMP) and n not in ("/tmp", "/var/tmp", "/dev/shm")


# ───────────────────────────── A: borrado y git ─────────────────────────────
def a_borrado(t, j, h):
    c = os.path.basename(t[j].lstrip("\\"))
    args = t[j + 1:]
    if c == "rm":
        fl = [a for a in args if a.startswith("-") and a != "--"]
        rec = any(f == "--recursive" or (re.match(r"^-[^-]", f) and re.search(r"[rR]", f)) for f in fl)
        objetivos = [a for a in args if not a.startswith("-") or a == "--"]
        objetivos = [o for o in objetivos if o != "--"]
        if rec:
            if objetivos and all(_tmp_seguro(o) for o in objetivos):
                return
            h.append(("A", "borrado recursivo: rm %s %s" % (" ".join(fl), " ".join(objetivos)[:80])))
        elif any(re.search(r"\.(sqlite3?|db|sql|dump|bak)$", o) for o in objetivos) and not all(_tmp_seguro(o) for o in objetivos):
            h.append(("B", "rm de un fichero de base de datos: " + " ".join(objetivos)[:80]))
    elif c in ("shred", "mkfs") or c.startswith("mkfs."):
        h.append(("A", c + " (destruye datos sin vuelta atrás)"))
    elif c == "truncate" and not all(_tmp_seguro(o) for o in args if not o.startswith("-") and not re.match(r"^\d", o)):
        h.append(("A", "truncate (vacía ficheros)"))
    elif c == "dd" and any(a.startswith("of=/dev/") for a in args):
        h.append(("A", "dd sobre un dispositivo"))
    elif c == "mv" and args and args[-1] == "/dev/null":
        h.append(("A", "mv a /dev/null (el fichero desaparece)"))
    elif c == "find" and ("-delete" in args or ("-exec" in args and any(os.path.basename(a) in ("rm", "shred") for a in args))):
        raices = []
        for a in args:
            if a.startswith(("-", "(", "!")):
                break
            raices.append(a)
        filtro = any(x in args for x in ("-name", "-iname", "-mtime", "-newer", "-regex", "-path"))
        en_tmp = bool(raices) and all(_tmp_seguro(a) or (filtro and posixpath.normpath(a) in ("/tmp", "/var/tmp")) for a in raices)
        if not en_tmp:
            h.append(("A", "find … -delete / -exec rm"))
    elif c == "rsync" and any(a.startswith("--del") or a.startswith("--remove-source") for a in args) and not (
            "--dry-run" in args or any(re.match(r"^-[A-Za-z]*n[A-Za-z]*$", a) for a in args)):
        h.append(("A", "rsync con --delete (borra en el destino lo que no está en el origen)"))
    elif c == "kubectl" and "delete" in args:
        h.append(("A", "kubectl delete"))
    elif c == "docker" and (args[:2] == ["system", "prune"] or args[:2] == ["image", "prune"] or args[:2] == ["container", "prune"]):
        h.append(("A", "docker %s" % " ".join(args[:2])))
    elif c == "git":
        k = 0
        while k < len(args) and args[k].startswith("-"):
            k += 2 if args[k] in ("-C", "-c", "--git-dir", "--work-tree") else 1
        sub = args[k] if k < len(args) else ""
        rest = args[k + 1:]
        corto = "".join(r[1:] for r in rest if re.match(r"^-[A-Za-z]+$", r))
        if sub == "reset" and ("--hard" in rest or "--keep" in rest and False):
            h.append(("A", "git reset --hard (se pierde lo no commiteado)"))
        elif sub == "clean" and not ("--dry-run" in rest or "n" in corto):
            h.append(("A", "git clean (borra ficheros sin seguimiento)"))
        elif sub == "push":
            if any(r in ("-f", "--force", "--mirror", "--delete", "-d") or r.startswith("--force-with-lease")
                   or re.match(r"^\+\S", r) or re.match(r"^-[A-Za-z]*f[A-Za-z]*$", r) or re.match(r"^:\S", r) for r in rest):
                h.append(("A", "git push forzado o que borra una rama remota (reescribe la historia remota)"))
            elif any("$(" in r or "`" in r for r in rest) and re.search(r"force|-f\b", " ".join(rest)):
                h.append(("A", "git push con la opción escondida en una expansión (parece force)"))
        elif sub == "branch" and (("D" in corto) or ("--force" in rest and ("-d" in rest or "--delete" in rest)) or
                                  ("f" in corto and "d" in corto) or ("-M" in rest)):
            h.append(("A", "git branch -D (borra la rama aunque no esté fusionada)"))
        elif sub == "worktree" and rest[:1] == ["remove"] and ("-f" in rest or "--force" in rest):
            h.append(("A", "git worktree remove --force (borra el worktree aunque tenga cambios)"))
        elif sub == "stash" and rest[:1] in (["drop"], ["clear"]):
            h.append(("A", "git stash %s (se pierde lo guardado)" % rest[0]))
        elif sub in ("checkout", "restore") and ("." in rest or ":/" in rest or "-f" in rest or "--force" in rest) and ("--staged" not in rest or "--worktree" in rest):
            h.append(("A", "git %s . / -f (descarta cambios sin commitear)" % sub))
        elif sub == "switch" and ("-f" in rest or "--force" in rest or "--discard-changes" in rest):
            h.append(("A", "git switch --discard-changes"))
        elif sub in ("filter-branch", "filter-repo") or (sub == "reflog" and rest[:1] == ["expire"]) or \
                (sub == "gc" and any(r.startswith("--prune=now") for r in rest)) or (sub == "update-ref" and "-d" in rest):
            h.append(("A", "git %s (reescribe o purga la historia)" % sub))


# ───────────────────────────── B: BD ─────────────────────────────
def contexto_django(cwd):
    """Solo con GUARDA_RADIO=1: BD destino y migraciones pendientes, con timeout. Ejecuta código del proyecto."""
    d = cwd
    for _ in range(4):
        if os.path.exists(os.path.join(d, "manage.py")):
            break
        d = os.path.dirname(d)
    else:
        return " | sin manage.py cerca: no se puede medir el radio"
    py = os.environ.get("GUARDA_PYTHON") or "python3"
    try:
        r = subprocess.run([py, "manage.py", "showmigrations", "--plan"], cwd=d, capture_output=True, text=True, timeout=3)
        if r.returncode != 0:
            return " | showmigrations falló (%d)" % r.returncode
        pend = [l[4:] for l in r.stdout.splitlines() if l.startswith("[ ]")]
        return " | migraciones pendientes: %d%s" % (len(pend), (" (" + ", ".join(pend[:8]) + ")") if pend else "")
    except Exception as e:  # noqa
        return " | radio no medido (%s)" % type(e).__name__


RADIO_A_MANO = (" | radio sin medir (medirlo ejecutaría código del proyecto antes de que confirmes): "
                "`python manage.py showmigrations --plan` y `python manage.py diffsettings | grep DATABASES`")


def b_bd(t, j, h, cwd, crudo):
    """Mira TODA la lista de palabras del trozo (docker compose exec web python manage.py migrate, uv run …)."""
    txt = " ".join(t[j:])
    bases = [os.path.basename(x) for x in t[j:]]
    # --- Django -----------------------------------------------------------------
    for n, b in enumerate(bases):
        if b in ("manage.py", "django-admin", "django-admin.py"):
            args = t[j + n + 1:]
            sub = next((a for a in args if not a.startswith("-")), "")
            if sub == "migrate" and not any(a in ("--plan", "--check", "--list", "-h", "--help") for a in args):
                extra = contexto_django(cwd) if os.environ.get("GUARDA_RADIO") == "1" else RADIO_A_MANO
                h.append(("B", "manage.py migrate" + (" ... zero (deshace todas las migraciones)" if "zero" in args else ""), extra))
            elif sub in ("flush", "reset_db", "sqlclear", "reset_schema", "drop_test_database"):
                h.append(("B", "manage.py %s (vacía o borra la BD)" % sub, RADIO_A_MANO))
            break
    # --- herramientas de BD con SQL/orden destructivo ----------------------------
    for rx, desc in BD_HERRAMIENTAS:
        if re.search(rx, txt, re.I):
            if desc.startswith("herramienta") and re.search(r"\b(status|info|validate|--dry-run|--help|diff|list)\b", txt):
                continue
            if re.search(r"\b(alembic|prisma)\b.*\b(status|diff|resolve|current|history)\b", txt):
                continue
            h.append(("B", desc, ""))
            break
    if any(b == "alembic" for b in bases):
        i = bases.index("alembic")
        a = t[j + i + 1:]
        if any(x in ("upgrade", "downgrade", "stamp") for x in a) and "--sql" not in a:
            h.append(("B", "alembic " + next(x for x in a if x in ("upgrade", "downgrade", "stamp")), ""))


def _texto_sql(trozos_, crudo):
    partes = [" ".join(t) for t in trozos_]
    partes += [m.group(3) for m in re.finditer(r"<<-?\s*(['\"]?)(\w+)\1[^\n]*\n(.*?)\n\s*\2\s*(?:\n|$)", crudo, flags=re.S)]
    return re.sub(r"'[^']*'", "''", "\n".join(partes))


def b_cliente(trozos_, crudo, h):
    """Un cliente de BD en cualquier trozo + SQL destructivo en el comando entero (también por tubería o -f)."""
    hay = False
    for t in trozos_:
        j = palabra_orden(t)
        if j < len(t) and any(os.path.basename(x) in DB_CLIENTS for x in t[j:]):
            hay = True
            break
        if "manage.py" in " ".join(t) and "dbshell" in t:
            hay = True
            break
    if not hay:
        return
    crudo = _texto_sql(trozos_, crudo)
    m = SQL_DESTR.search(crudo)
    if m:
        frag = m.group(0)
        if re.match(r"DELETE\s+FROM", frag, re.I) and re.search(r"\bWHERE\b", crudo, re.I):
            return
        h.append(("B", "SQL destructivo por un cliente de BD: " + frag[:60], ""))
        return
    if re.search(r"\bUPDATE\s+\S+\s+SET\b", crudo, re.I) and not re.search(r"\bWHERE\b", crudo, re.I):
        h.append(("B", "UPDATE sin WHERE por un cliente de BD", ""))
        return
    if re.search(r"(drop|truncate|reset|wipe|flush|purge|destroy|nuke|clean)\w*\.sql", crudo, re.I):
        h.append(("B", "script SQL con nombre destructivo por un cliente de BD", ""))


# ───────────────────────────── C: servidor expuesto ─────────────────────────────
HOST_FLAGS = {"--host", "--bind", "-b", "-H", "--address", "--ip", "--server.address", "--listen", "-l", "--hostname",
              "--bind-address", "--listen-address", "--interface", "-a", "-S", "--http-address", "--web-host",
              "--server-address", "--api-host", "--public-host", "-L"}
_ABIERTO_RX = re.compile(r"(^|[=:/@,])(0\.0\.0\.0|\[?::\]?)(:\d+)?(/.*)?$")


def _host_abierto(v):
    v = v.strip("'\"")
    v = re.sub(r"^(tcp|http|https|ws)://", "", v)
    return v.split(":")[0].strip("[]") in ("0.0.0.0", "::", "0", "*") if v and not v.startswith("[") else v.startswith("[::]")


def c_expuesto(t, j, h):
    c = os.path.basename(t[j])
    args = [a.strip("'\"") for a in t[j + 1:]]
    todo = " ".join(t[j:])
    if "runserver" in args:
        dest = next((a for a in args if re.match(r"^(\d+\.\d+\.\d+\.\d+|0|\[?::\]?|\*)?(:\d+)?$", a) and a and a != "runserver"), None)
        if dest and (dest.split(":")[0] in ("0.0.0.0", "0", "::", "[::]", "*") or dest.startswith("[::]")):
            h.append(("C", "runserver en todas las interfaces: " + dest))
        return
    es_py_http = c.startswith("python") and any(a == "-m" and i + 1 < len(args) and args[i + 1] in ("http.server", "SimpleHTTPServer")
                                                for i, a in enumerate(args))
    if es_py_http or c in ("http-server",) or (c == "npx" and "http-server" in args):
        host = None
        for i, a in enumerate(args):
            if a in ("--bind", "-b", "-a", "--address") and i + 1 < len(args):
                host = args[i + 1]
            elif a.startswith("--bind=") or a.startswith("--address="):
                host = a.split("=", 1)[1]
        if host is None:
            if es_py_http:
                h.append(("C", "http.server sin --bind escucha en TODAS las interfaces (0.0.0.0): añade --bind 127.0.0.1"))
            elif c in ("http-server", "npx"):
                h.append(("C", "http-server sin -a 127.0.0.1 escucha en todas las interfaces"))
        elif not _lo(host):
            h.append(("C", "http.server/http-server enlazado a " + host))
        return
    if c == "docker" or c == "podman":
        if any(x in args for x in ("run", "create")) or "compose" in args:
            for i, a in enumerate(args):
                v = None
                if a in ("-p", "--publish") and i + 1 < len(args):
                    v = args[i + 1]
                elif a.startswith("--publish="):
                    v = a.split("=", 1)[1]
                elif re.match(r"^-p\S+", a):
                    v = a[2:]
                if v is not None and not v.startswith(("127.0.0.1:", "[::1]:", "localhost:")):
                    h.append(("C", "docker -p %s publica en todas las interfaces (falta 127.0.0.1:)" % v))
                    return
                if a in ("-P", "--publish-all"):
                    h.append(("C", "docker -P publica todos los puertos en todas las interfaces"))
                    return
                if (a in ("--network", "--net") and i + 1 < len(args) and args[i + 1] == "host") or a in ("--network=host", "--net=host"):
                    h.append(("C", "docker --network host (el contenedor usa las interfaces de la máquina)"))
                    return
        return
    if c in ("nc", "ncat", "netcat") and any(re.match(r"^-[a-zA-Z]*l", a) for a in args) and not any(_lo(a) for a in args):
        h.append(("C", "escucha con netcat (todas las interfaces por defecto)"))
        return
    if c == "socat" and any(re.search(r"(TCP|TCP4|TCP6)-LISTEN:\d+", a, re.I) and "bind=" not in a.lower() for a in args):
        h.append(("C", "socat TCP-LISTEN sin bind= (todas las interfaces)"))
        return
    if c in TEXTO:
        return
    # flags de escucha con un valor abierto (--host 0.0.0.0, --server.address=0.0.0.0, serve -l tcp://0.0.0.0…)
    for i, a in enumerate(args):
        flag, val = (a.split("=", 1) + [None])[:2] if a.startswith("-") and "=" in a else (a, None)
        if flag in HOST_FLAGS:
            if val is None and i + 1 < len(args) and not args[i + 1].startswith("-"):
                val = args[i + 1]
            if val is None:
                if flag == "--host" or flag == "-H":
                    h.append(("C", "--host sin valor (vite/next lo abren a toda la red)"))
                    return
                continue
            if _host_abierto(val):
                h.append(("C", "servidor enlazado a %s (%s)" % (val, c)))
                return
    # cualquier argumento que sea un destino abierto (php -S 0.0.0.0:8000, ssh -L 0.0.0.0:…)
    for a in args:
        if _ABIERTO_RX.search(a) and not a.startswith("-") and not a.endswith(".py"):
            h.append(("C", "%s con destino abierto %s" % (c, a)))
            return
        if a.startswith("-") and "=" not in a:
            continue
    # php -S :8000 (sin host = todas) no se mira: es un default implícito


def _lo(host):
    return host.strip("'\"") in LOOP


_COMPOSE = re.compile(r"(^|/)(docker-)?compose[^/]*\.ya?ml$")
_PUERTO = re.compile(r"^(\d+(-\d+)?:\d+(-\d+)?(/\w+)?|\d+(-\d+)?(/\w+)?|0\.0\.0\.0:.*|\[::\]:.*|:\d+:\d+)$")
_CODIGO = re.compile(r"\.(py|js|mjs|cjs|ts|tsx|jsx|json|ya?ml|toml|ini|cfg|conf|sh|env|service|go|rb|php|rs|java|kt)$")
_BIND = re.compile(r"(host|bind|address|listen|hostname|\bip\b)[^\n#]{0,40}?['\"=:\s(]0\.0\.0\.0", re.I)


def c_fichero(path, texto, h):
    """Write/Edit de un compose (ports sin 127.0.0.1) o de un fichero de código/config que escucha en 0.0.0.0."""
    if _COMPOSE.search(path):
        en_ports = False
        for l in texto.splitlines():
            s = l.strip()
            if re.match(r"^network_mode:\s*[\"']?host", s):
                h.append(("C", "%s usa network_mode: host" % os.path.basename(path)))
            m_inline = re.match(r"^ports:\s*\[(.*)\]\s*$", s)
            if m_inline:
                for v in re.findall(r"[\"']?([^\"',\[\]\s]+)[\"']?", m_inline.group(1)):
                    if _PUERTO.match(v) and not v.startswith(("127.0.0.1:", "[::1]:", "localhost:")):
                        h.append(("C", "%s publica %s en todas las interfaces" % (os.path.basename(path), v)))
                continue
            if re.match(r"^ports:\s*$", s):
                en_ports = True
                continue
            m = re.match(r"^-\s*[\"']?([^\"'#]+?)[\"']?\s*(#.*)?$", s)
            if en_ports and m:
                v = m.group(1).strip()
                if _PUERTO.match(v) and not v.startswith(("127.0.0.1:", "[::1]:", "localhost:")):
                    h.append(("C", "%s publica %s en todas las interfaces" % (os.path.basename(path), v)))
            elif en_ports and s and not s.startswith(("-", "#")):
                en_ports = False
            if not en_ports and m and re.match(r"^(0\.0\.0\.0:|\[::\]:)", m.group(1).strip()):
                h.append(("C", "%s publica %s en todas las interfaces" % (os.path.basename(path), m.group(1).strip())))
        return
    ruta = path.replace("\\", "/")
    if not _CODIGO.search(ruta) or re.search(r"(^|/)(\.claude/(hooks|smoke|rules|skills|scripts)|\.docs|documentation|_archive|tests?|__tests__|node_modules)/|/test_[^/]*$|\.test\.|\.spec\.", ruta):
        return
    for l in texto.splitlines():
        s = l.strip()
        if s.startswith(("#", "//", "*", "/*")) or "ALLOWED_HOSTS" in s or "CSRF_TRUSTED" in s:
            continue
        if _BIND.search(l):
            h.append(("C", "%s escucha en 0.0.0.0: %s" % (os.path.basename(path), s[:70])))
            return


# ───────────────────────────── D: git add -A con otra sesión ─────────────────────────────
def tocados_por_mi(transcript):
    s = set()
    try:
        for line in open(transcript, errors="replace"):
            try:
                o = json.loads(line)
            except Exception:
                continue
            c = (o.get("message") or {}).get("content")
            if not isinstance(c, list):
                continue
            for b in c:
                if isinstance(b, dict) and b.get("type") == "tool_use" and b.get("name") in ("Write", "Edit", "MultiEdit", "NotebookEdit"):
                    p = (b.get("input") or {}).get("file_path") or (b.get("input") or {}).get("notebook_path")
                    if p:
                        s.add(os.path.realpath(p))
    except Exception:
        return None
    return s


_ENV_GIT = dict(os.environ, GIT_OPTIONAL_LOCKS="0")


def _toplevel(d):
    try:
        r = subprocess.run(["git", "-C", d, "rev-parse", "--show-toplevel"], capture_output=True, text=True, timeout=3, env=_ENV_GIT)
        return os.path.realpath(r.stdout.strip()) if r.returncode == 0 and r.stdout.strip() else None
    except Exception:
        return None


def otras_sesiones(top):
    """Procesos `claude` cuyo cwd tiene a `top` como raíz de git (un worktree propio NO cuenta: está aislado)."""
    mios = set()
    p = os.getpid()
    while p > 1:
        mios.add(p)
        try:
            p = int(open("/proc/%d/stat" % p).read().rsplit(")", 1)[1].split()[1])
        except Exception:
            break
    res, cache = [], {}
    for d in os.listdir("/proc"):
        if not d.isdigit() or int(d) in mios:
            continue
        try:
            argv0 = open("/proc/%s/cmdline" % d, "rb").read().split(b"\0")[0].decode(errors="replace")
            if os.path.basename(argv0) != "claude":
                continue
            cwd = os.path.realpath(os.readlink("/proc/%s/cwd" % d))
        except Exception:
            continue
        if cwd == top or cwd.startswith(top + os.sep):
            if cwd not in cache:
                cache[cwd] = _toplevel(cwd)
            if cache[cwd] == top:
                res.append(int(d))
    return res


def d_add_todo(t, j, cwd, transcript, h):
    if os.path.basename(t[j]) != "git":
        return
    args = t[j + 1:]
    k, gdir = 0, cwd
    while k < len(args) and args[k].startswith("-"):
        if args[k] == "-C" and k + 1 < len(args):
            gdir = os.path.normpath(os.path.join(gdir, args[k + 1]))
        k += 2 if args[k] in ("-C", "-c") else 1
    sub = args[k] if k < len(args) else ""
    rest = args[k + 1:]
    if any(r in ("-n", "--dry-run") or re.match(r"^-[A-Za-z]*n[A-Za-z]*$", r) for r in rest) and sub == "add":
        return  # git add -n -A: no añade nada
    solo_tracked = False
    pathspecs = []
    todo = False
    if sub in ("add", "stage"):
        pos, tras = [], False
        for r in rest:
            if r == "--":
                tras = True
            elif tras or not r.startswith("-"):
                pos.append(r)
        if any(r in ("-A", "--all", "-u", "--update") for r in rest) or any(re.match(r"^-[A-Za-z]*[Au][A-Za-z]*$", r) for r in rest):
            todo = True
            solo_tracked = any(r in ("-u", "--update") for r in rest) and not any(r in ("-A", "--all") for r in rest)
            pathspecs = pos
        elif any(x in (".", ":/", "*", "./", ":/.", ":(top)") for x in pos):
            todo = True
            pathspecs = [x for x in pos if x not in (".", "./", "*", ":/", ":/.")] if len(pos) > 1 else []
    elif sub == "commit":
        if any(r in ("-a", "--all") or re.match(r"^-[a-zA-Z]*a[a-zA-Z]*$", r) for r in rest if not r.startswith("--m")):
            todo = True
            solo_tracked = True
    if not todo:
        return
    try:
        top = _toplevel(gdir)
        if not top:
            return
        otras = otras_sesiones(top)
        if not otras:
            return  # sin otra sesión viva en este repo, `git add -A` no arrastra lo de nadie
        try:
            st = subprocess.run(["git", "-C", top, "status", "--porcelain", "-uall"], capture_output=True, text=True, timeout=4,
                                env=_ENV_GIT).stdout
        except subprocess.TimeoutExpired:  # no se pudo medir y hay otra sesión: se avisa igual
            h.append(("D", "git %s con otra sesión viva en este repo y `git status` tarda demasiado para saber qué arrastraría. "
                      "Usa rutas explícitas (`git add -- <tus ficheros>`)" % sub, ""))
            return
        sucios = []
        for l in st.splitlines():
            if len(l) < 4:
                continue
            if solo_tracked and l.startswith("??"):
                continue
            sucios.append(l[3:].strip().strip('"').split(" -> ")[-1])
        # `git add .` desde un subdirectorio, o con pathspecs, solo toca esa parte
        zona = []
        if pathspecs:
            zona = [os.path.realpath(os.path.join(gdir, x)) for x in pathspecs if not x.startswith(":")]
        elif sub in ("add",) and "." in rest and os.path.realpath(gdir) != top:
            zona = [os.path.realpath(gdir)]
        if zona:
            sucios = [f for f in sucios if any((os.path.realpath(os.path.join(top, f)) + os.sep).startswith(z + os.sep) or
                                              os.path.realpath(os.path.join(top, f)) == z for z in zona)]
        mios = tocados_por_mi(transcript) if transcript else None
        if mios is None:
            ajenos, nota = sucios, " (sin transcript legible: no se distingue lo mío)"
        else:
            ajenos, nota = [f for f in sucios if os.path.realpath(os.path.join(top, f)) not in mios], ""
        if ajenos:
            h.append(("D", "git %s %s arrastraría %d fichero(s) que esta sesión no tocó (hay %d sesión(es) de Claude viva(s) en este repo): %s%s. "
                      "Usa rutas explícitas (`git add -- <tus ficheros>`) o trabaja en un worktree" %
                      (sub, " ".join(rest), len(ajenos), len(otras), ", ".join(ajenos[:6]), nota), ""))
    except Exception as e:
        raise Roto("D: " + str(e))


# ───────────────────────────── análisis ─────────────────────────────
def analizar(d):
    ti = d.get("tool_input") or {}
    tool = d.get("tool_name") or ""
    cwd = d.get("cwd") or os.getcwd()
    h = []
    if tool == "Bash":
        cmd = ti.get("command") or ""
        if len(cmd) > 30000:  # límite declarado: de un comando enorme se mira el principio y el final
            cmd = cmd[:20000] + "\n" + cmd[-10000:]
        tz = trozos(cmd)
        utiles = "\n".join(" ".join(x) for x in tz)
        cwd_act = cwd
        for t in tz:
            j = palabra_orden(t)
            if j >= len(t):
                continue
            if os.path.basename(t[j]) == "cd" and j + 1 < len(t) and not t[j + 1].startswith(("-", "$")):
                nuevo = os.path.normpath(os.path.join(cwd_act, os.path.expanduser(t[j + 1])))
                if os.path.isdir(nuevo):  # un cd a un sitio que no existe aquí no cambia el repo que se mira
                    cwd_act = nuevo
                continue
            if t[j].startswith("$") and re.search(r"-rf|-fr|--force|--hard|migrate|flush", " ".join(t[j + 1:])):
                h.append(("A", "orden escondida en una variable (%s) con banderas destructivas" % t[j]))
                continue
            for w in t[:j]:
                if re.match(r"^\w*(HOST|HOSTNAME|BIND\w*|LISTEN\w*|ADDR\w*|ADDRESS)=(0\.0\.0\.0|::|\[::\]|\*)\S*$", w, re.I):
                    h.append(("C", "variable de entorno %s abre el servidor a todas las interfaces" % w))
            a_borrado(t, j, h)
            b_bd(t, j, h, cwd, utiles)
            c_expuesto(t, j, h)
            d_add_todo(t, j, cwd_act, d.get("transcript_path"), h)
        b_cliente(tz, cmd, h)
        if re.search(r"\bsqlflush\b", utiles) and re.search(r"\b(dbshell|psql|mysql|sqlite3)\b", utiles):
            h.append(("B", "sqlflush enviado a la BD (vacía todas las tablas)", ""))
        if re.search(r"\|\s*(sudo\s+)?(ba|z|da)?sh\b", cmd) and re.search(r"-f\b|--force|rm\s+-\w*[rR]|--hard", cmd) and not h:
            h.append(("A", "orden destructiva enviada a una shell por pipe"))
        # un compose escrito desde la shell (cat > docker-compose.yml <<EOF …)
        m = re.search(r"(?:>|tee\s+(?:-a\s+)?)\s*([^\s|;&<>]*compose[^\s|;&<>]*\.ya?ml)", cmd)
        if m:
            c_fichero(m.group(1), cmd, h)
    elif tool in ("Write", "Edit", "MultiEdit"):
        texto = ti.get("content") or ti.get("new_string") or ""
        if tool == "MultiEdit":
            texto = "\n".join((e or {}).get("new_string", "") for e in (ti.get("edits") or []))
        c_fichero(ti.get("file_path") or "", texto, h)
    # sin duplicados
    vistos, out = set(), []
    for x in h:
        if (x[0], x[1]) not in vistos:
            vistos.add((x[0], x[1]))
            out.append(x)
    return out


def main():
    crudo = sys.stdin.read()
    signal.signal(signal.SIGALRM, _alarma)
    signal.alarm(7)
    try:
        if os.environ.get("TL_GUARDA_SABOTAJE") == "excepcion":
            raise Roto("sabotaje: la guarda revienta")
        d = json.loads(crudo)
        h = analizar(d)
    except Exception as e:  # noqa — FALLA CERRADO: el envoltorio decide con la regex ancha
        sys.stderr.write("%s: se rompió por dentro (%s: %s)\n" % (TAG, type(e).__name__, str(e)[:120]))
        sys.exit(3)
    signal.alarm(0)
    if not h:
        sys.exit(0)
    razon = " ; ".join("[%s] %s" % (x[0], x[1]) for x in h)
    extra = "".join(x[2] for x in h if len(x) > 2 and x[2])
    sale_ask(razon + extra)


if __name__ == "__main__":
    main()
