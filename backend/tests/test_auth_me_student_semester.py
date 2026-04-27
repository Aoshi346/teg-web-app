"""
Characterization tests for PATCH /api/auth/me/ — Estudiante semester field protection.

The backend already excludes `semester` from an Estudiante's allowed_fields on PATCH.
These tests pin that behaviour so a future refactor cannot reintroduce the leak.
"""

import pytest
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient

User = get_user_model()

ME_URL = "/api/auth/me/"


@pytest.fixture
def student_with_semester(db):
    """Crea un Estudiante con semester='9' para tests de protección de campo."""
    return User.objects.create_user(
        email="student-semester@test.local",
        password="test-pass-123",
        first_name="Semester",
        last_name="Student",
        role="Estudiante",
        status="active",
        semester="9",
        nationality="V",
        cedula=99999001,
    )


@pytest.mark.django_db
def test_student_cannot_change_semester_via_me(student_with_semester):
    client = APIClient()
    client.force_authenticate(student_with_semester)

    resp = client.patch(ME_URL, {"semester": "10"}, format="json")

    assert resp.status_code == 200
    student_with_semester.refresh_from_db()
    assert student_with_semester.semester == "9"


@pytest.mark.django_db
def test_student_can_update_phone_via_me(student_with_semester):
    client = APIClient()
    client.force_authenticate(student_with_semester)

    resp = client.patch(ME_URL, {"phone": "+58-414-9999999"}, format="json")

    assert resp.status_code == 200
    student_with_semester.refresh_from_db()
    assert student_with_semester.phone == "+58-414-9999999"
