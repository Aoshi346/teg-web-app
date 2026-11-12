#!/usr/bin/env python3
"""estado_flujo.py — el estado del flujo de un proyecto, en JSON, para quien lo pinte.

Lo lee el mod del tablero TL (tarjeta sobre el prompt, recibo de turno, /tablero). El mod
solo dibuja: TODA la lógica vive aquí, versionada en el template y con su caso en el smoke
(`smoke/arreglos-locales`, D-18). Así el mismo dato sirve a la terminal y a cualquier otro.

Qué devuelve:
  proyecto, rama · sesion SpecKit activa · waves (hecho/curso/bloq/pend por wave) ·
  actual (la primera wave sin cerrar: bloqueos y siguiente tarea) · fuera (secciones que no
  son waves con algo abierto) · chips (peticiones pendientes, commits sin subir, reglas
  activas, Telegram).

Sesión activa: la que se pase con --sesion; si no, la de tasks.md más reciente entre las que
tienen algo abierto. Sin sesión SpecKit, el PLAN de superpowers más reciente
(`docs/superpowers/plans/AAAA-MM-DD-*.md`, sin los `*PROMPT*`) si le queda algo abierto: cada
`### Task N: …` cuenta como una wave y sus `- [ ]` como tareas (`"tipo": "superpowers"`). Si el plan
avanza en un worktree (`.claude/worktrees/*/`), se lee la copia con más casillas marcadas.
OJO, medido en Decision-Maker (2026-10-27): superpowers lleva el avance en su lista de tareas y NO
marca las casillas del plan; un plan terminado y fusionado salía 0/77. Por eso una Task cuyo paso
«Commit `mensaje`» ya está en `git log --all` cuenta como HECHA entera; sin mensaje, mandan las casillas. Sin ninguno de los dos → "sesion": null (no se inventa una).

Una marca de checkbox que no se sabe leer ABORTA con exit 2, igual que task_progress.py:
contarla como nada daría una wave «cerrada» que no lo está (rules/verification.md).

Con --todos (para /tablero) recorre las raíces (argumentos, o TL_RAICES separadas por «:», o
/home/aoshi) buscando proyectos con `.specify/sessions`, y añade la vigilancia: develop sin
sincronizar (desde el último «merge(sync): … hasta <sha>»), CORE de cada proyecto contra el del
template, RAM libre y Telegram, más un consejo: lo primero que conviene mirar.

Uso:
  python3 estado_flujo.py [proyecto] [--sesion <id o ruta>] [--json]
  python3 estado_flujo.py --todos [raíz ...] [--json]
"""
import json, os, re, subprocess, sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from task_progress import BOX, H2, OTRA, LABEL, MarcaDesconocida  # noqa: E402

WAVE = re.compile(r"^Wave\s+([0-9]+[a-z]?)\b\s*[—–\-:.]?\s*(.*)", re.I)
ABIERTO = ("backlog", "doing", "blocked")


def secciones(path):
    """[{titulo, tareas:[(estado, texto)]}] en orden; aborta ante una marca desconocida."""
    out, cur = [], None
    for n, line in enumerate(open(path, encoding="utf-8"), 1):
        h = H2.match(line)
        if h:
            cur = {"titulo": h.group(1).strip(), "tareas": []}
            out.append(cur)
            continue
        m = BOX.match(line)
        if not m:
            o = OTRA.match(line)
            if o:
                raise MarcaDesconocida(f"{path}:{n}: marca «[{o.group(1)}]» desconocida")
            continue
        if cur is None:
            cur = {"titulo": "", "tareas": []}
            out.append(cur)
        k = m.group(1)
        cur["tareas"].append((LABEL["x" if k in "xX" else k], m.group(2).strip()))
    return out


def cuenta(tareas):
    c = {"hecho": 0, "curso": 0, "bloq": 0, "pend": 0}
    for st, _ in tareas:
        c[{"done": "hecho", "doing": "curso", "blocked": "bloq", "backlog": "pend"}[st]] += 1
    c["total"] = len(tareas)
    return c


def limpio(t, n=70):
    t = re.sub(r"<!--.*?(-->|$)", "", t)
    # Emojis fuera: ocupan dos celdas y descuadran las cajas del tablero.
    t = re.sub(r"[\U0001F000-\U0001FAFF\u2600-\u27BF\uFE0F]", "", t)
    t = re.sub(r"\s+", " ", re.sub(r"(?<!\w)_+|_+(?!\w)", "", re.sub(r"[*`]", "", t))).strip()
    return t if len(t) <= n else t[: n - 1] + "…"


