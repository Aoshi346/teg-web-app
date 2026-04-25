"""
Integration tests for Wave 3 — dispatcher wiring into viewset actions.

Each test class verifies that hitting a real API endpoint produces the
expected Notification rows. The dispatchers themselves are tested in unit
isolation in test_notifications_dispatch.py; here we confirm the viewset
wiring is in place (i.e., the calls are made).

Phase RED — views.py does not yet call any dispatcher. All tests are expected
to fail with AssertionError on Notification.objects.filter(...).exists().
"""

import pytest
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient

from api.models import Notification, Project, Semester

User = get_user_model()

# ---------------------------------------------------------------------------
# Module-level autouse: silence email during integration tests
# ---------------------------------------------------------------------------


@pytest.fixture(autouse=True)
def _use_locmem_email(settings):
    """
    Fuerza el backend de correo a locmem para evitar salidas en consola y
    hacer los tests deterministas. No afecta la lógica bajo prueba.
    """
    settings.EMAIL_BACKEND = "django.core.mail.backends.locmem.EmailBackend"
    settings.DEFAULT_FROM_EMAIL = "noreply@tesisfar.local"


# ---------------------------------------------------------------------------
# Local factory helpers (mirrors dispatch test conventions)
# ---------------------------------------------------------------------------

_user_counter = 0


def _make_user(role="Estudiante", email=None, **kwargs):
    """Crea un usuario mínimo con el rol indicado."""
    global _user_counter
    _user_counter += 1
    if email is None:
        safe_role = role.lower().replace(" ", "_")
        email = f"{safe_role}_{_user_counter}@integ.test"
    return User.objects.create_user(
        email=email,
        password="TestPass123!",
        first_name="Test",
        last_name="User",
        role=role,
        status="active",
        **kwargs,
    )


def _make_project(student, *, partner=None, advisors=None, reviewer=None,
                  project_type="proyecto", state="pending_review_1"):
    """
    Crea un Project mínimo. Si project_type='tesis' no usa lifecycle state.
    Los advisors deben ser usuarios con role='Tutor'.
    """
    project = Project.objects.create(
        title="Integration Test Project",
        student=student,
        partner=partner,
        reviewer=reviewer,
        project_type=project_type,
        state=state,
        period="",
    )
    if advisors:
        project.advisors.set(advisors)
    return project


def _authed_client(user):
    client = APIClient()
    client.force_authenticate(user=user)
    return client


# ---------------------------------------------------------------------------
# 1. TestEvaluationCreateWiring
# ---------------------------------------------------------------------------


