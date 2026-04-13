# Summary — 20260413-003-user-manager-fix

## Final Status

**DONE — GREEN CONFIRMED** ✅

40/40 tests pass. User registration (`/api/auth/register/`) works again. `createsuperuser` path is fixed. No regressions in the 25 pre-existing tests.

```
pytest -v
======================== 40 passed in 120.91s (0:02:00) ========================
```

## What the bug actually was (correction from task 001 summary)

In the task 001 summary I wrote that `create_test_users.py` was broken. **That was wrong.** It uses `get_or_create()` + direct attribute assignment and works fine.

The real broken paths were:

1. **`RegisterSerializer.create()`** at [backend/api/serializers.py:75](backend/api/serializers.py#L75), which is the `/api/auth/register/` endpoint. **User registration was broken in production** — any POST to that endpoint would raise `TypeError: User() got unexpected keyword arguments: 'username'` because Django's inherited `UserManager._create_user_object` passes `username=None` to a User model that has removed the `username` field via `username = None`.
2. **`python manage.py createsuperuser`** management command — same root cause.
3. **Test fixtures** — `conftest.py` had to work around it with a custom `_make_user` helper.

## Files Changed

| File | Change |
|---|---|
| [backend/api/models.py](backend/api/models.py) | Added `UserManager` class (11 methods, Spanish docstring) and `objects = UserManager()` on `User` |
| [backend/api/migrations/0023_alter_user_managers.py](backend/api/migrations/0023_alter_user_managers.py) | **NEW** — Django auto-generated `AlterModelManagers` operation. State-only, zero schema change. |
| [backend/conftest.py](backend/conftest.py) | Removed `_make_user` workaround, fixtures now call `User.objects.create_user(...)` directly |
| [backend/tests/test_user_manager.py](backend/tests/test_user_manager.py) | **NEW** — 10 unit tests for `UserManager` |
| [backend/tests/test_auth.py](backend/tests/test_auth.py) | **NEW** — 5 integration tests for `/api/auth/register/` |

## The Fix

**Added to `backend/api/models.py`** (before the `User` class):

```python
class UserManager(BaseUserManager):
    """
    Manager personalizado para el modelo User que usa email como identificador...
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
```

And inside `User`:
```python
objects = UserManager()
```

## TDD Trace

1. **RED** — test-worker wrote `test_user_manager.py` (10 tests) + `test_auth.py` (5 tests). **All 15 failed** with `TypeError: UserManager.create_user() missing 1 required positional argument: 'username'`. Zero "already passing" tests — even the `ValueError` paths (email required, superuser flag checks) failed with `TypeError` first because Django's `create_user` signature demands `username` positionally.
2. **GREEN (backend-worker)** — Added `UserManager` to `models.py`, cleaned up `conftest.py`. `pytest -v` → 40 passed.
3. **GREEN (orchestrator verification)** — Re-ran `pytest -v` independently → 40 passed in 120s. Inspected the auto-generated migration to confirm it's state-only.

## Test Breakdown

### UserManager unit tests — 10/10 ✅
- `test_create_user_creates_persisted_user`
- `test_create_user_sets_password_hashed`
- `test_create_user_requires_email`
- `test_create_user_normalizes_email_domain`
- `test_create_user_defaults_is_staff_false`
- `test_create_user_defaults_is_superuser_false`
- `test_create_user_accepts_custom_fields`
- `test_create_superuser_sets_is_staff_and_is_superuser_true`
- `test_create_superuser_raises_if_is_staff_false`
- `test_create_superuser_raises_if_is_superuser_false`

### Register endpoint integration tests — 5/5 ✅
- `test_register_endpoint_creates_user_with_valid_payload`
- `test_register_endpoint_returns_user_data_without_password`
- `test_register_endpoint_splits_full_name`
- `test_register_endpoint_sets_status_pending`
- `test_register_endpoint_rejects_duplicate_email`

### Regression check — 25/25 ✅
All existing `test_evaluations.py` tests still pass. The `conftest.py` simplification did not introduce any regressions.

## Deviation from the brief: migration auto-generated

The brief predicted no migration would be needed. I was wrong.

Because the `UserManager` class sets `use_in_migrations = True`, Django tracks it in the migration graph. Running `makemigrations` produced `backend/api/migrations/0023_alter_user_managers.py` with a single `AlterModelManagers` operation. **This is not a schema change** — no tables, columns, or indexes are touched. The migration simply records the manager binding so that data migrations using `apps.get_model()` get the custom manager.

**Impact for deployments:**
- The migration must be applied via `python manage.py migrate` on any environment before deploying this change. That's already part of normal deploy flow.
- No downtime, no backfill, no DDL.

## Verification Criteria — Status

- [x] `backend/api/models.py` has `UserManager` class and `User.objects = UserManager()`
- [x] `backend/tests/test_user_manager.py` has 10 unit tests
- [x] `backend/tests/test_auth.py` has 5 integration tests
- [x] `backend/conftest.py` `_make_user` workaround removed, fixtures use `create_user`
- [x] `pytest -v` → 40 passed, 0 failed
- [x] Full suite includes auto-applied `0023_alter_user_managers.py` migration without issues
- [x] `ruff check backend/` → no new violations
- [x] `backend/api/views.py`, `serializers.py`, `urls.py` unchanged
- [x] `backend/create_test_users.py` unchanged

## Recommended Manual Smoke Checks

These are not automated but worth doing after pulling this branch:

1. **`/api/auth/register/` end-to-end:** start the dev server, POST a valid payload through Postman / curl / the frontend `RegisterForm`. Should return 201.
2. **`python manage.py createsuperuser`:** the underlying `create_superuser` method is unit-tested, but the management command has its own wrapper that prompts for `USERNAME_FIELD` + `REQUIRED_FIELDS`. Confirm it prompts for email, first_name, last_name, password, and creates a working superuser.

## Next Steps for the Human

1. **Review** the diff in `backend/api/models.py`, `backend/conftest.py`, the two new test files, and the migration.
2. **Apply the migration** locally: `python manage.py migrate` (or let the test run do it).
3. **Smoke checks** above.
4. **Commit when ready.** Suggested message:
   ```
   fix(auth): add custom UserManager, fixing registration endpoint

   - Add UserManager._create_user / create_user / create_superuser that
     do not pass `username` to the custom User model
   - Add 10 unit tests for the manager + 5 integration tests for
     POST /api/auth/register/
   - Remove the _make_user workaround from conftest.py now that the
     default create_user path works
   - Auto-generated migration 0023_alter_user_managers (state-only,
     no schema change)
   ```

## Artifacts

- Brief: `.claude/state/20260413-003-user-manager-fix/brief.md`
- test-worker result: `.claude/state/20260413-003-user-manager-fix/test-worker-result.md`
- backend-worker result: `.claude/state/20260413-003-user-manager-fix/backend-worker-result.md`
- Summary (this file): `.claude/state/20260413-003-user-manager-fix/summary.md`
