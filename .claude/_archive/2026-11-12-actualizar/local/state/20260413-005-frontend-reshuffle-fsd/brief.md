# Task 005 — Frontend Folder Reshuffle (Feature-Sliced Design lite)

## Goal

Reorganize `frontend/src/` into a clear, modular, feature-first layout so that:
- Each feature owns its own components, hooks, API calls, and types.
- Shared UI primitives and infra live in one obvious place (`shared/`).
- Next.js routes in `app/` become thin — they import from features, not the other way around.
- Zero runtime behavior change. This is a mechanical reshuffle + import rewrite only.
- "Check some behavior and functions" pass (task 006) becomes easier because responsibilities are co-located.

**Out of scope:** introducing domain/use-case/repository layers, DTOs, dependency injection, rewriting any component, changing routes, touching the backend.

## Target layout

```
frontend/src/
  app/                          # Next.js App Router (routes only)
    layout.tsx
    page.tsx                    # landing
    dashboard/
      layout.tsx
      page.tsx
      proyectos/...              # thin pages that import from features/
      tesis/...
      agregar/page.tsx
      settings/page.tsx
      tracking/page.tsx
      scan/layout.tsx

  features/
    auth/
      api/                       # clientAuth.ts, credentials.ts, sessionService.ts
      components/                # LoginModal.tsx
      index.ts                   # public barrel
    projects/
      api/                       # projectService.ts
      components/                # ProjectCard, ProjectDetailView, CommentsSection
      types/                     # project.ts
      index.ts
    evaluations/
      components/                # EvaluationForm, EvaluationSidebar, QuestionCard, StickyActionBar, ResultsSummary, inputs/
      hooks/                     # useEvaluationDraft, useScrollSpy, useEvaluationSubmit
      lib/                       # questions/, scoring
      index.ts
    semesters/
      api/                       # semesters.ts
      components/                # SemesterSelector
      index.ts
    dashboard/                   # dashboard-specific widgets (not routes)
      components/                # Dashboard.tsx, DocumentForm.tsx
      lib/                       # dashboardState.ts
      index.ts
    settings/
      components/                # UserModal
      index.ts
    landing/
      components/                # Hero, FeatureCard, FeaturesSection
      index.ts

  widgets/                       # cross-feature layout composites
    sidebar/                     # Sidebar.tsx, SidebarContext.tsx
    header/                      # Header.tsx, DashboardHeader.tsx, Footer.tsx

  shared/
    api/                         # api.ts (http client), normalizeError.ts
    ui/                          # button, card, input, Banner, Toast, Notice, DeleteModal,
                                 #   PageTransition, NotificationProvider, RouteLoading,
                                 #   DashboardSkeleton, LoginLoading, ImageTooltip, TrackingTable
    lib/                         # utils.ts (cn helper)
    hooks/                       # useValidation
    types/                       # split-type.d.ts
```

## Path aliases (tsconfig.json)

Add alongside existing `@/*`:

```json
"paths": {
  "@/*": ["./src/*"],
  "@features/*": ["./src/features/*"],
  "@shared/*": ["./src/shared/*"],
  "@widgets/*": ["./src/widgets/*"]
}
```

Existing `@/*` imports keep working — the reshuffle only rewrites them where the file moved.

## File-move map (authoritative)

