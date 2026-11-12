# Task 007 — Planificación Restyle (match dashboard look + dropdown auto-fill)

## Goal

Replace the bespoke "Editorial Almanac" visual treatment of the
Planificación module (task 006) with the same visual language used by
the rest of the dashboard. Make the calendar bigger. Replace the raw
"ID del Proyecto" / "ID del Jurado" number inputs in the form modal
with **searchable dropdowns** that load real projects and Jurado users
and **auto-fill** all the implicit fields (tutor, project type, etc.)
when a project is picked.

User intent verbatim:

> Redesign the planificacion section, using the same design as the
> rest of the modules, making the calendar bigger and keeping the same
> font as well. As for the form, make it auto fillable by the dropdowns
> showing the available tesis and proyectos and jurados.

## Scope summary

This is a frontend-only restyle + form-behavior change. **No backend
changes. No new tests.** The existing 9 vitest tests in
`tests/structure/planificacion-layout.test.ts` and
`tests/features/planificacion-roles.test.tsx` must still pass — none
of the file paths or `aria-label` contracts are changing, only the
visuals + the form internals.

## What's changing

### 1. Drop the bespoke visual identity

**Delete:**
- `frontend/src/app/dashboard/planificacion/fonts.ts` (Fraunces import)
- The Fraunces variable wiring on the route wrapper (the `font-display` CSS variable)
- The `bg-[#fbfaf6]` warm page background
- The full-bleed gradient `PlanificacionHeader.tsx` component (the header now comes from the standard `DashboardHeader` like every other dashboard route)
- The decorative serif glyph behind the wordmark
- The grain SVG overlay

**Keep:** the four USM brand colors (Navy / Blue / Orange / Yellow). They are referenced from `globals.css` as `--color-usm-*` and used elsewhere too. Don't strip them — just stop layering them under decorative gradient + grain treatment.

### 2. Match the dashboard layout pattern

Mirror `frontend/src/app/dashboard/proyectos/page.tsx` and `frontend/src/app/dashboard/tracking/page.tsx`:

```tsx
return (
  <>
    <DashboardHeader pageTitle="Planificación" />
    <main className="flex-1 p-3 sm:p-4 md:p-6 lg:p-8 overflow-y-auto bg-gray-50">
      <div className="max-w-7xl mx-auto">
        {/* Title row with semester selector + admin CTA on the right */}
        <div className="mb-8 flex flex-col lg:flex-row lg:items-end justify-between gap-6">
          <div className="space-y-1">
            <h2 className="text-3xl font-extrabold text-gray-900 tracking-tight">
              Planificación de presentaciones
            </h2>
            <p className="text-gray-500 font-medium">
              Programa los días y horarios de las presentaciones del período.
            </p>
          </div>
          <div className="flex flex-wrap items-center gap-4">
            <SemesterSelector ... />
            {/* Admin: "Crear días" CTA pill */}
          </div>
        </div>

        {/* Mode toggle (segmented control, dashboard style) */}
        <div className="bg-white/60 backdrop-blur-xl rounded-[2rem] border border-gray-200/60 shadow-xl shadow-slate-200/40 p-5 sm:p-6 mb-8">
          {/* Range / Individual segmented control + helper text */}
        </div>

        {/* Calendar + day cards layout */}
        <div className="grid grid-cols-1 xl:grid-cols-12 gap-8">
          <div className="xl:col-span-7">{/* Bigger calendar */}</div>
          <div className="xl:col-span-5">{/* Day cards stack */}</div>
        </div>
      </div>
    </main>
  </>
);
```

Use the existing `DashboardHeader`, `SemesterSelector`, segmented-control pattern, white/60 backdrop-blur cards, button styles, and loading spinner from those reference files. **Match the rounded-2xl / rounded-[2rem] radius. Match the shadow-xl shadow-slate-200/40 elevation. Match the text-3xl font-extrabold tracking-tight title style.** No new tokens.

Font is whatever the rest of the dashboard already uses (Geist, configured at the root `layout.tsx`). Do NOT introduce any font import inside this route.

