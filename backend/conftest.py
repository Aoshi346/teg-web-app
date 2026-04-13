"""
Pytest fixtures compartidas para el backend de TesisFar.

Aquí se centralizan los fixtures que los tests reutilizan: creación de usuarios
por rol, clientes API autenticados y datos base (proyectos, semestres). Mantener
estos fixtures en un solo lugar evita duplicación y asegura que todos los tests
usen los mismos factories — lo cual es crítico para tests de permisos basados en
rol, donde un error en la creación de un usuario silenciosamente invalida el test.
"""

import pytest
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient

from api.models import Project

User = get_user_model()

_USER_PASSWORD = "test-pass-123"


def _make_user(email, role, first_name, last_name, status="active"):
    """
    Crea un usuario de prueba sin usar create_user(), ya que el UserManager
    heredado de AbstractUser no es compatible con el modelo User personalizado
    que elimina el campo `username` (falla en Django 6 al pasar username=... al
    constructor del modelo).
    """
    user = User(
        email=email,
        first_name=first_name,
        last_name=last_name,
        role=role,
        status=status,
    )
    user.set_password(_USER_PASSWORD)
    user.save()
    return user


@pytest.fixture
def api_client():
    return APIClient()


@pytest.fixture
def admin_user(db):
    return _make_user("admin@test.local", "Administrador", "Admin", "Test")


@pytest.fixture
def tutor_user(db):
    return _make_user("tutor@test.local", "Tutor", "Tutor", "Test")


@pytest.fixture
def jurado_user(db):
    return _make_user("jurado@test.local", "Jurado", "Jurado", "Test")


@pytest.fixture
def student_user(db):
    return _make_user("student@test.local", "Estudiante", "Student", "Test")


@pytest.fixture
def authed_client(api_client, admin_user):
    api_client.force_authenticate(user=admin_user)
    return api_client


@pytest.fixture
def student_client(api_client, student_user):
    api_client.force_authenticate(user=student_user)
    return api_client


@pytest.fixture
def tutor_client(api_client, tutor_user):
    api_client.force_authenticate(user=tutor_user)
    return api_client


@pytest.fixture
def jurado_client(api_client, jurado_user):
    api_client.force_authenticate(user=jurado_user)
    return api_client


@pytest.fixture
def project_factory(db):
    """
    Factoría mínima para crear instancias de Project en tests.

    Permite sobreescribir cualquier campo mediante kwargs. El campo `student`
    es obligatorio y debe pasarse siempre. Los demás tienen valores por defecto
    sensatos para tests de EvaluationViewSet.
    """

    def make(student, **kwargs):
        defaults = {
            "title": "Test Project",
            "project_type": "proyecto",
            "failed_attempts": 0,
            "status": "pending",
            "period": "",
        }
        defaults.update(kwargs)
        advisors = defaults.pop("advisors", [])
        project = Project.objects.create(student=student, **defaults)
        if advisors:
            project.advisors.set(advisors)
        return project

    return make