class TestEvaluationCreateWiring:
    """POST /api/evaluations/ must call dispatch_evaluation_received and,
    when the PTEG state advances, also dispatch_state_change(kind_source='evaluation')."""

    @pytest.mark.django_db
    def test_evaluation_received_rows_created_for_student_and_partner(self):
        """Jurado creates evaluation → student + partner each get an evaluation_received row."""
        jurado = _make_user(role="Jurado")
        student = _make_user(role="Estudiante")
        partner = _make_user(role="Estudiante")
        project = _make_project(student, partner=partner, reviewer=jurado)

        client = _authed_client(jurado)
        resp = client.post("/api/evaluations/", {
            "project": project.pk,
            "pass_status": "Pass",
            "kind": "review",
            "score": 75.0,
        }, format="json")

        assert resp.status_code == 201, resp.data

        assert Notification.objects.filter(
            recipient=student, kind="evaluation_received"
        ).exists()
        assert Notification.objects.filter(
            recipient=partner, kind="evaluation_received"
        ).exists()

    @pytest.mark.django_db
    def test_jurado_actor_excluded_from_evaluation_received(self):
        """The Jurado who submits the evaluation must NOT receive an evaluation_received row."""
        jurado = _make_user(role="Jurado")
        student = _make_user(role="Estudiante")
        project = _make_project(student, reviewer=jurado)

        client = _authed_client(jurado)
        client.post("/api/evaluations/", {
            "project": project.pk,
            "pass_status": "Pass",
            "kind": "review",
            "score": 75.0,
        }, format="json")

        assert not Notification.objects.filter(
            recipient=jurado, kind="evaluation_received"
        ).exists()

    @pytest.mark.django_db
    def test_state_change_rows_created_when_pteg_state_advances(self):
        """When a PTEG evaluation causes a state transition, state_change rows are created."""
        jurado = _make_user(role="Jurado")
        student = _make_user(role="Estudiante")
        advisor = _make_user(role="Tutor")
        project = _make_project(
            student, advisors=[advisor], reviewer=jurado,
            project_type="proyecto", state="pending_review_1"
        )

        client = _authed_client(jurado)
        resp = client.post("/api/evaluations/", {
            "project": project.pk,
            "pass_status": "Pass",
            "kind": "review",
            "score": 80.0,
        }, format="json")

        assert resp.status_code == 201, resp.data

        # state should have advanced → state_change notification expected
        assert Notification.objects.filter(
            recipient=student, kind="state_change"
        ).exists()
        # advisor also notified on evaluation-triggered state change
        assert Notification.objects.filter(
            recipient=advisor, kind="state_change"
        ).exists()

    @pytest.mark.django_db
    def test_state_change_payload_reflects_kind_source_evaluation(self):
        """state_change notifications from an evaluation must carry kind_source='evaluation' in payload."""
        jurado = _make_user(role="Jurado")
        student = _make_user(role="Estudiante")
        project = _make_project(
            student, reviewer=jurado,
            project_type="proyecto", state="pending_review_1"
        )

        client = _authed_client(jurado)
        client.post("/api/evaluations/", {
            "project": project.pk,
            "pass_status": "Pass",
            "kind": "review",
            "score": 80.0,
        }, format="json")

        notif = Notification.objects.filter(
            recipient=student, kind="state_change"
        ).first()
        assert notif is not None
        assert notif.payload.get("kind_source") == "evaluation"

    @pytest.mark.django_db
    def test_evaluation_received_payload_and_link_url_set(self):
        """evaluation_received notifications must have a non-empty payload and link_url."""
        jurado = _make_user(role="Jurado")
        student = _make_user(role="Estudiante")
        project = _make_project(student, reviewer=jurado)

        client = _authed_client(jurado)
        client.post("/api/evaluations/", {
            "project": project.pk,
            "pass_status": "Pass",
            "kind": "review",
            "score": 75.0,
        }, format="json")

        notif = Notification.objects.filter(
            recipient=student, kind="evaluation_received"
        ).first()
        assert notif is not None
        assert notif.payload  # non-empty dict
        assert notif.link_url  # non-empty string


# ---------------------------------------------------------------------------
# 2. TestAssignReviewerWiring
# ---------------------------------------------------------------------------


