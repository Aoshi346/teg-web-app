# Backend Worker Result — 20260413-002-evaluation-queryset-fixes

## Status
done

## Files Changed
- backend/api/views.py:256-268 — replaced `EvaluationViewSet.get_queryset` to fix Bug A (partner visibility) and Bug B (Tutor over-access)

## Diff Applied

**File:** `backend/api/views.py`, lines 256-268

**Before (lines 256-265):**
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

**After (lines 256-268):**
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

No other code was touched. `Q` was already imported at line 6. `perform_create`, `create`, and `IsReviewerRole` are unchanged.

## Tests Status
- `pytest tests/test_evaluations.py -v` — **25 passed, 0 failed**
- `pytest` (full suite) — **25 passed, 0 failed**

All 6 previously-failing tests now pass:
- `TestQuerysetFiltering::test_tutor_lists_only_advised_project_evaluations` — PASS
- `TestQuerysetFiltering::test_student_as_partner_sees_evaluation` — PASS
- `TestQuerysetFiltering::test_tutor_filtered_by_project_query_param_for_unassigned_project` — PASS
- `TestQuerysetFiltering::test_student_as_partner_can_filter_by_project` — PASS
- `TestQuerysetFiltering::test_tutor_cannot_retrieve_evaluation_on_unassigned_project` — PASS
- `TestQuerysetFiltering::test_student_as_partner_can_retrieve_evaluation` — PASS

The invariant test `test_tutor_filtered_by_project_query_param_for_assigned_project` continued to pass (as expected).

## Lint Status
- `ruff check .` — 18 errors found, **all pre-existing** (I001 import ordering, B904 exception chaining, DJ012 model method ordering, DJ001 null=True on TextField, F401 unused import in api/tests.py). None of these are in the lines I modified. My change introduced zero new lint violations.

## Notes for Orchestrator
- The pre-existing ruff issues are across `api/admin.py`, `api/management/commands/set_semester.py`, `api/models.py`, `api/serializers.py`, `api/tests.py`, `api/urls.py`, `api/views.py`, `core/urls.py`, and `create_test_users.py`. These are out of scope for this task per the brief ("Only modify `backend/api/views.py`").
- No migrations were needed — this was a pure view logic change.
- The fix is exactly as specified in the brief's "Target behavior" section.

## Blockers
None.
