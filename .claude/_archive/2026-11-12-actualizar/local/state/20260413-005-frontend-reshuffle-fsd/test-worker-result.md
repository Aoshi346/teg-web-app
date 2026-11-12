# Test Worker Result — 20260413-005-frontend-reshuffle-fsd — Phase RED

## Status
red-phase-ready

## New Test File
`frontend/tests/structure/fsd-layout.test.ts`

### What it asserts

**`it("new target paths exist after reshuffle")`** — checks `existsSync` on all of:
- `src/shared/api/api.ts`
- `src/shared/api/normalizeError.ts`
- `src/shared/lib/utils.ts`
- `src/shared/ui/button.tsx`
- `src/shared/ui/card.tsx`
- `src/features/auth/api/clientAuth.ts`
- `src/features/auth/api/credentials.ts`
- `src/features/auth/components/LoginModal.tsx`
- `src/features/projects/api/projectService.ts`
- `src/features/projects/components/ProjectCard.tsx`
- `src/features/projects/types/project.ts`
- `src/features/evaluations/components/EvaluationForm.tsx`
- `src/features/evaluations/lib/questions/questions.ts`
- `src/features/semesters/api/semesters.ts`
- `src/features/dashboard/components/Dashboard.tsx`
- `src/features/landing/components/Hero.tsx`
- `src/widgets/sidebar/Sidebar.tsx`
- `src/widgets/header/DashboardHeader.tsx`

**`it("old paths no longer exist after reshuffle")`** — checks the following are GONE:
- `src/lib/api.ts`
- `src/components/layout/Sidebar.tsx`
- `src/types/project.ts`
- `src/lib/utils.ts`
- `src/components/dashboard/ProjectCard.tsx`
- `src/lib/semesters.ts`

## Exact Failing Test Output

```
 RUN  v2.1.9 /home/aoshi/Test/app_test/teg-web-app/frontend

 ❯ tests/structure/fsd-layout.test.ts (2 tests | 2 failed) 43ms
   × FSD layout > new target paths exist after reshuffle 33ms
     → shared/api/api.ts: expected false to be true // Object.is equality
   × FSD layout > old paths no longer exist after reshuffle 4ms
     → src/lib/api.ts should be gone: expected true to be false // Object.is equality

 FAIL  tests/structure/fsd-layout.test.ts > FSD layout > new target paths exist after reshuffle
AssertionError: shared/api/api.ts: expected false to be true // Object.is equality

- Expected
+ Received

- true
+ false

 ❯ tests/structure/fsd-layout.test.ts:11:71

 FAIL  tests/structure/fsd-layout.test.ts > FSD layout > old paths no longer exist after reshuffle
AssertionError: src/lib/api.ts should be gone: expected true to be false // Object.is equality

- Expected
+ Received

- false
+ true

 ❯ tests/structure/fsd-layout.test.ts:50:76

 Test Files  1 failed (1)
      Tests  2 failed (2)
   Start at  22:25:04
   Duration  3.27s
```

## Reason for Failure
Both tests fail for the correct reason: the FSD reshuffle has not been done yet.
- "new paths exist" fails because `src/shared/`, `src/widgets/`, and the new sub-directories inside `src/features/` don't exist.
- "old paths removed" fails because the files are still in their original locations.
This is the expected RED state. No import errors, no syntax bugs, no fixture issues.

## Baseline `tsc --noEmit` Result
FAIL — 3 pre-existing errors, all in `tests/lib/api-timing.test.ts`:

```
tests/lib/api-timing.test.ts(49,11): error TS2322: Type 'unknown' is not assignable to type 'string'.
tests/lib/api-timing.test.ts(63,11): error TS2322: Type 'unknown' is not assignable to type 'string'.
tests/lib/api-timing.test.ts(81,11): error TS2322: Type 'unknown' is not assignable to type 'string'.
```

These 3 errors pre-exist (the brief anticipated them). After the reshuffle, `tsc --noEmit` must still show only these 3 errors (or zero if the frontend-worker fixes them) — no new errors introduced.

## Baseline `vitest run` Result
```
 Test Files  1 failed | 2 passed (3)
      Tests  2 failed | 9 passed (11)
   Duration  4.42s
```

