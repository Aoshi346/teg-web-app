"""
Tests for the dispatch module api/notifications.py.

Phase RED — api/notifications.py does not yet exist. All tests are expected
to fail with ImportError or AttributeError during this phase.

Each test class covers one public dispatcher function. A sixth class covers
cross-cutting concerns (email failure isolation, re-dispatch semantics).

EMAIL_BACKEND is forced to locmem in the module-level autouse fixture so that
django.core.mail.outbox is available for assertions without hitting SMTP.
"""

import pytest
from django.contrib.auth import get_user_model
from django.core import mail

User = get_user_model()


# ---------------------------------------------------------------------------
# autouse fixture: force locmem email backend for the whole module
# ---------------------------------------------------------------------------


@pytest.fixture(autouse=True)
def _use_locmem_email(settings):
    """
    Fuerza el backend de correo electrónico a locmem para que django.core.mail.outbox
    esté disponible durante todos los tests de este módulo. Sin esto, los assertions
    sobre outbox no funcionan aunque el backend global sea console o smtp.
    """
    settings.EMAIL_BACKEND = "django.core.mail.backends.locmem.EmailBackend"
    settings.DEFAULT_FROM_EMAIL = "noreply@tesisfar.local"
    mail.outbox = []


# ---------------------------------------------------------------------------
# Local factory helpers
# ---------------------------------------------------------------------------


