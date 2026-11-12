"""Rutas del proyecto — con la de salud, que es la que hace que el sistema se pueda vigilar solo."""
from django.http import JsonResponse
from django.urls import include, path
from rest_framework.routers import DefaultRouter

from expedientes.views import ExpedienteViewSet

router = DefaultRouter()
router.register("expedientes", ExpedienteViewSet, basename="expedientes")


def healthz(request):
    """Sin auth y sin tocar la base de datos: responde si el PROCESO está vivo.

    Es lo que consultan el balanceador, el `condition: service_healthy` del compose y la alerta.
    Si además quieres saber si la base responde, ese es otro endpoint (`readyz`) y otra pregunta:
    mezclarlos hace que un hipo de la base tire el proceso entero.
    """
    return JsonResponse({"ok": True})


urlpatterns = [
    path("healthz/", healthz, name="healthz"),
    path("api/", include(router.urls)),
]
