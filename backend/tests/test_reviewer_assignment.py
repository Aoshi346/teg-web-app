"""Integration tests for Project.reviewer assignment."""

import pytest
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient

from api.models import Evaluation, Project

User = get_user_model()

PROJECTS_URL = "/api/projects/"
EVALUATIONS_URL = "/api/evaluations/"


def _eval_payload(project_id):
    return {"project": project_id, "pass_status": "Pass"}


def _assign_url(project_id):
    return f"/api/projects/{project_id}/assign_reviewer/"


@pytest.fixture
def second_jurado(db):
    user = User(
        email="jurado2@test.local",
        first_name="Jurado2",
        last_name="Test",
        role="Jurado",
        status="active",
    )
    user.set_password("test-pass-123")
    user.save()
    return user


class TestProjectVisibility:
    @pytest.mark.django_db
    def test_unassigned_project_invisible_to_jurado(self, jurado_user, student_user, project_factory):
        project_factory(student=student_user)  # reviewer=None
        client = APIClient()
        client.force_authenticate(user=jurado_user)
        resp = client.get(PROJECTS_URL)
        assert resp.status_code == 200
        assert resp.json() == []

    @pytest.mark.django_db
    def test_assigned_project_visible_to_jurado(self, jurado_user, student_user, project_factory):
        project = project_factory(student=student_user, reviewer=jurado_user)
        client = APIClient()
        client.force_authenticate(user=jurado_user)
        resp = client.get(PROJECTS_URL)
        assert resp.status_code == 200
        ids = [p["id"] for p in resp.json()]
        assert project.id in ids

    @pytest.mark.django_db
    def test_other_jurado_cannot_see_project(self, jurado_user, second_jurado, student_user, project_factory):
        project_factory(student=student_user, reviewer=jurado_user)
        client = APIClient()
        client.force_authenticate(user=second_jurado)
        resp = client.get(PROJECTS_URL)
        assert resp.status_code == 200
        assert resp.json() == []


class TestEvaluationGuard:
    @pytest.mark.django_db
    def test_jurado_cannot_evaluate_unassigned_project(self, jurado_user, student_user, project_factory):
        project = project_factory(student=student_user)
        client = APIClient()
        client.force_authenticate(user=jurado_user)
        resp = client.post(EVALUATIONS_URL, _eval_payload(project.id), format="json")
        assert resp.status_code == 403
        assert not Evaluation.objects.filter(project=project).exists()

    @pytest.mark.django_db
    def test_jurado_can_evaluate_assigned_project(self, jurado_user, student_user, project_factory):
        project = project_factory(student=student_user, reviewer=jurado_user)
        client = APIClient()
        client.force_authenticate(user=jurado_user)
        resp = client.post(EVALUATIONS_URL, _eval_payload(project.id), format="json")
        assert resp.status_code == 201

    @pytest.mark.django_db
    def test_tutor_cannot_create_evaluation(self, tutor_user, student_user, project_factory):
        project = project_factory(student=student_user)
        client = APIClient()
        client.force_authenticate(user=tutor_user)
        resp = client.post(EVALUATIONS_URL, _eval_payload(project.id), format="json")
        assert resp.status_code == 403

    @pytest.mark.django_db
    def test_admin_can_still_create_evaluation(self, admin_user, student_user, project_factory):
        project = project_factory(student=student_user)
        client = APIClient()
        client.force_authenticate(user=admin_user)
        resp = client.post(EVALUATIONS_URL, _eval_payload(project.id), format="json")
        assert resp.status_code == 201


class TestAssignReviewerAction:
    @pytest.mark.django_db
    def test_admin_assign_reviewer_sets_reviewer(self, admin_user, jurado_user, student_user, project_factory):
        project = project_factory(student=student_user)
        client = APIClient()
        client.force_authenticate(user=admin_user)
        resp = client.post(_assign_url(project.id), {"reviewer": jurado_user.id}, format="json")
        assert resp.status_code == 200
        project.refresh_from_db()
        assert project.reviewer_id == jurado_user.id

    @pytest.mark.django_db
    def test_admin_assign_reviewer_can_unset(self, admin_user, jurado_user, student_user, project_factory):
        project = project_factory(student=student_user, reviewer=jurado_user)
        client = APIClient()
        client.force_authenticate(user=admin_user)
        resp = client.post(_assign_url(project.id), {"reviewer": None}, format="json")
        assert resp.status_code == 200
        project.refresh_from_db()
        assert project.reviewer_id is None

    @pytest.mark.django_db
    def test_non_admin_cannot_assign_reviewer(self, tutor_user, jurado_user, student_user, project_factory):
        project = project_factory(student=student_user)
        client = APIClient()
        client.force_authenticate(user=tutor_user)
        resp = client.post(_assign_url(project.id), {"reviewer": jurado_user.id}, format="json")
        assert resp.status_code == 403

    @pytest.mark.django_db
    def test_assign_reviewer_rejects_non_jurado(self, admin_user, tutor_user, student_user, project_factory):
        project = project_factory(student=student_user)
        client = APIClient()
        client.force_authenticate(user=admin_user)
        resp = client.post(_assign_url(project.id), {"reviewer": tutor_user.id}, format="json")
        assert resp.status_code == 400
