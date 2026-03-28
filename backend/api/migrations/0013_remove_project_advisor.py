"""Schema migration: remove the legacy advisor CharField from Project."""
from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ("api", "0012_copy_advisor_to_m2m"),
    ]

    operations = [
        migrations.RemoveField(
            model_name="project",
            name="advisor",
        ),
    ]
