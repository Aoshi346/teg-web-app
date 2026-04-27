"""Seed an active semester for the current period.

Idempotent: matches on `period`. Activating one semester deactivates the rest.
"""
from __future__ import annotations

from datetime import date

from . import _bootstrap

_bootstrap.setup()

from api.models import Semester  # noqa: E402


def current_period(today: date | None = None) -> str:
    today = today or date.today()
    half = "01" if today.month <= 6 else "02"
    return f"{today.year}-{half}"


def upsert_semester(period: str, *, start_month: int, end_month: int, active: bool = False) -> Semester:
    sem, created = Semester.objects.get_or_create(period=period)
    sem.start_month = start_month
    sem.end_month = end_month
    sem.is_active = active
    sem.save()
    if active:
        Semester.objects.exclude(pk=sem.pk).update(is_active=False)
    print(f"  {'+' if created else '~'} {period}  months={start_month}-{end_month}  active={active}")
    return sem


def seed_semesters() -> None:
    period = current_period()
    today = date.today()
    start = today.month
    end = (start + 5) % 12 or 12
    print("Seeding semesters:")
    upsert_semester(period, start_month=start, end_month=end, active=True)


if __name__ == "__main__":
    seed_semesters()
