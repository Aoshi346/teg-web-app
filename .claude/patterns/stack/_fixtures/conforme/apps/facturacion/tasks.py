"""Facturación — tasks Celery.

Contrato de la capa: argumentos serializables en JSON (nunca objetos del ORM), idempotencia
demostrada con un test, techo de tiempo y política de reintentos explícita para el I/O de red.
Ver `.claude/patterns/stack/backend-celery.md`.
"""
import logging

import requests
from celery import shared_task
from celery.exceptions import SoftTimeLimitExceeded
from django.utils import timezone
from requests.exceptions import RequestException

from .models import Factura

logger = logging.getLogger(__name__)


@shared_task(
    autoretry_for=(RequestException,),
    retry_backoff=True,
    retry_backoff_max=600,
    max_retries=5,
    acks_late=True,
    soft_time_limit=60,
    time_limit=90,
)
def enviar_factura_por_email(factura_id: str) -> str:
    """Envía la factura al cliente.

    Recibe el id, no el objeto: entre que se encola y se ejecuta la fila puede haber cambiado, y
    el worker debe trabajar sobre el estado actual, no sobre una foto vieja.

    Idempotente: con acks_late=True Celery re-entrega la tarea si el worker muere a mitad, así que
    ejecutarla dos veces tiene que dar el mismo resultado. Lo cubre
    `test_enviar_factura_por_email_es_idempotente`.
    """
    factura = Factura.objects.filter(pk=factura_id).first()
    if factura is None:
        logger.warning("factura %s ya no existe; nada que enviar", factura_id)
        return "inexistente"
    if factura.enviada_en is not None:
        return "ya-enviada"

    try:
        requests.post(
            "https://api.emailer.example/send",
            json={"factura": str(factura.pk)},
            timeout=10,
        )
    except SoftTimeLimitExceeded:
        logger.error("envío de %s abortado por soft_time_limit", factura_id)
        raise

    # UPDATE condicional: si otra ejecución llegó antes, esta no pisa su marca de tiempo.
    Factura.objects.filter(pk=factura.pk, enviada_en__isnull=True).update(
        enviada_en=timezone.now()
    )
    return "enviada"
