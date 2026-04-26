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
| `src/widgets/sidebar/Sidebar.tsx` | Navigation with role filtering |
| `src/features/evaluations/components/EvaluationForm.tsx` | Evaluation form orchestrator |
| `src/features/evaluations/components/EvaluationSidebar.tsx` | Sticky sidebar with section progress |
| `src/features/evaluations/components/QuestionCard.tsx` | Single question wrapper with input dispatch |
| `src/features/evaluations/components/StickyActionBar.tsx` | Sticky bottom navigation/submit bar |
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
| `src/app/globals.css` | Theme variables + custom animations + `pulse-soft` keyframe + `dashboard-hero-bg` utility (radial mesh + dot grid). |

## Known Limitations

- Vitest is configured (`vitest.config.ts`) — small test suite under `tests/` (structure, prefetch hygiene, api timing). No Cypress / Playwright e2e yet.
- `@supabase/supabase-js` is in dependencies but not used for auth (Django handles it)
- No error boundaries for React error handling
- No i18n setup (UI text is hardcoded in Spanish)
- `src/app/modules/` is vestigial dead code — pending deletion (see task 005 follow-ups)
