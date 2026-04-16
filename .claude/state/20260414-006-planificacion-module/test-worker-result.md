# Test Worker Result — 20260414-006 — Phase 1 (RED, backend)

## Status
red-confirmed

## Files Changed
- `backend/tests/test_planificacion.py` — new (10 tests)
- `backend/conftest.py` — not modified (existing fixtures were sufficient)

## Tests Written

- `test_admin_can_create_presentation_day` — FAILED: POST `/api/planificacion/days/` returns 404 because the URL is not registered yet (expected 201)
- `test_non_admin_cannot_create_day` — FAILED: same 404, expected 403
- `test_any_authenticated_user_can_list_days` — FAILED: GET `/api/planificacion/days/` returns 404 for all roles, expected 200
- `test_unauthenticated_user_cannot_list_days` — FAILED: GET returns 404, expected 401/403
- `test_bulk_create_days_from_date_list` — FAILED: POST `/api/planificacion/days/bulk/` returns 404, expected 200/201
- `test_unique_project_per_day_constraint` — ERROR at setup: `a_day` fixture posts to the non-existent URL; `HttpResponseNotFound` has no `.data` attribute. Root cause is the same missing endpoint — will become a proper FAILED once the endpoint exists.
- `test_cascade_delete_removes_presentations` — FAILED: POST to create a day returns 404, setup assert fires (expected 201)
- `test_presentation_requires_start_time_and_round_trips_hh_mm` — ERROR at setup (same `a_day` fixture issue as above)
- `test_jurado_m2m_rejects_non_jurado_users` — ERROR at setup (same)
- `test_admin_can_update_and_delete_presentation` — ERROR at setup (same)

All 10 failures / errors trace back to the same root cause: `/api/planificacion/days/` and its sub-routes do not exist.

## Pytest Output

```
============================= test session starts ==============================
platform linux -- Python 3.12.3, pytest-8.3.3, pluggy-1.6.0
django: version: 6.0.1, settings: core.settings (from ini)
collected 10 items

tests/test_planificacion.py::test_admin_can_create_presentation_day FAILED [ 10%]
tests/test_planificacion.py::test_non_admin_cannot_create_day FAILED     [ 20%]
tests/test_planificacion.py::test_any_authenticated_user_can_list_days FAILED [ 30%]
tests/test_planificacion.py::test_unauthenticated_user_cannot_list_days FAILED [ 40%]
tests/test_planificacion.py::test_bulk_create_days_from_date_list FAILED [ 50%]
tests/test_planificacion.py::test_unique_project_per_day_constraint ERROR [ 60%]
tests/test_planificacion.py::test_cascade_delete_removes_presentations FAILED [ 70%]
tests/test_planificacion.py::test_presentation_requires_start_time_and_round_trips_hh_mm ERROR [ 80%]
tests/test_planificacion.py::test_jurado_m2m_rejects_non_jurado_users ERROR [ 90%]
tests/test_planificacion.py::test_admin_can_update_and_delete_presentation ERROR [100%]

==================================== ERRORS ====================================
___________ ERROR at setup of test_unique_project_per_day_constraint ___________
tests/test_planificacion.py:91: in a_day
    assert resp.status_code == 201, f"Setup failed: {resp.data}"
E   AttributeError: 'HttpResponseNotFound' object has no attribute 'data'
Not Found: /api/planificacion/days/

=================================== FAILURES ===================================
____________________ test_admin_can_create_presentation_day ____________________
tests/test_planificacion.py:118: in test_admin_can_create_presentation_day
    assert response.status_code == 201
E   assert 404 == 201

_______________________ test_non_admin_cannot_create_day _______________________
tests/test_planificacion.py:138: in test_non_admin_cannot_create_day
    assert resp.status_code == 403, f"{label} expected 403, got {resp.status_code}"
E   AssertionError: Estudiante expected 403, got 404

__________________ test_unauthenticated_user_cannot_list_days __________________
tests/test_planificacion.py:168: in test_unauthenticated_user_cannot_list_days
    assert response.status_code in (401, 403)
E   assert 404 in (401, 403)

_____________________ test_bulk_create_days_from_date_list _____________________
tests/test_planificacion.py:184: in test_bulk_create_days_from_date_list
    assert response.status_code in (200, 201)
E   assert 404 in (200, 201)
Not Found: /api/planificacion/days/bulk/

=========================== short test summary info ============================
ERROR tests/test_planificacion.py::test_unique_project_per_day_constraint
ERROR tests/test_planificacion.py::test_presentation_requires_start_time_and_round_trips_hh_mm
ERROR tests/test_planificacion.py::test_jurado_m2m_rejects_non_jurado_users
ERROR tests/test_planificacion.py::test_admin_can_update_and_delete_presentation
FAILED tests/test_planificacion.py::test_admin_can_create_presentation_day
FAILED tests/test_planificacion.py::test_non_admin_cannot_create_day
FAILED tests/test_planificacion.py::test_any_authenticated_user_can_list_days
FAILED tests/test_planificacion.py::test_unauthenticated_user_cannot_list_days
FAILED tests/test_planificacion.py::test_bulk_create_days_from_date_list
FAILED tests/test_planificacion.py::test_cascade_delete_removes_presentations
========================= 6 failed, 4 errors in 30.52s =========================
```

## Notes for Backend Worker

1. **URL registration:** Register the router prefix as `planificacion/days` and `planificacion/presentations`. The tests hit `/api/planificacion/days/`, `/api/planificacion/days/bulk/`, `/api/planificacion/days/{id}/presentations/`, and `/api/planificacion/presentations/{id}/`.