| Current path                                                   | New path                                                   |
|----------------------------------------------------------------|------------------------------------------------------------|
| `src/features/auth/clientAuth.ts`                              | `src/features/auth/api/clientAuth.ts`                      |
| `src/features/auth/credentials.ts`                             | `src/features/auth/api/credentials.ts`                     |
| `src/features/auth/sessionService.ts`                          | `src/features/auth/api/sessionService.ts`                  |
| `src/components/auth/LoginModal.tsx`                           | `src/features/auth/components/LoginModal.tsx`              |
| `src/features/projects/projectService.ts`                      | `src/features/projects/api/projectService.ts`              |
| `src/components/dashboard/ProjectCard.tsx`                     | `src/features/projects/components/ProjectCard.tsx`         |
| `src/components/dashboard/ProjectDetailView.tsx`               | `src/features/projects/components/ProjectDetailView.tsx`   |
| `src/components/dashboard/CommentsSection.tsx`                 | `src/features/projects/components/CommentsSection.tsx`     |
| `src/types/project.ts`                                         | `src/features/projects/types/project.ts`                   |
| `src/components/evaluation/**`                                 | `src/features/evaluations/components/**`                   |
| `src/lib/questions/**`                                         | `src/features/evaluations/lib/questions/**`                |
| `src/lib/semesters.ts`                                         | `src/features/semesters/api/semesters.ts`                  |
| `src/components/ui/SemesterSelector.tsx`                       | `src/features/semesters/components/SemesterSelector.tsx`   |
| `src/components/dashboard/Dashboard.tsx`                       | `src/features/dashboard/components/Dashboard.tsx`          |
| `src/components/dashboard/DocumentForm.tsx`                    | `src/features/dashboard/components/DocumentForm.tsx`       |
| `src/lib/dashboardState.ts`                                    | `src/features/dashboard/lib/dashboardState.ts`             |
| `src/components/ui/UserModal.tsx`                              | `src/features/settings/components/UserModal.tsx`           |
| `src/components/landing/**`                                    | `src/features/landing/components/**`                       |
| `src/components/layout/Sidebar.tsx`                            | `src/widgets/sidebar/Sidebar.tsx`                          |
| `src/components/layout/SidebarContext.tsx`                     | `src/widgets/sidebar/SidebarContext.tsx`                   |
| `src/components/layout/Header.tsx`                             | `src/widgets/header/Header.tsx`                            |
| `src/components/layout/DashboardHeader.tsx`                    | `src/widgets/header/DashboardHeader.tsx`                   |
| `src/components/layout/Footer.tsx`                             | `src/widgets/header/Footer.tsx`                            |
| `src/lib/api.ts`                                               | `src/shared/api/api.ts`                                    |
| `src/lib/normalizeError.ts`                                    | `src/shared/api/normalizeError.ts`                         |
| `src/lib/utils.ts`                                             | `src/shared/lib/utils.ts`                                  |
| `src/hooks/useValidation.ts`                                   | `src/shared/hooks/useValidation.ts`                        |
| `src/types/split-type.d.ts`                                    | `src/shared/types/split-type.d.ts`                         |
| `src/components/ui/{button,card,input,Banner,Toast,Notice,DeleteModal,PageTransition,NotificationProvider,RouteLoading,DashboardSkeleton,LoginLoading,ImageTooltip,TrackingTable}.tsx` | `src/shared/ui/<same>.tsx` |

`src/app/**` pages are **not moved** — only their import paths get rewritten.

## Items flagged for user decision (NOT moved in this task)

- `src/app/modules/` — contains `Dashboard.tsx`, `Sidebar.tsx`, `menu.ts`, `page.tsx`, `selected/page.tsx`. Looks vestigial/dead. **Do not touch** in this task. After reshuffle completes, I'll ask if it should be deleted.
- Dashboard `agregar/hooks/` and `agregar/components/` — these are page-local and stay inside the route directory. They can migrate to `features/documents/` in a future pass if needed.

## Decomposition

### Phase 1 — RED (test-worker)
Write a boundary/typecheck smoke test that will fail until imports are rewritten:
1. `frontend/tests/structure/fsd-layout.test.ts` — asserts the target directories exist and that certain canonical files live in the new location (e.g. `src/shared/api/api.ts`, `src/features/projects/api/projectService.ts`). Uses `fs.existsSync`. Expected to FAIL now (files still in old location).
2. Record the current `tsc --noEmit` pass/fail state and current `vitest run` pass count as a baseline in the result file.

