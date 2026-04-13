import pytest
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient

User = get_user_model()

REGISTER_URL = "/api/auth/register/"

VALID_PAYLOAD = {
    "email": "newuser@test.local",
    "password": "strongpass123",
    "full_name": "John Doe",
    "role": "Estudiante",
}


@pytest.fixture
def client():
    return APIClient()


@pytest.mark.django_db
def test_register_endpoint_creates_user_with_valid_payload(client):
    response = client.post(REGISTER_URL, VALID_PAYLOAD, format="json")
    assert response.status_code == 201
    assert User.objects.filter(email="newuser@test.local").exists()


@pytest.mark.django_db
def test_register_endpoint_returns_user_data_without_password(client):
    response = client.post(REGISTER_URL, VALID_PAYLOAD, format="json")
    assert response.status_code == 201
    data = response.data
    assert "email" in data
    assert "full_name" in data
    assert "password" not in data


@pytest.mark.django_db
def test_register_endpoint_splits_full_name(client):
    response = client.post(REGISTER_URL, VALID_PAYLOAD, format="json")
    assert response.status_code == 201
    user = User.objects.get(email="newuser@test.local")
    assert user.first_name == "John"
    assert user.last_name == "Doe"


@pytest.mark.django_db
def test_register_endpoint_sets_status_pending(client):
    response = client.post(REGISTER_URL, VALID_PAYLOAD, format="json")
    assert response.status_code == 201
    user = User.objects.get(email="newuser@test.local")
    assert user.status == "pending"


@pytest.mark.django_db
def test_register_endpoint_rejects_duplicate_email(client):
    client.post(REGISTER_URL, VALID_PAYLOAD, format="json")
    response = client.post(REGISTER_URL, VALID_PAYLOAD, format="json")
    assert response.status_code == 400
