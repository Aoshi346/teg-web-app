"""Vistas — heredan de la base de casa, así que el filtro por dueño no se puede olvidar."""
from rest_framework import status
from rest_framework.decorators import action
from rest_framework.exceptions import ValidationError
from rest_framework.response import Response

from core.api import BaseViewSet

from .models import Expediente
from .serializers import ExpedienteSerializer
from .services import ErrorDeExpediente, abrir_expediente


class ExpedienteViewSet(BaseViewSet):
    modelo = Expediente
    serializer_class = ExpedienteSerializer

    @action(detail=False, methods=["post"])
    def abrir(self, request):
        try:
            expediente = abrir_expediente(
                referencia=request.data["referencia"],
                titulo=request.data.get("titulo", ""),
                responsable_id=request.data["responsable"],
                usuario=request.user,
            )
        except ErrorDeExpediente as exc:
            # LANZAR, no devolver: el EXCEPTION_HANDLER solo corre para excepciones lanzadas, así
            # que un `return Response(..., status=400)` saldría sin el sobre {"errors": …}.
            raise ValidationError(str(exc)) from exc
        return Response(ExpedienteSerializer(expediente).data, status=status.HTTP_201_CREATED)
