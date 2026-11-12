"""Servicios — y el dueño se asigna aquí, explícitamente.

`owner` es el campo por el que filtra el scoping por usuario. En el arquetipo server-rendered lo
pone el formulario base; cualquier escritor que NO sea ese formulario tiene que ponerlo a mano, y
si se olvida la fila se crea, existe en la base de datos y no aparece en la pantalla de nadie sin
permiso de organización. No falla nada: simplemente el registro es invisible.
"""
from django.db import transaction

from .models import Estado, Expediente


class ErrorDeExpediente(Exception):
    """Base del dominio. La vista decide qué significa en HTTP."""


@transaction.atomic
def abrir_expediente(*, referencia: str, titulo: str, responsable_id: int, usuario) -> Expediente:
    expediente = Expediente.objects.create(
        referencia=referencia,
        titulo=titulo,
        responsable_id=responsable_id,
        estado=Estado.ABIERTO,
        owner=usuario,          # sin esto la fila nace huérfana e invisible
        created_by=usuario,
    )
    return expediente
