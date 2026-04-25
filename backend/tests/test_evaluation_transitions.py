"""Integration tests for PTEG state transitions driven by Evaluation creation."""

import pytest
from rest_framework.test import APIClient

EVALUATIONS_URL = "/api/evaluations/"


def _pass_payload(project_id, kind="review"):
    return {
        "project": project_id,
        "kind": kind,
        "pass_status": "Pass",
        "score": 18,
    }


def _fail_payload(project_id, kind="review"):
    return {
        "project": project_id,
        "kind": kind,
        "pass_status": "Fail",
        "score": 5,
    }


@pytest.fixture
def pteg(db, student_user, jurado_user, project_factory):
    """A PTEG in pending_review_1 assigned to jurado_user."""
    return project_factory(
        student=student_user,
        reviewer=jurado_user,
        state="pending_review_1",
    )


class TestReviewTransitions:
    @pytest.mark.django_db
    def test_review_pass_on_pending_review_1_moves_to_pending_defense(self, pteg, jurado_user):
        client = APIClient()
        client.force_authenticate(user=jurado_user)
        resp = client.post(EVALUATIONS_URL, _pass_payload(pteg.id), format="json")
        assert resp.status_code == 201, resp.content
        pteg.refresh_from_db()
        assert pteg.state == "pending_defense"
        assert pteg.status == "pending"

    @pytest.mark.django_db
    def test_review_fail_on_pending_review_1_moves_to_pending_review_2(self, pteg, jurado_user):
        client = APIClient()
        client.force_authenticate(user=jurado_user)
        resp = client.post(EVALUATIONS_URL, _fail_payload(pteg.id), format="json")
        assert resp.status_code == 201, resp.content
        pteg.refresh_from_db()
        assert pteg.state == "pending_review_2"
        assert pteg.status == "pending"

    @pytest.mark.django_db
    def test_review_pass_on_pending_review_2_moves_to_pending_defense(self, jurado_user, student_user, project_factory):
        pteg = project_factory(student=student_user, reviewer=jurado_user, state="pending_review_2")
        client = APIClient()
        client.force_authenticate(user=jurado_user)
        resp = client.post(EVALUATIONS_URL, _pass_payload(pteg.id), format="json")
        assert resp.status_code == 201, resp.content
        pteg.refresh_from_db()
        assert pteg.state == "pending_defense"

    @pytest.mark.django_db
    def test_review_fail_on_pending_review_2_moves_to_failed_final(self, jurado_user, student_user, project_factory):
        pteg = project_factory(student=student_user, reviewer=jurado_user, state="pending_review_2")
        client = APIClient()
        client.force_authenticate(user=jurado_user)
        resp = client.post(EVALUATIONS_URL, _fail_payload(pteg.id), format="json")
        assert resp.status_code == 201, resp.content
        pteg.refresh_from_db()
        assert pteg.state == "failed_final"


class TestDefenseTransitions:
    @pytest.mark.django_db
    def test_defense_pass_on_pending_defense_moves_to_approved(self, jurado_user, student_user, project_factory):
        pteg = project_factory(student=student_user, reviewer=jurado_user, state="pending_defense")
        client = APIClient()
        client.force_authenticate(user=jurado_user)
        resp = client.post(EVALUATIONS_URL, _pass_payload(pteg.id, kind="defense"), format="json")
        assert resp.status_code == 201, resp.content
        pteg.refresh_from_db()
        assert pteg.state == "approved"

    @pytest.mark.django_db
    def test_defense_fail_on_pending_defense_stays_pending_defense(self, jurado_user, student_user, project_factory):
        pteg = project_factory(student=student_user, reviewer=jurado_user, state="pending_defense")
        client = APIClient()
        client.force_authenticate(user=jurado_user)
        resp = client.post(EVALUATIONS_URL, _fail_payload(pteg.id, kind="defense"), format="json")
        assert resp.status_code == 201, resp.content
        pteg.refresh_from_db()
        assert pteg.state == "pending_defense"
        assert pteg.status == "pending"

    @pytest.mark.django_db
    def test_admin_can_record_defense(self, admin_user, jurado_user, student_user, project_factory):
        pteg = project_factory(student=student_user, reviewer=jurado_user, state="pending_defense")
        client = APIClient()
        client.force_authenticate(user=admin_user)
        resp = client.post(EVALUATIONS_URL, _pass_payload(pteg.id, kind="defense"), format="json")
        assert resp.status_code == 201, resp.content
        pteg.refresh_from_db()
        assert pteg.state == "approved"


class TestIllegalTransitions:
    @pytest.mark.django_db
    def test_review_on_pending_defense_rejected(self, jurado_user, student_user, project_factory):
        pteg = project_factory(student=student_user, reviewer=jurado_user, state="pending_defense")
        client = APIClient()
        client.force_authenticate(user=jurado_user)
        resp = client.post(EVALUATIONS_URL, _pass_payload(pteg.id, kind="review"), format="json")
        assert resp.status_code == 400

    @pytest.mark.django_db
    def test_defense_on_pending_review_1_rejected(self, pteg, jurado_user):
        client = APIClient()
        client.force_authenticate(user=jurado_user)
        resp = client.post(EVALUATIONS_URL, _pass_payload(pteg.id, kind="defense"), format="json")
        assert resp.status_code == 400

    @pytest.mark.django_db
    def test_any_eval_on_approved_rejected(self, jurado_user, student_user, project_factory):
        pteg = project_factory(student=student_user, reviewer=jurado_user, state="approved")
        client = APIClient()
        client.force_authenticate(user=jurado_user)
        resp = client.post(EVALUATIONS_URL, _pass_payload(pteg.id, kind="review"), format="json")
        assert resp.status_code == 400
        pteg.refresh_from_db()
        assert pteg.state == "approved"

    @pytest.mark.django_db
    def test_any_eval_on_failed_final_rejected(self, jurado_user, student_user, project_factory):
        pteg = project_factory(student=student_user, reviewer=jurado_user, state="failed_final")
        client = APIClient()
        client.force_authenticate(user=jurado_user)
        resp = client.post(EVALUATIONS_URL, _fail_payload(pteg.id, kind="review"), format="json")
        assert resp.status_code == 400
        pteg.refresh_from_db()
        assert pteg.state == "failed_final"


