from django.core.management.base import BaseCommand

class Command(BaseCommand):
    help = "Set academic period for all projects (or by type) to the given value. Default is 2026-02."

    def add_arguments(self, parser):
        parser.add_argument('period', nargs='?', default='2026-02', help='Period in format YYYY-PP (e.g., 2026-02)')
        parser.add_argument('--type', dest='project_type', choices=['proyecto', 'tesis'], default=None,
                            help='Optionally limit to a specific project_type')

    def handle(self, *args, **options):
        period = options['period']
        project_type = options.get('project_type')

        # Import lazily to avoid app registry issues
        from api.models import Project

        qs = Project.objects.all()
        if project_type:
            qs = qs.filter(project_type=project_type)

        updated = qs.update(period=period)
        self.stdout.write(self.style.SUCCESS(f"Updated {updated} projects to period {period}"))
