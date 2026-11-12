"""Settings ÚNICO — el otro layout válido, y es deliberado que este fichero exista.

`_fixtures/conforme/` parte el settings en `config/settings/base.py`. Este no lo parte: un solo
fichero parametrizado por entorno. Los dos puntúan 0 hallazgos, y esa es exactamente la afirmación
que este fixture sostiene — el split `base/dev/prod` es el DEFAULT de proyecto nuevo, no una regla.

Medida que lo respalda (informe K, backend Django de 740 ficheros en producción): un `settings.py`
de 960 líneas resuelve por ~40 variables de entorno lo mismo que el split resuelve por ficheros,
con una sola rama por entorno. Partirlo cuesta trabajo y no cierra ningún fallo demostrado.
"""
import environ

env = environ.Env()

SECRET_KEY = env("DJANGO_SECRET_KEY")
DEBUG = env.bool("DJANGO_DEBUG", default=False)
ALLOWED_HOSTS = env.list("DJANGO_ALLOWED_HOSTS", default=[])
DATABASE_URL = env("DATABASE_URL")

# Apps hermanas planas del paquete de configuración: no hay carpeta `apps/`, y tampoco hace falta.
INSTALLED_APPS = [
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.messages",
    "core",
    "expedientes",
]

# Observabilidad: el bloque LOGGING no es opcional aunque el settings sea único y pequeño. Sin él
# el error se va a consola y se pierde; y lo que no deja rastro no se puede ni verificar por la
# mañana ni convertir en alerta.
LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "handlers": {
        "fichero": {
            "class": "logging.handlers.RotatingFileHandler",
            "filename": "/var/log/expedientes/app.log",
            "maxBytes": 20 * 1024 * 1024,
            "backupCount": 5,
        },
    },
    "root": {"handlers": ["fichero"], "level": "DEBUG" if DEBUG else "INFO"},
}

# La rama por entorno: una, explícita, en vez de tres ficheros que hay que mantener en paralelo.
if env.bool("CLOUD_DEPLOY", default=False):
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True
    SECURE_SSL_REDIRECT = True

# Aquí NO hay REST_FRAMEWORK, y no es un olvido: este backend renderiza plantillas en el servidor.
# Las tres reglas de settings de DRF (permisos, paginación, exception handler) no le aplican y no
# deben disparar — comprobarlo es la mitad de lo que hace este fixture.
