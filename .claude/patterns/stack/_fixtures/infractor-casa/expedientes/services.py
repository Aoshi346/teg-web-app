"""ANTIPATRÓN A PROPÓSITO — banco de pruebas del checker. No copiar nada de aquí."""
from .models import Expediente


def abrir_expediente(referencia, titulo, responsable_id):
    """be-owner-create-sin-dueno: crea la fila sin dueño.

    El proyecto filtra por `owner`, así que este expediente se crea, existe en la base de datos y
    **no aparece en la pantalla de nadie** sin permiso de organización. No hay error, no hay log,
    no hay excepción: solo un registro invisible. Es el fallo más difícil de diagnosticar de los
    que produce el olvido de un campo, porque el síntoma que llega es "se ha perdido lo que metí".
    """
    return Expediente.objects.create(
        referencia=referencia, titulo=titulo, responsable_id=responsable_id,
    )


def importar_lote(filas, usuario):
    """be-model-bulk-create-invariante: `bulk_create` no llama a `save()`.

    `Expediente` hereda `CodigoVisibleMixin`, cuyo `save()` calcula el código visible — el que el
    usuario final dicta por teléfono. Estas filas entran con el código a NULO y sin fila de
    historial, y nadie protesta porque el campo admite nulos. El daño aparece meses después,
    cuando alguien busca por un código que no existe.
    """
    return Expediente.objects.bulk_create(
        [Expediente(referencia=f["referencia"], owner=usuario) for f in filas]
    )
