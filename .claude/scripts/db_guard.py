#!/usr/bin/env python3
"""db_guard.py — ¿apunta este Django solo a cosas locales? El guard común de lo que toca la BBDD en dev.

Lo usan las fotos de Pilar (`templates/impacto/foto_django.py`, que no debe medir otra cosa que una
copia local) y el login sin contraseña de `skills/verify-ticket/session_login.py` (que no debe crear
una sesión fuera de desarrollo). Un solo criterio para los dos:

  · cada BBDD es SQLite (`django.db.backends.sqlite3`, motor exacto) o tiene HOST local
    (`""`, `localhost`, `127.0.0.1`, `::1` o un socket unix que empieza por `/`);
  · con HOST vacío, el destino no se esconde en `OPTIONS` (`host`, `hostaddr`, `service`, `passfile`)
    ni en un `NAME` con forma de cadena de conexión (`://` o `=`);
  · ninguna está en la lista prohibida (host o nombre);
  · si las sesiones van a caché (`cache`, `cached_db`), esa caché también es local.

Solo lee settings: no conecta con nada. `--self-test` lo ve fallar con cada salto conocido.
"""
from __future__ import annotations

import sys
from urllib.parse import urlparse

LOCAL_HOSTS = {"", "localhost", "127.0.0.1", "::1"}
SQLITE = "django.db.backends.sqlite3"
REMOTE_OPTIONS = ("host", "hostaddr", "service", "passfile")
LOCAL_CACHE_BACKENDS = ("locmem.LocMemCache", "dummy.DummyCache", "filebased.FileBasedCache")


def _local_host(host: str) -> bool:
    return host.startswith("/") or host.lower() in LOCAL_HOSTS


def check_databases(databases: dict, forbidden: list[str] | None = None) -> list[str]:
    """Una línea por cada BBDD que no es local o está prohibida; lista vacía si todas valen."""
    problems = []
    for alias, cfg in databases.items():
        engine = str(cfg.get("ENGINE") or "")
        host = str(cfg.get("HOST") or "")
        name = str(cfg.get("NAME") or "")
        if engine != SQLITE:
            if not _local_host(host):
                problems.append(f"BBDD '{alias}' apunta a '{host}', que no es local")
            opts = cfg.get("OPTIONS") or {}
            for key in REMOTE_OPTIONS:
                value = str(opts.get(key) or "")
                if value and not (key == "host" and _local_host(value)):
                    problems.append(f"BBDD '{alias}': OPTIONS['{key}'] puede llevar a otra máquina")
            if "://" in name or "=" in name:
                problems.append(f"BBDD '{alias}': NAME parece una cadena de conexión")
        for f in forbidden or []:
            if f and f in (host, name):
                problems.append(f"BBDD '{alias}' ({name}@{host or 'local'}) está en la lista prohibida")
    return problems


def cache_is_local(cfg: dict) -> bool:
    if str(cfg.get("BACKEND") or "").endswith(LOCAL_CACHE_BACKENDS):
        return True
    locs = cfg.get("LOCATION") or ""
    for loc in locs if isinstance(locs, (list, tuple)) else [locs]:
        loc = str(loc)
        if loc.startswith(("unix:", "/")):
            continue
        host = urlparse(loc if "://" in loc else f"//{loc}").hostname or ""
        if host.lower() not in LOCAL_HOSTS - {""}:
            return False
    return True


def check_session_store(session_engine: str, caches: dict, alias: str = "default") -> list[str]:
    """La sesión se escribe donde diga SESSION_ENGINE: con caché, esa caché también es local."""
    if "cache" not in session_engine:
        return []
    return [] if cache_is_local(caches.get(alias) or {}) else [f"la caché de sesiones '{alias}' no es local"]


def self_test() -> int:
    fails = []

    def expect(name, problems, bad):
        ok = bool(problems) == bad
        print(f"  {'✓' if ok else '✗'} {name}")
        if not ok:
            fails.append(name)

    pg = "django.db.backends.postgresql"
    expect("sqlite → vale", check_databases({"d": {"ENGINE": SQLITE, "NAME": "/tmp/x.db"}}), False)
    expect("postgres en 127.0.0.1 → vale", check_databases({"d": {"ENGINE": pg, "HOST": "127.0.0.1"}}), False)
    expect("socket unix → vale", check_databases({"d": {"ENGINE": pg, "HOST": "/var/run/postgresql"}}), False)
    expect("HOST remoto → no", check_databases({"d": {"ENGINE": pg, "HOST": "db.prod.example"}}), True)
    expect("alias secundario remoto → no", check_databases({
        "d": {"ENGINE": SQLITE}, "r": {"ENGINE": pg, "HOST": "db.prod.example"}}), True)
    expect("HOST vacío + OPTIONS service → no", check_databases({
        "d": {"ENGINE": pg, "HOST": "", "OPTIONS": {"service": "prod"}}}), True)
    expect("HOST vacío + OPTIONS host remoto → no", check_databases({
        "d": {"ENGINE": pg, "OPTIONS": {"host": "db.prod.example"}}}), True)
    expect("NAME con URI → no", check_databases({
        "d": {"ENGINE": pg, "NAME": "postgresql://u@db.prod.example/app"}}), True)
    expect("ENGINE que solo se parece a sqlite → no", check_databases({
        "d": {"ENGINE": "myproj.sqlite_remote_proxy", "HOST": "db.prod.example"}}), True)
    expect("nombre prohibido → no", check_databases({"d": {"ENGINE": SQLITE, "NAME": "app_prod"}},
                                                     ["app_prod"]), True)
    redis = "django.core.cache.backends.redis.RedisCache"
    expect("sesión en db → no mira cachés", check_session_store(
        "django.contrib.sessions.backends.db", {"default": {"BACKEND": redis, "LOCATION": "redis://x.example"}}), False)
    expect("sesión en Redis local → vale", check_session_store(
        "django.contrib.sessions.backends.cache", {"default": {"BACKEND": redis, "LOCATION": "redis://127.0.0.1:6379/1"}}), False)
    expect("sesión en Redis remoto → no", check_session_store(
        "django.contrib.sessions.backends.cached_db",
        {"default": {"BACKEND": redis, "LOCATION": ["redis://127.0.0.1:6379", "redis://cache.prod.example:6379"]}}), True)
    print(f"self-test db_guard: {'OK' if not fails else f'{len(fails)} fallos'}")
    return 1 if fails else 0


if __name__ == "__main__":
    if "--self-test" in sys.argv:
        sys.exit(self_test())
    print(__doc__)
