#!/usr/bin/env python3
"""access_audit.py — el registro de accesos (AN-8) contra un PostgreSQL de verdad, desechable.

    python3 .claude/smoke/harvest/access_audit.py     # exit 1 si algo no da lo esperado

Levanta `postgres:17.11-alpine` (imagen local; sin puertos publicados, se habla por `docker exec`),
aplica `templates/access-audit/schema.sql` como `audit_owner` y comprueba:
  · la app inserta, y no puede ni UPDATE, ni DELETE, ni TRUNCATE — tampoco si le conceden UPDATE;
  · la cadena verifica en verde (control) y detecta una fila alterada por quien administra la base;
  · un administrador que recalcula la cadena entera pasa la cadena sola y lo caza el ancla;
  · sabotaje: sin el trigger de inmutabilidad, el UPDATE con permiso pasa (la prueba lo ve).
El contenedor se borra al terminar, pase lo que pase. `bash .claude/hooks/check-ram.sh` antes.
"""
from __future__ import annotations

import json
import os
import subprocess
import sys
import time

CL = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
TPL = os.path.join(CL, "templates", "access-audit")
sys.path.insert(0, TPL)
import chain  # noqa: E402

IMAGE = "postgres:17.11-alpine"
NAME = f"tl-smoke-access-audit-{os.getpid()}"
FAILURES: list[str] = []


def check(name: str, ok: bool, extra: str = "") -> None:
    print(f"  {'✓' if ok else '✗'} {name}{' · ' + extra if extra else ''}")
    if not ok:
        FAILURES.append(name)


def psql(sql: str, role: str | None = None) -> subprocess.CompletedProcess:
    prefix = f"SET ROLE {role};\n" if role else ""
    return subprocess.run(
        ["docker", "exec", "-i", NAME, "psql", "-U", "postgres", "-At", "-v", "ON_ERROR_STOP=1"],
        input=prefix + sql, capture_output=True, text=True, timeout=60)


def export() -> list[dict]:
    out = psql(chain.EXPORT_SQL + ";").stdout
    return [json.loads(line) for line in out.splitlines() if line.strip()]


def insert(actor: str, resource: str, action: str = "read") -> subprocess.CompletedProcess:
    ref = chain.pseudonym(b"clave-de-prueba", 8421)
    return psql(
        "INSERT INTO access_event (ts, actor_id, actor_role, subject_ref, resource, fields, action,"
        f" result, context) VALUES ('2001-01-01', '{actor}', 'enfermera', '{ref}', '{resource}',"
        f" 'analitica,diagnostico', '{action}', 'allowed', 'tenant:demo');", role="app_user")


