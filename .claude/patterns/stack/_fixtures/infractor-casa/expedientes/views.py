"""ANTIPATRÓN A PROPÓSITO — banco de pruebas del checker. No copiar nada de aquí."""
from rest_framework import viewsets

from .models import Expediente
from .serializers import ExpedienteSerializer


class ExpedienteViewSet(viewsets.ModelViewSet):
    """be-view-base-de-casa: hereda de DRF y no de `core.api.BaseViewSet`.

    La base de casa existe y resuelve el filtrado por dueño en un punto. Esta vista se la salta,
    así que vuelve a haber una oportunidad de olvidar el filtro — y aquí el olvido significa que
    un cliente ve las filas de otro.
    """

    serializer_class = ExpedienteSerializer

    def get_queryset(self):
        return Expediente.objects.all()
