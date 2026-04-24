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
def test_semester_list_includes_project_count_zero(admin_client):
    Semester.objects.create(period="2026-01", start_month=1, end_month=6)
    response = admin_client.get("/api/semesters/")
    assert response.status_code == 200
    item = next(s for s in response.data if s["period"] == "2026-01")
    assert item["project_count"] == 0


@pytest.mark.django_db
def test_semester_list_includes_project_count_with_projects(admin_client):
    Semester.objects.create(period="2026-01", start_month=1, end_month=6)
    student = User.objects.create_user(
        email="s@test.local", password="p", role="Estudiante", status="active"
    )
    Project.objects.create(title="P1", student=student, period="2026-01", project_type="proyecto")
    Project.objects.create(title="P2", student=student, period="2026-01", project_type="proyecto")
    response = admin_client.get("/api/semesters/")
    item = next(s for s in response.data if s["period"] == "2026-01")
    assert item["project_count"] == 2