### 3. Two calendar sections — Overview (all roles) + Editor (admin)

The page now has **two** distinct calendar surfaces. Both are styled identically to each other and to the rest of the dashboard, but they serve different purposes.

#### 3a. Schedule Overview Calendar — NEW component, all roles

A new read-only month calendar that shows **every day with scheduled presentations** for the active semester. This is the primary "when am I supposed to be where" view for students, tutors, and jurados — and the at-a-glance summary for admins.

- **New file:** `frontend/src/features/planificacion/components/ScheduleOverviewCalendar.tsx`
- Lives in a card at the **top** of the content area (above the editor and day cards), full content width on all breakpoints. It is the most prominent element on the page.
- Same big-cell month grid style as the editor calendar (see 3b for sizing).
- Each day with a `PresentationDay` shows a `usm-blue` chip with the **count** of presentations and a small calendar icon. Days without presentations are dim (`text-gray-400`).
- Today gets a subtle `usm-yellow` ring.
- **No selection state.** Clicking a populated day **smoothly scrolls** the page to that day's card below (`element.scrollIntoView({ behavior: 'smooth', block: 'center' })`) and briefly flashes the destination card with a `usm-yellow` ring (CSS animation, 1 s). Clicking an empty day is a no-op.
- Month navigation arrows `< >` switch the visible month. Defaults to the month containing the soonest upcoming `PresentationDay`, or current month if none.
- Header: `text-2xl font-bold text-gray-900 tracking-tight` for "Calendario de presentaciones" + a small subtitle "Haz clic en un día para ver los detalles."
- Visible to **all four roles**. No admin gating.

#### 3b. Editor Calendar — existing `WeekCalendar.tsx`, admin-only

The existing range/individual selection calendar that admins use to create new `PresentationDay` rows. After the restyle:

- Lives in its own card **below the overview**, in a 12-column layout: `xl:col-span-7` for the editor card (~720 px wide) and `xl:col-span-5` for the day cards stack to its right. Below `xl:` everything stacks vertically.
- **Render-gated to admin only** (use the existing `isAdmin` check in `PlanificacionView`). Non-admins skip this section entirely and see overview + day cards only.
- Day cells grow from 40×40 to **64×64**. Day numerals go from `text-base` to `text-xl font-semibold`.
- Month header (`< Abril 2026 >`) uses the dashboard title style (`text-2xl font-bold text-gray-900 tracking-tight`), not Fraunces.
- Selected days: solid `usm-navy` background with white text.
- Range preview during hover: `usm-blue/15` fill, same as before.
- The "Crear días" / "Actualizar días" CTA stays at the footer of the editor card. **Keep its accessible name matching `/crear .* días/i`** for the existing role test.
- The editor calendar does NOT need to highlight existing `PresentationDay`s with chips — that's the overview's job. A simple subtle outline is enough so the admin doesn't double-create.

#### Layout recap

```
[DashboardHeader: Planificación]

Title row + semester selector

┌─ Schedule Overview Calendar (NEW, all roles) ──────────────────┐
│  Big month grid, click a populated day to scroll to its card  │
└────────────────────────────────────────────────────────────────┘

┌─ Mode toggle (admin only) ──┐
│  Rango ⇄ Individual         │
└─────────────────────────────┘

┌─ 12-col grid ────────────────────────────────────────────────────┐
│ ┌── Editor Calendar (admin only, col-span-7) ──┐ ┌── Day cards ─┐│
│ │ 64×64 cells, range/individual selection      │ │ DayCard       ││
│ │ [Crear/actualizar días]                      │ │ DayCard       ││
│ └──────────────────────────────────────────────┘ │ ...           ││
│                                                   └───────────────┘│
└──────────────────────────────────────────────────────────────────┘

# For NON-admins, the layout is simpler:

[DashboardHeader: Planificación]
Title row + semester selector
┌─ Schedule Overview Calendar ──────────┐
└───────────────────────────────────────┘
┌─ Day cards stack (full width) ────────┐
└───────────────────────────────────────┘
```

