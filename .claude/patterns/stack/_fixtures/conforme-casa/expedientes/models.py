"""Expedientes — el modelo de dominio, heredando lo de casa.

Tres cosas que este fichero demuestra y que se comprueban solas:
  1. hereda de `CRUDModel` → trae `owner`, y por eso el filtrado por usuario puede funcionar;
  2. su `Meta` hereda de `MetaDeCasa` → sus permisos se crean al migrar, incluido `relate`;
  3. el campo con `choices` lleva además su `CheckConstraint` → la lista de valores válidos la
     aplica también la base de datos, no solo el formulario.
"""
from django.db import models
from django.db.models import Q

from core.models import CRUDModel, CodigoVisibleMixin, MetaDeCasa


class Estado(models.TextChoices):
    BORRADOR = "borrador", "Borrador"
    ABIERTO = "abierto", "Abierto"
    CERRADO = "cerrado", "Cerrado"


class Expediente(CRUDModel, CodigoVisibleMixin):
    referencia = models.CharField(max_length=32, unique=True)
    titulo = models.CharField(max_length=200, blank=True, default="")
    estado = models.CharField(max_length=16, choices=Estado.choices, default=Estado.BORRADOR)
    importe = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    responsable = models.ForeignKey(
        "expedientes.Equipo", on_delete=models.PROTECT, related_name="expedientes",
    )

    class Meta(MetaDeCasa):
        ordering = ["-created_at"]
        constraints = [
            # La misma regla que `choices`, pero en la puerta por la que entra TODO: el import
            # masivo, el `manage.py shell`, la migración de datos y el `create()` de una task.
            models.CheckConstraint(
                condition=Q(estado__in=Estado.values), name="expediente_estado_valido",
            ),
            models.CheckConstraint(
                condition=Q(importe__gte=0), name="expediente_importe_no_negativo",
            ),
        ]


class Equipo(CRUDModel):
    nombre = models.CharField(max_length=100, unique=True)

    class Meta(MetaDeCasa):
        verbose_name = "equipo"
