# backend/tests/test_teg_state_backfill.py
"""Unit tests for the TEG state backfill function used by migration 0034."""

import pytest


@pytest.mark.parametrize(
    'status,stage1_passed,expected_state',
    [
        ('checked',  False, 'approved'),
        ('checked',  True,  'approved'),
        ('rejected', False, 'failed_final'),
        ('rejected', True,  'failed_final'),
        ('pending',  False, 'pending_articulo'),
        ('pending',  True,  'pending_defensa'),
    ],
)
def test_teg_state_backfill_mapping(status, stage1_passed, expected_state):
    from api.migrations._teg_backfill import compute_teg_state
    assert compute_teg_state(status=status, stage1_passed=stage1_passed) == expected_state
