# Task Brief — 20260413-002-evaluation-queryset-fixes

## Goal

Fix two bugs in `EvaluationViewSet.get_queryset` ([backend/api/views.py:256-265](backend/api/views.py#L256-L265)) that were discovered and pinned down by the characterization tests in task `20260413-001`:

1. **Bug A — Partner visibility gap.** A student who is a `partner` on a project cannot see that project's evaluations. The student/partner dynamic means both work on the same project, so both must see its evaluations.
2. **Bug B — Tutor over-access.** Any Tutor currently sees all evaluations regardless of advisor assignment. Tutors should only see evaluations for projects they advise — mirroring `ProjectViewSet.get_queryset`.

Both fixes are **scoped to the `list` and `retrieve` actions** (controlled by `get_queryset`). Permission to **create** evaluations is not changed — `IsReviewerRole` still allows all three reviewer roles.

## User Request (verbatim)

> Finding 2: The partner should see the evaluation as well, since the student/partner dynamic is that they both work on the same project.
> Finding 3: The tutors should only see the projects they advise, not the others

## Current behavior (to be changed)

```python
def get_queryset(self):
    user = self.request.user
    qs = Evaluation.objects.select_related('project', 'reviewer').all()
    project_id = self.request.query_params.get('project')
    if project_id:
        qs = qs.filter(project_id=project_id)

    if getattr(user, 'role', None) in ['Administrador', 'Tutor', 'Jurado']:
        return qs                           # BUG B: tutor is unfiltered
    return qs.filter(project__student=user) # BUG A: excludes partner
```

## Target behavior

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
    # Estudiante — own project OR partner project
    return qs.filter(Q(project__student=user) | Q(project__partner=user)).distinct()
```

`Q` is already imported at [views.py:6](backend/api/views.py#L6). `.distinct()` is required because `advisors` is M2M and the join could produce duplicates.

## Decomposition

**Strict TDD.** Order:

### 1. test-worker (RED)
Modify existing tests in `backend/tests/test_evaluations.py`:

- **Test #13** — rename `test_tutor_lists_all_evaluations_regardless_of_assignment` to `test_tutor_lists_only_advised_project_evaluations`. Assert that a tutor who advises project A but not project B sees only evaluations for A.
- **Test #16** — rename `test_student_as_partner_does_not_see_evaluation` to `test_student_as_partner_sees_evaluation`. Assert that a student listed as `partner` on a project sees that project's evaluations.

Add new tests:

- **`test_tutor_filtered_by_project_query_param_for_unassigned_project`** — tutor queries `?project=<unassigned_project_id>`, gets empty list (not 403).
- **`test_tutor_filtered_by_project_query_param_for_assigned_project`** — tutor queries `?project=<assigned_project_id>`, sees its evaluations.
- **`test_student_as_partner_can_filter_by_project`** — student-as-partner queries `?project=<partner_project_id>`, sees evaluations.
- **`test_tutor_cannot_retrieve_evaluation_on_unassigned_project`** — tutor GETs `/api/evaluations/<id>/` for an evaluation on a project they don't advise, gets 404.
- **`test_student_as_partner_can_retrieve_evaluation`** — student-as-partner GETs `/api/evaluations/<id>/` for a partner project, gets 200.

Run `pytest tests/test_evaluations.py -v`. The 2 modified tests + the 5 new retrieve/filter tests must **fail** against the current (unchanged) code. Confirm each one fails for the right reason (assertion, not import/setup). Report RED to `.claude/state/20260413-002-evaluation-queryset-fixes/test-worker-result.md`.

### 2. backend-worker
Read `test-worker-result.md` to confirm RED. Apply the target `get_queryset` implementation shown above to `backend/api/views.py`. No other changes. Do not touch `create`, `perform_create`, permissions, serializers, or urls. Run `pytest tests/test_evaluations.py -v` and confirm all 27 tests (original 20, with 2 renamed + 5 added) pass. Run `ruff check .`. Report to `.claude/state/20260413-002-evaluation-queryset-fixes/backend-worker-result.md`.

### 3. test-worker (GREEN)
Run the **full** backend suite (`pytest`) to confirm no regressions elsewhere. Run the 2 renamed + 5 added tests to confirm they now pass. Report GREEN to the same `test-worker-result.md` (append a GREEN phase section).

## Relevant Files

- `backend/api/views.py:246-285` — `EvaluationViewSet` (to be modified by backend-worker)
- `backend/api/views.py:130-151` — `ProjectViewSet.get_queryset` (**reference** — mirrors the target tutor filter)
- `backend/api/models.py:49-76` — `Project.partner`, `Project.advisors`
- `backend/tests/test_evaluations.py` — tests to modify/add (test-worker only)
- `backend/conftest.py` — existing fixtures (`project_factory` supports `advisors=` and `partner=` kwargs — verify in RED phase and extend if needed)

## Verification Criteria

- [ ] 2 existing tests renamed and assertions inverted to assert the correct behavior
- [ ] 5 new tests added
- [ ] `pytest tests/test_evaluations.py -v` → **25 passed, 0 failed** (20 original − 2 renamed + 2 renamed + 5 new = 25)
- [ ] `pytest` (full suite) → all green, no regressions
- [ ] `ruff check backend/` → clean
- [ ] Only `backend/api/views.py` and `backend/tests/test_evaluations.py` (and possibly `conftest.py`) modified. No other files.
- [ ] `EvaluationViewSet.create` and `IsReviewerRole` unchanged.

## Risks

- **Risk:** `project_factory` may not support `partner=` kwarg. **Mitigation:** test-worker verifies and extends `conftest.py` if needed (partner is optional FK, so just pass it through).
- **Risk:** `.distinct()` on the partner/student Q-or query may be unnecessary (since partner and student are non-M2M FKs), but it's needed for the tutor branch (M2M `advisors`). **Mitigation:** keep `.distinct()` on the tutor branch only; leave it off the student branch unless the test fails.
- **Risk:** The `?project=` filter already runs before the role branch — it intersects correctly with role filtering, but the test for "tutor queries unassigned project gets empty" must explicitly verify this intersection rather than assume.
- **Risk:** Mass assignment on queryset filters can produce unexpected results when a tutor is both an advisor AND a student on different projects. **Mitigation:** not a supported scenario in this app (tutors are not students) — out of scope.
- **Risk:** Changing `get_queryset` may affect `retrieve`, not just `list` — that's actually the fix we want. The 2 new retrieve-specific tests lock this down.

## Out of Scope

- Do **not** modify `IsReviewerRole` or `perform_create`.
- Do **not** change who can **create** evaluations.
- Do **not** touch the `failed_attempts` logic (that's pinned down by task 001).
- Do **not** fix the broken `User.objects.create_user()` (finding #1 from task 001 — separate task when you want it).
- Do **not** touch the frontend. Partners should *automatically* see evaluations once the backend serves them — no UI change needed for this task.
- Do **not** add coverage reporting, CI, or other infrastructure.

## Model & Worker Allocation

- Orchestrator: Opus 4.6
- test-worker (Sonnet 4.6) — two phases (RED and GREEN)
- backend-worker (Sonnet 4.6) — single phase (implement fix)

## Human Checkpoint

Status: `PENDING_APPROVAL`

After writing this brief, the orchestrator pauses and asks the user:
> "Plan drafted at `.claude/state/20260413-002-evaluation-queryset-fixes/brief.md`. Approve to proceed, request changes, or cancel."

The orchestrator may not spawn any worker until the user replies with explicit approval.
