#!/usr/bin/env python3
"""demo_e2e.py — `templates/frontend-demo/e2e/run-e2e.mjs` contra un Django y un PostgreSQL de verdad.

    python3 .claude/smoke/harvest/demo_e2e.py --python <python con django y psycopg>   # exit 1 si falla

El python que se pasa necesita `django` 5.x y `psycopg` 3 (un venv desechable vale:
`python3 -m venv <dir> && <dir>/bin/pip install "django==5.2.*" "psycopg[binary]==3.2.*"`). Sin él,
o sin la imagen `postgres:17.11-alpine` en local, sale 2: no se pudo medir (no descarga nada).

Monta en un directorio temporal un proyecto Django mínimo (login de verdad con sesión y CSRF, una
vista que exige sesión y un `seed_demo` con usuario sintético), un PostgreSQL desechable publicado
solo en 127.0.0.1, y comprueba:
  · verde: base creada, migrada y sembrada; runserver en 127.0.0.1; el test entra con usuario y
    contraseña y lee la vista protegida; al terminar la base ya no existe y el puerto está libre;
  · contraseña mala → 1, y la base se borra igual;
  · E2E_DB sin el prefijo, o un prefijo que no acaba en «_e2e» → 2 sin crear nada;
  · puerto ocupado → 2;
  · E2E_KEEP_DB=1 conserva la base y E2E_REUSE_DB=1 la reutiliza sin sembrar;
  · sabotaje: una copia del runner sin el borrado deja la base viva, y la prueba lo ve.
El contenedor y el directorio se borran al terminar. `bash .claude/hooks/check-ram.sh` antes.
"""
from __future__ import annotations

import os
import shutil
import socket
import subprocess
import sys
import tempfile
import textwrap
import time

CL = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
RUNNER = os.path.join(CL, "templates", "frontend-demo", "e2e", "run-e2e.mjs")
IMAGE = "postgres:17.11-alpine"
NAME = f"tl-smoke-demo-e2e-{os.getpid()}"
PG_PASSWORD = "solo-para-esta-prueba"
FAILURES: list[str] = []

SETTINGS = '''
import os
SECRET_KEY = "solo-para-esta-prueba"
DEBUG = True
ALLOWED_HOSTS = ["127.0.0.1"]
INSTALLED_APPS = ["django.contrib.auth", "django.contrib.contenttypes", "django.contrib.sessions", "demoapp"]
MIDDLEWARE = ["django.contrib.sessions.middleware.SessionMiddleware",
              "django.middleware.csrf.CsrfViewMiddleware",
              "django.contrib.auth.middleware.AuthenticationMiddleware"]
ROOT_URLCONF = "demo.urls"
TEMPLATES = [{"BACKEND": "django.template.backends.django.DjangoTemplates", "DIRS": [], "APP_DIRS": True,
              "OPTIONS": {"context_processors": ["django.template.context_processors.request"]}}]
DATABASES = {"default": {"ENGINE": "django.db.backends.postgresql", "NAME": os.environ["POSTGRES_DB"],
                         "USER": "postgres", "PASSWORD": os.environ["POSTGRES_PASSWORD"],
                         "HOST": "127.0.0.1", "PORT": os.environ["POSTGRES_PORT"]}}
USE_TZ = True
'''
URLS = '''
from django.contrib.auth.views import LoginView
from django.http import HttpResponse, JsonResponse
from django.urls import path

def health(request):
    return HttpResponse("ok")

def me(request):
    if not request.user.is_authenticated:
        return JsonResponse({"detail": "sin sesión"}, status=401)
    return JsonResponse({"username": request.user.username})

urlpatterns = [path("health/", health), path("accounts/login/", LoginView.as_view()), path("api/me/", me)]
'''
LOGIN_HTML = ('<form method="post">{% csrf_token %}{{ form.as_p }}<button type="submit">Entrar</button></form>')
SEED = '''
from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand

class Command(BaseCommand):
    help = "Usuario sintético de la demo"
    def handle(self, *args, **opts):
        u, _ = get_user_model().objects.get_or_create(username="demo")
        u.set_password("demo-pass-123")
        u.save()
        self.stdout.write("seed_demo: usuario demo")
'''
# El test: entra por el formulario de login (CSRF + sesión) y lee la vista que exige sesión.
LOGIN_TEST = '''
import http.cookiejar, json, os, re, sys, urllib.parse, urllib.request
api = os.environ["E2E_API_URL"]
jar = http.cookiejar.CookieJar()
op = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(jar))
html = op.open(api + "/accounts/login/").read().decode()
token = re.search(r'name="csrfmiddlewaretoken" value="([^"]+)"', html).group(1)
data = urllib.parse.urlencode({"csrfmiddlewaretoken": token, "username": "demo",
                               "password": os.environ.get("E2E_LOGIN_PASSWORD", "demo-pass-123"),
                               "next": "/health/"}).encode()
op.open(urllib.request.Request(api + "/accounts/login/", data=data, headers={"Referer": api + "/"}))
try:
    body = json.loads(op.open(api + "/api/me/").read())
except urllib.error.HTTPError as e:
    print("login fallido:", e.code); sys.exit(1)
print("login ok como", body["username"], "· base", os.environ["E2E_DB"])
import subprocess
port = api.rsplit(":", 1)[1]
print("escucha:", " ".join(l.split()[3] for l in subprocess.run(["ss", "-Htln"], capture_output=True,
      text=True).stdout.splitlines() if l.split()[3].endswith(":" + port)))
sys.exit(0 if body["username"] == "demo" else 1)
'''


