"""Common Django bootstrap for seed scripts run as `python -m seeds.<name>`."""
import os
import django


def setup() -> None:
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "core.settings")
    django.setup()
