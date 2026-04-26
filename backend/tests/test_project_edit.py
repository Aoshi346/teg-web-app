"""Integration tests for PATCH /api/projects/{id}/ — title edit gate by role."""

import pytest
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient

User = get_user_model()


def _url(project_id):
    return f"/api/projects/{project_id}/"


@pytest.fixture
def other_student(db):
    return User.objects.create_user(
        email="student2@test.local",
        password="test-pass-123",
        first_name="Student2",
        last_name="Test",
        role="Estudiante",
        status="active",
    )


@pytest.mark.django_db
def test_admin_can_edit_title(authed_client, student_user, project_factory):
    project = project_factory(student=student_user, title="Original")
    resp = authed_client.patch(_url(project.id), {"title": "Nuevo título"}, format="json")
    assert resp.status_code == 200, resp.content
    assert resp.json()["title"] == "Nuevo título"
    project.refresh_from_db()
    assert project.title == "Nuevo título"


@pytest.mark.django_db
def test_student_can_edit_own_title(student_client, student_user, project_factory):
    project = project_factory(student=student_user, title="Original")
    resp = student_client.patch(_url(project.id), {"title": "Mi nuevo título"}, format="json")
    assert resp.status_code == 200, resp.content
    project.refresh_from_db()
    assert project.title == "Mi nuevo título"


@pytest.mark.django_db
def test_student_cannot_edit_other_students_project(student_client, other_student, project_factory):
    project = project_factory(student=other_student, title="Otro")
    resp = student_client.patch(_url(project.id), {"title": "Hack"}, format="json")
    # Note: get_queryset filtra a solo proyectos propios → DRF responde 404
    # antes de que la compuerta llegue a evaluar 403. Aceptamos cualquiera de
    # los dos como "bloqueado": lo crítico es que el título no cambió.
    assert resp.status_code in (403, 404)
    project.refresh_from_db()
    assert project.title == "Otro"


@pytest.mark.django_db
def test_student_cannot_edit_forbidden_field(student_client, student_user, project_factory):
    project = project_factory(student=student_user, state="pending_review_1")
    resp = student_client.patch(_url(project.id), {"state": "approved"}, format="json")
    assert resp.status_code == 400, resp.content
    project.refresh_from_db()
    assert project.state == "pending_review_1"


@pytest.mark.django_db
def test_student_cannot_edit_terminal_state_project(student_client, student_user, project_factory):
    project = project_factory(student=student_user, state="approved", title="Aprobado")
    resp = student_client.patch(_url(project.id), {"title": "Cambio"}, format="json")
    assert resp.status_code == 400, resp.content
    project.refresh_from_db()
    assert project.title == "Aprobado"


@pytest.mark.django_db
def test_student_cannot_edit_failed_final_project(student_client, student_user, project_factory):
    project = project_factory(student=student_user, state="failed_final", title="Reprobado")
    resp = student_client.patch(_url(project.id), {"title": "Cambio"}, format="json")
    assert resp.status_code == 400, resp.content
    project.refresh_from_db()
    assert project.title == "Reprobado"


@pytest.mark.django_db
def test_tutor_cannot_edit_title(tutor_client, tutor_user, student_user, project_factory):
    project = project_factory(student=student_user, title="Original")
    project.advisors.add(tutor_user)
    resp = tutor_client.patch(_url(project.id), {"title": "Hack"}, format="json")
    assert resp.status_code == 403, resp.content
    project.refresh_from_db()
    assert project.title == "Original"


@pytest.mark.django_db
def test_jurado_cannot_edit_title(jurado_client, jurado_user, student_user, project_factory):
    project = project_factory(student=student_user, title="Original", reviewer=jurado_user)
    resp = jurado_client.patch(_url(project.id), {"title": "Hack"}, format="json")
    assert resp.status_code == 403, resp.content
    project.refresh_from_db()
    assert project.title == "Original"
