import pytest
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient
from api.models import Semester, Project

User = get_user_model()


@pytest.fixture
def admin_client(db):
    admin = User.objects.create_user(
        email="admin@test.local", password="p", role="Administrador", status="active"
    )
    client = APIClient()
    client.force_authenticate(admin)
    return client


@pytest.mark.django_db
def test_delete_semester_with_no_projects_succeeds(admin_client):
    s = Semester.objects.create(period="2026-01", start_month=1, end_month=6)
    response = admin_client.delete(f"/api/semesters/{s.id}/")
    assert response.status_code == 204
    assert not Semester.objects.filter(id=s.id).exists()


@pytest.mark.django_db
def test_delete_semester_with_projects_returns_400(admin_client):
    s = Semester.objects.create(period="2026-01", start_month=1, end_month=6)
    student = User.objects.create_user(
        email="s@test.local", password="p", role="Estudiante", status="active"
    )
    Project.objects.create(title="P1", student=student, period="2026-01", project_type="proyecto")

    response = admin_client.delete(f"/api/semesters/{s.id}/")
    assert response.status_code == 400
    assert "proyectos asignados" in str(response.data.get("detail", "")).lower()
    assert Semester.objects.filter(id=s.id).exists()
