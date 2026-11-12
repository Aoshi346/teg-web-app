# Task 006 — Planificación module (replaces Escanear)

## Goal

Replace the unused `Escanear` (`/dashboard/scan`) module with a new
**Planificación** module that lets administrators plan a week of TEG/PTEG
presentations and lets every user view that schedule read-only.

Requirements straight from the user request:

- **Remove** the `Escanear` route, sidebar entry, layout, and any ancillary scan code.
- **Add** a Planificación route at `/dashboard/planificacion`.
- **Admin-only edit.** All other roles (Estudiante / Tutor / Jurado) get a read-only view.
- **Date selection UX:** intuitive picker supporting both *range mode*
  (e.g. "April 21 – April 25") and *individual dates* (multi-select of
  arbitrary days).
- **Each scheduled day stores a list of presentations.** Per presentation we
  capture: the Project (which carries student + project_type tesis|proyecto +
  advisors), the Tutor (denormalized from the project so admins can override),
  one or more Jurado (jury) members, and a **start time (HH:MM)** so the
  admin can lay out a day's agenda.
- **Visual design:** keep the existing Tesisfar visual language (Tailwind,
  Navy/Blue/Orange/Yellow palette, Inter font, soft shadows, rounded cards)
  but step it up — modern, sleek, colorful. Use the `frontend-design` skill
  before coding the UI.

## Out of scope

