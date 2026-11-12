#!/usr/bin/env python3
"""session_login.py — sesión Django sin contraseña para un usuario de PRUEBA, solo en desarrollo.

QUÉ ES (WA-4, sub-ola 4.16). Cada ticket de EvoPreven traía su `sesion.py`: una sesión creada a mano
e inyectada como cookie en Playwright, para no teclear contraseñas en los guiones. Aquí, una sola vez:
crea la sesión con el motor que use el proyecto (`db`, `cache`/Redis, `cached_db`, `signed_cookies`),
le pone caducidad (`set_expiry`: sin ella, 302 eterno en algunos backoffice) y saca la cookie en JSON.

SE NIEGA (exit 1, sin crear nada) si:
  · `settings.DEBUG` es False: esto es una puerta trasera y no existe fuera de desarrollo;
  · alguna BBDD o la caché de sesiones no es local, o la BBDD está en `--forbidden-db`
    (`scripts/db_guard.py`, el mismo guard que las fotos de Pilar);
  · el usuario no existe o no está activo (no se crea ninguno: los de prueba los siembra el proyecto).

USO (con el python del proyecto, desde la carpeta de `manage.py`):
    python <kit>/session_login.py --settings config.settings.local --username prueba_tecnico
    → {"name": "sessionid", "value": "…", "domain": "127.0.0.1", "path": "/", "expires": 1730…}

Salida: 0 cookie impresa · 1 se niega (DEBUG, BBDD, usuario) · 2 no se pudo (sin Django, settings
ilegibles). Lo llama `verify_ticket.py`; también vale suelto para un guion propio.
"""
from __future__ import annotations

import argparse
import importlib
import json
import os
import pathlib
import sys
import time

KIT = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(KIT.parent.parent / "scripts"))
import db_guard  # noqa: E402 — el mismo guard que las fotos de Pilar


class Refused(RuntimeError):
    """Un guard impide crear la sesión: exit 1."""


def make_cookie(username: str, ttl: int = 3600, forbidden: list[str] | None = None,
                domain: str = "127.0.0.1") -> dict:
    """Con Django ya configurado: la cookie de sesión de `username`. Lanza Refused si no procede."""
    from django.conf import settings
    from django.contrib.auth import (BACKEND_SESSION_KEY, HASH_SESSION_KEY, SESSION_KEY,
                                     get_user_model)

    if not settings.DEBUG:
        raise Refused("DEBUG=False: el login sin contraseña solo existe en desarrollo")
    problems = (db_guard.check_databases(settings.DATABASES, forbidden or [])
                + db_guard.check_session_store(settings.SESSION_ENGINE, settings.CACHES,
                                               getattr(settings, "SESSION_CACHE_ALIAS", "default")))
    if problems:
        raise Refused("; ".join(problems))
    model = get_user_model()
    try:
        user = model._default_manager.get(**{model.USERNAME_FIELD: username})
    except model.DoesNotExist as exc:
        raise Refused(f"no existe el usuario de prueba '{username}' (siémbralo en el proyecto)") from exc
    if not getattr(user, "is_active", True):
        raise Refused(f"el usuario '{username}' no está activo")

    engine = importlib.import_module(settings.SESSION_ENGINE)
    session = engine.SessionStore()
    session[SESSION_KEY] = user._meta.pk.value_to_string(user)
    session[BACKEND_SESSION_KEY] = settings.AUTHENTICATION_BACKENDS[0]
    session[HASH_SESSION_KEY] = user.get_session_auth_hash()
    session.set_expiry(ttl)
    session.save()
    return {"name": settings.SESSION_COOKIE_NAME, "value": session.session_key, "domain": domain,
            "path": settings.SESSION_COOKIE_PATH or "/", "expires": int(time.time()) + ttl,
            "httpOnly": True, "secure": False, "sameSite": "Lax"}


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--settings", required=True, help="módulo de settings de DESARROLLO")
    ap.add_argument("--username", required=True)
    ap.add_argument("--ttl", type=int, default=3600, help="segundos de vida de la sesión")
    ap.add_argument("--domain", default="127.0.0.1")
    ap.add_argument("--forbidden-db", nargs="*", default=[], help="host o nombre de BBDD prohibidos")
    a = ap.parse_args(argv)

    os.environ["DJANGO_SETTINGS_MODULE"] = a.settings
    sys.path.insert(0, os.getcwd())
    try:
        import django
        django.setup()
    except Exception as exc:  # noqa: BLE001 — cualquier fallo de settings es «no se pudo»
        print(f"[session_login] no se pudo cargar Django con {a.settings}: {exc}", file=sys.stderr)
        return 2
    try:
        cookie = make_cookie(a.username, a.ttl, a.forbidden_db, a.domain)
    except Refused as exc:
        print(f"[session_login] me niego: {exc}", file=sys.stderr)
        return 1
    print(json.dumps(cookie))
    return 0


if __name__ == "__main__":
    sys.exit(main())
