import pytest
from django.contrib.auth import get_user_model

User = get_user_model()


@pytest.mark.django_db
def test_create_user_creates_persisted_user():
    user = User.objects.create_user(
        email="u@test.local",
        password="pw",
        first_name="A",
        last_name="B",
        role="Estudiante",
    )
    assert user.pk is not None
    assert User.objects.filter(email="u@test.local").exists()


@pytest.mark.django_db
def test_create_user_sets_password_hashed():
    user = User.objects.create_user(
        email="hash@test.local",
        password="mysecret",
        first_name="A",
        last_name="B",
    )
    assert user.check_password("mysecret") is True
    assert user.password != "mysecret"


@pytest.mark.django_db
def test_create_user_requires_email():
    with pytest.raises(ValueError):
        User.objects.create_user(email="", password="pw")


@pytest.mark.django_db
def test_create_user_normalizes_email_domain():
    user = User.objects.create_user(
        email="User@EXAMPLE.COM",
        password="pw",
        first_name="A",
        last_name="B",
    )
    # normalize_email lowercases the domain only, not the local part
    assert user.email == "User@example.com"


@pytest.mark.django_db
def test_create_user_defaults_is_staff_false():
    user = User.objects.create_user(
        email="staff@test.local",
        password="pw",
        first_name="A",
        last_name="B",
    )
    assert user.is_staff is False


@pytest.mark.django_db
def test_create_user_defaults_is_superuser_false():
    user = User.objects.create_user(
        email="super@test.local",
        password="pw",
        first_name="A",
        last_name="B",
    )
    assert user.is_superuser is False


@pytest.mark.django_db
def test_create_user_accepts_custom_fields():
    user = User.objects.create_user(
        email="custom@test.local",
        password="pw",
        first_name="Juan",
        last_name="Pérez",
        role="Tutor",
        status="active",
        cedula="V-12345678",
        semester="9no",
        phone="+58-414-1234567",
    )
    assert user.role == "Tutor"
    assert user.status == "active"
    assert user.cedula == "V-12345678"
    assert user.semester == "9no"
    assert user.phone == "+58-414-1234567"


@pytest.mark.django_db
def test_create_superuser_sets_is_staff_and_is_superuser_true():
    user = User.objects.create_superuser(
        email="admin@test.local",
        password="adminpass",
        first_name="Admin",
        last_name="User",
    )
    assert user.is_staff is True
    assert user.is_superuser is True


@pytest.mark.django_db
def test_create_superuser_raises_if_is_staff_false():
    with pytest.raises(ValueError):
        User.objects.create_superuser(
            email="badstaff@test.local",
            password="pw",
            is_staff=False,
        )


@pytest.mark.django_db
def test_create_superuser_raises_if_is_superuser_false():
    with pytest.raises(ValueError):
        User.objects.create_superuser(
            email="badsuper@test.local",
            password="pw",
            is_superuser=False,
        )
