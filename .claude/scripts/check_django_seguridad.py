#!/usr/bin/env python3
"""check_django_seguridad.py — G3: la configuración de seguridad de un Django, antes de un release.

Es el gate G3 de `r3-ciberseguridad-harness` §6 (item SE-48 de la revisión integral). Hasta hoy
ningún gate corría el check de despliegue de Django ni miraba la CSP, y las dos cosas que más se
abren sin querer en DRF —el permiso por defecto y la vista pública sin límite de peticiones— solo
las veía `pattern_check_backend.py` (`be-view-permisos-por-defecto`), que mira el texto.

QUÉ COMPRUEBA (con los settings de PRODUCCIÓN, que se le pasan con --settings)

  1. `manage.py check --deploy --fail-level WARNING`, lanzado por este script. Cada aviso es un
     hallazgo `G3-CHECK-<id>` (`security.W018` es DEBUG=True; `W004`, sin HSTS; `W012`/`W016`, las
     cookies de sesión y CSRF sin Secure; `W009`, una SECRET_KEY débil; `W025`, una de
     SECRET_KEY_FALLBACKS débil). También los de las apps (`axes.W002`: axes sin su middleware).
  2. Los avisos de seguridad SILENCIADOS en `SILENCED_SYSTEM_CHECKS` (`G3-CHECK-SILENCIADO`): un
     `security.W018` silenciado no sale en el check, y sin esto el gate diría verde con DEBUG=True.
  3. La CSP (`G3-CSP-*`): en Django >= 6.0, `SECURE_CSP` con `ContentSecurityPolicyMiddleware`; en
     5.2 LTS (el stack de casa), django-csp (`CONTENT_SECURITY_POLICY` y `csp.middleware.CSPMiddleware`;
     se acepta también el formato 3.x `CSP_*`). Falla si no hay política, si la hay sin su
     middleware (no se envía), si solo está en modo informe (no bloquea nada) o si no tiene
     `default-src`. `'unsafe-inline'`/`'unsafe-eval'`/`*` en script-src o default-src es un AVISO.
     El check de Django no lo mira: en 6.0 solo valida que `SECURE_CSP` sea un dict.
  4. DRF, si está instalado: `DEFAULT_PERMISSION_CLASSES` existe y no es AllowAny
     (`G3-DRF-PERMISO-ABIERTO`; el valor por defecto de DRF es AllowAny), y cada vista que declara
     `AllowAny` —clase, vista de función con `@permission_classes` o `@action`— lleva su límite de
     peticiones: `throttle_scope` con `ScopedRateThrottle` activo y su tasa en
     `DEFAULT_THROTTLE_RATES`, o `throttle_classes` propio (`G3-ALLOWANY-SIN-THROTTLE`). Un
     `throttle_scope` sin `ScopedRateThrottle` o sin tasa no limita nada: `G3-THROTTLE-DECORATIVO`.
     El throttle global no cuenta: es la misma tasa para el login que para el resto de la API.
  5. Límite de intentos de login (`G3-SIN-LIMITE-INTENTOS`): django-axes, django-defender o
     allauth con sus límites puestos. Que axes esté a medias lo dice su propio check (punto 1).
  6. Segundo factor si el admin está instalado (`G3-SIN-2FA`): django-otp, django-two-factor-auth
     o allauth.mfa en INSTALLED_APPS.

QUÉ NO COMPRUEBA, dicho para que nadie lo dé por cubierto: lo que pone el proxy inverso o un
middleware propio (una CSP o un HSTS de nginx, o de una clase que no es la de Django ni la de
django-csp, se declaran como excepción con su razón, o se miran con `curl -I`); que el admin
EXIJA el segundo factor (`OTPAdminSite`), solo que hay una app que lo da; los permisos que se
deciden en `get_permissions()`/`get_throttles()` en tiempo de ejecución; un `permission_classes`
con AllowAny HEREDADO (se mira en la clase que lo declara; el throttle sí se busca en sus bases del
propio proyecto, por nombre); que la tasa sea la adecuada, solo que existe; y los permisos a nivel
de objeto (`patterns/stack/backend-vistas.md` §1.2). Los settings son los que se le dan: con los de
desarrollo mide desarrollo, y por eso los imprime en la cabecera.

POR QUÉ LO LANZA UN SCRIPT. Hasta la sub-ola 2.02 (MO-8, 2026-10-21) era porque el `deny`
`Bash(*deploy*)` de `settings.json` bloqueaba teclear `manage.py check --deploy`. Ese deny ya está
estrechado a despliegues reales y el chequeo se puede teclear a mano (medido con `claude -p`,
`_archive/2026-10-20/medicion-2.02/`); **el script lo sigue lanzando él** por otras razones, que
no han cambiado: necesita el python del proyecto y las variables de su `--env-file` (sin imprimir
sus valores), los mismos settings que el resto de comprobaciones, y convertir cada aviso en un
hallazgo `G3-CHECK-<id>` junto a los silenciados y la CSP. Desde el 22-10 (decisión MO8-PRODUCTION)
el `deny` `Bash(*production*)` también está estrechado a patrones concretos (migrate/flush/loaddata con
settings de production, compose, ssh, kubectl… contra production), así que `--settings config.settings.production`
ya se puede teclear con este script o con `check --deploy` (medido con `claude -p` en un juguete).

USO
    python3 .claude/scripts/check_django_seguridad.py <proyecto> --settings config.settings.production
    python3 .claude/scripts/check_django_seguridad.py <proyecto> --python .venv/bin/python --env-file ci.env
    python3 .claude/scripts/check_django_seguridad.py <proyecto> --json
    python3 .claude/scripts/check_django_seguridad.py --autoprueba --python <venv con django>/bin/python

`--env-file` carga variables `CLAVE=valor` para el subproceso (las que pidan los settings de
producción); sus valores no se imprimen nunca. El python es, por orden: `--python`, el del
manifiesto, `$G3_PYTHON`, el `.venv`/`venv` del proyecto, y este mismo.

MANIFIESTO (`--manifiesto`, por defecto `<proyecto>/.claude/gate-django.json` si existe):

    {"settings": "config.settings.production", "manage": "backend/manage.py",
     "excepciones": {
        "G3-CHECK-security.W008": "la redirección a HTTPS la hace nginx (deploy/nginx.conf:12)",
        "G3-ALLOWANY-SIN-THROTTLE@apps/salud/views.py::Salud": "sonda del balanceador, sin datos"}}

Una excepción es `<id>` o `<id>@<lugar>` con una razón de 15 caracteres o más. La que ya no cubre
ningún hallazgo es un fallo (`G3-EXCEPCION-CADUCADA`): no crecen solas.

SALIDA: 0 todo medido y bien · 1 hay hallazgos · 2 NO SE PUDO MEDIR (sin manage.py, sin settings,
python sin Django, settings que no importan, o el check que se rompe sin decir por qué). El 2 es
deliberado (`rules/verification.md` §El instrumento que no puede medir debe ABORTAR).

`--autoprueba` es el control negativo del propio gate: monta un Django de juguete en una carpeta
temporal, lo mide limpio (tiene que salir 0), con cada sabotaje plantado (cada uno tiene que caer
por SU hallazgo, ni uno más), con los controles que NO deben salir rojos y con los casos que tienen
que salir NO MEDIDO. Necesita en el python dado Django, djangorestframework, django-axes, django-otp
y, en Django < 6.0, django-csp >= 4.
"""
from __future__ import annotations

