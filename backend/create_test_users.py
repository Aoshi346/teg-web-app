import os
import django

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "core.settings")
django.setup()

from django.contrib.auth import get_user_model


def upsert_user(email: str, password: str, *, first_name: str, last_name: str,
                role: str, status: str = "active", cedula: str = "",
                semester: str = "", phone: str = "",
                is_staff: bool = False, is_superuser: bool = False):
    User = get_user_model()
    user, created = User.objects.get_or_create(email=email, defaults={
        "first_name": first_name,
        "last_name": last_name,
        "cedula": cedula,
        "role": role,
        "status": status,
        "semester": semester,
        "phone": phone,
        "is_staff": is_staff,
        "is_superuser": is_superuser,
    })

    # Update fields if user existed
    user.first_name = first_name
    user.last_name = last_name
    user.cedula = cedula
    user.role = role
    user.status = status
    user.semester = semester
    user.phone = phone
    user.is_staff = is_staff
    user.is_superuser = is_superuser
    user.set_password(password)
    user.save()

    print(f"{'Created' if created else 'Updated'} user: {email} (role={role}, name={user.full_name})")


def main():
    upsert_user(
        email="admin@example.com",
        password="123",
        first_name="Administrador",
        last_name="Test",
        role="Administrador",
        cedula="V-10000001",
        is_staff=True,
        is_superuser=True,
    )

    upsert_user(
        email="tutor@example.com",
        password="123",
        first_name="Tutor",
        last_name="Test",
        role="Tutor",
        cedula="V-10000002",
        phone="+58-414-0000000",
        is_staff=True,
    )

    upsert_user(
        email="jurado@example.com",
        password="123",
        first_name="Jurado",
        last_name="Test",
        role="Jurado",
        cedula="V-10000003",
        is_staff=True,
    )

    upsert_user(
        email="student@example.com",
        password="123",
        first_name="Estudiante",
        last_name="Test",
        role="Estudiante",
        cedula="V-20000001",
        semester="10",
    )

    print("Test users are ready.")


if __name__ == "__main__":
    main()
