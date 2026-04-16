"""
Tests for the Planificación module backend (PresentationDay + Presentation).

RED phase — the models/viewsets/urls do not exist yet. Every test here is
expected to fail until the backend-worker implements them.
"""

import pytest
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient

from api.models import Semester

User = get_user_model()

DAYS_URL = "/api/planificacion/days/"
DAYS_BULK_URL = "/api/planificacion/days/bulk/"
PRESENTATIONS_URL = "/api/planificacion/presentations/"


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def presentations_url_for_day(day_id):
    return f"/api/planificacion/days/{day_id}/presentations/"


def day_detail_url(day_id):
    return f"/api/planificacion/days/{day_id}/"


def presentation_detail_url(pres_id):
    return f"/api/planificacion/presentations/{pres_id}/"


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def semester(db):
    return Semester.objects.create(
        period="2026-01",
        is_active=True,
        start_month=1,
        end_month=6,
    )


@pytest.fixture
def admin_client(db, admin_user):
    client = APIClient()
    client.force_authenticate(user=admin_user)
    return client


@pytest.fixture
def student_client(db, student_user):
    client = APIClient()
    client.force_authenticate(user=student_user)
    return client


@pytest.fixture
def tutor_client(db, tutor_user):
    client = APIClient()
    client.force_authenticate(user=tutor_user)
    return client


@pytest.fixture
def jurado_client(db, jurado_user):
    client = APIClient()
    client.force_authenticate(user=jurado_user)
    return client


@pytest.fixture
def anon_client():
    return APIClient()


@pytest.fixture
def a_day(db, admin_client, semester):
    """Create one PresentationDay via the API and return the response JSON."""
    payload = {"date": "2026-05-12", "semester": semester.id, "notes": "Test day"}
    resp = admin_client.post(DAYS_URL, payload, format="json")
    assert resp.status_code == 201, f"Setup failed: {resp.data}"
    return resp.data


@pytest.fixture
def a_project(db, student_user, semester):
    from api.models import Project

    return Project.objects.create(
        title="Test TEG Project",
        student=student_user,
        project_type="tesis",
        status="pending",
        period=semester.period,
    )


# ---------------------------------------------------------------------------
# Test 1 — admin can create a presentation day
# ---------------------------------------------------------------------------


@pytest.mark.django_db
def test_admin_can_create_presentation_day(admin_client, semester):
    payload = {"date": "2026-05-12", "semester": semester.id, "notes": "Final week day 1"}
    response = admin_client.post(DAYS_URL, payload, format="json")

    assert response.status_code == 201
    assert response.data["date"] == "2026-05-12"
    assert "id" in response.data


# ---------------------------------------------------------------------------
# Test 2 — non-admin roles cannot create a day (403 for each)
# ---------------------------------------------------------------------------


@pytest.mark.django_db
def test_non_admin_cannot_create_day(student_client, tutor_client, jurado_client, semester):
    payload = {"date": "2026-05-13", "semester": semester.id}

    for role_client, label in [
        (student_client, "Estudiante"),
        (tutor_client, "Tutor"),
        (jurado_client, "Jurado"),
    ]:
        resp = role_client.post(DAYS_URL, payload, format="json")
        assert resp.status_code == 403, f"{label} expected 403, got {resp.status_code}"


# ---------------------------------------------------------------------------
# Test 3 — any authenticated user can list days
# ---------------------------------------------------------------------------


@pytest.mark.django_db
def test_any_authenticated_user_can_list_days(
    admin_client, student_client, tutor_client, jurado_client
):
    for role_client, label in [
        (admin_client, "Administrador"),
        (student_client, "Estudiante"),
        (tutor_client, "Tutor"),
        (jurado_client, "Jurado"),
    ]:
        resp = role_client.get(DAYS_URL)
        assert resp.status_code == 200, f"{label} expected 200, got {resp.status_code}"


# ---------------------------------------------------------------------------
# Test 4 — unauthenticated user cannot list days
# ---------------------------------------------------------------------------


@pytest.mark.django_db
def test_unauthenticated_user_cannot_list_days(anon_client):
    response = anon_client.get(DAYS_URL)
    assert response.status_code in (401, 403)


# ---------------------------------------------------------------------------
# Test 5 — bulk create from date list; idempotent on re-post
# ---------------------------------------------------------------------------


@pytest.mark.django_db
def test_bulk_create_days_from_date_list(admin_client, semester):
    payload = {
        "dates": ["2026-05-12", "2026-05-13", "2026-05-14"],
        "semester": semester.id,
    }
    response = admin_client.post(DAYS_BULK_URL, payload, format="json")

    assert response.status_code in (200, 201)
    # Must return the created/existing objects (3 total)
    assert len(response.data) == 3

    # Idempotent: posting the same dates again must NOT error and must NOT duplicate
    response2 = admin_client.post(DAYS_BULK_URL, payload, format="json")
    assert response2.status_code in (200, 201)
    assert len(response2.data) == 3

    # Confirm only 3 rows in the DB, not 6
    from api.models import PresentationDay

    assert PresentationDay.objects.filter(semester=semester).count() == 3


# ---------------------------------------------------------------------------
# Test 6 — same project cannot appear twice on the same day
# ---------------------------------------------------------------------------


