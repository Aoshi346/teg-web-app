"""App de dominio. Sin marcador de capa: solo la capa compartida se declara."""
from django.apps import AppConfig


class ExpedientesConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "expedientes"

    def ready(self):
        # El sitio que documenta Django para registrar receivers: explícito y greppable. Quien
        # busque «quién conecta las señales» lo encuentra aquí, no en un autodiscover mágico.
        from . import signals  # noqa: F401
