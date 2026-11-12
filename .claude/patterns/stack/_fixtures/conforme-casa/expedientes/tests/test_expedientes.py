"""Tests de la app. El nombre importa: `test_*.py` es lo que encuentra el descubridor.

Un fichero llamado `expedientes_tests.py` con estas mismas funciones **no se ejecuta nunca** —ni
con `manage.py test` (patrón `test*.py`) ni con pytest (`test_*.py` / `*_test.py`)— y no falla
nunca, que es exactamente lo que lo hace peligroso: parece cobertura y no la da.
"""
import pytest
from django.utils import timezone

from core.models import TokenApi
from expedientes.models import Estado, Expediente
from expedientes.services import abrir_expediente


@pytest.mark.django_db
def test_abrir_expediente_asigna_dueno(usuario, equipo):
    """El dueño no es cosmética: es el campo por el que filtra el scoping por usuario."""
    expediente = abrir_expediente(
        referencia="EXP-1", titulo="Alta", responsable_id=equipo.pk, usuario=usuario,
    )
    assert expediente.owner == usuario
    assert expediente.estado == Estado.ABIERTO


@pytest.mark.django_db
def test_expediente_rechaza_estado_invalido(usuario, equipo):
    """La constraint aplica aunque la escritura no pase por el formulario."""
    from django.db.utils import IntegrityError

    with pytest.raises(IntegrityError):
        Expediente.objects.create(
            referencia="EXP-2", estado="inventado", owner=usuario, responsable_id=equipo.pk,
        )


@pytest.mark.django_db
def test_token_caducado_no_autentica(cliente_api):
    """Regresión de la caducidad: el campo existe Y se aplica."""
    TokenApi.objects.create(
        nombre="portal", token_hash="a" * 64, activo=True,
        expiration_date=timezone.now() - timezone.timedelta(days=1),
    )
    respuesta = cliente_api.get("/api/expedientes/", HTTP_X_API_TOKEN="loquesea")
    assert respuesta.status_code == 401
