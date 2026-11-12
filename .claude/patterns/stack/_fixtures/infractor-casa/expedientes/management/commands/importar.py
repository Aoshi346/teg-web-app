"""ANTIPATRÓN A PROPÓSITO — banco de pruebas del checker. No copiar nada de aquí."""
import csv

from django.core.management.base import BaseCommand

from expedientes.models import Expediente


class Command(BaseCommand):
    """be-val-escritura-sin-full-clean: escribe sin validar nada.

    El formulario del proyecto valida muy bien, pero esta no es esa puerta. Aquí entra cualquier
    valor: un `estado` que no está en `choices`, una referencia de 900 caracteres, un importe
    negativo. Y como el modelo tampoco tiene constraints, la base tampoco lo para.
    """

    def handle(self, *args, **opciones):
        with open("expedientes.csv", encoding="utf-8") as fichero:
            for fila in csv.DictReader(fichero):
                Expediente.objects.create(referencia=fila["referencia"], estado=fila["estado"])
