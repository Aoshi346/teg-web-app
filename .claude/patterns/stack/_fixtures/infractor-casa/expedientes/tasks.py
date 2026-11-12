"""ANTIPATRÓN A PROPÓSITO — banco de pruebas del checker. No copiar nada de aquí."""
import requests
from celery import shared_task


@shared_task
def avisar_apertura_expediente(expediente_id):
    """be-http-timeout: `requests` sin `timeout=` espera para siempre.

    Es la comprobación de mayor valor para el trabajo nocturno, y no es teórica: en el backend de
    referencia, 37 de 39 llamadas salientes no lo llevaban, y existe un script escrito a mano para
    purgar la cola que eso acabó produciendo.
    """
    requests.post("https://portal.example/api/avisos", json={"id": expediente_id})
