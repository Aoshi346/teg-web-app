"""Seed the four canonical dev users (admin / tutor / jurado / student).

All passwords are `123` (dev only — uses set_password to bypass validators).
Idempotent: re-running updates the matching email's fields in place.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Iterable

from . import _bootstrap

_bootstrap.setup()

from django.contrib.auth import get_user_model  # noqa: E402


@dataclass
class UserSeed:
    email: str
    password: str
    first_name: str
    last_name: str
    role: str
    cedula: int
    nationality: str = "V"
    status: str = "active"
    semester: str = ""
    phone: str = ""
    is_staff: bool = False
    is_superuser: bool = False
    extra: dict = field(default_factory=dict)


DEFAULT_USERS: tuple[UserSeed, ...] = (
    UserSeed(
        email="admin@example.com",
        password="123",
        first_name="Administrador",
        last_name="Test",
        role="Administrador",
        cedula=10000001,
        is_staff=True,
        is_superuser=True,
    ),
    UserSeed(
        email="tutor@example.com",
        password="123",
        first_name="Tutor",
        last_name="Test",
        role="Tutor",
        cedula=10000002,
        phone="+58-414-0000000",
        is_staff=True,
    ),
    UserSeed(
        email="jurado@example.com",
        password="123",
        first_name="Jurado",
        last_name="Test",
        role="Jurado",
        cedula=10000003,
        is_staff=True,
    ),
    UserSeed(
        email="student@example.com",
        password="123",
        first_name="Estudiante",
        last_name="Test",
        role="Estudiante",
        cedula=20000001,
        semester="10",
    ),
)


def upsert_user(seed: UserSeed) -> None:
    User = get_user_model()
    user, created = User.objects.get_or_create(email=seed.email)
    user.first_name = seed.first_name
    user.last_name = seed.last_name
    user.nationality = seed.nationality
    user.cedula = seed.cedula
    user.role = seed.role
    user.status = seed.status
    user.semester = seed.semester
    user.phone = seed.phone
    user.is_staff = seed.is_staff
    user.is_superuser = seed.is_superuser
    for k, v in seed.extra.items():
        setattr(user, k, v)
    user.set_password(seed.password)
    user.save()
    print(f"  {'+' if created else '~'} {seed.email}  role={seed.role}  pwd={seed.password}")


def seed_users(users: Iterable[UserSeed] = DEFAULT_USERS) -> None:
    print("Seeding users:")
    for u in users:
        upsert_user(u)


if __name__ == "__main__":
    seed_users()