class TestAssignReviewerWiring:
    """POST /api/projects/<id>/assign_reviewer/ must call dispatch_assignment."""

    @pytest.mark.django_db
    def test_new_reviewer_gets_assignment_notification(self):
        """When a Jurado is assigned, they get an 'assignment' notification."""
        admin = _make_user(role="Administrador")
        student = _make_user(role="Estudiante")
        jurado = _make_user(role="Jurado")
        project = _make_project(student)

        client = _authed_client(admin)
        resp = client.post(f"/api/projects/{project.pk}/assign_reviewer/", {
            "reviewer": jurado.pk,
        }, format="json")

        assert resp.status_code == 200, resp.data
        assert Notification.objects.filter(
            recipient=jurado, kind="assignment"
        ).exists()

    @pytest.mark.django_db
    def test_previous_reviewer_gets_unassignment_notification(self):
        """When a reviewer is replaced, the previous reviewer gets an 'assignment' unassignment row."""
        admin = _make_user(role="Administrador")
        student = _make_user(role="Estudiante")
        old_jurado = _make_user(role="Jurado")
        new_jurado = _make_user(role="Jurado")
        project = _make_project(student, reviewer=old_jurado)

        client = _authed_client(admin)
        resp = client.post(f"/api/projects/{project.pk}/assign_reviewer/", {
            "reviewer": new_jurado.pk,
        }, format="json")

        assert resp.status_code == 200, resp.data
        # old reviewer notified of removal (also kind='assignment')
        assert Notification.objects.filter(
            recipient=old_jurado, kind="assignment"
        ).exists()
        # new reviewer notified of assignment
        assert Notification.objects.filter(
            recipient=new_jurado, kind="assignment"
        ).exists()

    @pytest.mark.django_db
    def test_admin_actor_excluded_from_assignment_notification(self):
        """The admin who performs the assignment must NOT receive an assignment row."""
        admin = _make_user(role="Administrador")
        student = _make_user(role="Estudiante")
        jurado = _make_user(role="Jurado")
        project = _make_project(student)

        client = _authed_client(admin)
        client.post(f"/api/projects/{project.pk}/assign_reviewer/", {
            "reviewer": jurado.pk,
        }, format="json")

        assert not Notification.objects.filter(recipient=admin, kind="assignment").exists()


# ---------------------------------------------------------------------------
# 3. TestOverrideStateWiring
# ---------------------------------------------------------------------------


class TestOverrideStateWiring:
    """POST /api/projects/<id>/override_state/ must call dispatch_state_change(kind_source='override')."""

    @pytest.mark.django_db
    def test_state_change_notification_created_for_student(self):
        """Admin override produces a state_change notification for the project student."""
        admin = _make_user(role="Administrador")
        student = _make_user(role="Estudiante")
        project = _make_project(
            student, project_type="proyecto", state="pending_review_1"
        )

        client = _authed_client(admin)
        resp = client.post(f"/api/projects/{project.pk}/override_state/", {
            "state": "pending_defense",
            "reason": "Admin override for testing purposes",
        }, format="json")

        assert resp.status_code == 200, resp.data
        assert Notification.objects.filter(
            recipient=student, kind="state_change"
        ).exists()

    @pytest.mark.django_db
    def test_state_change_payload_has_kind_source_override(self):
        """The state_change notification from override must carry kind_source='override' in payload."""
        admin = _make_user(role="Administrador")
        student = _make_user(role="Estudiante")
        project = _make_project(
            student, project_type="proyecto", state="pending_review_1"
        )

        client = _authed_client(admin)
        client.post(f"/api/projects/{project.pk}/override_state/", {
            "state": "pending_defense",
            "reason": "Admin override for integration test",
        }, format="json")

        notif = Notification.objects.filter(
            recipient=student, kind="state_change"
        ).first()
        assert notif is not None
        assert notif.payload.get("kind_source") == "override"

    @pytest.mark.django_db
    def test_reviewer_also_notified_on_override(self):
        """With kind_source='override', the reviewer must also receive a state_change row."""
        admin = _make_user(role="Administrador")
        student = _make_user(role="Estudiante")
        jurado = _make_user(role="Jurado")
        project = _make_project(
            student, reviewer=jurado,
            project_type="proyecto", state="pending_review_1"
        )

        client = _authed_client(admin)
        client.post(f"/api/projects/{project.pk}/override_state/", {
            "state": "pending_defense",
            "reason": "Admin override includes reviewer notification",
        }, format="json")

        assert Notification.objects.filter(
            recipient=jurado, kind="state_change"
        ).exists()

    @pytest.mark.django_db
    def test_admin_actor_excluded_from_override_state_notification(self):
        """The admin who performs the override must NOT receive a state_change row."""
        admin = _make_user(role="Administrador")
        student = _make_user(role="Estudiante")
        project = _make_project(
            student, project_type="proyecto", state="pending_review_1"
        )

        client = _authed_client(admin)
        client.post(f"/api/projects/{project.pk}/override_state/", {
            "state": "pending_defense",
            "reason": "Admin override actor exclusion test",
        }, format="json")

        assert not Notification.objects.filter(
            recipient=admin, kind="state_change"
        ).exists()


