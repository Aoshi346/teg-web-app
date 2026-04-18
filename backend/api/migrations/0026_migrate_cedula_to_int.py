# Migration A2: parse existing cedula strings into (nationality, cedula_int), then
# drop the old cedula CharField, rename cedula_int → cedula, and add the
# UniqueConstraint.
#
# Regex used: ^([VEP])?[-\s.]?(\d+)$  (case-insensitive after upper())
# Handles:
#   "V-30243721"  → nationality='V', cedula=30243721
#   "E-30243721"  → nationality='E', cedula=30243721
#   "P-30243721"  → nationality='P', cedula=30243721
#   "30243721"    → nationality='V' (default), cedula=30243721
#   "v 30243721"  → nationality='V', cedula=30243721  (space separator)
#   "30.243.721"  → strips dots → "30243721", nationality='V', cedula=30243721
# Rejects (leaves cedula_int=None, logs via print):
#   "" / None / whitespace → skipped silently
#   Anything else not matching the pattern

import re

from django.db import migrations, models

CEDULA_RE = re.compile(r'^([VEP])?[-\s]?(\d+)$', re.IGNORECASE)


def forward(apps, schema_editor):
    """
    Recorre todos los usuarios y parsea el campo cedula (CharField) al par
    (nationality, cedula_int). Filas que no coinciden con el patrón se dejan
    con cedula_int=None para que un administrador las corrija manualmente.
    El reverse es noop porque no es posible reconstruir exactamente el string
    original una vez que se borra la columna vieja.
    """
    User = apps.get_model('api', 'User')
    for u in User.objects.all():
        raw = u.cedula  # old CharField value
        if not raw or not str(raw).strip():
            continue
        normalized = str(raw).strip().upper().replace('.', '')
        match = CEDULA_RE.match(normalized)
        if match:
            prefix, digits = match.group(1), match.group(2)
            u.nationality = prefix if prefix else 'V'
            u.cedula_int = int(digits)
            u.save()
        else:
            print(
                f"[cedula migration] Unparseable cedula for user id={u.pk}: "
                f"{raw!r} — left null"
            )


class Migration(migrations.Migration):

    dependencies = [
        ('api', '0025_add_nationality_and_cedula_int'),
    ]

    operations = [
        migrations.RunPython(forward, migrations.RunPython.noop),
        migrations.RemoveField(
            model_name='user',
            name='cedula',
        ),
        migrations.RenameField(
            model_name='user',
            old_name='cedula_int',
            new_name='cedula',
        ),
        migrations.AlterField(
            model_name='user',
            name='cedula',
            field=models.PositiveIntegerField(
                null=True,
                blank=True,
                help_text='Numeric-only cédula/ID number',
            ),
        ),
        migrations.AddConstraint(
            model_name='user',
            constraint=models.UniqueConstraint(
                condition=models.Q(cedula__isnull=False),
                fields=('nationality', 'cedula'),
                name='unique_nationality_cedula',
            ),
        ),
    ]
