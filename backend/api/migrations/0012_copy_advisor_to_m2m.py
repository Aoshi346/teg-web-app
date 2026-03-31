"""Data migration: copy advisor CharField text into the advisors M2M table.

For any Project row where `advisor` is non-empty AND the M2M `advisors` is
empty, we try to find a User with role='Tutor' whose full_name matches the
advisor text.  If found, we add that user to the M2M relationship.
"""
from django.db import migrations


def copy_advisor_to_m2m(apps, schema_editor):
    Project = apps.get_model("api", "Project")
    User = apps.get_model("api", "User")

    for project in Project.objects.all():
        # Skip if already has M2M advisors or advisor text is blank
        if project.advisors.exists() or not project.advisor.strip():
            continue

        advisor_text = project.advisor.strip()
        # Try exact match on full_name
        tutor = User.objects.filter(role="Tutor", full_name__iexact=advisor_text).first()
        if tutor:
            project.advisors.add(tutor)


def reverse_noop(apps, schema_editor):
    """Reverse is a no-op; M2M entries are kept."""
    pass


class Migration(migrations.Migration):

    dependencies = [
        ("api", "0011_project_advisors_comment"),
    ]

    operations = [
        migrations.RunPython(copy_advisor_to_m2m, reverse_noop),
    ]