# ---------------------------------------------------------------------------
# 4. TestCommentCreateWiring
# ---------------------------------------------------------------------------


class TestCommentCreateWiring:
    """POST /api/comments/ must call dispatch_comment_added."""

    @pytest.mark.django_db
    def test_comment_notification_created_for_project_participants(self):
        """When a tutor posts a comment, student and reviewer get comment_added rows."""
        admin = _make_user(role="Administrador")
        student = _make_user(role="Estudiante")
        jurado = _make_user(role="Jurado")
        tutor = _make_user(role="Tutor")
        project = _make_project(student, reviewer=jurado, advisors=[tutor])

        client = _authed_client(tutor)
        resp = client.post("/api/comments/", {
            "project": project.pk,
            "content": "Great progress on your project!",
        }, format="json")

        assert resp.status_code == 201, resp.data
        assert Notification.objects.filter(
            recipient=student, kind="comment_added"
        ).exists()
        assert Notification.objects.filter(
            recipient=jurado, kind="comment_added"
        ).exists()

    @pytest.mark.django_db
    def test_comment_author_excluded_from_comment_notification(self):
        """The user who posts the comment must NOT receive a comment_added notification."""
        student = _make_user(role="Estudiante")
        jurado = _make_user(role="Jurado")
        project = _make_project(student, reviewer=jurado)

        client = _authed_client(student)
        client.post("/api/comments/", {
            "project": project.pk,
            "content": "This is my own comment, I should not be notified.",
        }, format="json")

        assert not Notification.objects.filter(
            recipient=student, kind="comment_added"
        ).exists()

    @pytest.mark.django_db
    def test_comment_notification_includes_partner(self):
        """The project partner also receives a comment_added notification."""
        student = _make_user(role="Estudiante")
        partner = _make_user(role="Estudiante")
        jurado = _make_user(role="Jurado")
        project = _make_project(student, partner=partner, reviewer=jurado)

        client = _authed_client(jurado)
        client.post("/api/comments/", {
            "project": project.pk,
            "content": "Here is my review comment for both students.",
        }, format="json")

        assert Notification.objects.filter(
            recipient=partner, kind="comment_added"
        ).exists()

    @pytest.mark.django_db
    def test_comment_notification_payload_and_link_url_set(self):
        """comment_added notifications must have a non-empty payload and link_url."""
        student = _make_user(role="Estudiante")
        jurado = _make_user(role="Jurado")
        project = _make_project(student, reviewer=jurado)

        client = _authed_client(jurado)
        client.post("/api/comments/", {
            "project": project.pk,
            "content": "A comment that triggers a notification for the student.",
        }, format="json")

        notif = Notification.objects.filter(
            recipient=student, kind="comment_added"
        ).first()
        assert notif is not None
        assert notif.payload
        assert notif.link_url


# ---------------------------------------------------------------------------
# 5. TestSemesterActivateWiring
# ---------------------------------------------------------------------------


