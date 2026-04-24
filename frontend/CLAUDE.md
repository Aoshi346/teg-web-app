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
- PTEG evaluation page (`/dashboard/proyectos/[id]/evaluar`) shows a Revisión / Defensa oral segmented control gated by `Project.state`. Terminal states hide the form entirely. The TEG evaluation page (`/dashboard/tesis/[id]/evaluar`) is unchanged — it retains the `stage1_passed` toggle.
- **Admin state override (PTEG):** `ProjectDetailView` shows a "Forzar estado" pill for `Administrador` on PTEG projects, next to the state badge. Opens `StateOverrideModal` (target state + reason ≥10 chars), calls `overrideProjectState(id, {state, reason})`. Past overrides render in `StateOverrideHistory` below the evaluations list. The history section is hidden entirely when `project.stateOverrides` is undefined (non-admin response — backend omits the field for non-admins).
- **Admin dashboard PTEG tile** shows clickable state-count chips via `StatTileData.segments` that deep-link to `/dashboard/proyectos?state=<value>`. The projects list page reads `?state=` via `applyStateFilter` helper and shows a "Filtrado por: {label} ✕" clear pill. Non-admin tiles keep the existing `breakdown` string shape.

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
| `src/features/projects/lib/ptegStateConfig.ts` | Shared `PTEG_STATE_CONFIG` (label + pill class) + `PTEG_STATE_FALLBACK`. Consumed by `ProjectDetailView`, `StateOverrideModal`, `StateOverrideHistory`, and the projects list filter pill. |
| `src/features/projects/lib/applyStateFilter.ts` | Pure helpers `applyStateFilter` and `readStateFromSearchParams` driving the `?state=<value>` filter on `/dashboard/proyectos`. |
| `src/features/projects/components/StateOverrideModal.tsx` | Admin-only modal that POSTs to `/api/projects/{id}/override_state/`. |
| `src/features/projects/components/StateOverrideHistory.tsx` | Read-only audit list for admins; returns `null` when `overrides === undefined` (non-admin response). |
| `src/app/globals.css` | Theme variables + custom animations |

## Known Limitations

- Vitest is configured (`vitest.config.ts`) — small test suite under `tests/` (structure, prefetch hygiene, api timing). No Cypress / Playwright e2e yet.
- `@supabase/supabase-js` is in dependencies but not used for auth (Django handles it)
- No error boundaries for React error handling
- No i18n setup (UI text is hardcoded in Spanish)
- `src/app/modules/` is vestigial dead code — pending deletion (see task 005 follow-ups)
