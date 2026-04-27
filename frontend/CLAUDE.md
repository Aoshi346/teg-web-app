# Frontend Development Guide - TesisFar

## Quick Reference

- **Entry point:** `src/app/layout.tsx` (root layout) / `src/app/page.tsx` (landing)
- **Run dev server:** `npm run dev` (port 3000, Webpack — Webpack is now the default; `npm run dev:turbo` opts into Turbopack)
- **Backend API:** http://localhost:8000/api
- **Install deps:** `npm install`

## Architecture

Next.js 15 App Router with file-based routing. All dashboard routes are protected by the auth guard in `src/app/dashboard/layout.tsx`. The codebase follows a **Feature-Sliced Design lite** layout.

```
Page (app/) → Feature Component (features/<x>/) → Service (features/<x>/api/) → HTTP Client (@shared/api/api) → Django API
```

## Project Layout

```
src/
  app/                     # Next.js routes only — pages stay thin
  features/<name>/         # auth, projects, evaluations, semesters, dashboard, settings, landing
    api/                   # service functions (HTTP calls)
    components/            # feature-specific components
    hooks/                 # feature-specific hooks
    lib/                   # feature-specific helpers
    types/                 # feature-specific types
    index.ts               # public barrel — only export what other features consume
  widgets/                 # cross-feature layout composites
    sidebar/               # Sidebar, SidebarContext
    header/                # Header, DashboardHeader, Footer
  shared/
    api/                   # api.ts (HTTP client), normalizeError.ts
    ui/                    # primitives (button, card, input, Toast, Banner, Notice, ...)
    lib/                   # utils.ts (cn helper)
    hooks/                 # cross-cutting hooks (useValidation)
    types/                 # ambient types (split-type.d.ts)
```

### Path aliases (`tsconfig.json`)

| Alias          | Resolves to        | Use for                                                       |
|----------------|--------------------|---------------------------------------------------------------|
| `@/*`          | `./src/*`          | legacy escape hatch                                           |
| `@features/*`  | `./src/features/*` | imports across features and from `app/` into a feature       |
| `@widgets/*`   | `./src/widgets/*`  | layout composites consumed by `app/` pages                    |
| `@shared/*`    | `./src/shared/*`   | UI primitives, http client, utils, cross-cutting hooks/types |

Within a single feature use **relative** imports (`./components/X`). Across features or from `app/`, use the alias.

## Code Conventions

- All pages under `dashboard/` use `"use client"` directive
- Components organized by feature under `features/<name>/components/`; layout chrome in `widgets/`; primitives in `@shared/ui/`
- API services split per feature under `features/<name>/api/`
- Spanish naming in UI text and some variable names (proyectos, tesis, evaluar, agregar)
- Tailwind classes applied inline, no CSS modules
- shadcn/ui primitives in `@shared/ui/` follow the CVA pattern
- Form validation uses React Hook Form + Zod (see `agregar/schema.ts`)
- Searchable dropdowns use the custom `Combobox` component with portal-based rendering

## When Adding a New Page

1. Create directory under `src/app/dashboard/` (e.g., `dashboard/new-page/page.tsx`)
2. Add `"use client"` at the top
3. Add sidebar link in `@widgets/sidebar/Sidebar` (filter by role if needed)
4. Use `DashboardHeader` from `@widgets/header/DashboardHeader`
5. Wrap content in `PageTransition` from `@shared/ui/PageTransition`
6. Page-local components/hooks live next to `page.tsx`. Reusable ones go in a feature, not the route directory.

## When Adding a New Component

Decide WHERE first:
- **Reusable across features** → `@shared/ui/` (primitive) or a feature folder
- **Owned by one feature** → `src/features/<feature>/components/`
- **Cross-feature layout chrome** (sidebar, header, footer) → `src/widgets/`
- **Route-local one-off** → next to the `page.tsx` that uses it

There is no flat top-level `src/components/` anymore.

## When Adding API Calls

1. Add the function to the appropriate service file under `src/features/<feature>/api/`:
   - Auth/users: `@features/auth/api/clientAuth` (e.g., `getTutors()`, `getJurados()`)
   - Projects/evaluations: `@features/projects/api/projectService` (e.g., `assignReviewer(projectId, reviewerId | null)`)
   - Semesters: `@features/semesters/api/semesters`
2. Use the `api` client from `@shared/api/api` (handles CSRF + session cookies automatically)
3. Define TypeScript types in `src/features/<feature>/types/`
4. If callable from outside the feature, re-export it from the feature's `index.ts` barrel.

## Authentication Pattern

```typescript
import { isAuthenticated, getUser, getUserRole } from "@features/auth/api/credentials";

const user = getUser();           // From sessionStorage
const role = getUserRole();       // "Administrador" | "Estudiante" | "Jurado" | "Tutor"
const authed = isAuthenticated(); // boolean
```

Session is stored in `sessionStorage` under key `tf_session_user`. The dashboard layout auto-redirects if not authenticated.

## Role-Based UI Pattern

```typescript
// In Sidebar.tsx, menu items are filtered:
const menuItems = allItems.filter(item => {
  if (item.roles && !item.roles.includes(userRole)) return false;
  return true;
});
```

Roles: `Administrador`, `Estudiante`, `Jurado`, `Tutor`