class TestSemesterActivateWiring:
    """POST /api/semesters/<id>/set_active/ must call dispatch_semester_activated."""

    @pytest.mark.django_db
    def test_semester_activated_notification_sent_to_all_students(self):
        """Activating a semester broadcasts semester_activated to all Estudiante users."""
        admin = _make_user(role="Administrador")
        student_a = _make_user(role="Estudiante")
        student_b = _make_user(role="Estudiante")
        # Non-student users should NOT receive the notification
        tutor = _make_user(role="Tutor")

        semester = Semester.objects.create(
            period="2099-01",
            is_active=False,
            start_month=1,
            end_month=6,
        )

        client = _authed_client(admin)
        resp = client.post(f"/api/semesters/{semester.pk}/set_active/", format="json")

        assert resp.status_code == 200, resp.data
        assert Notification.objects.filter(
            recipient=student_a, kind="semester_activated"
        ).exists()
        assert Notification.objects.filter(
            recipient=student_b, kind="semester_activated"
        ).exists()

    @pytest.mark.django_db
    def test_non_student_users_do_not_receive_semester_activated(self):
        """Tutors and Jurados must NOT receive semester_activated notifications."""
        admin = _make_user(role="Administrador")
        tutor = _make_user(role="Tutor")
        jurado = _make_user(role="Jurado")

        semester = Semester.objects.create(
            period="2099-02",
            is_active=False,
            start_month=7,
            end_month=12,
        )

        client = _authed_client(admin)
        client.post(f"/api/semesters/{semester.pk}/set_active/", format="json")

        assert not Notification.objects.filter(
            recipient=tutor, kind="semester_activated"
        ).exists()
        assert not Notification.objects.filter(
            recipient=jurado, kind="semester_activated"
        ).exists()

    @pytest.mark.django_db
    def test_admin_actor_excluded_from_semester_activated_when_admin_is_student(self):
        """Edge case: if the activating admin also has role=Estudiante (degenerate), they are excluded."""
        # Create a student who activates the semester (degenerate but valid to test)
        student_actor = _make_user(role="Estudiante")
        other_student = _make_user(role="Estudiante")

        semester = Semester.objects.create(
            period="2099-03",
            is_active=False,
            start_month=1,
            end_month=6,
        )

        # Promote student to admin so the endpoint allows it, but the dispatcher
        # should exclude them from the recipient set as the actor
        student_actor.role = "Administrador"
        student_actor.save()

        client = _authed_client(student_actor)
        client.post(f"/api/semesters/{semester.pk}/set_active/", format="json")

        # other_student must be notified
        assert Notification.objects.filter(
            recipient=other_student, kind="semester_activated"
        ).exists()
        # actor (now admin) not a student anymore, so excluded anyway; confirming no row
        assert not Notification.objects.filter(
            recipient=student_actor, kind="semester_activated"
        ).exists()


# ---------------------------------------------------------------------------
# 6. TestTransactionalRollback
# ---------------------------------------------------------------------------


class TestTransactionalRollback:
    """If the action raises after dispatch inside the same transaction.atomic() block,
    no Notification rows must persist."""

    @pytest.mark.django_db
    def test_no_notifications_persist_when_evaluation_create_rolls_back(self, monkeypatch):
        """
        Simulates a database error late in EvaluationViewSet.perform_create by
        monkeypatching Project.save to raise after the dispatcher would have been
        called. The atomic block must roll back, leaving Notification.objects empty.
        """
        # Note: we patch Project.save (called after dispatch in perform_create) to
        # raise IntegrityError, which forces the outer transaction.atomic() to roll back.
        from django.db import IntegrityError as DbIntegrityError

        jurado = _make_user(role="Jurado")
        student = _make_user(role="Estudiante")
        project = _make_project(
            student, reviewer=jurado,
            project_type="proyecto", state="pending_review_1"
        )

        def patched_save(self, *args, **kwargs):
            raise DbIntegrityError("Simulated rollback trigger")

        monkeypatch.setattr(Project, "save", patched_save)

        client = _authed_client(jurado)
        client.raise_request_exception = False
        resp = client.post("/api/evaluations/", {
            "project": project.pk,
            "pass_status": "Pass",
            "kind": "review",
            "score": 75.0,
        }, format="json")

        assert resp.status_code >= 400

        # Critical assertion: no notification rows must have persisted
        assert Notification.objects.count() == 0, (
            f"Expected 0 notifications after rollback, got {Notification.objects.count()}"
        )
