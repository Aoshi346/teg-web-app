# Summary — 20260413-002-evaluation-queryset-fixes

## Final Status

**DONE — GREEN CONFIRMED** ✅

Both bugs fixed via strict TDD. 25/25 tests pass. No regressions.

```
pytest tests/test_evaluations.py -v
======================== 25 passed in 108.28s ========================
```

## Files Changed

| File | Change |
|---|---|
| `backend/api/views.py:256-268` | Rewrote `EvaluationViewSet.get_queryset`: Tutor now filtered by `project__advisors=user`; Estudiante now matches on `student` OR `partner`. |
| `backend/tests/test_evaluations.py` | Renamed 2 tests (inverted assertions to match correct behavior), added 5 new tests for tutor/partner scenarios across list, retrieve, and `?project=` filter. |

No changes to `conftest.py` — existing `project_factory` already supported `partner=` and `advisors=` kwargs.

## The Fix

**Before** (`backend/api/views.py:256-265`):
```python
def get_queryset(self):
    user = self.request.user
    qs = Evaluation.objects.select_related('project', 'reviewer').all()
    project_id = self.request.query_params.get('project')
    if project_id:
        qs = qs.filter(project_id=project_id)
    if getattr(user, 'role', None) in ['Administrador', 'Tutor', 'Jurado']:
        return qs
    return qs.filter(project__student=user)
```

**After**:
```python
def get_queryset(self):
    user = self.request.user
    qs = Evaluation.objects.select_related('project', 'reviewer').all()
    project_id = self.request.query_params.get('project')
    if project_id:
        qs = qs.filter(project_id=project_id)
    role = getattr(user, 'role', None)
    if role in ['Administrador', 'Jurado']:
        return qs
    if role == 'Tutor':
        return qs.filter(project__advisors=user).distinct()
    return qs.filter(Q(project__student=user) | Q(project__partner=user)).distinct()
```

## TDD Trace

1. **RED** — test-worker renamed 2 tests + added 5. 6 of 7 failed with assertion errors against unchanged code (1 of the new tests was an invariant guard that already passed). Confirmed failures were not import/setup errors.
2. **GREEN (backend-worker)** — Applied the 6-line fix. `pytest tests/test_evaluations.py -v` → 25 passed.
3. **GREEN (orchestrator verification)** — Ran `pytest tests/test_evaluations.py -v` independently → 25 passed in 108s.

## Test Deltas

### Renamed (assertions inverted to match correct behavior)
- `test_tutor_lists_all_evaluations_regardless_of_assignment` → `test_tutor_lists_only_advised_project_evaluations`
- `test_student_as_partner_does_not_see_evaluation` → `test_student_as_partner_sees_evaluation`

### Added
- `test_tutor_filtered_by_project_query_param_for_unassigned_project`
- `test_tutor_filtered_by_project_query_param_for_assigned_project` (invariant guard — already passed pre-fix)
- `test_student_as_partner_can_filter_by_project`
- `test_tutor_cannot_retrieve_evaluation_on_unassigned_project`
- `test_student_as_partner_can_retrieve_evaluation`

### Unchanged (still passing)
All 18 tests for: create permissions (5), 2-attempt limit (6), admin/jurado list filtering (3), student own-project filtering (1), `?project=` admin/student scope (2), create validation (2), and the pre-existing `test_student_lists_only_own_project_evaluations`.

## Verification Criteria — Status

- [x] 2 existing tests renamed with inverted assertions
- [x] 5 new tests added
- [x] `pytest tests/test_evaluations.py -v` → 25 passed
- [x] `pytest` (full suite) → 25 passed, no regressions
- [x] `ruff check backend/` → no new violations (18 pre-existing issues untouched — out of scope)
- [x] Only `backend/api/views.py` and `backend/tests/test_evaluations.py` modified
- [x] `EvaluationViewSet.create` and `IsReviewerRole` unchanged

## Notes on Ruff

`ruff check .` reports 18 pre-existing warnings across the backend — none introduced by this change. These are scope for a separate cleanup task if desired (not a blocker).

## Next Steps for the Human

1. **Review the diff** in `backend/api/views.py:256-268` and the test updates.
2. **Smoke check** in the UI if you have partner projects set up — a partner should now see evaluations in the project detail page. No frontend change was needed; the API now simply returns the data.
3. **Commit when ready.** Suggested message:
   ```
   fix(evaluations): partners see evaluations, tutors see only advised projects

   - EvaluationViewSet.get_queryset now includes Project.partner in the
     student branch and filters tutors by advisor assignment
   - Adds 5 integration tests + renames 2 characterization tests to
     lock in the corrected behavior
   ```
4. **Still open** (from task 001 findings, not addressed here):
   - Finding #1 — `User.objects.create_user()` is broken (missing custom `UserManager`). Affects `create_test_users.py`. Open a new task when you want this fixed.

## Artifacts

- Brief: `.claude/state/20260413-002-evaluation-queryset-fixes/brief.md`
- test-worker result: `.claude/state/20260413-002-evaluation-queryset-fixes/test-worker-result.md`
- backend-worker result: `.claude/state/20260413-002-evaluation-queryset-fixes/backend-worker-result.md`
- Summary (this file): `.claude/state/20260413-002-evaluation-queryset-fixes/summary.md`
