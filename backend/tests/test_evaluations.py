"""
Integration tests for EvaluationViewSet.

Pins down two core behaviors:
1. Role-based access control (IsReviewerRole + get_queryset filtering).
2. The 2-attempt limit for project_type='proyecto' (not 'tesis').

These are characterization tests — they describe what the current implementation
does. Any future refactor that breaks them must be reviewed before merging.
"""

import pytest
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient

from api.models import Evaluation

User = get_user_model()


def _make_student(email):
    """Crea un Estudiante auxiliar para tests que necesitan más de un usuario."""
    user = User(
        email=email,
        first_name="Extra",
        last_name="Student",
        role="Estudiante",
        status="active",
    )
    user.set_password("test-pass-123")
    user.save()
    return user

EVALUATIONS_URL = "/api/evaluations/"


def _minimal_payload(project_id):
    """Return the smallest valid body accepted by EvaluationSerializer."""
    return {"project": project_id, "pass_status": "Pass"}


# ---------------------------------------------------------------------------
# Role permission tests (create)
# ---------------------------------------------------------------------------


class TestCreatePermissions:
    @pytest.mark.django_db
    def test_admin_can_create_evaluation(self, admin_user, student_user, project_factory):
        project = project_factory(student=student_user)
        client = APIClient()
        client.force_authenticate(user=admin_user)
        response = client.post(EVALUATIONS_URL, _minimal_payload(project.id), format="json")
        assert response.status_code == 201
        assert Evaluation.objects.filter(project=project).exists()

    @pytest.mark.django_db
    def test_tutor_cannot_create_evaluation(self, tutor_user, student_user, project_factory):
        project = project_factory(student=student_user)
        client = APIClient()
        client.force_authenticate(user=tutor_user)
        response = client.post(EVALUATIONS_URL, _minimal_payload(project.id), format="json")
        assert response.status_code == 403

    @pytest.mark.django_db
    def test_jurado_can_create_evaluation(self, jurado_user, student_user, project_factory):
        project = project_factory(student=student_user, reviewer=jurado_user)
        client = APIClient()
        client.force_authenticate(user=jurado_user)
        response = client.post(EVALUATIONS_URL, _minimal_payload(project.id), format="json")
        assert response.status_code == 201

    @pytest.mark.django_db
    def test_student_cannot_create_evaluation(self, student_user, project_factory):
        project = project_factory(student=student_user)
        client = APIClient()
        client.force_authenticate(user=student_user)
        response = client.post(EVALUATIONS_URL, _minimal_payload(project.id), format="json")
        assert response.status_code == 403

    @pytest.mark.django_db
    def test_unauthenticated_cannot_create_evaluation(self, student_user, project_factory):
        project = project_factory(student=student_user)
        client = APIClient()
        response = client.post(EVALUATIONS_URL, _minimal_payload(project.id), format="json")
        assert response.status_code in (401, 403)


# ---------------------------------------------------------------------------
# 2-attempt limit tests
# ---------------------------------------------------------------------------


class TestFailedAttemptsLimit:
    @pytest.mark.django_db
    def test_proyecto_in_initial_state_allows_creation(
        self, admin_user, student_user, project_factory
    ):
        project = project_factory(student=student_user, project_type="proyecto", state="pending_review_1")
        client = APIClient()
        client.force_authenticate(user=admin_user)
        response = client.post(EVALUATIONS_URL, _minimal_payload(project.id), format="json")
        assert response.status_code == 201

    @pytest.mark.django_db
    def test_proyecto_in_pending_review_2_allows_creation(
        self, admin_user, student_user, project_factory
    ):
        project = project_factory(student=student_user, project_type="proyecto", state="pending_review_2")
        client = APIClient()
        client.force_authenticate(user=admin_user)
        response = client.post(EVALUATIONS_URL, _minimal_payload(project.id), format="json")
        assert response.status_code == 201

    @pytest.mark.django_db
    def test_proyecto_in_failed_final_state_blocks_creation(
        self, admin_user, student_user, project_factory
    ):
        # La máquina de estados reemplazó la guardia failed_attempts >= 2.
        # Un proyecto en estado terminal (failed_final) ya no acepta evaluaciones.
        project = project_factory(
            student=student_user, project_type="proyecto", state="failed_final"
        )
        client = APIClient()
        client.force_authenticate(user=admin_user)
        response = client.post(EVALUATIONS_URL, _minimal_payload(project.id), format="json")
        assert response.status_code == 400
        assert "state" in response.json()  # Error must surface on the 'state' field, not generically.

    @pytest.mark.django_db
    def test_proyecto_in_approved_state_blocks_creation(
        self, admin_user, student_user, project_factory
    ):
        """Cualquier estado terminal bloquea la creación de nuevas evaluaciones."""
        project = project_factory(
            student=student_user, project_type="proyecto", state="approved"
        )
        client = APIClient()
        client.force_authenticate(user=admin_user)
        response = client.post(EVALUATIONS_URL, _minimal_payload(project.id), format="json")
        assert response.status_code == 400
        assert "state" in response.json()  # Error must surface on the 'state' field, not generically.


