"""ANTIPATRÓN A PROPÓSITO — banco de pruebas del checker. No copiar nada de aquí."""
from django.db import transaction
from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.permissions import AllowAny
from rest_framework.response import Response

from .models import Factura
from .serializers import FacturaSerializer
from .tasks import enviar_factura_por_email


class FacturaViewSet(viewsets.ModelViewSet):
    queryset = Factura.objects.all()
    serializer_class = FacturaSerializer
    permission_classes = [AllowAny]

    # be-view-action-multiverbo: el mismo camino consulta y cobra
    @action(detail=True, methods=["get", "post"])
    def cobrar(self, request, pk=None):
        # be-api-secreto-en-query: la credencial acaba en el log de acceso
        token = request.query_params.get("token")
        if request.method == "GET":
            return Response({"estado": "pendiente", "token_ok": bool(token)})
        return Response({"cobrado": True})

    @action(detail=True, methods=["post"])
    def emitir(self, request, pk=None):
        factura = self.get_object()
        if factura.estado != "borrador":
            return Response({"error": "ya emitida"}, status=400)
        with transaction.atomic():
            factura.estado = "emitida"
            factura.save()
            enviar_factura_por_email.delay(str(factura.pk))
        return Response(FacturaSerializer(factura).data)
