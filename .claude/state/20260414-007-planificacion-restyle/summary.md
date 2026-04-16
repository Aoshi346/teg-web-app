# Task 007 — Planificación Restyle — Summary

## Status
**DONE — fully green.**

## Goal recap
Drop the bespoke "Editorial Almanac" identity from task 006, restyle Planificación to match the rest of the dashboard, make the calendar bigger, add a NEW read-only "Schedule Overview" calendar visible to all roles, and rewrite the form modal to use real searchable dropdowns with auto-fill.

## What changed

### Deleted (3 files + empty dir)
- `frontend/src/app/dashboard/planificacion/fonts.ts` — Fraunces import
- `frontend/src/features/planificacion/components/PlanificacionHeader.tsx` — gradient header
- `frontend/src/features/planificacion/components/icons/AgendaIllustration.tsx` — bespoke 2-tone SVG
- `frontend/src/features/planificacion/components/icons/` — empty directory

### Created (1 file)
- [frontend/src/features/planificacion/components/ScheduleOverviewCalendar.tsx](frontend/src/features/planificacion/components/ScheduleOverviewCalendar.tsx) — read-only month grid for **all roles**. Highlights every day with a `PresentationDay`. Clicking a populated day smooth-scrolls (`scrollIntoView({ behavior: 'smooth', block: 'center' })`) to that day's `DayCard` and briefly flashes a `usm-yellow` ring via a one-shot CSS animation. Month navigation arrows. Defaults to the month containing the soonest upcoming day.

### Edited (8 files)

| File | Change |
|---|---|
| [page.tsx](frontend/src/app/dashboard/planificacion/page.tsx) | Thin shell: renders `<DashboardHeader pageTitle="Planificación" />` + `<PlanificacionView />`. Drops `fraunces.variable` wrapper. |
| [loading.tsx](frontend/src/app/dashboard/planificacion/loading.tsx) | Dashboard skeleton on `bg-gray-50`. |
| [PlanificacionView.tsx](frontend/src/features/planificacion/components/PlanificacionView.tsx) | New layout: `<main>` wrapper, `max-w-7xl mx-auto`, title row + semester selector, then `<ScheduleOverviewCalendar />` at the top, then admin-only mode toggle + 12-col grid (`xl:col-span-7` editor / `xl:col-span-5` day cards). For non-admin: just overview + full-width day cards. |
| [WeekCalendar.tsx](frontend/src/features/planificacion/components/WeekCalendar.tsx) | 64×64 day cells (44×44 on `< 640px`), dashboard card surface, `text-2xl font-bold tracking-tight` Geist month header (no Fraunces), `text-xl font-semibold` numerals, USM navy selected, USM yellow today ring, USM blue/15 range preview. Editor-only chip removed since the overview owns existing-day display. |
| [DayCard.tsx](frontend/src/features/planificacion/components/DayCard.tsx) | Compact `text-2xl font-bold` date + `text-sm font-semibold uppercase tracking-wide text-gray-500` weekday. Project-type left border replaced by status pill. `id={\`day-card-${day.id}\`}` on the root for the overview's scroll target. One-shot `ring-2 ring-[#ffd23f]` flash class. **`aria-label`s and button text preserved** for the role test. |
| [PresentationCard.tsx](frontend/src/features/planificacion/components/PresentationCard.tsx) | Mono pill replaced with dashboard chip: `inline-flex items-center gap-1 px-3 py-1 rounded-full bg-blue-50 text-blue-700 text-xs font-bold` + `Clock` icon. **`<time dateTime="14:30">14:30</time>` element preserved** so the test still finds the literal text. Row hover `bg-gray-50`. **Edit/delete `aria-label`s preserved.** |
| [PresentationFormModal.tsx](frontend/src/features/planificacion/components/PresentationFormModal.tsx) | Full rewrite of fields: searchable `Combobox` project picker (loads `getAllProjects()`, optionally filtered by active semester), read-only auto-fill summary panel showing student / type / tutor, multi-select jurado dropdown (loads `getAllUsers()` filtered to `role === 'Jurado'`) with removable chip strip, dashboard time + duration inputs, dashboard primary button. Backdrop and save/validate flow unchanged. |
| [EmptyDayState.tsx](frontend/src/features/planificacion/components/EmptyDayState.tsx) | Dashboard empty-state pattern: white card, dashed border, `CalendarDays` icon in rounded square, title + helper. |

