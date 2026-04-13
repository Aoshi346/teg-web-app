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


@pytest.fixture
def api_client():
    return APIClient()


@pytest.fixture
def admin_user(db):
    return User.objects.create_user(
        email="admin@test.local",
        password="test-pass-123",
        first_name="Admin",
        last_name="Test",
        role="Administrador",
        status="active",
    )


@pytest.fixture
def tutor_user(db):
    return User.objects.create_user(
        email="tutor@test.local",
        password="test-pass-123",
        first_name="Tutor",
        last_name="Test",
        role="Tutor",
        status="active",
    )


@pytest.fixture
def jurado_user(db):
    return User.objects.create_user(
        email="jurado@test.local",
        password="test-pass-123",
        first_name="Jurado",
        last_name="Test",
        role="Jurado",
        status="active",
    )


@pytest.fixture
def student_user(db):
    return User.objects.create_user(
        email="student@test.local",
        password="test-pass-123",
        first_name="Student",
        last_name="Test",
        role="Estudiante",
        status="active",
    )


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
