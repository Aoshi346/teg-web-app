"""Tasks — con techo de tiempo, reintentos y, sobre todo, `timeout=` en la llamada saliente."""
import logging

import requests
from celery import shared_task
from requests.exceptions import RequestException

from .models import Expediente

logger = logging.getLogger(__name__)


@shared_task(
    autoretry_for=(RequestException,),
    retry_backoff=True,
    max_retries=5,
    soft_time_limit=30,
    time_limit=60,
)
def avisar_apertura_expediente(expediente_id: str) -> str:
    """Avisa al portal del cliente de que hay expediente nuevo.

    El `timeout=` no es cosmética: sin él, `requests` espera indefinidamente. Un servicio que se
    DEGRADA (no que caiga: que tarde) retiene este worker, y si algo encola cada pocos segundos,
    por la mañana hay miles de tareas apiladas. Desde fuera no se ve un error, se ve que «la cola
    va lenta» — y el arreglo acaba siendo un script escrito a mano para purgarla.
    """
    expediente = Expediente.objects.filter(pk=expediente_id).first()
    if expediente is None:
        logger.warning("expediente %s ya no existe; nada que avisar", expediente_id)
        return "inexistente"

    respuesta = requests.post(
        "https://portal.example/api/avisos",
        json={"expediente": str(expediente.pk)},
        timeout=10,
    )
    respuesta.raise_for_status()   # un 500 del portal NO es un aviso entregado
    return "avisado"
