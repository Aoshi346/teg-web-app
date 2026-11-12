"""ANTIPATRÓN A PROPÓSITO — banco de pruebas del checker. No copiar nada de aquí."""
from django.db import migrations


def rellenar(apps, schema_editor):
    Factura = apps.get_model("facturacion", "Factura")
    Factura.objects.filter(numero=None).update(numero="SIN-NUMERO")


class Migration(migrations.Migration):
    dependencies = [("facturacion", "0001_initial")]

    operations = [
        migrations.RunPython(rellenar),
    ]
