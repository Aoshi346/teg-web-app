"""
Tests for the Notification model and /api/notifications/ REST endpoints.

Phase RED — the Notification model and viewset do not yet exist.
All tests are expected to fail during this phase.
"""

import pytest
from django.contrib.auth import get_user_model
from django.utils import timezone
from rest_framework.test import APIClient

User = get_user_model()

NOTIFICATIONS_URL = "/api/notifications/"
UNREAD_COUNT_URL = "/api/notifications/unread_count/"
MARK_ALL_READ_URL = "/api/notifications/mark_all_read/"


def _mark_read_url(notification_id):
    return f"/api/notifications/{notification_id}/mark_read/"


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def user_a(db):
    return User.objects.create_user(
        email="notif_user_a@test.local",
        password="TestPass123!",
        first_name="Alpha",
        last_name="User",
        role="Estudiante",
        status="active",
    )


@pytest.fixture
def user_b(db):
    return User.objects.create_user(
        email="notif_user_b@test.local",
        password="TestPass123!",
        first_name="Beta",
        last_name="User",
        role="Estudiante",
        status="active",
    )


@pytest.fixture
def client_a(user_a):
    client = APIClient()
    client.force_authenticate(user=user_a)
    return client


@pytest.fixture
def client_b(user_b):
    client = APIClient()
    client.force_authenticate(user=user_b)
    return client


def _make_notification(recipient, *, kind="evaluation_received", title="Test", body="Body",
                        payload=None, link_url="", read_at=None):
    """
    Crea un objeto Notification en la base de datos para usar en tests.
    Acepta el mismo conjunto de parámetros que Notification.objects.create.
    """
    from api.models import Notification

    kwargs = {
        "recipient": recipient,
        "kind": kind,
        "title": title,
        "body": body,
        "link_url": link_url,
    }
    if payload is not None:
        kwargs["payload"] = payload
    if read_at is not None:
        kwargs["read_at"] = read_at
    return Notification.objects.create(**kwargs)


# ---------------------------------------------------------------------------
# 1. Notification model basics
# ---------------------------------------------------------------------------


class TestNotificationModel:
    @pytest.mark.django_db
    def test_required_fields_present(self, user_a):
        from api.models import Notification

        n = _make_notification(user_a)
        assert n.pk is not None
        assert hasattr(n, "recipient")
        assert hasattr(n, "kind")
        assert hasattr(n, "title")
        assert hasattr(n, "body")
        assert hasattr(n, "payload")
        assert hasattr(n, "link_url")
        assert hasattr(n, "read_at")
        assert hasattr(n, "created_at")

    @pytest.mark.django_db
    def test_read_at_defaults_to_none(self, user_a):
        from api.models import Notification

        n = _make_notification(user_a)
        assert n.read_at is None

    @pytest.mark.django_db
    def test_payload_defaults_to_empty_dict(self, user_a):
        from api.models import Notification

        n = _make_notification(user_a)
        assert n.payload == {}

    @pytest.mark.django_db
    def test_link_url_defaults_to_empty_string(self, user_a):
        from api.models import Notification

        n = _make_notification(user_a)
        assert n.link_url == ""

    @pytest.mark.django_db
    def test_ordering_newest_first(self, user_a):
        from api.models import Notification

        n1 = _make_notification(user_a, title="First")
        n2 = _make_notification(user_a, title="Second")
        n3 = _make_notification(user_a, title="Third")

        ordered = list(Notification.objects.filter(recipient=user_a))
        assert ordered[0].pk == n3.pk
        assert ordered[1].pk == n2.pk
        assert ordered[2].pk == n1.pk

    @pytest.mark.django_db
    def test_cascade_delete_on_user_delete(self, user_a):
        from api.models import Notification

        n = _make_notification(user_a)
        n_id = n.pk
        user_a.delete()
        assert not Notification.objects.filter(pk=n_id).exists()


# ---------------------------------------------------------------------------
# 2. GET /api/notifications/
# ---------------------------------------------------------------------------