class TestGuards:
    @pytest.mark.django_db
    def test_unassigned_jurado_cannot_create_evaluation(self, jurado_user, student_user, project_factory):
        pteg = project_factory(student=student_user, reviewer=None, state="pending_review_1")
        client = APIClient()
        client.force_authenticate(user=jurado_user)
        resp = client.post(EVALUATIONS_URL, _pass_payload(pteg.id), format="json")
        assert resp.status_code == 403

    @pytest.mark.django_db
    def test_kind_defaults_to_review_when_omitted(self, pteg, jurado_user):
        client = APIClient()
        client.force_authenticate(user=jurado_user)
        payload = {"project": pteg.id, "pass_status": "Pass", "score": 15}  # no kind
        resp = client.post(EVALUATIONS_URL, payload, format="json")
        assert resp.status_code == 201, resp.content
        pteg.refresh_from_db()
        assert pteg.state == "pending_defense"

    @pytest.mark.django_db
    def test_admin_can_evaluate_project_assigned_to_different_jurado(
        self, admin_user, jurado_user, student_user, project_factory
    ):
        """
        Regla: el guard 'unassigned jurado → 403' SÓLO aplica a Jurado;
        Administrador bypassa el chequeo y puede evaluar cualquier proyecto
        independientemente de quién sea el reviewer asignado.
        """
        # Project is assigned to jurado_user, NOT to admin.
        pteg = project_factory(
            student=student_user,
            reviewer=jurado_user,
            state="pending_review_1",
        )
        client = APIClient()
        client.force_authenticate(user=admin_user)
        resp = client.post(EVALUATIONS_URL, _pass_payload(pteg.id), format="json")
        assert resp.status_code == 201, resp.content
        pteg.refresh_from_db()
        assert pteg.state == "pending_defense"


class TestDerivedFailedAttempts:
    @pytest.mark.django_db
    def test_failed_attempts_is_zero_with_no_evals(self, pteg, jurado_user):
        client = APIClient()
        client.force_authenticate(user=jurado_user)
        resp = client.get(f"/api/projects/{pteg.id}/")
        assert resp.status_code == 200
        assert resp.json()["failed_attempts"] == 0

    @pytest.mark.django_db
    def test_failed_attempts_increments_with_fail_evals(self, pteg, jurado_user):
        client = APIClient()
        client.force_authenticate(user=jurado_user)
        # First fail → pending_review_2
        client.post(EVALUATIONS_URL, _fail_payload(pteg.id), format="json")
        resp = client.get(f"/api/projects/{pteg.id}/")
        assert resp.status_code == 200
        assert resp.json()["failed_attempts"] == 1
        # Second fail → failed_final
        client.post(EVALUATIONS_URL, _fail_payload(pteg.id), format="json")
        resp = client.get(f"/api/projects/{pteg.id}/")
        assert resp.status_code == 200
        assert resp.json()["failed_attempts"] == 2

    @pytest.mark.django_db
    def test_failed_attempts_is_zero_for_tesis(self, jurado_user, student_user, project_factory):
        tesis = project_factory(student=student_user, reviewer=jurado_user, project_type='tesis')
        client = APIClient()
        client.force_authenticate(user=jurado_user)
        resp = client.get(f"/api/projects/{tesis.id}/")
        assert resp.status_code == 200
        assert resp.json()["failed_attempts"] == 0

    @pytest.mark.django_db
    def test_defense_fail_does_not_count_as_failed_attempt(self, pteg, jurado_user):
        """
        Regla: failed_attempts cuenta sólo evaluaciones kind='review'. Una defensa
        fallida NO incrementa el contador — el proyecto permanece en pending_defense
        y puede reprogramarse, no consume un intento de revisión.
        """
        client = APIClient()
        client.force_authenticate(user=jurado_user)
        # First advance to pending_defense via a review Pass
        client.post(EVALUATIONS_URL, _pass_payload(pteg.id, kind="review"), format="json")
        # Now post a defense Fail — should NOT increment failed_attempts
        client.post(EVALUATIONS_URL, _fail_payload(pteg.id, kind="defense"), format="json")
        resp = client.get(f"/api/projects/{pteg.id}/")
        assert resp.status_code == 200
        assert resp.json()["failed_attempts"] == 0

    @pytest.mark.django_db
    def test_patch_to_failed_attempts_is_noop(self, pteg, jurado_user):
        """
        failed_attempts es SerializerMethodField (read-only). PATCH con un valor
        arbitrario no debe mutarlo — DRF silenciosamente ignora la escritura.
        Protege contra regresiones cuando Task 7 retira el PATCH del frontend.
        """
        client = APIClient()
        client.force_authenticate(user=jurado_user)
        resp = client.patch(f"/api/projects/{pteg.id}/", {"failed_attempts": 5}, format="json")
        assert resp.status_code in (200, 202)
        resp = client.get(f"/api/projects/{pteg.id}/")
        assert resp.json()["failed_attempts"] == 0
