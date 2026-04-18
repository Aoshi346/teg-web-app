"""
Tests for the PresentationJuror through-model (Phase B — RED).

PresentationJuror replaces the implicit auto-generated M2M join table between
Presentation.jurado and User with an explicit model carrying per-juror tracking
fields: individual_score, notified, notified_at, confirmed_attendance, attended.

All tests are expected to FAIL until the backend-worker adds the model and
updates Presentation.jurado to use through='PresentationJuror'.

Note on M2M mutators: once through= is set, Django raises AttributeError on
.jurado.add() / .jurado.set() / .jurado.remove() / .jurado.clear(). Tests here
only use direct PresentationJuror.objects.create() for writes; .jurado.all() is
used only for reads — which remain valid on through-M2M fields.
"""

import pytest
from django.contrib.auth import get_user_model
from django.db import IntegrityError, transaction
from django.utils import timezone

from api.models import Presentation, PresentationDay, Project, Semester
from api.serializers import PresentationSerializer

User = get_user_model()


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
def student(db):
    return User.objects.create_user(
        email="pj_student@test.local",
        password="test-pass-123",
        first_name="Student",
        last_name="PJ",
        role="Estudiante",
        status="active",
    )


@pytest.fixture
def juror_a(db):
    return User.objects.create_user(
        email="juror_a@test.local",
        password="test-pass-123",
        first_name="Juror",
        last_name="Alpha",
        role="Jurado",
        status="active",
    )


@pytest.fixture
def juror_b(db):
    return User.objects.create_user(
        email="juror_b@test.local",
        password="test-pass-123",
        first_name="Juror",
        last_name="Beta",
        role="Jurado",
        status="active",
    )


@pytest.fixture
def day(db, semester, admin_user):
    return PresentationDay.objects.create(
        date="2026-05-20",
        semester=semester,
        created_by=admin_user,
    )


@pytest.fixture
def project(db, student, semester):
    return Project.objects.create(
        title="PJ Test Project",
        student=student,
        project_type="tesis",
        status="pending",
        period=semester.period,
    )


@pytest.fixture
def presentation(db, day, project):
    return Presentation.objects.create(
        day=day,
        project=project,
        start_time="09:00",
    )


# ---------------------------------------------------------------------------
# 1. Import smoke test
# ---------------------------------------------------------------------------


def test_presentation_juror_model_is_importable():
    """PresentationJuror can be imported and is a Django model subclass."""
    from api.models import PresentationJuror
    from django.db import models

    assert issubclass(PresentationJuror, models.Model)


# ---------------------------------------------------------------------------
# 2. Through-model wiring
# ---------------------------------------------------------------------------


@pytest.mark.django_db
def test_presentation_jurado_field_uses_through_model(presentation):
    """Presentation.jurado.through must resolve to PresentationJuror, not the
    implicit auto-created join model.  If the field still has no through=
    argument Django will create an auto model whose name is something like
    'Presentation_jurado' — not 'PresentationJuror'."""
    from api.models import PresentationJuror

    assert Presentation.jurado.through is PresentationJuror


# ---------------------------------------------------------------------------
# 3. Create a PresentationJuror row and verify defaults
# ---------------------------------------------------------------------------


@pytest.mark.django_db
def test_create_presentation_juror_row_with_defaults(presentation, juror_a):
    """A PresentationJuror created with only FK fields gets sensible defaults."""
    from api.models import PresentationJuror

    pj = PresentationJuror.objects.create(
        presentation=presentation,
        juror=juror_a,
    )
    pj.refresh_from_db()

    assert pj.individual_score is None
    assert pj.notified is False
    assert pj.notified_at is None
    assert pj.confirmed_attendance is False
    assert pj.attended is False
    assert pj.created_at is not None
    assert pj.updated_at is not None


# ---------------------------------------------------------------------------
# 4. Round-trip all tracking fields
# ---------------------------------------------------------------------------


@pytest.mark.django_db
def test_presentation_juror_tracking_fields_round_trip(presentation, juror_a):
    """All tracking fields survive a save-and-reload cycle."""
    from api.models import PresentationJuror

    now = timezone.now()
    pj = PresentationJuror.objects.create(
        presentation=presentation,
        juror=juror_a,
        individual_score=18.5,
        notified=True,
        notified_at=now,
        confirmed_attendance=True,
        attended=True,
    )
    pj.refresh_from_db()

    assert pj.individual_score == 18.5
    assert pj.notified is True
    assert pj.notified_at is not None
    assert pj.confirmed_attendance is True
    assert pj.attended is True


# ---------------------------------------------------------------------------
# 5. M2M read API still works
# ---------------------------------------------------------------------------


@pytest.mark.django_db
def test_presentation_jurado_m2m_read_returns_assigned_users(
    presentation, juror_a, juror_b
):
    """
    Dado que through= está activo, sólo se puede escribir vía
    PresentationJuror.objects.create(). El API de lectura M2M
    (presentation.jurado.all()) debe seguir devolviendo los usuarios correctos.
    """
    from api.models import PresentationJuror

    PresentationJuror.objects.create(presentation=presentation, juror=juror_a)
    PresentationJuror.objects.create(presentation=presentation, juror=juror_b)

    assert set(presentation.jurado.all()) == {juror_a, juror_b}