2. **Bulk endpoint shape:** Tests POST `{dates: ["YYYY-MM-DD", ...], semester: <id>}` to `/api/planificacion/days/bulk/`. Response must be a list of all created/retrieved day objects (idempotent via `get_or_create`). Accept both 200 and 201 as success codes.

3. **Nested presentations URL:** Tests use `/api/planificacion/days/{id}/presentations/` (nested under a day) for POST, but `/api/planificacion/presentations/{id}/` (flat) for PATCH and DELETE. Use a `@action` on `PresentationDayViewSet` for the nested POST, and a separate `PresentationViewSet` for PATCH/DELETE.

4. **Jurado validation:** The serializer for `Presentation` must validate that every user ID in the `jurado` list has `role == 'Jurado'` and return 400 with a role-related error message if not. The `limit_choices_to` on the M2M field alone is not enough — add a `validate_jurado` method on the serializer.

5. **start_time serialization:** Django's `TimeField` serializes to `HH:MM:SS` by default. The tests assert `"14:30"` (no seconds). Use `serializers.TimeField(format="%H:%M", input_formats=["%H:%M"])` to strip seconds.

6. **Permission class:** Mirror `SemesterViewSet`'s pattern — `get_permissions()` returns `[IsAuthenticated(), IsAdminUserRole()]` for create/update/destroy/bulk/add_presentation actions, and `[IsAuthenticated()]` for list/retrieve. The `IsAdminUserRole` class already exists in `views.py`.

7. **The 4 ERROR tests** (unique constraint, start_time round-trip, jurado M2M, admin update/delete) all fail at the `a_day` fixture setup because that fixture calls the non-existent endpoint. They will automatically transition from ERROR to FAILED (then PASSED) once the day creation endpoint exists. No changes to the test file are needed.

## Blockers
None.

---

## Phase 3 (RED, frontend) — 2026-04-13

### Status
red-confirmed

### Files Changed
- `frontend/tests/structure/planificacion-layout.test.ts` — new (4 tests)
- `frontend/tests/features/planificacion-roles.test.tsx` — new (5 tests)

### Tests Written

**planificacion-layout.test.ts (structure smoke):**
- `route files exist` — FAILED: `planificacion/page.tsx` does not exist yet
- `scan route is removed` — FAILED: `app/dashboard/scan/` still exists
- `feature files exist` — FAILED: first missing file is `features/planificacion/index.ts`
- `sidebar contains planificacion href and not scan href` — FAILED: sidebar has no `/dashboard/planificacion` string

**planificacion-roles.test.tsx (RTL role contract):**
- entire suite fails at module resolution: `Failed to resolve import "@features/planificacion/components/PlanificacionView"` — the file does not exist yet (correct RED state)
- Once the file exists, the 5 tests inside will assert:
  - `renders read-only for Estudiante` — no admin buttons visible
  - `renders read-only for Tutor` — same
  - `renders read-only for Jurado` — same
  - `renders admin controls for Administrador` — agregar/crear/editar/eliminar buttons present
  - `shows time pill in HH:MM` — `screen.findByText("14:30")` visible

### Vitest Output
```
 FAIL  tests/features/planificacion-roles.test.tsx
Error: Failed to resolve import "@features/planificacion/components/PlanificacionView"
  from "tests/features/planificacion-roles.test.tsx". Does the file exist?

 FAIL  tests/structure/planificacion-layout.test.ts (4 failed)
  × route files exist — planificacion/page.tsx: expected false to be true
  × scan route is removed — scan/ directory should be gone: expected true to be false
  × feature files exist — features/planificacion/index.ts: expected false to be true
  × sidebar contains planificacion href and not scan href — expected content to contain '/dashboard/planificacion'

 Test Files  2 failed (2)
      Tests  4 failed (4)
   Duration  3.05s
```

### Notes for Frontend Worker

- **aria-label convention (REQUIRED):** The admin edit/delete affordances on `PresentationCard` MUST be rendered as `<button aria-label="Editar presentación">` and `<button aria-label="Eliminar presentación">` (or any text matching `/editar/i` and `/eliminar/i`). RTL finds them via `getByRole("button", { name: /editar/i })`. Do NOT use icon-only buttons without `aria-label`.

- **"Agregar presentación" button:** Must be a `<button>` whose accessible name matches `/agregar presentación/i` (case-insensitive). Rendered at the bottom of each `DayCard`, admin-only.

- **"Crear días" CTA:** Must be a `<button>` whose accessible name matches `/crear .* días/i`. Rendered below the `WeekCalendar`, admin-only.

- **`listDays()` service signature expected by tests:** `listDays(): Promise<PresentationDay[]>` where `PresentationDay` has `{ id, date, notes, presentations: Presentation[] }`. Export from `@features/planificacion/api/planificacionService`.

- **Time pill contract:** `PresentationCard` must render `start_time` as plain text `"HH:MM"` (e.g. `"14:30"`) findable by `screen.findByText("14:30")`. Wrap in `<time dateTime="HH:MM">` per the accessibility spec.

- **Role gating:** `PlanificacionView` must call `getUserRole()` from `@features/auth/api/clientAuth` and gate admin-only controls. Non-admin roles must receive NO edit/delete/agregar/crear buttons — not even disabled ones (per the design spec accessibility note).

- **Fixture shape for mock:** See the `mockDays` constant in `planificacion-roles.test.tsx` lines 17-37 — this is the exact object shape `listDays()` must return from the real service.

### Blockers
None.
