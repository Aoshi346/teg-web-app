"""Correcto a propósito: las infracciones de este fixture están en otras capas."""
from rest_framework import serializers

from .models import Expediente


class ExpedienteSerializer(serializers.ModelSerializer):
    class Meta:
        model = Expediente
        fields = ["id", "referencia", "estado", "importe", "owner"]
        read_only_fields = ["id", "owner"]
