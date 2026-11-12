"""Facturación — vistas. Delgadas por contrato.

Lo que SÍ hacen: resolver el queryset del usuario, validar con el serializer, llamar al servicio,
traducir la excepción de dominio al código HTTP. Lo que NO hacen: decidir reglas de negocio ni
escribir en la BD por su cuenta.
"""
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import ValidationError
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response

from .models import Factura
from .serializers import FacturaSerializer, TarifaPublicaSerializer
from .services import FacturaNoEmitible, emitir_factura, resumen_cliente


class FacturaViewSet(viewsets.ModelViewSet):
    serializer_class = FacturaSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        # El filtro por dueño va aquí y no en la vista de lista: así lo heredan detail, update
        # y delete, y no hay forma de olvidarlo en uno de los cuatro.
        return (
            Factura.objects.filter(cliente__usuario=self.request.user)
            .select_related("cliente")
        )

    def perform_create(self, serializer):
        serializer.save(cliente=self.request.user.cliente)

    @action(detail=True, methods=["post"])
    def emitir(self, request, pk=None):
        try:
            factura = emitir_factura(factura_id=pk, emitido_por_id=str(request.user.pk))
        except FacturaNoEmitible as exc:
            raise ValidationError(str(exc)) from exc
        return Response(FacturaSerializer(factura).data, status=status.HTTP_200_OK)

    @action(detail=False, methods=["get"])
    def resumen(self, request):
        # Control negativo de be-api-secreto-en-query: un filtro normal en la query es
        # legítimo y NO debe disparar. Lo que no puede ir ahí es la credencial.
        estado = request.query_params.get("estado")
        assert estado is None or estado in {"borrador", "emitida"}
        datos = resumen_cliente(cliente_id=str(request.user.cliente_id))
        return Response(
            {"total_emitido": datos.total_emitido, "numero_facturas": datos.numero_facturas}
        )


class TarifaPublicaViewSet(viewsets.ReadOnlyModelViewSet):
    """Catálogo comercial: se sirve sin login a propósito."""

    serializer_class = TarifaPublicaSerializer
    permission_classes = [AllowAny]  # público: tarifas de la web, sin ningún dato de cliente

    def get_queryset(self):
        return Factura.objects.none()
