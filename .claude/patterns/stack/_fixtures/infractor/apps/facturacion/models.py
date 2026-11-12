"""ANTIPATRÓN A PROPÓSITO — banco de pruebas del checker. No copiar nada de aquí."""
import uuid

from django.db import models
from django.db.models import Q


class Factura(models.Model):
    cliente = models.ForeignKey("clientes.Cliente", on_delete=models.CASCADE)
    numero = models.CharField(max_length=32, null=True, blank=True)
    concepto = models.CharField(max_length=200, null=True)
    importe = models.FloatField(default=0.0)
    estado = models.CharField(max_length=16, default="borrador")
    creada_en = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.CheckConstraint(check=Q(importe__gte=0), name="importe_no_negativo"),
        ]
