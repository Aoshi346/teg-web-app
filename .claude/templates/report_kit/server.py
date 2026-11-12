#!/usr/bin/env python3
"""server.py — sirve un set del report-kit y guarda report.json en disco.

Sirve DIR/ (las páginas del set, report.json, shots/, …) y expone:
  GET  /api/health        → {"ok":true,"permisos":{…}}  (detecta backend + perfil de autonomía vigente)
  POST /api/save          → guarda report.json      (cada cambio del dashboard llega aquí)
                            acepta `items` (obligatorio) y `yolo` (la política del plan). Si
                            `yolo.activo` cambia, aplica `settings_profile.py --yolo on|off` al
                            proyecto y lo anota en decisiones.md. Exige JSON y Origin local.
Hace backup rotado en DIR/.backups/ antes de cada guardado. Sin dependencias externas.

Uso:
    python3 server.py [DIR] [--port N]
      DIR  = carpeta del dashboard (por defecto: cwd)
      port = env PORT o --port (por defecto 8800)

Abre:  http://<host>:<port>/dashboard.html
"""
import json, os, sys, shutil, datetime
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer

argv = [a for a in sys.argv[1:]]
PORT = int(os.environ.get("PORT", "8800"))
if "--port" in argv:
    i = argv.index("--port"); PORT = int(argv[i + 1]); del argv[i:i + 2]
ROOT = os.path.abspath(argv[0]) if argv else os.getcwd()
ITEMS = os.path.join(ROOT, "report.json")
HOST = os.environ.get("HOST", "127.0.0.1")  # solo local por defecto; export HOST=0.0.0.0 para exponer (NO recomendado)


# PV-3 · los DOS montajes extra, y ninguno más:
#     /core/   -> .docs/core/    las páginas permanentes (lo que el proyecto ES)
#     /plans/  -> .docs/plans/   los informes, para poder ir de uno a otro
#
# Por qué no ampliar la raíz servida a .docs/ y ya: ahí cuelga resources/ con código de cliente.
# Servir un directorio de más para que un enlace no dé 404 es un intercambio pésimo
# (rules/security.md). Esto abre exactamente dos carpetas, con el escape bloqueado.
#
# Y por qué las rutas son las MISMAS en disco y servidas: desde <plan>/dashboard.html el enlace al
# Core es ../../core/x.html — en disco resuelve a .docs/core/x.html, y en el navegador los `..` que
# se pasan de la raíz se descartan (RFC 3986 §5.2.4), así que llega como /core/x.html. Un solo
# juego de enlaces para los dos modos.
#
# Lo encontró un navegador de verdad, no una lectura del código: el montaje de /core/ estaba bien
# y la VUELTA (../plans/<plan>/dashboard.html) daba 404, porque el plan se sirve en la raíz. El
# mismo 404 tenía ya el selector de plan de PV-7 y nadie lo había pulsado servido.
_DOCS = os.path.abspath(os.path.join(ROOT, "..", ".."))
MOUNTS = {"/core": os.path.join(_DOCS, "core"), "/plans": os.path.join(_DOCS, "plans")}


# T-101 · EL INTERRUPTOR YOLO DEL DASHBOARD CAMBIA LOS PERMISOS DE VERDAD.
# Hasta aquí el botón «🚀 Modo yolo» guardaba una política en meta.yolo y nada más: settings.json
# no se enteraba. Ahora, cuando `yolo.activo` cambia, se llama a `settings_profile.py --yolo on|off`
# sobre el proyecto al que pertenece este plan. `off` restaura los permisos ENTEROS (no pasa por
# --perfil, que nunca baja el deny y dejaría push/merge denegados en vez de preguntados).
#
# Y por eso /api/save se blinda: un endpoint que cambia permisos no puede aceptar un POST de
# cualquier página abierta en el navegador. Dos comprobaciones, las dos baratas:
#   · Content-Type application/json → fuerza el preflight CORS, que este servidor no responde,
#     así que una página ajena no puede ni mandar la petición.
#   · Origin, si viene, tiene que ser local (127.0.0.1 / localhost / [::1]). Se mira el HOST y no
#     el puerto: por túnel SSH el puerto local puede ser otro.
def _proyecto():
    """La raíz del proyecto: el primer ancestro del plan con .claude/settings.json."""
    d = ROOT
    while True:
        if os.path.exists(os.path.join(d, ".claude", "settings.json")):
            return d
        padre = os.path.dirname(d)
        if padre == d:
            return None
        d = padre


def _perfiles(proj):
    for base in (proj, os.environ.get("TL_TEMPLATE_DIR", "/home/tech-lead-template")):
        s = os.path.join(base or "", ".claude", "scripts", "settings_profile.py")
        if base and os.path.exists(s):
            return s
    return None


