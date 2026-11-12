#!/usr/bin/env python3
"""ticket_kit.py — la skill `verify-ticket` contra un Django de verdad, con su base desechable.

    python3 .claude/smoke/harvest/ticket_kit.py --python <python con django y playwright>   # exit 1 si falla

El python que se pasa necesita `django` 5.x y `playwright` (y Chromium: el del sistema vale). Sin él,
sale 2: no se pudo medir (no descarga nada). `bash .claude/hooks/check-ram.sh` antes; ~1 min.

Monta en un temporal un Django mínimo (SQLite, una vista con login obligatorio que enseña una tabla
con un nombre y un DNI, otra pública), siembra un usuario de prueba, levanta runserver en 127.0.0.1 y
comprueba:
  · verde: el kit entra sin contraseña (sesión en BBDD y en cookie firmada), captura con las celdas
    enmascaradas, y deja report.json, results.html con la captura embebida, el PDF y las anotaciones
    del auditor; el DNI real no está en ningún fichero;
  · un texto que no está → 1 y el criterio en notdone;
  · el DNI sin enmascarar → la captura se descarta (blocked) y el kit sale con 1;
  · DEBUG=False → session_login sale con 1 y el kit no captura nada; BBDD remota → 1;
  · sabotaje: un session_login sin el guard de DEBUG entrega la cookie, y esta prueba lo caza.
El temporal y el servidor se borran al terminar.
"""
from __future__ import annotations

import argparse
import json
import os
import shutil
import socket
import subprocess
import sys
import tempfile
import textwrap
import time
import urllib.request

CL = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
KIT = os.path.join(CL, "skills", "verify-ticket")
REAL_DNI = "12345678Z"
FAILURES: list[str] = []

SETTINGS = '''
import os
SECRET_KEY = "solo-para-esta-prueba"
DEBUG = os.environ.get("TK_DEBUG", "1") == "1"
ALLOWED_HOSTS = ["127.0.0.1"]
INSTALLED_APPS = ["django.contrib.auth", "django.contrib.contenttypes", "django.contrib.sessions"]
MIDDLEWARE = ["django.contrib.sessions.middleware.SessionMiddleware",
              "django.contrib.auth.middleware.AuthenticationMiddleware"]
ROOT_URLCONF = "demo.urls"
SESSION_ENGINE = os.environ.get("TK_SESSION", "django.contrib.sessions.backends.db")
DATABASES = {"default": {"ENGINE": "django.db.backends.sqlite3",
                         "NAME": os.path.join(os.path.dirname(__file__), "..", "db.sqlite3")}}
if os.environ.get("TK_DB_HOST"):
    # el motor «dummy» carga sin driver: lo que se prueba es el guard, no la conexión
    DATABASES["default"] = {"ENGINE": "django.db.backends.dummy", "NAME": "app",
                            "HOST": os.environ["TK_DB_HOST"]}
if os.environ.get("TK_DB_SERVICE"):
    DATABASES["default"] = {"ENGINE": "django.db.backends.dummy", "NAME": "app", "HOST": "",
                            "OPTIONS": {"service": os.environ["TK_DB_SERVICE"]}}
if os.environ.get("TK_CACHE"):
    CACHES = {"default": {"BACKEND": "django.core.cache.backends.redis.RedisCache",
                          "LOCATION": os.environ["TK_CACHE"]}}
USE_TZ = True
'''
URLS = f'''
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse
from django.urls import path

@login_required(login_url="/no-login/")
def workers(request):
    return HttpResponse("<html><body><h1>Trabajadores activos</h1><p>Usuario: " + request.user.username +
        "</p><table><tr><td class='nombre'>GARCÍA LÓPEZ, Ana</td><td class='dni'>{REAL_DNI}</td></tr>"
        "</table></body></html>")

def public(request):
    return HttpResponse("<html><body><h1>Bienvenida</h1></body></html>")

urlpatterns = [path("workers/", workers), path("public/", public)]
'''


