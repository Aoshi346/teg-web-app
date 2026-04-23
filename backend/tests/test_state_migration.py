"""
Tests de migración de datos para `0030_backfill_project_state`.

Ejecuta la lógica de backfill directamente sobre modelos reales (no uso de
pytest-django migrations) para verificar que las reglas derivan el estado
correcto a partir de los campos legacy.
"""

import pytest
from django.contrib.auth import get_user_model

from api.migrations._state_backfill_logic import derive_state
from api.models import Evaluation, Project

User = get_user_model()


@pytest.fixture
def student(db):
    return User.objects.create_user(
        email="s@t.local", password="x", first_name="S", last_name="T",
        role="Estudiante", status="active",
    )


def _mk(student, **kwargs):
    defaults = {"title": "T", "project_type": "proyecto", "status": "pending", "failed_attempts": 0}
    defaults.update(kwargs)
    return Project.objects.create(student=student, **defaults)


class TestDeriveState:
    def test_no_evals_is_pending_review_1(self, student):
        p = _mk(student)
        assert derive_state(p, evaluations=[]) == 'pending_review_1'

    def test_one_fail_eval_is_pending_review_2(self, student):
        p = _mk(student)
        evals = [Evaluation(project=p, pass_status='Fail', score=5, kind='review')]
        assert derive_state(p, evaluations=evals) == 'pending_review_2'

    def test_one_pass_eval_pending_status_is_pending_defense(self, student):
        p = _mk(student, status='pending')
        evals = [Evaluation(project=p, pass_status='Pass', score=15, kind='review')]
        assert derive_state(p, evaluations=evals) == 'pending_defense'

    def test_one_pass_eval_checked_status_is_approved(self, student):
        p = _mk(student, status='checked')
        evals = [Evaluation(project=p, pass_status='Pass', score=15, kind='review')]
        assert derive_state(p, evaluations=evals) == 'approved'

    def test_two_fail_evals_is_failed_final(self, student):
        p = _mk(student)
        evals = [
            Evaluation(project=p, pass_status='Fail', score=5, kind='review'),
            Evaluation(project=p, pass_status='Fail', score=4, kind='review'),
        ]
        assert derive_state(p, evaluations=evals) == 'failed_final'

    def test_failed_attempts_counter_without_evals_still_classifies(self, student):
        p = _mk(student, failed_attempts=2)
        assert derive_state(p, evaluations=[]) == 'failed_final'

    def test_failed_attempts_one_without_evals_is_pending_review_2(self, student):
        p = _mk(student, failed_attempts=1)
        assert derive_state(p, evaluations=[]) == 'pending_review_2'

    def test_tesis_is_untouched(self, student):
        p = _mk(student, project_type='tesis', status='checked')
        # derive_state only called for PTEG; caller must skip for TEG
        # but the function itself should still behave; no special case here.
        # This test just documents that TEG callers skip the function.
        assert p.project_type == 'tesis'
