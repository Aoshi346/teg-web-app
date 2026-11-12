"""Backfill del número de factura. Reversible: si el deploy se revierte, la migración también."""
from django.db import migrations


def rellenar_numero(apps, schema_editor):
    Factura = apps.get_model("facturacion", "Factura")
    pendientes = Factura.objects.filter(numero="").order_by("pk").iterator(chunk_size=500)
    for i, factura in enumerate(pendientes, start=1):
        Factura.objects.filter(pk=factura.pk).update(numero=f"F-{i:06d}")


def vaciar_numero(apps, schema_editor):
    Factura = apps.get_model("facturacion", "Factura")
    Factura.objects.filter(numero__startswith="F-").update(numero="")


class Migration(migrations.Migration):
    dependencies = [("facturacion", "0001_initial")]

    operations = [
        migrations.RunPython(rellenar_numero, vaciar_numero),
    ]