def _permisos(*args):
    """Llama a settings_profile.py. Devuelve (ok, salida). Nunca lanza."""
    import subprocess
    proj = _proyecto()
    s = _perfiles(proj) if proj else None
    if not proj or not s:
        return False, "no se encontró el settings.json del proyecto o settings_profile.py"
    try:
        r = subprocess.run([sys.executable, s, proj, *args], capture_output=True, text=True, timeout=20)
        return r.returncode == 0, (r.stdout + r.stderr).strip()
    except Exception as e:
        return False, str(e)


def _anotar(linea):
    """Deja rastro en decisiones.md del plan (solo añade). Si falla, no rompe el guardado."""
    try:
        f = os.path.join(ROOT, "decisiones.md")
        nuevo = not os.path.exists(f)
        with open(f, "a", encoding="utf-8") as fh:
            if nuevo:
                fh.write("# Decisiones del plan\n\n> Solo se añade. Cada línea: fecha · quién · qué.\n\n")
            fh.write(linea + "\n")
    except Exception:
        pass


class Handler(SimpleHTTPRequestHandler):
    def __init__(self, *a, **k):
        super().__init__(*a, directory=ROOT, **k)

    def translate_path(self, path):
        import posixpath, urllib.parse
        p = path.split("?", 1)[0].split("#", 1)[0]
        for pref, base in MOUNTS.items():
            if p == pref or p.startswith(pref + "/"):
                rel = urllib.parse.unquote(p[len(pref) + 1:])
                # se descarta cualquier segmento .. ANTES de unir: nada puede salirse de `base`
                segs = [x for x in posixpath.normpath("/" + rel).split("/") if x and x != ".."]
                dest = os.path.normpath(os.path.join(base, *segs))
                if not os.path.isdir(base) or os.path.commonpath([dest, base]) != base:
                    return base
                return dest
        return super().translate_path(path)

    def log_message(self, format, *args):  # noqa: A002 - firma de la stdlib
        return  # silencioso

    def _json(self, code, obj):
        body = json.dumps(obj).encode("utf-8")
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(body)

    def _vivo(self):
        """Estado EN VIVO: lo que está pasando ahora mismo, no lo que se generó al construir.

        Lee tres fuentes que ya existen y nadie juntaba:
          · report.json           → los items y su estado
          · los journal.jsonl de los workflows → qué agentes corren AHORA y cuáles cerraron
          · el audit log          → la última actividad real

        Solo lectura y datos AGREGADOS: nunca rutas absolutas ni contenido de ficheros. Cada
        endpoint es superficie, y detrás de esto hay material de cliente."""
        import glob, json as _j, os as _o, time
        base = _o.path.dirname(_o.path.abspath(__file__))
        out = {"ts": int(time.time()), "items": {}, "workflows": [], "actividad": []}

        rp = _o.path.join(base, "report.json")
        if _o.path.exists(rp):
            try:
                it = _j.load(open(rp, encoding="utf-8")).get("items", [])
                out["items"] = {
                    "total": len(it),
                    "done": sum(1 for i in it if i.get("status") == "done"),
                    "blocked": sum(1 for i in it if i.get("status") == "blocked"),
                    "aprobados": sum(1 for i in it if i.get("decision") == "aprobar"),
                    "sin_decidir": sum(1 for i in it if not i.get("decision")),
                }
            except Exception:
                pass

        # Workflows: un journal por run. `started` sin su `result` = corriendo ahora.
        wdir = _o.path.expanduser("~/.claude/projects")
        for j in sorted(glob.glob(_o.path.join(wdir, "**", "workflows", "wf_*", "journal.jsonl"),
                                  recursive=True), key=_o.path.getmtime, reverse=True)[:4]:
            try:
                lanzados, cerrados, ultimo = 0, 0, ""
                for ln in open(j, encoding="utf-8"):
                    try: d = _j.loads(ln)
                    except Exception: continue
                    t = d.get("type")
                    if t == "started": lanzados += 1
                    elif t == "result":
                        cerrados += 1
                        ultimo = str(d.get("label") or "")[:48] or ultimo
                out["workflows"].append({
                    "run": _o.path.basename(_o.path.dirname(j))[:11],
                    "lanzados": lanzados, "cerrados": cerrados,
                    "corriendo": max(0, lanzados - cerrados),
                    "ultimo": ultimo,
                    "edad_s": int(time.time() - _o.path.getmtime(j)),
                })
            except Exception:
                continue

        alog = _o.path.expanduser("~/.claude/audit")
        for f in sorted(glob.glob(_o.path.join(alog, "*.jsonl")), key=_o.path.getmtime,
                        reverse=True)[:1]:
            try:
                with open(f, "rb") as fh:
                    fh.seek(0, 2); fh.seek(max(0, fh.tell() - 8000))
                    for ln in fh.read().decode("utf-8", "ignore").splitlines()[-8:]:
                        try: d = _j.loads(ln)
                        except Exception: continue
                        out["actividad"].append({
                            "ts": d.get("ts", ""), "tool": d.get("tool", ""),
                            # solo el basename: una ruta absoluta en un endpoint es una fuga
                            "que": _o.path.basename(str(d.get("file") or d.get("skill")
                                                        or d.get("agent") or d.get("cmd", "")))[:60],
                        })
            except Exception:
                pass
        out["actividad"] = out["actividad"][-8:][::-1]
        return out

    def do_GET(self):
        if self.path.rstrip("/") == "/api/vivo":
            body = json.dumps(self._vivo()).encode()
            self.send_response(200)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.send_header("Cache-Control", "no-store")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers(); self.wfile.write(body); return
        if self.path.rstrip("/") == "/api/health":
            ok, out = _permisos("--estado")
            try:
                perm = json.loads(out) if ok else {"error": out}
            except Exception:
                perm = {"error": out}
            return self._json(200, {"ok": True, "permisos": perm})
        return super().do_GET()

    def _origen_ok(self):
        import urllib.parse
        o = self.headers.get("Origin")
        if not o or o == "null":
            return not o          # sin Origin (curl, scripts) sí; «null» (iframes sandbox, file://) no
        return urllib.parse.urlsplit(o).hostname in ("127.0.0.1", "localhost", "::1")

    def do_POST(self):
        if self.path.rstrip("/") != "/api/save":
            return self._json(404, {"ok": False, "error": "not found"})
        if not (self.headers.get("Content-Type") or "").lower().startswith("application/json"):
            return self._json(415, {"ok": False, "error": "Content-Type debe ser application/json"})
        if not self._origen_ok():
            return self._json(403, {"ok": False, "error": "origen no local"})
        try:
            n = int(self.headers.get("Content-Length", 0))
            payload = json.loads(self.rfile.read(n).decode("utf-8"))
            items = payload.get("items")
            if not isinstance(items, list):
                raise ValueError("payload.items debe ser una lista")
            if os.path.exists(ITEMS):
                bdir = os.path.join(ROOT, ".backups"); os.makedirs(bdir, exist_ok=True)
                stamp = datetime.datetime.now().strftime("%Y%m%d-%H%M")
                shutil.copy2(ITEMS, os.path.join(bdir, "report-%s.json" % stamp))
            cur = json.load(open(ITEMS, encoding="utf-8")) if os.path.exists(ITEMS) else {}
            antes = bool(((cur.get("meta") or {}).get("yolo") or {}).get("activo"))
            cur["items"] = items
            # La política de modo yolo es del PLAN, no de un item: vive en meta.
            # Se acepta SOLO esa clave — el navegador no reescribe el resto del meta,
            # que lo genera tasks_to_items.py y no es suyo.
            if "yolo" in payload:
                y = payload.get("yolo")
                if y is not None and not isinstance(y, dict):
                    raise ValueError("payload.yolo debe ser un objeto o null")
                cur.setdefault("meta", {})["yolo"] = y
            tmp = ITEMS + ".tmp"
            with open(tmp, "w", encoding="utf-8") as f:
                json.dump(cur, f, ensure_ascii=False, indent=2)
            os.replace(tmp, ITEMS)
            ahora = bool(((cur.get("meta") or {}).get("yolo") or {}).get("activo"))
            permisos = None
            if "yolo" in payload and ahora != antes:
                ok, out = _permisos("--yolo", "on" if ahora else "off")
                permisos = {"ok": ok, "salida": out[-400:]}
                stamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
                _anotar(f"- {stamp} · dashboard · modo YOLO {'ACTIVADO' if ahora else 'desactivado'} — "
                        + (("permisos del proyecto → perfil yolo" if ahora else
                            "permisos del proyecto restaurados a como estaban") if ok
                           else f"⚠️ los permisos NO cambiaron: {out[-200:]}"))
            return self._json(200, {"ok": True, "saved": len(items), "yolo": ahora,
                                    "permisos": permisos})
        except Exception as e:
            return self._json(500, {"ok": False, "error": str(e)})


if __name__ == "__main__":
    if not os.path.isdir(ROOT):
        sys.exit("ERROR: no existe el directorio %s" % ROOT)
    os.chdir(ROOT)
    srv = ThreadingHTTPServer((HOST, PORT), Handler)
    print("SpecKit dashboard · %s" % ROOT)
    # El enlace que se le da al Usuario es localhost, y se comprueba antes de darlo (MO-26):
    #   python3 .claude/templates/report_kit/enlace.py <puerto> index.html dashboard.html
    print("  → http://localhost:%d/dashboard.html  (escucha en %s · Ctrl+C para parar)" % (PORT, HOST))
    try:
        srv.serve_forever()
    except KeyboardInterrupt:
        print("\nparado.")
