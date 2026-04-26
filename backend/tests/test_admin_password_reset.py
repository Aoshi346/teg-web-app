"""Integration tests for POST /api/users/{id}/reset_password/ — admin-only password reset."""

import pytest
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient

User = get_user_model()


def _url(user_id):
    return f"/api/users/{user_id}/reset_password/"


@pytest.fixture
def target_user(db):
    return User.objects.create_user(
        email="target@test.local",
        password="OldPass123!",
        first_name="Target",
        last_name="User",
        role="Estudiante",
        status="active",
    )


@pytest.mark.django_db
def test_admin_can_reset_password_and_target_can_login(authed_client, target_user):
    new_password = "NewPass123"
    resp = authed_client.post(_url(target_user.id), {"new_password": new_password}, format="json")
    assert resp.status_code == 200, resp.content

    target_user.refresh_from_db()
    assert target_user.check_password(new_password)

    login_client = APIClient()
    login_resp = login_client.post(
        "/api/auth/login/",
        {"email": target_user.email, "password": new_password},
        format="json",
    )
    assert login_resp.status_code == 200, login_resp.content


@pytest.mark.django_db
def test_admin_short_password_rejected(authed_client, target_user):
    resp = authed_client.post(_url(target_user.id), {"new_password": "short"}, format="json")
    assert resp.status_code == 400
    target_user.refresh_from_db()
    assert target_user.check_password("OldPass123!")


@pytest.mark.django_db
def test_admin_missing_password_rejected(authed_client, target_user):
    resp = authed_client.post(_url(target_user.id), {}, format="json")
    assert resp.status_code == 400
    target_user.refresh_from_db()
    assert target_user.check_password("OldPass123!")


@pytest.mark.django_db
def test_tutor_cannot_reset_password(tutor_client, target_user):
    resp = tutor_client.post(_url(target_user.id), {"new_password": "NewPass123"}, format="json")
    assert resp.status_code in (403, 404)
    target_user.refresh_from_db()
    assert target_user.check_password("OldPass123!")


@pytest.mark.django_db
def test_jurado_cannot_reset_password(jurado_client, target_user):
    resp = jurado_client.post(_url(target_user.id), {"new_password": "NewPass123"}, format="json")
    assert resp.status_code in (403, 404)
    target_user.refresh_from_db()
    assert target_user.check_password("OldPass123!")


@pytest.mark.django_db
def test_estudiante_cannot_reset_own_password(student_client, student_user):
    resp = student_client.post(_url(student_user.id), {"new_password": "NewPass123"}, format="json")
    assert resp.status_code in (403, 404)
    student_user.refresh_from_db()
    assert student_user.check_password("test-pass-123")


@pytest.mark.django_db
def test_unauthenticated_cannot_reset_password(target_user):
    client = APIClient()
    resp = client.post(_url(target_user.id), {"new_password": "NewPass123"}, format="json")
    assert resp.status_code in (401, 403)
    target_user.refresh_from_db()
    assert target_user.check_password("OldPass123!")
