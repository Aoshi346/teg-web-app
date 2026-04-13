# Test Worker Result — 20260413-004-performance-top3-fixes — Phase RED (Phase 0 Instrumentation)

## Status
red-confirmed

---

## Tests Written

### Backend — `backend/tests/test_perf_middleware.py`

1. `test_api_response_includes_query_count_header`  
   File: `backend/tests/test_perf_middleware.py:18-29`  
   Expects: GET `/api/csrf/` response contains `X-Query-Count` header with a parseable integer value.

2. `test_api_response_includes_response_time_header`  
   File: `backend/tests/test_perf_middleware.py:33-44`  
   Expects: GET `/api/csrf/` response contains `X-Response-Time-Ms` header with a parseable positive float/int value.

3. `test_query_count_increases_with_db_hits`  
   File: `backend/tests/test_perf_middleware.py:48-67`  
   Expects: Authenticated GET `/api/evaluations/` returns `X-Query-Count` > 0, proving the middleware actually counts real DB queries.

4. `test_non_api_paths_do_not_get_headers`  
   File: `backend/tests/test_perf_middleware.py:70-86`  
   Expects: GET `/admin/login/` does NOT contain either perf header (scope guard).

### Frontend — `frontend/tests/lib/api-timing.test.ts`

1. `logs duration after successful GET`  
   File: `frontend/tests/lib/api-timing.test.ts:40-51`  
   Expects: `console.info` called after `api.get()` with a message matching method + path + duration number.

2. `logs duration after POST`  
   File: `frontend/tests/lib/api-timing.test.ts:53-65`  
   Expects: `console.info` called after `api.post()` with a message matching POST + path + duration number.

3. `logs duration after a failing request`  
   File: `frontend/tests/lib/api-timing.test.ts:67-83`  
   Expects: `console.info` still fires even when fetch returns 500, and the message includes the status code.

4. `does not log in production`  
   File: `frontend/tests/lib/api-timing.test.ts:85-96`  
   Expects: When `NODE_ENV=production`, `console.info` is NOT called.

---

## Failure Confirmation

### Backend output (trimmed)

```
$ pytest tests/test_perf_middleware.py -v

FAILED tests/test_perf_middleware.py::test_api_response_includes_query_count_header
  AssertionError: Expected X-Query-Count header but it was absent —
  PerfHeadersMiddleware not installed or not active
  assert 'X-Query-Count' in <Response status_code=200, "application/json">

FAILED tests/test_perf_middleware.py::test_api_response_includes_response_time_header
  AssertionError: Expected X-Response-Time-Ms header but it was absent —
  PerfHeadersMiddleware not installed or not active
  assert 'X-Response-Time-Ms' in <Response status_code=200, "application/json">

FAILED tests/test_perf_middleware.py::test_query_count_increases_with_db_hits
  AssertionError: Expected X-Query-Count header on authenticated endpoint —
  PerfHeadersMiddleware not installed or not active
  assert 'X-Query-Count' in <Response status_code=200, "application/json">

PASSED tests/test_perf_middleware.py::test_non_api_paths_do_not_get_headers

3 failed, 1 passed in 6.76s
```

### Frontend output (trimmed)

```
$ npx vitest run tests/lib/api-timing.test.ts --reporter=verbose

× api timing instrumentation > logs duration after successful GET
  → expected "info" to be called at least once
  AssertionError at tests/lib/api-timing.test.ts:48

× api timing instrumentation > logs duration after POST
  → expected "info" to be called at least once
  AssertionError at tests/lib/api-timing.test.ts:62

× api timing instrumentation > logs duration after a failing request
  → expected "info" to be called at least once
  AssertionError at tests/lib/api-timing.test.ts:80

✓ api timing instrumentation > does not log in production

Test Files  1 failed (1)
Tests  3 failed | 1 passed (4)
```

---

## Reason for Failure Analysis

### Backend tests 1-3
- Failing because the `PerfHeadersMiddleware` does not exist yet. The headers `X-Query-Count` and `X-Response-Time-Ms` are simply absent from every response. The assertion error messages are precise and describe the missing middleware.
- All three failures are **the expected reason**: header absent, not import error, not syntax error, not fixture failure.

### Backend test 4 (`test_non_api_paths_do_not_get_headers`)
- Passes trivially today because no middleware adds these headers anywhere. This is **expected and documented in the test docstring**. Its purpose is as a regression guard: once the middleware exists, it must not leak headers to non-`/api/` routes.

### Frontend tests 1-3
- Failing because `api.ts` never calls `console.info`. The assertion `expect(infoSpy).toHaveBeenCalled()` fails with "expected 'info' to be called at least once".
- All three failures are **the expected reason**: `console.info` not called, not import error, not type error.

### Frontend test 4 (`does not log in production`)
- Passes trivially today because `console.info` is never called in any environment. Same situation as backend test 4 — regression guard.

---

## Infrastructure Fix Applied

The vitest run was blocked by a pre-existing PostCSS incompatibility: `postcss.config.mjs` references `"@tailwindcss/postcss"` as a string plugin, which Vite 5 cannot resolve during config initialization even when `css: false` is set in the test config. This is a pre-existing issue that blocks ALL frontend tests from running.

Fix applied: added `css: { postcss: { plugins: [] } }` override to `frontend/vitest.config.ts` to prevent vite from loading the external PostCSS config file during vitest initialization. This does not affect the frontend build or Next.js dev server (those use `postcss.config.mjs` directly). No test logic was changed.

---

## Regression Check

### Backend existing suite
```
pytest tests/test_evaluations.py tests/test_user_manager.py tests/test_auth.py -v
40 passed in 132.79s
```
All 40 existing tests pass. No regressions.

### Frontend existing suite
The only frontend test file that matches the vitest include patterns is the new `tests/lib/api-timing.test.ts`. No other `.test.ts(x)` files exist under `src/` or `tests/`. The new file is the only test found; 3 RED, 1 trivially passing.

---

## Next Step

Orchestrator should spawn **backend-worker** to implement:
1. `backend/core/middleware.py` — `PerfHeadersMiddleware` class that:
   - Scopes to `request.path.startswith('/api/')`
   - Counts SQL queries via `django.test.utils.CaptureQueriesContext` or `django.db.connection.queries` (DEBUG=True only)
   - Measures wall-clock time with `time.perf_counter()`
   - Sets `X-Query-Count` and `X-Response-Time-Ms` on the response
   - Is a no-op when `settings.DEBUG` is False
2. Register it in `core/settings.py` MIDDLEWARE list (after `AuthenticationMiddleware`, before `MessageMiddleware`)

And spawn **frontend-worker** to implement the timing wrapper in `frontend/src/lib/api.ts`:
- Wrap the `request()` function body with `performance.now()` before and after `fetch`
- After `fetch` resolves (or rejects), call `console.info(\`[api] METHOD endpoint → Nms (status)\`)` gated on `process.env.NODE_ENV !== 'production'`

## Blockers
None.
