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
        assert pteg.status == "rejected"


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
        assert pteg.status == "checked"

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

    @pytest.mark.django_db
    def test_any_eval_on_failed_final_rejected(self, jurado_user, student_user, project_factory):
        pteg = project_factory(student=student_user, reviewer=jurado_user, state="failed_final")
        client = APIClient()
        client.force_authenticate(user=jurado_user)
        resp = client.post(EVALUATIONS_URL, _fail_payload(pteg.id, kind="review"), format="json")
        assert resp.status_code == 400


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
