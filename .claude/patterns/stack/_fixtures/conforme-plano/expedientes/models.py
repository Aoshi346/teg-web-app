"""Expedientes — app hermana plana del paquete de configuración. No hay carpeta `apps/`."""
from django.conf import settings
from django.db import models


class Expediente(models.Model):
    class Estado(models.TextChoices):
        BORRADOR = "borrador", "Borrador"
        ABIERTO = "abierto", "Abierto"
        CERRADO = "cerrado", "Cerrado"

    referencia = models.CharField(max_length=32, unique=True)
    titulo = models.CharField(max_length=200, blank=True, default="")
    estado = models.CharField(max_length=16, choices=Estado.choices, default=Estado.BORRADOR)
    importe = models.DecimalField(max_digits=12, decimal_places=2, default=0)

    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT,
        related_name="expedientes_en_propiedad",
    )
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT,
        related_name="expedientes_creados",
    )
    updated_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT, null=True,
        related_name="expedientes_actualizados",
    )

    class Meta:
        constraints = [
            models.CheckConstraint(
                condition=models.Q(estado__in=["borrador", "abierto", "cerrado"]),
                name="expediente_estado_valido",
            )
        ]
