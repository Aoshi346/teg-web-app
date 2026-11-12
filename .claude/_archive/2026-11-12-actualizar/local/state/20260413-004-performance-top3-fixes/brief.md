# Task Brief — 20260413-004-performance-top3-fixes

## Goal

Fix the **three highest-confidence performance offenders** in the TesisFar app in a measured, instrumented way. Each fix is gated by a before/after measurement so we can prove (or disprove) its impact instead of guessing.

The user's symptom is: *"Everything is slow on localhost in dev — login, page transitions, forms"*. Two parallel audits (backend + frontend) produced evidence. This brief synthesizes the findings and prioritizes the fixes by expected leverage.

## User Request (verbatim)

> The issue is that the frontend is too slow, all transitions are slow, takes seconds to log in, register, etc. Everything is slow, transitions between pages too, I need to make the project dynamic and the actual app flow correctly and smooth, use our workers to handle this correctly
>
> Is running on localhost, it is laggy even in dev, WHich should not happen

## Evidence summary (from the two audits)

Detailed reports live in this task's result files. High-level ranked findings:

### Tier 1 — Critical (most likely cause of user-visible lag)

1. **No data caching layer across page navigations.** The frontend has a 30-second module-level TTL cache in `projectService.ts:5` and `clientAuth.ts:4`, but there is **no React Query / SWR / TanStack Query**. Every navigation after 30 seconds refetches from scratch. Every page's `useEffect` also refetches on mount without deduplication. [frontend audit]

2. **Backend N+1 in `ProjectSerializer._latest_eval()`** (called from `get_score`, `get_diagramacion_score`, `get_contenido_score` — three separate method fields per project, scanning the same evaluation list three times). [backend audit]

3. **API waterfall on login.** `src/lib/api.ts:42-46` lazy-fetches `/api/csrf/` on the first POST, adding ~100–200ms round-trip before the login POST fires. [frontend audit, `api.ts:42-46`]

### Tier 1.5 — Big lever, bigger refactor (OUT OF SCOPE for this task — documented for later)

4. **`app/dashboard/layout.tsx` declares `"use client"`**, cascading to **17 of 18 dashboard pages**. This kills SSR and streaming for the entire dashboard. Every navigation must download JS, parse, hydrate, then fire `useEffect` to fetch data. **Reason for deferring:** the auth guard currently reads from `sessionStorage` which is client-only. Moving to a server component requires a broader auth refactor (HttpOnly cookie flow + Next.js middleware). Too big to bundle with this task. Will be **task 005** or later.

### Tier 2 — Secondary (measurable but lower leverage)

5. No pagination on list endpoints — not impactful yet at current data size.
6. `DEBUG=True` + `runserver` — adds Python-level overhead, but frontend is served separately so static-file cost is zero.
7. GSAP + `split-type` loaded synchronously (~180 KB) on the landing page — affects first paint but not dashboard transitions.

## What this task will do

Three fixes, in priority order, **with a measurement before and after each one**. If any fix does not produce measurable improvement, we stop that line and re-investigate instead of piling more fixes on top.

### Phase 0 — Instrumentation and baseline (REQUIRED before any fix)

**Backend instrumentation:**
- Add a tiny custom middleware (`core/middleware.py`) that logs per-request `X-Query-Count` and `X-Response-Time-Ms` headers for requests under `/api/`. Enabled only when `DEBUG=True`. ~30 lines.
- Add a pytest helper that asserts query counts on key endpoints using `django_assert_num_queries` (already available via `pytest-django`).

**Frontend instrumentation:**
- Add a timing wrapper in `src/lib/api.ts` that `console.info`s every API call with duration. Gated on `process.env.NODE_ENV !== 'production'`. ~10 lines.

**Baseline measurement:**
The **user runs 3 flows manually** in Chrome DevTools after instrumentation lands, and reports:
1. Fresh login → dashboard. Record: total time, slowest request, total request count, total query count (from headers).
2. Navigate dashboard → proyectos → evaluar. Record: transition times, requests per navigation, cache hits vs misses.
3. Open the agregar form. Record: time to interactive, how many parallel/sequential API calls.

These numbers go into `baseline.md` under this task folder. Without a baseline we cannot prove improvement, we can only assert it.