# ---------------------------------------------------------------------------
# 6. Uniqueness constraint
# ---------------------------------------------------------------------------


@pytest.mark.django_db
def test_unique_together_presentation_juror_raises_integrity_error(
    presentation, juror_a
):
    """unique_together=('presentation','juror') prevents duplicate assignments."""
    from api.models import PresentationJuror

    PresentationJuror.objects.create(presentation=presentation, juror=juror_a)

    with pytest.raises(IntegrityError):
        with transaction.atomic():
            PresentationJuror.objects.create(
                presentation=presentation, juror=juror_a
            )


# ---------------------------------------------------------------------------
# 7a. Cascade delete — deleting Presentation removes its PresentationJuror rows
# ---------------------------------------------------------------------------


@pytest.mark.django_db
def test_deleting_presentation_cascades_to_juror_rows(
    presentation, juror_a, juror_b
):
    from api.models import PresentationJuror

    PresentationJuror.objects.create(presentation=presentation, juror=juror_a)
    PresentationJuror.objects.create(presentation=presentation, juror=juror_b)

    pres_id = presentation.id
    presentation.delete()

    assert PresentationJuror.objects.filter(presentation_id=pres_id).count() == 0


# ---------------------------------------------------------------------------
# 7b. Cascade delete — deleting a juror User removes their PresentationJuror rows
# ---------------------------------------------------------------------------


@pytest.mark.django_db
def test_deleting_juror_user_cascades_to_juror_rows(
    presentation, juror_a, juror_b
):
    from api.models import PresentationJuror

    PresentationJuror.objects.create(presentation=presentation, juror=juror_a)
    PresentationJuror.objects.create(presentation=presentation, juror=juror_b)

    juror_a_id = juror_a.id
    juror_a.delete()

    assert PresentationJuror.objects.filter(juror_id=juror_a_id).count() == 0
    # juror_b's row must be untouched
    assert PresentationJuror.objects.filter(
        presentation=presentation, juror=juror_b
    ).count() == 1


# ---------------------------------------------------------------------------
# 8. related_name access
# ---------------------------------------------------------------------------


@pytest.mark.django_db
def test_related_name_juror_entries_on_user(presentation, juror_a):
    """user.juror_entries.all() returns the PresentationJuror row."""
    from api.models import PresentationJuror

    pj = PresentationJuror.objects.create(presentation=presentation, juror=juror_a)

    entries = list(juror_a.juror_entries.all())
    assert pj in entries


@pytest.mark.django_db
def test_related_name_juror_entries_on_presentation(presentation, juror_a, juror_b):
    """presentation.juror_entries.all() returns all PresentationJuror rows."""
    from api.models import PresentationJuror

    pj_a = PresentationJuror.objects.create(presentation=presentation, juror=juror_a)
    pj_b = PresentationJuror.objects.create(presentation=presentation, juror=juror_b)

    entries = set(presentation.juror_entries.all())
    assert {pj_a, pj_b} == entries


# ---------------------------------------------------------------------------
# 9. Serializer shape
# ---------------------------------------------------------------------------


@pytest.mark.django_db
def test_presentation_serializer_exposes_juror_entries_key(
    presentation, juror_a
):
    """PresentationSerializer.data must include a 'juror_entries' key with the
    expected per-juror fields for each populated row."""
    from api.models import PresentationJuror

    PresentationJuror.objects.create(
        presentation=presentation,
        juror=juror_a,
        individual_score=17.0,
        notified=True,
    )

    data = PresentationSerializer(presentation).data

    assert "juror_entries" in data, "'juror_entries' key missing from serializer output"
    assert isinstance(data["juror_entries"], list)
    assert len(data["juror_entries"]) == 1

    entry = data["juror_entries"][0]
    expected_keys = {
        "juror", "juror_name", "individual_score",
        "notified", "notified_at", "confirmed_attendance", "attended",
    }
    missing = expected_keys - set(entry.keys())
    assert not missing, f"Missing keys in juror_entries entry: {missing}"

    # Type spot-checks for one populated row
    assert isinstance(entry["juror"], int)
    assert isinstance(entry["juror_name"], str)
    assert entry["individual_score"] == 17.0
    assert entry["notified"] is True


@pytest.mark.django_db
def test_presentation_serializer_backwards_compat_jurado_names(
    presentation, juror_a, juror_b
):
    """jurado_names read-only list must still be present (backwards compat)."""
    from api.models import PresentationJuror

    PresentationJuror.objects.create(presentation=presentation, juror=juror_a)
    PresentationJuror.objects.create(presentation=presentation, juror=juror_b)

    data = PresentationSerializer(presentation).data

    assert "jurado_names" in data, "'jurado_names' key missing — backwards compat broken"
    assert isinstance(data["jurado_names"], list)
    assert len(data["jurado_names"]) == 2
