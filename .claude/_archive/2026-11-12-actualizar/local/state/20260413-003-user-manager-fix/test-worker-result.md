# Test Worker Result — 20260413-003-user-manager-fix — Phase RED

## Status
red-confirmed

## Tests Written

### File 1: backend/tests/test_user_manager.py (unit tests, lines 1-122)

1. `test_create_user_creates_persisted_user` (line 9)
   - Calls `User.objects.create_user(email=..., password=..., first_name=..., last_name=..., role=...)` and asserts pk is set and row exists in DB.

2. `test_create_user_sets_password_hashed` (line 22)
   - Asserts `check_password` returns True and stored password differs from plaintext.

3. `test_create_user_requires_email` (line 35)
   - Calls with `email=""` and expects `ValueError`.

4. `test_create_user_normalizes_email_domain` (line 40)
   - Passes `"User@EXAMPLE.COM"`, asserts stored email is `"User@example.com"` (domain lowercased, local part preserved).

5. `test_create_user_defaults_is_staff_false` (line 52)
   - Asserts `user.is_staff is False` when not passed.

6. `test_create_user_defaults_is_superuser_false` (line 63)
   - Asserts `user.is_superuser is False` when not passed.

7. `test_create_user_accepts_custom_fields` (line 74)
   - Passes `role`, `status`, `cedula`, `semester`, `phone` and asserts all are persisted.

8. `test_create_superuser_sets_is_staff_and_is_superuser_true` (line 94)
   - Calls `create_superuser(...)` and asserts both flags are True.

9. `test_create_superuser_raises_if_is_staff_false` (line 107)
   - Passes `is_staff=False` to `create_superuser` and expects `ValueError`.

10. `test_create_superuser_raises_if_is_superuser_false` (line 117)
    - Passes `is_superuser=False` to `create_superuser` and expects `ValueError`.

### File 2: backend/tests/test_auth.py (integration tests, lines 1-52)

11. `test_register_endpoint_creates_user_with_valid_payload` (line 24)
    - POST `{email, password, full_name, role}` to `/api/auth/register/` → expects 201 and user in DB.

12. `test_register_endpoint_returns_user_data_without_password` (line 31)
    - Expects response has `email` and `full_name` keys, does NOT have `password`.

13. `test_register_endpoint_splits_full_name` (line 40)
    - POST with `full_name="John Doe"` → stored user has `first_name="John"`, `last_name="Doe"`.

14. `test_register_endpoint_sets_status_pending` (line 47)
    - Asserts new user's `status == "pending"`.

15. `test_register_endpoint_rejects_duplicate_email` (line 53)
    - Two POSTs with same email → second returns 400.

## Failure Confirmation

All 15 tests FAIL. Full run:

```
$ pytest tests/test_user_manager.py tests/test_auth.py -v
...
FAILED tests/test_user_manager.py::test_create_user_creates_persisted_user
FAILED tests/test_user_manager.py::test_create_user_sets_password_hashed
FAILED tests/test_user_manager.py::test_create_user_requires_email
FAILED tests/test_user_manager.py::test_create_user_normalizes_email_domain
FAILED tests/test_user_manager.py::test_create_user_defaults_is_staff_false
FAILED tests/test_user_manager.py::test_create_user_defaults_is_superuser_false
FAILED tests/test_user_manager.py::test_create_user_accepts_custom_fields
FAILED tests/test_user_manager.py::test_create_superuser_sets_is_staff_and_is_superuser_true
FAILED tests/test_user_manager.py::test_create_superuser_raises_if_is_staff_false
FAILED tests/test_user_manager.py::test_create_superuser_raises_if_is_superuser_false
FAILED tests/test_auth.py::test_register_endpoint_creates_user_with_valid_payload
FAILED tests/test_auth.py::test_register_endpoint_returns_user_data_without_password
FAILED tests/test_auth.py::test_register_endpoint_splits_full_name
FAILED tests/test_auth.py::test_register_endpoint_sets_status_pending
FAILED tests/test_auth.py::test_register_endpoint_rejects_duplicate_email
15 failed in 3.22s
```

## Reason for Failure (per test)

**Tests 1-10 (unit tests — all 10 fail with the same root cause):**

- Error: `TypeError: UserManager.create_user() missing 1 required positional argument: 'username'`
- This is the expected failure — Django's default `UserManager` inherited by `AbstractUser` requires `username` as the first positional argument. The `User` model sets `username = None`, but no custom manager overrides the signature. The fix (adding a custom `UserManager`) doesn't exist yet.
- This is the correct RED failure for tests 1-2, 4-8.

**Tests 3, 9, 10 special note:**
- `test_create_user_requires_email` was expected to possibly already pass (brief noted `ValueError` might be raised before the `TypeError`). In practice it FAILS with `TypeError` — the `username` argument check fires before the empty-email check in `BaseUserManager._create_user`. So this test is correctly RED.
- `test_create_superuser_raises_if_is_staff_false` and `test_create_superuser_raises_if_is_superuser_false` were similarly expected to possibly already pass. In practice both FAIL with `TypeError: UserManager.create_superuser() missing 1 required positional argument: 'username'`. The `username` positional check fires first. All three are correctly RED.

**Tests 11-15 (integration tests — all 5 fail):**

- Tests 11-14: The `TypeError` propagates from `serializers.py:75` → `create_user(...)` through the DRF view without being caught, raising a 500. Django's test client re-raises it, so the test sees `TypeError: UserManager.create_user() missing 1 required positional argument: 'username'` instead of a status code assertion failure.
- Test 15 (duplicate email): Same — first POST fails with 500/TypeError before the duplicate check can ever be reached.
- All fail for the right reason: the custom UserManager doesn't exist yet.

## No "Already Passing" Tests

Contrary to the brief's prediction that tests 3, 9, 10 might already pass, all 15 fail. The `TypeError` for the missing `username` argument fires before any `ValueError` path is reached. This is correct RED behavior.

## Existing Suite Verification

```
$ pytest tests/test_evaluations.py -v
25 passed in 97.18s
```
No regressions. The two new test files do not affect the existing suite.

## Next Step

Orchestrator should spawn backend-worker to implement the custom `UserManager` in `backend/api/models.py` and clean up `backend/conftest.py` as described in the brief's Decomposition section 2.
