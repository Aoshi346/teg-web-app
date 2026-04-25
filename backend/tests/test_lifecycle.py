"""Unit tests for the PTEG lifecycle state machine. Pure — no DB."""

from dataclasses import dataclass

import pytest

from api.lifecycle import InvalidTransition, next_state


@dataclass
class FakeProject:
    state: str
    project_type: str = 'proyecto'


class TestNextStateReview:
    def test_review_pass_on_pending_review_1_goes_to_pending_defense(self):
        assert next_state(FakeProject(state='pending_review_1'), 'review', 'Pass') == 'pending_defense'

    def test_review_fail_on_pending_review_1_goes_to_pending_review_2(self):
        assert next_state(FakeProject(state='pending_review_1'), 'review', 'Fail') == 'pending_review_2'

    def test_review_pass_on_pending_review_2_goes_to_pending_defense(self):
        assert next_state(FakeProject(state='pending_review_2'), 'review', 'Pass') == 'pending_defense'

    def test_review_fail_on_pending_review_2_goes_to_failed_final(self):
        assert next_state(FakeProject(state='pending_review_2'), 'review', 'Fail') == 'failed_final'

    def test_review_on_pending_defense_raises(self):
        with pytest.raises(InvalidTransition):
            next_state(FakeProject(state='pending_defense'), 'review', 'Pass')


class TestNextStateDefense:
    def test_defense_pass_on_pending_defense_goes_to_approved(self):
        assert next_state(FakeProject(state='pending_defense'), 'defense', 'Pass') == 'approved'

    def test_defense_fail_on_pending_defense_stays_pending_defense(self):
        assert next_state(FakeProject(state='pending_defense'), 'defense', 'Fail') == 'pending_defense'

    def test_defense_on_pending_review_1_raises(self):
        with pytest.raises(InvalidTransition):
            next_state(FakeProject(state='pending_review_1'), 'defense', 'Pass')

    def test_defense_on_pending_review_2_raises(self):
        with pytest.raises(InvalidTransition):
            next_state(FakeProject(state='pending_review_2'), 'defense', 'Pass')


class TestTerminalStates:
    def test_any_eval_on_approved_raises(self):
        with pytest.raises(InvalidTransition):
            next_state(FakeProject(state='approved'), 'review', 'Pass')

    def test_any_eval_on_failed_final_raises(self):
        with pytest.raises(InvalidTransition):
            next_state(FakeProject(state='failed_final'), 'review', 'Fail')

    def test_defense_on_approved_raises(self):
        with pytest.raises(InvalidTransition):
            next_state(FakeProject(state='approved'), 'defense', 'Pass')


class TestUnknownInputs:
    def test_unknown_kind_raises(self):
        with pytest.raises(InvalidTransition):
            next_state(FakeProject(state='pending_review_1'), 'garbage', 'Pass')


class TestUnknownPassStatus:
    def test_lowercase_pass_raises(self):
        with pytest.raises(InvalidTransition):
            next_state(FakeProject(state='pending_review_1'), 'review', 'pass')

    def test_none_pass_status_raises(self):
        with pytest.raises(InvalidTransition):
            next_state(FakeProject(state='pending_review_1'), 'review', None)

    def test_empty_string_pass_status_raises(self):
        with pytest.raises(InvalidTransition):
            next_state(FakeProject(state='pending_review_1'), 'review', '')

    def test_arbitrary_string_pass_status_raises(self):
        with pytest.raises(InvalidTransition):
            next_state(FakeProject(state='pending_review_1'), 'review', 'Yes')



class _FakeProject:
    def __init__(self, project_type, state):
        self.project_type = project_type
        self.state = state


def teg(state):
    return _FakeProject('tesis', state)


def pteg(state):
    return _FakeProject('proyecto', state)


class TestTegTransitions:
    def test_articulo_pass_advances_to_entrega(self):
        assert next_state(teg('pending_articulo'), 'review', 'Pass') == 'pending_entrega'

    def test_articulo_fail_terminal(self):
        assert next_state(teg('pending_articulo'), 'review', 'Fail') == 'failed_final'

    def test_entrega_pass_advances_to_defensa(self):
        assert next_state(teg('pending_entrega'), 'review', 'Pass') == 'pending_defensa'

    def test_entrega_fail_terminal(self):
        assert next_state(teg('pending_entrega'), 'review', 'Fail') == 'failed_final'

    def test_defensa_pass_approved(self):
        assert next_state(teg('pending_defensa'), 'defense', 'Pass') == 'approved'

    def test_defensa_fail_terminal(self):
        assert next_state(teg('pending_defensa'), 'defense', 'Fail') == 'failed_final'

    def test_defense_kind_on_articulo_is_invalid(self):
        with pytest.raises(InvalidTransition):
            next_state(teg('pending_articulo'), 'defense', 'Pass')

    def test_review_kind_on_defensa_is_invalid(self):
        with pytest.raises(InvalidTransition):
            next_state(teg('pending_defensa'), 'review', 'Pass')

    def test_terminal_state_rejects_further_evaluations(self):
        with pytest.raises(InvalidTransition):
            next_state(teg('approved'), 'defense', 'Pass')
        with pytest.raises(InvalidTransition):
            next_state(teg('failed_final'), 'review', 'Fail')

    def test_pteg_transitions_unchanged(self):
        # Regression guard for the PTEG dispatch
        assert next_state(pteg('pending_review_1'), 'review', 'Pass') == 'pending_defense'
        assert next_state(pteg('pending_review_1'), 'review', 'Fail') == 'pending_review_2'
        assert next_state(pteg('pending_review_2'), 'review', 'Fail') == 'failed_final'
        assert next_state(pteg('pending_defense'), 'defense', 'Pass') == 'approved'
        # Existing behaviour: defense Fail keeps the project at pending_defense
        assert next_state(pteg('pending_defense'), 'defense', 'Fail') == 'pending_defense'
