"""ANTIPATRÓN A PROPÓSITO — banco de pruebas del checker. No copiar nada de aquí."""
from django.db import models

from core.models import CRUDModel, CodigoVisibleMixin


class Expediente(CRUDModel, CodigoVisibleMixin):
    referencia = models.CharField(max_length=32, unique=True)
    # be-model-choices-sin-constraint: la lista de valores válidos solo la aplica el formulario.
    estado = models.CharField(
        max_length=16,
        choices=[("borrador", "Borrador"), ("abierto", "Abierto")],
        default="borrador",
    )
    # be-model-floatfield-max-length + be-model-dinero-float: `max_length` no hace nada en un
    # campo numérico, y que esté ahí prueba que la declaración no la revisó nadie. Y es dinero.
    importe = models.FloatField(max_length=10, default=0.0)
    responsable = models.ForeignKey(
        "expedientes.Equipo", on_delete=models.PROTECT, related_name="expedientes",
    )

    class Meta:
        # be-model-meta-base-de-casa: sin `MetaDeCasa`. No falla nada, no avisa nadie: este modelo
        # simplemente se queda sin el permiso `relate_expediente`, y como los permisos por defecto
        # se crean AL MIGRAR, arreglar la herencia mañana no crea el que faltó hoy.
        ordering = ["-created_at"]


class Equipo(CRUDModel):
    nombre = models.CharField(max_length=100, unique=True)

    class Meta:
        verbose_name = "equipo"


class Nota(models.Model):
    """be-model-base-de-casa: hereda de `models.Model` pelado.

    Se queda sin auditoría y —lo que importa— sin el campo `owner` por el que filtra el scoping
    por usuario. No es que se le olvide el filtro: es que para este modelo el filtro no puede
    existir.
    """

    texto = models.TextField(blank=True, default="")
    expediente = models.ForeignKey(
        Expediente, on_delete=models.CASCADE, related_name="notas",
    )
