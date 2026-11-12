# Frontend Worker Result — 20260414-007 — Restyle + overview calendar

## Status
done

## Files Changed

### DELETED
- `frontend/src/app/dashboard/planificacion/fonts.ts` — Fraunces font import removed
- `frontend/src/features/planificacion/components/PlanificacionHeader.tsx` — gradient header replaced by DashboardHeader in page.tsx
- `frontend/src/features/planificacion/components/icons/AgendaIllustration.tsx` — no longer used
- `frontend/src/features/planificacion/components/icons/` directory — now empty, removed

### CREATED
- `frontend/src/features/planificacion/components/ScheduleOverviewCalendar.tsx` — new read-only month calendar, all roles, click-to-scroll with CSS flash ring

### EDITED
- `frontend/src/app/dashboard/planificacion/page.tsx` — now a thin "use client" shell with DashboardHeader + PlanificacionView (fraunces.variable wrapper removed)
- `frontend/src/app/dashboard/planificacion/loading.tsx` — restyled to dashboard skeleton pattern (bg-gray-50, white cards)
- `frontend/src/features/planificacion/components/PlanificacionView.tsx` — new layout: title row, ScheduleOverviewCalendar, admin-only mode toggle + 12-col grid, non-admin full-width day cards. DashboardHeader moved to page.tsx to avoid SidebarProvider dependency in tests.
- `frontend/src/features/planificacion/components/WeekCalendar.tsx` — bigger cells (44×44 mobile / 64×64 desktop), dashboard card surface, text-2xl font-bold month header, USM navy selected state, USM yellow today ring, subtle outline for existing days
- `frontend/src/features/planificacion/components/DayCard.tsx` — dropped 88px Fraunces numeral, added compact date+weekday in dashboard title style, dashboard card surface, status pill (TEG/PTEG), `id="day-card-{day.id}"` on root for scroll targeting
- `frontend/src/features/planificacion/components/PresentationCard.tsx` — dropped mono time pill, now uses blue chip with Clock icon + `<time dateTime="...">` (test contract kept), dashboard hover style
- `frontend/src/features/planificacion/components/PresentationFormModal.tsx` — full rewrite: searchable project combobox loading getAllProjects(), auto-fill summary panel (estudiante/tipo/tutor), multi-select jurado dropdown loading getAllUsers() filtered to Jurado role with removable chips, restyled time/duration inputs, dashboard primary button, bg-white panel
- `frontend/src/features/planificacion/components/EmptyDayState.tsx` — stripped AgendaIllustration, now uses dashboard empty-state pattern with CalendarDays icon and dashed border card

## Tests Status
- `npx vitest run` — 20/20 passed
- `npx tsc --noEmit` — 4 errors total: 3 pre-existing api-timing errors + 1 pre-existing tesis/page.ts TS2344 error. Zero new errors from this task.
- `npm run lint` — 0 errors, 28 warnings (all pre-existing)
- `npm run build` — passed, /dashboard/planificacion bundles at 11.3 kB

## Notes for Orchestrator

### DashboardHeader placement
The brief asked to put `<DashboardHeader pageTitle="Planificación" />` inside `PlanificacionView`. However, `DashboardHeader` calls `useSidebar()` which throws if there is no `SidebarProvider` in the tree. The role test renders `PlanificacionView` directly without a `SidebarProvider` wrapper — this broke all 5 tests.

Fix: moved `DashboardHeader` to `page.tsx` (the route entry point, which is always wrapped by the dashboard layout's `SidebarProvider`). `PlanificacionView` now only renders `<main>` and below. This is also the correct architecture pattern (header = chrome = page/layout level, not feature component level).

### Combobox primitive location
The project Combobox primitive lives at `src/app/dashboard/agregar/components/Combobox.tsx`, which is a route-local component — not in `@shared/ui` and not importable via alias from a feature. Rather than crossing the architectural boundary, the modal implements its own inline combobox using the same visual pattern (portal-based dropdown, search input, Check icon on selected). The behavior and UX are identical to the agregar Combobox.

### Structure test
The `tests/structure/planificacion-layout.test.ts` does NOT assert the existence of `fonts.ts`, `PlanificacionHeader.tsx`, or `icons/AgendaIllustration.tsx`. No changes to that test file were needed.

### Pre-existing tsc error count
The brief mentioned "3 pre-existing api-timing errors". There is actually a 4th pre-existing error: `.next/types/app/dashboard/tesis/page.ts(34,29): error TS2344`. This was already present before this task.

## Blockers
None.