class TestListNotifications:
    @pytest.mark.django_db
    def test_auth_required(self):
        client = APIClient()
        response = client.get(NOTIFICATIONS_URL)
        assert response.status_code in (401, 403)

    @pytest.mark.django_db
    def test_returns_only_requesting_users_rows(self, user_a, user_b, client_a):
        _make_notification(user_a, title="For A")
        _make_notification(user_b, title="For B")

        response = client_a.get(NOTIFICATIONS_URL)
        assert response.status_code == 200
        results = response.data["results"]
        titles = [r["title"] for r in results]
        assert "For A" in titles
        assert "For B" not in titles

    @pytest.mark.django_db
    def test_results_ordered_newest_first(self, user_a, client_a):
        n1 = _make_notification(user_a, title="Oldest")
        n2 = _make_notification(user_a, title="Middle")
        n3 = _make_notification(user_a, title="Newest")

        response = client_a.get(NOTIFICATIONS_URL)
        assert response.status_code == 200
        results = response.data["results"]
        ids = [r["id"] for r in results]
        assert ids[0] == n3.pk
        assert ids[1] == n2.pk
        assert ids[2] == n1.pk

    @pytest.mark.django_db
    def test_response_has_paginated_envelope(self, user_a, client_a):
        _make_notification(user_a)

        response = client_a.get(NOTIFICATIONS_URL)
        assert response.status_code == 200
        assert "count" in response.data
        assert "next" in response.data
        assert "previous" in response.data
        assert "results" in response.data

    @pytest.mark.django_db
    def test_default_page_size_is_ten(self, user_a, client_a):
        for i in range(15):
            _make_notification(user_a, title=f"Notif {i}")

        response = client_a.get(NOTIFICATIONS_URL)
        assert response.status_code == 200
        assert len(response.data["results"]) == 10
        assert response.data["count"] == 15
        assert response.data["next"] is not None

    @pytest.mark.django_db
    def test_page_size_can_be_set_up_to_25(self, user_a, client_a):
        for i in range(30):
            _make_notification(user_a, title=f"Notif {i}")

        response = client_a.get(NOTIFICATIONS_URL, {"page_size": 25})
        assert response.status_code == 200
        assert len(response.data["results"]) == 25

    @pytest.mark.django_db
    def test_page_size_capped_at_25(self, user_a, client_a):
        for i in range(30):
            _make_notification(user_a, title=f"Notif {i}")

        response = client_a.get(NOTIFICATIONS_URL, {"page_size": 100})
        assert response.status_code == 200
        assert len(response.data["results"]) <= 25


# ---------------------------------------------------------------------------
# 3. GET /api/notifications/unread_count/
# ---------------------------------------------------------------------------


class TestUnreadCount:
    @pytest.mark.django_db
    def test_returns_count_of_unread_for_user(self, user_a, client_a):
        _make_notification(user_a)
        _make_notification(user_a)
        _make_notification(user_a, read_at=timezone.now())

        response = client_a.get(UNREAD_COUNT_URL)
        assert response.status_code == 200
        assert response.data == {"count": 2}

    @pytest.mark.django_db
    def test_returns_zero_when_no_unread(self, user_a, client_a):
        _make_notification(user_a, read_at=timezone.now())

        response = client_a.get(UNREAD_COUNT_URL)
        assert response.status_code == 200
        assert response.data == {"count": 0}

    @pytest.mark.django_db
    def test_does_not_count_other_users_unread(self, user_a, user_b, client_a):
        _make_notification(user_b)
        _make_notification(user_b)

        response = client_a.get(UNREAD_COUNT_URL)
        assert response.status_code == 200
        assert response.data == {"count": 0}

    @pytest.mark.django_db
    def test_auth_required_for_unread_count(self):
        client = APIClient()
        response = client.get(UNREAD_COUNT_URL)
        assert response.status_code in (401, 403)


# ---------------------------------------------------------------------------
# 4. POST /api/notifications/<id>/mark_read/
# ---------------------------------------------------------------------------