import argparse
import ast
import json
import os
import re
import secrets
import shutil
import stat
import subprocess
import sys
import tempfile
from dataclasses import asdict, dataclass, field
from pathlib import Path

EXIT_OK, EXIT_FALLO, EXIT_NO_MEDIDO = 0, 1, 2
MANIFIESTO_POR_DEFECTO = Path(".claude") / "gate-django.json"
RAZON_MINIMA = 15          # caracteres: «legacy» no es una razón
MARCA = "@@G3@@"
TIEMPO = 180               # segundos por subproceso
# Lo que no es código de la app. `tests` y `test` van aparte (ver _es_test).
PODA = {".git", ".venv", "venv", "env", "node_modules", "site-packages", "__pycache__",
        "migrations", ".claude", ".docs", "dist", "build", ".tox", ".mypy_cache",
        ".pytest_cache", "static", "staticfiles", "media"}
SILENCIABLES_NO = ("security.", "axes.")       # silenciar estos es apagar el gate
APPS_LIMITE = ("axes", "defender")
APPS_2FA = ("django_otp", "two_factor", "allauth.mfa", "mfa", "trench")
MW_CSP_NATIVO = "ContentSecurityPolicyMiddleware"
MW_CSP_DJANGO_CSP = "CSPMiddleware"


class NoMedible(Exception):
    """El gate no puede llegar al sujeto. Sale con 2, nunca con 0."""


@dataclass
class Hallazgo:
    id: str
    lugar: str
    que: str
    arreglo: str
    exento: str = ""


@dataclass
class Resultado:
    proyecto: str
    settings: str = ""
    python: str = ""
    django: str = ""
    manage: str = ""
    hallazgos: list = field(default_factory=list)
    avisos: list = field(default_factory=list)
    medido: list = field(default_factory=list)

    def falla(self, id_: str, lugar: str, que: str, arreglo: str) -> None:
        self.hallazgos.append(Hallazgo(id_, lugar, que, arreglo))

    def rojos(self) -> list:
        return [h for h in self.hallazgos if not h.exento]

    def ids(self) -> set:
        return {h.id for h in self.rojos()}


# ── localizar el sujeto ──────────────────────────────────────────────────────────────────


def _podado(p: Path, raiz: Path) -> bool:
    return any(parte in PODA for parte in p.relative_to(raiz).parts[:-1])


def buscar_manage(raiz: Path, declarado: str | None) -> Path:
    if declarado:
        m = (raiz / declarado).resolve()
        if not m.is_file():
            raise NoMedible(f"el manage.py declarado no existe: {declarado}")
        return m
    for cand in (raiz / "manage.py", raiz / "backend" / "manage.py"):
        if cand.is_file():
            return cand.resolve()
    hallados = [p for p in raiz.glob("**/manage.py")
                if len(p.relative_to(raiz).parts) <= 4 and not _podado(p, raiz)]
    if not hallados:
        raise NoMedible(f"no hay manage.py en {raiz} (ni a 3 niveles): ¿es un proyecto Django? "
                        "Si lo es, dilo con --manage <ruta>")
    if len(hallados) > 1:
        rels = ", ".join(str(p.relative_to(raiz)) for p in sorted(hallados))
        raise NoMedible(f"hay varios manage.py ({rels}): elige uno con --manage")
    return hallados[0].resolve()


def modulo_de_settings(manage: Path, declarado: str | None) -> str:
    if declarado:
        return declarado
    if os.environ.get("DJANGO_SETTINGS_MODULE"):
        return os.environ["DJANGO_SETTINGS_MODULE"]
    m = re.search(r"""DJANGO_SETTINGS_MODULE['"]\s*,\s*['"]([\w.]+)['"]""",
                  manage.read_text(encoding="utf-8", errors="replace"))
    if not m:
        raise NoMedible("no sé qué settings medir: pásalos con --settings (los de PRODUCCIÓN)")
    return m.group(1)


def elegir_python(raiz: Path, manage: Path, declarado: str | None) -> str:
    if declarado:
        return declarado
    if os.environ.get("G3_PYTHON"):
        return os.environ["G3_PYTHON"]
    for base in dict.fromkeys((raiz, manage.parent)):
        for venv in (".venv", "venv"):
            cand = base / venv / "bin" / "python"
            if cand.exists():
                return str(cand)
    return sys.executable


def leer_env(fichero: str | None) -> dict:
    """`CLAVE=valor` por línea; `#` comenta. Los valores no salen nunca por pantalla."""
    if not fichero:
        return {}
    p = Path(fichero)
    if not p.is_file():
        raise NoMedible(f"--env-file no existe: {fichero}")
    env = {}
    for n, ln in enumerate(p.read_text(encoding="utf-8").splitlines(), 1):
        ln = ln.strip()
        if not ln or ln.startswith("#"):
            continue
        if ln.startswith("export "):
            ln = ln[7:].strip()
        clave, sep, valor = ln.partition("=")
        if not sep or not re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]*", clave.strip()):
            raise NoMedible(f"--env-file, línea {n}: no es CLAVE=valor")
        env[clave.strip()] = valor.strip().strip('"').strip("'")
    return env


def entorno(base_env: dict, settings: str) -> dict:
    env = dict(os.environ)
    env.update(base_env)
    env["DJANGO_SETTINGS_MODULE"] = settings
    env["PYTHONDONTWRITEBYTECODE"] = "1"        # no dejar __pycache__ en el proyecto medido
    env.pop("PYTHONSTARTUP", None)
    return env


def _cola(texto: str, n: int = 6) -> str:
    """Las últimas líneas de un error, SIN las de código fuente del traceback (van sangradas
    cuatro espacios): un settings con un secreto escrito en la línea que falla lo imprimiría."""
    lineas = [ln for ln in texto.strip().splitlines() if ln.strip() and not ln.startswith("    ")]
    return "\n      ".join(lineas[-n:]) if lineas else "(sin salida)"


# ── la sonda de settings y el check, en el python del proyecto ───────────────────────────

SONDA = r'''
import json, os, sys
sys.path.insert(0, os.getcwd())
import django
from django.conf import settings
_ = settings.DEBUG
w = settings._wrapped
def plano(v):
    if isinstance(v, dict):
        return {str(k): plano(x) for k, x in v.items()}
    if isinstance(v, (list, tuple, set, frozenset)):
        return [plano(x) for x in v]
    if isinstance(v, (bool, int, float)) or v is None:
        return v
    return str(v)
def s(nombre, defecto=None):
    return plano(getattr(w, nombre, defecto))
rf = getattr(w, "REST_FRAMEWORK", None) or {}
out = {
    "django": django.get_version(),
    "DEBUG": bool(getattr(w, "DEBUG", False)),
    "INSTALLED_APPS": s("INSTALLED_APPS", []),
    "MIDDLEWARE": s("MIDDLEWARE", []),
    "AUTHENTICATION_BACKENDS": s("AUTHENTICATION_BACKENDS", []),
    "SILENCED_SYSTEM_CHECKS": s("SILENCED_SYSTEM_CHECKS", []),
    "SECURE_CSP": s("SECURE_CSP"),
    "SECURE_CSP_REPORT_ONLY": s("SECURE_CSP_REPORT_ONLY"),
    "CONTENT_SECURITY_POLICY": s("CONTENT_SECURITY_POLICY"),
    "CONTENT_SECURITY_POLICY_REPORT_ONLY": s("CONTENT_SECURITY_POLICY_REPORT_ONLY"),
    "CSP_ANTIGUO": {k: plano(getattr(w, k)) for k in dir(w) if k.startswith("CSP_")},
    "REST_FRAMEWORK": {k: plano(rf.get(k)) for k in
                       ("DEFAULT_PERMISSION_CLASSES", "DEFAULT_THROTTLE_CLASSES",
                        "DEFAULT_THROTTLE_RATES") if k in rf},
    "ACCOUNT_RATE_LIMITS": plano(getattr(w, "ACCOUNT_RATE_LIMITS", "__sin_definir__")),
}
print("@@G3@@" + json.dumps(out))
'''

