"""
Seguridad del alta y del login expuestos a internet.

El auto-registro es público (AllowAny), así que el backend no puede fiarse de lo que mande el
cliente: un anónimo no elige ser Administrador ni pide contraseñas temporales, y una cuenta que
aún no aprobó un Administrador no obtiene sesión aunque su contraseña sea correcta.
"""

import pytest
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient

User = get_user_model()

REGISTER_URL = "/api/auth/register/"
LOGIN_URL = "/api/auth/login/"


def _self_register_payload(**overrides):
    payload = {
        "email": "nuevo@test.local",
        "password": "clave-segura-123",
        "full_name": "Nuevo Usuario",
        "role": "Estudiante",
    }
    payload.update(overrides)
    return payload


@pytest.mark.django_db
@pytest.mark.parametrize("role", ["Estudiante", "Tutor", "Jurado"])
def test_anonymous_can_self_register_with_public_roles(role):
    response = APIClient().post(REGISTER_URL, _self_register_payload(role=role), format="json")
    assert response.status_code == 201, response.content
    user = User.objects.get(email="nuevo@test.local")
    assert user.role == role
    assert user.status == "pending"


@pytest.mark.django_db
def test_anonymous_cannot_self_register_as_admin():
    response = APIClient().post(
        REGISTER_URL, _self_register_payload(role="Administrador"), format="json"
    )
    assert response.status_code == 400
    assert not User.objects.filter(email="nuevo@test.local").exists()


@pytest.mark.django_db
def test_anonymous_cannot_use_admin_create():
    payload = _self_register_payload(admin_create=True)
    payload.pop("password")
    response = APIClient().post(REGISTER_URL, payload, format="json")
    assert response.status_code == 403
    assert "temporary_password" not in getattr(response, "data", {})
    assert not User.objects.filter(email="nuevo@test.local").exists()


@pytest.mark.django_db
def test_non_admin_cannot_use_admin_create(student_client):
    payload = _self_register_payload(admin_create=True)
    payload.pop("password")
    response = student_client.post(REGISTER_URL, payload, format="json")
    assert response.status_code == 403
    assert not User.objects.filter(email="nuevo@test.local").exists()


@pytest.mark.django_db
def test_admin_can_create_administrators(authed_client):
    payload = _self_register_payload(role="Administrador", admin_create=True)
    payload.pop("password")
    response = authed_client.post(REGISTER_URL, payload, format="json")
    assert response.status_code == 201, response.content
    assert User.objects.get(email="nuevo@test.local").role == "Administrador"


@pytest.mark.django_db
@pytest.mark.parametrize("account_status", ["pending", "rejected"])
def test_login_rejects_accounts_not_approved(account_status):
    User.objects.create_user(
        email="espera@test.local",
        password="clave-segura-123",
        role="Estudiante",
        status=account_status,
    )
    client = APIClient()
    response = client.post(
        LOGIN_URL,
        {"email": "espera@test.local", "password": "clave-segura-123"},
        format="json",
    )
    assert response.status_code == 403
    assert "_auth_user_id" not in client.session


@pytest.mark.django_db
def test_login_accepts_active_accounts():
    User.objects.create_user(
        email="activo@test.local",
        password="clave-segura-123",
        role="Estudiante",
        status="active",
    )
    response = APIClient().post(
        LOGIN_URL,
        {"email": "activo@test.local", "password": "clave-segura-123"},
        format="json",
    )
    assert response.status_code == 200, response.content
