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
    defaults = {"title": "T", "project_type": "proyecto", "status": "pending"}
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

    def test_derive_state_has_no_tesis_guard(self, student):
        """
        Regla: `derive_state` no tiene guardia para TEG — devolverá un estado
        válido aunque le pasen un proyecto TEG. El filtro `project_type='proyecto'`
        en la migración 0030 es lo que previene que TEG sea tocado. Este test
        documenta ese contrato para que nadie añada un guard redundante dentro
        de `derive_state` sin leer la migración primero.
        """
        p = _mk(student, project_type='tesis', status='checked')
        assert derive_state(p, evaluations=[]) == 'approved'

    def test_checked_status_wins_over_fail_evals(self, student):
        """Contradiction: status='checked' + 2 Fail evals → approved (status wins)."""
        p = _mk(student, status='checked')
        evals = [
            Evaluation(project=p, pass_status='Fail', score=5, kind='review'),
            Evaluation(project=p, pass_status='Fail', score=4, kind='review'),
        ]
        assert derive_state(p, evaluations=evals) == 'approved'

    def test_pass_eval_wins_over_fail_evals(self, student):
        """
        Tie-breaker: a Pass eval overrides 2 Fail evals. Rule order is
        checked → has_pass → fails, so has_pass is evaluated before fails.
        """
        p = _mk(student, status='pending')
        evals = [
            Evaluation(project=p, pass_status='Pass', score=15, kind='review'),
            Evaluation(project=p, pass_status='Fail', score=5, kind='review'),
            Evaluation(project=p, pass_status='Fail', score=4, kind='review'),
        ]
        assert derive_state(p, evaluations=evals) == 'pending_defense'