Jurados only see projects assigned to them (where the project's `reviewer` is the current user) — this is backend-enforced in `ProjectViewSet.get_queryset`, so client lists/counts (e.g., the dashboard Jurado tile) reflect that filter automatically.

## Evaluation System

- Modular architecture under `src/features/evaluations/`
- Input components in `features/evaluations/components/inputs/` (YesNoInput, FrequencyInput, TernaryInput, StarRatingInput, FreeTextInput)
- Custom hooks in `features/evaluations/hooks/` (useEvaluationDraft, useScrollSpy, useEvaluationSubmit)
- Layout: sticky sidebar with section progress + scrollable question grid + sticky action bar
- Question types: `yesno`, `frequency`, `ternary`, `ternary_na`, `ternary_info`, `stars`, `text`
- Two evaluation categories: Diagramacion (5pts) and Contenido (15pts), total 20pts, passing = 10pts
- Thesis has two phases (fase1/fase2); proyecto has one
- Draft persistence via localStorage (`teg_eval_draft:{type}:{projectId}`)
- Evaluator comments stored in `Evaluation.comments` as `{ general: "..." }` and displayed to students on project/thesis detail pages
- Questions/scoring defined in `src/features/evaluations/lib/questions/`
- PTEG evaluation page (`/dashboard/proyectos/[id]/evaluar`) shows a Revisión / Defensa oral segmented control gated by `Project.state`. Terminal states hide the form entirely. The TEG evaluation page (`/dashboard/tesis/[id]/evaluar`) shows a 3-card phase picker (Artículo / Entrega / Defensa) gated by `Project.state` — each completed gate unlocks the next; any failure terminates. The phase picker is wrapped in `dashboard-hero-bg` with Fraunces serif numerals (`.font-display` on `.phase-numeral`) and `.phase` cards tinted by phase state.
- **Sub-F detail-page redesign:** The PTEG and TEG list pages (`/dashboard/proyectos`, `/dashboard/tesis`) share an editorial hero + 3-tile StatTile strip + `StateFilter` dropdown + 4-column card grid (`max-w-screen-2xl`). Each `ProjectCard` carries a single-word `StatePill`, person line, optional context (gauge for approved, phase bar for TEG), and a role-aware action affordance via `cardAction()` — the card-level `<Link>` opens the detail page; the foot-row action `<button>` programmatically routes to the role's action (evaluar / motivo / etc.) with `stopPropagation`. The detail page (`ProjectDetailView`) composes `DetailHero` (hero band + lifecycle ladder + sticky right rail with Evaluar CTA, "Asignar jurado" / "Reasignar estudiante" / "Forzar estado") and `DetailTabs` (URL-driven, `?tab=`) over 5 tab components: `InfoTab`, `EvaluationsTab`, `CommentsTab`, `FilesTab`, `HistoryTab`.
- **Admin state override (PTEG):** `ProjectDetailView` shows a "Forzar estado" button in the right rail for `Administrador` on PTEG projects. Opens `StateOverrideModal` (target state + reason ≥10 chars), calls `overrideProjectState(id, {state, reason})`. Past overrides render in `HistoryTab`'s amber callout for admins only. Non-admin responses omit `project.stateOverrides`.
- **Admin dashboard PTEG tile** shows clickable state-count chips via `StatTileData.segments` that deep-link to `/dashboard/proyectos?state=<value>`. The projects list page reads `?state=` via `applyStateFilter` helper and the `StateFilter` dropdown trigger surfaces the active selection. Non-admin tiles keep the existing `breakdown` string shape.
- **Sub-G Seguimiento redesign:** `/dashboard/tracking` is now table-first and role-aware. The page opens with an editorial hero (`dashboard-hero-bg`) and a `.seg-pill-summary` count line, followed by a filter bar (search + Fase + Modalidad + role-conditional Tutor dropdown). Admin, Jurado, and Tutor all render `SeguimientoTable`; the visible column set is derived from `seguimientoColumnsFor(role)` and varies per role (e.g., admin gets the full set including the inline 3-dot fase ladder; jurado drops tutor/jurado and fase columns). Estudiante diverges entirely: no table is rendered — the page shows `MyProjectCard` instead, a single-project card with 3 phase gates (Fraunces numerals on `.pgate .num`) and a "Próximo paso" callout; gate labels and CTA route branch on `project.type` (PTEG vs TEG). URL state filter is handled via `?state=...` using the existing `applyStateFilter` helper. Per-row actions in `SeguimientoTable` are driven by `cardAction()` — the same helper Sub-F uses on `ProjectCard`. The legacy `frontend/src/shared/ui/TrackingTable.tsx` is retained as dead code; deletion is deferred to a follow-up task.
- **Sub-H Agregar redesign:** `/dashboard/agregar` is now a fully brand-tokened submission surface. Sidebar-level role gate: `Tutor` and `Jurado` no longer see the "Agregar" item — direct URL hits land on a polished `AccessDenied` (Fraunces title, `pending-soft` shield, two CTAs: Volver + a `<Link>` to `/dashboard/tracking`). The page opens with an editorial hero (`dashboard-hero-bg`) carrying role-aware copy (admin: "Registrar trabajo académico"; estudiante 9°: "Sube tu propuesta inicial"; estudiante 10°: "Sube tu trabajo final"). `DocumentTypeSelector` was rebuilt: both PTEG/TEG cards always render with Fraunces "9°"/"10°" numerals; non-allowed cards receive `.locked` + `aria-disabled="true"` driven by `--accent-pteg-soft-*` / `--accent-teg-soft-*` brand tokens. `DocumentFormNew` is restructured into a sectioned card: 3 sections for admin (01 Identificación / 02 Equipo / 03 Archivos), 2 for estudiante (01 Información / 02 Archivo); every raw color class (`purple-*`, `indigo-*`, `emerald-*`) is replaced with `agg-*` semantic classes. `AdvisorsChips` replaces `AdvisorsFieldArray`: a chip stack + single Combobox + "Añadir" button; the 2-tutor cap and `advisors: (number | "")[]` schema contract are preserved. Submit labels: "Registrar trabajo" (admin), "Subir proyecto" / "Subir tesis" (estudiante). Responsive ladder: 980 px (main grid stacks), 780/560 (form rows collapse), 520 (form-head + actions wrap), 380 (advisor button stacks vertical, hero compacts).
- **Sub-I Planificación redesign:** `/dashboard/planificacion` is now role-aware and brand-aligned. `PlanificacionView` dispatches to three role shells via `planificacionRoleView()`: `PlanAdminView` (Administrador), `PlanReviewerView` (Tutor / Jurado), `PlanStudentView` (Estudiante). The two legacy calendars are unified into `UnifiedCalendar` with a `mode: "view" | "create"` toggle — the toggle is visible to admin only; non-admins always get view mode with their assigned days highlighted via `mineDates`. `PresentationRow` (replaces `PresentationCard`) renders a 3-column grid: time block + title-with-dot-and-pill + role-aware action buttons (admin: aria-label edit/delete icon buttons; tutor/jurado: arrow + ownership chip). `DayCard` (replaces `CompactDayCard`) shows a Fraunces day numeral + weekday + count chip + compact time list. `DayDetailModal` (new) shows a Fraunces numeral block + agenda list + notes block + admin footer actions (Editar día / + Añadir presentación); closes on ✕, overlay click, ESC. `PlanStudentView` shows a `mydef` card with a pending-soft Fraunces date block + 4-col dashed-divider meta row when the student has a scheduled defense; shows an `empty-card` dashed-border otherwise. Legacy files deleted: `WeekCalendar`, `PresentationCard`, `CompactDayCard`, `ScheduleOverviewCalendar`, `DateSelectionCalendar`, `EmptyDayState`. `PresentationFormModal` is unchanged — deferred to Sub-J.
- **Sub-J PresentationFormModal redesign:** The legacy 501-LOC modal in `/dashboard/planificacion` was rewritten to match the Sub-F/G/H/I design system. Reuses the `.modal*` frame from Sub-I (overlay/dialog/head/body/foot), the `.agg-field*` form tokens from Sub-H, and the existing `Combobox` primitive for both the project picker and the jurado picker. Three numbered sections (01 Proyecto / 02 Tribunal / 03 Horario) match the `DocumentFormNew` rhythm. Project summary block uses `.pres-summary.is-pteg` or `.is-teg` tinted by `--accent-pteg-soft-*` / `--accent-teg-soft-*` brand tokens. Jurado picker uses a chip-stack pattern modelled on `AdvisorsChips` (capped at 3). All raw color classes (`text-gray-*`, `bg-black/40`, `bg-[#0f172a]`, etc.) replaced by semantic variables. Responsive ladder collapses agg-row-2 + modal footer at ≤ 520 px.
- **Sub-K Modal system unified:** Three modals in `/dashboard/planificacion` now share one shell — `.modal-band` with two variants (`band.read` navy gradient + dot-grid + diagonal yellow sweep for `DayDetailModal`; `band.edit` pteg-soft tinted + same diagonal sweep for `EditDayModal` + `PresentationFormModal`). Body uses Fraunces-numbered sections (`.section`, `.section-h`, `.section-num`, `.section-title-h`). `.modal-foot` standardized to `[foot-meta or btn.danger | foot-actions]`. New component `EditDayModal` fills the previously-stub `Editar día` action — saves notes/date via `updateDay`, deletes via `deleteDay`. `PresentationFormModal` now receives a `dayDate` prop so the band-sub shows the day context (e.g. "jueves 12 de marzo"). Old Sub-I `.modal-head/.modal-numblk/.modal-stats/.modal-prow/.notes-block` and Sub-J `.pres-summary*/.jurado-*` rules retired; renamed to `.read-stats/.read-stat`, `.notes`, `.proj-summary*`, `.jur-chips/.jur-chip/.jur-empty/.jur-add`. Form fields reuse Sub-H `.agg-field*` tokens; new `.field-help-soft` hint text token added. Buttons use new `.btn`, `.btn.ghost`, `.btn.primary`, `.btn.danger` primitives. `PlanAdminView` wired: `handleOpenEditDay` now sets `editDayTarget` state and opens `EditDayModal`; `PresentationFormModal` receives computed `dayDate` string.
- **Sub-L Filter + Timeline redesign:** `/dashboard/planificacion` presentation section rebuilt with two new components. `PresentationFilter` (`pf-*` CSS namespace) — tinted C4 ribbon with 4 zones (Buscar / Modalidad / Período / Resultados), vertical brand-colored stripes, modality chip counts via `countByModality`, period popover with per-option counts via `countForPeriod`, active-filter chip strip with per-chip × and "Limpiar todo". `PresentationTimeline` (`pt-*` CSS namespace) — vertical rail (`::before` gradient pteg→teg) connecting per-day markers (Fraunces numeral + dominant-modality border, today gets pulsing orange `.pulse-dot`). Pure helper module `applyPresentationFilters.ts` exports `applyPresentationFilters`, `countByModality`, `countForPeriod`, `isFiltersActive` with `PresentationFilters` / `PeriodFilter` / `DEFAULT_FILTERS`. `PlanAdminView` wired: filter state via `useState<PresentationFilters>`, `filteredDays` via `applyPresentationFilters`. `PlanReviewerView` wired: same pattern on top of `filterPresentationsForRole` output; role-based empty state preserved via `.empty-state` wrapper when `roleDays.length === 0`.
- **Sub-N Evaluation form redesign:** `EvaluationForm.tsx` refactored from paginated wizard to single-scroll editorial layout. Dropped page state; added `errorQId` validation banner (`.err-banner`), `findMissingGlobal()`, `handleJumpToMissing()`. Renders `.ev-hero` (eyebrow pill + Fraunces title + lede + 3-stat strip), sticky `.ribbon [.is-teg]` per section, global question numerals (01–N padded), and a right `<Rail>` component. `QuestionCard` gains `numeral: string` prop and semantic `.qcard*` CSS (`.qcard-header`, `.qcard-num font-display`, `.qcard-body`, `.qcard-label`, `.qcard-helper`, `.qcard-img-badge`, `.qcard-status` pill: Pendiente/Respondida/Falta). `Rail` built from stub: `.rail` aside with `.rail-grp [.is-teg]`, `.rail-grp-header`, `.rail-anchor [.active]`, `.rail-summary`, `.rail-draft [.saved/.saving]`. `MobileCategoryJumper` built from stub: `.m-jumper` with `.m-jumper-pill [.is-teg]` buttons, `.m-jumper-label`, `.m-jumper-count`. `StickyActionBar` rewritten with `errorMode` prop: normal → "Enviar evaluación"; error → "Saltar a falta". `ResultsSummary` rewritten with `.res-band` navy gradient, conic score widget (`.res-score` inline `conic-gradient`), per-section `.res-section [pteg-soft/teg-soft]`, `.res-q` answer rows with `[success-soft/danger-soft/neutral]` pills, comments callout (`.pending-soft`). All 5 input components rebuilt: `YesNoInput` → `.inp-seg.v-yesno` (active Sí = `success`, active No = `danger`); `FrequencyInput` → `.inp-seg` (`active blue`); `TernaryInput` → `.inp-seg` (`active blue`); `StarRatingInput` → `.inp-stars` (`active yellow`, no points display); `FreeTextInput` → `.inp-text` wrapper + `.inp-text-area` textarea (no score note). Sub-N CSS banner appended to `globals.css` covering all `.ev-*`, `.ribbon*`, `.qcard*`, `.inp-*`, `.rail*`, `.err-banner*`, `.res-*`, `.m-jumper*` namespaces with responsive breakpoints.
- **Sub-M Dashboard chrome redesign:** `Sidebar.tsx`, `DashboardHeader.tsx`, and two new extracted components (`Breadcrumb.tsx`, `ProfileMenu.tsx`) rewritten to match the Sub-F → Sub-L design system. The unifying device: same `navy → blue → yellow → orange` gradient runs vertically on the sidebar's right edge (`.sb::after`) and horizontally under the header (`.hd::after`), forming an L-shaped brand frame. Sidebar: `.sb-*` namespace; Fraunces logo mark + "Tesisfar" wordmark + "Gestión TEG" tag; items split into `Workspace` / `Operación` groups via `data-testid="sb-group-{name}"`; active item has `aria-current="page"` + `active` class + brand-blue→orange left stripe (`::before`); `Alt+N` keyboard shortcut chips (`.sb-item-kbd`); foot card with avatar + name + role (`sb-foot`, `sb-foot-ava`, `sb-foot-name`, `sb-foot-role`); `is-collapsed` class on root shrinks to 72 px with CSS-only tooltip via `data-label` + `::after`/`::before`. Mobile drawer: `role="dialog"` + GSAP slide-in + swipe-to-close. Header: `.hd-*` namespace; `pageTitle` prop now feeds `Breadcrumb` as the "now" segment — NOT rendered as a standalone `<h2>`; `Breadcrumb` has two variants: `expanded` (`.hd-crumb` text trail) and `collapsed` (`.hd-crumb-pill` segmented chip); profile chip (`.hd-prof`) toggles `ProfileMenu` (`.prof-pop`) which receives `email`, `role`, `onClose`, `onLogout` as props and handles ESC + outside-click closing internally. `ProfileMenu` band reuses the C4 pteg-soft gradient language (`.prof-band`). No legacy `text-slate-*`, `bg-slate-*`, `bg-primary/10` classes in any chrome file.

## Document Creation (Agregar)

- Modular architecture under `src/app/dashboard/agregar/`
- Zod schema + React Hook Form for validation (`agregar/schema.ts`)
- Custom hook `useDocumentData` for data fetching (students, tutors, semesters)
- Searchable Combobox for student/partner/tutor selection (portal-based, no overflow clipping)
- Skeleton loading state (`FormSkeleton`)
- AccessDenied component for Tutor/Jurado roles
- Semester period is read-only, set by the active semester from admin

## Semester System

- Semesters managed in `src/features/semesters/api/semesters.ts`
- Format: `YYYY-01` (first semester) or `YYYY-02` (second semester)
- Each semester has `start_month` and `end_month` fields (can span years, e.g., Sep 2026 – Jan 2027)
- Admin creates/activates semesters in Settings page
- Active semester auto-assigned to new projects

## Settings Page

- 3-column layout: vertical nav | main content | context panel
- Tabs: Perfil, Seguridad, Notificaciones, Administración
- Admin sub-tabs: Pendientes, Directorio, Semestres
- User management with UserModal (create/edit) and searchable user list
- Semester management with month range pickers and active semester toggle

## Styling Patterns

- Use Tailwind utilities inline
- For class composition: `clsx()` + `tailwind-merge` (via `cn()` from `@shared/lib/utils`)
- Custom theme colors defined as CSS variables in `globals.css`
- Primary palette: Navy (#011638), Blue (#0066ff), Orange (#ff6b35), Yellow (#ffd23f)
- Animation: GSAP for complex sequences, CSS keyframes for simple loops

## Key Files to Know

| File | Purpose |
|------|---------|
| `src/shared/api/api.ts` | HTTP client, CSRF handling |
| `src/features/auth/api/clientAuth.ts` | Auth + user management API calls (incl. `getTutors()` and `getJurados()`) |
| `src/features/auth/api/credentials.ts` | Session storage helpers |
| `src/features/projects/api/projectService.ts` | Project/evaluation/comment API calls (incl. `assignReviewer(id, reviewerId \| null)`) |
| `src/features/semesters/api/semesters.ts` | Semester CRUD + utilities |
| `src/widgets/sidebar/Sidebar.tsx` | Sub-M redesign: `.sb-*` namespace, role filtering, group titles (Workspace/Operación), foot card, collapsed tooltip, mobile GSAP drawer |
| `src/widgets/header/DashboardHeader.tsx` | Sub-M redesign: `.hd-*` namespace; `pageTitle` feeds `Breadcrumb` (not rendered as `<h2>`); profile chip toggles `ProfileMenu` |
| `src/widgets/header/Breadcrumb.tsx` | Sub-M new component: `expanded` variant (`.hd-crumb` text trail) \| `collapsed` variant (`.hd-crumb-pill` segmented chip) |
| `src/widgets/header/ProfileMenu.tsx` | Sub-M new component: `.prof-pop` dropdown; C4 pteg-soft band; 3 sections (Cuenta/Soporte/logout); ESC + outside-click close |
| `src/features/evaluations/components/EvaluationForm.tsx` | Sub-N redesign: single-scroll editorial layout; `.ev-hero`, `.ev-layout` grid, sticky ribbons, global numerals, `errorQId` validation banner, `<Rail>` right column |
| `src/features/evaluations/components/EvaluationSidebar.tsx` | Sticky sidebar with section progress (legacy, kept for compat) |
| `src/features/evaluations/components/QuestionCard.tsx` | Sub-N redesign: `.qcard*` semantic classes, `numeral` prop (Fraunces `.qcard-num`), status pill (Pendiente/Respondida/Falta) |
| `src/features/evaluations/components/Rail.tsx` | Sub-N new component: `.rail` aside with `.rail-grp [.is-teg]`, `.rail-anchor [.active]`, progress summary, draft save indicator |
| `src/features/evaluations/components/MobileCategoryJumper.tsx` | Sub-N new component: `.m-jumper` pill bar for mobile section navigation |
| `src/features/evaluations/components/StickyActionBar.tsx` | Sub-N redesign: `errorMode` prop switches CTA (Enviar evaluación ↔ Saltar a falta), Fraunces fraction, progress bar |
| `src/features/evaluations/components/ResultsSummary.tsx` | Sub-N redesign: `.res-band` navy gradient, conic score widget, per-section answer rows with colored pills |
| `src/features/evaluations/components/inputs/` | Sub-N redesign: YesNoInput (`.inp-seg.v-yesno`), FrequencyInput (`.inp-seg`), TernaryInput (`.inp-seg`), StarRatingInput (`.inp-stars`), FreeTextInput (`.inp-text`) — no points display |
| `src/app/dashboard/agregar/schema.ts` | Zod validation schema for document creation |
| `src/app/dashboard/agregar/hooks/useDocumentData.ts` | Data fetching hook for agregar page |
| `src/features/evaluations/lib/questions/questions.ts` | Evaluation question definitions |
| `src/features/evaluations/lib/questions/scoring.ts` | Score calculation |
| `src/features/projects/types/project.ts` | TypeScript interfaces (`Project` includes `reviewer?: number \| null`, `reviewerName?: string \| null`, and `state: ProjectState` for PTEG lifecycle) |
| `src/features/projects/api/projectService.ts` (ApiProject) | Extended to include `state` and `Evaluation.kind`. `createEvaluation` accepts `kind: 'review' \| 'defense'`. `overrideProjectState(id, {state, reason})` calls the admin-only override endpoint and returns the refreshed `Project`. |
| `src/features/projects/lib/stateConfig.ts` | Shared `STATE_CONFIG` (label + pill class) + `STATE_FALLBACK`, covering PTEG and TEG states. Consumed by `StateOverrideModal` and `StateOverrideHistory`. The redesigned list/detail pages use `StatePill` directly instead. |
| `src/features/projects/lib/stateBadge.ts` | Hybrid pill helper — maps `ProjectState` to `{tone, label}` (amber/green/red). Consumed by `ListRow` and `TrackingTable`. The detail page now uses `StatePill` directly. |
| `src/features/projects/lib/applyStateFilter.ts` | Pure helpers `applyStateFilter` and `readStateFromSearchParams` driving the `?state=<value>` filter on `/dashboard/proyectos`. |
| `src/features/projects/components/StateOverrideModal.tsx` | Admin-only modal that POSTs to `/api/projects/{id}/override_state/`. |
| `src/features/projects/components/StateOverrideHistory.tsx` | Read-only audit list for admins; returns `null` when `overrides === undefined` (non-admin response). |
| `src/features/projects/components/StatePill.tsx` | v5 single-word state badge. Single source of truth for state→variant mapping; feminine override for tesis. |
| `src/features/projects/components/StateFilter.tsx` | Dropdown filter trigger + popover for the list-page state filter (replaces the old chip row). |
| `src/features/projects/components/JuradoAssignModal.tsx` | Admin-only modal to assign/remove the project's reviewer. Loads jurados from `getJurados()`. |
| `src/features/projects/components/StudentReassignModal.tsx` | Admin-only modal to reassign the project's student (PTEG). |
| `src/features/projects/lib/cardAction.ts` | Pure helper: `(role, project, viewerId?) → {label, intent, href}`. Drives the foot-row action on every `ProjectCard` and the right-rail Evaluar CTA in `DetailHero`. |
| `src/features/projects/lib/buildStateTimeline.ts` | Pure helper that merges evaluations + state overrides + creation into a chronological `TimelineEvent[]`. |
| `src/shared/ui/ScoreGauge.tsx` | Circular conic-gradient score widget; sizes `sm\|md\|lg`, tones `primary\|success`. |
| `src/shared/ui/StateTimeline.tsx` | Renders a list of `TimelineEvent`s with color-coded dots + active pulse. |
| `src/features/projects/components/detail/` | Detail-page composition: `DetailHero` (hero + lifecycle ladder + sticky right rail), `DetailTabs` (URL-driven `?tab=`), `InfoTab`, `EvaluationsTab`, `CommentsTab`, `FilesTab`, `HistoryTab`. |
| `src/features/dashboard/components/Dashboard.tsx` | Sub-D layout: `DashboardHero` + 4-tile strip + 2-col list/feed lower zone. Computes `semesterDaysRemaining` / `todaysDeliveries` / `totalProjects` and feeds them into `buildDashboardContent`. |
| `src/features/dashboard/components/DashboardHero.tsx` | Editorial banner: eyebrow + greeting (gradient name) + lede + enriched `SemesterStrip`. Uses `dashboard-hero-bg` utility from `globals.css`. |
| `src/features/dashboard/lib/roleContent.ts` | Emits 4 `StatTileData` per role (hero + 3 secondary), plus optional `semesterStats` for the strip. Comentarios tile dropped — `Project.commentsCount` not in API. |
| `src/features/dashboard/lib/types.ts` | Adds `TileTone`, `ChipSegment`, `SemesterMiniStat`; extends `StatTileData` with `chips`/`urgent`; adds `DashboardContent.semesterStats?`. |
| `src/shared/ui/StatTile.tsx` | Tones: `primary`/`accent`/`hero`/`blue`/`orange`/`green`/`amber`. Optional `chips`, `urgent` (renders `pulse-soft` dot), `spanCols: 1\|2`. Hero tile has dot-grid + glow corner + bottom gradient line. |
| `src/shared/ui/SemesterStrip.tsx` | Card primitive: gradient top border, period + status pill (Activo/Próximo/Finalizado), optional `mainStats` mini-stats, animated progress bar with glow. |
| `src/shared/ui/ListRow.tsx` | Ring-style status indicator (8px dot with triple-ring shadow), breadcrumb subtitle parsing on ` · `, hover-revealed arrow. `type` prop kept for compat but no longer rendered. |
| `src/shared/ui/ActivityFeed.tsx` | Square 30×30 `rounded-[10px]` icon blocks, dashed dividers between items, tabular-nums on timestamps. |
| `src/shared/ui/DateCell.tsx` | 42×42 calendar mini-block (blue header band with Spanish month abbr + day number) — used in Jurado's defense list. |
| `src/app/globals.css` | Theme variables + custom animations + `pulse-soft` keyframe + `dashboard-hero-bg` utility (radial mesh + dot grid). + Seguimiento (Sub-G) classes (`.seg-table*`, `.tdot`, `.ladder*`, `.pgate*`, `.next-step`, `.seg-pill-summary`). + Agregar (Sub-H) classes (`.agg-tcard*`, `.agg-form*`, `.agg-section*`, `.agg-field*`, `.agg-row-2`, `.agg-dropzone*`, `.agg-file-list`, `.agg-fc-*`, `.agg-form-actions`, `.agg-btn*`, `.advisors-chips`, `.a-chip`, `.a-input-wrap`, `.agg-denied*`, `.period-chip*`, `.agg-tcards`, `.agg-tb-title`, `.ts-pill*`, `.agg-stack`, `.agg-sec-num/title/hint`, `.agg-form-h/sub`). + Planificación (Sub-I) classes (`.cal-toolbar`, `.cal-mode`, `.cal-nav`, `.cal-grid`, `.cal-dow`, `.cal-day`, `.cal-day.dim/.has-pteg/.has-teg/.has-both/.mine/.today/.selected`, `.cal-day .dotrow`, `.cal-legend`, `.plist`, `.pgroup-h`, `.prow`, `.ptime`, `.ptitle`, `.pmeta`, `.pactions`, `.daycard*`, `.modal-overlay`, `.modal`, `.modal-head`, `.modal-numblk`, `.modal-title-row`, `.modal-eyebrow`, `.modal-title`, `.modal-sub`, `.modal-close`, `.modal-body`, `.modal-section*`, `.modal-stats`, `.modal-stat`, `.modal-prow`, `.notes-block`, `.modal-foot`, `.mydef`, `.mydef-top`, `.mydef-num`, `.mydef-info`, `.mydef-eyebrow`, `.mydef-meta`, `.empty-state`, `.empty-card`). + Filter + Timeline (Sub-L) classes (`.pf-filter`, `.pf-zone`, `.pf-zone-search/.pf-zone-modality/.pf-zone-period/.pf-zone-result`, `.pf-search-input/.pf-search-clear/.pf-search-kbd`, `.pf-mod-chip/.pf-mod-chip.active/.pteg/.teg`, `.pf-period-trigger/.pf-period-trigger.open`, `.pf-period-popover/.pf-period-option`, `.pf-result-num/.pf-result-lbl`, `.pf-active-filters`, `.pf-af-chip/.pf-clear-all`, `.pt-card/.pt-head/.pt-body`, `.pt-day/.pt-marker/.pt-marker.pteg-day/.pt-marker.teg-day/.pt-marker.today`, `.pulse-dot`, `.pt-day-content/.pt-day-h`, `.pt-empty/.pt-loading`, `.spinner`). + Chrome (Sub-M) classes (`.sb`, `.sb::after`, `.sb-logo*`, `.sb-nav`, `.sb-group-title`, `.sb-item`, `.sb-item.active`, `.sb-item-icon/.sb-item-label/.sb-item-kbd`, `.sb-foot*`, `.sb.is-collapsed` + tooltip `::after`/`::before`, `.hd`, `.hd::after`, `.hd-left`, `.hd-collapse-btn`, `.hd-menu-btn`, `.hd-crumb*`, `.hd-crumb-pill*`, `.hd-actions`, `.hd-bell*`, `.hd-prof*`, `.prof-pop`, `@keyframes popIn`, `.prof-band*`, `.prof-sec*`, `.prof-item*`, `.prof-shortcut`). + Evaluation form (Sub-N) classes (`.ev-hero`, `.ev-hero-eyebrow`, `.ev-hero-pill`, `.ev-hero-title`, `.ev-hero-lede`, `.ev-hero-strip`, `.ev-hero-stat*`, `.ev-layout`, `.ev-feed`, `.ev-subsection`, `.ev-sub-title`, `.ev-questions`, `.ev-comments*`, `.ribbon`, `.ribbon.is-teg`, `.ribbon-info`, `.ribbon-label`, `.ribbon-desc`, `.ribbon-progress`, `.ribbon-frac`, `.qcard`, `.qcard.done`, `.qcard.error`, `.qcard-header`, `.qcard-num`, `.qcard-body`, `.qcard-label-row`, `.qcard-label`, `.qcard-helper`, `.qcard-img-badge`, `.qcard-status`, `.qcard-input`, `.inp-seg`, `.inp-seg.v-yesno`, `.inp-stars`, `.inp-text`, `.inp-text-area`, `.rail`, `.rail-grp`, `.rail-grp.is-teg`, `.rail-grp-header`, `.rail-grp-num`, `.rail-grp-label`, `.rail-grp-chip`, `.rail-anchor`, `.rail-anchor.active`, `.rail-dot`, `.rail-summary`, `.rail-summary-bar`, `.rail-draft`, `.rail-draft-dot`, `.err-banner`, `.err-banner-msg`, `.err-banner-jump`, `.res-wrap`, `.res-band`, `.res-score`, `.res-score-num`, `.res-band-info`, `.res-band-eyebrow`, `.res-band-title`, `.res-band-status`, `.res-body`, `.res-section`, `.res-sec-header`, `.res-sec-num`, `.res-sec-label`, `.res-sec-count`, `.res-q`, `.res-q-info`, `.res-q-label`, `.res-q-sub`, `.res-q-pill`, `.res-pill`, `.res-actions`, `.comments-callout`, `.m-jumper`, `.m-jumper-pill`, `.m-jumper-pill.is-teg`, `.m-jumper-label`, `.m-jumper-count`). |
| `src/features/projects/components/SeguimientoTable.tsx` | Role-aware Seguimiento table. Columns derived from `seguimientoColumnsFor(role)`. Renders `StatePill`, modality dot prefix (`.tdot.pteg` / `.tdot.teg`), inline 3-dot fase ladder (admin only), and a per-row action button driven by `cardAction()`. No avatars. Pagination footer inside the card. |
| `src/features/projects/components/MyProjectCard.tsx` | Estudiante's single-project card with 3 phase gates (Fraunces numerals on `.pgate .num`) and a "Próximo paso" callout. Gate labels and the detail-page CTA branch on `project.type` (PTEG: Revisión 1 / Reentrega / Defensa; TEG: Artículo / Entrega / Defensa). Callout is hidden when the project is in a terminal state. |
| `src/features/projects/lib/seguimientoColumns.ts` | Pure helper `seguimientoColumnsFor(role): SeguimientoColumnKey[]` mapping each role to its visible column set. Returns `[]` for Estudiante — a signal to the page to render the card view instead of the table. |
| `src/app/dashboard/agregar/components/DocumentTypeSelector.tsx` | Sub-H type selector. Both PTEG/TEG cards always render with Fraunces "9°"/"10°" numerals; non-allowed cards receive `.locked` + `aria-disabled="true"`. Driven by `--accent-pteg-soft-*` / `--accent-teg-soft-*` brand tokens. |
| `src/app/dashboard/agregar/components/AdvisorsChips.tsx` | Replaces `AdvisorsFieldArray`. Chip stack + single `Combobox` + "Añadir" button; preserves the 2-tutor cap and `advisors: (number \| "")[]` schema contract. |
| `src/app/dashboard/agregar/components/DocumentFormNew.tsx` | Sectioned form card: 3 sections for admin (Identificación / Equipo / Archivos), 2 for estudiante (Información / Archivo). All `agg-*` classes; no raw color classes. Uses `AdvisorsChips` and the rebuilt `DocumentTypeSelector`. |
| `src/app/dashboard/agregar/components/AccessDenied.tsx` | Sub-H polished fallback for direct URL hits by Tutor/Jurado. Fraunces title, `pending-soft` shield, two CTAs: Volver button + `<Link href="/dashboard/tracking">` for "Ir a Seguimiento". |
| `src/features/planificacion/components/UnifiedCalendar.tsx` | Sub-I unified month calendar. `mode: "view" \| "create"` prop. View: day cells tinted by `.has-pteg`/`.has-teg`/`.has-both`, dot row, mine highlight. Create (admin only): selectable cells (`.selected`), range + individual sub-modes, "Crear N días" CTA. Mode toggle hidden when `allowCreate={false}`. |
| `src/features/planificacion/components/DayDetailModal.tsx` | Sub-K day detail modal. `.modal-band.read` navy gradient band with Fraunces numeral block (`band-numblk .m/.d/.dow`) + `band-eyebrow`/`band-title`/`band-sub`. Body: `read-stats` strip (Inicio/Cierre/Duración) + section 01 Agenda (`.prow` rows with `.tdot`/`.spill`) + section 02 Notas (`.notes`/`.notes.empty`). Footer: `.foot-meta` (clock icon + creation info) + `.foot-actions` (Editar día ghost + Añadir presentación primary, admin only). Closes on ✕, overlay click, ESC. |
| `src/features/planificacion/components/EditDayModal.tsx` | Sub-K new form modal. `.modal-band.edit` pteg-soft band with gradient icon badge. Body: section 01 Fecha (date input + `.field-help-soft`) + section 02 Notas (textarea). Footer: `.btn.danger` Eliminar día (left) + Cancelar ghost + Guardar primary (right). Saves via `updateDay(id, {date, notes})`, deletes via `deleteDay(id)`. ESC + overlay click close. |
| `src/features/planificacion/components/PresentationRow.tsx` | Sub-I row component: 3-col grid (`.ptime` / `.ptitle` + dot + pill / `.pactions`). Role-aware actions: admin gets aria-label edit/delete icon buttons; tutor/jurado get arrow + `.spill.you` chip for owned rows. |
| `src/features/planificacion/lib/applyPresentationFilters.ts` | Sub-L pure helpers: `applyPresentationFilters(days, filters, now?)`, `countByModality(days)`, `countForPeriod(days, period, now?)`, `isFiltersActive(filters)`. Exports `PresentationFilters`, `PeriodFilter`, `DEFAULT_FILTERS`. |
| `src/features/planificacion/components/PresentationFilter.tsx` | Sub-L filter bar (Variant G refined). `pf-*` CSS namespace. 4 zones: search (role=searchbox), modality chips with counts, period popover, result numeral (Fraunces). Active-filters strip with per-chip × and Limpiar todo. Parent-driven via `filters` + `onChange` props. |
| `src/features/planificacion/components/PresentationTimeline.tsx` | Sub-L timeline card (Variant B). `pt-*` CSS namespace. Vertical rail via `::before`. Per-day: `.pt-marker` (dominant-modality border, today=`.pulse-dot`), `.pt-day-content` with `PresentationRow` stack. Sorted ascending by date. |
| `src/features/planificacion/components/DayCard.tsx` | Sub-I compact day card for admin authoring grid. Fraunces `.daycard-numblk .n` + `.dow` + `.my` + `.daycard-cnt` count chip + `.daycard-list` of time items. Click → `onDayClick`. |
| `src/features/planificacion/components/PlanAdminView.tsx` | Sub-I Administrador view: editorial hero + filter bar + 2-col calendar/presentations grid + day management section. All presentation days rendered without client-side filtering. |
| `src/features/planificacion/components/PlanReviewerView.tsx` | Sub-I Tutor + Jurado view: editorial hero + 2-col calendar (mine highlights only) / presentation list filtered by `filterPresentationsForRole`. |
| `src/features/planificacion/components/PlanStudentView.tsx` | Sub-I Estudiante view: editorial hero + `mydef` card when scheduled, `empty-card` otherwise. `mydef` card renders Fraunces pending-soft date block + 4-col dashed meta (Hora / Tutor / Jurado / Modalidad) + `next-step` callout. |
| `src/features/planificacion/lib/roleView.ts` | Pure helper `planificacionRoleView(role, viewerId?) → "admin" \| "reviewer" \| "student"`. |
| `src/features/planificacion/lib/filterForRole.ts` | Pure helper `filterPresentationsForRole(days, role, {viewerId?, viewerEmail?}) → PresentationDay[]`. Admin: all; Tutor: days where tutor===viewerId; Jurado: days where viewerId in jurado[]; Estudiante: at most one day matching student_email. |
| `src/features/planificacion/components/PresentationFormModal.tsx` | Sub-K rewritten modal. `.modal-band.edit` band. Props: `isOpen`, `dayId`, `editTarget?`, `dayDate?`, `onClose`, `onSave`. Three sections: 01 Proyecto (`Combobox` + `.proj-summary.pteg/.teg`) / 02 Tribunal (`.jur-empty`/`.jur-chips`/`.jur-chip`/`.jur-add`, cap 3) / 03 Horario (`.row-2` time + duration). Footer: `.foot-meta` (info icon + "Auto-asigna tutor") + Cancelar + Guardar. Loading spinner while data fetches. |

## Known Limitations

- Vitest is configured (`vitest.config.ts`) — small test suite under `tests/` (structure, prefetch hygiene, api timing). No Cypress / Playwright e2e yet.
- `@supabase/supabase-js` is in dependencies but not used for auth (Django handles it)
- No error boundaries for React error handling
- No i18n setup (UI text is hardcoded in Spanish)
- `src/app/modules/` is vestigial dead code — pending deletion (see task 005 follow-ups)
