#!/usr/bin/env python3
"""django_audit_trail.py — el paquete `webapps/django-audit-trail` contra un PostgreSQL desechable (4.13).

    python3 .claude/smoke/harvest/django_audit_trail.py --python <python con django y psycopg2>

Levanta `postgres:17.11-alpine` (imagen local, solo en 127.0.0.1), migra el Django de fixture del
paquete como `audit_owner` y lo hace funcionar como `app_user`, y comprueba:
  · migrar con el rol de la app → la migración se niega (la barrera 1 no existiría);
  · lecturas y escrituras reales por HTTP de test dejan filas, sin nombre ni diagnóstico en el registro;
  · desde la conexión de Django, UPDATE y DELETE sobre access_event fallan (rol + trigger);
  · `check --database default` sin E003 como app_user, y con E003 si Django se conecta como dueño;
  · `audit_trail_verify` en verde; fila alterada por el DBA → 1; cadena recalculada → pasa sola y
    con `--anchors` → 1;
  · el coste por guardado, medido (N=300) frente a un INSERT de un modelo normal.
Exit 0 todo bien · 1 algo no dio lo esperado · 2 sin datos (sin imagen, sin docker o sin --python).
El contenedor se borra al terminar, pase lo que pase. `bash .claude/hooks/check-ram.sh` antes.
"""
from __future__ import annotations

import json
import os
import subprocess
import sys
import time
from pathlib import Path

CL = Path(__file__).resolve().parents[2]
PKG = CL.parent / "webapps" / "django-audit-trail"
sys.path.insert(0, str(PKG / "audit_trail"))
import chain  # noqa: E402

IMAGE = "postgres:17.11-alpine"
NAME = f"tl-smoke-dat-{os.getpid()}"
PASSWORD = "desechable"
FAILURES: list[str] = []
SECRETS = ("María", "Pérez", "diabetes", "retinopatía")

# Lo que corre DENTRO de Django (como app_user), con la salida en JSON por stdout.
INSIDE = r'''
import json, time, io
import django
django.setup()
from django.test import Client
from django.contrib.auth.models import User, Group
from django.core.management import call_command
from django.core.management.base import CommandError
from django.db import connection, transaction
from audit_trail import services
from example.clinic.models import Patient
out = {}
u = User.objects.create_user("enfermera1", password="x", is_staff=True)
u.groups.add(Group.objects.create(name="enfermeria"))
p = Patient.objects.create(full_name="María Pérez Lozano", diagnosis="diabetes tipo 2 con retinopatía")
c = Client(); c.force_login(u)
out["get_diag"] = c.get(f"/patients/{p.pk}/diagnosis/").status_code
out["get_detail"] = c.get(f"/patients/{p.pk}/").status_code
p.diagnosis = "otro"; p.save(update_fields=["diagnosis"])
for sql in ("UPDATE access_event SET actor_id = 'x'", "DELETE FROM access_event"):
    try:
        with transaction.atomic(), connection.cursor() as cur:
            cur.execute(sql)
        out[sql.split()[0]] = "pasó"
    except Exception as e:
        out[sql.split()[0]] = type(e).__name__ + ": " + str(e).splitlines()[0][:90]
from audit_trail.checks import check_database_role
out["db_check"] = [e.id for e in check_database_role(None, databases=["default"])]
N = 300
t = time.perf_counter()
for i in range(N):
    services.record_access(user=u, subject_id=p.pk, resource=f"clinic.Patient#{p.pk}",
                           fields=["diagnosis"], action="read")
out["ms_record"] = round((time.perf_counter() - t) * 1000 / N, 3)
from audit_trail import writes
writes.unregister(Patient)
t = time.perf_counter()
for i in range(N):
    Patient.objects.create(full_name="x", diagnosis="y")
out["ms_plain"] = round((time.perf_counter() - t) * 1000 / N, 3)
try:
    call_command("audit_trail_verify", stdout=io.StringIO()); out["verify"] = 0
except CommandError:
    out["verify"] = 1
buf = io.StringIO(); call_command("audit_trail_heads", stdout=buf); out["heads"] = json.loads(buf.getvalue())
out["patient_pk"] = p.pk
print("JSON:" + json.dumps(out, ensure_ascii=False))
'''

VERIFY = r'''
import django, io, sys
django.setup()
from django.core.management import call_command
from django.core.management.base import CommandError
args = sys.argv[1:]
try:
    call_command("audit_trail_verify", *args, stdout=io.StringIO(), stderr=io.StringIO()); print("RC:0")
except CommandError:
    print("RC:1")
'''


def check(name: str, ok: bool, extra: str = "") -> None:
    print(f"  {'✓' if ok else '✗'} {name}{' · ' + extra if extra else ''}")
    if not ok:
        FAILURES.append(name)


