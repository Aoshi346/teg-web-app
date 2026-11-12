"""ANTIPATRÓN A PROPÓSITO — las dos infracciones de la capa de señales."""
from django.db.models.signals import post_save
from django.dispatch import receiver

from .models import Expediente
from .tasks import avisar_apertura_expediente


def crear_nota_de_apertura(expediente):
    """be-sig-logica-de-negocio: no es un receiver, escribe en la BD y vive en signals.py.

    Solo se la puede llamar desde el ciclo post_save. Ni una task, ni un comando, ni un test la
    alcanzan — así que el día que haya que abrir expedientes en batch, alguien reescribe esta
    misma lógica al lado y a partir de ahí hay dos versiones que divergen.
    """
    expediente.notas.create(texto="expediente abierto")


@receiver(post_save, sender=Expediente)
def al_guardar(sender, instance, created, **kwargs):
    """be-sig-efecto-sin-on-commit: encola DENTRO de la transacción de quien guardó.

    Un receiver no abre transacción propia: corre dentro de la de la vista que llamó a save(). El
    broker entrega el mensaje en milisegundos y el COMMIT puede tardar más, así que el worker hace
    `get(id=...)` y no encuentra la fila. Peor: si la transacción acaba en rollback, el aviso ya
    salió y el expediente no existe.
    """
    if not created:
        return
    crear_nota_de_apertura(instance)
    avisar_apertura_expediente.delay(str(instance.pk))
