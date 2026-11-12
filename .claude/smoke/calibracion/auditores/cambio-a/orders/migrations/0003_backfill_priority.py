from django.db import migrations


def backfill(apps, schema_editor):
    Order = apps.get_model("orders", "Order")
    Order.objects.filter(total__gte=200).update(priority=2)
    Order.objects.filter(total__lt=200).update(priority=1)


class Migration(migrations.Migration):

    dependencies = [
        ("orders", "0002_order_priority"),
    ]

    operations = [
        migrations.RunPython(backfill),
    ]
