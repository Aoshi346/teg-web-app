from datetime import timedelta

from django.core.management.base import BaseCommand
from django.utils import timezone


class Command(BaseCommand):
    help = "Delete read Notification rows older than N days (default 90). Unread rows are never deleted."

    def add_arguments(self, parser):
        parser.add_argument(
            "--days",
            type=int,
            default=90,
            help="Retention window in days (default: 90). Read notifications older than this are deleted.",
        )
        parser.add_argument(
            "--dry-run",
            action="store_true",
            default=False,
            help="Print the number of rows that would be deleted without actually deleting them.",
        )

    def handle(self, *args, **options):
        """
        Elimina notificaciones leídas cuyo read_at sea anterior al umbral de retención.

        Regla de negocio:
        - Solo se eliminan filas donde read_at IS NOT NULL (notificaciones leídas).
        - Las filas con read_at IS NULL (no leídas) NUNCA se eliminan, sin importar su antigüedad.
        - El umbral por defecto es 90 días desde el momento de ejecución.
        - Con --days N se puede ajustar la ventana de retención.
        - Con --dry-run se imprime el conteo sin ejecutar el DELETE.
        """
        from api.models import Notification

        days = options["days"]
        dry_run = options["dry_run"]
        cutoff = timezone.now() - timedelta(days=days)

        qs = Notification.objects.filter(
            read_at__isnull=False,
            read_at__lt=cutoff,
        )

        count = qs.count()

        if dry_run:
            self.stdout.write(
                self.style.WARNING(f"Would delete {count} notifications (dry run, --days={days}).")
            )
        else:
            qs.delete()
            self.stdout.write(
                self.style.SUCCESS(f"Deleted {count} notifications (--days={days}).")
            )
