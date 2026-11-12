"""Settings base — implementación de referencia del patrón de casa.

Todo lo que cambia entre entornos se lee del entorno y no tiene default inseguro. Las cuatro
opciones de DRF/Celery de aquí abajo no son cosmética: son las que hacen que un endpoint nuevo
nazca cerrado y paginado, y que una task nunca cuelgue un worker para siempre.
"""
import environ
from kombu import Exchange, Queue

env = environ.Env()

SECRET_KEY = env("DJANGO_SECRET_KEY")
DEBUG = env.bool("DJANGO_DEBUG", default=False)
ALLOWED_HOSTS = env.list("DJANGO_ALLOWED_HOSTS", default=[])
DATABASE_URL = env("DATABASE_URL")
SENTRY_DSN = env("SENTRY_DSN", default="")

# ── Observabilidad ───────────────────────────────────────────────────────────
# Sin este bloque, Django manda los errores a consola y ahí mueren: el fallo de las 4 de la mañana
# no queda en ningún fichero y por la mañana solo hay "faltan datos" sin causa. Con trabajo
# desatendido esto es lo PRIMERO, no lo último: sin señal de vuelta, ninguna otra mejora se puede
# ni verificar.
LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "detallado": {"format": "{asctime} {levelname} {name} {message}", "style": "{"},
    },
    "handlers": {
        "consola": {"class": "logging.StreamHandler", "formatter": "detallado"},
        "fichero": {
            "class": "logging.handlers.RotatingFileHandler",
            "filename": "/var/log/facturacion/app.log",
            "maxBytes": 20 * 1024 * 1024,
            "backupCount": 5,
            "formatter": "detallado",
        },
    },
    # El nivel cuelga de una variable que YA existe, en vez de inventar otra: subirlo para depurar
    # un incidente no debe exigir tocar código.
    "root": {"handlers": ["consola", "fichero"], "level": "DEBUG" if DEBUG else "INFO"},
}

# ── DRF ──────────────────────────────────────────────────────────────────────
# Sin DEFAULT_PERMISSION_CLASSES el default de DRF es AllowAny: un ViewSet que olvide declarar
# permisos queda abierto. El default cerrado convierte el olvido en un 403, no en una fuga.
REST_FRAMEWORK = {
    "DEFAULT_PERMISSION_CLASSES": ["rest_framework.permissions.IsAuthenticated"],
    "DEFAULT_AUTHENTICATION_CLASSES": [
        "rest_framework_simplejwt.authentication.JWTAuthentication"
    ],
    "DEFAULT_PAGINATION_CLASS": "rest_framework.pagination.PageNumberPagination",
    "PAGE_SIZE": 50,
    # Una sola forma de error para el frontend: 400 {"errors": {campo: [msg]}}.
    # Sin esto DRF devuelve dos formas distintas (campo-a-nivel-raíz y {"detail": ...}).
    "EXCEPTION_HANDLER": "config.exceptions.api_exception_handler",
}

# ── Caché ────────────────────────────────────────────────────────────────────
CACHES = {
    "default": {
        "BACKEND": "django.core.cache.backends.redis.RedisCache",
        "LOCATION": env("REDIS_URL"),
        "KEY_PREFIX": "facturacion",   # varios proyectos comparten este Redis
        "TIMEOUT": 300,
    }
}

# ── Celery ───────────────────────────────────────────────────────────────────
CELERY_BROKER_URL = env("RABBITMQ_URL")
CELERY_RESULT_BACKEND = env("REDIS_URL")

# json y solo json: con pickle, un mensaje de la cola ejecuta código arbitrario. Como efecto
# secundario deseado, pasar un objeto del ORM a una task revienta al encolar y no en producción.
CELERY_TASK_SERIALIZER = "json"
CELERY_RESULT_SERIALIZER = "json"
CELERY_ACCEPT_CONTENT = ["json"]

CELERY_TASK_SOFT_TIME_LIMIT = 300   # excepción capturable: da tiempo a cerrar limpio
CELERY_TASK_TIME_LIMIT = 360        # SIGKILL: el techo duro
CELERY_TASK_ACKS_LATE = True
CELERY_TASK_REJECT_ON_WORKER_LOST = True
CELERY_WORKER_PREFETCH_MULTIPLIER = 1

_dlx = Exchange("facturacion.dlx", type="direct")

CELERY_TASK_QUEUES = (
    Queue(
        "facturacion.default",
        Exchange("facturacion"),
        routing_key="default",
        queue_arguments={
            "x-queue-type": "quorum",
            "x-dead-letter-exchange": "facturacion.dlx",
            "x-delivery-limit": 5,
        },
    ),
    # pattern-exempt: be-mq-dlx — es la cola de descarte final; no reencola en ningún sitio
    Queue("facturacion.dead", _dlx, routing_key="default"),
)
