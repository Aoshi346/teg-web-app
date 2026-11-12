"""Capa compartida del proyecto.
# pattern-layer: shared

Ese marcador es toda la declaración que necesita `be-capa-compartida-importa-dominio`: dice que
`core/` es infraestructura de la que cuelgan las apps de dominio, no una app más. A partir de ahí
el checker mide una sola cosa —que la flecha no se invierta— y la mide en SOMBRA: avisa, no
bloquea. No hay ningún YAML que mantener; el día que esta app deje de ser compartida se borra esta
línea y la regla deja de aplicarle.
"""
from django.apps import AppConfig


class CoreConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "core"
