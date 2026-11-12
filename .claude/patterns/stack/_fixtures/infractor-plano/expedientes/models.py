"""Modelo correcto a propósito: las infracciones de este fixture son de la capa de formularios."""
from django.conf import settings
from django.db import models


class Expediente(models.Model):
    referencia = models.CharField(max_length=32, unique=True)
    titulo = models.CharField(max_length=200, blank=True, default="")
    estado = models.CharField(max_length=16, default="borrador")
    importe = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT,
        related_name="expedientes_en_propiedad",
    )