TAREA_ID = re.compile(r"^([A-Za-z]{1,5}(?:-[A-Za-z]{0,2})?\.?\d[\w.\-]{0,10})(?:\s*[—–:]\s+|\s+)")
CORTO = {"doing": "curso", "blocked": "bloq", "backlog": "pend"}


def abiertas(tareas, n=60):
    """Las tareas que faltan, con su id si lo tiene (W6.10, T5.4, W4-01): lo que pinta el detalle."""
    out = []
    for st, x in tareas:
        if st == "done":
            continue
        t = limpio(x, 200)
        m = TAREA_ID.match(t)
        out.append({"id": m.group(1) if m else None, "texto": limpio(t[m.end():] if m else t, n), "estado": CORTO[st]})
    return out


def sesiones(base):
    raiz = os.path.join(base, ".specify", "sessions")
    if not os.path.isdir(raiz):
        return []
    return sorted(os.path.join(raiz, d) for d in os.listdir(raiz)
                  if os.path.isfile(os.path.join(raiz, d, "tasks.md")))


def elegir(base, pedida):
    todas = sesiones(base)
    if pedida:
        if os.path.isfile(os.path.join(pedida, "tasks.md")):
            return pedida
        hit = [s for s in todas if os.path.basename(s).startswith(pedida)]
        if not hit:
            raise SystemExit(f"estado_flujo: no hay sesión «{pedida}» en {base}")
        return hit[0]
    vivas = []
    for s in todas:
        t = os.path.join(s, "tasks.md")
        if any(st in ABIERTO for sec in secciones(t) for st, _ in sec["tareas"]):
            vivas.append((os.path.getmtime(t), s))
    return max(vivas)[1] if vivas else None


PLAN_TASK = re.compile(r"^#{2,4}\s+Task\s+(\d+[a-z]?)\s*[:.—–\-]?\s*(.*)", re.I)
PLAN_FECHA = re.compile(r"^(\d{4})-(\d{2})-(\d{2})-.+\.md$")
PLAN_COMMIT = re.compile(r"Commit\**:?\**\s*`([^`]+)`")


def _palabras(x):
    return {w for w in re.findall(r"\w+", x.lower()) if len(w) > 3}


def commit_hecho(msg, hechos):
    """¿Está en el historial el commit que el plan pide para la Task? El mensaje real no siempre es
    el del plan (Decision-Maker: «feat(prompts): v5 sortea…» se commiteó como «…v5 existe en
    disco…»): mismo `tipo(ámbito):` y, o uno empieza por el otro, o comparten ≥3 palabras con
    contenido que sean ≥40 % de las del plan. Sin el mismo ámbito no casa nunca: «feat(metrics): el …» hay varios."""
    if not msg or ":" not in msg:
        return False
    ambito, cuerpo = msg.split(":", 1)
    pal = _palabras(cuerpo)
    for h in hechos:
        if not h.startswith(ambito + ":"):
            continue
        if h.startswith(msg) or msg.startswith(h):
            return True
        comunes = len(pal & _palabras(h.split(":", 1)[1]))
        if comunes >= 3 and comunes / len(pal) >= 0.4:      # con 2 casaban mensajes cortos distintos (smoke D-20)
            return True
    return False


