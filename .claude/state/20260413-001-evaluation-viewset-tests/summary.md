# Summary — 20260413-001-evaluation-viewset-tests

## Final Status

**DONE — GREEN CONFIRMED** ✅

All 20 characterization tests pass against unchanged production code. No backend-worker was needed; this was pure test-writing.

```
pytest tests/test_evaluations.py -v
======================== 20 passed in 64.17s ========================
```

## Files Changed

| File | Change |
|---|---|
| `backend/tests/test_evaluations.py` | **NEW** — 20 tests in 4 classes (Create Permissions, Failed Attempts Limit, Queryset Filtering, Create Validation) |
| `backend/conftest.py` | **MODIFIED** — added `project_factory` fixture + fixed pre-existing broken user fixtures (see Finding #1 below) |

## Test Breakdown

### Role permissions on `create` — 5/5 ✅
- admin / tutor / jurado can create (201)
- student cannot (403)
- unauthenticated cannot (401/403)

### 2-attempt limit on `proyecto` — 6/6 ✅
- `proyecto` with `failed_attempts` 0, 1 → allowed
- `proyecto` with `failed_attempts` 2, 3 → blocked (400)
- `tesis` with `failed_attempts` 2, 99 → **allowed** (the limit does not apply to `tesis`)

### Queryset filtering on `list` — 7/7 ✅
- admin / tutor / jurado see all evaluations
- student sees only their own projects' evaluations (as `student`, not `partner`)
- `?project=` filter works for admin and respects student scope

### Create validation — 2/2 ✅
- missing `project` field → 400
- nonexistent `project` id → 400

## Findings to Report to the User

### Finding #1 — Pre-existing bug: `User.objects.create_user()` is broken in this project

**Severity:** Medium. Affects any script that creates users programmatically.

**What we found:**
The `api.User` model sets `username = None` to disable the field (since auth uses `email`), but **no custom `UserManager`** is defined. Django 6's inherited `UserManager._create_user_object` still passes `username=<value>` to the model constructor, which then raises:

```
TypeError: User() got unexpected keyword arguments: 'username'
```

**Impact:**
- [`backend/create_test_users.py`](backend/create_test_users.py) almost certainly doesn't work anymore if it uses `create_user()` — worth checking.
- Any management command, data migration, or seed script using `User.objects.create_user()` will fail the same way.

**How the tests worked around it:**
`conftest.py` now uses `User(...); user.set_password(); user.save()` directly, bypassing the manager. This is a **test infrastructure fix only** — no production code was touched.

**Recommended follow-up (not part of this task):**
Add a custom `UserManager` to `api/models.py` that overrides `_create_user` to not pass `username`. Open a separate task if you want this fixed.

### Finding #2 — Design asymmetry: students see projects as `partner` but not evaluations

**Severity:** Unclear — may be intentional, may be a bug.

**What we found:**
- [`ProjectViewSet.get_queryset`](backend/api/views.py#L149-L151): a student sees projects where they are **either** `student` **or** `partner`.
- [`EvaluationViewSet.get_queryset`](backend/api/views.py#L265): a student sees only evaluations where they are `project__student`. **Partners do not see evaluations of projects they are on.**

**Test pinning this down:**
[`test_student_as_partner_does_not_see_evaluation`](backend/tests/test_evaluations.py) — explicitly verifies the current behavior.

**Question for the user:**
Should a partner see the evaluations for a shared project? If yes, this is a real bug and should be a new task. If no, the current behavior is correct and the test is a legitimate regression guard.

### Finding #3 — Design decision: tutors see all evaluations regardless of assignment

**Severity:** Likely intentional, but worth confirming.

**What we found:**
[`EvaluationViewSet.get_queryset`](backend/api/views.py#L263-L264) returns all evaluations for any role in `['Administrador', 'Tutor', 'Jurado']`. A tutor who is **not** assigned as advisor on a project can still list evaluations for that project.

**Compare with `ProjectViewSet`:**
`ProjectViewSet.get_queryset` filters tutors by `advisors=user`. So a tutor sees only their advised projects, but can read evaluations for projects they don't advise.

**Test pinning this down:**
[`test_tutor_lists_all_evaluations_regardless_of_assignment`](backend/tests/test_evaluations.py)

**Question for the user:**
Is this intentional (tutors should see all evaluations for cross-referencing purposes) or should tutors only see evaluations on their advised projects?

## Verification Criteria — Status

- [x] `backend/tests/test_evaluations.py` exists with 20 test cases
- [x] `pytest tests/test_evaluations.py -v` → 20 passed, 0 failed
- [x] Full suite → 20 passed, 0 failed (no other test files yet)
- [x] `ruff check` → clean
- [x] Production code **unchanged**
- [x] Any ambiguous behavior flagged, not silently adjusted

## Next Steps for the Human

1. **Review** `backend/tests/test_evaluations.py` and `backend/conftest.py`.
2. **Decide** on Findings #2 and #3:
   - If either is a bug → open a new task (e.g., `20260413-002-evaluation-partner-visibility-fix`) and I will plan it with strict TDD: fix the viewset, update the existing test to assert the new behavior, no regressions.
   - If both are intentional → the tests are correct as written and become your regression guard.
3. **Decide** on Finding #1 (broken `create_user`): if you want a custom `UserManager`, open a separate task.
4. **Commit** when ready. I have not touched git.

## Artifacts

- Brief: `.claude/state/20260413-001-evaluation-viewset-tests/brief.md`
- Test-worker result: `.claude/state/20260413-001-evaluation-viewset-tests/test-worker-result.md`
- Summary (this file): `.claude/state/20260413-001-evaluation-viewset-tests/summary.md`