def psql(sql: str, db: str = "postgres") -> subprocess.CompletedProcess:
    return subprocess.run(["docker", "exec", "-i", NAME, "psql", "-U", "postgres", "-d", db, "-At",
                           "-v", "ON_ERROR_STOP=1"], input=sql, capture_output=True, text=True,
                          timeout=60)


def django_run(py: str, port: str, user: str, code: str, *args: str, db: str = "postgres",
               owner: bool = False) -> subprocess.CompletedProcess:
    env = {"PATH": "/usr/bin:/bin", "PYTHONDONTWRITEBYTECODE": "1", "PYTHONPATH": str(PKG),
           "DJANGO_SETTINGS_MODULE": "example.settings", "DAT_PG_HOST": "127.0.0.1",
           "DAT_PG_PORT": port, "DAT_PG_PASSWORD": PASSWORD, "DAT_PG_NAME": db,
           "DAT_PG_USER": user}
    if owner:
        env["DAT_PG_OWNER"] = user
    return subprocess.run([py, "-c", code, *args], cwd=PKG, env=env, capture_output=True,
                          text=True, timeout=300)


def migrate(py: str, port: str, user: str, db: str = "postgres") -> subprocess.CompletedProcess:
    code = "import django,sys;django.setup();from django.core.management import call_command;" \
           "call_command('migrate', verbosity=0)"
    return django_run(py, port, user, code, db=db, owner=True)


def export() -> list[dict]:
    out = psql(chain.EXPORT_SQL + ";").stdout
    return [json.loads(line) for line in out.splitlines() if line.strip()]