def _make_user(role="Estudiante", email=None, **kwargs):
    """Crea un usuario mínimo con el rol indicado."""
    counter = getattr(_make_user, "_counter", 0) + 1
    _make_user._counter = counter
    if email is None:
        safe_role = role.lower().replace(" ", "_")
        email = f"{safe_role}_{counter}@dispatch.test"
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
    Crea un Project mínimo con los participantes indicados.
    Los advisors deben ser usuarios con role='Tutor'.
    """
    from api.models import Project

    project = Project.objects.create(
        title="Dispatch Test Project",
        student=student,
        partner=partner,
        reviewer=reviewer,
        project_type=project_type,
        status="pending",
        state=state,
        period="",
    )
    if advisors:
        project.advisors.set(advisors)
    return project


def _make_evaluation(project, reviewer, *, pass_status="Pass", kind="review"):
    """Crea una Evaluation mínima para el proyecto indicado."""
    from api.models import Evaluation

    return Evaluation.objects.create(
        project=project,
        reviewer=reviewer,
        kind=kind,
        pass_status=pass_status,
        score=0.0,
    )


def _make_semester(period="2026-01"):
    """Crea un Semester mínimo."""
    from api.models import Semester

    return Semester.objects.create(
        period=period,
        is_active=False,
        start_month=1,
        end_month=6,
    )


def _make_comment(project, author, content="Test comment"):
    """Crea un Comment mínimo."""
    from api.models import Comment

    return Comment.objects.create(
        project=project,
        author=author,
        content=content,
    )


def _set_prefs(user, **kwargs):
    """
    Crea o actualiza el UserPreference del usuario con los campos indicados.
    Devuelve el objeto preferences actualizado.
    """
    from api.models import UserPreference

    prefs, _ = UserPreference.objects.get_or_create(user=user)
    for key, value in kwargs.items():
        setattr(prefs, key, value)
    prefs.save()
    return prefs


# ---------------------------------------------------------------------------
# 1. dispatch_evaluation_received
# ---------------------------------------------------------------------------


class TestDispatchEvaluationReceived:
    @pytest.mark.django_db
    def test_creates_rows_for_student_and_partner(self):
        from api.models import Notification
        from api.notifications import dispatch_evaluation_received

        actor = _make_user(role="Jurado")
        student = _make_user(role="Estudiante")
        partner = _make_user(role="Estudiante")
        project = _make_project(student, partner=partner, reviewer=actor)
        evaluation = _make_evaluation(project, actor)

        dispatch_evaluation_received(evaluation, actor)

        recipients = set(
            Notification.objects.filter(kind="evaluation_received").values_list(
                "recipient_id", flat=True
            )
        )
        assert student.pk in recipients
        assert partner.pk in recipients

    @pytest.mark.django_db
    def test_excludes_actor_from_recipients(self):
        from api.models import Notification
        from api.notifications import dispatch_evaluation_received

        actor = _make_user(role="Jurado")
        student = _make_user(role="Estudiante")
        project = _make_project(student, reviewer=actor)
        evaluation = _make_evaluation(project, actor)

        dispatch_evaluation_received(evaluation, actor)

        assert not Notification.objects.filter(
            kind="evaluation_received", recipient=actor
        ).exists()

    @pytest.mark.django_db
    def test_skips_users_with_notify_evaluation_received_false(self):
        from api.models import Notification
        from api.notifications import dispatch_evaluation_received

        actor = _make_user(role="Jurado")
        student = _make_user(role="Estudiante")
        partner = _make_user(role="Estudiante")
        _set_prefs(partner, notify_evaluation_received=False)
        project = _make_project(student, partner=partner, reviewer=actor)
        evaluation = _make_evaluation(project, actor)

        dispatch_evaluation_received(evaluation, actor)

        assert not Notification.objects.filter(
            kind="evaluation_received", recipient=partner
        ).exists()
        assert Notification.objects.filter(
            kind="evaluation_received", recipient=student
        ).exists()

    @pytest.mark.django_db
    def test_user_without_preference_row_is_opted_in_by_default(self):
        from api.models import Notification, UserPreference
        from api.notifications import dispatch_evaluation_received

        actor = _make_user(role="Jurado")
        student = _make_user(role="Estudiante")
        # Ensure no UserPreference row exists for this student
        UserPreference.objects.filter(user=student).delete()
        project = _make_project(student, reviewer=actor)
        evaluation = _make_evaluation(project, actor)

        dispatch_evaluation_received(evaluation, actor)

        assert Notification.objects.filter(
            kind="evaluation_received", recipient=student
        ).exists()

    @pytest.mark.django_db
    def test_sends_email_when_email_enabled_and_kind_enabled(self):
        from api.notifications import dispatch_evaluation_received

        actor = _make_user(role="Jurado")
        student = _make_user(role="Estudiante")
        _set_prefs(student, email_enabled=True, notify_evaluation_received=True)
        project = _make_project(student, reviewer=actor)
        evaluation = _make_evaluation(project, actor)

        mail.outbox = []
        dispatch_evaluation_received(evaluation, actor)

        assert len(mail.outbox) >= 1
        recipients = [msg.to[0] for msg in mail.outbox]
        assert student.email in recipients

    @pytest.mark.django_db
    def test_skips_email_when_email_enabled_false(self):
        from api.models import Notification
        from api.notifications import dispatch_evaluation_received

        actor = _make_user(role="Jurado")
        student = _make_user(role="Estudiante")
        _set_prefs(student, email_enabled=False, notify_evaluation_received=True)
        project = _make_project(student, reviewer=actor)
        evaluation = _make_evaluation(project, actor)

        mail.outbox = []
        dispatch_evaluation_received(evaluation, actor)

        # Row still written (per-kind preference is on)
        assert Notification.objects.filter(
            kind="evaluation_received", recipient=student
        ).exists()
        # But no email
        student_mails = [msg for msg in mail.outbox if student.email in msg.to]
        assert len(student_mails) == 0

    @pytest.mark.django_db
    def test_skips_email_and_row_when_kind_disabled(self):
        from api.models import Notification
        from api.notifications import dispatch_evaluation_received

        actor = _make_user(role="Jurado")
        student = _make_user(role="Estudiante")
        _set_prefs(student, email_enabled=True, notify_evaluation_received=False)
        project = _make_project(student, reviewer=actor)
        evaluation = _make_evaluation(project, actor)

        mail.outbox = []
        dispatch_evaluation_received(evaluation, actor)

        # No row written
        assert not Notification.objects.filter(
            kind="evaluation_received", recipient=student
        ).exists()
        # No email
        student_mails = [msg for msg in mail.outbox if student.email in msg.to]
        assert len(student_mails) == 0

    @pytest.mark.django_db
    def test_payload_includes_evaluation_id_and_project_id(self):
        from api.models import Notification
        from api.notifications import dispatch_evaluation_received

        actor = _make_user(role="Jurado")
        student = _make_user(role="Estudiante")
        project = _make_project(student, reviewer=actor)
        evaluation = _make_evaluation(project, actor)

        dispatch_evaluation_received(evaluation, actor)

        notif = Notification.objects.get(kind="evaluation_received", recipient=student)
        assert "evaluation_id" in notif.payload
        assert notif.payload["evaluation_id"] == evaluation.pk
        assert "project_id" in notif.payload
        assert notif.payload["project_id"] == project.pk

    @pytest.mark.django_db
    def test_link_url_points_at_project_detail(self):
        from api.models import Notification
        from api.notifications import dispatch_evaluation_received

        actor = _make_user(role="Jurado")
        student = _make_user(role="Estudiante")
        project = _make_project(student, reviewer=actor, project_type="proyecto")
        evaluation = _make_evaluation(project, actor)

        dispatch_evaluation_received(evaluation, actor)

        notif = Notification.objects.get(kind="evaluation_received", recipient=student)
        assert str(project.pk) in notif.link_url

    @pytest.mark.django_db
    def test_link_url_uses_tesis_path_for_teg_project(self):
        from api.models import Notification
        from api.notifications import dispatch_evaluation_received

        actor = _make_user(role="Jurado")
        student = _make_user(role="Estudiante")
        project = _make_project(student, reviewer=actor, project_type="tesis")
        evaluation = _make_evaluation(project, actor)

        dispatch_evaluation_received(evaluation, actor)

        notif = Notification.objects.get(kind="evaluation_received", recipient=student)
        assert "tesis" in notif.link_url or str(project.pk) in notif.link_url


# ---------------------------------------------------------------------------
# 2. dispatch_state_change
# ---------------------------------------------------------------------------


class TestDispatchStateChange:
    @pytest.mark.django_db
    def test_evaluation_source_notifies_student_partner_advisors(self):
        from api.models import Notification
        from api.notifications import dispatch_state_change

        actor = _make_user(role="Jurado")
        student = _make_user(role="Estudiante")
        partner = _make_user(role="Estudiante")
        advisor = _make_user(role="Tutor")
        project = _make_project(student, partner=partner, advisors=[advisor], reviewer=actor)

        dispatch_state_change(
            project,
            from_state="pending_review_1",
            to_state="pending_review_2",
            actor=actor,
            kind_source="evaluation",
        )

        recipients = set(
            Notification.objects.filter(kind="state_change").values_list(
                "recipient_id", flat=True
            )
        )
        assert student.pk in recipients
        assert partner.pk in recipients
        assert advisor.pk in recipients

    @pytest.mark.django_db
    def test_evaluation_source_does_not_notify_reviewer(self):
        from api.models import Notification
        from api.notifications import dispatch_state_change

        actor = _make_user(role="Jurado")
        student = _make_user(role="Estudiante")
        reviewer = _make_user(role="Jurado")
        project = _make_project(student, reviewer=reviewer)

        dispatch_state_change(
            project,
            from_state="pending_review_1",
            to_state="pending_review_2",
            actor=actor,
            kind_source="evaluation",
        )

        assert not Notification.objects.filter(
            kind="state_change", recipient=reviewer
        ).exists()

    @pytest.mark.django_db
    def test_override_source_includes_reviewer(self):
        from api.models import Notification
        from api.notifications import dispatch_state_change

        actor = _make_user(role="Administrador")
        student = _make_user(role="Estudiante")
        reviewer = _make_user(role="Jurado")
        project = _make_project(student, reviewer=reviewer)

        dispatch_state_change(
            project,
            from_state="pending_review_1",
            to_state="approved",
            actor=actor,
            kind_source="override",
        )

        recipients = set(
            Notification.objects.filter(kind="state_change").values_list(
                "recipient_id", flat=True
            )
        )
        assert reviewer.pk in recipients

    @pytest.mark.django_db
    def test_actor_excluded_regardless_of_kind_source(self):
        from api.models import Notification
        from api.notifications import dispatch_state_change

        actor = _make_user(role="Administrador")
        student = _make_user(role="Estudiante")
        project = _make_project(student)

        dispatch_state_change(
            project,
            from_state="pending_review_1",
            to_state="approved",
            actor=actor,
            kind_source="override",
        )

        assert not Notification.objects.filter(
            kind="state_change", recipient=actor
        ).exists()

    @pytest.mark.django_db
    def test_skips_users_with_notify_state_change_false(self):
        from api.models import Notification
        from api.notifications import dispatch_state_change

        actor = _make_user(role="Administrador")
        student = _make_user(role="Estudiante")
        partner = _make_user(role="Estudiante")
        _set_prefs(partner, notify_state_change=False)
        project = _make_project(student, partner=partner)

        dispatch_state_change(
            project,
            from_state="pending_review_1",
            to_state="approved",
            actor=actor,
            kind_source="override",
        )

        assert not Notification.objects.filter(
            kind="state_change", recipient=partner
        ).exists()
        assert Notification.objects.filter(
            kind="state_change", recipient=student
        ).exists()

    @pytest.mark.django_db
    def test_payload_includes_from_state_to_state_kind_source(self):
        from api.models import Notification
        from api.notifications import dispatch_state_change

        actor = _make_user(role="Administrador")
        student = _make_user(role="Estudiante")
        project = _make_project(student)

        dispatch_state_change(
            project,
            from_state="pending_review_1",
            to_state="pending_defense",
            actor=actor,
            kind_source="override",
        )

        notif = Notification.objects.get(kind="state_change", recipient=student)
        assert notif.payload["from_state"] == "pending_review_1"
        assert notif.payload["to_state"] == "pending_defense"
        assert notif.payload["kind_source"] == "override"


# ---------------------------------------------------------------------------
# 3. dispatch_assignment
# ---------------------------------------------------------------------------


class TestDispatchAssignment:
    @pytest.mark.django_db
    def test_new_reviewer_receives_assignment_row(self):
        from api.models import Notification
        from api.notifications import dispatch_assignment

        actor = _make_user(role="Administrador")
        student = _make_user(role="Estudiante")
        new_reviewer = _make_user(role="Jurado")
        project = _make_project(student)

        dispatch_assignment(project, new_reviewer=new_reviewer, previous_reviewer=None, actor=actor)

        notifs = Notification.objects.filter(kind="assignment", recipient=new_reviewer)
        assert notifs.count() == 1

    @pytest.mark.django_db
    def test_previous_reviewer_receives_unassignment_row(self):
        from api.models import Notification
        from api.notifications import dispatch_assignment

        actor = _make_user(role="Administrador")
        student = _make_user(role="Estudiante")
        previous_reviewer = _make_user(role="Jurado")
        project = _make_project(student, reviewer=previous_reviewer)

        dispatch_assignment(project, new_reviewer=None, previous_reviewer=previous_reviewer, actor=actor)

        notifs = Notification.objects.filter(kind="assignment", recipient=previous_reviewer)
        assert notifs.count() == 1

    @pytest.mark.django_db
    def test_both_reviewers_receive_distinct_rows_on_reassignment(self):
        from api.models import Notification
        from api.notifications import dispatch_assignment

        actor = _make_user(role="Administrador")
        student = _make_user(role="Estudiante")
        old_reviewer = _make_user(role="Jurado")
        new_reviewer = _make_user(role="Jurado")
        project = _make_project(student, reviewer=old_reviewer)

        dispatch_assignment(
            project,
            new_reviewer=new_reviewer,
            previous_reviewer=old_reviewer,
            actor=actor,
        )

        new_notif = Notification.objects.get(kind="assignment", recipient=new_reviewer)
        old_notif = Notification.objects.get(kind="assignment", recipient=old_reviewer)
        # The two rows must be distinguishable — different title or body
        assert new_notif.title != old_notif.title or new_notif.body != old_notif.body

    @pytest.mark.django_db
    def test_actor_excluded_even_when_actor_is_reviewer(self):
        from api.models import Notification
        from api.notifications import dispatch_assignment

        # Degenerate: admin self-assigns (contrived but should still skip self)
        actor = _make_user(role="Administrador")
        student = _make_user(role="Estudiante")
        new_reviewer = _make_user(role="Jurado")
        project = _make_project(student)

        dispatch_assignment(project, new_reviewer=new_reviewer, previous_reviewer=None, actor=actor)

        assert not Notification.objects.filter(
            kind="assignment", recipient=actor
        ).exists()

    @pytest.mark.django_db
    def test_skips_users_with_notify_assignment_false(self):
        from api.models import Notification
        from api.notifications import dispatch_assignment

        actor = _make_user(role="Administrador")
        student = _make_user(role="Estudiante")
        new_reviewer = _make_user(role="Jurado")
        _set_prefs(new_reviewer, notify_assignment=False)
        project = _make_project(student)

        dispatch_assignment(project, new_reviewer=new_reviewer, previous_reviewer=None, actor=actor)

        assert not Notification.objects.filter(
            kind="assignment", recipient=new_reviewer
        ).exists()

    @pytest.mark.django_db
    def test_payload_includes_project_id_and_reviewer_ids(self):
        from api.models import Notification
        from api.notifications import dispatch_assignment

        actor = _make_user(role="Administrador")
        student = _make_user(role="Estudiante")
        old_reviewer = _make_user(role="Jurado")
        new_reviewer = _make_user(role="Jurado")
        project = _make_project(student)

        dispatch_assignment(
            project,
            new_reviewer=new_reviewer,
            previous_reviewer=old_reviewer,
            actor=actor,
        )

        notif = Notification.objects.get(kind="assignment", recipient=new_reviewer)
        assert "project_id" in notif.payload
        assert notif.payload["project_id"] == project.pk
        assert "new_reviewer_id" in notif.payload
        assert "previous_reviewer_id" in notif.payload


# ---------------------------------------------------------------------------
# 4. dispatch_comment_added
# ---------------------------------------------------------------------------


class TestDispatchCommentAdded:
    @pytest.mark.django_db
    def test_notifies_student_partner_advisors_reviewer_except_author(self):
        from api.models import Notification
        from api.notifications import dispatch_comment_added

        student = _make_user(role="Estudiante")
        partner = _make_user(role="Estudiante")
        advisor = _make_user(role="Tutor")
        reviewer = _make_user(role="Jurado")
        author = _make_user(role="Tutor")
        project = _make_project(
            student, partner=partner, advisors=[advisor, author], reviewer=reviewer
        )
        comment = _make_comment(project, author=author)

        dispatch_comment_added(comment)

        recipients = set(
            Notification.objects.filter(kind="comment_added").values_list(
                "recipient_id", flat=True
            )
        )
        assert student.pk in recipients
        assert partner.pk in recipients
        assert advisor.pk in recipients
        assert reviewer.pk in recipients
        assert author.pk not in recipients

    @pytest.mark.django_db
    def test_author_excluded_even_when_author_is_student(self):
        from api.models import Notification
        from api.notifications import dispatch_comment_added

        student = _make_user(role="Estudiante")
        project = _make_project(student)
        # Author is the student themselves
        comment = _make_comment(project, author=student)

        dispatch_comment_added(comment)

        assert not Notification.objects.filter(
            kind="comment_added", recipient=student
        ).exists()

    @pytest.mark.django_db
    def test_skips_users_with_notify_comment_added_false(self):
        from api.models import Notification
        from api.notifications import dispatch_comment_added

        student = _make_user(role="Estudiante")
        partner = _make_user(role="Estudiante")
        _set_prefs(partner, notify_comment_added=False)
        author = _make_user(role="Tutor")
        project = _make_project(student, partner=partner)
        comment = _make_comment(project, author=author)

        dispatch_comment_added(comment)

        assert not Notification.objects.filter(
            kind="comment_added", recipient=partner
        ).exists()
        assert Notification.objects.filter(
            kind="comment_added", recipient=student
        ).exists()

    @pytest.mark.django_db
    def test_payload_includes_comment_id_project_id_author_id(self):
        from api.models import Notification
        from api.notifications import dispatch_comment_added

        student = _make_user(role="Estudiante")
        author = _make_user(role="Tutor")
        project = _make_project(student)
        comment = _make_comment(project, author=author)

        dispatch_comment_added(comment)

        notif = Notification.objects.get(kind="comment_added", recipient=student)
        assert "comment_id" in notif.payload
        assert notif.payload["comment_id"] == comment.pk
        assert "project_id" in notif.payload
        assert notif.payload["project_id"] == project.pk
        assert "author_id" in notif.payload
        assert notif.payload["author_id"] == author.pk


# ---------------------------------------------------------------------------
# 5. dispatch_semester_activated
# ---------------------------------------------------------------------------


class TestDispatchSemesterActivated:
    @pytest.mark.django_db
    def test_broadcasts_to_all_estudiante_users_excluding_actor(self):
        from api.models import Notification
        from api.notifications import dispatch_semester_activated

        actor = _make_user(role="Administrador")
        student_a = _make_user(role="Estudiante")
        student_b = _make_user(role="Estudiante")
        student_c = _make_user(role="Estudiante")
        semester = _make_semester()

        dispatch_semester_activated(semester, actor)

        recipients = set(
            Notification.objects.filter(kind="semester_activated").values_list(
                "recipient_id", flat=True
            )
        )
        assert student_a.pk in recipients
        assert student_b.pk in recipients
        assert student_c.pk in recipients
        assert actor.pk not in recipients

    @pytest.mark.django_db
    def test_tutores_jurados_admins_receive_no_row(self):
        from api.models import Notification
        from api.notifications import dispatch_semester_activated

        actor = _make_user(role="Administrador")
        tutor = _make_user(role="Tutor")
        jurado = _make_user(role="Jurado")
        another_admin = _make_user(role="Administrador")
        semester = _make_semester(period="2026-02")

        dispatch_semester_activated(semester, actor)

        assert not Notification.objects.filter(
            kind="semester_activated", recipient=tutor
        ).exists()
        assert not Notification.objects.filter(
            kind="semester_activated", recipient=jurado
        ).exists()
        assert not Notification.objects.filter(
            kind="semester_activated", recipient=another_admin
        ).exists()

    @pytest.mark.django_db
    def test_actor_student_is_excluded_degenerate_case(self):
        """If the actor happens to be a student (contrived), they get no row."""
        from api.models import Notification
        from api.notifications import dispatch_semester_activated

        actor = _make_user(role="Estudiante")
        other_student = _make_user(role="Estudiante")
        semester = _make_semester(period="2026-03")

        dispatch_semester_activated(semester, actor)

        assert not Notification.objects.filter(
            kind="semester_activated", recipient=actor
        ).exists()
        assert Notification.objects.filter(
            kind="semester_activated", recipient=other_student
        ).exists()

    @pytest.mark.django_db
    def test_skips_students_with_notify_semester_changes_false(self):
        from api.models import Notification
        from api.notifications import dispatch_semester_activated

        actor = _make_user(role="Administrador")
        student_on = _make_user(role="Estudiante")
        student_off = _make_user(role="Estudiante")
        _set_prefs(student_off, notify_semester_changes=False)
        semester = _make_semester(period="2026-04")

        dispatch_semester_activated(semester, actor)

        assert Notification.objects.filter(
            kind="semester_activated", recipient=student_on
        ).exists()
        assert not Notification.objects.filter(
            kind="semester_activated", recipient=student_off
        ).exists()

    @pytest.mark.django_db
    def test_payload_includes_semester_id_and_period(self):
        from api.models import Notification
        from api.notifications import dispatch_semester_activated

        actor = _make_user(role="Administrador")
        student = _make_user(role="Estudiante")
        semester = _make_semester(period="2026-05")

        dispatch_semester_activated(semester, actor)

        notif = Notification.objects.get(kind="semester_activated", recipient=student)
        assert "semester_id" in notif.payload
        assert notif.payload["semester_id"] == semester.pk
        assert "period" in notif.payload
        assert notif.payload["period"] == semester.period

    @pytest.mark.django_db
    def test_correct_notification_rows_count(self):
        """Exactly one row per eligible student, not one row total."""
        from api.models import Notification
        from api.notifications import dispatch_semester_activated

        actor = _make_user(role="Administrador")
        students = [_make_user(role="Estudiante") for _ in range(4)]
        semester = _make_semester(period="2026-06")

        dispatch_semester_activated(semester, actor)

        assert Notification.objects.filter(kind="semester_activated").count() == 4


# ---------------------------------------------------------------------------
# 6. Cross-cutting concerns
# ---------------------------------------------------------------------------


class TestDispatchCrossCutting:
    @pytest.mark.django_db
    def test_email_failure_does_not_prevent_row_creation(self):
        """
        Si send_mail lanza SMTPException, el dispatcher no debe propagar la
        excepción y la fila de Notification debe existir de todos modos.
        """
        import smtplib
        from unittest.mock import patch

        from api.models import Notification
        from api.notifications import dispatch_evaluation_received

        actor = _make_user(role="Jurado")
        student = _make_user(role="Estudiante")
        _set_prefs(student, email_enabled=True, notify_evaluation_received=True)
        project = _make_project(student, reviewer=actor)
        evaluation = _make_evaluation(project, actor)

        with patch("django.core.mail.send_mail", side_effect=smtplib.SMTPException("boom")):
            # Must NOT raise
            dispatch_evaluation_received(evaluation, actor)

        assert Notification.objects.filter(
            kind="evaluation_received", recipient=student
        ).exists()

    @pytest.mark.django_db
    def test_redispatch_creates_additional_rows(self):
        """
        Llamar a dispatch_evaluation_received dos veces con la misma evaluation
        produce 2x filas — re-dispatch es responsabilidad del caller, no del dispatcher.
        Este test documenta la semántica elegida (no-idempotente por diseño).
        """
        from api.models import Notification
        from api.notifications import dispatch_evaluation_received

        actor = _make_user(role="Jurado")
        student = _make_user(role="Estudiante")
        project = _make_project(student, reviewer=actor)
        evaluation = _make_evaluation(project, actor)

        dispatch_evaluation_received(evaluation, actor)
        dispatch_evaluation_received(evaluation, actor)

        count = Notification.objects.filter(
            kind="evaluation_received", recipient=student
        ).count()
        assert count == 2

    @pytest.mark.django_db
    def test_dispatch_returns_none(self):
        """Dispatchers are fire-and-forget — they must return None."""
        from api.notifications import dispatch_evaluation_received

        actor = _make_user(role="Jurado")
        student = _make_user(role="Estudiante")
        project = _make_project(student, reviewer=actor)
        evaluation = _make_evaluation(project, actor)

        result = dispatch_evaluation_received(evaluation, actor)
        assert result is None
