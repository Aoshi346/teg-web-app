from django.db import migrations, models

from ._teg_backfill import compute_teg_state

NEW_STATE_CHOICES = [
    ('pending_review_1', 'Pendiente 1ra revisión'),
    ('pending_review_2', 'Pendiente 2da revisión'),
    ('pending_defense',  'Pendiente defensa oral'),
    ('pending_articulo', 'Pendiente Artículo'),
    ('pending_entrega',  'Pendiente Entrega Ejemplar'),
    ('pending_defensa',  'Pendiente Defensa Oral'),
    ('approved',         'Aprobado'),
    ('failed_final',     'Reprobado (sin más intentos)'),
]


def backfill_teg_state(apps, schema_editor):
    Project = apps.get_model('api', 'Project')
    for project in Project.objects.filter(project_type='tesis').iterator():
        new_state = compute_teg_state(
            status=project.status,
            stage1_passed=project.stage1_passed,
        )
        if project.state != new_state:
            project.state = new_state
            project.save(update_fields=['state'])


def reverse_backfill(apps, schema_editor):
    # Irreversible — original `state` for TEG rows was meaningless. No-op.
    pass


class Migration(migrations.Migration):
    dependencies = [
        ('api', '0034_notification'),
    ]

    operations = [
        migrations.AlterField(
            model_name='project',
            name='state',
            field=models.CharField(
                max_length=20,
                choices=NEW_STATE_CHOICES,
                default='pending_review_1',
                db_index=True,
                help_text='Estado del ciclo de vida del proyecto. Autogestionado por Evaluation.',
            ),
        ),
        migrations.AlterField(
            model_name='stateoverride',
            name='from_state',
            field=models.CharField(max_length=20, choices=NEW_STATE_CHOICES),
        ),
        migrations.AlterField(
            model_name='stateoverride',
            name='to_state',
            field=models.CharField(max_length=20, choices=NEW_STATE_CHOICES),
        ),
        migrations.RunPython(backfill_teg_state, reverse_backfill),
    ]