class TestMarkRead:
    @pytest.mark.django_db
    def test_mark_read_sets_read_at(self, user_a, client_a):
        from api.models import Notification

        n = _make_notification(user_a)
        assert n.read_at is None

        response = client_a.post(_mark_read_url(n.pk))
        assert response.status_code == 200

        n.refresh_from_db()
        assert n.read_at is not None

    @pytest.mark.django_db
    def test_mark_read_returns_new_unread_count(self, user_a, client_a):
        n1 = _make_notification(user_a)
        _make_notification(user_a)

        response = client_a.post(_mark_read_url(n1.pk))
        assert response.status_code == 200
        assert "count" in response.data
        assert response.data["count"] == 1

    @pytest.mark.django_db
    def test_mark_read_returns_404_for_other_users_notification(self, user_a, user_b, client_a):
        n = _make_notification(user_b)

        response = client_a.post(_mark_read_url(n.pk))
        assert response.status_code == 404

    @pytest.mark.django_db
    def test_mark_read_is_idempotent(self, user_a, client_a):
        from api.models import Notification

        already_read = timezone.now()
        n = _make_notification(user_a, read_at=already_read)

        response = client_a.post(_mark_read_url(n.pk))
        assert response.status_code == 200
        assert "count" in response.data

        n.refresh_from_db()
        assert n.read_at is not None

    @pytest.mark.django_db
    def test_mark_read_auth_required(self, user_a):
        n = _make_notification(user_a)
        client = APIClient()
        response = client.post(_mark_read_url(n.pk))
        assert response.status_code in (401, 403)


# ---------------------------------------------------------------------------
# 5. POST /api/notifications/mark_all_read/
# ---------------------------------------------------------------------------


class TestMarkAllRead:
    @pytest.mark.django_db
    def test_mark_all_read_marks_all_unread_for_user(self, user_a, client_a):
        from api.models import Notification

        _make_notification(user_a)
        _make_notification(user_a)
        _make_notification(user_a)

        response = client_a.post(MARK_ALL_READ_URL)
        assert response.status_code == 200
        assert response.data == {"count": 0}

        all_notifications = Notification.objects.filter(recipient=user_a)
        for n in all_notifications:
            assert n.read_at is not None

    @pytest.mark.django_db
    def test_mark_all_read_returns_count_zero(self, user_a, client_a):
        _make_notification(user_a)
        _make_notification(user_a)

        response = client_a.post(MARK_ALL_READ_URL)
        assert response.status_code == 200
        assert response.data == {"count": 0}

    @pytest.mark.django_db
    def test_mark_all_read_does_not_touch_other_users_rows(self, user_a, user_b, client_a):
        from api.models import Notification

        _make_notification(user_a)
        n_b1 = _make_notification(user_b)
        n_b2 = _make_notification(user_b)

        response = client_a.post(MARK_ALL_READ_URL)
        assert response.status_code == 200

        n_b1.refresh_from_db()
        n_b2.refresh_from_db()
        assert n_b1.read_at is None
        assert n_b2.read_at is None

    @pytest.mark.django_db
    def test_mark_all_read_auth_required(self):
        client = APIClient()
        response = client.post(MARK_ALL_READ_URL)
        assert response.status_code in (401, 403)


# ---------------------------------------------------------------------------
# 6. Cross-user isolation
# ---------------------------------------------------------------------------


class TestCrossUserIsolation:
    @pytest.mark.django_db
    def test_user_a_list_never_contains_user_b_rows(self, user_a, user_b, client_a):
        for i in range(3):
            _make_notification(user_a, title=f"A-{i}")
        for i in range(3):
            _make_notification(user_b, title=f"B-{i}")

        response = client_a.get(NOTIFICATIONS_URL)
        assert response.status_code == 200
        results = response.data["results"]
        for row in results:
            assert not row["title"].startswith("B-"), (
                f"User A's list contains User B's row: {row}"
            )

    @pytest.mark.django_db
    def test_user_a_cannot_mark_read_user_b_notification(self, user_a, user_b, client_a):
        n = _make_notification(user_b, title="Only B's")

        response = client_a.post(_mark_read_url(n.pk))
        assert response.status_code == 404

        n.refresh_from_db()
        assert n.read_at is None
