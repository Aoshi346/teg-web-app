"""Expedientes — la capa de servicio de este proyecto, que se llama utils.py.
# pattern-layer: services

Prueba de que la degradación del NOMBRE no degrada la REGLA: el fichero no se llama `services.py`
y aun así `be-svc-sin-drf` dispara aquí dos veces —el import de HTTP y el parámetro `request`—
porque el marcador declara la capa. Sin el marcador, este fichero pasaría en silencio y la parte
que de verdad importa (que la lógica sea invocable sin una petición HTTP) no se comprobaría nunca.
"""
from django.shortcuts import get_object_or_404   # be-svc-sin-drf: import de HTTP

from .models import Expediente


def cerrar_expediente(request, expediente_id):   # be-svc-sin-drf: recibe `request`
    expediente = get_object_or_404(Expediente, pk=expediente_id)
    expediente.estado = "cerrado"
    expediente.updated_by = request.user
    expediente.save()
    return expediente
