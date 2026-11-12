"""Contrato de la API. `owner` es de solo lectura: lo decide el servidor, no el payload."""
from rest_framework import serializers

from .models import Expediente


class ExpedienteSerializer(serializers.ModelSerializer):
    class Meta:
        model = Expediente
        fields = ["id", "codigo", "referencia", "titulo", "estado", "importe", "responsable",
                  "owner", "created_at"]
        read_only_fields = ["id", "codigo", "owner", "created_at"]