def plan_superpowers(base):
    """(ruta, título, secciones como «Wave N — …») del plan de superpowers vivo más reciente, o None."""
    rel = os.path.join("docs", "superpowers", "plans")
    d = os.path.join(base, rel)
    if not os.path.isdir(d):
        return None
    planes = sorted((f for f in os.listdir(d) if PLAN_FECHA.match(f) and "PROMPT" not in f.upper()), reverse=True)
    if not planes:
        return None
    nombre = planes[0]                       # el más reciente por fecha del nombre: el que se está ejecutando
    wt = os.path.join(base, ".claude", "worktrees")
    copias = [os.path.join(d, nombre)] + sorted(
        os.path.join(wt, w, rel, nombre) for w in (os.listdir(wt) if os.path.isdir(wt) else [])
        if os.path.isfile(os.path.join(wt, w, rel, nombre)))
    marcadas = lambda f: len(re.findall(r"^\s*[-*]\s*\[[xX]\]", open(f, encoding="utf-8").read(), re.M))
    ruta = max(copias, key=lambda f: (marcadas(f), f == copias[0]))
    titulo, secs, cur = "", [], None
    for n, line in enumerate(open(ruta, encoding="utf-8"), 1):
        if not titulo and line.startswith("# "):
            titulo = line[2:].strip()
        h = PLAN_TASK.match(line)
        if h:
            cur = {"titulo": f"Wave {h.group(1)} — {h.group(2).strip()}", "tareas": [], "commit": None}
            secs.append(cur)
            continue
        c = PLAN_COMMIT.search(line) if cur is not None else None
        if c and cur["commit"] is None:
            cur["commit"] = c.group(1).strip()
        if cur is None:
            continue                         # lo de antes de la primera Task: contexto, no pasos
        m = BOX.match(line)
        if not m:
            o = OTRA.match(line)
            if o:
                raise MarcaDesconocida(f"{ruta}:{n}: marca «[{o.group(1)}]» desconocida")
            continue
        k = m.group(1)
        cur["tareas"].append((LABEL["x" if k in "xX" else k], m.group(2).strip()))
    # El commit de la Task en el historial = Task hecha (las casillas del plan no se marcan).
    hechos = git(base, "log", "--all", "--format=%s", "-n", "3000").splitlines()
    for s in secs:
        if commit_hecho(s.pop("commit"), hechos):
            s["tareas"] = [("done", x) for _, x in s["tareas"]]
    if not any(st in ABIERTO for s in secs for st, _ in s["tareas"]):
        return None
    f = PLAN_FECHA.match(nombre)
    return ruta, f"plan {f.group(2)}-{f.group(3)}", re.sub(r"[\s:\-—–]*plan de implementaci[oó]n\s*$", "", titulo.replace("---", "—"), flags=re.I), secs


def git(base, *a):
    try:
        return subprocess.check_output(["git", "-C", base, *a], stderr=subprocess.DEVNULL,
                                       text=True, timeout=2).strip()
    except Exception:
        return ""


def pendientes(base):
    """Peticiones abiertas del Usuario en pending-tasks.md del plan activo (o la raíz)."""
    os.environ.setdefault("CLAUDE_PROJECT_DIR", base)
    try:
        from tasks_registry import _plan_activo
        ruta = _plan_activo(base)
    except Exception:
        ruta = os.path.join(base, "pending-tasks.md")
    if not os.path.exists(ruta):
        return None
    return len(re.findall(r"^\s*[-*]\s*\[[ >]\]\s*`T-\d+`", open(ruta, encoding="utf-8").read(), re.M))


def reglas_activas(base):
    cat = os.path.join(base, ".claude", "patterns", "catalog.yaml")
    if not os.path.exists(cat):
        return None
    return len(re.findall(r"^\s*estado:\s*activo\b", open(cat, encoding="utf-8").read(), re.M))


def estado(base, pedida=None):
    base = os.path.abspath(base)
    out = {"proyecto": os.path.basename(base), "ruta": base,
           "rama": git(base, "rev-parse", "--abbrev-ref", "HEAD") or None, "sesion": None}
    s = elegir(base, pedida)
    plan = None if (s or pedida) else plan_superpowers(base)
    if s or plan:
        if s:
            nombre = os.path.basename(s)
            m = re.match(r"^([A-Z]+-\d+)\s*[-–—]?\s*(.*)$", nombre)
            out["sesion"] = {"id": m.group(1) if m else nombre, "nombre": (m.group(2) if m else "") or nombre,
                             "tasks": os.path.join(s, "tasks.md")}
            todas = secciones(os.path.join(s, "tasks.md"))
        else:
            ruta, pid, titulo, todas = plan
            out["sesion"] = {"id": pid, "nombre": limpio(titulo, 60) or os.path.basename(ruta),
                             "tasks": ruta, "tipo": "superpowers"}
        waves, fuera = [], []
        out["sesion"].update(cuenta([t for sec in todas for t in sec["tareas"]]))
        for sec in todas:
            w = WAVE.match(sec["titulo"])
            if w:
                waves.append({"id": w.group(1), "nombre": limpio(re.sub(r"\(.*?\)", "", w.group(2)), 40),
                              **cuenta(sec["tareas"]), "abiertas": abiertas(sec["tareas"]), "_t": sec["tareas"]})
            elif any(st in ABIERTO for st, _ in sec["tareas"]):
                fuera.append({"titulo": limpio(sec["titulo"], 40), **cuenta(sec["tareas"]), "abiertas": abiertas(sec["tareas"])})
        actual = next((w for w in waves if any(st in ("backlog", "doing", "blocked") for st, _ in w["_t"])), None)
        if actual:
            t = actual["_t"]
            sig = next((x for st, x in t if st == "doing"), None) or next((x for st, x in t if st == "backlog"), None)
            out["actual"] = {"id": actual["id"], "hecho": actual["hecho"], "total": actual["total"],
                             "bloqueos": [limpio(x) for st, x in t if st == "blocked"],
                             "en_curso": [limpio(x) for st, x in t if st == "doing"],
                             "siguiente": limpio(sig) if sig else None}
        else:
            out["actual"] = None
        for w in waves:
            w["actual"] = bool(actual) and w["id"] == actual["id"]
            del w["_t"]
        out["waves"], out["fuera"] = waves, fuera
    ahead = git(base, "rev-list", "--count", "@{u}..HEAD")
    out["chips"] = {"pend": pendientes(base),
                    "ahead": int(ahead) if ahead.isdigit() else None,
                    "reglas": reglas_activas(base),
                    "tg": telegram_listo(), "tg_bot": telegram_bot(),
                    "tl": os.environ.get("TLC_SESION") or None}
    return out