# ---------------------------------------------------------------------------
# Queryset filtering tests (list + retrieve)
# ---------------------------------------------------------------------------


class TestQuerysetFiltering:
    @pytest.mark.django_db
    def test_admin_lists_all_evaluations(self, admin_user, student_user, project_factory):
        """Admin GET /evaluations/ returns evaluations from all projects."""
        p1 = project_factory(student=student_user, title="P1")
        p2 = project_factory(student=student_user, title="P2")
        p3 = project_factory(student=student_user, title="P3")
        for project in (p1, p2, p3):
            Evaluation.objects.create(project=project, reviewer=admin_user, pass_status="Pass")

        client = APIClient()
        client.force_authenticate(user=admin_user)
        response = client.get(EVALUATIONS_URL)
        assert response.status_code == 200
        assert len(response.json()) == 3

    @pytest.mark.django_db
    def test_tutor_lists_only_advised_project_evaluations(
        self, admin_user, tutor_user, student_user, project_factory, db
    ):
        """
        Tutor must see only evaluations for projects where they are an advisor.
        A second tutor is used to own project B so tutor_user is genuinely not
        an advisor on it.
        """
        second_tutor = User(
            email="tutor2@test.local",
            first_name="Second",
            last_name="Tutor",
            role="Tutor",
            status="active",
        )
        second_tutor.set_password("test-pass-123")
        second_tutor.save()

        p1 = project_factory(student=student_user, title="Advised", advisors=[tutor_user])
        p2 = project_factory(student=student_user, title="Not Advised", advisors=[second_tutor])
        eval_p1 = Evaluation.objects.create(project=p1, reviewer=admin_user, pass_status="Pass")
        Evaluation.objects.create(project=p2, reviewer=admin_user, pass_status="Fail")

        client = APIClient()
        client.force_authenticate(user=tutor_user)
        response = client.get(EVALUATIONS_URL)
        assert response.status_code == 200
        ids = [e["id"] for e in response.json()]
        assert ids == [eval_p1.id]

    @pytest.mark.django_db
    def test_jurado_lists_only_evaluations_on_assigned_projects(
        self, admin_user, jurado_user, student_user, project_factory
    ):
        """Jurado sees evaluations only for projects where they are assigned reviewer."""
        p_mine = project_factory(student=student_user, title="Mine", reviewer=jurado_user)
        p_other = project_factory(student=student_user, title="Other")
        Evaluation.objects.create(project=p_mine, reviewer=admin_user, pass_status="Pass")
        Evaluation.objects.create(project=p_other, reviewer=admin_user, pass_status="Fail")

        client = APIClient()
        client.force_authenticate(user=jurado_user)
        response = client.get(EVALUATIONS_URL)
        assert response.status_code == 200
        ids = [e["project"] for e in response.json()]
        assert ids == [p_mine.id]

    @pytest.mark.django_db
    def test_student_lists_only_own_project_evaluations(
        self, admin_user, student_user, project_factory, db
    ):
        """Student sees evaluations only for their own project (as student FK)."""
        other_student = _make_student("other@test.local")
        own_project = project_factory(student=student_user, title="Own")
        other_project = project_factory(student=other_student, title="Other")
        own_eval = Evaluation.objects.create(project=own_project, reviewer=admin_user, pass_status="Pass")
        Evaluation.objects.create(project=other_project, reviewer=admin_user, pass_status="Pass")

        client = APIClient()
        client.force_authenticate(user=student_user)
        response = client.get(EVALUATIONS_URL)
        assert response.status_code == 200
        ids = [e["id"] for e in response.json()]
        assert ids == [own_eval.id]

    @pytest.mark.django_db
    def test_student_as_partner_sees_evaluation(
        self, admin_user, student_user, project_factory, db
    ):
        """
        A student who is `partner` on a project must see evaluations for that
        project. The student/partner dynamic means both work on the same project
        and both need visibility into its evaluations.
        """
        owner = _make_student("owner@test.local")
        project = project_factory(student=owner, title="Shared", partner=student_user)
        evaluation = Evaluation.objects.create(project=project, reviewer=admin_user, pass_status="Pass")

        client = APIClient()
        client.force_authenticate(user=student_user)
        response = client.get(EVALUATIONS_URL)
        assert response.status_code == 200
        ids = [e["id"] for e in response.json()]
        assert evaluation.id in ids

    @pytest.mark.django_db
    def test_project_query_param_filters_for_admin(
        self, admin_user, student_user, project_factory
    ):
        p1 = project_factory(student=student_user, title="P1")
        p2 = project_factory(student=student_user, title="P2")
        e1 = Evaluation.objects.create(project=p1, reviewer=admin_user, pass_status="Pass")
        Evaluation.objects.create(project=p2, reviewer=admin_user, pass_status="Fail")

        client = APIClient()
        client.force_authenticate(user=admin_user)
        response = client.get(EVALUATIONS_URL, {"project": p1.id})
        assert response.status_code == 200
        ids = [e["id"] for e in response.json()]
        assert ids == [e1.id]

    @pytest.mark.django_db
    def test_project_query_param_respects_student_scope(
        self, admin_user, student_user, project_factory, db
    ):
        """
        Student querying ?project=<other_project_id> gets an empty list,
        not 403 and not a leak of the other project's evaluations.
        """
        other_student = _make_student("other2@test.local")
        other_project = project_factory(student=other_student, title="Other")
        Evaluation.objects.create(project=other_project, reviewer=admin_user, pass_status="Pass")

        client = APIClient()
        client.force_authenticate(user=student_user)
        response = client.get(EVALUATIONS_URL, {"project": other_project.id})
        assert response.status_code == 200
        assert len(response.json()) == 0

    @pytest.mark.django_db
    def test_tutor_filtered_by_project_query_param_for_unassigned_project(
        self, admin_user, tutor_user, student_user, project_factory, db
    ):
        """
        Tutor queries ?project=<project_id> for a project they do NOT advise.
        Must return 200 with empty list, not a 403 or data leak.
        """
        other_student = _make_student("other3@test.local")
        unassigned_project = project_factory(student=other_student, title="Unassigned")
        Evaluation.objects.create(project=unassigned_project, reviewer=admin_user, pass_status="Pass")

        client = APIClient()
        client.force_authenticate(user=tutor_user)
        response = client.get(EVALUATIONS_URL, {"project": unassigned_project.id})
        assert response.status_code == 200
        assert len(response.json()) == 0

    @pytest.mark.django_db
    def test_tutor_filtered_by_project_query_param_for_assigned_project(
        self, admin_user, tutor_user, student_user, project_factory
    ):
        """
        Tutor queries ?project=<project_id> for a project they DO advise.
        Must return only evaluations for that project.
        """
        assigned_project = project_factory(
            student=student_user, title="Assigned", advisors=[tutor_user]
        )
        evaluation = Evaluation.objects.create(
            project=assigned_project, reviewer=admin_user, pass_status="Pass"
        )

        client = APIClient()
        client.force_authenticate(user=tutor_user)
        response = client.get(EVALUATIONS_URL, {"project": assigned_project.id})
        assert response.status_code == 200
        ids = [e["id"] for e in response.json()]
        assert evaluation.id in ids

    @pytest.mark.django_db
    def test_student_as_partner_can_filter_by_project(
        self, admin_user, student_user, project_factory, db
    ):
        """
        A student who is `partner` on a project queries ?project=<partner_project_id>.
        Must see the evaluations for that project.
        """
        owner = _make_student("owner2@test.local")
        partner_project = project_factory(student=owner, title="Partner Project", partner=student_user)
        evaluation = Evaluation.objects.create(
            project=partner_project, reviewer=admin_user, pass_status="Pass"
        )

        client = APIClient()
        client.force_authenticate(user=student_user)
        response = client.get(EVALUATIONS_URL, {"project": partner_project.id})
        assert response.status_code == 200
        ids = [e["id"] for e in response.json()]
        assert evaluation.id in ids

    @pytest.mark.django_db
    def test_tutor_cannot_retrieve_evaluation_on_unassigned_project(
        self, admin_user, tutor_user, student_user, project_factory, db
    ):
        """
        Tutor GETs /api/evaluations/<id>/ for an evaluation on a project they
        do not advise. DRF returns 404 for objects outside get_queryset scope.
        """
        other_student = _make_student("other4@test.local")
        unadvised_project = project_factory(student=other_student, title="Unadvised")
        evaluation = Evaluation.objects.create(
            project=unadvised_project, reviewer=admin_user, pass_status="Pass"
        )

        client = APIClient()
        client.force_authenticate(user=tutor_user)
        response = client.get(f"{EVALUATIONS_URL}{evaluation.id}/")
        assert response.status_code == 404

    @pytest.mark.django_db
    def test_student_as_partner_can_retrieve_evaluation(
        self, admin_user, student_user, project_factory, db
    ):
        """
        A student who is `partner` on a project GETs /api/evaluations/<id>/.
        Must return 200 (partner has visibility into partner project evaluations).
        """
        owner = _make_student("owner5@test.local")
        partner_project = project_factory(student=owner, title="Partner Project 2", partner=student_user)
        evaluation = Evaluation.objects.create(
            project=partner_project, reviewer=admin_user, pass_status="Pass"
        )

        client = APIClient()
        client.force_authenticate(user=student_user)
        response = client.get(f"{EVALUATIONS_URL}{evaluation.id}/")
        assert response.status_code == 200


# ---------------------------------------------------------------------------
# Create validation tests
# ---------------------------------------------------------------------------


class TestCreateValidation:
    @pytest.mark.django_db
    def test_create_without_project_field_returns_400(self, admin_user):
        client = APIClient()
        client.force_authenticate(user=admin_user)
        response = client.post(EVALUATIONS_URL, {"pass_status": "Pass"}, format="json")
        assert response.status_code == 400

    @pytest.mark.django_db
    def test_create_with_nonexistent_project_returns_400(self, admin_user):
        client = APIClient()
        client.force_authenticate(user=admin_user)
        response = client.post(
            EVALUATIONS_URL, {"project": 99999, "pass_status": "Pass"}, format="json"
        )
        assert response.status_code == 400
