# Task Brief — 20260413-001-evaluation-viewset-tests

## Goal

Write a comprehensive pytest integration test suite for `EvaluationViewSet` that locks in the current behavior of the two most important business rules:

1. **Role-based access** — who can create, list, and retrieve evaluations (`IsReviewerRole`, `get_queryset` filtering).
2. **The 2-attempt limit** — enforced in `perform_create` at `backend/api/views.py:276-277` for `project_type='proyecto'` only.

These tests are **characterization tests** for behavior that currently exists in code but is untested. They become the safety net for any future refactor of `EvaluationViewSet`.

## User Request (verbatim)

> Write tests of integration for EvalutionViewSet, taking into account the max limit of 2 and respecting the roles

## Critical Findings From Reading The Code

Before planning the tests I read `backend/api/views.py:246-285`, `backend/api/models.py:90-107`, and `backend/api/CLAUDE.md`. The following behaviors will be pinned down — some are subtle and would silently break in a refactor:

1. **Create permission** — `IsReviewerRole` allows only roles `Administrador`, `Tutor`, `Jurado`. Students get 403. Unauthenticated requests get 401/403.
2. **2-attempt limit is type-specific** — the guard at `views.py:276` only fires when `project.project_type == 'proyecto'`. A `tesis` with any `failed_attempts` is **allowed** to receive new evaluations. This is non-obvious and easy to break.
3. **The limit is a `>=` check** — `failed_attempts >= 2` blocks. So 0 and 1 are allowed, 2+ is blocked.
4. **`failed_attempts` is not auto-incremented by the view** — posting a failing evaluation does NOT bump the counter. Tests must set the counter manually; they are not testing the increment logic (there is none in `EvaluationViewSet`).
5. **Student queryset filter** — `get_queryset` for students returns `qs.filter(project__student=user)`. It does **not** include projects where the user is a `partner`. This is asymmetric with `ProjectViewSet.get_queryset` and is the current behavior we're pinning down.
6. **Tutor/Jurado queryset is unfiltered by assignment** — `get_queryset` returns all evaluations for any role in `['Administrador', 'Tutor', 'Jurado']`, even for Tutors not assigned to the project. This is the current behavior.
7. **`?project=X` filter** — applies before role filtering, works for all roles.
8. **Error wrapping** — `EvaluationViewSet.create` catches `ValidationError` and returns 400. Assertions should expect 400 on business rule violations.

If any of these findings contradict actual intended behavior, **that is a bug in production code, not in the tests**. The user should be notified before we silently "fix" it via test assertions.

## Decomposition

This task is **backend-only**. No frontend changes. No new models. No migrations.

### Phase 1 — Setup (one-shot, handled inside test-worker RED step)
- Ensure `pytest-django`, `pytest`, and `ruff` are installed (user already did `pip install -r requirements.txt`).
- Ensure `conftest.py` fixtures are usable. Add a `Project` factory fixture since `conftest.py` currently only has users.

### Phase 2 — test-worker (RED)
Write `backend/tests/test_evaluations.py` with the following test cases. **All tests must fail initially only because the file did not exist before** — they should pass against the current implementation once written. (This is characterization testing — the RED phase here is the absence of the test file, and GREEN is the test passing against unchanged code. No backend-worker is needed for this task.)

#### Role permission tests (create)
1. `test_admin_can_create_evaluation` — POST as admin returns 201 and persists.
2. `test_tutor_can_create_evaluation` — POST as tutor returns 201.
3. `test_jurado_can_create_evaluation` — POST as jurado returns 201.
4. `test_student_cannot_create_evaluation` — POST as student returns 403.
5. `test_unauthenticated_cannot_create_evaluation` — POST with no auth returns 401 or 403 (accept either — DRF default is 403 for session auth).

#### 2-attempt limit tests
6. `test_proyecto_with_zero_failed_attempts_allows_creation` — `failed_attempts=0`, POST succeeds (201).
7. `test_proyecto_with_one_failed_attempt_allows_creation` — `failed_attempts=1`, POST succeeds (201).
8. `test_proyecto_with_two_failed_attempts_blocks_creation` — `failed_attempts=2`, POST returns 400 with the Spanish error message containing `"2 intentos"`.
9. `test_proyecto_with_three_failed_attempts_blocks_creation` — `failed_attempts=3`, POST returns 400. Locks in the `>=` semantics.
10. `test_tesis_with_two_failed_attempts_allows_creation` — `project_type='tesis'`, `failed_attempts=2`, POST succeeds (201). **Pins down the type-specific nature of the guard.**
11. `test_tesis_with_many_failed_attempts_allows_creation` — `project_type='tesis'`, `failed_attempts=99`, POST succeeds (201).

