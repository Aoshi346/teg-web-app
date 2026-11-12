#!/usr/bin/env python3
"""compose_wrapper.py — el envoltorio de compose (AN-15) contra fixtures, sin levantar nada.

    python3 .claude/smoke/harvest/compose_wrapper.py   # exit 1 si algo no da lo esperado

Solo usa `docker compose config` y `docker inspect` (lectura): no crea, para ni recrea contenedores.
Cada negativa lleva su control. El caso del contenedor ajeno usa uno VIVO de otro proyecto de esta
máquina (el primero con etiqueta de compose que encuentre) y comprueba que el guion se niega sin
tocarlo; sin ninguno, ese caso sale «sin datos», no verde.
"""
from __future__ import annotations

import atexit
import os
import shutil
import stat
import subprocess
import sys
import tempfile

CL = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
WRAPPER = os.path.join(CL, "templates", "compose-wrapper", "compose-wrapper.sh")
FAILURES: list[str] = []

COMPOSE = """services:
  db:
    image: postgres:17.11-alpine
    container_name: ${STACK_PREFIX:-prodapp}_db
    networks: [net]
    volumes: [pgdata:/var/lib/postgresql/data]
networks:
  net:
    name: ${STACK_PREFIX:-prodapp}_net
volumes:
  pgdata:
    name: ${STACK_PREFIX:-prodapp}_pgdata
"""

CONFIG = '''PROJECT="demo-stage"
ENV_FILE=".env"
FILES=(infra/docker-compose.yml)
PROFILES=()
MARKERS=({markers})
NAME_PREFIX="{prefix}"
EXTERNAL_NETWORKS=()
'''


def check(name: str, ok: bool, extra: str = "") -> None:
    print(f"  {'✓' if ok else '✗'} {name}{' · ' + extra if extra else ''}")
    if not ok:
        FAILURES.append(name)


def make(env: str, markers: str = '"APP_ENV=stage"', prefix: str = "demo_stage",
         compose: str = COMPOSE) -> str:
    d = tempfile.mkdtemp(prefix="cw-")
    atexit.register(shutil.rmtree, d, True)
    os.makedirs(os.path.join(d, "infra"))
    with open(os.path.join(d, "infra", "docker-compose.yml"), "w") as f:
        f.write(compose)
    with open(os.path.join(d, ".env"), "w") as f:
        f.write(env)
    src = open(WRAPPER, encoding="utf-8").read()
    start, end = src.index("# ── CONFIG"), src.index("# ── fin CONFIG")
    body = src[:start] + "# ── CONFIG\n" + CONFIG.format(markers=markers, prefix=prefix) + src[end:]
    path = os.path.join(d, "stage")
    with open(path, "w", encoding="utf-8") as f:
        f.write(body)
    os.chmod(path, os.stat(path).st_mode | stat.S_IXUSR)
    return path


def run(path: str, *args: str) -> subprocess.CompletedProcess:
    return subprocess.run([path, *args], capture_output=True, text=True, timeout=60)


def foreign_container() -> tuple[str, str] | None:
    out = subprocess.run(["docker", "ps", "--format",
                          '{{.Names}}\t{{.Label "com.docker.compose.project"}}'],
                         capture_output=True, text=True).stdout
    for line in out.splitlines():
        name, _, project = line.partition("\t")
        if project and project != "demo-stage":
            return name, project
    return None


def main() -> int:
    if shutil.which("docker") is None:
        print("sin datos: no hay docker")
        return 2
    print("AN-15 · envoltorio de docker compose")
    good = "APP_ENV=stage\nSTACK_PREFIX=demo_stage\n"
    r = run(make(good), "check")
    check("control: .env de stage con su prefijo → en orden", r.returncode == 0, r.stderr.strip())
    r = run(make(good), "config", "--services")
    check("control: la orden pasa a compose tras la guarda", r.returncode == 0 and "db" in r.stdout)

    r = run(make("APP_ENV=prod\nSTACK_PREFIX=demo_stage\n"), "up", "-d")
    check(".env sin el marcador del entorno → se niega", r.returncode == 1, r.stderr.strip())

    # La cicatriz: marcador bien, pero el .env no trae STACK_PREFIX → los nombres caen a los de prod.
    r = run(make("APP_ENV=stage\n"), "up", "-d")
    check("sin STACK_PREFIX los nombres caen al de producción → se niega",
          r.returncode == 1 and "prodapp_db" in r.stderr, r.stderr.strip().splitlines()[0]
          if r.stderr.strip() else "")
    check("… y nombra también la red y el volumen", "prodapp_net" in r.stderr and "prodapp_pgdata"
          in r.stderr)

    r = run(make(good), "-p", "otro", "up")
    check("opciones globales desde fuera (-p) → se niega", r.returncode == 1)

    fc = foreign_container()
    if fc is None:
        print("  · sin datos: no hay ningún contenedor de otro proyecto compose vivo para probarlo")
    else:
        name, project = fc
        compose = COMPOSE.replace("${STACK_PREFIX:-prodapp}_db", name)
        r = run(make(good, prefix="", compose=compose), "up", "-d")
        check(f"container_name de un contenedor vivo de «{project}» → se niega sin tocarlo",
              r.returncode == 1 and project in r.stderr, name)
        r = run(make(good), "net-connect", name, "bridge")
        check(f"net-connect de un contenedor de «{project}» a una red que existe → se niega",
              r.returncode == 1 and "es del proyecto" in r.stderr, r.stderr.strip())

    r = run(make(good), "net-connect", "x", "demo_stage_net_que_no_existe")
    check("net-connect a una red que no existe con ese nombre exacto → se niega", r.returncode == 1)
    print(f"\n{'OK' if not FAILURES else 'FALLA: ' + ', '.join(FAILURES)}")
    return 1 if FAILURES else 0


if __name__ == "__main__":
    sys.exit(main())
