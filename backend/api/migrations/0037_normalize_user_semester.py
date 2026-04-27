import re

from django.db import migrations, models


def _canonical_semester(raw: str) -> str:
    """
    Normaliza el valor de `User.semester` al conjunto canónico
    {'9no', '10mo', 'N/A', ''}. Acepta variantes históricas en formato libre
    (p. ej. '10', 'décimo', 'Noveno', '9°') que existían antes de añadir
    `choices=` al campo.
    """
    if not raw:
        return ''
    text = raw.strip().lower()
    if not text or text in {'n/a', 'na'}:
        return 'N/A'
    if re.search(r'(?:^|\D)10(?:\D|$)|d[eé]cimo', text):
        return '10mo'
    if re.search(r'(?:^|\D)9(?:\D|$)|noveno', text):
        return '9no'
    return ''


def normalize_existing_rows(apps, schema_editor):
    User = apps.get_model('api', 'User')
    for user in User.objects.exclude(semester__in=['9no', '10mo', 'N/A', '']):
        canonical = _canonical_semester(user.semester)
        if canonical != user.semester:
            user.semester = canonical
            user.save(update_fields=['semester'])


def noop_reverse(apps, schema_editor):
    pass


class Migration(migrations.Migration):

    dependencies = [
        ('api', '0036_drop_status_and_stage1'),
    ]

    operations = [
        migrations.RunPython(normalize_existing_rows, noop_reverse),
        migrations.AlterField(
            model_name='user',
            name='semester',
            field=models.CharField(
                blank=True,
                choices=[('9no', '9no'), ('10mo', '10mo'), ('N/A', 'N/A')],
                default='',
                help_text='9no, 10mo, N/A; vacío para roles no-estudiante.',
                max_length=10,
            ),
        ),
    ]