# `obj: (app.W001) mensaje` — el formato de los system checks de Django.
RX_ISSUE = re.compile(r"^(?P<obj>.*?): \((?P<id>[A-Za-z0-9_]+(?:\.[A-Za-z0-9_]+)*\.[CEWI]\d+)\) "
                      r"(?P<msg>.*)$", re.M)


def sondear(python: str, manage: Path, env: dict) -> dict:
    try:
        r = subprocess.run([python, "-c", SONDA], cwd=manage.parent, env=env,
                           capture_output=True, text=True, timeout=TIEMPO)
    except FileNotFoundError as e:
        raise NoMedible(f"el python no existe: {python}") from e
    except subprocess.TimeoutExpired as e:
        raise NoMedible(f"la lectura de settings tardó más de {TIEMPO}s") from e
    for ln in r.stdout.splitlines():
        if ln.startswith(MARCA):
            return json.loads(ln[len(MARCA):])
    if "No module named 'django'" in r.stderr:
        raise NoMedible(f"{python} no tiene Django: pásale el del proyecto con --python")
    raise NoMedible("los settings no se pueden importar (¿faltan variables? usa --env-file):\n      "
                    + _cola(r.stderr))


def correr_check(python: str, manage: Path, settings: str, env: dict) -> tuple[list, int]:
    cmd = [python, str(manage), "check", "--deploy", "--fail-level", "WARNING",
           "--settings", settings]
    try:
        r = subprocess.run(cmd, cwd=manage.parent, env=env, capture_output=True, text=True,
                           timeout=TIEMPO)
    except subprocess.TimeoutExpired as e:
        raise NoMedible(f"el check tardó más de {TIEMPO}s") from e
    salida = r.stdout + "\n" + r.stderr
    issues = [m.groupdict() for m in RX_ISSUE.finditer(salida)]
    silenciados = sum(int(n) for n in re.findall(r"\((\d+) silenced\)", salida))
    if r.returncode != 0 and not issues:
        raise NoMedible("el check se rompió sin decir qué encontró:\n      " + _cola(salida))
    if r.returncode == 0 and "System check identified" not in salida:
        raise NoMedible("el check no imprimió su resultado: no sé si corrió\n      " + _cola(salida))
    return issues, silenciados


# ── las comprobaciones sobre los settings ────────────────────────────────────────────────


def _version(v: str) -> tuple:
    return tuple(int(x) for x in re.findall(r"\d+", v)[:2]) or (0, 0)


def _hay(lista, sufijo: str) -> bool:
    # La CLASE se llama así; «NoCSPMiddleware» no es el middleware de la CSP (verificador de la 2.29).
    return any(str(x).rsplit(".", 1)[-1] == sufijo for x in lista or [])


def _app(apps, prefijos) -> bool:
    return any(a == p or a.startswith(p + ".") for a in apps or [] for p in prefijos)


ARREGLOS = {
    "security.W004": "SECURE_HSTS_SECONDS = 31536000 (empieza por 3600 si no estás seguro del HTTPS "
                     "de todos los subdominios)",
    "security.W005": "SECURE_HSTS_INCLUDE_SUBDOMAINS = True",
    "security.W008": "SECURE_SSL_REDIRECT = True — o, si redirige el proxy, excepción con la ruta de "
                     "su config",
    "security.W009": "SECRET_KEY de 50+ caracteres aleatorios, leída del entorno; la vieja pasa a "
                     "SECRET_KEY_FALLBACKS mientras dure la rotación",
    "security.W012": "SESSION_COOKIE_SECURE = True",
    "security.W016": "CSRF_COOKIE_SECURE = True",
    "security.W018": "DEBUG = False en producción (leído del entorno, con False por defecto)",
    "security.W020": "ALLOWED_HOSTS con los dominios reales",
    "security.W021": "SECURE_HSTS_PRELOAD = True (solo si de verdad vas a pedir la precarga)",
    "security.W025": "cada clave de SECRET_KEY_FALLBACKS, de 50+ caracteres aleatorios; y se quitan "
                     "al acabar la rotación",
}


def comprobar_check(res: Resultado, issues: list, silenciados: int, conf: dict) -> None:
    for i in issues:
        if re.search(r"\.I\d+$", i["id"]):
            res.avisos.append(f"{i['id']} (informativo): {i['msg'][:160]}")
            continue
        msg = i["msg"] if len(i["msg"]) <= 220 else i["msg"][:220].rsplit(" ", 1)[0] + "…"
        res.falla(f"G3-CHECK-{i['id']}", "settings" if i["obj"] == "?" else i["obj"][:80], msg,
                  ARREGLOS.get(i["id"], "corrígelo en los settings de producción, o declara la "
                               "excepción con su razón si lo resuelve otra capa (el proxy)"))
    for sid in conf.get("SILENCED_SYSTEM_CHECKS") or []:
        if str(sid).startswith(SILENCIABLES_NO):
            res.falla("G3-CHECK-SILENCIADO", str(sid),
                      f"SILENCED_SYSTEM_CHECKS apaga {sid}: el check no lo dice y el gate saldría "
                      "verde con el problema puesto",
                      f"quita {sid} de SILENCED_SYSTEM_CHECKS; si de verdad no aplica, es una "
                      "excepción del manifiesto con su razón, que se ve")
    res.medido.append(f"check de despliegue: {len(issues)} aviso(s), {silenciados} silenciado(s)")


def _directivas(politica) -> dict:
    if not isinstance(politica, dict):
        return {}
    if "DIRECTIVES" in politica and isinstance(politica["DIRECTIVES"], dict):
        politica = politica["DIRECTIVES"]
    return {str(k).lower(): v for k, v in politica.items()}


def _valores(v) -> list:
    if v is None:
        return []
    if isinstance(v, (list, tuple)):
        return [str(x) for x in v]
    return str(v).split()


