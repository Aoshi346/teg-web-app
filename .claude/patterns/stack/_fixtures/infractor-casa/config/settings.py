"""ANTIPATRÓN A PROPÓSITO — banco de pruebas del checker. No copiar nada de aquí."""
import os

SECRET_KEY = os.environ["DJANGO_SECRET_KEY"]
DEBUG = True

INSTALLED_APPS = [
    "django.contrib.auth",
    "rest_framework",
    "core",
    "expedientes",
]

ROOT_URLCONF = "config.urls"

# be-test-db-alias-sin-engine + be-no-mongo. Dos fallos que viajan juntos:
#   - `manage.py test` crea una base de datos de test POR ALIAS. El alias `logs` no declara
#     ENGINE, así que la suite entera no arranca — y el error no dice que la causa sea esto.
#   - `djongo` mete una segunda base de datos para lo que el JSONField de PostgreSQL ya cubre, y
#     arrastra un pin de `sqlparse` antiguo que bloquea la ruta de actualización de Django.
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": os.environ["POSTGRES_DB"],
    },
    "historical": {
        "ENGINE": "djongo",
        "NAME": "historial",
    },
    "logs": {
        "CLIENT": {"host": "mongo", "port": 27017},
        "NAME": "logs",
    },
}

# be-obs-logging: no hay bloque LOGGING en ninguna parte. El error de las 4 de la mañana se va a
# consola y ahí muere: por la mañana solo queda "faltan datos", sin causa y sin rastro.

REST_FRAMEWORK = {
    "DEFAULT_PERMISSION_CLASSES": ["rest_framework.permissions.IsAuthenticated"],
    "DEFAULT_PAGINATION_CLASS": "rest_framework.pagination.PageNumberPagination",
    "PAGE_SIZE": 50,
    "EXCEPTION_HANDLER": "config.exceptions.api_exception_handler",
}
