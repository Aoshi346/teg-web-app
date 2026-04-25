import pytest
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient

User = get_user_model()

PREFERENCES_URL = "/api/auth/preferences/"

BOOL_FIELDS = [
    "notify_evaluation_received",
    "notify_state_change",
    "notify_assignment",
    "notify_comment_added",
    "notify_semester_changes",
    "email_enabled",
]


@pytest.fixture
def user_a(db):
    return User.objects.create_user(
        email="user_a@test.local",
        password="TestPass123!",
        first_name="User",
        last_name="A",
        role="Estudiante",
        status="active",
    )


@pytest.fixture
def user_b(db):
    return User.objects.create_user(
        email="user_b@test.local",
        password="TestPass123!",
        first_name="User",
        last_name="B",
        role="Estudiante",
        status="active",
    )


@pytest.fixture
def client_a(user_a):
    client = APIClient()
    client.force_authenticate(user=user_a)
    return client


@pytest.fixture
def client_b(user_b):
    client = APIClient()
    client.force_authenticate(user=user_b)
    return client


@pytest.mark.django_db
def test_get_preferences_lazy_creates_with_defaults(user_a, client_a):
    """
    A fresh user with no UserPreference row GETs the endpoint and receives
    200 with all 6 boolean fields set to True. The row must be created
    lazily so it exists in the DB after the response.
    """
    from api.models import UserPreference

    assert not UserPreference.objects.filter(user=user_a).exists()

    response = client_a.get(PREFERENCES_URL)

    assert response.status_code == 200
    for field in BOOL_FIELDS:
        assert field in response.data, f"Missing field: {field}"
        assert response.data[field] is True, f"Expected {field}=True, got {response.data[field]}"

    assert UserPreference.objects.filter(user=user_a).exists()


@pytest.mark.django_db
def test_patch_preferences_partial_update(user_a, client_a):
    """
    PATCH with two fields set to False updates only those fields.
    A subsequent GET confirms the two changed fields are False and all
    remaining fields are still True.
    """
    patch_response = client_a.patch(
        PREFERENCES_URL,
        {"notify_evaluation_received": False, "email_enabled": False},
        format="json",
    )
    assert patch_response.status_code == 200

    get_response = client_a.get(PREFERENCES_URL)
    assert get_response.status_code == 200

    data = get_response.data
    assert data["notify_evaluation_received"] is False
    assert data["email_enabled"] is False

    remaining = [f for f in BOOL_FIELDS if f not in ("notify_evaluation_received", "email_enabled")]
    for field in remaining:
        assert data[field] is True, f"Expected {field}=True after partial update, got {data[field]}"


@pytest.mark.django_db
def test_patch_unknown_field_is_ignored_or_400(user_a, client_a):
    """
    PATCH with an unknown field must not crash the server and must not
    silently corrupt any known field.

    Decision: DRF ModelSerializer with partial=True ignores unknown fields
    by default (they are not in `fields`). We therefore assert 200 and that
    all known boolean fields remain True. If the implementation chooses to
    return 400, that is also acceptable — we allow both.
    """
    response = client_a.patch(
        PREFERENCES_URL,
        {"this_field_does_not_exist": True},
        format="json",
    )
    assert response.status_code in (200, 400), (
        f"Expected 200 or 400 for unknown field, got {response.status_code}"
    )

    if response.status_code == 200:
        get_response = client_a.get(PREFERENCES_URL)
        assert get_response.status_code == 200
        for field in BOOL_FIELDS:
            assert get_response.data[field] is True, (
                f"Known field {field} was corrupted after unknown-field PATCH"
            )


@pytest.mark.django_db
def test_anonymous_get_is_rejected():
    """An unauthenticated request to GET preferences must return 401 or 403."""
    client = APIClient()
    response = client.get(PREFERENCES_URL)
    assert response.status_code in (401, 403)


@pytest.mark.django_db
def test_users_do_not_see_each_other_preferences(user_a, user_b, client_a, client_b):
    """
    User A patches their own preferences to False. User B GETs and must
    see their own default values (True), confirming complete row isolation.
    """
    patch_response = client_a.patch(
        PREFERENCES_URL,
        {field: False for field in BOOL_FIELDS},
        format="json",
    )
    assert patch_response.status_code == 200

    get_response = client_b.get(PREFERENCES_URL)
    assert get_response.status_code == 200

    for field in BOOL_FIELDS:
        assert get_response.data[field] is True, (
            f"User B's {field} was affected by User A's PATCH"
        )