def comprobar_csp(res: Resultado, conf: dict) -> None:
    mw = conf.get("MIDDLEWARE") or []
    antiguo = conf.get("CSP_ANTIGUO") or {}
    nativa = _directivas(conf.get("SECURE_CSP"))
    nativa_ro = _directivas(conf.get("SECURE_CSP_REPORT_ONLY"))
    dcsp = _directivas(conf.get("CONTENT_SECURITY_POLICY"))
    dcsp_ro = _directivas(conf.get("CONTENT_SECURITY_POLICY_REPORT_ONLY"))
    viejas = {k[4:].lower().replace("_", "-"): v for k, v in antiguo.items()
              if k not in ("CSP_REPORT_ONLY", "CSP_EXCLUDE_URL_PREFIXES", "CSP_REPORT_PERCENTAGE")}
    viejas_ro = bool(antiguo.get("CSP_REPORT_ONLY"))
    hay_mw_nativo = _hay(mw, MW_CSP_NATIVO)
    hay_mw_dcsp = _hay(mw, MW_CSP_DJANGO_CSP)
    nueva = _version(res.django) >= (6, 0)

    candidatas = []          # (nombre, directivas, solo_informe, se_envia)
    if nativa or nativa_ro:
        envia = hay_mw_nativo and nueva
        candidatas.append(("SECURE_CSP", nativa or nativa_ro, not nativa, envia))
    if dcsp or dcsp_ro:
        candidatas.append(("CONTENT_SECURITY_POLICY", dcsp or dcsp_ro, not dcsp, hay_mw_dcsp))
    if viejas:
        candidatas.append(("CSP_* (django-csp 3.x)", viejas, viejas_ro, hay_mw_dcsp))

    arreglo = ("Django >= 6.0: SECURE_CSP = {\"default-src\": [CSP.SELF], …} y "
               "django.middleware.csp.ContentSecurityPolicyMiddleware; Django 5.2: django-csp >= 4, "
               "CONTENT_SECURITY_POLICY = {\"DIRECTIVES\": {\"default-src\": [SELF], …}} y "
               "csp.middleware.CSPMiddleware")
    if not candidatas:
        res.falla("G3-CSP-AUSENTE", "settings", "no hay Content-Security-Policy: ni SECURE_CSP "
                  "ni django-csp. Un XSS que entre se ejecuta con todos los permisos de la página",
                  arreglo + " — o, si la pone el proxy, excepción con la ruta de su config")
        return
    enviadas = [c for c in candidatas if c[3]]
    if not enviadas:
        nombre = candidatas[0][0]
        porque = (" (SECURE_CSP no existe antes de Django 6.0)" if nombre == "SECURE_CSP"
                  and not nueva else "")
        res.falla("G3-CSP-SIN-MIDDLEWARE", "settings.MIDDLEWARE",
                  f"hay política en {nombre} pero ningún middleware la envía{porque}: la cabecera "
                  "no sale", arreglo)
        return
    aplicadas = [c for c in enviadas if not c[2]]
    if not aplicadas:
        res.falla("G3-CSP-SOLO-INFORME", "settings", "la CSP solo está en modo informe "
                  "(Report-Only): avisa, pero no bloquea nada",
                  "cuando el informe esté limpio, pasa la misma política a SECURE_CSP / "
                  "CONTENT_SECURITY_POLICY")
        return
    nombre, dirs, _, _ = aplicadas[0]
    if "default-src" not in dirs:
        res.falla("G3-CSP-SIN-DEFAULT-SRC", f"settings.{nombre.split()[0]}",
                  "la CSP no tiene default-src: todo lo que no nombra (script-src, connect-src, "
                  "frame-src…) queda sin restringir", "añade \"default-src\": [\"'self'\"]")
    for d in ("default-src", "script-src"):
        malos = [v for v in _valores(dirs.get(d)) if v.strip("'\"") in ("unsafe-inline",
                                                                       "unsafe-eval", "*")]
        if malos:
            res.avisos.append(f"G3-CSP-DEBIL: {d} permite {', '.join(sorted(set(malos)))} — "
                              "con eso la CSP apenas frena un XSS (usa nonces)")
    res.medido.append(f"CSP: {nombre}, enviada por su middleware, {len(dirs)} directiva(s)")


def comprobar_drf(res: Resultado, conf: dict, raiz: Path) -> None:
    if not _app(conf.get("INSTALLED_APPS"), ("rest_framework",)):
        res.medido.append("DRF: no está instalado (no aplica)")
        return
    rf = conf.get("REST_FRAMEWORK") or {}
    perm = rf.get("DEFAULT_PERMISSION_CLASSES")
    if not perm or any("AllowAny" in str(p) for p in perm):
        res.falla("G3-DRF-PERMISO-ABIERTO", "settings.REST_FRAMEWORK",
                  "DEFAULT_PERMISSION_CLASSES " + ("no está: el valor por defecto de DRF es "
                  "AllowAny" if not perm else "incluye AllowAny") + " — cualquier vista que "
                  "olvide permission_classes queda abierta a internet",
                  '"DEFAULT_PERMISSION_CLASSES": ["rest_framework.permissions.IsAuthenticated"]')
    n = escanear_vistas(res, raiz, rf)
    res.medido.append(f"DRF: permiso por defecto {perm or '(ninguno)'} · {n} vista(s) con AllowAny")


def comprobar_login(res: Resultado, conf: dict) -> None:
    apps = conf.get("INSTALLED_APPS") or []
    if not _app(apps, ("django.contrib.auth",)):
        res.medido.append("login: sin django.contrib.auth (no aplica)")
        return
    allauth = _app(apps, ("allauth.account",)) and conf.get("ACCOUNT_RATE_LIMITS") not in (False,
                                                                                           "False")
    if not (_app(apps, APPS_LIMITE) or allauth):
        res.falla("G3-SIN-LIMITE-INTENTOS", "settings.INSTALLED_APPS",
                  "no hay límite de intentos de login (ni django-axes, ni django-defender, ni "
                  "allauth con sus límites): un ataque de diccionario contra una cuenta no se frena",
                  "django-axes: 'axes' en INSTALLED_APPS, axes.middleware.AxesMiddleware al final de "
                  "MIDDLEWARE y axes.backends.AxesStandaloneBackend el primero de "
                  "AUTHENTICATION_BACKENDS")
    if _app(apps, ("django.contrib.admin",)) and not _app(apps, APPS_2FA):
        res.falla("G3-SIN-2FA", "settings.INSTALLED_APPS",
                  "el admin está instalado y no hay segundo factor (django-otp, two-factor-auth, "
                  "allauth.mfa): una contraseña filtrada basta para entrar como staff",
                  "django-otp + django_otp.plugins.otp_totp y OTPAdminSite (o two_factor) para el "
                  "admin")
    res.medido.append("login: límite de intentos y 2FA mirados por INSTALLED_APPS")


# ── las vistas públicas, por AST ─────────────────────────────────────────────────────────


def _es_test(rel: Path) -> bool:
    return (any(p in ("tests", "test") for p in rel.parts[:-1])
            or rel.name.startswith("test_") or rel.name == "conftest.py"
            or rel.name.endswith("_test.py"))


def _nombre(n) -> str:
    if isinstance(n, ast.Name):
        return n.id
    if isinstance(n, ast.Attribute):
        return n.attr
    if isinstance(n, ast.Call):
        return _nombre(n.func)
    return ""


def _nombres(n) -> set:
    return {_nombre(x) for x in ast.walk(n) if isinstance(x, (ast.Name, ast.Attribute))}


def _vacia(n) -> bool:
    return isinstance(n, (ast.List, ast.Tuple)) and not n.elts


def _literal(n):
    return n.value if isinstance(n, ast.Constant) and isinstance(n.value, str) else None


def _attr(cls: ast.ClassDef, nombre: str):
    for st in cls.body:
        if isinstance(st, ast.Assign) and any(isinstance(t, ast.Name) and t.id == nombre
                                              for t in st.targets):
            return st.value
        if (isinstance(st, ast.AnnAssign) and isinstance(st.target, ast.Name)
                and st.target.id == nombre and st.value is not None):
            return st.value
    return None


def _kw(call: ast.Call, nombre: str):
    for k in call.keywords:
        if k.arg == nombre:
            return k.value
    return None


class Indice:
    """Las clases del proyecto por nombre, para buscar el throttle en sus bases."""

    def __init__(self):
        self.clases: dict[str, list] = {}

    def anadir(self, arbol: ast.AST) -> None:
        for n in ast.walk(arbol):
            if isinstance(n, ast.ClassDef):
                self.clases.setdefault(n.name, []).append(n)

    def resolver(self, cls: ast.ClassDef, nombre: str, visto=None):
        visto = visto or set()
        if id(cls) in visto:
            return None
        visto.add(id(cls))
        v = _attr(cls, nombre)
        if v is not None:
            return v
        for b in cls.bases:
            for base in self.clases.get(_nombre(b), []):
                v = self.resolver(base, nombre, visto)
                if v is not None:
                    return v
        return None


