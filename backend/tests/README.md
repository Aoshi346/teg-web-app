# Backend Tests — TesisFar

## Running

```bash
source ../.venv/bin/activate
cd backend
pytest                                    # full suite
pytest tests/test_users.py               # one file
pytest tests/test_users.py::test_admin_can_list_users  # one test
pytest -k "permissions"                  # pattern match
pytest -v                                # verbose
```

## Conventions

- **Files:** `test_<feature>.py` (e.g., `test_evaluations.py`, `test_semesters.py`).
- **Fixtures:** Defined in `backend/conftest.py`. Use `admin_user`, `student_user`, `tutor_user`, `jurado_user` for user setup and `admin_client`, `student_client`, etc. for authenticated API clients.
- **DB access:** Add `@pytest.mark.django_db` to any test that touches the database.
- **Language:** Test code and test names in **English**. Complex helpers may have a **Spanish** docstring.

## Test Naming

Describe the behavior, not the implementation:

- ✅ `test_student_cannot_see_other_students_projects`
- ✅ `test_evaluation_fails_after_two_failed_attempts`
- ❌ `test_get_queryset`
- ❌ `test_permission_class_returns_false`

## TDD Workflow

This repo enforces strict TDD via the orchestration system in `.claude/`:

1. **RED** — `test-worker` writes a failing test.
2. **GREEN** — `backend-worker` implements the smallest change to make it pass.
3. **REFACTOR** — only if the test is green and the refactor is in the brief's scope.

Never write implementation before the RED phase is confirmed.

## Coverage (optional)

Not wired up yet. When you need it:

```bash
pip install pytest-cov
pytest --cov=api --cov-report=term-missing
```
