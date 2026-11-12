"""Expedientes — lógica de negocio.
# pattern-layer: services

Esa línea de arriba es el punto del fixture: este proyecto llamó `utils.py` a su capa de servicio
—como hacen los backends Django reales, con decenas de miles de líneas ya escritas ahí— y NO va a
renombrar 30 ficheros para complacer al patrón. El marcador declara la capa, y el checker le
aplica lo que sí es la regla: no importar HTTP, no recibir `request`, ser invocable desde un test,
una task o un comando. El NOMBRE del fichero es el default de proyecto nuevo; esto es la costumbre
de un proyecto que ya existe.
"""
from django.db import transaction

from .models import Expediente


class ErrorDeExpediente(Exception):
    """Base del dominio. La vista decide qué significa en HTTP."""


class ExpedienteNoCerrable(ErrorDeExpediente):
    ...


@transaction.atomic
def cerrar_expediente(*, expediente_id: str, cerrado_por_id: str) -> Expediente:
    expediente = Expediente.objects.select_for_update().get(pk=expediente_id)
    if expediente.estado != Expediente.Estado.ABIERTO:
        raise ExpedienteNoCerrable(
            f"el expediente {expediente.referencia} está en estado {expediente.estado}"
        )
    expediente.estado = Expediente.Estado.CERRADO
    expediente.updated_by_id = cerrado_por_id
    expediente.save(update_fields=["estado", "updated_by"])
    return expediente
