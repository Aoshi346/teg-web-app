# Test Worker Result — 20260413-001-evaluation-viewset-tests — Phase RED + GREEN (combined)

## Status
green-confirmed

---

## Phase RED — Test Written

- `backend/tests/test_evaluations.py` — 20 tests across 4 classes
- `backend/conftest.py` — `project_factory` fixture added; all pre-existing fixtures corrected (see Infrastructure Fixes below)

### Tests written (file: backend/tests/test_evaluations.py)

| # | Test | Class |
|---|------|-------|
| 1 | `test_admin_can_create_evaluation` | `TestCreatePermissions` |
| 2 | `test_tutor_can_create_evaluation` | `TestCreatePermissions` |
| 3 | `test_jurado_can_create_evaluation` | `TestCreatePermissions` |
| 4 | `test_student_cannot_create_evaluation` | `TestCreatePermissions` |
| 5 | `test_unauthenticated_cannot_create_evaluation` | `TestCreatePermissions` |
| 6 | `test_proyecto_with_zero_failed_attempts_allows_creation` | `TestFailedAttemptsLimit` |
| 7 | `test_proyecto_with_one_failed_attempt_allows_creation` | `TestFailedAttemptsLimit` |
| 8 | `test_proyecto_with_two_failed_attempts_blocks_creation` | `TestFailedAttemptsLimit` |
| 9 | `test_proyecto_with_three_failed_attempts_blocks_creation` | `TestFailedAttemptsLimit` |
| 10 | `test_tesis_with_two_failed_attempts_allows_creation` | `TestFailedAttemptsLimit` |
| 11 | `test_tesis_with_many_failed_attempts_allows_creation` | `TestFailedAttemptsLimit` |
| 12 | `test_admin_lists_all_evaluations` | `TestQuerysetFiltering` |
| 13 | `test_tutor_lists_all_evaluations_regardless_of_assignment` | `TestQuerysetFiltering` |
| 14 | `test_jurado_lists_all_evaluations` | `TestQuerysetFiltering` |
| 15 | `test_student_lists_only_own_project_evaluations` | `TestQuerysetFiltering` |
| 16 | `test_student_as_partner_does_not_see_evaluation` | `TestQuerysetFiltering` |
| 17 | `test_project_query_param_filters_for_admin` | `TestQuerysetFiltering` |
| 18 | `test_project_query_param_respects_student_scope` | `TestQuerysetFiltering` |
| 19 | `test_create_without_project_field_returns_400` | `TestCreateValidation` |
| 20 | `test_create_with_nonexistent_project_returns_400` | `TestCreateValidation` |

### Minimal payload confirmed
After reading `EvaluationSerializer`: only `pass_status` is required (no default, has choices). `score`, `ratings`, `comments`, `section_scores` all have defaults or `required=False`. `project` is validated by the serializer AND by `perform_create`. Minimal payload used: `{"project": <id>, "pass_status": "Pass"}`.

### Infrastructure fix applied to conftest.py
The pre-existing `admin_user`, `tutor_user`, `jurado_user`, `student_user` fixtures used `User.objects.create_user(email=..., ...)` (keyword-only). Django 6's inherited `UserManager._create_user_object` always passes `username=username` as a keyword argument to the model constructor, which fails because `User.username = None` removes the field. No custom `UserManager` was defined on the model.

Fix: replaced `create_user()` calls with `User(...).set_password(...).save()` pattern via a `_make_user()` helper. This is a test infrastructure fix (not a production code change) and was necessary to make any test run at all. The same pattern was used for inline user creation in `test_evaluations.py` via `_make_student()`.

---

## Phase GREEN — Verification

### Per-test results

| # | Test | Result |
|---|------|--------|
| 1 | `test_admin_can_create_evaluation` | PASS |
| 2 | `test_tutor_can_create_evaluation` | PASS |
| 3 | `test_jurado_can_create_evaluation` | PASS |
| 4 | `test_student_cannot_create_evaluation` | PASS |
| 5 | `test_unauthenticated_cannot_create_evaluation` | PASS |
| 6 | `test_proyecto_with_zero_failed_attempts_allows_creation` | PASS |
| 7 | `test_proyecto_with_one_failed_attempt_allows_creation` | PASS |
| 8 | `test_proyecto_with_two_failed_attempts_blocks_creation` | PASS |
| 9 | `test_proyecto_with_three_failed_attempts_blocks_creation` | PASS |
| 10 | `test_tesis_with_two_failed_attempts_allows_creation` | PASS |
| 11 | `test_tesis_with_many_failed_attempts_allows_creation` | PASS |
| 12 | `test_admin_lists_all_evaluations` | PASS |
| 13 | `test_tutor_lists_all_evaluations_regardless_of_assignment` | PASS |
| 14 | `test_jurado_lists_all_evaluations` | PASS |
| 15 | `test_student_lists_only_own_project_evaluations` | PASS |
| 16 | `test_student_as_partner_does_not_see_evaluation` | PASS |
| 17 | `test_project_query_param_filters_for_admin` | PASS |
| 18 | `test_project_query_param_respects_student_scope` | PASS |
| 19 | `test_create_without_project_field_returns_400` | PASS |
| 20 | `test_create_with_nonexistent_project_returns_400` | PASS |

### Full suite
```
20 passed in 63.10s
```
No pre-existing tests existed, so no regressions possible.

### Ruff
```
ruff check tests/test_evaluations.py conftest.py
All checks passed!
```

## Potential Bugs Found
None. All 20 tests passed against the unchanged implementation.

Notable confirmed behaviors (from the brief's critical findings):
- Test 16 (`test_student_as_partner_does_not_see_evaluation`) PASSED — meaning the current code truly does NOT expose evaluations to a student who is `partner` (not `student`) on a project. This asymmetry is real and documented in the test's docstring. The orchestrator should surface this to the user as a design decision to review.
- Test 13 (`test_tutor_lists_all_evaluations_regardless_of_assignment`) PASSED — tutor sees all evaluations even for projects they don't advise.

## Notes for Orchestrator

1. **conftest.py was broken before this task** — the original `create_user()` calls would have failed for any test that used the user fixtures. The fix is in `_make_user()` helper. The orchestrator should note this in the summary for the user.

2. **`api.models.User` lacks a custom `UserManager`** — this is a latent bug in the production model that would affect any code that calls `User.objects.create_user()` or `create_superuser()` (e.g., management commands, admin). The `management/commands/create_test_users.py` script (mentioned in CLAUDE.md) likely also fails. This is worth flagging to the user.

3. **Partner visibility gap** — `get_queryset` in `EvaluationViewSet` filters students by `project__student=user`, not by `project__partner=user`. A student who is a partner sees zero evaluations about their own project. This is the current behavior (pinned by test 16), but may not be the intended UX.
