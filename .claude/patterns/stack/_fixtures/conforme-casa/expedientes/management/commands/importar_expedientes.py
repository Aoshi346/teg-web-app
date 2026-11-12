"""Importación masiva — la OTRA puerta, y por eso valida.

El formulario del proyecto es excelente y es la única puerta con validación... del formulario.
Todo lo que entra por `create`, `update`, `bulk_create` o un comando como este entra sin verificar
nada, y en un producto cuyo valor es el registro auditable eso se paga en filas medio construidas.

Dos cerraduras, no una:
  - `full_clean()` aquí, que aplica `choices`, `max_length` y los validadores del modelo;
  - la `CheckConstraint` del modelo, que aplica la invariante venga el dato de donde venga —
    también del `manage.py shell` de dentro de seis meses.
"""
import csv

from django.core.exceptions import ValidationError
from django.core.management.base import BaseCommand
from django.db import transaction

from expedientes.models import Estado, Expediente


class Command(BaseCommand):
    help = "Importa expedientes desde un CSV, validando fila a fila."

    def add_arguments(self, parser):
        parser.add_argument("ruta")
        parser.add_argument("--owner-id", type=int, required=True)

    @transaction.atomic
    def handle(self, *args, **opciones):
        rechazadas = 0
        with open(opciones["ruta"], encoding="utf-8") as fichero:
            for numero, fila in enumerate(csv.DictReader(fichero), start=2):
                expediente = Expediente(
                    referencia=fila["referencia"],
                    titulo=fila.get("titulo", ""),
                    estado=fila.get("estado", Estado.BORRADOR),
                    owner_id=opciones["owner_id"],
                )
                try:
                    expediente.full_clean()
                except ValidationError as exc:
                    rechazadas += 1
                    self.stderr.write(f"fila {numero}: {exc.message_dict}")
                    continue
                expediente.save()
        self.stdout.write(f"importación terminada · {rechazadas} fila(s) rechazadas")
