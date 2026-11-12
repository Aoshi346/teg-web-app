"""Settings mínimos: sqlite local, sin servicios externos."""
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
SECRET_KEY = "solo-para-el-fixture"  # tl-secret-ok: fixture sintético, sqlite local sin datos reales
DEBUG = True
ALLOWED_HOSTS = ["127.0.0.1", "localhost", "testserver"]
INSTALLED_APPS = [
    "django.contrib.contenttypes",
    "django.contrib.auth",
    "orders",
]
MIDDLEWARE = []
ROOT_URLCONF = "shop.urls"
DATABASES = {
    "default": {"ENGINE": "django.db.backends.sqlite3", "NAME": BASE_DIR / "db.sqlite3"},
}
USE_TZ = True
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"