def _throttle(tc, scope, rf: dict) -> tuple[str, str]:
    """('ok' | 'sin' | 'decorativo', detalle) para un throttle_classes y un throttle_scope."""
    defectos = [str(x) for x in rf.get("DEFAULT_THROTTLE_CLASSES") or []]
    tasas = rf.get("DEFAULT_THROTTLE_RATES") or {}
    valor = _literal(scope) if scope is not None else None
    if tc is not None:
        if _vacia(tc):
            return "sin", "throttle_classes = [] apaga el throttle en esta vista"
        if "ScopedRateThrottle" in _nombres(tc):
            if scope is None:
                return "decorativo", "ScopedRateThrottle sin throttle_scope: DRF no aplica ninguna tasa"
            if valor is not None and valor not in tasas:
                return "decorativo", f"throttle_scope '{valor}' sin tasa en DEFAULT_THROTTLE_RATES"
        return "ok", "throttle_classes propio"
    if scope is not None:
        if not any("ScopedRateThrottle" in d for d in defectos):
            return "decorativo", ("throttle_scope sin ScopedRateThrottle, ni en la vista ni en "
                                  "DEFAULT_THROTTLE_CLASSES: la tasa no se aplica")
        if valor is None:
            return "ok", "throttle_scope no literal: su tasa no se comprueba"
        if valor not in tasas:
            return "decorativo", f"throttle_scope '{valor}' sin tasa en DEFAULT_THROTTLE_RATES"
        return "ok", f"throttle_scope '{valor}' a {tasas[valor]}"
    extra = f" (el global {', '.join(d.rsplit('.', 1)[-1] for d in defectos)} es la misma tasa " \
            "para todo)" if defectos else ""
    return "sin", "ni throttle_scope ni throttle_classes" + extra


def escanear_vistas(res: Resultado, raiz: Path, rf: dict) -> int:
    arboles = []
    for p in sorted(raiz.rglob("*.py")):
        rel = p.relative_to(raiz)
        if _podado(p, raiz) or _es_test(rel):
            continue
        try:
            arbol = ast.parse(p.read_text(encoding="utf-8", errors="replace"))
        except SyntaxError as e:
            res.avisos.append(f"{rel}: no se puede leer ({e.msg}, línea {e.lineno}); sus vistas "
                              "no se miran")
            continue
        arboles.append((rel, arbol))
    idx = Indice()
    for _, arbol in arboles:
        idx.anadir(arbol)

    n = 0

    def anotar(estado: str, detalle: str, lugar: str) -> None:
        if estado == "sin":
            res.falla("G3-ALLOWANY-SIN-THROTTLE", lugar,
                      f"vista pública (AllowAny) sin límite de peticiones: {detalle}",
                      'throttle_scope = "<nombre>" con ScopedRateThrottle y su tasa en '
                      "DEFAULT_THROTTLE_RATES (o throttle_classes propio)")
        elif estado == "decorativo":
            res.falla("G3-THROTTLE-DECORATIVO", lugar, f"el throttle no limita nada: {detalle}",
                      "rest_framework.throttling.ScopedRateThrottle en DEFAULT_THROTTLE_CLASSES "
                      "(o en la vista) y la tasa del scope en DEFAULT_THROTTLE_RATES")

    for rel, arbol in arboles:
        # Las constantes del módulo (`PUBLICO = [AllowAny]`): un permission_classes que las nombra
        # es AllowAny igual (verificador de la 2.29).
        constantes = {t.id: st.value for st in arbol.body if isinstance(st, ast.Assign)
                      for t in st.targets if isinstance(t, ast.Name)}

        def resuelto(v):
            return constantes.get(v.id, v) if isinstance(v, ast.Name) else v

        # ast.walk y no arbol.body: una vista dentro de un `if` del módulo también cuenta.
        for nodo in ast.walk(arbol):
            if isinstance(nodo, ast.ClassDef):
                pc = _attr(nodo, "permission_classes")
                pc = resuelto(pc) if pc is not None else None
                if pc is not None and "AllowAny" in _nombres(pc):
                    n += 1
                    anotar(*_throttle(idx.resolver(nodo, "throttle_classes"),
                                      idx.resolver(nodo, "throttle_scope"), rf),
                           f"{rel.as_posix()}::{nodo.name}")
                for fn in nodo.body:
                    if not isinstance(fn, (ast.FunctionDef, ast.AsyncFunctionDef)):
                        continue
                    for dec in fn.decorator_list:
                        if (isinstance(dec, ast.Call) and _nombre(dec) == "action"
                                and _kw(dec, "permission_classes") is not None
                                and "AllowAny" in _nombres(_kw(dec, "permission_classes"))):
                            n += 1
                            tc = _kw(dec, "throttle_classes")
                            if tc is None:
                                tc = idx.resolver(nodo, "throttle_classes")
                            anotar(*_throttle(tc, idx.resolver(nodo, "throttle_scope"), rf),
                                   f"{rel.as_posix()}::{nodo.name}.{fn.name}")
            elif isinstance(nodo, (ast.FunctionDef, ast.AsyncFunctionDef)):
                decs = {_nombre(d): d for d in nodo.decorator_list if isinstance(d, ast.Call)}
                pc = decs.get("permission_classes")
                if pc is not None and pc.args:
                    pc = resuelto(pc.args[0])
                if pc is not None and "AllowAny" in _nombres(pc):
                    n += 1
                    tc = decs.get("throttle_classes")
                    tc = tc.args[0] if tc is not None and tc.args else None
                    anotar(*_throttle(tc, None, rf), f"{rel.as_posix()}::{nodo.name}")
    return n


# ── manifiesto y excepciones ─────────────────────────────────────────────────────────────


def leer_manifiesto(raiz: Path, ruta: str | None) -> tuple[dict, str]:
    p = Path(ruta) if ruta else raiz / MANIFIESTO_POR_DEFECTO
    if not p.exists():
        if ruta:
            raise NoMedible(f"el manifiesto no existe: {ruta}")
        return {}, ""
    try:
        d = json.loads(p.read_text(encoding="utf-8"))
    except ValueError as e:
        raise NoMedible(f"el manifiesto {p} no es JSON válido: {e}") from e
    if not isinstance(d, dict):
        raise NoMedible(f"el manifiesto {p} no es un objeto JSON")
    return d, str(p)


def aplicar_excepciones(res: Resultado, excepciones: dict) -> None:
    usadas = set()
    validas = {}
    for clave, razon in (excepciones or {}).items():
        if len(str(razon or "").strip()) < RAZON_MINIMA:
            res.falla("G3-EXCEPCION-SIN-RAZON", f"manifiesto: {clave}",
                      f"la excepción no tiene una razón de {RAZON_MINIMA} caracteres o más: no se "
                      "aplica", "escribe por qué no aplica y dónde se resuelve")
            continue
        validas[clave] = str(razon).strip()
    for h in res.hallazgos:
        if h.id.startswith("G3-EXCEPCION-"):
            continue
        for clave in (f"{h.id}@{h.lugar}", h.id):
            if clave in validas:
                h.exento = validas[clave]
                usadas.add(clave)
                break
    for clave in validas:
        if clave not in usadas:
            res.falla("G3-EXCEPCION-CADUCADA", f"manifiesto: {clave}",
                      "la excepción ya no cubre ningún hallazgo: o se arregló (quítala) o cambió "
                      "de sitio (actualízala)", "borra la entrada del manifiesto")


