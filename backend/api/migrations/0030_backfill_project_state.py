"""
Data migration: derive Project.state for existing PTEG rows from legacy
status + failed_attempts + Evaluation history. TEG rows are skipped.
"""

from django.db import migrations


def backfill(apps, schema_editor):
    Project = apps.get_model('api', 'Project')
    Evaluation = apps.get_model('api', 'Evaluation')

    # Importamos la regla compartida para mantener una única fuente de verdad
    # entre la migración y sus tests. El import vive dentro de la función para
    # evitar ejecutar módulos `api.*` al momento de cargar migraciones.
    from api.migrations._state_backfill_logic import derive_state

    for p in Project.objects.filter(project_type='proyecto').iterator():
        evals = list(Evaluation.objects.filter(project=p))
        p.state = derive_state(p, evals)
        p.save(update_fields=['state'])

    # At this point in migration history the only valid kind is 'review'.
    # The AddField default covers any rows inserted after 0029, but we run
    # this sweep unconditionally in case a prior data load bypassed the default.
    Evaluation.objects.update(kind='review')


def reverse(apps, schema_editor):
    """Reverse is a no-op — state column persists but loses derived values."""


class Migration(migrations.Migration):
    dependencies = [
        ('api', '0029_project_state_evaluation_kind'),
    ]

    operations = [
        migrations.RunPython(backfill, reverse),
    ]
