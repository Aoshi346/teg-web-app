"""
Tests for PerfHeadersMiddleware — verifies that X-Query-Count and
X-Response-Time-Ms headers are injected into /api/ responses when
DEBUG=True, and are absent on non-/api/ paths.
"""

import pytest
from django.test import override_settings
from rest_framework.test import APIClient


@pytest.mark.django_db
def test_api_response_includes_query_count_header(admin_user):
    """GET /api/csrf/ must include X-Query-Count with an integer value."""
    client = APIClient()
    response = client.get("/api/csrf/")

    assert "X-Query-Count" in response, (
        "Expected X-Query-Count header but it was absent — "
        "PerfHeadersMiddleware not installed or not active"
    )
    raw = response["X-Query-Count"]
    # Must be parseable as an integer (not a float, not empty)
    parsed = int(raw)
    assert parsed >= 0, f"X-Query-Count must be >= 0, got {parsed!r}"


@pytest.mark.django_db
def test_api_response_includes_response_time_header(admin_user):
    """GET /api/csrf/ must include X-Response-Time-Ms with a positive numeric value."""
    client = APIClient()
    response = client.get("/api/csrf/")

    assert "X-Response-Time-Ms" in response, (
        "Expected X-Response-Time-Ms header but it was absent — "
        "PerfHeadersMiddleware not installed or not active"
    )
    raw = response["X-Response-Time-Ms"]
    # May be int or float string; use float() to accept both
    parsed = float(raw)
    assert parsed >= 0, f"X-Response-Time-Ms must be >= 0, got {parsed!r}"


@pytest.mark.django_db
def test_query_count_increases_with_db_hits(admin_user):
    """
    An authenticated request to /api/evaluations/ must show X-Query-Count > 0,
    proving the middleware counts real DB queries and does not hard-code zero.
    """
    client = APIClient()
    client.force_authenticate(user=admin_user)
    response = client.get("/api/evaluations/")

    assert "X-Query-Count" in response, (
        "Expected X-Query-Count header on authenticated endpoint — "
        "PerfHeadersMiddleware not installed or not active"
    )
    count = int(response["X-Query-Count"])
    assert count > 0, (
        f"Expected at least 1 SQL query for /api/evaluations/, got {count}. "
        "Middleware may be counting incorrectly or not counting at all."
    )


def test_non_api_paths_do_not_get_headers():
    """
    Non-/api/ paths (e.g. Django admin root) must NOT receive the perf headers.
    This verifies that middleware scope is limited to /api/* requests.

    Note: this test passes trivially today (headers are absent everywhere),
    so it will remain green both before and after implementation. Its value
    is as a regression guard — once the middleware exists it must not leak
    headers outside /api/.
    """
    client = APIClient()
    # /admin/ login page does not require authentication for a GET
    response = client.get("/admin/login/", follow=True)

    assert "X-Query-Count" not in response, (
        "X-Query-Count header must not appear on non-/api/ paths"
    )
    assert "X-Response-Time-Ms" not in response, (
        "X-Response-Time-Ms header must not appear on non-/api/ paths"
    )
