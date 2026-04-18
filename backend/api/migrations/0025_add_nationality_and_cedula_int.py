# Migration A1: add nationality field and temporary cedula_int column alongside the
# existing cedula CharField. The old column is preserved until migration A2 copies
# the parsed numeric value and drops it.

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('api', '0024_planificacion'),
        ('auth', '0012_alter_user_first_name_max_length'),
    ]

    operations = [
        migrations.AddField(
            model_name='user',
            name='nationality',
            field=models.CharField(
                blank=True,
                choices=[('V', 'Venezolano'), ('E', 'Extranjero'), ('P', 'Pasaporte')],
                default='V',
                max_length=1,
            ),
        ),
        # Temporary column — holds the parsed integer while the old cedula CharField
        # still contains the original string values.
        migrations.AddField(
            model_name='user',
            name='cedula_int',
            field=models.PositiveIntegerField(
                null=True,
                blank=True,
                help_text='Temporary — migrated to cedula in the next migration',
            ),
        ),
    ]