def check(name: str, ok: bool, extra: str = "") -> None:
    print(f"  {'✓' if ok else '✗'} {name}{' · ' + extra if extra else ''}")
    if not ok:
        FAILURES.append(name)


def free_port() -> int:
    s = socket.socket()
    s.bind(("127.0.0.1", 0))
    port = s.getsockname()[1]
    s.close()
    return port


class Project:
    def __init__(self, py: str):
        self.py, self.root = py, tempfile.mkdtemp(prefix="tl-ticket-kit-")
        self.backend = os.path.join(self.root, "backend")
        os.makedirs(os.path.join(self.backend, "demo"))
        for name, body in (("__init__.py", ""), ("settings.py", SETTINGS), ("urls.py", URLS)):
            with open(os.path.join(self.backend, "demo", name), "w", encoding="utf-8") as f:
                f.write(body)
        self.server = None
        self.port = free_port()

    def env(self, **kw) -> dict:
        e = dict(os.environ, DJANGO_SETTINGS_MODULE="demo.settings", PYTHONPATH=self.backend)
        e.pop("CLAUDE_PROJECT_DIR", None)
        e.update(kw)
        return e

    def manage(self, *args: str, **env) -> subprocess.CompletedProcess:
        return subprocess.run([self.py, "-m", "django", *args], cwd=self.backend, env=self.env(**env),
                              capture_output=True, text=True, timeout=120)

    def seed(self) -> None:
        r = self.manage("migrate", "-v0")
        assert r.returncode == 0, r.stderr
        r = self.manage("shell", "-c", "from django.contrib.auth.models import User;"
                        "User.objects.create_user('prueba_tecnico', password=None)")
        assert r.returncode == 0, r.stderr

    def start(self, **env) -> None:
        self.stop()
        self.server = subprocess.Popen([self.py, "-m", "django", "runserver", "--noreload",
                                        f"127.0.0.1:{self.port}"], cwd=self.backend, env=self.env(**env),
                                       stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        for _ in range(60):
            try:
                urllib.request.urlopen(f"http://127.0.0.1:{self.port}/public/", timeout=1)
                return
            except OSError:
                time.sleep(0.25)
        raise RuntimeError("runserver no arrancó")

    def stop(self) -> None:
        if self.server:
            self.server.terminate()
            self.server.wait(timeout=10)
            self.server = None

    def ticket(self, name: str, criteria: list[dict], auditors: list[str] | None = None) -> str:
        d = os.path.join(self.root, "plan", name)
        os.makedirs(d, exist_ok=True)
        t = {"schema": "ticket-verify/1", "ticket": f"TK-{name}", "title": "Prueba del kit",
             "base_url": f"http://127.0.0.1:{self.port}", "settings": "demo.settings",
             "project_root": self.root, "backend_dir": "backend",
             "actors": {"tecnico": {"username": "prueba_tecnico"}}, "criteria": criteria,
             "auditors": auditors or []}
        p = os.path.join(d, "ticket.json")
        with open(p, "w", encoding="utf-8") as f:
            json.dump(t, f, ensure_ascii=False)
        return p

    def verify(self, ticket: str, *extra: str, **env) -> subprocess.CompletedProcess:
        return subprocess.run([self.py, os.path.join(KIT, "verify_ticket.py"), ticket,
                               "--django-python", self.py, *extra], env=self.env(**env),
                              capture_output=True, text=True, timeout=300)

    def session_login(self, script: str, **env) -> subprocess.CompletedProcess:
        return subprocess.run([self.py, script, "--settings", "demo.settings", "--username", "prueba_tecnico"],
                              cwd=self.backend, env=self.env(**env), capture_output=True, text=True, timeout=60)


AC_OK = {"id": "AC-1", "title": "El técnico ve la lista de trabajadores", "actor": "tecnico",
         "url": "/workers/", "expect_text": ["Trabajadores activos", "prueba_tecnico"],
         "mask": ["td.nombre", "td.dni"]}
AC_PUBLIC = {"id": "AC-2", "title": "La portada pública abre sin sesión", "url": "/public/",
             "expect_text": ["Bienvenida"]}


def grep_tree(root: str, needle: str) -> list[str]:
    hits = []
    for d, _, files in os.walk(root):
        for f in files:
            p = os.path.join(d, f)
            try:
                if needle.encode() in open(p, "rb").read():
                    hits.append(os.path.relpath(p, root))
            except OSError:
                pass
    return hits


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--python", required=True, help="python con django y playwright")
    ap.add_argument("--keep", help="copia aquí el informe del caso verde para mirarlo")
    a = ap.parse_args()
    probe = subprocess.run([a.python, "-c", "import django, playwright"], capture_output=True)
    if probe.returncode != 0:
        print("NO MEDIDO: ese python no tiene django y playwright", file=sys.stderr)
        return 2
    pr = Project(a.python)
    try:
        pr.seed()
        print("verde · sesión en BBDD")
        pr.start()
        aud_dir = os.path.join(pr.root, "plan", "verde", "roberto")
        os.makedirs(aud_dir)
        with open(os.path.join(aud_dir, "findings.json"), "w", encoding="utf-8") as f:
            json.dump({"schema": "code-findings/1", "agent": "roberto-clean-code", "autonomy_phase": 1,
                       "findings": [{"id": "ROB-001", "severity": "P2", "title": "nombre poco claro"}],
                       "verdict": {"global": "PASA_CON_AVISOS", "verdict": "partial"}}, f)
        t = pr.ticket("verde", [AC_OK, AC_PUBLIC], ["roberto/findings.json"])
        out = os.path.dirname(t)
        r = pr.verify(t, "--pdf")
        check("criterios que se cumplen → 0", r.returncode == 0, f"rc={r.returncode} {r.stderr[-300:]}")
        rep = json.load(open(os.path.join(out, "report.json"), encoding="utf-8"))
        items = {i["id"]: i for i in rep["items"]}
        check("AC-1 done con su captura", items.get("AC-1", {}).get("verdict") == "done"
              and os.path.exists(os.path.join(out, "shots", "AC-1.png")))
        check("anotaciones de Roberto en el informe", items.get("AUD-roberto-clean-code", {}).get("verdict") == "partial")
        check("PII-REV pendiente hasta que alguien mire", items.get("PII-REV", {}).get("verdict") == "review")
        html = open(os.path.join(out, "results.html"), encoding="utf-8").read()
        check("results.html con la captura embebida", "data:image" in html)
        check("PDF generado", open(os.path.join(out, "informe.pdf"), "rb").read(5) == b"%PDF-")
        check("el DNI real no está en ningún fichero del informe", not grep_tree(out, REAL_DNI),
              ", ".join(grep_tree(out, REAL_DNI)))
        reg = subprocess.run([sys.executable, os.path.join(CL, "scripts", "guarda_pii_capturas.py"), "--registrar",
                              os.path.join(out, "shots"), "--por", "smoke",
                              *(os.path.join(out, "shots", f) for f in ("AC-1.png", "AC-2.png"))],
                             capture_output=True, text=True)
        r = pr.verify(t, "--no-build")
        rep = json.load(open(os.path.join(out, "report.json"), encoding="utf-8"))
        rev = next(i for i in rep["items"] if i["id"] == "PII-REV")
        check("tras registrar la revisión → PII-REV done", reg.returncode == 0 and rev["verdict"] == "done",
              rev["why"][-200:])

        if a.keep:
            shutil.copytree(out, a.keep, dirs_exist_ok=True)
        print("verde · sesión en cookie firmada")
        pr.start(TK_SESSION="django.contrib.sessions.backends.signed_cookies")
        r = pr.verify(pr.ticket("firmada", [AC_OK]), "--no-build",
                      TK_SESSION="django.contrib.sessions.backends.signed_cookies")
        check("signed_cookies → 0", r.returncode == 0, r.stderr[-300:])
        pr.start()

        print("controles")
        r = pr.verify(pr.ticket("falla", [dict(AC_PUBLIC, id="AC-3", expect_text=["Texto que no está"])]),
                      "--no-build")
        res = json.load(open(os.path.join(pr.root, "plan", "falla", "resultados.json")))["results"][0]
        check("texto ausente → 1 y notdone", r.returncode == 1 and res["verdict"] == "notdone")
        r = pr.verify(pr.ticket("sin-python", [AC_OK]), "--no-build", "--django-python", "/nonexistent/python")
        check("python de Django que no existe → 2 (no medido, no «el guard se negó»)", r.returncode == 2,
              f"rc={r.returncode}")
        pr.stop()
        r = pr.verify(pr.ticket("caido", [AC_PUBLIC]), "--no-build")
        check("runserver caído → 2", r.returncode == 2, f"rc={r.returncode}")
        pr.start()
        t = pr.ticket("pii", [dict(AC_OK, id="AC-PII", mask=["td.nombre"])])
        r = pr.verify(t, "--no-build")
        res = json.load(open(os.path.join(pr.root, "plan", "pii", "resultados.json")))["results"][0]
        check("DNI sin enmascarar → captura descartada (blocked) y 1",
              r.returncode == 1 and res["verdict"] == "blocked"
              and not os.path.exists(os.path.join(pr.root, "plan", "pii", "shots", "AC-PII.png")))
        check("…y el DNI no queda escrito en resultados.json", not grep_tree(os.path.dirname(t), REAL_DNI))

        real = os.path.join(KIT, "session_login.py")
        check("DEBUG=False → session_login 1", pr.session_login(real, TK_DEBUG="0").returncode == 1)
        t = pr.ticket("debug-off", [AC_OK])
        r = pr.verify(t, TK_DEBUG="0")
        check("DEBUG=False → el kit sale con 1 sin capturar",
              r.returncode == 1 and not os.path.exists(os.path.join(os.path.dirname(t), "shots")), r.stderr[-200:])
        check("BBDD remota → session_login 1",
              pr.session_login(real, TK_DB_HOST="db.prod.example").returncode == 1)
        check("HOST vacío y el destino en OPTIONS['service'] → session_login 1",
              pr.session_login(real, TK_DB_SERVICE="prod").returncode == 1)
        check("sesiones en una caché remota → session_login 1",
              pr.session_login(real, TK_SESSION="django.contrib.sessions.backends.cache",
                               TK_CACHE="redis://cache.prod.example:6379/1").returncode == 1)
        check("control: DEBUG=True y BBDD local → cookie",
              pr.session_login(real).returncode == 0)

        print("sabotaje")
        sab_dir = tempfile.mkdtemp(prefix="tl-ticket-kit-sab-")
        sab = os.path.join(sab_dir, "session_login.py")
        src = open(real, encoding="utf-8").read()
        assert "if not settings.DEBUG:" in src
        src = src.replace("if not settings.DEBUG:", "if False:").replace(
            'KIT.parent.parent / "scripts"', repr(os.path.join(CL, "scripts")))  # la copia vive fuera del kit
        open(sab, "w", encoding="utf-8").write(src)
        rc = pr.session_login(sab, TK_DEBUG="0").returncode
        check("sin el guard de DEBUG la cookie sale con DEBUG=False, y esta prueba lo caza", rc == 0,
              f"rc={rc}")
        shutil.rmtree(sab_dir, ignore_errors=True)
    finally:
        pr.stop()
        shutil.rmtree(pr.root, ignore_errors=True)
    print(f"\n{'OK' if not FAILURES else 'FALLA'}: {len(FAILURES)} fallo(s)")
    return 1 if FAILURES else 0


if __name__ == "__main__":
    sys.exit(main())