- Notification emails / calendar sync (.ics export). Flag for a follow-up task if asked.
- Conflict detection across rooms/jurors (simple uniqueness only — same student can't be scheduled twice on the same day; we do NOT block overlapping HH:MM slots in v1).
- Room / location assignment (Phase 2 if requested).
- Modifying any unrelated module.

## Affected surface (current state)

### Backend (`backend/api/`)

- `models.py` — add `PresentationDay` and `Presentation` models. No model needs to be deleted; the scan module never had a backend.
- `serializers.py` — add `PresentationDaySerializer`, `PresentationSerializer`.
- `views.py` — add `PresentationDayViewSet` with admin-only write permission and authenticated read.
- `urls.py` — register `/api/planificacion/days/` route.
- New migration `0024_planificacion.py`.
- Tests in `backend/tests/test_planificacion.py` (RED first).

### Frontend (`frontend/src/`)

**Delete:**
- `app/dashboard/scan/layout.tsx`
- `app/dashboard/scan/loading.tsx`
- (entire `app/dashboard/scan/` directory)
- The "Escanear" sidebar entry in `widgets/sidebar/Sidebar.tsx:127`.
- The `ScanLine` icon import if it's now unused.

**Add:**
- `app/dashboard/planificacion/page.tsx` — thin route, `"use client"`, renders the feature component.
- `app/dashboard/planificacion/loading.tsx` — skeleton matching the new design.
- `features/planificacion/api/planificacionService.ts` — list/create/update/delete day, add/remove presentation.
- `features/planificacion/components/PlanificacionView.tsx` — top-level orchestrator.
- `features/planificacion/components/WeekCalendar.tsx` — day picker (range + multi-select toggle).
- `features/planificacion/components/PresentationCard.tsx` — one presentation row inside a day.
- `features/planificacion/components/PresentationFormModal.tsx` — admin add/edit modal (project autocomplete, tutor display, jurado multi-select).
- `features/planificacion/components/EmptyDayState.tsx`
- `features/planificacion/hooks/usePlanificacion.ts` — fetch + cache.
- `features/planificacion/types/planificacion.ts` — TS interfaces.
- `features/planificacion/index.ts` — barrel.
- New sidebar entry: `{ icon: CalendarDays, label: "Planificación", href: "/dashboard/planificacion" }` for **all roles**.

## Data model (proposed)

```python
class PresentationDay(models.Model):
    """A planned day of presentations (admin-managed)."""
    date = models.DateField(unique=True)
    semester = models.ForeignKey(Semester, on_delete=models.CASCADE,
                                  related_name='presentation_days')
    notes = models.CharField(max_length=255, blank=True, default='')
    created_at = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True,
                                    related_name='created_presentation_days')

    class Meta:
        ordering = ['date']

class Presentation(models.Model):
    """A single thesis/project presentation slot inside a day."""
    day = models.ForeignKey(PresentationDay, on_delete=models.CASCADE,
                            related_name='presentations')
    project = models.ForeignKey(Project, on_delete=models.CASCADE,
                                related_name='presentations')
    # Snapshot/override at scheduling time. Default = first advisor on the project.
    tutor = models.ForeignKey(User, on_delete=models.SET_NULL, null=True,
                              related_name='tutored_presentations',
                              limit_choices_to={'role': 'Tutor'})
    jurado = models.ManyToManyField(User, related_name='juried_presentations',
                                     limit_choices_to={'role': 'Jurado'})
    start_time = models.TimeField(help_text="Hora de inicio HH:MM")
    duration_minutes = models.PositiveSmallIntegerField(default=30,
                                                          help_text="Duración estimada en minutos")
    order = models.PositiveSmallIntegerField(default=0)

    class Meta:
        ordering = ['day__date', 'start_time', 'order']
        constraints = [
            models.UniqueConstraint(fields=['day', 'project'],
                                    name='unique_project_per_day'),
        ]
```

`student` is reachable via `project.student`; we don't denormalize. The
serializer flattens `student_name`, `student_email`, `project_title`,
`project_type` for the frontend.

## API contract (proposed)

| Method | Path                                              | Who    | Returns                                    |
|--------|---------------------------------------------------|--------|--------------------------------------------|
| GET    | `/api/planificacion/days/`                         | any    | `[{id, date, notes, presentations: [...]}]` |
| GET    | `/api/planificacion/days/?from=YYYY-MM-DD&to=...` | any    | filtered list                              |
| POST   | `/api/planificacion/days/`                         | admin  | create day (`{date, notes?}`)              |
| POST   | `/api/planificacion/days/bulk/`                    | admin  | bulk-create days from a date list/range    |
| PATCH  | `/api/planificacion/days/{id}/`                    | admin  | update day                                 |
| DELETE | `/api/planificacion/days/{id}/`                    | admin  | delete day (cascade-deletes presentations) |
| POST   | `/api/planificacion/days/{id}/presentations/`      | admin  | add presentation `{project, tutor?, jurado: []}` |
| PATCH  | `/api/planificacion/presentations/{id}/`           | admin  | update presentation                        |
| DELETE | `/api/planificacion/presentations/{id}/`           | admin  | remove presentation                        |

Permission: `IsAuthenticated` for read; admin-only (`request.user.role == 'Administrador'`) for any write. Mirror the pattern already used in `SemesterViewSet`.

## Frontend UX (high level — refined by frontend-design skill)

- **Header strip** with semester selector (defaults to active semester) and a "Modo selección" toggle: `Rango` ⇄ `Individual`.
- **Calendar grid** (one month at a time, navigable). In Rango mode: click start, click end, fill highlights. In Individual mode: click toggles each day. Selected days that don't yet exist as `PresentationDay` are visually distinct from existing planned days.
- **"Crear / actualizar días" button** (admin only) commits the selection via `POST /days/bulk/`.
- **Day cards** stack below the calendar showing each `PresentationDay` with its presentations; admin sees "+ agregar presentación" / edit / delete affordances; students/tutors/jurados see the same data but read-only.
- **Presentation modal** uses the existing `Combobox` for project search (filtered to active semester), auto-populates the tutor from `project.advisors[0]` (overridable), lets the admin pick 1–N jurados via a multi-select, and asks for **start time (HH:MM)** + duration (minutes, default 30).
- **Day cards render presentations in chronological order** by `start_time`, each row showing the time pill on the left and the project/tutor/jurado info on the right.
- **Visual upgrades over the existing dashboard look:**
  - Gradient header bar (Navy → Blue) with subtle noise/grain texture.
  - Day cards with colored left border keyed by project_type (proyecto = Blue, tesis = Orange).
  - Soft entrance animations (Framer Motion or CSS keyframes — match what the rest of the app uses; do NOT introduce a new animation lib).
  - Empty state with friendly illustration + CTA.
  - Use the `frontend-design` skill to specify exact spacing/typography/color tokens before implementation.

## Decomposition

### Phase 0 — UX spec (orchestrator) — **HUMAN CHECKPOINT**
1. Invoke the `frontend-design` skill to nail down the visual spec for the calendar, day cards, time-row, and modal. Save as `.claude/state/20260414-006-planificacion-module/design-spec.md`.
2. **STOP and present the spec to the user.** Do not advance to Phase 1 until the user explicitly approves the design spec (or requests revisions and approves a revised version).

### Phase 1 — RED (test-worker, backend)
1. Write failing pytest cases in `backend/tests/test_planificacion.py`:
   - admin can create a `PresentationDay`
   - non-admin (Tutor/Estudiante/Jurado) gets 403 on POST/PATCH/DELETE
   - any authenticated user can GET
   - bulk endpoint creates N days from a date list
   - duplicate `(day, project)` constraint enforced
   - cascade delete removes presentations
   - presentation requires `start_time`; serializer accepts and returns `HH:MM`
   - jurado M2M accepts a list of user ids whose role == 'Jurado'; rejects others
2. Run pytest, confirm RED.

### Phase 2 — IMPL backend (backend-worker)
1. Add models, migration `0024_planificacion.py`.
2. Add serializers + viewset + URL route.
3. Reuse existing `IsAuthenticated` and add a small `IsAdminOrReadOnly` permission class (or inline check).
4. Run pytest until GREEN.

### Phase 3 — RED (test-worker, frontend)
1. Add `frontend/tests/features/planificacion.test.tsx` (vitest + RTL):
   - read-only role hides admin controls
   - admin role shows "+ agregar día" and edit/delete buttons
   - calendar Range mode highlights inclusive range
   - calendar Individual mode toggles single days
2. Run vitest, confirm RED.

### Phase 4 — IMPL frontend (frontend-worker)
1. Delete the scan/ directory and sidebar entry.
2. Build the feature folder per the file map above, following the design spec from Phase 0.
3. Implement service calls against the new endpoints.
4. Wire sidebar entry (visible to all roles).
5. Run vitest, tsc, lint, build until all green.

### Phase 5 — Verification (test-worker)
1. Backend: full pytest suite still green.
2. Frontend: full vitest suite + tsc + lint + build all green.
3. Manual smoke check via `./start.sh`:
   - log in as admin → create a range of days → add a presentation → log out
   - log in as student → see the planificación read-only → no edit affordances
4. Document results in `summary.md`.

## Artifacts

- **Reads:**
  - `backend/api/{models,serializers,views,urls}.py`
  - `backend/api/migrations/` (latest)
  - `frontend/src/widgets/sidebar/Sidebar.tsx`
  - `frontend/src/app/dashboard/scan/*`
  - `frontend/src/features/projects/api/projectService.ts`
  - `frontend/src/features/semesters/api/semesters.ts`
- **Writes:**
  - `backend/api/models.py` (+ migration)
  - `backend/api/serializers.py`
  - `backend/api/views.py`
  - `backend/api/urls.py`
  - `backend/tests/test_planificacion.py` (new)
  - `frontend/src/features/planificacion/**` (new)
  - `frontend/src/app/dashboard/planificacion/page.tsx` (new)
  - `frontend/src/app/dashboard/planificacion/loading.tsx` (new)
  - `frontend/src/widgets/sidebar/Sidebar.tsx` (edit)
  - DELETE `frontend/src/app/dashboard/scan/` (entire dir)
  - `frontend/tests/features/planificacion.test.tsx` (new)
  - `.claude/state/20260414-006-planificacion-module/{design-spec,brief,backend-worker-result,frontend-worker-result,test-worker-result,summary}.md`

## Verification

- `pytest` → all green, including ≥6 new tests
- `npx vitest run` → all green, including new feature tests
- `npx tsc --noEmit` → no new errors
- `npm run lint` → no new errors
- `npm run build` → succeeds
- Manual: admin can plan a week, non-admin sees read-only

## Risks

1. **Permission misconfiguration.** Easy to leave a write endpoint open. Mitigation: tests assert 403 for each non-admin role on every write verb.
2. **Date timezone bugs.** `DateField` is timezone-naive; the frontend must send `YYYY-MM-DD` strings, not Date objects. Mitigation: serialize/deserialize as strings, never as `new Date()` JSON.
3. **Calendar UX complexity.** Range vs individual selection is the trickiest piece; pulling in a heavy date-picker lib would be wrong. Plan: build it in-house with Tailwind + simple state, ~150 LoC, no new dependency. If complexity balloons we can fall back to `react-day-picker` (small, ~10 kB), but only with explicit approval.
4. **Project autocomplete performance.** Filtering all projects in a semester might be slow for big lists. Mitigation: reuse existing `projectService.list()` with a server-side `?period=` filter; debounce client-side text filter.
5. **Cascade delete surprise.** Deleting a `PresentationDay` removes its presentations silently. Mitigation: confirmation modal in the UI; document in API docs.
6. **Sidebar role visibility regression.** Removing the scan entry could accidentally remove other entries; do a single-line `Edit` not a rewrite.
7. **Frontend-design skill output drift.** If the design spec contradicts the existing visual language, we should reconcile before coding. Phase 0 explicitly produces the spec for human review (optional checkpoint).

## User answers (locked in 2026-04-14)

1. **Multiple jurados per presentation:** YES — M2M.
2. **Jurado pool:** any user with `role == 'Jurado'`.
3. **Time-of-day slots:** YES — `start_time` (HH:MM) is required, `duration_minutes` defaults to 30.
4. **Sidebar visibility:** all 4 roles see "Planificación".
5. **Design-spec checkpoint:** YES — Phase 0 produces the spec and BLOCKS until the user approves it.

## Plan summary

1. Orchestrator: invoke `frontend-design` skill → `design-spec.md`. (Phase 0)
2. test-worker (RED, backend): write failing pytest. (Phase 1)
3. backend-worker (IMPL): models, migration, serializers, viewset, urls. (Phase 2)
4. test-worker (RED, frontend): write failing vitest. (Phase 3)
5. frontend-worker (IMPL): delete scan, build planificacion feature, sidebar swap. (Phase 4)
6. test-worker (GREEN both stacks) + manual smoke. (Phase 5)
7. Orchestrator: write summary, report to human, do NOT commit.