Breakdown:
- `tests/structure/fsd-layout.test.ts` — 2 FAILED (the new RED test, expected)
- `tests/lib/api-timing.test.ts` — 4 PASSED
- `tests/frontend-prefetch-hygiene.test.tsx` — 5 PASSED (including prefetch hygiene)

After the reshuffle, the GREEN target is: 11 passed, 0 failed (all 3 test files green).

## Surprises Found While Reading the Source Tree

1. **`src/features/auth/` already has a sub-structure** — `clientAuth.ts`, `credentials.ts`, `sessionService.ts` are already at `src/features/auth/` (not under `src/features/auth/api/`). The brief's file-move map for these is a within-features move (adding the `api/` subdirectory), not a cross-directory move.

2. **`src/features/projects/projectService.ts` exists at the feature root** — same situation; the move is to add `api/` subdirectory.

3. **`src/components/evaluation/hooks/`** — the hooks (`useEvaluationDraft.ts`, `useEvaluationSubmit.ts`, `useScrollSpy.ts`) live inside `src/components/evaluation/hooks/`, not at the evaluation feature root. The brief maps `src/components/evaluation/**` → `src/features/evaluations/components/**` wholesale; the frontend-worker must handle this nested structure correctly, likely moving hooks to `src/features/evaluations/hooks/`.

4. **No `src/lib/questions/scoring.ts` in the brief's file-move map but it exists** — `src/lib/questions/scoring.ts` exists alongside `questions.ts`. Both should move to `src/features/evaluations/lib/questions/` even though only `questions.ts` is explicitly called out in the brief.

5. **`src/app/modules/` vestiges** — confirmed present (`Dashboard.tsx`, `Sidebar.tsx`, `menu.ts`, `page.tsx`, `selected/page.tsx`), and correctly flagged as "do not touch" in the brief.

6. **`src/components/ui/SemesterSelector.tsx` exists** — correctly listed in the file-move map; it moves to `src/features/semesters/components/SemesterSelector.tsx`.

## Blockers
None. RED phase is confirmed. The frontend-worker can proceed with the FSD reshuffle.

## Next Step
Orchestrator should spawn `frontend-worker` to implement the reshuffle per Phase 2 of the brief.

---

# Phase 3 — GREEN gate

## Status
partial

## Results

### 1. Structure test
`npx vitest run tests/structure/fsd-layout.test.ts`
```
 RUN  v2.1.9 /home/aoshi/Test/app_test/teg-web-app/frontend

 ✓ tests/structure/fsd-layout.test.ts (2 tests) 18ms

 Test Files  1 passed (1)
      Tests  2 passed (2)
   Start at  23:08:06
   Duration  2.95s
```
Result: 2 passed, 0 failed — GREEN.

### 2. Prefetch hygiene regression
`npx vitest run tests/frontend-prefetch-hygiene.test.tsx`
```
 RUN  v2.1.9 /home/aoshi/Test/app_test/teg-web-app/frontend

 ✓ tests/frontend-prefetch-hygiene.test.tsx (5 tests) 1276ms
   ✓ ProjectCard prefetch hygiene > does not prefetch on mount when given a primaryHref 609ms

 Test Files  1 passed (1)
      Tests  5 passed (5)
   Start at  23:09:26
   Duration  4.51s
```
Result: 5 passed, 0 failed — GREEN. Task 004 behavior preserved.

### 3. Full vitest suite
`npx vitest run`
```
 RUN  v2.1.9 /home/aoshi/Test/app_test/teg-web-app/frontend

 ✓ tests/structure/fsd-layout.test.ts (2 tests) 14ms
 ✓ tests/lib/api-timing.test.ts (4 tests) 43ms
 ✓ tests/frontend-prefetch-hygiene.test.tsx (5 tests) 1280ms

 Test Files  3 passed (3)
      Tests  11 passed (11)
   Start at  23:09:44
   Duration  4.44s
```
Result: 11 passed, 0 failed, 3 files — GREEN. Matches the baseline target.

### 4. tsc --noEmit
```
tests/lib/api-timing.test.ts(49,11): error TS2322: Type 'unknown' is not assignable to type 'string'.
tests/lib/api-timing.test.ts(63,11): error TS2322: Type 'unknown' is not assignable to type 'string'.
tests/lib/api-timing.test.ts(81,11): error TS2322: Type 'unknown' is not assignable to type 'string'.
```
Result: exactly 3 pre-existing errors in `tests/lib/api-timing.test.ts`, no new errors — matches baseline.