For non-admins, the day cards stack takes the full content width since there's no editor column to share with.

### 4. Day card simplification

`DayCard.tsx` keeps its info but loses the editorial flourishes:

- Drop the 88 px Fraunces day numeral. Replace with a compact day-of-month + weekday label in the dashboard's title style: `text-2xl font-bold text-gray-900` for the date, `text-sm font-semibold uppercase tracking-wide text-gray-500` for the weekday.
- Drop the project-type-keyed 4 px left border + border-image gradient. Replace with a small status pill in the card header: blue chip "PTEG" or orange chip "TEG" (matching the existing tracking/proyectos pages' chip style).
- Card surface: `bg-white rounded-2xl border border-gray-200/60 shadow-xl shadow-slate-200/40 p-5 sm:p-6` (matches the dashboard cards).
- Admin actions row (✎ / 🗑) stays as before; **keep the existing `aria-label="Editar presentación"` and `aria-label="Eliminar presentación"` — the role test depends on these strings.**
- Empty day state inside a card: simple muted text, no illustration.

### 5. Presentation row simplification

`PresentationCard.tsx`:

- Time pill stays — keep `<time dateTime="HH:MM">HH:MM</time>` (the test asserts the rendered text), but restyle to match the existing badge pattern: `inline-flex items-center gap-1 px-3 py-1 rounded-full bg-blue-50 text-blue-700 text-xs font-bold` plus a small `Clock` icon from `lucide-react`. **Do NOT use Geist Mono — use the same font stack as the rest of the row.**
- Project title: `text-base font-semibold text-gray-900`.
- Student / tutor / jurado lines: `text-sm text-gray-500`.
- Hover background: `bg-gray-50`.

### 6. Form modal — searchable dropdowns + auto-fill

This is the biggest behavior change. Replace the current raw-input form with the existing dashboard form patterns. Reference: `frontend/src/app/dashboard/agregar/components/DocumentFormNew.tsx` to see how `Combobox` is used in this app.

**Modal styling:**
- Drop the `bg-[#fbfaf6]`, drop the `font-display` style override on the title, drop the editorial framing.
- Use `bg-white rounded-2xl shadow-2xl ring-1 ring-black/5`.
- Title: `text-2xl font-bold text-gray-900 tracking-tight` (dashboard style).
- Backdrop: `bg-black/40 backdrop-blur-sm` (already correct).

**Form fields (top to bottom):**

1. **Proyecto / Tesis** — searchable Combobox. On modal open, fetch projects from `getAllProjects()` (already in `projectService`). Filter to projects in the active semester if a semester is selected on the page. Display label: `${project.title} — ${project.student} (${project.type === 'tesis' ? 'TEG' : 'PTEG'})`. Selecting a project sets `projectId` AND triggers auto-fill of the readonly fields below.

2. **Read-only auto-filled summary panel** (appears once a project is selected):
   ```
   ┌──────────────────────────────────────────────┐
   │ Estudiante:  Ana López                       │
   │ Tipo:        Tesis (TEG)                     │
   │ Tutor:       Prof. Carlos Méndez             │
   └──────────────────────────────────────────────┘
   ```
   Style: `bg-blue-50/50 rounded-xl border border-blue-100 p-4 text-sm`. Use `font-semibold text-gray-900` for values, `text-gray-500` for labels. The tutor comes from `project.advisorNames[0]` — look at the existing project type to confirm the field name (it's `advisorNames` in `Project`, but the API returns `advisors` — pick whichever is available on the loaded object).

3. **Jurados** — searchable multi-select dropdown. On modal open, fetch users via `getAllUsers()` (already in `clientAuth.ts`), filter to `user.role === 'Jurado'`. Display label: `${user.fullName} — ${user.email}`. Selected jurados render as removable chips below the dropdown. **Do not allow adding a non-Jurado user — the dropdown is the only path in.**

4. **Hora de inicio** + **Duración** — keep the existing time + number inputs side by side, but restyle to match the dashboard input style: `w-full px-4 py-2.5 rounded-xl border border-gray-200 bg-white text-sm focus:bg-white focus:border-blue-400 focus:ring-4 focus:ring-blue-100/50 transition-all`.

5. **Footer:** "Cancelar" (ghost) + "Guardar" (solid `bg-[#0f172a] text-white hover:bg-[#1e293b]` like the dashboard primary button).

**Validation:** project + start_time required (already enforced); jurados array can be empty (optional). Match the existing inline error pattern: `text-sm text-red-600 font-semibold`.

**Loading state:** while `getAllProjects` and `getAllUsers` are pending, render an inline spinner inside each dropdown (existing `Combobox` already supports this). Do NOT block the entire modal.

### 7. Calendar size + header simplification — concrete numbers

| Element             | Before                | After                        |
|---------------------|----------------------|------------------------------|
| Calendar column width| `lg:w-72 xl:w-80`    | `xl:col-span-7` (~720 px)    |
| Day cell             | 40×40                 | 64×64                        |
| Day numeral          | Fraunces, weight 300  | Geist, `text-xl font-semibold` |
| Month header         | `display-m` Fraunces  | `text-2xl font-bold` Geist   |
| Existing day marker  | 4 px `usm-blue` dot   | small chip with count        |
| Calendar surface     | white, soft 24 px shadow | dashboard `rounded-2xl border border-gray-200/60 shadow-xl shadow-slate-200/40` |

## Files to touch

| File                                                                              | Change                                  |
|-----------------------------------------------------------------------------------|----------------------------------------|
| `frontend/src/app/dashboard/planificacion/fonts.ts`                                | DELETE                                 |
| `frontend/src/app/dashboard/planificacion/page.tsx`                                | drop fonts.variable wrapper            |
| `frontend/src/app/dashboard/planificacion/loading.tsx`                             | restyle to dashboard skeleton          |
| `frontend/src/features/planificacion/components/PlanificacionView.tsx`             | new layout (DashboardHeader + max-w-7xl), overview at top, 12-col grid below, semester selector |
| `frontend/src/features/planificacion/components/PlanificacionHeader.tsx`           | DELETE (responsibilities absorbed into PlanificacionView) |
| `frontend/src/features/planificacion/components/ScheduleOverviewCalendar.tsx`      | NEW — read-only month overview with click-to-scroll, all roles |
| `frontend/src/features/planificacion/components/WeekCalendar.tsx`                  | bigger cells, dashboard style, admin-only render gate |
| `frontend/src/features/planificacion/components/DayCard.tsx`                       | strip Fraunces, dashboard card style, status pill |
| `frontend/src/features/planificacion/components/PresentationCard.tsx`              | strip mono pill, use dashboard chip style |
| `frontend/src/features/planificacion/components/PresentationFormModal.tsx`         | full rewrite of fields: Combobox project picker, auto-fill summary, multi-select jurados |
| `frontend/src/features/planificacion/components/EmptyDayState.tsx`                 | strip illustration, dashboard empty state pattern |
| `frontend/src/features/planificacion/components/icons/AgendaIllustration.tsx`      | DELETE (no longer used)                |

**Files NOT touched:** `api/planificacionService.ts`, `types/planificacion.ts`, `hooks/usePlanificacion.ts`, `hooks/useDateSelection.ts`, `lib/formatDate.ts`, `index.ts`. The contract with the backend stays the same; the type interfaces stay the same; the data hooks stay the same.

## Test contract — what must keep passing

The existing 9 tests must still pass without modification:

- `tests/structure/planificacion-layout.test.ts` — asserts file existence. **Two files are being deleted (`fonts.ts`, `PlanificacionHeader.tsx`, `AgendaIllustration.tsx`).** Check the test file FIRST — if it asserts any of those paths exist, update the test in the same commit. If it doesn't, no change needed.
- `tests/features/planificacion-roles.test.tsx` — asserts:
  - "agregar presentación" button exists for admin → **keep the same button text inside `DayCard`**
  - "crear días" / "actualizar días" CTA exists for admin → **keep this button accessible by name**
  - `aria-label="Editar presentación"` and `aria-label="Eliminar presentación"` on row icons → **keep these exact labels**
  - Time pill renders `"14:30"` as findable text → **keep `<time dateTime="14:30">14:30</time>`**
  - "Sistema de Gestión Académica" project title visible → **make sure the project title still renders inside the row**
  - Non-admin renders MUST NOT contain admin buttons → **keep render-time role gating**

If the structure test asserts the deleted file paths, update it as a one-line edit alongside the implementation. The roles test shouldn't need any changes.

## Decomposition

This is small enough to skip the test-worker red phase — no new tests, the existing tests already encode the contract. Plan:

1. **Phase 1 — IMPL (frontend-worker).** Restyle the 8 components, delete the 3 dead files, rewrite the modal form. Run the existing test suite + tsc + lint + build to verify no regression. Spot-check the structure test for stale path assertions and update if needed.
2. **Phase 2 — Verification (orchestrator).** Run the full vitest suite, tsc, lint, build. Read the worker's report and write the summary.

## Verification

- `npx vitest run` → 20/20 still passing (or N+1 if structure test updated)
- `npx tsc --noEmit` → 3 pre-existing api-timing errors only, zero new
- `npm run lint` → 0 errors
- `npm run build` → success
- Manual smoke (worker spins up dev server briefly, kills it after the check):
  - `/dashboard/planificacion` loads
  - Calendar is visibly bigger and matches the dashboard look
  - Open the modal as admin → project dropdown loads real projects → selecting one auto-fills the summary panel → jurado dropdown lists Jurado users → save flow still works

## Risks

1. **`Combobox` API surface unknown to me.** Worker must read `frontend/src/shared/ui/Combobox.tsx` (or wherever it lives) and use its existing props. Do NOT modify the Combobox primitive — if it doesn't support multi-select natively, build a thin local wrapper inside `features/planificacion/components/JuradoMultiSelect.tsx` that uses the single-select Combobox plus a chip strip. Do not add to `@shared`.
0. **Day-card scroll target.** The overview's click-to-scroll requires each `DayCard` to be reachable by id. Add `id={`day-card-${day.id}`}` to the root element of `DayCard.tsx` and have the overview scroll via `document.getElementById(...)?.scrollIntoView(...)`. The flash effect is a one-shot CSS class added then removed via `setTimeout(1000)`.
2. **`getAllProjects()` and `getAllUsers()` payload shapes.** Worker must inspect both before calling them — the field names (`fullName` vs `full_name`, `advisorNames` vs `advisors`) may differ between camelCase and snake_case depending on how the API client normalizes. Use whatever is actually on the returned object.
3. **`PlanificacionHeader.tsx` deletion** — make sure no other file imports it. Grep first.
4. **Fraunces removal** — the route's `<html>` wrapper currently injects `fraunces.variable`. Removing this is a route-file edit, not a global one. Verify Geist is still loaded from the root `layout.tsx` (it is — this app uses Geist as the default sans-serif).
5. **Bigger calendar on small screens** — at `< xl` the calendar stacks above the day cards, so 64×64 cells are fine on tablet. On mobile (`< 640px`), shrink to 44×44 to avoid horizontal overflow.
6. **Test breakage from deleted files** — if `planificacion-layout.test.ts` asserts the existence of any of the 3 deleted files (`fonts.ts`, `PlanificacionHeader.tsx`, `icons/AgendaIllustration.tsx`), update those assertions in the same commit. Document the change in the worker result.

## Out of scope

- Backend changes
- New tests (the existing 9 already cover the contract)
- Multi-month calendar view (still single-month)
- Print stylesheet
- Conflict detection for overlapping HH:MM slots
- ICS export
- The 3 pre-existing tsc errors in `tests/lib/api-timing.test.ts` (still task 004 leftover)

## Plan summary

1. Orchestrator writes brief, presents to user, waits for approval.
2. frontend-worker (IMPL): restyle 8 components, delete 3 files, rewrite modal form, spot-check structure test.
3. Orchestrator: run full verification suite, write summary, report to human, do NOT commit.
