"""El candado de datos reales: el proceso no arranca tocando datos reales de terceros sin su permiso.

Cosechado de `accounting_AMC` (`backend/core/seguridad/candado.py`, invariante 2: «sin DPA firmado no
se tocan datos reales de AMC»), generalizado en la sub-ola 2.29 de la revisión integral del template
(SE-49). El patrón entero —por qué así, dónde se cuelga y cómo se demuestra en CI que bloquea— está en
`.claude/patterns/stack/backend-candado-datos-reales.md`.

**Las dos mitades, que es lo que se confunde:**

  · `.claude/estado-datos-reales.json` + `.claude/scripts/gate_datos_reales.py` gobiernan si una
    PERSONA tiene derecho a poner `DATOS_REALES=1`. Son del harness de desarrollo, el estado está en
    el `deny` de `settings.json` (ningún agente lo edita) y NO se despliegan.
  · Este módulo gobierna el proceso en ejecución y solo mira el entorno. Es lo único que existe en
    producción.

Cuando están las dos (en desarrollo, que es donde se comete el error: poner la variable a 1 «para
probar» con el gate en rojo), se cruzan.

CÓMO SE INSTALA: se copia a `backend/core/seguridad/candado.py` (o donde viva lo transversal), se
rellenan las cuatro constantes de abajo y se llama a `comprobar_candado()` desde el `ready()` de una
app que esté en INSTALLED_APPS. `ready()` corre en TODO arranque de Django —runserver, gunicorn,
celery, manage.py, pytest—; un system check no bastaría, porque gunicorn no los ejecuta.
"""
from __future__ import annotations

import json
import os
from pathlib import Path

try:                                        # en un proyecto Django, el error que Django entiende
    from django.core.exceptions import ImproperlyConfigured as _Base
except ImportError:                         # pragma: no cover — fuera de Django (scripts, tests)
    _Base = RuntimeError

# ── lo que se rellena al copiarlo ────────────────────────────────────────────────────────────
#: La variable que abre el candado. Por proyecto, con su prefijo: `AMC_DATOS_REALES`, `EVO_DATOS_REALES`.
VARIABLE = "DATOS_REALES"
#: Las integraciones que pueden tocar datos reales, con la variable que las conmuta a «real».
MODOS: tuple[str, ...] = ("CRM_MODE", "CORREO_MODE")
#: Lo que tiene que existir ADEMÁS cuando hay datos reales (p. ej. una clave de cifrado propia que no
#: salga de SECRET_KEY: en AMC, la de los secretos de la doble verificación).
REQUISITOS_CON_DATOS_REALES: tuple[str, ...] = ()
#: Dónde vive el estado que firma una persona (relativo a la raíz del repo).
ESTADO = Path(".claude") / "estado-datos-reales.json"
#: La raíz del repo desde este fichero (backend/core/seguridad/candado.py → parents[3]).
NIVELES_HASTA_LA_RAIZ = 3
# ─────────────────────────────────────────────────────────────────────────────────────────────

GATE = "python3 .claude/scripts/gate_datos_reales.py"


class CandadoCerrado(_Base):
    """El proceso iba a tocar datos reales sin permiso. Es ImproperlyConfigured dentro de Django."""


def _pendientes(raiz: Path, estado: Path) -> list[str] | None:
    """Condiciones sin cerrar según el harness, o None si aquí no hay harness que mirar.

    Devuelve None —y no una lista vacía— cuando el fichero no existe o no se puede leer, para no
    confundir «no hay nada que comprobar» (producción) con «todo en verde». Una condición cuenta como
    cerrada solo con `ok: true` Y quién, cuándo y con qué evidencia: un verde sin firma es un fichero
    editado a mano. (El gate añade lo que aquí no se mira: que quien firma no sea un agente, que la
    fecha no sea futura y que la evidencia exista.)
    """
    ruta = raiz / estado
    if not ruta.exists():
        return None                                   # producción: no hay harness que mirar
    try:
        datos = json.loads(ruta.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        datos = None
    # Un estado que EXISTE y no se puede leer (a medias, vacío, otra forma) no abre nada: cuenta
    # como pendiente, no como «no hay harness» (verificador de la 2.29).
    if not isinstance(datos, dict) or not isinstance(datos.get("condiciones") or {}, dict):
        return ["(estado ilegible)"]
    if not datos.get("condiciones"):
        return ["(estado sin condiciones)"]
    pend = []
    for nombre, c in datos["condiciones"].items():
        c = c if isinstance(c, dict) else {}
        firmada = all(str(c.get(k) or "").strip() for k in ("quien", "fecha", "evidencia"))
        if c.get("ok") is not True or not firmada:
            pend.append(nombre)
    return pend


def comprobar_candado(entorno: dict[str, str] | None = None, raiz: Path | None = None, *,
                      variable: str = VARIABLE, modos: tuple[str, ...] = MODOS,
                      requisitos: tuple[str, ...] = REQUISITOS_CON_DATOS_REALES,
                      estado: Path = ESTADO) -> None:
    """Lanza CandadoCerrado si la configuración viola el candado. Si no, calla.

    Pura respecto a sus argumentos para poder probarla sin tocar el entorno del proceso.
    """
    env = os.environ if entorno is None else entorno
    raiz = Path(__file__).resolve().parents[NIVELES_HASTA_LA_RAIZ] if raiz is None else raiz

    datos_reales = env.get(variable, "0") == "1"
    en_real = [v for v in modos if env.get(v, "mock") == "real"]

    if en_real and not datos_reales:
        raise CandadoCerrado(
            f"{', '.join(en_real)} en modo real con {variable}=0.\n"
            "Sin el permiso firmado (contrato de encargo y lo demás) no se tocan datos reales.\n"
            f"Se trabaja contra fixtures/ y mocks/. Comprueba el estado con:\n    {GATE}")

    if datos_reales:
        pendientes = _pendientes(raiz, estado)
        if pendientes:
            raise CandadoCerrado(
                f"{variable}=1 pero el gate de datos reales está en ROJO ({len(pendientes)} "
                f"condiciones pendientes: {', '.join(pendientes)}).\n"
                f"El candado lo abre el permiso firmado, no la variable de entorno. Ponla a 0.\n"
                f"    {GATE}")
        faltan = [r for r in requisitos if not str(env.get(r, "")).strip()]
        if faltan:
            raise CandadoCerrado(f"{variable}=1 sin {', '.join(faltan)}: con datos reales esto tiene "
                                 "que existir antes de arrancar.")


def hay_datos_reales(entorno: dict[str, str] | None = None, variable: str = VARIABLE) -> bool:
    """¿Está abierto el candado en ESTE proceso?

    Para las puertas por las que entran datos A MANO (una subida de ficheros, un import): ahí no se
    bloquea —el sistema tiene que poder demostrarse con datos de prueba— sino que se avisa en pantalla
    y se deja traza. En AMC fue la puerta que el candado no miraba: protegía los conectores automáticos
    y dejaba fuera `/subir`, la pantalla más usada del panel (PRIYA-003).
    """
    env = os.environ if entorno is None else entorno
    return env.get(variable, "0") == "1"