### Phase 1 — Backend N+1 fix (TDD with `assertNumQueries`)

**Scope:** `backend/api/serializers.py` — `ProjectSerializer._latest_eval` and its three callers.

**Root cause:** `_latest_eval` is called three times per project (once each for `get_score`, `get_diagramacion_score`, `get_contenido_score`). Even with the `evaluations` prefetch, the Python-level iteration is repeated three times.

**Fix approach:**
- Replace the three method fields with a single method that computes all scores in one pass and caches the result on `self` (or use a single serializer method that returns a dict, then expose individual fields from it).
- Alternative: add a `@property` on the `Project` model that computes the latest eval lazily and caches it. Pros: clean. Cons: couples model to serializer concerns.
- We will pick the cleaner one during implementation.

**Tests (written first by test-worker in RED phase):**
- `test_project_list_query_count_is_constant_for_n_projects` — use `django_assert_num_queries` + create 1, then 5, then 20 projects with evaluations; assert query count does not grow linearly with project count.
- `test_project_list_returns_correct_scores_for_all_projects` — regression guard that the scores are still correct after the refactor (not silently zero).
- `test_project_with_no_evaluations_returns_null_scores` — edge case that existed before.

**Workers:** test-worker (RED) → backend-worker → test-worker (GREEN) → orchestrator measures end-to-end via curl + the instrumentation middleware.

### Phase 2 — Frontend data caching (TanStack Query)

**Scope:** `frontend/src/lib/api.ts`, `frontend/src/features/projects/projectService.ts`, `frontend/src/features/auth/clientAuth.ts`, `frontend/src/lib/semesters.ts`, and the components that call them.

**Root cause:** There is no proper client cache. Navigations re-fetch. Multiple components calling the same endpoint don't deduplicate.

**Fix approach:**
1. Add `@tanstack/react-query` dependency (already compatible with React 19 and Next.js 15).
2. Add a `QueryClientProvider` in `app/layout.tsx` (the root server component — can wrap children client-side via a small client provider component).
3. Create hooks:
   - `useProjects()` — wraps `getAllProjects`, key `['projects', filters]`, 5-min staleTime
   - `useSemesters()` — wraps `getSemesters`, 10-min staleTime
   - `useCurrentSemester()` — 10-min staleTime
   - `useStudents()`, `useTutors()` — 5-min staleTime
4. Migrate `Dashboard.tsx`, `proyectos/page.tsx`, `tesis/page.tsx`, `agregar/useDocumentData.ts` to use the hooks instead of manual `useEffect` + fetch + local state.
5. **Remove** the module-level 30s TTL cache in `projectService.ts` and `clientAuth.ts` — TanStack Query replaces it.
6. Wire up `queryClient.invalidateQueries` on mutations (create project, update user, etc.) so stale data refreshes correctly.

**Tests:**
- Vitest + `@testing-library/react` hook tests for `useProjects()` with a mocked `api` client. Assert: first call fetches, second call within staleTime returns cached data, refetch after invalidation re-fires.
- Pin the test-worker on verifying the hooks, not rewriting every page.

**Workers:** test-worker (RED — write hook tests) → frontend-worker (add provider + hooks + migrate one page as proof of concept) → test-worker (GREEN) → frontend-worker (migrate remaining pages).

**Risk:** the migration touches many files. We will do it **in one worker session** to avoid half-migrated state, but scope is limited to the 5 data fetches listed above. No unrelated refactors.

### Phase 3 — CSRF pre-flight fix

**Scope:** `frontend/src/lib/api.ts` + the app's root provider.

**Root cause:** First POST request after page load blocks on a lazy `GET /api/csrf/`. For a user logging in on a cold tab, this adds a full round-trip to the first POST.

**Fix approach:**
- Fetch CSRF token **once**, eagerly, when the root layout mounts (in the client provider we create for TanStack Query, which is already running on every page).
- Remove the lazy-fetch branch in `api.ts`.
- If the cookie already exists, skip the fetch.

**Tests:**
- Vitest: `api.ts` unit test that mocks fetch and asserts CSRF is only requested once across many POST calls.

