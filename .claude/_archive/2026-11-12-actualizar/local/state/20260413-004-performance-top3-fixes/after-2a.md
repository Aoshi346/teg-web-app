# Performance Re-measurement — After Phase 2A (Prefetch Cleanup)

> **User: run the same 3 flows from `baseline.md`, fill in the numbers, reply "2A done" in chat.**
> This is the GREEN gate for Phase 2A.

## What changed since baseline

- `ProjectCard.tsx` — removed the per-card `useEffect` that prefetched `primaryHref` on mount
- `dashboard/layout.tsx` — removed the 3-route `useEffect` prefetch block
- `Sidebar.tsx` — removed `prefetch={true}` from every nav `<Link>`
- The hover-prefetch path in Sidebar and Dashboard ProjectRow is **intact** — it's the right pattern

Expected impact: **no more per-card chunk compile storm on page transitions in dev mode**.

## Setup

1. **Important:** kill the Next.js dev server if running and restart: `npm run dev`. Turbopack caches compiled chunks in-memory, so a restart ensures we measure the new prefetch-free behavior from a cold start.
2. Hard reload the landing page (`Cmd/Ctrl + Shift + R`).
3. Open DevTools → Network tab → clear → check "Disable cache".
4. Console tab filtered to Info so you can see `[api]` lines.

---

## Flow A — Fresh login → dashboard visible

**Baseline was: 2.64 seconds, 21 total requests, subjective "Frustrating (3–5s)"**

- **Total wall-clock time (click → dashboard data visible):** `770 ms`
- **Total requests in Network tab:** `23`
- **Top 3 slowest requests** (click each in the Network tab, look at the duration):
  1. URL: `http://localhost:3000/_next/static/chunks/node_modules_51bdf575._.js` — duration: `981 ms`
  2. URL: `http://localhost:3000/_next/static/chunks/node_modules_lucide-react_dist_esm_icons_bdf0df42._.js` — duration: `981 ms`
  3. URL: `http://localhost:3000/_next/static/chunks/src_f74e5707._.js` — duration: `843 ms`
- **Subjective feel (pick one):**
  - [ ] Instant (<500ms)
  - [ ] Noticeable pause (500ms–1s)
  - [ ] Slow but usable (1–3s)
  - [X] Frustrating (3–5s)
  - [ ] Broken-feeling (>5s)

---

## Flow B — Navigate between 3 dashboard pages

**Baseline was: 489ms / 500ms / 1.92s per transition, 12/12/2 requests, subjective "Multi-second wait"**

1. Clear Network tab (don't reload).
2. Click **Proyectos**. Wait until cards are visible.
3. Click **Tesis**. Wait.
4. Click **Dashboard**. Wait.

**Fill in:**

- **Dashboard → Proyectos:**
  - Wall-clock time: `751 ms`
  - Number of new requests in Network tab: `12`
  - How many of those are `localhost:8000/api/*` (the actual backend calls): `4`
  - How many are `localhost:3000/_next/*` (Next.js dev chunks): `5`

- **Proyectos → Tesis:**
  - Wall-clock time: `424 ms`
  - New requests: `14`
  - Backend `/api/*` only: `3`
  - Next.js `_next/*` only: `2`

- **Tesis → Dashboard:**
  - Wall-clock time: `981 ms`
  - New requests: `4`
  - Backend `/api/*` only: `3`
  - Next.js `_next/*` only: `0`

- **Subjective feel on transitions:**
  - [ ] Instant
  - [ ] Quick but visible
  - [ ] Noticeable lag
  - [X] Multi-second wait
  - [ ] Frozen / UI unresponsive

---

## Flow C — Open the "Agregar" form

**Baseline was: 705ms, 19 total requests, all parallel, subjective was "slow but workable"**

- **Wall-clock time from click to form interactive:** `993 ms`
- **Total requests:** `17`
- **Backend `/api/*` requests only:** `8`
- **Next.js `_next/*` requests only:** `11`

---

## Quick vibe check

After running all 3 flows, which of these describes the overall experience compared to the baseline?

- [ ] Noticeably faster across the board — the problem is essentially solved
- [ ] Some transitions dramatically faster, others unchanged
- [X] Slightly faster but still frustrating
- [ ] No perceptible difference
- [ ] Somehow worse

**Anything unexpected?** (e.g., a page that broke, a feature that stopped working, a new console error): `____`

---

## Done?

Reply in chat with **"2A done"** and I will:

1. Read the numbers here
2. Compare to baseline
3. Decide:
   - **Big win (e.g., Flow B drops from 500ms to <100ms):** skip Phase 2B, go straight to Phase 3 (CSRF) or declare done
   - **Partial win:** do Phase 2B (TanStack Query) to fix the remaining API fetch waterfall
   - **No change:** re-investigate before touching more code (the prefetches weren't the problem, something else is)
4. Report back with findings + next recommended step