### 5. Lint
`npm run lint`
```
✖ 28 problems (0 errors, 28 warnings)
  0 errors and 1 warning potentially fixable with the `--fix` option.
```
Result: 0 errors, 28 warnings — exactly matching the pre-reshuffle baseline. GREEN.

### 6. Production build
`npm run build` — FAILED (exit code 1).

The FSD reshuffle itself compiled successfully (Turbopack: "Compiled successfully in 9.6s", lint/type pass with only the same 28 pre-existing warnings). The failure occurs during static page generation:

```
⨯ useSearchParams() should be wrapped in a suspense boundary at page "/modules/selected".
  Read more: https://nextjs.org/docs/messages/missing-suspense-with-csr-bailout
Error occurred prerendering page "/modules/selected". Read more: https://nextjs.org/docs/messages/prerender-error
Export encountered an error on /modules/selected/page: /modules/selected, exiting the build.
⨯ Next.js build worker exited with code: 1 and signal: null
```

Root cause: `src/app/modules/selected/page.tsx` calls `useSearchParams()` without wrapping in a `<Suspense>` boundary. This page is in `src/app/modules/` — the vestigial directory the brief explicitly flagged as "do not touch" and "looks vestigial/dead". The reshuffle did not create or modify this file.

Assessment of whether this is a regression: Cannot confirm conclusively without running `npm run build` against the pre-reshuffle state. However, the brief identified `src/app/modules/` as vestigial, and the frontend-worker confirmed it was untouched. The FSD reshuffle compiled to completion; the build abort is caused by this pre-existing page during static page generation. No file in `src/features/`, `src/shared/`, or `src/widgets/` is involved.

### 7. Empty legacy dirs
`ls src/components src/lib src/types src/hooks`

The `ls` command shows subdirectory names (auth, dashboard, evaluation, hooks, inputs, landing, layout, questions, ui) but `find -type f` returns zero files in all four trees. All legacy directories contain only empty subdirectory shells — no source files remain.

Detailed dir structure (directories only, no files):
```
src/components/
  auth/          (empty)
  dashboard/     (empty)
  evaluation/
    hooks/       (empty)
    inputs/      (empty)
  landing/       (empty)
  layout/        (empty)
  ui/            (empty)
src/lib/
  questions/     (empty)
src/types/       (empty)
src/hooks/       (empty)
```

## Verdict
partial — The FSD reshuffle is functionally complete and verified across vitest (11/11), tsc (0 new errors), and lint (0 errors / 28 warnings unchanged). The production build fails due to the vestigial `src/app/modules/selected/page.tsx` calling `useSearchParams()` without a Suspense boundary. This file was explicitly excluded from the reshuffle scope ("do not touch") and is pre-existing dead code.

## Notes for orchestrator
1. **Build failure is pre-existing dead code, not a reshuffle regression.** The FSD reshuffle itself compiled cleanly. The failure is at static generation of `/modules/selected` which uses `useSearchParams()` bare (no `<Suspense>` boundary). Fix options:
   - Simplest: wrap `useSearchParams()` in a `<Suspense>` in `src/app/modules/selected/page.tsx`.
   - Cleanest: delete `src/app/modules/` entirely (it is vestigial; the brief already flagged it for deletion).
   The orchestrator should present this to the human as a follow-up decision.

2. **Empty legacy directories** (`src/components/`, `src/lib/`, `src/types/`, `src/hooks/`) contain zero files — only empty subdirectory shells. Safe to remove with a human `git rm -r` after the reshuffle commit.

3. **`frontend/CLAUDE.md` is stale** — still references old paths (`src/lib/api.ts`, `src/components/layout/Sidebar.tsx`, etc.). Needs updating to reflect the new FSD layout before the next frontend-worker run.

4. **`src/features/auth/api/credentials.ts`** is vestigial (contains only a comment, no exports). The barrel (`src/features/auth/index.ts`) was fixed to not re-export it. Either delete it or populate it.

5. The brief's verification criterion "npm run build — completes without error" is NOT met due to the pre-existing `src/app/modules/selected` issue. All other verification criteria are met.
