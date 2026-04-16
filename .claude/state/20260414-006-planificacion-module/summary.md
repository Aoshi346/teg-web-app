# Task 006 — Planificación module — Summary

## Status
**DONE — fully green on both stacks.**

## What changed

Replaced the vestigial `Escanear` module with a new **Planificación** module
for admin-managed thesis/project presentation scheduling. All four roles see
it; only Administradores can edit.

### Backend

- New models `PresentationDay` and `Presentation` ([backend/api/models.py](backend/api/models.py))
  - `Presentation` carries `start_time` (TimeField, HH:MM round-trip), `duration_minutes` (default 30), `tutor` (FK), `jurado` (M2M), `UniqueConstraint(day, project)`.
- Migration [backend/api/migrations/0024_planificacion.py](backend/api/migrations/0024_planificacion.py)
- `PresentationSerializer` + `PresentationDaySerializer` ([backend/api/serializers.py](backend/api/serializers.py))
  - `start_time` uses `format="%H:%M", input_formats=["%H:%M"]`
  - `validate_jurado` enforces `role == 'Jurado'` (since `limit_choices_to` doesn't produce 400s)
- `PresentationDayViewSet` + `PresentationViewSet` ([backend/api/views.py](backend/api/views.py))
  - `IsAdminUserRole` for write, `IsAuthenticated` for read (mirrors `SemesterViewSet`)
  - `@action bulk` is idempotent via `get_or_create`
  - `@action presentations` for nested admin-only create
- Routes registered at [backend/api/urls.py](backend/api/urls.py): `/api/planificacion/days/` and `/api/planificacion/presentations/`

### Frontend

**Deleted:** entire `frontend/src/app/dashboard/scan/` directory (vestigial Escanear).

**New feature folder** [frontend/src/features/planificacion/](frontend/src/features/planificacion/) (15 files):

```
api/planificacionService.ts                # 7 service functions
types/planificacion.ts                     # TS interfaces
hooks/usePlanificacion.ts                  # fetch + cache
hooks/useDateSelection.ts                  # range/individual state
lib/formatDate.ts                          # Spanish locale formatters
components/
  PlanificacionView.tsx                    # orchestrator
  PlanificacionHeader.tsx                  # gradient header + mode toggle
  WeekCalendar.tsx                         # hand-built month grid, no new deps
  DayCard.tsx                              # 88px Fraunces day numeral, project-type left border
  PresentationCard.tsx                     # time pill + admin row affordances
  PresentationFormModal.tsx                # admin add/edit
  EmptyDayState.tsx                        # zero-data state
  icons/AgendaIllustration.tsx             # inline 2-tone SVG
index.ts                                   # public barrel
```

**New route files:**
- [frontend/src/app/dashboard/planificacion/page.tsx](frontend/src/app/dashboard/planificacion/page.tsx)
- [frontend/src/app/dashboard/planificacion/loading.tsx](frontend/src/app/dashboard/planificacion/loading.tsx)
- [frontend/src/app/dashboard/planificacion/fonts.ts](frontend/src/app/dashboard/planificacion/fonts.ts) (Fraunces via `next/font`, scoped to this route via `--font-display`)

**Sidebar swap:** [frontend/src/widgets/sidebar/Sidebar.tsx](frontend/src/widgets/sidebar/Sidebar.tsx) — removed `ScanLine` import + Escanear entry, added `CalendarDays` + Planificación entry visible to all 4 roles.

### Visual direction

Followed the "Editorial Almanac" design spec — gradient navy→blue header with grain overlay, warm `#fbfaf6` page background, **Fraunces variable serif** (scoped via `next/font` only inside `/dashboard/planificacion`) for the day numerals + headings, Geist Mono for time pills, project-type-keyed left borders (blue=proyecto, orange=tesis), Tailwind motion for stagger fade and toggle slides — **no new motion library**, **no new dependencies** beyond Fraunces.

## Verification

| Check | Result |
|---|---|
| `pytest tests/test_planificacion.py -v` | **10/10 passed** (Phase 2) |
| `pytest -q` (full backend suite) | **54/54 passed** — zero regressions |
| `vitest run tests/structure/planificacion-layout.test.ts` | **4/4 passed** |
| `vitest run tests/features/planificacion-roles.test.tsx` | **5/5 passed** |
| `vitest run` (full frontend suite) | **20/20 passed** |
| `npx tsc --noEmit` | 3 pre-existing errors in `tests/lib/api-timing.test.ts` only — **zero new errors** |
| `npm run lint` | 0 errors, baseline warnings |
| `npm run build` | **SUCCESS**, `/dashboard/planificacion` prerendered as static (7.3 kB / 141 kB first-load) |

## Workflow

| Phase | Worker | Outcome |
|---|---|---|
| Phase 0 — Visual spec | orchestrator + `frontend-design` skill | `design-spec.md` written, human-approved |
| Phase 1 — RED backend | test-worker | 10 failing tests in `backend/tests/test_planificacion.py` |
| Phase 2 — IMPL backend | backend-worker | models + migration + serializers + viewset + urls; 10/10 GREEN |
| Phase 3 — RED frontend | test-worker | 9 failing tests across 2 vitest files |
| Phase 4 — IMPL frontend | frontend-worker | 15-file feature folder + sidebar swap + scan/ deleted; all GREEN |
| Phase 5 — Verification | orchestrator | full suites green; 2 stale-test fixes applied inline |

## Inline fixes by orchestrator (Phase 5)

Two trivial test-file fixes I made directly rather than spawning test-worker for one-line changes:

1. **`frontend/tests/structure/fsd-layout.test.ts`** — removed assertion that `features/auth/api/credentials.ts` exists. That file was deleted as dead code in task 005 and the assertion was never updated. Pre-existing stale assertion, not related to this task.

2. **`frontend/tests/features/planificacion-roles.test.tsx`** — replaced `vi.fn<[], string>()` (old vitest type-arg syntax) with `vi.fn<() => string>()` (current syntax). The test-worker wrote it with the older syntax; both new tsc errors traced to that one line.

Frontend-worker flagged both in its result file but couldn't fix them because test files are off-limits to it. The orchestrator handled them as cleanup since neither edit changes test logic.

## Notes for human follow-up

1. **Notification emails / .ics export** — not built. Mentioned as out-of-scope in the brief; flag for a follow-up task if you want it.
2. **Conflict detection** — overlapping HH:MM slots within a day are NOT validated. Only `(day, project)` uniqueness is enforced. Add as a follow-up if needed.
3. **Room / location field** — not modeled. Phase 2 if requested.
4. **Drag-to-reorder presentations** — not built. The `order` field exists on the model but the UI uses chronological `start_time` ordering for now.
5. **Print stylesheet** — the editorial visual direction would shine on paper. Possible nice follow-up.
6. **Manual smoke check** — frontend-worker reported the build succeeds and the route renders; I did not personally `./start.sh` and click through. If you want a verified end-to-end manual pass, run `./start.sh`, log in as `admin@example.com / 123`, navigate to `/dashboard/planificacion`, create a date range, and add a presentation. Then log in as `student@example.com / 123` and verify it renders read-only.
7. **3 pre-existing tsc errors** in `tests/lib/api-timing.test.ts` (carry-over from task 004) — still trivial to fix (`as string` cast), still out of scope.

## Git status

All changes are unstaged. Commit when ready. Suggested split:
1. **Backend** — models + migration + serializers + viewset + urls + tests
2. **Frontend** — feature folder + route files + sidebar swap + scan/ deletion + 2 stale-test fixes
3. (Optional) **Task state** — `.claude/state/20260414-006-planificacion-module/`

Or one bundled commit since these layers are coupled. Your call.