@pytest.mark.django_db
def test_unique_project_per_day_constraint(admin_client, a_day, a_project, jurado_user):
    day_id = a_day["id"]
    url = presentations_url_for_day(day_id)

    pres_payload = {
        "project": a_project.id,
        "start_time": "09:00",
        "jurado": [jurado_user.id],
    }

    first = admin_client.post(url, pres_payload, format="json")
    assert first.status_code == 201

    # Same project, same day — must fail
    second = admin_client.post(url, pres_payload, format="json")
    assert second.status_code == 400


# ---------------------------------------------------------------------------
# Test 7 — deleting a day cascade-deletes its presentations
# ---------------------------------------------------------------------------


@pytest.mark.django_db
def test_cascade_delete_removes_presentations(db, admin_client, semester, student_user, jurado_user):
    from api.models import Project

    # Create two projects
    proj1 = Project.objects.create(
        title="Project Alpha", student=student_user, project_type="proyecto",
        status="pending", period=semester.period,
    )
    proj2_student = User.objects.create_user(
        email="student2@test.local", password="test-pass-123",
        first_name="Student", last_name="Two",
        role="Estudiante", status="active",
    )
    proj2 = Project.objects.create(
        title="Project Beta", student=proj2_student, project_type="tesis",
        status="pending", period=semester.period,
    )

    # Create a day
    day_resp = admin_client.post(DAYS_URL, {"date": "2026-05-20", "semester": semester.id}, format="json")
    assert day_resp.status_code == 201
    day_id = day_resp.data["id"]
    url = presentations_url_for_day(day_id)

    # Add two presentations
    for proj in (proj1, proj2):
        resp = admin_client.post(
            url,
            {"project": proj.id, "start_time": "10:00", "jurado": [jurado_user.id]},
            format="json",
        )
        assert resp.status_code == 201, f"Could not create presentation: {resp.data}"

    # Delete the day
    del_resp = admin_client.delete(day_detail_url(day_id))
    assert del_resp.status_code == 204

    # Both presentations must be gone
    from api.models import Presentation

    assert Presentation.objects.filter(day_id=day_id).count() == 0


# ---------------------------------------------------------------------------
# Test 8 — start_time is required; HH:MM round-trips; duration defaults to 30
# ---------------------------------------------------------------------------


@pytest.mark.django_db
def test_presentation_requires_start_time_and_round_trips_hh_mm(
    admin_client, a_day, a_project, jurado_user
):
    day_id = a_day["id"]
    url = presentations_url_for_day(day_id)

    # Missing start_time → 400
    resp_bad = admin_client.post(
        url,
        {"project": a_project.id, "jurado": [jurado_user.id]},
        format="json",
    )
    assert resp_bad.status_code == 400

    # Valid start_time → 201 with HH:MM string back and default duration
    resp_good = admin_client.post(
        url,
        {"project": a_project.id, "start_time": "14:30", "jurado": [jurado_user.id]},
        format="json",
    )
    assert resp_good.status_code == 201
    assert resp_good.data["start_time"] == "14:30"
    assert resp_good.data["duration_minutes"] == 30


# ---------------------------------------------------------------------------
# Test 9 — jurado M2M rejects non-Jurado users; accepts Jurado users
# ---------------------------------------------------------------------------


@pytest.mark.django_db
def test_jurado_m2m_rejects_non_jurado_users(
    admin_client, a_day, a_project, tutor_user, jurado_user
):
    day_id = a_day["id"]
    url = presentations_url_for_day(day_id)

    # Tutor user in jurado list → 400
    resp_bad = admin_client.post(
        url,
        {"project": a_project.id, "start_time": "10:00", "jurado": [tutor_user.id]},
        format="json",
    )
    assert resp_bad.status_code == 400

    # Jurado user in jurado list → 201
    resp_good = admin_client.post(
        url,
        {"project": a_project.id, "start_time": "10:00", "jurado": [jurado_user.id]},
        format="json",
    )
    assert resp_good.status_code == 201


# ---------------------------------------------------------------------------
# Test 10 — admin can update and delete presentations; student cannot
# ---------------------------------------------------------------------------


@pytest.mark.django_db
def test_admin_can_update_and_delete_presentation(
    admin_client, student_client, a_day, a_project, jurado_user
):
    day_id = a_day["id"]
    create_url = presentations_url_for_day(day_id)

    # Create the presentation
    create_resp = admin_client.post(
        create_url,
        {"project": a_project.id, "start_time": "09:00", "jurado": [jurado_user.id]},
        format="json",
    )
    assert create_resp.status_code == 201
    pres_id = create_resp.data["id"]
    detail_url = presentation_detail_url(pres_id)

    # Admin PATCH → 200
    patch_resp = admin_client.patch(detail_url, {"start_time": "10:00"}, format="json")
    assert patch_resp.status_code == 200
    assert patch_resp.data["start_time"] == "10:00"

    # Student PATCH → 403
    student_patch = student_client.patch(detail_url, {"start_time": "11:00"}, format="json")
    assert student_patch.status_code == 403

    # Student DELETE → 403
    student_del = student_client.delete(detail_url)
    assert student_del.status_code == 403

    # Admin DELETE → 204
    admin_del = admin_client.delete(detail_url)
    assert admin_del.status_code == 204
