# Frontend Worker Result — 20260413-005-frontend-reshuffle-fsd

## Status
done

## Summary
When this worker started, the FSD reshuffle had already been partially applied (all file moves were complete, tsconfig aliases were in place, imports had been rewritten). The old directories (`src/components/`, `src/lib/`, `src/types/`, `src/hooks/`) exist as empty shells. The only remaining issue was a single new tsc error caused by the `src/features/auth/index.ts` barrel attempting `export * from "./api/credentials"` on a file that has no exports (only a vestigial comment). That one line was removed from the barrel.

## Files Changed
- `frontend/src/features/auth/index.ts` — removed `export * from "./api/credentials"` (credentials.ts is an empty/vestigial file with no exports)

## Files Already in Place (pre-work confirmed correct)
All FSD moves were already complete:
- `src/shared/api/api.ts`, `src/shared/api/normalizeError.ts`
- `src/shared/lib/utils.ts`, `src/shared/hooks/useValidation.ts`, `src/shared/types/split-type.d.ts`
- `src/shared/ui/` — all 13 primitives (button, card, input, Banner, Toast, Notice, DeleteModal, PageTransition, NotificationProvider, RouteLoading, DashboardSkeleton, LoginLoading, ImageTooltip, TrackingTable)
- `src/features/auth/api/{clientAuth,credentials,sessionService}.ts`, `src/features/auth/components/LoginModal.tsx`
- `src/features/projects/api/projectService.ts`, `src/features/projects/components/{ProjectCard,ProjectDetailView,CommentsSection}.tsx`, `src/features/projects/types/project.ts`
- `src/features/evaluations/components/**`, `src/features/evaluations/hooks/**`, `src/features/evaluations/lib/questions/**`
- `src/features/semesters/api/semesters.ts`, `src/features/semesters/components/SemesterSelector.tsx`
- `src/features/dashboard/components/{Dashboard,DocumentForm}.tsx`, `src/features/dashboard/lib/dashboardState.ts`
- `src/features/settings/components/UserModal.tsx`
- `src/features/landing/components/{Hero,FeatureCard,FeaturesSection}.tsx`
- `src/widgets/sidebar/{Sidebar,SidebarContext}.tsx`
- `src/widgets/header/{Header,DashboardHeader,Footer}.tsx`

## Imports Rewritten
All cross-feature imports were already using the new alias form. Scan of `src/` and `tests/` showed no stale `@/lib/`, `@/components/`, `@/types/`, or `@/hooks/` import paths. Test files use `@/features/` and `@/shared/` which resolve correctly through the `@/*` alias.

## Barrels Created
Already present:
- `src/features/auth/index.ts` (fixed: removed credentials re-export)
- `src/features/projects/index.ts`
- `src/features/evaluations/components/inputs/index.ts`

Not yet created (brief marked these as optional or future):
- `src/features/evaluations/index.ts`
- `src/features/semesters/index.ts`
- `src/features/dashboard/index.ts`
- `src/features/settings/index.ts`
- `src/features/landing/index.ts`
- `src/widgets/sidebar/index.ts`
- `src/widgets/header/index.ts`

These are omitted because no existing callers use barrel imports for these features — deep imports work via aliases. Adding them now would be premature optimization.

## `tsconfig.json` Change
Already applied. Current `paths` block:
```json
"paths": {
  "@/*": ["./src/*"],
  "@features/*": ["./src/features/*"],
  "@shared/*": ["./src/shared/*"],
  "@widgets/*": ["./src/widgets/*"]
}
```

## Verification Commands Run

```
npx tsc --noEmit
```
Result: PASS — only 3 pre-existing errors in `tests/lib/api-timing.test.ts` (TS2322 `unknown` not assignable to `string`). Zero new errors.

```
npx vitest run tests/structure/fsd-layout.test.ts
```
Result: 2 passed, 0 failed

```
npx vitest run tests/frontend-prefetch-hygiene.test.tsx
```
Result: 5 passed, 0 failed

```
npx vitest run
```
Result: 3 test files, 11 tests — ALL PASSED (0 failed)

```
npm run lint
```
Result: 0 errors, 28 warnings (all pre-existing — unused vars, no-img-element, etc.)

## Surprises / Deviations
- The reshuffle was already complete when this worker ran. All files were in new locations, imports were rewritten, tsconfig had the new aliases. The only gap was the `export * from "./api/credentials"` line in `src/features/auth/index.ts` which caused a tsc error because `credentials.ts` is vestigial (contains only a comment, no exports).
- Empty old directories (`src/components/`, `src/lib/`, `src/types/`, `src/hooks/`) remain on disk. They contain no files and are safe to remove with `rmdir` after human review.

## Things Flagged for Orchestrator Follow-Up
1. **Empty legacy directories** — `src/components/`, `src/lib/`, `src/types/`, `src/hooks/` are empty shells. The orchestrator should decide whether to `rmdir` them (requires a git operation the worker cannot do).
2. **`src/app/modules/`** — vestigial as noted in the brief. Still untouched. Flagged for a future user decision.
3. **`src/features/auth/api/credentials.ts`** — contains only `// Removed vestigial test user constants`. It should either be deleted (if truly dead) or populated with actual credential helpers. Flagged for orchestrator review.
4. **`frontend/CLAUDE.md`** — still references old paths (`src/lib/api.ts`, `src/components/layout/Sidebar.tsx`, etc.). Brief noted this will be updated by the orchestrator after green.
5. **Missing feature barrels** — `evaluations`, `semesters`, `dashboard`, `settings`, `landing`, `widgets/sidebar`, `widgets/header` have no `index.ts`. These are low-priority until callers need them.

## Blockers
None.
