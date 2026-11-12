"""be-obs-healthcheck: ninguna ruta de salud en todo el proyecto.

Sin una ruta que responda 200 sin tocar la base, saber si el proceso está vivo exige que una
persona lo mire. Ni el balanceador, ni el `condition: service_healthy` del compose, ni una alerta
pueden hacerlo por su cuenta.
"""
from django.urls import include, path
from rest_framework.routers import DefaultRouter

from expedientes.views import ExpedienteViewSet

router = DefaultRouter()
router.register("expedientes", ExpedienteViewSet, basename="expedientes")

urlpatterns = [path("api/", include(router.urls))]
