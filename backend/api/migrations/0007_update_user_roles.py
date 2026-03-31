from django.db import migrations


def forwards(apps, schema_editor):
    User = apps.get_model("api", "User")
    User.objects.filter(role="Admin").update(role="Administrador")
    User.objects.filter(role="Profesor").update(role="Tutor")


def backwards(apps, schema_editor):
    User = apps.get_model("api", "User")
    User.objects.filter(role="Administrador").update(role="Admin")
    User.objects.filter(role="Tutor").update(role="Profesor")


class Migration(migrations.Migration):
    dependencies = [
        ("api", "0006_alter_attachedfile_file"),
    ]

    operations = [
        migrations.RunPython(forwards, backwards),
    ]
