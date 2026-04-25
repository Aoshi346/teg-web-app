# backend/tests/test_teg_evaluation_transitions.py
"""Integration tests: creating Evaluations on a TEG advances Project.state."""

import pytest
from django.urls import reverse
from rest_framework.test import APIClient

from api.models import Project, User


@pytest.fixture
def admin(db):
    return User.objects.create_user(
        email='admin-teg@example.com', password='x', role='Administrador',
        first_name='A', last_name='Dmin',
    )


@pytest.fixture
def jurado(db):
    return User.objects.create_user(
        email='jurado-teg@example.com', password='x', role='Jurado',
        first_name='J', last_name='Urado',
    )


@pytest.fixture
def student(db):
    return User.objects.create_user(
        email='student-teg@example.com', password='x', role='Estudiante',
        first_name='S', last_name='Tudent',
    )


@pytest.fixture
def teg(db, student, jurado):
    return Project.objects.create(
        title='TEG', student=student, project_type='tesis',
        state='pending_articulo', reviewer=jurado, period='2026-01',
    )


@pytest.fixture
def client(admin):
    c = APIClient()
    c.force_authenticate(user=admin)
    return c


def _post_eval(client, teg, kind, pass_status):
    return client.post(
        reverse('evaluation-list'),
        {'project': teg.id, 'kind': kind, 'pass_status': pass_status, 'score': 15},
        format='json',
    )


def test_articulo_pass_advances_to_entrega(client, teg):
    response = _post_eval(client, teg, 'review', 'Pass')
    assert response.status_code == 201
    teg.refresh_from_db()
    assert teg.state == 'pending_entrega'


def test_articulo_fail_terminal(client, teg):
    response = _post_eval(client, teg, 'review', 'Fail')
    assert response.status_code == 201
    teg.refresh_from_db()
    assert teg.state == 'failed_final'


def test_full_happy_path_to_approved(client, teg):
    assert _post_eval(client, teg, 'review', 'Pass').status_code == 201
    assert _post_eval(client, teg, 'review', 'Pass').status_code == 201
    assert _post_eval(client, teg, 'defense', 'Pass').status_code == 201
    teg.refresh_from_db()
    assert teg.state == 'approved'


def test_defense_kind_on_articulo_rejected_400(client, teg):
    response = _post_eval(client, teg, 'defense', 'Pass')
    assert response.status_code == 400


def test_evaluation_after_failed_final_rejected_400(client, teg):
    teg.state = 'failed_final'
    teg.save(update_fields=['state'])
    response = _post_eval(client, teg, 'review', 'Pass')
    assert response.status_code == 400
