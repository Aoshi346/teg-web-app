import os
import django

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "core.settings")
django.setup()

from django.contrib.auth import get_user_model


def upsert_user(email: str, password: str, *, role: str, full_name: str = "", status: str = "active",
                semester: int | None = None, phone: int | None = None,
                is_staff: bool = False, is_superuser: bool = False):
    User = get_user_model()
    user, created = User.objects.get_or_create(email=email, defaults={
        "full_name": full_name,
        "role": role,
        "status": status,
        "semester": semester,
        "phone": phone,
        "is_staff": is_staff,
        "is_superuser": is_superuser,
    })

    # Update fields if user existed
    user.full_name = full_name or user.full_name
    user.role = role
    user.status = status
    if semester is not None:
        user.semester = semester
    if phone is not None:
        user.phone = phone
    user.is_staff = is_staff
    user.is_superuser = is_superuser
    user.set_password(password)
    user.save()

    print(f"{'Created' if created else 'Updated'} user: {email} (role={role}, staff={is_staff}, superuser={is_superuser})")


def main():
    # Administrador user
    upsert_user(
        email="admin@example.com",
        password="123",
        role="Administrador",
        full_name="Administrador Test",
        status="active",
        is_staff=True,
        is_superuser=True,
    )

    # Tutor user
    upsert_user(
        email="tutor@example.com",
        password="123",
        role="Tutor",
        full_name="Tutor Test",
        status="active",
        is_staff=True,
        is_superuser=False,
        phone=580000000,
    )

    # Jurado user
    upsert_user(
        email="jurado@example.com",
        password="123",
        role="Jurado",
        full_name="Jurado Test",
        status="active",
        is_staff=True,
        is_superuser=False,
    )

    # Student user
    upsert_user(
        email="student@example.com",
        password="123",
        role="Estudiante",
        full_name="Student Test",
        status="active",
        semester=10,
        is_staff=False,
        is_superuser=False,
    )

    print("Test users are ready.")


if __name__ == "__main__":
    main()
