"""ANTIPATRÓN A PROPÓSITO — banco de pruebas del checker. No copiar nada de aquí."""
import requests
from celery import shared_task

from .models import Factura


@shared_task
def enviar_factura_por_email(factura_id):
    factura = Factura.objects.get(pk=factura_id)
    requests.post("https://api.emailer.example/send", json={"n": factura.numero}, timeout=5)


@shared_task(acks_late=True)
def recalcular_totales_cliente(cliente_id):
    total = 0
    for factura in Factura.objects.filter(cliente_id=cliente_id):
        total += factura.importe
    return total
