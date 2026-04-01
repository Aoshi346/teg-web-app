"""
Normalize User model fields:
- Convert phone from IntegerField(null) to CharField(blank, default='')
- Convert semester from IntegerField(null) to CharField(blank, default='')
- Add cedula CharField
- Restore first_name/last_name from AbstractUser (were set to None)
- Migrate full_name data into first_name/last_name
- Remove full_name column
"""

from django.db import migrations, models


def migrate_user_data(apps, schema_editor):
    """Split full_name into first_name/last_name, convert int fields to str."""
    User = apps.get_model('api', 'User')
    for user in User.objects.all():
        # Migrate full_name → first_name + last_name
        full = user.full_name or ''
        if full:
            parts = full.strip().split(' ', 1)
            user.first_name = parts[0]
            user.last_name = parts[1] if len(parts) > 1 else ''

        # Convert integer phone to string
        if user.phone_new == '' and user.phone_old is not None:
            user.phone_new = str(user.phone_old)

        # Convert integer semester to string
        if user.semester_new == '' and user.semester_old is not None:
            val = user.semester_old
            user.semester_new = str(val) if val else ''

        user.save()


class Migration(migrations.Migration):

    dependencies = [
        ('api', '0019_semester_is_active_alter_project_period'),
    ]

    operations = [
        # Step 1: Add new fields (first_name, last_name, cedula, new phone/semester as temp names)
        migrations.AddField(
            model_name='user',
            name='cedula',
            field=models.CharField(blank=True, default='', help_text='Student/staff ID number', max_length=20),
        ),
        # Rename old int fields to *_old before adding new CharField versions
        migrations.RenameField(
            model_name='user',
            old_name='phone',
            new_name='phone_old',
        ),
        migrations.RenameField(
            model_name='user',
            old_name='semester',
            new_name='semester_old',
        ),
        # Add new CharField versions
        migrations.AddField(
            model_name='user',
            name='phone_new',
            field=models.CharField(blank=True, default='', help_text='e.g. +58-414-1234567', max_length=20),
        ),
        migrations.AddField(
            model_name='user',
            name='semester_new',
            field=models.CharField(blank=True, default='', help_text='e.g. 9no, 10mo, N/A', max_length=10),
        ),
        # Add first_name/last_name (AbstractUser defines them but old model set them to None)
        migrations.AddField(
            model_name='user',
            name='first_name',
            field=models.CharField(blank=True, default='', max_length=150),
        ),
        migrations.AddField(
            model_name='user',
            name='last_name',
            field=models.CharField(blank=True, default='', max_length=150),
        ),

        # Step 2: Migrate data
        migrations.RunPython(migrate_user_data, migrations.RunPython.noop),

        # Step 3: Remove old fields and rename new ones
        migrations.RemoveField(model_name='user', name='phone_old'),
        migrations.RemoveField(model_name='user', name='semester_old'),
        migrations.RemoveField(model_name='user', name='full_name'),
        migrations.RenameField(model_name='user', old_name='phone_new', new_name='phone'),
        migrations.RenameField(model_name='user', old_name='semester_new', new_name='semester'),
    ]
