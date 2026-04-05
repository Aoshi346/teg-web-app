from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('api', '0021_add_semester_date_range'),
    ]

    operations = [
        migrations.CreateModel(
            name='SessionLog',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('session_key', models.CharField(max_length=40, unique=True)),
                ('device', models.CharField(blank=True, default='', max_length=100)),
                ('browser', models.CharField(blank=True, default='', max_length=100)),
                ('ip_address', models.GenericIPAddressField(blank=True, null=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('last_active_at', models.DateTimeField(auto_now=True)),
                ('is_active', models.BooleanField(default=True)),
                ('user_agent', models.TextField(blank=True, null=True)),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='session_logs', to='api.user')),
            ],
            options={
                'verbose_name': 'Session Log',
                'verbose_name_plural': 'Session Logs',
                'ordering': ['-last_active_at'],
            },
        ),
    ]
