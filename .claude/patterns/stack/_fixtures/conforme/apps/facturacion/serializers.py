"""Facturación — serializers. Contrato de entrada/salida de la API.

Validan FORMA (tipos, rangos, obligatoriedad). Las reglas que dependen del estado del sistema
("¿se puede emitir esta factura ahora?") viven en `services.py`, no aquí.
"""
from rest_framework import serializers

from .models import Factura


class FacturaSerializer(serializers.ModelSerializer):
    cliente_nombre = serializers.CharField(source="cliente.nombre", read_only=True)

    class Meta:
        model = Factura
        fields = [
            "id",
            "numero",
            "cliente",
            "cliente_nombre",
            "concepto",
            "importe",
            "estado",
            "emitida_en",
            "creada_en",
        ]
        # `cliente` y `estado` los decide el servidor: si fueran escribibles, el cliente podría
        # facturar a nombre de otro o marcarse una factura como pagada desde el payload.
        read_only_fields = ["id", "numero", "cliente", "estado", "emitida_en", "creada_en"]

    def validate_importe(self, value):
        if value <= 0:
            raise serializers.ValidationError("El importe debe ser mayor que cero.")
        return value


class TarifaPublicaSerializer(serializers.ModelSerializer):
    class Meta:
        model = Factura
        fields = ["id", "concepto", "importe"]
