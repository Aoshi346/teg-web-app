# Test Worker Result — 20260413-002-evaluation-queryset-fixes — Phase RED

## Status
red-confirmed

## Fixture Changes
None. `conftest.py`'s `project_factory` already supports `partner=` via `kwargs` passthrough to `Project.objects.create()`, and handles `advisors=` via the M2M `.set()` branch. No changes to `conftest.py` were needed.

A second tutor user is created inline in `test_tutor_lists_only_advised_project_evaluations` using the same `User(...)` + `set_password()` + `save()` pattern from `_make_student`.

## Tests Written / Modified

### Renamed (assertions inverted)
1. `tests/test_evaluations.py::TestQuerysetFiltering::test_tutor_lists_only_advised_project_evaluations`
   - Was: `test_tutor_lists_all_evaluations_regardless_of_assignment` — asserted 2 evals returned (current broken behavior)
   - Now: sets up 2 projects (p1 advised by `tutor_user`, p2 advised by a second tutor), asserts only the eval for p1 is returned (correct behavior)

2. `tests/test_evaluations.py::TestQuerysetFiltering::test_student_as_partner_sees_evaluation`
   - Was: `test_student_as_partner_does_not_see_evaluation` — asserted 0 evals (current broken behavior)
   - Now: creates project with `partner=student_user`, asserts the evaluation IS in the response (correct behavior)

### New tests added
3. `tests/test_evaluations.py::TestQuerysetFiltering::test_tutor_filtered_by_project_query_param_for_unassigned_project`
   - Tutor queries `?project=<unassigned_project_id>`, expects 200 + empty list

4. `tests/test_evaluations.py::TestQuerysetFiltering::test_tutor_filtered_by_project_query_param_for_assigned_project`
   - Tutor queries `?project=<assigned_project_id>`, expects the evaluation in response
   - Note: this test PASSES against the current code (tutor sees all evals, so assigned project eval is included). It will continue to pass after the fix. This is an invariant test.

5. `tests/test_evaluations.py::TestQuerysetFiltering::test_student_as_partner_can_filter_by_project`
   - Partner student queries `?project=<partner_project_id>`, expects evaluation in response

6. `tests/test_evaluations.py::TestQuerysetFiltering::test_tutor_cannot_retrieve_evaluation_on_unassigned_project`
   - Tutor GETs `/api/evaluations/<id>/` for eval on unadvised project, expects 404

7. `tests/test_evaluations.py::TestQuerysetFiltering::test_student_as_partner_can_retrieve_evaluation`
   - Partner student GETs `/api/evaluations/<id>/` for partner project eval, expects 200

## Failure Confirmation

```
$ pytest tests/test_evaluations.py -v
============================= test session starts ==============================
...
tests/test_evaluations.py::TestQuerysetFiltering::test_tutor_lists_only_advised_project_evaluations FAILED [ 52%]
tests/test_evaluations.py::TestQuerysetFiltering::test_student_as_partner_sees_evaluation FAILED [ 64%]
tests/test_evaluations.py::TestQuerysetFiltering::test_tutor_filtered_by_project_query_param_for_unassigned_project FAILED [ 76%]
tests/test_evaluations.py::TestQuerysetFiltering::test_tutor_filtered_by_project_query_param_for_assigned_project PASSED [ 80%]  <-- invariant test
tests/test_evaluations.py::TestQuerysetFiltering::test_student_as_partner_can_filter_by_project FAILED [ 84%]
tests/test_evaluations.py::TestQuerysetFiltering::test_tutor_cannot_retrieve_evaluation_on_unassigned_project FAILED [ 88%]
tests/test_evaluations.py::TestQuerysetFiltering::test_student_as_partner_can_retrieve_evaluation FAILED [ 92%]
...
=================== 6 failed, 19 passed in 108.02s ===================
```

### Per-test failure reasons

All 6 failing tests fail due to **assertion errors** — the data returned does not match the expected correct behavior. None fail on import, setup, or fixture errors.

1. `test_tutor_lists_only_advised_project_evaluations`
   - `assert [1, 2] == [1]` — tutor currently sees 2 evals (Bug B: no advisor filtering), expected 1
   - Failing for the right reason (assertion)

2. `test_student_as_partner_sees_evaluation`
   - `assert 1 in []` — partner student gets empty list (Bug A: `project__student=user` excludes partner), expected eval in list
   - Failing for the right reason (assertion)

3. `test_tutor_filtered_by_project_query_param_for_unassigned_project`
   - `assert 1 == 0` — tutor gets 1 eval for unassigned project (Bug B), expected 0
   - Failing for the right reason (assertion)

4. `test_student_as_partner_can_filter_by_project`
   - `assert 1 in []` — partner student gets empty list even with project filter (Bug A), expected eval in list
   - Failing for the right reason (assertion)

5. `test_tutor_cannot_retrieve_evaluation_on_unassigned_project`
   - `assert 200 == 404` — tutor gets 200 for unadvised project eval (Bug B), expected 404
   - Failing for the right reason (assertion)

6. `test_student_as_partner_can_retrieve_evaluation`
   - `assert 404 == 200` — partner student gets 404 (Bug A, partner excluded from queryset), expected 200
   - Failing for the right reason (assertion)

### Note on test count
The brief expected 7 failing tests. One of the 7 new/modified tests (`test_tutor_filtered_by_project_query_param_for_assigned_project`) currently PASSES because the current buggy code (tutor sees all evals) happens to include the assigned project's eval — satisfying the assertion. This test is still correct: it passes now and will continue to pass after the fix, serving as an invariant guard.

## Next Step
Orchestrator should spawn backend-worker to implement the `get_queryset` fix in `backend/api/views.py` as described in the brief's "Target behavior" section.

## Blockers
None.
