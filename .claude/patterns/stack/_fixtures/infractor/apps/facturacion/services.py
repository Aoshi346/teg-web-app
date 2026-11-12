"""ANTIPATRÓN A PROPÓSITO — banco de pruebas del checker. No copiar nada de aquí."""
from django.core.cache import cache
from rest_framework.exceptions import ValidationError
from rest_framework.response import Response

from .models import Factura


def clave_resumen(cliente_id):
    return f"resumen:{cliente_id}"


def emitir(request, factura_id):
    factura = Factura.objects.get(pk=factura_id)
    if factura.estado != "borrador":
        raise ValidationError("ya emitida")
    factura.estado = "emitida"
    factura.save()
    cache.set(clave_resumen(str(factura.cliente_id)), {"n": 1}, timeout=None)
    return Response({"ok": True})


def resumen(cliente_id):
    return cache.get(f"resumen:{cliente_id}")