def main() -> int:
    if "--python" not in sys.argv:
        print("sin datos: falta --python <python con django y psycopg2> (ver la cabecera)")
        return 2
    py = sys.argv[sys.argv.index("--python") + 1]
    if subprocess.run([py, "-c", "import django, psycopg2"], capture_output=True).returncode:
        print(f"sin datos: {py} no tiene django y psycopg2")
        return 2
    if subprocess.run(["docker", "image", "inspect", IMAGE], capture_output=True).returncode:
        print(f"sin datos: la imagen {IMAGE} no está en local (no se descarga nada)")
        return 2
    subprocess.run(["docker", "run", "-d", "--rm", "--name", NAME, "--memory", "256m",
                    "-e", f"POSTGRES_PASSWORD={PASSWORD}", "-p", "127.0.0.1::5432", IMAGE],
                   check=True, capture_output=True)
    try:
        port = subprocess.run(["docker", "port", NAME, "5432/tcp"], capture_output=True,
                              text=True).stdout.split(":")[-1].strip()
        for _ in range(60):
            if psql("SELECT 1;").returncode == 0:
                break
            time.sleep(1)
        print(f"4.13 · django-audit-trail contra PostgreSQL desechable (127.0.0.1:{port})")
        r = psql(f"CREATE ROLE audit_owner LOGIN PASSWORD '{PASSWORD}';"
                 f" CREATE ROLE app_user LOGIN PASSWORD '{PASSWORD}'; CREATE ROLE audit_purger;"
                 " GRANT CREATE, USAGE ON SCHEMA public TO audit_owner;"
                 " GRANT USAGE ON SCHEMA public TO app_user;"
                 " CREATE DATABASE wrongowner OWNER app_user;")
        check("roles creados", r.returncode == 0, r.stderr.strip()[:120])

        bad = migrate(py, port, "app_user", db="wrongowner")
        check("migrar con el rol de la app → la migración se niega", bad.returncode != 0
              and "rol dueño" in bad.stderr, bad.stderr.strip().splitlines()[-1][:120]
              if bad.stderr.strip() else "")

        mig = migrate(py, port, "audit_owner")
        check("migrate como audit_owner", mig.returncode == 0, mig.stderr.strip()[-200:])
        # Lo que hace quien administra la base después de migrar: la app usa el resto de tablas.
        g = psql("SET ROLE audit_owner;"
                 " GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA public TO app_user;"
                 " GRANT USAGE ON ALL SEQUENCES IN SCHEMA public TO app_user;"
                 " REVOKE UPDATE, DELETE, TRUNCATE ON access_event FROM app_user;")
        check("permisos de la app sobre sus tablas", g.returncode == 0, g.stderr.strip()[:120])

        run = django_run(py, port, "app_user", INSIDE)
        line = next((ln for ln in run.stdout.splitlines() if ln.startswith("JSON:")), None)
        check("el escenario corre como app_user", line is not None, run.stderr.strip()[-300:])
        if line is None:
            return 1
        res = json.loads(line[5:])
        check("lecturas por decorador y mixin → 200", res["get_diag"] == res["get_detail"] == 200)
        check("UPDATE desde la conexión de Django → falla", res["UPDATE"] != "pasó", res["UPDATE"])
        check("DELETE desde la conexión de Django → falla", res["DELETE"] != "pasó", res["DELETE"])
        check("check --database como app_user: sin E003 ni W003", res["db_check"] == [],
              str(res["db_check"]))
        check("audit_trail_verify en verde (control)", res["verify"] == 0)

        # El trigger, aparte del permiso: con UPDATE concedido por error, lo tiene que parar él.
        psql("SET ROLE audit_owner; GRANT UPDATE, DELETE ON access_event TO app_user;")
        trig = django_run(py, port, "app_user",
                          "import django;django.setup();from django.db import connection\n"
                          "for sql in ('UPDATE access_event SET actor_id = %s', 'DELETE FROM access_event'):\n"
                          "    try:\n"
                          "        with connection.cursor() as c: c.execute(sql, ['x'] if '%s' in sql else None)\n"
                          "        print('PASO')\n"
                          "    except Exception as e: print('PARADO', 'solo inserción' in str(e))\n")
        psql("SET ROLE audit_owner; REVOKE UPDATE, DELETE ON access_event FROM app_user;")
        check("con UPDATE/DELETE concedidos por error → los para el trigger",
              trig.stdout.split().count("True") == 2, trig.stdout.strip().replace("\n", " · "))

        owner_check = django_run(py, port, "audit_owner",
                                 "import django;django.setup();from audit_trail.checks import "
                                 "check_database_role as c;print([e.id for e in c(None,"
                                 " databases=['default'])])", owner=True)
        check("check --database conectado como dueño → E003", "audit_trail.E003" in owner_check.stdout,
              owner_check.stdout.strip())

        dump = psql("SELECT t::text FROM access_event t;").stdout
        leaked = [s for s in SECRETS if s in dump]
        rows = export()
        check("ni nombre ni diagnóstico en el registro", not leaked and len(rows) > 300,
              f"{len(rows)} filas; filtrado: {leaked}")
        acts = {r["action"] for r in rows}
        check("lecturas y escrituras registradas", {"read", "create", "update"} <= acts, str(sorted(acts)))
        check("coste por guardado medido", res["ms_record"] > 0,
              f"record_access {res['ms_record']} ms/fila frente a INSERT normal {res['ms_plain']} ms"
              f" (N=300, PostgreSQL 17 local en docker, sin carga)")

        anchors_file = PKG.parent.parent / ".claude" / "smoke" / "harvest" / f".anclas-{NAME}.json"
        anchors_file.write_text(json.dumps(res["heads"]))
        try:
            psql("ALTER TABLE access_event DISABLE TRIGGER access_event_no_update;"
                 " UPDATE access_event SET actor_id = 'user:999' WHERE seq = 2;"
                 " ALTER TABLE access_event ENABLE TRIGGER access_event_no_update;")
            v = django_run(py, port, "app_user", VERIFY)
            check("el DBA cambia quién leyó → audit_trail_verify sale con 1", "RC:1" in v.stdout,
                  v.stdout.strip() or v.stderr.strip()[-120:])
            rows = export()
            fix = ["ALTER TABLE access_event DISABLE TRIGGER access_event_no_update;"]
            prev, seg = chain.GENESIS, None
            for r in sorted(rows, key=lambda x: (x["segment"], int(x["seq"]))):
                if r["segment"] != seg:
                    prev, seg = chain.GENESIS, r["segment"]
                r["prev_hash"], r["hash"] = prev, chain.row_hash(prev, r)
                prev = r["hash"]
                fix.append(f"UPDATE access_event SET prev_hash = '{r['prev_hash']}', hash = "
                           f"'{r['hash']}' WHERE segment = '{r['segment']}' AND seq = {r['seq']};")
            fix.append("ALTER TABLE access_event ENABLE TRIGGER access_event_no_update;")
            psql("\n".join(fix))
            v = django_run(py, port, "app_user", VERIFY)
            check("cadena recalculada → pasa sola (por eso el ancla)", "RC:0" in v.stdout,
                  v.stdout.strip())
            v = django_run(py, port, "app_user", VERIFY, f"--anchors={anchors_file}")
            check("… y con --anchors sale con 1", "RC:1" in v.stdout, v.stdout.strip())
        finally:
            anchors_file.unlink(missing_ok=True)
    finally:
        subprocess.run(["docker", "rm", "-f", NAME], capture_output=True)
    print(f"\n{'OK' if not FAILURES else 'FALLA: ' + ', '.join(FAILURES)}")
    return 1 if FAILURES else 0


if __name__ == "__main__":
    sys.exit(main())
