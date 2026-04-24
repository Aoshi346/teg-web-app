import re
import pytest
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient

User = get_user_model()


@pytest.fixture
def client():
    return APIClient()


@pytest.mark.django_db
def test_self_register_still_uses_client_password(client):
    payload = {
        "email": "self@test.local",
        "password": "clientpass123",
        "full_name": "Self User",
        "role": "Estudiante",
    }
    response = client.post("/api/auth/register/", payload, format="json")
    assert response.status_code == 201
    user = User.objects.get(email="self@test.local")
    assert user.check_password("clientpass123")
    assert "temporary_password" not in response.data


@pytest.mark.django_db
def test_admin_create_generates_random_password(client):
    payload = {
        "email": "new@test.local",
        "full_name": "New User",
        "role": "Estudiante",
        "admin_create": True,
    }
    response = client.post("/api/auth/register/", payload, format="json")
    assert response.status_code == 201
    assert "temporary_password" in response.data
    temp_pw = response.data["temporary_password"]
    assert isinstance(temp_pw, str)
    assert len(temp_pw) >= 10
    # readable format: alphanumeric groups separated by dashes
    assert re.match(r"^[A-Za-z0-9]+(-[A-Za-z0-9]+)+$", temp_pw), f"unexpected format: {temp_pw}"
    user = User.objects.get(email="new@test.local")
    assert user.check_password(temp_pw)


@pytest.mark.django_db
def test_admin_create_ignores_client_supplied_password(client):
    payload = {
        "email": "new2@test.local",
        "password": "clientpass123",  # should be ignored
        "full_name": "New User Two",
        "role": "Estudiante",
        "admin_create": True,
    }
    response = client.post("/api/auth/register/", payload, format="json")
    assert response.status_code == 201
    user = User.objects.get(email="new2@test.local")
    assert not user.check_password("clientpass123")
    assert user.check_password(response.data["temporary_password"])


@pytest.mark.django_db
def test_admin_create_returns_different_password_each_time(client):
    passwords = set()
    for i in range(3):
        response = client.post("/api/auth/register/", {
            "email": f"u{i}@test.local",
            "full_name": f"User {i}",
            "role": "Estudiante",
            "admin_create": True,
        }, format="json")
        passwords.add(response.data["temporary_password"])
    assert len(passwords) == 3, "passwords should be unique per create"
