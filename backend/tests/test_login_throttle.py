"""El login limita los intentos por cuenta (fuerza bruta) sin bloquear a las demás cuentas."""

import pytest
from rest_framework.test import APIClient

from api.throttles import LoginAccountThrottle, LoginIPThrottle

LOGIN_URL = "/api/auth/login/"


@pytest.fixture
def tight_login_rates(monkeypatch):
    rates = {"login_account": "3/hour", "login_ip": "1000/hour"}
    monkeypatch.setattr(LoginAccountThrottle, "THROTTLE_RATES", rates)
    monkeypatch.setattr(LoginIPThrottle, "THROTTLE_RATES", rates)


def _attempt(email, password="mala-clave"):
    return APIClient().post(LOGIN_URL, {"email": email, "password": password}, format="json")


@pytest.mark.django_db
def test_login_is_throttled_per_account(tight_login_rates, student_user):
    for _ in range(3):
        assert _attempt(student_user.email).status_code == 400
    response = _attempt(student_user.email, password="test-pass-123")
    assert response.status_code == 429


@pytest.mark.django_db
def test_account_throttle_is_case_insensitive(tight_login_rates, student_user):
    for _ in range(3):
        _attempt(student_user.email.upper())
    assert _attempt(student_user.email).status_code == 429


@pytest.mark.django_db
def test_throttle_on_one_account_does_not_block_others(tight_login_rates, student_user, tutor_user):
    for _ in range(4):
        _attempt(student_user.email)
    response = _attempt(tutor_user.email, password="test-pass-123")
    assert response.status_code == 200, response.content
