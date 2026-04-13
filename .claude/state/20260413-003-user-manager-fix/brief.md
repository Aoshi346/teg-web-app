# Task Brief — 20260413-003-user-manager-fix

## Goal

Add a custom `UserManager` to `api.User` so that `User.objects.create_user(...)` and `User.objects.create_superuser(...)` work against the custom User model (which disables `username`). Lock the fix down with unit and integration tests.

## Important correction to the earlier finding

In the summary of task `20260413-001`, I wrote that `create_test_users.py` was broken by the missing `UserManager`. **This is incorrect.** After re-reading [backend/create_test_users.py](backend/create_test_users.py), it does NOT call `create_user()`. It uses `User.objects.get_or_create()` + direct attribute assignment + `set_password()`. So it is currently working.

The actual broken paths are:

1. **`RegisterSerializer.create()`** at [backend/api/serializers.py:75](backend/api/serializers.py#L75) — calls `User.objects.create_user(email=..., password=..., ...)`. This is the **`/api/auth/register/` endpoint**. In practice this means **user registration is broken in production**. That is a real user-facing bug.
2. **`python manage.py createsuperuser`** — the Django management command calls `User.objects.create_superuser(**user_data)` through the default manager, which hits the same `TypeError: User() got unexpected keyword arguments: 'username'`.
3. **Future code** — any developer instinctively calling `User.objects.create_user(...)` will hit the same error.
4. **Test fixtures workaround** — `conftest.py._make_user` currently works around the bug by bypassing `create_user`. Once fixed, this workaround can be removed.

## User Request (verbatim)

> Start with create test users

Interpretation: the user's previous message listed four open items and #1 was "Fix `User.objects.create_user()` — add a custom `UserManager`". "Start with create test users" means "start with item #1". I am treating this as approval to *plan* (not yet execute) the UserManager fix.

## Target implementation

Add a `UserManager` class to `backend/api/models.py` just above `class User(AbstractUser)`, and set `objects = UserManager()` on User. The manager overrides `_create_user`, `create_user`, and `create_superuser` so that `username` is never passed to the model constructor.

```python
from django.contrib.auth.models import AbstractUser, BaseUserManager


class UserManager(BaseUserManager):
    """
    Manager personalizado para el modelo User que usa email como identificador
    en lugar de username. La implementación por defecto de BaseUserManager pasa
    username=... al constructor del modelo, lo cual falla en Django 6 contra un
    User que elimina ese campo. Esta clase evita ese problema aceptando email
    como primer argumento y delegando el resto a set_password + save.
    """

    use_in_migrations = True

    def _create_user(self, email, password, **extra_fields):
        if not email:
            raise ValueError("Users require an email address")
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_user(self, email, password=None, **extra_fields):
        extra_fields.setdefault("is_staff", False)
        extra_fields.setdefault("is_superuser", False)
        return self._create_user(email, password, **extra_fields)

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)
        if extra_fields.get("is_staff") is not True:
            raise ValueError("Superuser must have is_staff=True.")
        if extra_fields.get("is_superuser") is not True:
            raise ValueError("Superuser must have is_superuser=True.")
        return self._create_user(email, password, **extra_fields)


class User(AbstractUser):
    # ... existing fields unchanged ...
    objects = UserManager()
```

## Decomposition (strict TDD)

### 1. test-worker (RED)

Create `backend/tests/test_user_manager.py` with unit tests for the manager plus `backend/tests/test_auth.py` (or extend existing) with integration tests for `/api/auth/register/`.

**Unit tests for `UserManager` (test_user_manager.py):**

1. `test_create_user_creates_persisted_user` — `User.objects.create_user(email="u@test.local", password="pw", first_name="A", last_name="B", role="Estudiante")` → returns an instance whose `pk` is set and exists in DB.
2. `test_create_user_sets_password_hashed` — the returned user's `check_password("pw")` is True, and `user.password != "pw"`.
3. `test_create_user_requires_email` — calling with `email=""` or `email=None` raises `ValueError`.
4. `test_create_user_normalizes_email_domain` — pass `"User@EXAMPLE.COM"` → stored as `"User@example.com"` (Django's `normalize_email` lowercases the domain only).
5. `test_create_user_defaults_is_staff_false` — no `is_staff` passed → `user.is_staff is False`.
6. `test_create_user_defaults_is_superuser_false` — no `is_superuser` passed → `user.is_superuser is False`.
7. `test_create_user_accepts_custom_fields` — pass `role`, `status`, `cedula`, `semester`, `phone` → all persisted.
8. `test_create_superuser_sets_is_staff_and_is_superuser_true` — `create_superuser(email=..., password=...)` returns user with both flags True.
9. `test_create_superuser_raises_if_is_staff_false` — explicit `is_staff=False` → `ValueError`.
10. `test_create_superuser_raises_if_is_superuser_false` — explicit `is_superuser=False` → `ValueError`.

**Integration tests for `/api/auth/register/` (test_auth.py, new file):**

11. `test_register_endpoint_creates_user_with_valid_payload` — POST with `{email, password, full_name, role}` → 201 and `User.objects.filter(email=...).exists()`.
12. `test_register_endpoint_returns_user_data_without_password` — response contains `email`, `full_name`, NO `password` key.
13. `test_register_endpoint_splits_full_name` — POST with `full_name="John Doe"` → stored user has `first_name="John"`, `last_name="Doe"`.
14. `test_register_endpoint_sets_status_pending` — new registrants get `status='pending'` (matches current serializer behavior).
15. `test_register_endpoint_rejects_duplicate_email` — two POSTs with same email → second returns 400.

Run:
```bash
cd backend && source ../.venv/bin/activate
pytest tests/test_user_manager.py tests/test_auth.py -v
```

**Expected RED:** unit tests 1-10 fail with `TypeError: User() got unexpected keyword arguments: 'username'`. Integration tests 11-15 fail with the same error surfaced as 500 (or DRF may wrap it as 400 — accept both for the RED confirmation). Tests that check `ValueError` paths (3, 9, 10) may already pass because `BaseUserManager._create_user` does raise `ValueError` before instantiating the model — test-worker should note this and flag it.

### 2. backend-worker

Apply the UserManager to `backend/api/models.py`. Add `from django.contrib.auth.models import BaseUserManager` (already imports `AbstractUser`). Add the `UserManager` class and `objects = UserManager()` on the User class.

Then simplify `backend/conftest.py`:
- Remove `_make_user` helper.
- Revert the user fixtures to use `User.objects.create_user(email=..., password=..., first_name=..., last_name=..., role=..., status=...)` directly.
- Keep the fixture names and signatures unchanged so existing tests don't break.

Run the full suite:
```bash
pytest -v
```
Expected: all 25 existing evaluation tests pass + all 15 new user-manager tests pass = **40 passed**.

Lint:
```bash
ruff check .
```

Report to `.claude/state/20260413-003-user-manager-fix/backend-worker-result.md`.

### 3. test-worker (GREEN)

Run the full suite from orchestrator's position as independent verification. Confirm 40/40 passing. Append GREEN section to `test-worker-result.md`.

## Relevant Files

- `backend/api/models.py:5-46` — `User` model (to be modified: add `objects = UserManager()` and import)
- `backend/api/serializers.py:49-86` — `RegisterSerializer` (**not modified**, but its currently-broken `create()` path becomes working)
- `backend/api/views.py:49-54` — `AuthViewSet.register` action (calls the serializer)
- `backend/api/urls.py` — to confirm the register route (should be `POST /api/auth/register/`)
- `backend/conftest.py` — `_make_user` workaround to remove
- `backend/tests/test_user_manager.py` — to create
- `backend/tests/test_auth.py` — to create
- `backend/create_test_users.py` — **not modified**; it already uses `get_or_create`, not `create_user`. Left alone.

## Verification Criteria

- [ ] `backend/api/models.py` has a `UserManager` class and `User.objects = UserManager()`
- [ ] `backend/tests/test_user_manager.py` has 10 unit tests for the manager
- [ ] `backend/tests/test_auth.py` has 5 integration tests for `/api/auth/register/`
- [ ] `backend/conftest.py` `_make_user` workaround removed, fixtures use `create_user`
- [ ] `pytest -v` → **40 passed, 0 failed** (25 existing + 15 new)
- [ ] `ruff check backend/` → no new violations
- [ ] Production code changes limited to `backend/api/models.py` only
- [ ] `backend/api/views.py`, `serializers.py`, and `urls.py` unchanged

## Risks

- **Risk:** Django's `createsuperuser` management command expects `create_superuser(**user_data)` where `user_data` has keys from `USERNAME_FIELD` + `REQUIRED_FIELDS`. Current model has `USERNAME_FIELD='email'`, `REQUIRED_FIELDS=['first_name', 'last_name']`. The new manager accepts `email` positionally + `**extra_fields` so this should work — but we are not testing the management command directly (only the underlying `create_superuser` method). **Mitigation:** note in summary.md that a manual check of `python manage.py createsuperuser` is a good post-merge smoke test.
- **Risk:** Migrating `conftest.py` to use `create_user` might expose subtle differences if the workaround was doing something slightly different (e.g., not setting `password` at all). **Mitigation:** test-worker runs the full existing suite after the refactor; if any evaluation test fails due to auth, investigate before declaring GREEN.
- **Risk:** `test_create_user_normalizes_email_domain` depends on Django's `BaseUserManager.normalize_email` behavior, which lowercases the domain but preserves the local part. Test-worker must write the assertion accordingly (don't assume full lowercase).
- **Risk:** `RegisterSerializer` may have additional validation that makes the integration tests fail for reasons unrelated to the UserManager (e.g., password validators). **Mitigation:** test-worker reads the serializer first and uses a payload that satisfies all constraints.
- **Risk:** Adding a new manager changes `objects = UserManager()` which replaces Django's default. Some code might call `User._default_manager` or rely on manager methods we don't override. **Mitigation:** `BaseUserManager` inherits from `models.Manager`, so the full `QuerySet` API stays available. No impact on `User.objects.filter(...)` etc.

## Out of Scope

- **Do NOT** modify `RegisterSerializer`, `AuthViewSet`, or `UserViewSet`.
- **Do NOT** modify `create_test_users.py` (already works without `create_user`).
- **Do NOT** change `USERNAME_FIELD` or `REQUIRED_FIELDS`.
- **Do NOT** add email validation, password strength rules, or other registration logic.
- **Do NOT** write frontend tests.
- **Do NOT** add coverage reporting.
- **Do NOT** touch git.

## Model & Worker Allocation

- Orchestrator: Opus 4.6
- test-worker (Sonnet 4.6) — RED phase and GREEN phase
- backend-worker (Sonnet 4.6) — implement manager + clean up conftest

## Human Checkpoint

Status: `PENDING_APPROVAL`

After writing this brief, the orchestrator pauses and asks the user:
> "Plan drafted at `.claude/state/20260413-003-user-manager-fix/brief.md`. Approve to proceed, request changes, or cancel."
