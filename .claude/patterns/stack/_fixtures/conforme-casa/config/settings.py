"""Settings del proyecto — un fichero único, y con las cuatro piezas que sostienen la noche."""
import environ

env = environ.Env()

SECRET_KEY = env("DJANGO_SECRET_KEY")
DEBUG = env.bool("DJANGO_DEBUG", default=False)
ALLOWED_HOSTS = env.list("DJANGO_ALLOWED_HOSTS", default=[])

INSTALLED_APPS = [
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "rest_framework",
    "core",
    "expedientes",
]

ROOT_URLCONF = "config.urls"

# ── Bases de datos ───────────────────────────────────────────────────────────
# UN alias, y con ENGINE. Parece obvio hasta que alguien usa `DATABASES` como cajón de sastre para
# guardar diccionarios de conexión de otras librerías: `manage.py test` crea una base de datos de
# test POR ALIAS, así que un alias sin ENGINE no rompe la aplicación —rompe la suite entera, y el
# error no dice que la causa sea la configuración.
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": env("POSTGRES_DB"),
        "USER": env("POSTGRES_USER"),
        "PASSWORD": env("POSTGRES_PASSWORD"),
        "HOST": env("POSTGRES_HOST", default="db"),
        "CONN_MAX_AGE": 60,
    }
}

# ── Observabilidad ───────────────────────────────────────────────────────────
LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {"detallado": {"format": "{asctime} {levelname} {name} {message}", "style": "{"}},
    "handlers": {
        "fichero": {
            "class": "logging.handlers.RotatingFileHandler",
            "filename": "/var/log/expedientes/app.log",
            "maxBytes": 20 * 1024 * 1024,
            "backupCount": 5,
            "formatter": "detallado",
        },
    },
    "root": {"handlers": ["fichero"], "level": "DEBUG" if DEBUG else "INFO"},
}

# ── DRF ──────────────────────────────────────────────────────────────────────
REST_FRAMEWORK = {
    "DEFAULT_PERMISSION_CLASSES": ["rest_framework.permissions.IsAuthenticated"],
    "DEFAULT_PAGINATION_CLASS": "rest_framework.pagination.PageNumberPagination",
    "PAGE_SIZE": 50,
    "EXCEPTION_HANDLER": "config.exceptions.api_exception_handler",
}

# ── Celery ───────────────────────────────────────────────────────────────────
CELERY_BROKER_URL = env("RABBITMQ_URL")
CELERY_TASK_SERIALIZER = "json"
CELERY_ACCEPT_CONTENT = ["json"]
CELERY_TASK_SOFT_TIME_LIMIT = 300
CELERY_TASK_TIME_LIMIT = 360