#### Queryset filtering tests (list + retrieve)
12. `test_admin_lists_all_evaluations` — seeds 3 evaluations across 3 projects, admin sees all 3.
13. `test_tutor_lists_all_evaluations_regardless_of_assignment` — seeds evaluations, tutor is not assigned as advisor on some, still sees all. Pins down current unfiltered behavior.
14. `test_jurado_lists_all_evaluations` — same as admin.
15. `test_student_lists_only_own_project_evaluations` — student with one project and evaluations on other students' projects sees only their own.
16. `test_student_as_partner_does_not_see_evaluation` — pins down finding #5: student is `partner` on project X, evaluation exists on X, student does NOT see it. **If the user thinks this is a bug, flag it in summary.md.**
17. `test_project_query_param_filters_for_admin` — `GET ?project=<id>` returns only evaluations for that project.
18. `test_project_query_param_respects_student_scope` — student queries `?project=<other_student_project_id>`, gets empty list (not 403, not leaked).

#### Create validation tests
19. `test_create_without_project_field_returns_400` — POST with no `project` key returns 400.
20. `test_create_with_nonexistent_project_returns_400` — POST with `project=99999` returns 400.

#### Required payload shape
Use a minimal valid body: `{"project": <id>, "pass_status": "Pass", "score": 15, "ratings": {}, "comments": {"general": "ok"}, "section_scores": {"total": 15, "diagramacion": 4, "contenido": 11}}`. Inspect `EvaluationSerializer` in the RED phase to confirm exact required fields and adjust if necessary.

### Phase 3 — test-worker (GREEN)
Run the full suite and confirm all 20 tests pass against the unchanged implementation. Report any test that fails — that indicates either a misunderstanding of the current behavior or a real bug.

## Relevant Files (context)

- `backend/api/views.py:246-285` — `EvaluationViewSet` and `IsReviewerRole` — the code under test.
- `backend/api/models.py:90-107` — `Evaluation` model.
- `backend/api/models.py:49-76` — `Project` model (`project_type`, `failed_attempts`).
- `backend/api/serializers.py` — `EvaluationSerializer` (must read in RED to confirm required fields).
- `backend/conftest.py` — existing user/client fixtures. **Will need a new `project_factory` fixture added.**
- `backend/tests/test_evaluations.py` — the file to create.
- `backend/api/urls.py` — to confirm the router prefix is `/api/evaluations/`.

## Verification Criteria

- [ ] `backend/tests/test_evaluations.py` exists with all 20 test cases.
- [ ] `cd backend && source ../.venv/bin/activate && pytest tests/test_evaluations.py -v` → **20 passed, 0 failed**.
- [ ] `pytest` (full suite) → all green, no regressions in any other test file.
- [ ] `ruff check backend/tests/test_evaluations.py` → clean.
- [ ] `ruff check backend/conftest.py` → clean (after adding `project_factory`).
- [ ] Any test that fails against current implementation is **reported in summary.md** as a potential real bug, not silently adjusted.

## Risks

- **Risk:** `EvaluationSerializer` may require fields I haven't accounted for in the minimal payload (e.g., `pass_status` is a `CharField` without a default and with `choices`, which is required). **Mitigation:** test-worker must read `serializers.py` during RED phase and adjust.
- **Risk:** Tests 16 (partner-not-seeing-evaluation) or 13 (tutor-unfiltered) could reveal real bugs. **Mitigation:** If a test fails, the orchestrator must **stop** and report to the user before touching any code. Do NOT change the assertion to match the bug.
- **Risk:** Unauthenticated test case (5) may return 401 or 403 depending on DRF's authentication classes. **Mitigation:** Assert `response.status_code in (401, 403)`.
- **Risk:** The post-edit hook runs `ruff` and `eslint`/`tsc` on every Edit/Write. For this task that's fine, but the hook output may look noisy in the agent UI. **Mitigation:** none needed — hooks are non-blocking by design.
- **Risk:** `conftest.py` currently has no `Project` fixture. Adding one couples the test infrastructure to the Project model; if the model changes, the factory must be updated. **Mitigation:** keep the factory minimal and inline-parameterized.

## Out of Scope

- **Do NOT** modify `EvaluationViewSet`, `IsReviewerRole`, or any production code. This is pure test-writing against current behavior.
- **Do NOT** add auto-increment logic for `failed_attempts` — that's a separate feature discussion.
- **Do NOT** fix the "student as partner doesn't see evaluations" asymmetry — only document it if it fails.
- **Do NOT** add tests for PATCH/PUT/DELETE on evaluations. Scope is CREATE + LIST + RETRIEVE.
- **Do NOT** add coverage reporting, CI config, or test factories beyond what this task needs.
- **Do NOT** touch the frontend at all.

## Model & Worker Allocation

- Orchestrator: Opus 4.6
- test-worker (Sonnet 4.6) — **only worker needed for this task**. No backend-worker because we are not writing or modifying production code.

## Human Checkpoint

Status: `PENDING_APPROVAL`

After writing this brief, the orchestrator pauses and asks the user:
> "Plan drafted at `.claude/state/20260413-001-evaluation-viewset-tests/brief.md`. Approve to proceed, request changes, or cancel."

The orchestrator may not spawn the test-worker until the user replies with explicit approval.
