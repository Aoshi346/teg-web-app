# Frontend Worker Result — 20260413-004-performance-top3-fixes — Phase 0

## Status
done

## Files Changed
- `frontend/src/lib/api.ts` lines 57–68 — added timing instrumentation inside the `request()` function

## Diff Applied to api.ts

Before (the `fetch` call and error handling block):
```ts
  const response = await fetch(`${API_URL}${endpoint}`, config);
  
  // Handle 401 Unauthorized globally if needed (e.g., redirect to login)
```

After:
```ts
  const t0 = performance.now();
  const response = await fetch(`${API_URL}${endpoint}`, config);
  const elapsed = Math.round(performance.now() - t0);

  // Dev-only timing log: gated at runtime so test environment stubs work correctly
  if (process.env.NODE_ENV !== "production") {
    if (response.ok) {
      console.info(`[api] ${method} ${endpoint} → ${elapsed}ms`);
    } else {
      console.info(`[api] ${method} ${endpoint} → ${response.status} (${elapsed}ms)`);
    }
  }

  // Handle 401 Unauthorized globally if needed (e.g., redirect to login)
```

The `method` variable was already defined at line 39 as `const method = (config.method || "GET").toUpperCase()` for the CSRF guard — I reused it, no duplication needed.

## Tests Status
- `npx vitest run tests/lib/api-timing.test.ts` — 4 passed, 0 failed
- `npx vitest run` (full suite) — 4 passed, 0 failed

## Type-check and Lint

Type-check: 3 pre-existing errors in `tests/lib/api-timing.test.ts` (the test file itself assigns `infoSpy.mock.calls[0][0]` typed as `unknown` to `const callArg: string`). These errors exist in the test file written by test-worker and predate this implementation. Zero errors in `src/lib/api.ts` or any other source file.

Lint: 27 pre-existing warnings, 0 errors. The one warning on `api.ts:48` (`'e' is defined but never used`) is pre-existing from the CSRF catch block. No new warnings introduced.

## Notes for Orchestrator

- The timing instrumentation fires AFTER the main `fetch()` but BEFORE the error-throw path. This means even for 4xx/5xx responses, the `console.info` fires with the status code before the error is thrown — exactly matching the test expectation.
- The `process.env.NODE_ENV` check is evaluated at runtime (not compile-time), which is required for `vi.stubEnv("NODE_ENV", "production")` to work in the test environment.
- CSRF pre-flight behavior is completely untouched (lines 38–55).
- `postForm()` is out of scope — it uses its own `fetch` call and was not touched.
- The 3 TypeScript errors in the test file should be addressed by test-worker or left as-is if the test runner accepts them (vitest does not enforce tsc strictness by default).

## Blockers
None.

---

## Phase 2A Implementation

### Status
done

### Files Changed
- `frontend/src/components/dashboard/ProjectCard.tsx` — removed mount-time prefetch `useEffect` and `useEffect` from React import
- `frontend/src/app/dashboard/layout.tsx` — removed prefetch `useEffect` block (3 routes)
- `frontend/src/components/layout/Sidebar.tsx` — removed `prefetch={true}` prop from `<Link>` in `renderLink`

### Diffs

#### 1. `frontend/src/components/dashboard/ProjectCard.tsx`

Before:
```tsx
import React, { useEffect } from "react";
...
  useEffect(() => {
    if (primaryHref) router.prefetch(primaryHref);
  }, [primaryHref, router]);

  const navigate = (e: React.MouseEvent) => {
```

After:
```tsx
import React from "react";
...
  const navigate = (e: React.MouseEvent) => {
```

`useEffect` removed from the import (no other usage in the file). The `useRouter` import and `const router = useRouter()` are unchanged — `router` is still used by `navigate()` and `edit()`.

#### 2. `frontend/src/app/dashboard/layout.tsx`

Before:
```tsx
  // Prefetch only the top 3 most-visited routes to avoid wasting bandwidth
  useEffect(() => {
    const routes = [
      "/dashboard",
      "/dashboard/proyectos",
      "/dashboard/tesis",
    ];
    routes.forEach((r) => router.prefetch(r));
  }, [router]);

  // Pending account gate
```

After:
```tsx
  // Pending account gate
```

`useEffect` remains in the React import — it is still used by the mobile-sidebar-close effect above. `router` is still used for `router.push("/")` in the pending-user branch.

#### 3. `frontend/src/components/layout/Sidebar.tsx`

Before:
```tsx
          onMouseEnter={() => handleLinkHover(item.href)}
          prefetch={true}
          className={...}
```

After:
```tsx
          onMouseEnter={() => handleLinkHover(item.href)}
          className={...}
```

`handleLinkHover` and its `onMouseEnter` binding are completely untouched.

### Vitest Output (prefetch-hygiene file)

```
 RUN  v2.1.9 /home/aoshi/Test/app_test/teg-web-app/frontend

 ✓ tests/frontend-prefetch-hygiene.test.tsx (5 tests) 1226ms
   ✓ ProjectCard prefetch hygiene > does not prefetch on mount when given a primaryHref 598ms

 Test Files  1 passed (1)
      Tests  5 passed (5)
   Start at  21:15:24
   Duration  4.32s
```

### Full Suite Output

```
 ✓ tests/lib/api-timing.test.ts (4 tests) 38ms
 ✓ tests/frontend-prefetch-hygiene.test.tsx (5 tests) 1135ms

 Test Files  2 passed (2)
      Tests  9 passed (9)
```

### Type-check Output

3 pre-existing errors in `frontend/tests/lib/api-timing.test.ts` (lines 49, 63, 81) — `unknown` assigned to `string` in test-worker-written test assertions. These are unrelated to Phase 2A edits and existed before this session. Zero errors in any of the 3 files edited here.

### Lint Output

0 errors. 28 pre-existing warnings in files I did not touch. No new warnings introduced by any of the 3 edits.

### Notes for Orchestrator

- The Sidebar test "prefetches on link hover (the good pattern — must stay)" passes — `handleLinkHover` still fires on `mouseEnter` as intended.
- `prefetch={true}` removal from `<Link>` in Sidebar is safe: Next.js App Router's default behavior is lazy prefetch on viewport intersection, which is the accepted fallback. The explicit `onMouseEnter` handler remains the fast path.
- No component external APIs (props, behavior from the outside) were changed.

### Blockers
None.