# ── medir ────────────────────────────────────────────────────────────────────────────────


def medir(raiz: Path, settings: str | None = None, python: str | None = None,
          manage: str | None = None, manifiesto: str | None = None,
          env_file: str | None = None) -> Resultado:
    raiz = raiz.resolve()
    if not raiz.is_dir():
        raise NoMedible(f"el proyecto no existe: {raiz}")
    man, ruta_man = leer_manifiesto(raiz, manifiesto)
    m = buscar_manage(raiz, manage or man.get("manage"))
    mod = modulo_de_settings(m, settings or man.get("settings"))
    py = elegir_python(raiz, m, python or man.get("python"))
    env = entorno(leer_env(env_file), mod)
    res = Resultado(proyecto=str(raiz), settings=mod, python=py,
                    manage=str(m.relative_to(raiz)))
    conf = sondear(py, m, env)
    res.django = conf.get("django", "")
    if conf.get("DEBUG"):
        res.avisos.append("DEBUG=True en estos settings: ¿son de verdad los de producción?")
    issues, silenciados = correr_check(py, m, mod, env)
    comprobar_check(res, issues, silenciados, conf)
    comprobar_csp(res, conf)
    comprobar_drf(res, conf, raiz)
    comprobar_login(res, conf)
    aplicar_excepciones(res, man.get("excepciones") or {})
    if ruta_man:
        res.medido.append(f"manifiesto: {ruta_man}")
    return res


def imprimir(res: Resultado) -> None:
    print(f"\nG3 · seguridad de Django · {res.proyecto}")
    print(f"  settings: {res.settings} · Django {res.django} · {res.manage} · python: {res.python}")
    for m in res.medido:
        print(f"  · {m}")
    print()
    for h in res.rojos():
        print(f"  ❌ {h.id}  {h.lugar}")
        print(f"       {h.que}")
        print(f"       ↳ {h.arreglo}")
    for h in res.hallazgos:
        if h.exento:
            print(f"  ⏸  {h.id}  {h.lugar} — exento: {h.exento}")
    for a in res.avisos:
        print(f"  ⚠  {a}")
    rojos = res.rojos()
    if rojos:
        print(f"\n⛔ {len(rojos)} hallazgo(s): esta configuración no sale a producción.")
    else:
        print("\n✅ Sin hallazgos. Ojo: el check de Django es necesario, no suficiente; lo que no "
              "mira este gate está en su cabecera (QUÉ NO COMPRUEBA).")


def _a_json(res: Resultado) -> str:
    d = asdict(res)
    d["pasa"] = not res.rojos()
    return json.dumps(d, ensure_ascii=False, indent=1)


# ── autoprueba: el gate se ve fallar ─────────────────────────────────────────────────────

MANAGE_PY = '''#!/usr/bin/env python
import os
import sys

if __name__ == "__main__":
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings_prod")
    from django.core.management import execute_from_command_line
    execute_from_command_line(sys.argv)
'''

URLS_PY = '''from django.contrib import admin
from django.urls import path

from app import views

urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/publico/", views.Publico.as_view()),
    path("api/privada/", views.Privada.as_view()),
]
'''

VISTAS_PY = '''from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView


class Publico(APIView):
    """El formulario de contacto: público y con su tasa."""

    permission_classes = [AllowAny]
    throttle_scope = "publico"

    def get(self, request):
        return Response({"ok": True})


class Privada(APIView):
    def get(self, request):
        return Response({"ok": True})
'''

SETTINGS_PY = '''SECRET_KEY = "@@CLAVE@@"
DEBUG = False
ALLOWED_HOSTS = ["app.ejemplo.test"]
INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "rest_framework",
    "axes",
    "django_otp",
    "django_otp.plugins.otp_totp",
@@CSP_APP@@    "app",
]
MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django_otp.middleware.OTPMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
@@CSP_MW@@    "axes.middleware.AxesMiddleware",
]
AUTHENTICATION_BACKENDS = [
    "axes.backends.AxesStandaloneBackend",
    "django.contrib.auth.backends.ModelBackend",
]
ROOT_URLCONF = "config.urls"
TEMPLATES = [{
    "BACKEND": "django.template.backends.django.DjangoTemplates",
    "DIRS": [],
    "APP_DIRS": True,
    "OPTIONS": {"context_processors": [
        "django.template.context_processors.request",
        "django.contrib.auth.context_processors.auth",
        "django.contrib.messages.context_processors.messages",
    ]},
}]
DATABASES = {"default": {"ENGINE": "django.db.backends.sqlite3", "NAME": ":memory:"}}
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"
STATIC_URL = "static/"
SECURE_HSTS_SECONDS = 31536000
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = True
SECURE_SSL_REDIRECT = True
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
REST_FRAMEWORK = {
    "DEFAULT_PERMISSION_CLASSES": ["rest_framework.permissions.IsAuthenticated"],
    "DEFAULT_THROTTLE_CLASSES": ["rest_framework.throttling.ScopedRateThrottle"],
    "DEFAULT_THROTTLE_RATES": {"publico": "30/min"},
}
@@CSP@@'''

CSP_NATIVA = dict(
    nombre="SECURE_CSP", app="", mw='    "django.middleware.csp.ContentSecurityPolicyMiddleware",\n',
    bloque='from django.utils.csp import CSP\n\nSECURE_CSP = {"default-src": [CSP.SELF], '
           '"script-src": [CSP.SELF], "frame-ancestors": [CSP.NONE]}\n')
CSP_DJANGO_CSP = dict(
    nombre="CONTENT_SECURITY_POLICY", app='    "csp",\n', mw='    "csp.middleware.CSPMiddleware",\n',
    bloque='from csp.constants import NONE, SELF\n\nCONTENT_SECURITY_POLICY = {"DIRECTIVES": '
           '{"default-src": [SELF], "script-src": [SELF], "frame-ancestors": [NONE]}}\n')

ST, VI = "config/settings_prod.py", "app/views.py"
SIN_CSP = "@@SIN_CSP@@"            # se sustituye por las tres piezas de la CSP de la versión

FUNCION_PUBLICA = '''

from rest_framework.decorators import api_view, permission_classes


@api_view(["POST"])
@permission_classes([AllowAny])
def alta(request):
    return Response({"ok": True})
'''

ACCION_PUBLICA = '''

from rest_framework import viewsets
from rest_framework.decorators import action


class Cuentas(viewsets.ViewSet):
    @action(detail=False, methods=["post"], permission_classes=[AllowAny])
    def recuperar(self, request):
        return Response({"ok": True})
'''

BASE_CON_TASA = '''from rest_framework.views import APIView


class PublicaConTasa(APIView):
    throttle_scope = "publico"
'''

HEREDA_TASA = '''

from app.base import PublicaConTasa


class Contacto(PublicaConTasa):
    permission_classes = [AllowAny]

    def post(self, request):
        return Response({"ok": True})
'''

TEST_PUBLICO = '''from rest_framework.permissions import AllowAny
from rest_framework.views import APIView


class VistaDePrueba(APIView):
    permission_classes = [AllowAny]
'''

SIN_AXES = [(ST, '    "axes",\n', ""), (ST, '    "axes.middleware.AxesMiddleware",\n', ""),
            (ST, '    "axes.backends.AxesStandaloneBackend",\n', "")]