### Phase 2 — IMPL (frontend-worker)
1. Create new directories.
2. Move files per the map using `git mv` (preserves blame). Worker runs `git mv` but does NOT commit.
3. Update `tsconfig.json` to add `@features/*`, `@shared/*`, `@widgets/*` aliases.
4. Rewrite imports project-wide. Approach:
   - Use grep to find every import of a moved file and rewrite it to the new path.
   - Prefer the new alias form (`@features/auth/api/clientAuth`) over relative paths in `app/` and cross-feature imports.
   - Within a single feature, relative imports (`./components/X`) are fine.
5. Add `index.ts` barrels for each feature exporting its public surface (components + types + api functions actually consumed from outside the feature).
6. Do NOT rename any symbol, do NOT change any component body, do NOT delete any file.

### Phase 3 — GREEN (test-worker)
1. Run `npx tsc --noEmit` → must pass with zero errors.
2. Run `npm run lint` → must pass (or match pre-reshuffle error count).
3. Run `npm run test:run` (vitest) → all existing tests pass + the new structure test passes.
4. Run `npm run build` (webpack) to catch anything tsc missed. Optional but recommended.
5. Document pass/fail in result file with exact counts.

## Artifacts

- **Reads:** every file under `frontend/src/`, `frontend/tsconfig.json`, `frontend/package.json`.
- **Writes:**
  - `frontend/src/**` (moves + import rewrites)
  - `frontend/tsconfig.json` (alias additions)
  - `frontend/tests/structure/fsd-layout.test.ts` (new)
  - `.claude/state/20260413-005-frontend-reshuffle-fsd/test-worker-result.md`
  - `.claude/state/20260413-005-frontend-reshuffle-fsd/frontend-worker-result.md`
  - `.claude/state/20260413-005-frontend-reshuffle-fsd/summary.md`

## Verification

- `npx tsc --noEmit` → 0 errors
- `npm run test:run` → all green (new structure test + existing tests)
- `npm run lint` → no new errors vs. pre-reshuffle
- `npm run build` (webpack) → completes without error
- Manual: `./start.sh` → dev server boots, dashboard loads, one route transition works

## Risks

1. **Import rewrite misses** — ~100 files. Mitigation: grep-based find-and-replace, tsc catches remaining.
2. **Circular imports** after barrels — `index.ts` files can create cycles if feature A imports feature B's barrel and vice versa. Mitigation: keep barrels minimal; prefer deep imports for cross-feature usage.
3. **Next.js App Router quirks** — `page.tsx` / `layout.tsx` files MUST stay under `src/app/`. We are not moving them. Only their imports get rewritten.
4. **`git mv` vs. plain move** — worker must use `git mv` so blame history survives. If worker forgets, history breaks.
5. **Vestigial `src/app/modules/`** — untouched, flagged for later user decision.
6. **The hover-prefetch + no-mount-prefetch behavior** from task 004 must survive — the file moves preserve content, but test-worker should re-run `frontend-prefetch-hygiene.test.tsx` in the green phase to confirm.
7. **`agregar/hooks/useDocumentData`** — page-local, stays put, but its imports of `api.ts` / `projectService.ts` will change.

## Agent file updates

After the checkpoint (before Phase 1), I'll update `.claude/agents/frontend-worker.md` to document the new layout conventions so future workers know:
- where to add new components (feature folder, not `src/components/`)
- when to use `@features/*` alias vs. relative import
- the public-barrel pattern

## Plan summary

1. Orchestrator: update `.claude/agents/frontend-worker.md` + `frontend/CLAUDE.md` with new layout (after approval).
2. test-worker (RED): write structure test + record baseline.
3. frontend-worker (IMPL): `git mv` files, add aliases, rewrite imports, add barrels.
4. test-worker (GREEN): tsc + vitest + lint + build.
5. Orchestrator: write summary, report to human, flag `src/app/modules/` for follow-up.
