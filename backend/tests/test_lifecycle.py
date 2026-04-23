"""Unit tests for the PTEG lifecycle state machine. Pure — no DB."""

from dataclasses import dataclass

import pytest

from api.lifecycle import InvalidTransition, next_state, status_projection


@dataclass
class FakeProject:
    state: str


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


class TestStatusProjection:
    def test_approved_maps_to_checked(self):
        assert status_projection('approved') == 'checked'

    def test_failed_final_maps_to_rejected(self):
        assert status_projection('failed_final') == 'rejected'

    def test_pending_review_1_maps_to_pending(self):
        assert status_projection('pending_review_1') == 'pending'

    def test_pending_review_2_maps_to_pending(self):
        assert status_projection('pending_review_2') == 'pending'

    def test_pending_defense_maps_to_pending(self):
        assert status_projection('pending_defense') == 'pending'
