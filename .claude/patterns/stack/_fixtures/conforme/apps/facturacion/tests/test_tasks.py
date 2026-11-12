"""El test que la regla `be-celery-ackslate-idempotente` exige que exista."""
import pytest

from apps.facturacion.tasks import enviar_factura_por_email


@pytest.mark.django_db
def test_enviar_factura_por_email_es_idempotente(factura_emitida, emailer_falso):
    """acks_late=True ⇒ Celery puede re-entregar la tarea. Correrla dos veces debe dejar el mismo
    estado final y mandar UN solo correo."""
    assert enviar_factura_por_email(str(factura_emitida.pk)) == "enviada"
    assert enviar_factura_por_email(str(factura_emitida.pk)) == "ya-enviada"

    factura_emitida.refresh_from_db()
    assert factura_emitida.enviada_en is not None
    assert emailer_falso.call_count == 1
