"""Señales — SOLO receivers, y todo efecto hacia fuera esperando al COMMIT.

Las dos reglas de esta capa están aquí en su forma correcta:

`be-sig-efecto-sin-on-commit` — un receiver corre DENTRO de la transacción de quien guardó. Si la
vista que llamó a `form.save()` abrió un `atomic()` (y la vista CRUD genérica de un proyecto así
lo abre para todas sus tablas), encolar aquí significa que el worker puede coger la tarea antes
del COMMIT y hacer `get(id=…)` sobre una fila que todavía no existe — o que el aviso salga de una
operación que acaba en rollback. `on_commit` es la diferencia.

`be-sig-logica-de-negocio` — aquí no hay ninguna función que no sea un receiver. La lógica está en
`services.py`, así que la puede llamar también una task, un comando o un test. Una función de
negocio definida en este fichero solo sería alcanzable desde un `post_save`.
"""
from functools import partial

from django.db import transaction
from django.db.models.signals import post_save
from django.dispatch import receiver

from .models import Expediente
from .tasks import avisar_apertura_expediente


@receiver(post_save, sender=Expediente, dispatch_uid="expedientes.avisar_apertura")
def avisar_apertura(sender, instance, created, **kwargs):
    if not created:
        return
    # `partial` y no `lambda`: dentro de un bucle, el lambda captura la VARIABLE y todas las
    # llamadas acaban usando el último valor. Con partial se congela el argumento aquí.
    transaction.on_commit(partial(avisar_apertura_expediente.delay, str(instance.pk)))
