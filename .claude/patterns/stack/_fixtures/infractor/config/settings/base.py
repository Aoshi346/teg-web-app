"""ANTIPATRÓN A PROPÓSITO — banco de pruebas del checker. No copiar nada de aquí."""
import os

from kombu import Queue

SECRET_KEY = "django-insecure-4f9a2b7c1d8e3f6a"
DEBUG = True
DATABASE_URL = os.environ["DATABASE_URL"]
STRIPE_API_KEY = "sk_live_51H8xQ2eZvKYlo2C"
SENTRY_DSN = os.environ.get("SENTRY_DSN", "")

REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": [
        "rest_framework.authentication.SessionAuthentication"
    ],
}

CACHES = {
    "default": {
        "BACKEND": "django.core.cache.backends.redis.RedisCache",
        "LOCATION": "redis://cache:6379/0",
    }
}

CELERY_BROKER_URL = "amqp://broker:5672//"
CELERY_TASK_QUEUES = (Queue("facturacion.default"),)
