"""Facturación — servicios. AQUÍ vive la lógica de negocio.

Regla de la capa: este módulo no sabe que existe HTTP. No importa DRF, no recibe `request` y no
devuelve `Response`. Por eso lo puede llamar igual una vista, una task nocturna, un comando de
`manage.py` o un test — que es exactamente lo que hace posible dejar trabajo corriendo sin nadie
delante. Ver `.claude/patterns/stack/backend-servicios.md`.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass
from decimal import Decimal

from django.core.cache import cache
from django.db import transaction
from django.db.models import Count, Sum
from django.utils import timezone

from .models import Factura
from .tasks import enviar_factura_por_email

TTL_RESUMEN_SEGUNDOS = 300


class ErrorDeFacturacion(Exception):
    """Base del dominio. La vista decide qué código HTTP significa cada subclase."""


class FacturaNoEmitible(ErrorDeFacturacion):
    """La factura no está en un estado desde el que se pueda emitir."""


@dataclass(frozen=True)
class ResumenCliente:
    total_emitido: Decimal
    numero_facturas: int


def clave_resumen_cliente(cliente_id: str) -> str:
    """Única fuente de la clave: quien invalide no tiene que recordar el formato."""
    return f"facturacion:resumen:{cliente_id}"


@transaction.atomic
def emitir_factura(*, factura_id: str, emitido_por_id: str) -> Factura:
    """Pasa una factura de borrador a emitida. Idempotente hacia fuera: reintentar lanza
    FacturaNoEmitible en vez de emitir dos veces."""
    factura = Factura.objects.select_for_update().get(pk=factura_id)
    if factura.estado != Factura.Estado.BORRADOR:
        raise FacturaNoEmitible(f"la factura {factura.numero} ya está en estado {factura.estado}")

    factura.estado = Factura.Estado.EMITIDA
    factura.emitida_en = timezone.now()
    factura.save(update_fields=["estado", "emitida_en", "actualizada_en"])

    cache.delete(clave_resumen_cliente(str(factura.cliente_id)))
    # on_commit y no .delay() directo: dentro de atomic el worker puede coger la tarea antes
    # del COMMIT y no encontrar la fila.
    transaction.on_commit(lambda: enviar_factura_por_email.delay(str(factura.pk)))
    return factura


def resumen_cliente(*, cliente_id: str) -> ResumenCliente:
    clave = clave_resumen_cliente(cliente_id)
    cacheado = cache.get(clave)
    if cacheado is not None:
        return ResumenCliente(**cacheado)

    agregado = (
        Factura.objects.filter(cliente_id=cliente_id)
        .exclude(estado=Factura.Estado.BORRADOR)
        .aggregate(total=Sum("importe"), n=Count("id"))
    )
    resumen = ResumenCliente(
        total_emitido=agregado["total"] or Decimal("0.00"),
        numero_facturas=agregado["n"],
    )
    cache.set(clave, asdict(resumen), timeout=TTL_RESUMEN_SEGUNDOS)
    return resumen
