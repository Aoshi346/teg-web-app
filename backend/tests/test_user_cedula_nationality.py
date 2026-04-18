"""
Tests for the target schema where User.cedula is a PositiveIntegerField and
User.nationality is a 1-char CharField with choices V/E/P.

These tests are written RED-first: they describe the desired behavior and are
expected to FAIL until the backend-worker applies the schema change, data
migration, and serializer update.
"""

import pytest
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.db import IntegrityError, transaction

from api.serializers import UserSerializer

User = get_user_model()


# ---------------------------------------------------------------------------
# 1. Basic creation — nationality + cedula round-trip
# ---------------------------------------------------------------------------

@pytest.mark.django_db
def test_user_created_with_nationality_and_cedula_stores_exact_values():
    user = User.objects.create_user(
        email="cedula@test.local",
        password="test-pass-123",
        first_name="Ana",
        last_name="García",
        nationality="V",
        cedula=30243721,
    )
    fetched = User.objects.get(pk=user.pk)
    assert fetched.nationality == "V"
    assert fetched.cedula == 30243721


# ---------------------------------------------------------------------------
# 2. nationality choices — valid values accepted, invalid rejected
# ---------------------------------------------------------------------------

@pytest.mark.django_db
@pytest.mark.parametrize("code", ["V", "E", "P"])
def test_nationality_accepts_valid_codes(code):
    user = User.objects.create_user(
        email=f"nat_{code.lower()}@test.local",
        password="test-pass-123",
        first_name="X",
        last_name="Y",
        nationality=code,
        cedula=10000001,
    )
    user.full_clean()  # must not raise
    assert user.nationality == code


@pytest.mark.django_db
def test_nationality_rejects_invalid_code():
    user = User.objects.create_user(
        email="bad_nat@test.local",
        password="test-pass-123",
        first_name="X",
        last_name="Y",
        nationality="X",
        cedula=10000001,
    )
    with pytest.raises(ValidationError):
        user.full_clean()


# ---------------------------------------------------------------------------
# 3. cedula is numeric-only (PositiveIntegerField)
# ---------------------------------------------------------------------------

@pytest.mark.django_db
def test_cedula_rejects_negative_value_via_full_clean():
    # Build an unsaved user so full_clean() runs before any DB save.
    # Using create_user would trigger the DB CHECK constraint (IntegrityError)
    # before full_clean() gets a chance to raise ValidationError.
    user = User(
        email="neg_cedula@test.local",
        first_name="X",
        last_name="Y",
        nationality="V",
        cedula=-1,
    )
    user.set_password("test-pass-123")
    with pytest.raises(ValidationError):
        user.full_clean()


@pytest.mark.django_db
def test_cedula_accepts_positive_integer():
    user = User.objects.create_user(
        email="pos_cedula@test.local",
        password="test-pass-123",
        first_name="X",
        last_name="Y",
        nationality="V",
        cedula=30243721,
    )
    user.full_clean()
    assert isinstance(user.cedula, int)


# ---------------------------------------------------------------------------
# 4. UniqueConstraint(nationality, cedula) with partial index on cedula IS NOT NULL
# ---------------------------------------------------------------------------

@pytest.mark.django_db
def test_duplicate_nationality_cedula_pair_raises_integrity_error():
    User.objects.create_user(
        email="first@test.local",
        password="test-pass-123",
        first_name="X",
        last_name="Y",
        nationality="V",
        cedula=30243721,
    )
    with pytest.raises(IntegrityError):
        with transaction.atomic():
            User.objects.create_user(
                email="second@test.local",
                password="test-pass-123",
                first_name="A",
                last_name="B",
                nationality="V",
                cedula=30243721,
            )


@pytest.mark.django_db
def test_same_cedula_different_nationality_is_allowed():
    User.objects.create_user(
        email="venezolano@test.local",
        password="test-pass-123",
        first_name="X",
        last_name="Y",
        nationality="V",
        cedula=30243721,
    )
    # nationality='E' with the same cedula number must succeed
    other = User.objects.create_user(
        email="extranjero@test.local",
        password="test-pass-123",
        first_name="A",
        last_name="B",
        nationality="E",
        cedula=30243721,
    )
    assert other.pk is not None


@pytest.mark.django_db
def test_multiple_users_with_null_cedula_are_allowed():
    """La condición cedula__isnull=False excluye NULLs del unique index."""
    u1 = User.objects.create_user(
        email="no_cedula_1@test.local",
        password="test-pass-123",
        first_name="X",
        last_name="Y",
        nationality="V",
        cedula=None,
    )
    u2 = User.objects.create_user(
        email="no_cedula_2@test.local",
        password="test-pass-123",
        first_name="A",
        last_name="B",
        nationality="V",
        cedula=None,
    )
    assert u1.pk is not None
    assert u2.pk is not None


# ---------------------------------------------------------------------------
# 5. Blank / null cedula is valid
# ---------------------------------------------------------------------------

@pytest.mark.django_db
def test_user_without_cedula_is_valid():
    user = User.objects.create_user(
        email="no_cedula@test.local",
        password="test-pass-123",
        first_name="X",
        last_name="Y",
    )
    user.full_clean()  # must not raise
    assert user.cedula is None


# ---------------------------------------------------------------------------
# 6. UserSerializer exposes nationality, cedula, and cedula_display
# ---------------------------------------------------------------------------

@pytest.mark.django_db
def test_serializer_exposes_nationality_and_cedula():
    user = User.objects.create_user(
        email="serial@test.local",
        password="test-pass-123",
        first_name="X",
        last_name="Y",
        nationality="V",
        cedula=30243721,
    )
    data = UserSerializer(user).data
    assert "nationality" in data
    assert "cedula" in data
    assert data["nationality"] == "V"
    assert data["cedula"] == 30243721


@pytest.mark.django_db
def test_serializer_cedula_display_formats_correctly():
    user = User.objects.create_user(
        email="display@test.local",
        password="test-pass-123",
        first_name="X",
        last_name="Y",
        nationality="V",
        cedula=30243721,
    )
    data = UserSerializer(user).data
    assert "cedula_display" in data
    assert data["cedula_display"] == "V-30243721"


@pytest.mark.django_db
def test_serializer_cedula_display_is_empty_string_when_cedula_null():
    user = User.objects.create_user(
        email="nodisplay@test.local",
        password="test-pass-123",
        first_name="X",
        last_name="Y",
    )
    data = UserSerializer(user).data
    assert "cedula_display" in data
    assert data["cedula_display"] == ""