def telegram_listo():
    """¿Saldría el aviso? Lo mismo que mira avisar.py, sin leer más que si hay token.

    El token puede estar en el entorno (bot de avisos) o en `$TELEGRAM_STATE_DIR/.env`: las sesiones
    de `tlc` quitan TELEGRAM_BOT_TOKEN a propósito y avisan por el bot de su ranura (2026-11-03,
    T-204: el chip salía apagado con el canal conectado). Nunca devuelve ni imprime el token."""
    if os.environ.get("TL_AVISO") == "off":
        return False
    if os.environ.get("TELEGRAM_BOT_TOKEN"):
        return True
    d = os.environ.get("TELEGRAM_STATE_DIR") or os.path.expanduser("~/.claude/channels/telegram")
    try:
        with open(os.path.join(d, ".env")) as f:
            return any(re.match(r"\s*TELEGRAM_BOT_TOKEN\s*=\s*\S", linea) for linea in f)
    except OSError:
        return False


def telegram_bot():
    """Qué bot sacaría el aviso, para el chip: «avisos» (token del entorno) o el de la ranura de tlc.

    `tlc` deja el usuario del bot en `<ranura>/usuario` (p. ej. aoshi_dmbot → «dmbot»). Sin ese
    fichero, el nombre de la ranura. None si no hay canal. Sin red y sin tocar el token."""
    if not telegram_listo():
        return None
    if os.environ.get("TELEGRAM_BOT_TOKEN"):
        return "avisos"
    d = os.environ.get("TELEGRAM_STATE_DIR") or os.path.expanduser("~/.claude/channels/telegram")
    try:
        u = open(os.path.join(d, "usuario")).read().strip().lstrip("@")
    except OSError:
        u = ""
    if u:
        return u.split("_", 1)[1] if "_" in u else u
    return os.path.basename(d.rstrip("/")).replace("telegram-", "ranura ") or "plugin"


TPL = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


# Copias que no son proyectos de trabajo (despliegues, copias frías). TL_IGNORAR las amplía.
IGNORAR = [x for x in os.environ.get("TL_IGNORAR", "-prod,copia").split(",") if x]


def descubrir(raices, hondo=3):
    vistos = []
    for r in raices:
        r = os.path.abspath(r)
        for dirpath, dirnames, _ in os.walk(r):
            nivel = dirpath[len(r):].count(os.sep)
            dirnames[:] = [d for d in dirnames if not d.startswith(".") and d not in ("node_modules", "venv", ".venv")
                           and not any(x in d for x in IGNORAR)] if nivel < hondo else []
            if os.path.isdir(os.path.join(dirpath, ".specify", "sessions")):
                vistos.append(dirpath)
                dirnames[:] = []
    return sorted(set(vistos))


def core_hash():
    r = subprocess.run([sys.executable, os.path.join(TPL, ".claude", "scripts", "template_diff.py"), "--core-hash"],
                       capture_output=True, text=True, timeout=30)
    return r.stdout.strip().split()[0] if r.returncode == 0 and r.stdout.strip() else None


def develop_sin_sync():
    """Commits de origin/develop desde el último merge de sync (ref local: no hace fetch)."""
    ult = git(TPL, "log", "-1", "--format=%s", "--grep=^merge(sync)")
    m = re.search(r"hasta\s+([0-9a-f]{7,40})", ult)
    if not m:
        return None
    n = git(TPL, "rev-list", "--count", f"{m.group(1)}..origin/develop")
    return int(n) if n.isdigit() else None


