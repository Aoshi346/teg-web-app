"""
Tests for the prune_notifications management command.

Phase RED — backend/api/management/commands/prune_notifications.py does not
exist yet. All tests are expected to fail with CommandError (unknown command).

Business rules under test:
- Default retention window is 90 days of read notifications.
- Only rows where read_at IS NOT NULL AND read_at < cutoff are deleted.
- Rows with read_at IS NULL (unread) are NEVER pruned regardless of age.
  Note: keeping unread rows forever is a hard rule — users must be able to
  see their unread notifications even if they never open the app.
- --days N overrides the default cutoff.
- --dry-run prints the would-delete count without deleting any rows.
"""

import pytest
from io import StringIO
from datetime import timedelta

from django.contrib.auth import get_user_model
from django.core.management import call_command
from django.utils import timezone

User = get_user_model()


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_user(role="Estudiante", suffix=""):
    counter = getattr(_make_user, "_counter", 0) + 1
    _make_user._counter = counter
    return User.objects.create_user(
        email=f"prune_{suffix}{counter}@test.local",
        password="TestPass123!",
        first_name="Prune",
        last_name="Test",
        role=role,
        status="active",
    )


def _make_notification(recipient, *, read_at=None, created_at=None):
    """
    Crea una Notification con timestamps controlados para los tests de poda.
    Django no permite asignar auto_now_add directamente, así que usamos
    update() después de crear la fila.
    """
    from api.models import Notification

    notif = Notification.objects.create(
        recipient=recipient,
        kind="comment_added",
        title="Test notification",
        body="Test body",
        read_at=read_at,
    )
    # Override auto_now_add created_at if provided
    if created_at is not None:
        Notification.objects.filter(pk=notif.pk).update(created_at=created_at)
        notif.refresh_from_db()
    return notif


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


class TestPruneNotificationsCommand:
    @pytest.mark.django_db
    def test_default_days_is_90_prunes_old_read_rows(self):
        """Rows with read_at older than 90 days are deleted by default."""
        from api.models import Notification

        user = _make_user(suffix="default")
        old_read_at = timezone.now() - timedelta(days=91)
        notif = _make_notification(user, read_at=old_read_at)

        call_command("prune_notifications", stdout=StringIO())

        assert not Notification.objects.filter(pk=notif.pk).exists()

    @pytest.mark.django_db
    def test_recent_read_rows_are_kept(self):
        """Rows with read_at newer than the cutoff (e.g. 10 days ago) are kept."""
        from api.models import Notification

        user = _make_user(suffix="recent")
        recent_read_at = timezone.now() - timedelta(days=10)
        notif = _make_notification(user, read_at=recent_read_at)

        call_command("prune_notifications", stdout=StringIO())

        assert Notification.objects.filter(pk=notif.pk).exists()

    @pytest.mark.django_db
    def test_unread_rows_are_never_pruned(self):
        """
        Unread notifications (read_at IS NULL) must NEVER be deleted,
        regardless of how old their created_at is. This is a hard business rule:
        users must be able to see unread notifications even if they were created
        years ago and never opened the app.
        """
        from api.models import Notification

        user = _make_user(suffix="unread")
        ancient_created_at = timezone.now() - timedelta(days=365)
        # Note: unread (read_at=None) but very old created_at
        notif = _make_notification(user, read_at=None, created_at=ancient_created_at)

        call_command("prune_notifications", stdout=StringIO())

        assert Notification.objects.filter(pk=notif.pk).exists()

    @pytest.mark.django_db
    def test_custom_days_flag_overrides_default(self):
        """--days 7 prunes rows read more than 7 days ago."""
        from api.models import Notification

        user = _make_user(suffix="custom")
        # 20 days ago — within the default 90-day window but outside --days 7
        read_at = timezone.now() - timedelta(days=20)
        notif = _make_notification(user, read_at=read_at)

        call_command("prune_notifications", "--days", "7", stdout=StringIO())

        assert not Notification.objects.filter(pk=notif.pk).exists()

    @pytest.mark.django_db
    def test_custom_days_flag_keeps_rows_within_window(self):
        """--days 7 keeps rows read fewer than 7 days ago."""
        from api.models import Notification

        user = _make_user(suffix="within")
        recent_read_at = timezone.now() - timedelta(days=3)
        notif = _make_notification(user, read_at=recent_read_at)

        call_command("prune_notifications", "--days", "7", stdout=StringIO())

        assert Notification.objects.filter(pk=notif.pk).exists()

    @pytest.mark.django_db
    def test_dry_run_does_not_delete_and_prints_count(self):
        """--dry-run reports the would-delete count via stdout but deletes nothing."""
        from api.models import Notification

        user = _make_user(suffix="dryrun")
        old_read_at = timezone.now() - timedelta(days=100)
        notif = _make_notification(user, read_at=old_read_at)

        out = StringIO()
        call_command("prune_notifications", "--dry-run", stdout=out)

        # Row must still exist
        assert Notification.objects.filter(pk=notif.pk).exists()

        # Output must mention "would delete"
        output = out.getvalue().lower()
        assert "would delete" in output or "would" in output