def check(name: str, ok: bool, extra: str = "") -> None:
    print(f"  {'✓' if ok else '✗'} {name}{' · ' + extra if extra else ''}")
    if not ok:
        FAILURES.append(name)


def write(root: str, rel: str, text: str) -> None:
    path = os.path.join(root, rel)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        f.write(textwrap.dedent(text).lstrip())


def db_exists(name: str) -> bool:
    r = subprocess.run(["docker", "exec", NAME, "psql", "-U", "postgres", "-Atc",
                        f"SELECT 1 FROM pg_database WHERE datname = '{name}'"], capture_output=True, text=True)
    return r.stdout.strip() == "1"


def port_free(port: int) -> bool:
    with socket.socket() as s:
        return s.connect_ex(("127.0.0.1", port)) != 0


def free_port() -> int:
    with socket.socket() as s:
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]


def main() -> int:
    if "--python" not in sys.argv:
        print("sin datos: falta --python <python con django y psycopg> (ver la cabecera)")
        return 2
    py = sys.argv[sys.argv.index("--python") + 1]
    if subprocess.run([py, "-c", "import django, psycopg"], capture_output=True).returncode:
        print(f"sin datos: {py} no tiene django y psycopg")
        return 2
    if subprocess.run(["docker", "image", "inspect", IMAGE], capture_output=True).returncode:
        print(f"sin datos: la imagen {IMAGE} no está en local (no se descarga nada)")
        return 2
    if shutil.which("node") is None:
        print("sin datos: no hay node")
        return 2

    tmp = tempfile.mkdtemp(prefix="tl-demo-e2e-")
    try:
        subprocess.run(["docker", "run", "-d", "--rm", "--name", NAME, "-e", f"POSTGRES_PASSWORD={PG_PASSWORD}",
                        "-p", "127.0.0.1::5432", IMAGE], check=True, capture_output=True)
        pg_port = subprocess.run(["docker", "port", NAME, "5432/tcp"], capture_output=True, text=True,
                                 check=True).stdout.split(":")[-1].strip()
        for _ in range(60):
            if subprocess.run(["docker", "exec", NAME, "pg_isready", "-U", "postgres"],
                              capture_output=True).returncode == 0:
                break
            time.sleep(1)
        time.sleep(1)  # pg_isready responde antes de que el servidor final acepte conexiones TCP

        write(tmp, "backend/manage.py", '''
            import os, sys
            os.environ.setdefault("DJANGO_SETTINGS_MODULE", "demo.settings")
            from django.core.management import execute_from_command_line
            execute_from_command_line(sys.argv)
        ''')
        write(tmp, "backend/demo/__init__.py", "")
        write(tmp, "backend/demo/settings.py", SETTINGS)
        write(tmp, "backend/demo/urls.py", URLS)
        write(tmp, "backend/demoapp/__init__.py", "")
        write(tmp, "backend/demoapp/templates/registration/login.html", LOGIN_HTML)
        write(tmp, "backend/demoapp/management/__init__.py", "")
        write(tmp, "backend/demoapp/management/commands/__init__.py", "")
        write(tmp, "backend/demoapp/management/commands/seed_demo.py", SEED)
        write(tmp, "frontend/e2e/login_test.py", LOGIN_TEST)
        shutil.copy(RUNNER, os.path.join(tmp, "frontend/e2e/run-e2e.mjs"))
        runner = os.path.join(tmp, "frontend/e2e/run-e2e.mjs")

        api_port = free_port()
        base_env = {**os.environ, "POSTGRES_PASSWORD": PG_PASSWORD, "POSTGRES_PORT": pg_port,
                    "E2E_ROOT": tmp, "E2E_MANAGE": f"{py} backend/manage.py", "E2E_DB_PREFIX": "demo_e2e",
                    "E2E_API_PORT": str(api_port), "E2E_HEALTH_PATH": "/health/", "E2E_WEB_CMD": "",
                    "E2E_TEST_CMD": f"{py} e2e/login_test.py"}

        def e2e(script: str = runner, **extra) -> subprocess.CompletedProcess:
            return subprocess.run(["node", script], env={**base_env, **extra}, capture_output=True,
                                  text=True, timeout=300)

        print("run-e2e.mjs contra Django + PostgreSQL desechable (127.0.0.1)")
        r = e2e()
        out = r.stdout + r.stderr
        check("verde: crea, migra, siembra, entra con login y lee la vista protegida", r.returncode == 0
              and "login ok como demo" in out, f"rc={r.returncode}" + ("" if r.returncode == 0 else out[-600:]))
        listen = next((line for line in out.splitlines() if line.startswith("escucha:")), "")
        check("verde: el backend escuchó solo en 127.0.0.1 (ss, mientras corría)",
              listen.split()[1:] == [f"127.0.0.1:{api_port}"], listen)
        check("verde: la base ya no existe al terminar", not db_exists("demo_e2e"))
        check("verde: el puerto del backend queda libre", port_free(api_port))

        r = e2e(E2E_LOGIN_PASSWORD="mala")
        check("contraseña mala → 1", r.returncode == 1, f"rc={r.returncode}")
        check("contraseña mala: la base se borra igual", not db_exists("demo_e2e"))

        r = e2e(E2E_DB="demo")
        check("E2E_DB sin el prefijo → 2 sin crear nada", r.returncode == 2 and not db_exists("demo"),
              f"rc={r.returncode}")
        r = e2e(E2E_DB_PREFIX="demo", E2E_DB="demo")
        check("prefijo que no acaba en _e2e → 2", r.returncode == 2, f"rc={r.returncode}")

        # Los settings eligen la base por otra variable: aquí acabarían en «postgres» (la de desarrollo).
        r = e2e(E2E_DB_ENV="SOME_OTHER_VAR", POSTGRES_DB="postgres")
        tables = subprocess.run(["docker", "exec", NAME, "psql", "-U", "postgres", "-Atc",
                                 "SELECT count(*) FROM pg_tables WHERE tablename = 'django_migrations'"],
                                capture_output=True, text=True).stdout.strip()
        check("settings que no usan la base desechable → 2, sin migrar la otra", r.returncode == 2
              and tables == "0" and not db_exists("demo_e2e"), f"rc={r.returncode} · django_migrations={tables}")

        with socket.socket() as busy:
            busy.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)  # el puerto queda en TIME_WAIT
            busy.bind(("127.0.0.1", api_port))
            busy.listen()
            r = e2e()
        check("puerto ocupado → 2", r.returncode == 2 and not db_exists("demo_e2e"), f"rc={r.returncode}")

        r = e2e(E2E_KEEP_DB="1")
        check("E2E_KEEP_DB=1 conserva la base", r.returncode == 0 and db_exists("demo_e2e"), f"rc={r.returncode}")
        r = e2e(E2E_REUSE_DB="1")
        out = r.stdout + r.stderr
        check("E2E_REUSE_DB=1 la reutiliza sin sembrar y la borra al final",
              r.returncode == 0 and "REUSADA" in out and "seed_demo" not in out.split("REUSADA")[1]
              and not db_exists("demo_e2e"), f"rc={r.returncode}")

        sabotaged = os.path.join(tmp, "frontend/e2e/run-e2e-sin-borrado.mjs")
        with open(runner, encoding="utf-8") as f:
            src = f.read()
        with open(sabotaged, "w", encoding="utf-8") as f:
            f.write(src.replace("      dropDb();\n", "      // sabotaje: sin borrado\n"))
        r = e2e(script=sabotaged)
        check("sabotaje: sin el borrado, la base sigue viva y la prueba lo ve",
              r.returncode == 0 and db_exists("demo_e2e"), f"rc={r.returncode}")
    finally:
        subprocess.run(["docker", "rm", "-f", NAME], capture_output=True)
        shutil.rmtree(tmp, ignore_errors=True)
    print(f"\n{'OK' if not FAILURES else str(len(FAILURES)) + ' FALLO(S): ' + ', '.join(FAILURES)}")
    return 1 if FAILURES else 0


if __name__ == "__main__":
    sys.exit(main())