SIN_OTP = [(ST, '    "django_otp",\n    "django_otp.plugins.otp_totp",\n', ""),
           (ST, '    "django_otp.middleware.OTPMiddleware",\n', "")]
RAZON = "la redirección a HTTPS la hace el proxy inverso (nginx), no Django"

# (nombre, cambios, manifiesto, esperados, exit). Un cambio es (fichero, viejo, nuevo); viejo ""
# añade al final. Un sabotaje tiene que salir con EXACTAMENTE sus hallazgos: uno de más dice que el
# fixture no aísla el mecanismo; uno de menos, que el gate no lo ve.
CASOS = [
    ("limpio", [], None, set(), 0),
    # sabotajes
    ("DEBUG=True", [(ST, "DEBUG = False", "DEBUG = True")], None, {"G3-CHECK-security.W018"}, 1),
    ("sin CSP", [(ST, SIN_CSP, "")], None, {"G3-CSP-AUSENTE"}, 1),
    ("CSP sin su middleware", [(ST, "@@MW@@", "")], None, {"G3-CSP-SIN-MIDDLEWARE"}, 1),
    ("CSP solo en modo informe", [(ST, "@@NOMBRE@@ = ", "@@NOMBRE@@_REPORT_ONLY = ")], None,
     {"G3-CSP-SOLO-INFORME"}, 1),
    ("CSP sin default-src", [(ST, '"default-src": [', '"img-src": [')], None,
     {"G3-CSP-SIN-DEFAULT-SRC"}, 1),
    ("cookie de sesión sin Secure", [(ST, "SESSION_COOKIE_SECURE = True",
                                      "SESSION_COOKIE_SECURE = False")], None,
     {"G3-CHECK-security.W012"}, 1),
    ("cookie CSRF sin Secure", [(ST, "CSRF_COOKIE_SECURE = True", "CSRF_COOKIE_SECURE = False")],
     None, {"G3-CHECK-security.W016"}, 1),
    ("sin HSTS", [(ST, "SECURE_HSTS_SECONDS = 31536000", "SECURE_HSTS_SECONDS = 0")], None,
     {"G3-CHECK-security.W004"}, 1),
    ("SECRET_KEY débil", [(ST, 'SECRET_KEY = "', 'SECRET_KEY = "django-insecure-')], None,
     {"G3-CHECK-security.W009"}, 1),
    ("DEBUG=True con su aviso silenciado", [(ST, "DEBUG = False", "DEBUG = True"),
                                            (ST, "", 'SILENCED_SYSTEM_CHECKS = ["security.W018"]\n')],
     None, {"G3-CHECK-SILENCIADO"}, 1),
    ("DRF sin permiso por defecto", [(ST, '    "DEFAULT_PERMISSION_CLASSES": '
                                          '["rest_framework.permissions.IsAuthenticated"],\n', "")],
     None, {"G3-DRF-PERMISO-ABIERTO"}, 1),
    ("DRF con AllowAny por defecto", [(ST, "permissions.IsAuthenticated", "permissions.AllowAny")],
     None, {"G3-DRF-PERMISO-ABIERTO"}, 1),
    ("vista AllowAny sin throttle", [(VI, '    throttle_scope = "publico"\n', "")], None,
     {"G3-ALLOWANY-SIN-THROTTLE"}, 1),
    ("throttle_scope sin ScopedRateThrottle", [(ST, '"DEFAULT_THROTTLE_CLASSES": '
                                                    '["rest_framework.throttling.ScopedRateThrottle"]',
                                                '"DEFAULT_THROTTLE_CLASSES": []')], None,
     {"G3-THROTTLE-DECORATIVO"}, 1),
    ("throttle_scope sin tasa", [(ST, '{"publico": "30/min"}', '{"otro": "30/min"}')], None,
     {"G3-THROTTLE-DECORATIVO"}, 1),
    ("throttle_classes = [] en la vista pública",
     [(VI, '    throttle_scope = "publico"\n', '    throttle_scope = "publico"\n'
                                              '    throttle_classes = []\n')], None,
     {"G3-ALLOWANY-SIN-THROTTLE"}, 1),
    ("vista de función AllowAny sin throttle", [(VI, "", FUNCION_PUBLICA)], None,
     {"G3-ALLOWANY-SIN-THROTTLE"}, 1),
    ("@action AllowAny sin throttle", [(VI, "", ACCION_PUBLICA)], None,
     {"G3-ALLOWANY-SIN-THROTTLE"}, 1),
    ("AllowAny por una constante del módulo, sin throttle",
     [(VI, "", '\n\nPUBLICO = [AllowAny]\n\n\nclass Alias(APIView):\n    permission_classes = PUBLICO\n')],
     None, {"G3-ALLOWANY-SIN-THROTTLE"}, 1),
    ("vista AllowAny dentro de un if del módulo, sin throttle",
     [(VI, "", '\n\nif True:\n    class Escondida(APIView):\n        permission_classes = [AllowAny]\n')],
     None, {"G3-ALLOWANY-SIN-THROTTLE"}, 1),
    ("sin límite de intentos", SIN_AXES, None, {"G3-SIN-LIMITE-INTENTOS"}, 1),
    ("axes sin su middleware", [(ST, '    "axes.middleware.AxesMiddleware",\n', "")], None,
     {"G3-CHECK-axes.W002"}, 1),
    ("admin sin segundo factor", SIN_OTP, None, {"G3-SIN-2FA"}, 1),
    ("excepción con razón corta", [(ST, "DEBUG = False", "DEBUG = True")],
     {"excepciones": {"G3-CHECK-security.W018": "porque sí"}},
     {"G3-EXCEPCION-SIN-RAZON", "G3-CHECK-security.W018"}, 1),
    ("excepción que ya no cubre nada", [], {"excepciones": {"G3-CHECK-security.W008": RAZON}},
     {"G3-EXCEPCION-CADUCADA"}, 1),
    # controles: lo correcto NO puede salir rojo
    ("control · throttle_classes propio en la vista pública",
     [(VI, '    throttle_scope = "publico"\n',
       '    throttle_classes = [AnonRateThrottle]\n'),
      (VI, "from rest_framework.views import APIView\n",
       "from rest_framework.throttling import AnonRateThrottle\nfrom rest_framework.views import "
       "APIView\n"),
      (ST, '{"publico": "30/min"}', '{"publico": "30/min", "anon": "20/min"}')], None, set(), 0),
    ("control · throttle heredado de una base del proyecto",
     [("app/base.py", "", BASE_CON_TASA), (VI, "", HEREDA_TASA)], None, set(), 0),
    ("control · AllowAny en un test no cuenta", [("app/tests/__init__.py", "", ""),
                                                 ("app/tests/test_vistas.py", "", TEST_PUBLICO)],
     None, set(), 0),
    ("control · excepción válida (HTTPS en el proxy)",
     [(ST, "SECURE_SSL_REDIRECT = True", "SECURE_SSL_REDIRECT = False")],
     {"excepciones": {"G3-CHECK-security.W008": RAZON}}, set(), 0),
    ("control · excepción acotada a una vista",
     [(VI, '    throttle_scope = "publico"\n', "")],
     {"excepciones": {"G3-ALLOWANY-SIN-THROTTLE@app/views.py::Publico":
                      "sonda del balanceador: no devuelve datos ni escribe nada"}}, set(), 0),
    # no medido: el instrumento que no llega al sujeto ABORTA
    ("no medido · settings que no importan", [(ST, "", "import modulo_que_no_existe\n")], None,
     set(), 2),
    ("no medido · sin manage.py", [("manage.py", "@@BORRAR@@", "")], None, set(), 2),
    ("no medido · python sin Django", [], None, set(), 2),
]