def main() -> int:
    if subprocess.run(["docker", "image", "inspect", IMAGE], capture_output=True).returncode:
        print(f"sin datos: la imagen {IMAGE} no está en local (no se descarga nada)")
        return 2
    subprocess.run(["docker", "run", "-d", "--rm", "--name", NAME, "--memory", "256m",
                    "-e", "POSTGRES_PASSWORD=desechable", IMAGE], check=True, capture_output=True)
    try:
        for _ in range(60):
            if psql("SELECT 1;").returncode == 0:
                break
            time.sleep(1)
        print("AN-8 · registro de accesos (PostgreSQL desechable)")
        setup = psql("CREATE ROLE audit_owner; CREATE ROLE app_user; CREATE ROLE audit_purger;"
                     " GRANT CREATE ON SCHEMA public TO audit_owner;")
        check("roles creados", setup.returncode == 0, setup.stderr.strip())
        with open(os.path.join(TPL, "schema.sql"), encoding="utf-8") as f:
            r = psql(f.read(), role="audit_owner")
        check("schema.sql se aplica como audit_owner", r.returncode == 0, r.stderr.strip()[:200])

        oks = [insert(f"user:{i}", f"reconocimiento#{i}").returncode == 0 for i in range(1, 4)]
        # Un valor con el separador y con «ñ»: la forma canónica no se puede confundir.
        oks.append(insert("user:4", "historia|añadido:3").returncode == 0)
        check("la app inserta (4 filas)", all(oks))
        rows = export()
        check("el ts lo pone el servidor, no la app", rows and not rows[0]["ts"].startswith("2001"),
              rows[0]["ts"] if rows else "")
        upd = psql("UPDATE access_event SET actor_id = 'otro' WHERE seq = 2;", role="app_user")
        check("UPDATE como app → falla", upd.returncode != 0, upd.stderr.strip().splitlines()[-1:][0]
              if upd.stderr.strip() else "")
        check("DELETE como app → falla",
              psql("DELETE FROM access_event WHERE seq = 2;", role="app_user").returncode != 0)
        check("TRUNCATE como app → falla",
              psql("TRUNCATE access_event;", role="app_user").returncode != 0)
        psql("GRANT UPDATE ON access_event TO app_user;")
        upd2 = psql("UPDATE access_event SET actor_id = 'otro' WHERE seq = 2;", role="app_user")
        check("UPDATE con permiso concedido por error → lo para el trigger",
              upd2.returncode != 0 and "solo inserción" in upd2.stderr, upd2.stderr.strip()[-80:])

        rows = export()
        check("control: la cadena intacta verifica", chain.verify(rows) == [], f"{len(rows)} filas")
        anchors = chain.heads(rows)

        # Quien administra la base desactiva la barrera y cambia quién leyó.
        psql("ALTER TABLE access_event DISABLE TRIGGER access_event_no_update;"
             " UPDATE access_event SET actor_id = 'user:99' WHERE seq = 2;"
             " ALTER TABLE access_event ENABLE TRIGGER access_event_no_update;")
        problems = chain.verify(export())
        check("fila alterada → la cadena la detecta", any("#2" in p for p in problems), "; ".join(problems))

        # Y ahora recalcula la cadena entera desde la fila 2: la cadena sola ya no lo ve.
        rows = export()
        prev = chain.GENESIS
        fix = ["ALTER TABLE access_event DISABLE TRIGGER access_event_no_update;"]
        for r in sorted(rows, key=lambda x: int(x["seq"])):
            r["prev_hash"] = prev
            r["hash"] = chain.row_hash(prev, r)
            prev = r["hash"]
            fix.append(f"UPDATE access_event SET prev_hash = '{r['prev_hash']}', hash = '{r['hash']}'"
                       f" WHERE segment = '{r['segment']}' AND seq = {r['seq']};")
        fix.append("ALTER TABLE access_event ENABLE TRIGGER access_event_no_update;")
        psql("\n".join(fix))
        rows = export()
        check("cadena recalculada por el DBA → pasa la cadena sola (por eso hace falta el ancla)",
              chain.verify(rows) == [])
        problems = chain.verify(rows, anchors)
        check("… y la caza el ancla publicada fuera", bool(problems), "; ".join(problems))

        # Sabotaje del esquema: sin el trigger, un UPDATE con permiso pasa. La prueba distingue.
        psql("DROP TRIGGER access_event_no_update ON access_event;")
        sab = psql("UPDATE access_event SET reason = 'x' WHERE seq = 1;", role="app_user")
        check("sabotaje: sin el trigger de inmutabilidad, el UPDATE pasa (la prueba lo ve)",
              sab.returncode == 0)

        purge = psql("DELETE FROM access_event;", role="audit_purger")
        check("control: audit_purger borra segmentos enteros", purge.returncode == 0,
              purge.stderr.strip()[-80:])
    finally:
        subprocess.run(["docker", "rm", "-f", NAME], capture_output=True)
    print(f"\n{'OK' if not FAILURES else 'FALLA: ' + ', '.join(FAILURES)}")
    return 1 if FAILURES else 0


if __name__ == "__main__":
    sys.exit(main())