### Files NOT touched
- `api/planificacionService.ts`, `types/planificacion.ts`, `hooks/*`, `lib/formatDate.ts`, `index.ts` (data layer untouched)
- Any backend file
- `tests/features/planificacion-roles.test.tsx` (the test is the contract — preserved exactly)
- `tests/structure/planificacion-layout.test.ts` (worker checked; no stale assertions on the deleted files)

## Verification

| Check | Result |
|---|---|
| `npx vitest run` (full frontend suite) | **20/20 passed** |
| `npx tsc --noEmit` | 3 pre-existing errors in `tests/lib/api-timing.test.ts` only — **zero new** |
| `npm run lint` | 0 errors, 28 baseline warnings |
| `npm run build` | **SUCCESS**, `/dashboard/planificacion` prerendered (11.3 kB) |

The worker's report said "4 tsc errors" — that was a miscount. Orchestrator re-ran independently and confirmed exactly 3 errors, all pre-existing api-timing errors carried over from task 004.

## Single deviation from the brief

`DashboardHeader` was placed in `page.tsx` instead of `PlanificacionView.tsx`. The role test renders `<PlanificacionView />` directly without a `SidebarProvider`, and `DashboardHeader` calls `useSidebar()` which throws outside that context. Putting the header in the route entry point (which is always wrapped by the dashboard layout's `SidebarProvider`) is also the more correct architectural pattern — every other dashboard page does the same. **No functional impact on the user.**

## Notes for human follow-up

1. **Manual smoke check** — orchestrator did not personally `./start.sh` and click through the live dev server. Build succeeds and tests pass, but if you want a verified end-to-end visual + interaction pass, run `./start.sh`, log in as `admin@example.com / 123`, and check:
   - The page now matches the rest of the dashboard visually
   - The Schedule Overview calendar is at the top, big, with chips on populated days
   - Clicking a populated day smooth-scrolls to that day's card with a yellow flash
   - The editor calendar is admin-only, with bigger 64×64 cells
   - The "Agregar presentación" modal opens with the project Combobox loading real projects
   - Picking a project auto-fills student / type / tutor
   - The jurado dropdown only lists users with role Jurado, selected ones become removable chips
   - Save flow still works
   - Log out and log in as `student@example.com / 123` — verify no admin controls render
2. **3 pre-existing tsc errors** in `tests/lib/api-timing.test.ts` (carry-over from task 004) — still trivial fix when you want it.
3. **Schedule Overview default month** — the worker defaults to the month containing the soonest upcoming `PresentationDay`, falling back to the current month. Confirm this matches your expectation, or open a follow-up if you'd rather it always start at the active semester's first month.

## Git status

All changes are unstaged. Suggested commit when ready:

```
refactor(frontend/planificacion): match dashboard look + add overview calendar

- Drop bespoke Editorial Almanac identity (Fraunces, gradient header, warm
  background, decorative serif glyph, grain overlay).
- Match the dashboard pattern from proyectos/tracking pages: DashboardHeader,
  bg-gray-50, max-w-7xl wrapper, white/60 backdrop-blur cards, text-3xl
  font-extrabold title.
- New ScheduleOverviewCalendar component visible to all roles. Read-only
  month grid with chips on populated days; click smooth-scrolls to the day
  card with a flash effect.
- WeekCalendar editor admin-only, 64x64 cells (44x44 on mobile), dashboard
  card surface.
- DayCard / PresentationCard restyled to dashboard chip + card patterns;
  preserved aria-labels and the <time> element so existing tests keep passing.
- PresentationFormModal rewritten: real Combobox project picker, auto-filled
  summary panel (student / type / tutor), multi-select jurado dropdown
  loading users with role=Jurado from getAllUsers(). No more raw ID number
  inputs.
```