def _montar(dst: Path, csp: dict) -> None:
    (dst / "config").mkdir(parents=True)
    (dst / "app").mkdir()
    (dst / "manage.py").write_text(MANAGE_PY, encoding="utf-8")
    (dst / "config" / "__init__.py").write_text("", encoding="utf-8")
    (dst / "config" / "urls.py").write_text(URLS_PY, encoding="utf-8")
    (dst / "app" / "__init__.py").write_text("", encoding="utf-8")
    (dst / "app" / "views.py").write_text(VISTAS_PY, encoding="utf-8")
    st = (SETTINGS_PY.replace("@@CLAVE@@", secrets.token_urlsafe(48))
          .replace("@@CSP_APP@@", csp["app"]).replace("@@CSP_MW@@", csp["mw"])
          .replace("@@CSP@@", csp["bloque"]))
    (dst / ST).write_text(st, encoding="utf-8")


def _aplicar(dst: Path, cambios: list, csp: dict) -> None:
    for fichero, viejo, nuevo in cambios:
        p = dst / fichero
        if viejo == "@@BORRAR@@":
            p.unlink()
            continue
        if viejo == SIN_CSP:
            for pieza in (csp["bloque"], csp["mw"], csp["app"]):
                if pieza:
                    _aplicar(dst, [(fichero, pieza, "")], csp)
            continue
        viejo = viejo.replace("@@MW@@", csp["mw"]).replace("@@NOMBRE@@", csp["nombre"])
        nuevo = nuevo.replace("@@NOMBRE@@", csp["nombre"])
        p.parent.mkdir(parents=True, exist_ok=True)
        txt = p.read_text(encoding="utf-8") if p.exists() else ""
        if viejo == "":
            p.write_text(txt + nuevo, encoding="utf-8")
            continue
        if txt.count(viejo) != 1:
            raise NoMedible(f"autoprueba: el ancla {viejo[:50]!r} sale {txt.count(viejo)} veces en "
                            f"{fichero} (el fixture cambió y el sabotaje ya no apunta a nada)")
        p.write_text(txt.replace(viejo, nuevo), encoding="utf-8")


def _python_sin_django(carpeta: Path) -> str:
    """Un python que no ve site-packages: Django no se puede importar."""
    p = carpeta / "python-sin-django"
    p.write_text(f'#!/bin/sh\nexec "{sys.executable}" -S "$@"\n', encoding="utf-8")
    p.chmod(p.stat().st_mode | stat.S_IXUSR)
    return str(p)


def autoprueba(python: str, como_json: bool) -> int:
    faltan = []
    r = subprocess.run([python, "-c", "import django, sys; print(django.get_version())"],
                       capture_output=True, text=True)
    if r.returncode != 0:
        raise NoMedible(f"--autoprueba necesita Django en {python} (pásale --python)")
    version = r.stdout.strip()
    nueva = _version(version) >= (6, 0)
    for mod, pip in (("rest_framework", "djangorestframework"), ("axes", "django-axes"),
                     ("django_otp", "django-otp")) + ((() if nueva else (("csp", "django-csp>=4"),))):
        if subprocess.run([python, "-c", f"import {mod}"], capture_output=True).returncode != 0:
            faltan.append(pip)
    if faltan:
        raise NoMedible(f"--autoprueba necesita en {python}: {' '.join(faltan)} "
                        f"(uv pip install --python {python} {' '.join(faltan)})")
    csp = CSP_NATIVA if nueva else CSP_DJANGO_CSP
    filas = []
    with tempfile.TemporaryDirectory(prefix="g3-autoprueba-") as tmp:
        tmp = Path(tmp)
        sin_django = _python_sin_django(tmp)
        for i, (nombre, cambios, manifiesto, esperados, exit_esperado) in enumerate(CASOS):
            dst = tmp / f"caso{i:02d}"
            _montar(dst, csp)
            _aplicar(dst, cambios, csp)
            if manifiesto is not None:
                (dst / ".claude").mkdir()
                (dst / ".claude" / "gate-django.json").write_text(json.dumps(manifiesto),
                                                                  encoding="utf-8")
            py = sin_django if nombre == "no medido · python sin Django" else python
            try:
                res = medir(dst, python=py, settings="config.settings_prod")
                obtenido, exit_obtenido = res.ids(), (EXIT_FALLO if res.rojos() else EXIT_OK)
                detalle = "; ".join(f"{h.id} ({h.lugar})" for h in res.rojos())
            except NoMedible as e:
                obtenido, exit_obtenido, detalle = set(), EXIT_NO_MEDIDO, str(e).splitlines()[0]
            ok = exit_obtenido == exit_esperado and obtenido == esperados
            filas.append(dict(caso=nombre, ok=ok, exit_esperado=exit_esperado,
                              exit_obtenido=exit_obtenido, esperados=sorted(esperados),
                              obtenidos=sorted(obtenido), detalle=detalle))
    bien = sum(f["ok"] for f in filas)
    if como_json:
        print(json.dumps({"autoprueba": filas, "bien": bien, "total": len(filas),
                          "django": version, "csp": csp["nombre"]}, ensure_ascii=False, indent=1))
    else:
        print(f"G3 · autoprueba de check_django_seguridad.py · Django {version} · CSP por "
              f"{csp['nombre']}\n  (cada sabotaje tiene que caer por SU hallazgo, ni uno más)\n")
        for f in filas:
            print(f"  {'✓' if f['ok'] else '✗'} {f['caso']}  → exit {f['exit_obtenido']}")
            if not f["ok"]:
                print(f"      esperaba exit {f['exit_esperado']} con {f['esperados'] or '—'}; "
                      f"salió {f['obtenidos'] or '—'}  [{f['detalle'][:300]}]")
        print(f"\n═══ {bien}/{len(filas)} casos como se esperaba")
    return EXIT_OK if bien == len(filas) else EXIT_FALLO


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="G3: seguridad de la configuración de Django "
                                             "(ver la cabecera del script)")
    ap.add_argument("proyecto", nargs="?", default=".")
    ap.add_argument("--settings", help="módulo de settings de PRODUCCIÓN")
    ap.add_argument("--python", help="el python del proyecto (con Django instalado)")
    ap.add_argument("--manage", help="ruta de manage.py, relativa al proyecto")
    ap.add_argument("--manifiesto", help="por defecto <proyecto>/.claude/gate-django.json")
    ap.add_argument("--env-file", help="variables CLAVE=valor para los settings (no se imprimen)")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--autoprueba", action="store_true")
    args = ap.parse_args(argv)
    try:
        if args.autoprueba:
            return autoprueba(args.python or os.environ.get("G3_PYTHON") or sys.executable,
                              args.json)
        res = medir(Path(args.proyecto), args.settings, args.python, args.manage,
                    args.manifiesto, args.env_file)
    except NoMedible as e:
        if args.json:
            print(json.dumps({"no_medido": str(e)}, ensure_ascii=False))
        else:
            print(f"G3 · NO MEDIDO: {e}", file=sys.stderr)
        return EXIT_NO_MEDIDO
    if args.json:
        print(_a_json(res))
    else:
        imprimir(res)
    return EXIT_FALLO if res.rojos() else EXIT_OK


if __name__ == "__main__":
    sys.exit(main())
