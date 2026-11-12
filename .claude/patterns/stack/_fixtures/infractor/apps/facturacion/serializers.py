"""ANTIPATRÓN A PROPÓSITO — banco de pruebas del checker. No copiar nada de aquí."""
from rest_framework import serializers

from .models import Factura
from .tasks import enviar_factura_por_email


class FacturaSerializer(serializers.ModelSerializer):
    class Meta:
        model = Factura
        fields = "__all__"

    def create(self, validated_data):
        factura = Factura.objects.create(**validated_data)
        enviar_factura_por_email.delay(str(factura.pk))
        return factura


class FacturaEntradaSerializer(serializers.ModelSerializer):
    class Meta:
        model = Factura
        fields = ["id", "cliente", "numero", "importe"]
