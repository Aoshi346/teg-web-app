"""Los listados no hacen una consulta extra por fila (N+1)."""

import pytest
from django.db import connection
from django.test.utils import CaptureQueriesContext
from django.utils import timezone

from api.models import Evaluation, Project, Semester


def _count_queries(client, url):
    with CaptureQueriesContext(connection) as ctx:
        response = client.get(url)
    assert response.status_code == 200, response.content
    return len(ctx.captured_queries)


def _make_projects(student, n, reviewer):
    for i in range(n):
        project = Project.objects.create(
            title=f"P{i}", student=student, period="2026-01", project_type="proyecto"
        )
        Evaluation.objects.create(
            project=project,
            reviewer=reviewer,
            kind="review",
            pass_status="Fail",
            score=10,
            graded_at=timezone.now(),
        )


@pytest.mark.django_db
def test_project_list_queries_do_not_grow_with_projects(authed_client, student_user, jurado_user):
    _make_projects(student_user, 1, jurado_user)
    baseline = _count_queries(authed_client, "/api/projects/")
    _make_projects(student_user, 5, jurado_user)
    assert _count_queries(authed_client, "/api/projects/") == baseline


@pytest.mark.django_db
def test_project_failed_attempts_still_counted(authed_client, student_user, jurado_user):
    _make_projects(student_user, 1, jurado_user)
    response = authed_client.get("/api/projects/")
    data = response.data["results"] if isinstance(response.data, dict) else response.data
    assert data[0]["failed_attempts"] == 1


@pytest.mark.django_db
def test_semester_list_queries_do_not_grow_with_semesters(authed_client):
    Semester.objects.create(period="2026-01", start_month=1, end_month=6)
    baseline = _count_queries(authed_client, "/api/semesters/")
    for year in range(2027, 2032):
        Semester.objects.create(period=f"{year}-01", start_month=1, end_month=6)
    assert _count_queries(authed_client, "/api/semesters/") == baseline
