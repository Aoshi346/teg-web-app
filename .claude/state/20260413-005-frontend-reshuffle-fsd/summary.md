# Task 005 — Frontend Reshuffle (FSD) — Summary

## Status
**Green modulo a pre-existing build issue** in vestigial `src/app/modules/` that is unrelated to this task.

## What changed

Frontend `src/` reorganized into Feature-Sliced Design lite layout.

### New top-level structure

- `src/app/` — Next.js routes (unchanged location, imports rewritten)
- `src/features/{auth,projects,evaluations,semesters,dashboard,settings,landing}/` — feature modules with `api/`, `components/`, `hooks/`, `lib/`, `types/` subfolders
- `src/widgets/{sidebar,header}/` — cross-feature layout chrome
- `src/shared/{api,ui,lib,hooks,types}/` — primitives and infra

### Path aliases added to `tsconfig.json`
- `@features/*` → `src/features/*`
- `@widgets/*` → `src/widgets/*`
- `@shared/*` → `src/shared/*`
- `@/*` (legacy) preserved.

### Files moved
~104 files. `git mv` used to preserve blame. No symbol renames, no behavior changes, no body edits.

### Empty legacy directories
`src/components/`, `src/lib/`, `src/types/`, `src/hooks/` are now empty shells. Should be removed in the next commit.

## Verification

| Check                                                   | Result                                                   |
|---------------------------------------------------------|----------------------------------------------------------|
| `npx vitest run tests/structure/fsd-layout.test.ts`     | 2/2 passed (RED → GREEN)                                 |
| `npx vitest run tests/frontend-prefetch-hygiene...`     | 5/5 passed (task 004 regression check)                   |
| `npx vitest run` (full suite)                           | 11/11 passed                                             |
| `npx tsc --noEmit`                                      | 3 pre-existing errors only (in `tests/lib/api-timing.test.ts`) — zero new errors |
| `npm run lint`                                          | 0 errors, 28 warnings (matches baseline)                 |
| `npm run build` (webpack)                               | **FAIL** in `src/app/modules/selected/page.tsx` (pre-existing — vestigial dir) |

## Documentation updates

- [.claude/agents/frontend-worker.md](.claude/agents/frontend-worker.md) — new "Project Layout" section, alias table, "When You Add a New Component" decision tree, all internal references updated to new paths.
- [frontend/CLAUDE.md](frontend/CLAUDE.md) — Architecture, Project Layout, Code Conventions, Key Files table, Authentication / Evaluation / Semester / Styling sections all updated. `npm run dev` description updated to reflect Webpack-default decision from task 004.

## Things flagged for human follow-up

1. **`src/app/modules/` is dead code** (Dashboard.tsx 533 lines, Sidebar.tsx 184 lines, page.tsx 10 lines, selected/page.tsx 27 lines, menu.ts 10 lines). Single git history entry: `a3d03b7 chore: move existing frontend code to frontend/ directory`. Never touched since. It duplicates the real Dashboard (now `@features/dashboard/components/Dashboard.tsx`) and Sidebar (now `@widgets/sidebar/Sidebar.tsx`). It is also the **only thing blocking `npm run build`** — `selected/page.tsx` calls `useSearchParams()` without a `<Suspense>` boundary.
   **Recommendation:** delete the entire `src/app/modules/` directory. Build will pass after deletion. If you'd rather keep it, wrap the `useSearchParams()` call in a `<Suspense>`.

2. **Empty legacy directory shells** — `git rm -r src/components src/lib src/types src/hooks` after deciding on `modules/`.

3. **`src/features/auth/api/credentials.ts`** is vestigial — only contains a comment, no exports. Either delete it or populate it.

4. **3 pre-existing `tsc` errors** in `tests/lib/api-timing.test.ts` (carry-over from task 004). Each is `Type 'unknown' is not assignable to type 'string'` on `infoSpy.mock.calls[0][0]`. Trivial to fix (`as string` or change the type annotation), but out of scope for this task.

5. **Feature barrels not yet created** for `evaluations`, `semesters`, `dashboard`, `settings`, `landing`, `widgets/sidebar`, `widgets/header` — there are no callers needing them yet. Add them when the first cross-feature import would benefit.

## Next step ("check some behavior and functions" pass)

The reshuffle is the prerequisite for the behavior-audit pass you mentioned. With responsibilities now co-located by feature, that audit can go feature-by-feature instead of grep-ping flat directories. Suggested order: `auth` → `projects` → `evaluations` → `semesters` → `dashboard`/`settings`. We should write a brief for it as task 006 once you confirm the build-fix decision above.

## Git status

Worker did NOT run `git add`/`git commit`. All changes are unstaged. You'll see ~104 `R`/`RM` entries in `git status`, plus modified `tsconfig.json`, modified `frontend/CLAUDE.md`, modified `.claude/agents/frontend-worker.md`, and a new `tests/structure/fsd-layout.test.ts`.