**Workers:** test-worker (RED) → frontend-worker → test-worker (GREEN).

### Phase 4 — Final measurement and summary

Run the same 3 flows the user ran in Phase 0. Compare baseline numbers against post-fix numbers. Write `after.md` and then `summary.md` with:
- Baseline vs after for each of the 3 flows
- Which fix moved which metric and by how much
- Anything that did NOT improve (signal to investigate further)
- Recommended next step for **task 005** (the deferred dashboard layout refactor)

## What this task will NOT do

- Refactor `app/dashboard/layout.tsx` to be a server component. Big auth change. **Task 005**.
- Add pagination. Not the bottleneck yet.
- Lazy-load GSAP / `split-type`. Affects landing page first paint, not dashboard transitions.
- Remove `DEBUG=True`. It's a dev-mode concern, not a production fix. Would change other behavior.
- Switch session storage to cache-backed (Redis). Requires infra the project doesn't have.
- Add error boundaries.
- Upgrade any libraries beyond adding `@tanstack/react-query` and `@tanstack/react-query-devtools` (dev-only).
- Frontend build / bundle analysis beyond what the audit already flagged.

## Verification Criteria

### Per-phase gates
- **Phase 0:** `baseline.md` exists with numbers from the 3 flows. User confirms they ran the flows.
- **Phase 1:** `django_assert_num_queries` test is green; backend query count for `GET /api/projects/` is constant in N, not linear.
- **Phase 2:** TanStack Query installed, hooks created, 2nd navigation to a cached page fires **zero** network requests. Hook vitest tests green.
- **Phase 3:** CSRF is fetched at most once per page load. Vitest test green.
- **Phase 4:** `after.md` shows concrete before/after. Summary documents what worked and what did not.

### Overall
- [ ] All 40 existing tests still pass (`pytest` + `vitest run`)
- [ ] No new ruff violations
- [ ] No new ESLint / TypeScript errors
- [ ] The user reports **subjective** improvement in login + navigation after Phase 4

## Risks

- **Risk:** We instrument and fix, but the user's actual bottleneck is something neither audit caught (e.g., an antivirus scanning node_modules, Windows Defender on WSL, a proxy, Turbopack dev cache corruption). **Mitigation:** Phase 0 measurements will reveal if timings do not match the hypothesis. If Phase 1 delivers no improvement, STOP and re-investigate before moving to Phase 2.
- **Risk:** TanStack Query migration is larger than planned; touching 4+ pages risks scope creep. **Mitigation:** hard scope to the 5 data fetches listed in Phase 2. Other useEffect fetches stay manual for this task.
- **Risk:** The N+1 fix is correct but the actual slowness is frontend hydration, not backend. **Mitigation:** Phase 0 timings will tell us. If the dashboard load shows API calls completing in 50ms but the UI takes 2 seconds, the bottleneck is frontend, and Phase 1 can be deprioritized.
- **Risk:** `assertNumQueries` tests are brittle — any Django internal change shifts query counts. **Mitigation:** assert with `<` not `==` where possible, and comment why the count is what it is.
- **Risk:** Adding `QueryClientProvider` in the root layout may interact with the client-only dashboard layout in unexpected ways. **Mitigation:** use the standard Next.js 15 pattern (small client provider component wrapping `{children}`). Well-documented, low-risk.
- **Risk:** User cannot easily run the 3 baseline flows in devtools. **Mitigation:** I will write explicit step-by-step instructions in Phase 0's `baseline.md` template. The orchestrator can also run flows via curl against the backend (that won't capture frontend render time but will isolate backend response time).

## Model & Worker Allocation

- Orchestrator: Opus 4.6
- test-worker (Sonnet 4.6) — RED and GREEN phases
- backend-worker (Sonnet 4.6) — Phase 1 fix + Phase 0 backend instrumentation
- frontend-worker (Sonnet 4.6) — Phase 2 migration + Phase 3 CSRF fix + Phase 0 frontend instrumentation

## Human Checkpoint

Status: `PENDING_APPROVAL`

After writing this brief, the orchestrator pauses and asks the user:
> "Plan drafted at `.claude/state/20260413-004-performance-top3-fixes/brief.md`. Approve to proceed, request changes, or cancel."