def ram_libre_gb():
    try:
        for l in open("/proc/meminfo"):
            if l.startswith("MemAvailable:"):
                return round(int(l.split()[1]) / 1024 / 1024, 1)
    except Exception:
        return None


def todos(raices):
    core = core_hash()
    proyectos = []
    for p in descubrir(raices):
        try:
            e = estado(p)
        except MarcaDesconocida as err:
            e = {"proyecto": os.path.basename(p), "ruta": p, "sesion": None, "error": str(err)}
        if not e.get("sesion") and not e.get("error"):
            continue
        cv = os.path.join(p, ".claude", "CORE_VERSION")
        mio = open(cv).read().strip() if os.path.exists(cv) else None
        e["core"] = None if (not core or not mio or os.path.samefile(p, TPL)) else (mio == core)
        proyectos.append(e)
    ram = ram_libre_gb()
    vig = {"develop": develop_sin_sync(), "core": core, "ram_gb": ram, "ram_umbral_gb": 3.0,
           "tg": telegram_listo()}
    return {"proyectos": proyectos, "vigilancia": vig, "consejo": consejo(proyectos, vig)}


def consejo(ps, vig):
    for p in ps:
        if p.get("error"):
            return f"{p['proyecto']}: estado_flujo no puede leer su tasks.md"
    if vig["ram_gb"] is not None and vig["ram_gb"] < vig["ram_umbral_gb"]:
        return f"RAM libre {vig['ram_gb']} GB: no lances tests ni navegador"
    for p in ps:
        a = p.get("actual")
        if a and a["bloqueos"] and not a["siguiente"]:
            return f"{p['sesion']['id']} W{a['id']} no cierra: {a['bloqueos'][0]}"
    for p in ps:
        if (p["chips"].get("ahead") or 0) > 0:
            return f"{p['proyecto']}: {p['chips']['ahead']} commits sin subir"
    for p in ps:
        if p.get("core") is False:
            return f"{p['proyecto']}: harness por detrás del template (CORE) — /update-agent"
    if vig["develop"]:
        return f"develop tiene {vig['develop']} commits nuevos desde el último sync"
    for p in ps:
        a = p.get("actual")
        if a and a["bloqueos"]:
            return f"{p['sesion']['id']} W{a['id']}: {a['bloqueos'][0]}"
    return "todo en orden"


def main():
    a = sys.argv[1:]
    pedida = None
    if "--sesion" in a:
        i = a.index("--sesion"); pedida = a[i + 1]; del a[i:i + 2]
    pos = [x for x in a if not x.startswith("--")]
    if "--todos" in a:
        raices = pos or [r for r in os.environ.get("TL_RAICES", "/home/aoshi").split(":") if r]
        t = todos(raices)
        if "--json" in a:
            print(json.dumps(t, ensure_ascii=False)); return
        for p in t["proyectos"]:
            ac = p.get("actual") or {}
            print(f"{p['proyecto']:<22} {p['sesion']['id'] if p.get('sesion') else '✗':<9} "
                  + (f"W{ac['id']} {ac['hecho']}/{ac['total']}" if ac else "") + ("  core≠" if p.get("core") is False else ""))
        v = t["vigilancia"]
        print(f"develop +{v['develop']} · CORE {v['core']} · RAM {v['ram_gb']} GB · tg {'on' if v['tg'] else 'off'}")
        print(f"▸ {t['consejo']}")
        return
    base = pos[0] if pos else os.environ.get("CLAUDE_PROJECT_DIR", os.getcwd())
    if not os.path.isdir(base):
        print(f"estado_flujo: {base} no es un directorio", file=sys.stderr); sys.exit(2)
    try:
        e = estado(base, pedida)
    except MarcaDesconocida as err:
        print(f"estado_flujo: {err}", file=sys.stderr); sys.exit(2)
    if "--json" in a:
        print(json.dumps(e, ensure_ascii=False))
        return
    if not e["sesion"]:
        print(f"{e['proyecto']}: sin sesión SpecKit ni plan de superpowers abierto"); return
    ac = e["actual"]
    print(f"{e['sesion']['id']} · " + " ".join(f"W{w['id']} {w['hecho']}/{w['total']}" for w in e["waves"]))
    if ac:
        print(f"  actual W{ac['id']} {ac['hecho']}/{ac['total']}" + (f" · ✗ {len(ac['bloqueos'])}" if ac["bloqueos"] else ""))
        if ac["siguiente"]:
            print(f"  ▸ {ac['siguiente']}")


if __name__ == "__main__":
    main()
