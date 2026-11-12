"""Facturación — modelos. Patrón de casa: `.claude/patterns/stack/backend-modelos.md`.

Este fichero es la implementación de referencia que citan las reglas `be-model-*`. Se usa además
como banco de pruebas del checker (`pattern_check_backend.py --self-test`): debe producir CERO
hallazgos, así que no lo "mejores" introduciendo un atajo.
"""
import uuid
from decimal import Decimal

from django.core.validators import MinValueValidator
from django.db import models
from django.db.models import Q


class Estado(models.TextChoices):
    """A nivel de módulo, y no anidada dentro del modelo, por una razón concreta: el cuerpo de
    `class Meta` NO ve el espacio de nombres de la clase que lo contiene, así que una constraint
    que quiera decir `estado__in=Estado.values` no puede alcanzarla si está anidada. Con el enum
    fuera, la lista de valores válidos se escribe UNA vez y la usan el campo y la constraint."""

    BORRADOR = "borrador", "Borrador"
    EMITIDA = "emitida", "Emitida"
    PAGADA = "pagada", "Pagada"
    ANULADA = "anulada", "Anulada"


class Factura(models.Model):
    Estado = Estado   # alias de conveniencia: `Factura.Estado.BORRADOR` en el resto del código

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    cliente = models.ForeignKey(
        "clientes.Cliente",
        on_delete=models.PROTECT,          # una factura emitida sobrevive al borrado del cliente
        related_name="facturas",
    )
    numero = models.CharField(max_length=32, unique=True)
    concepto = models.CharField(max_length=200, blank=True, default="")
    importe = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        validators=[MinValueValidator(Decimal("0.00"))],
    )
    estado = models.CharField(max_length=16, choices=Estado.choices, default=Estado.BORRADOR)
    emitida_en = models.DateTimeField(null=True, blank=True)
    enviada_en = models.DateTimeField(null=True, blank=True)
    creada_en = models.DateTimeField(auto_now_add=True)
    actualizada_en = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-creada_en"]
        indexes = [
            # el listado del cliente es la query caliente: filtra por cliente y ordena por fecha
            models.Index(fields=["cliente", "-creada_en"], name="factura_cliente_fecha_idx"),
        ]
        constraints = [
            models.CheckConstraint(
                condition=Q(importe__gte=Decimal("0.00")),
                name="factura_importe_no_negativo",
                violation_error_message="El importe de una factura no puede ser negativo.",
            ),
            # `choices` solo lo aplica el formulario o el serializer. Esta constraint es la misma
            # regla, pero en la puerta por la que entra TODO: el import masivo, el `shell`, la
            # migración de datos y el `objects.create()` de una task.
            models.CheckConstraint(
                condition=Q(estado__in=Estado.values),
                name="factura_estado_valido",
            ),
            models.UniqueConstraint(
                fields=["cliente", "numero"],
                condition=~Q(estado="borrador"),
                name="factura_numero_unico_por_cliente_emitida",
            ),
        ]

    def __str__(self) -> str:
        return f"{self.numero} · {self.importe} €"
