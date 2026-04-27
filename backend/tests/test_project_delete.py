"""
Integration tests for DELETE /api/projects/{id}/ — admin-only hard delete.

Phase RED: all tests expected to fail until ProjectViewSet.destroy is
gated to Administrador and perform_destroy handles file cleanup.
"""

import os
import datetime

import pytest
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import override_settings

from api.models import (
    AttachedFile,
    Comment,
    Evaluation,
    Presentation,
    PresentationDay,
    PresentationJuror,
    Project,
    Semester,
    StateOverride,
)


def _url(project_id):
    return f"/api/projects/{project_id}/"


# ---------------------------------------------------------------------------
# Case 1: Admin deletes a PTEG project — 204, DB rows cascaded
# ---------------------------------------------------------------------------

@pytest.mark.django_db
def test_admin_deletes_pteg_project_returns_204(authed_client, admin_user, student_user, project_factory):
    project = project_factory(student=student_user, project_type="proyecto")
    evaluation = Evaluation.objects.create(
        project=project, reviewer=admin_user, kind="review",
        pass_status="Pass", score=80,
    )
    comment = Comment.objects.create(
        project=project, author=student_user, content="Some comment"
    )
    StateOverride.objects.create(
        project=project, admin=admin_user,
        from_state="pending_review_1", to_state="pending_defense",
        reason="test override reason here",
    )

    resp = authed_client.delete(_url(project.id))

    assert resp.status_code == 204
    assert not Project.objects.filter(pk=project.pk).exists()
    assert not Evaluation.objects.filter(pk=evaluation.pk).exists()
    assert not Comment.objects.filter(pk=comment.pk).exists()
    assert not StateOverride.objects.filter(project_id=project.pk).exists()


# ---------------------------------------------------------------------------
# Case 2: Admin deletes TEG project with a real attached PDF — file removed
# ---------------------------------------------------------------------------

@pytest.mark.django_db
def test_admin_deletes_teg_project_removes_file_from_disk(
    authed_client, student_user, project_factory, tmp_path, settings
):
    settings.MEDIA_ROOT = str(tmp_path)

    project = project_factory(student=student_user, project_type="tesis")
    fake_pdf = SimpleUploadedFile(
        "Anteproyecto.pdf", b"%PDF-1.4 fake content", content_type="application/pdf"
    )
    attached = AttachedFile.objects.create(
        project=project,
        name="Anteproyecto",
        file=fake_pdf,
        file_type="pdf",
    )

    file_path = attached.file.path
    assert os.path.exists(file_path), "File should exist on disk before delete"

    resp = authed_client.delete(_url(project.id))

    assert resp.status_code == 204
    assert not Project.objects.filter(pk=project.pk).exists()
    assert not AttachedFile.objects.filter(pk=attached.pk).exists()
    assert not os.path.exists(file_path), "File should be removed from disk after delete"


# ---------------------------------------------------------------------------
# Case 3: Estudiante (project owner) → 403; project still exists
# ---------------------------------------------------------------------------

@pytest.mark.django_db
def test_student_owner_cannot_delete_own_project(student_client, student_user, project_factory):
    project = project_factory(student=student_user)

    resp = student_client.delete(_url(project.id))

    assert resp.status_code == 403
    assert Project.objects.filter(pk=project.pk).exists()


# ---------------------------------------------------------------------------
# Case 4: Estudiante (not owner) → 403 or 404; project still exists
# ---------------------------------------------------------------------------

@pytest.mark.django_db
def test_student_non_owner_cannot_delete_other_project(db, student_user, project_factory):
    from django.contrib.auth import get_user_model
    from rest_framework.test import APIClient

    User = get_user_model()
    other_student = User.objects.create_user(
        email="other_student@test.local",
        password="test-pass-123",
        first_name="Other",
        last_name="Student",
        role="Estudiante",
        status="active",
    )
    project = project_factory(student=other_student)

    client = APIClient()
    client.force_authenticate(user=student_user)
    resp = client.delete(_url(project.id))

    assert resp.status_code != 204
    assert Project.objects.filter(pk=project.pk).exists()


# ---------------------------------------------------------------------------
# Case 5: Tutor (advisor on the project) → 403; project still exists
# ---------------------------------------------------------------------------

@pytest.mark.django_db
def test_tutor_advisor_cannot_delete_project(tutor_client, tutor_user, student_user, project_factory):
    project = project_factory(student=student_user, advisors=[tutor_user])

    resp = tutor_client.delete(_url(project.id))

    assert resp.status_code == 403
    assert Project.objects.filter(pk=project.pk).exists()


# ---------------------------------------------------------------------------
# Case 6: Jurado (assigned reviewer) → 403; project still exists
# ---------------------------------------------------------------------------

@pytest.mark.django_db
def test_jurado_reviewer_cannot_delete_project(jurado_client, jurado_user, student_user, project_factory):
    project = project_factory(student=student_user, reviewer=jurado_user)

    resp = jurado_client.delete(_url(project.id))

    assert resp.status_code == 403
    assert Project.objects.filter(pk=project.pk).exists()


# ---------------------------------------------------------------------------
# Case 7: Anonymous client → 401 or 403; project still exists
# ---------------------------------------------------------------------------

@pytest.mark.django_db
def test_anonymous_cannot_delete_project(api_client, student_user, project_factory):
    project = project_factory(student=student_user)

    resp = api_client.delete(_url(project.id))

    assert resp.status_code in (401, 403)
    assert Project.objects.filter(pk=project.pk).exists()


# ---------------------------------------------------------------------------
# Case 8: Cascading Presentation rows (Presentation + PresentationJuror gone)
# ---------------------------------------------------------------------------

@pytest.mark.django_db
def test_admin_delete_cascades_presentation_and_juror_rows(
    authed_client, admin_user, student_user, jurado_user, project_factory
):
    semester = Semester.objects.create(
        period="2026-01", is_active=True, start_month=1, end_month=6
    )
    project = project_factory(student=student_user, project_type="proyecto")
    day = PresentationDay.objects.create(
        date=datetime.date(2026, 6, 15),
        semester=semester,
        created_by=admin_user,
    )
    presentation = Presentation.objects.create(
        day=day,
        project=project,
        start_time=datetime.time(9, 0),
        duration_minutes=30,
        order=1,
    )
    pj = PresentationJuror.objects.create(
        presentation=presentation,
        juror=jurado_user,
    )

    resp = authed_client.delete(_url(project.id))

    assert resp.status_code == 204
    assert not Project.objects.filter(pk=project.pk).exists()
    assert not Presentation.objects.filter(pk=presentation.pk).exists()
    assert not PresentationJuror.objects.filter(pk=pj.pk).exists()
    # PresentationDay should still exist (it is not scoped to the project)
    assert PresentationDay.objects.filter(pk=day.pk).exists()


# ---------------------------------------------------------------------------
# Case 9: StateOverride rows on the project are gone after delete
# ---------------------------------------------------------------------------

@pytest.mark.django_db
def test_admin_delete_cascades_state_overrides(authed_client, admin_user, student_user, project_factory):
    project = project_factory(student=student_user, project_type="proyecto")
    override = StateOverride.objects.create(
        project=project,
        admin=admin_user,
        from_state="pending_review_1",
        to_state="pending_defense",
        reason="legitimate override reason",
    )

    resp = authed_client.delete(_url(project.id))

    assert resp.status_code == 204
    assert not Project.objects.filter(pk=project.pk).exists()
    assert not StateOverride.objects.filter(pk=override.pk).exists()
