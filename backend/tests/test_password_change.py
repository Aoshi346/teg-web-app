import pytest
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient

User = get_user_model()

CHANGE_PASSWORD_URL = "/api/auth/change_password/"
ME_URL = "/api/auth/me/"

CURRENT_PASSWORD = "OldPass123!"
NEW_PASSWORD = "NewPass456!"


@pytest.fixture
def regular_user(db):
    return User.objects.create_user(
        email="user@test.local",
        password=CURRENT_PASSWORD,
        first_name="Regular",
        last_name="User",
        role="Estudiante",
        status="active",
    )


@pytest.fixture
def authenticated_client(regular_user):
    client = APIClient()
    client.force_authenticate(user=regular_user)
    return client


@pytest.mark.django_db
def test_authenticated_user_can_change_password_successfully(authenticated_client, regular_user):
    response = authenticated_client.post(
        CHANGE_PASSWORD_URL,
        {"current_password": CURRENT_PASSWORD, "new_password": NEW_PASSWORD},
        format="json",
    )
    assert response.status_code == 200
    regular_user.refresh_from_db()
    assert regular_user.check_password(NEW_PASSWORD)


@pytest.mark.django_db
def test_session_remains_valid_after_password_change(regular_user):
    client = APIClient()
    client.force_authenticate(user=regular_user)

    change_response = client.post(
        CHANGE_PASSWORD_URL,
        {"current_password": CURRENT_PASSWORD, "new_password": NEW_PASSWORD},
        format="json",
    )
    assert change_response.status_code == 200

    me_response = client.get(ME_URL)
    assert me_response.status_code == 200


@pytest.mark.django_db
def test_wrong_current_password_returns_400_with_field_error(authenticated_client):
    response = authenticated_client.post(
        CHANGE_PASSWORD_URL,
        {"current_password": "WrongPassword!", "new_password": NEW_PASSWORD},
        format="json",
    )
    assert response.status_code == 400
    assert "current_password" in response.data


@pytest.mark.django_db
def test_new_password_too_short_returns_400(authenticated_client):
    response = authenticated_client.post(
        CHANGE_PASSWORD_URL,
        {"current_password": CURRENT_PASSWORD, "new_password": "short"},
        format="json",
    )
    assert response.status_code == 400


@pytest.mark.django_db
def test_new_password_same_as_current_returns_400(authenticated_client):
    response = authenticated_client.post(
        CHANGE_PASSWORD_URL,
        {"current_password": CURRENT_PASSWORD, "new_password": CURRENT_PASSWORD},
        format="json",
    )
    assert response.status_code == 400


@pytest.mark.django_db
def test_unauthenticated_request_is_rejected():
    client = APIClient()
    response = client.post(
        CHANGE_PASSWORD_URL,
        {"current_password": CURRENT_PASSWORD, "new_password": NEW_PASSWORD},
        format="json",
    )
    assert response.status_code in (401, 403)
