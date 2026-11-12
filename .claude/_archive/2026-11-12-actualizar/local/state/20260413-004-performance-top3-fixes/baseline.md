# Performance Baseline — Pre-Fix

> **User: this is a form. Run the flows below, fill in the numbers, then reply "baseline done" in chat.**
> No guessing — round numbers are fine.

## Setup

1. Start the backend:
   ```bash
   cd backend && source ../.venv/bin/activate && python manage.py runserver
   ```
2. Start the frontend (fresh terminal):
   ```bash
   cd frontend && npm run dev
   ```
3. Open the app in Chrome → **Open DevTools** (F12).
4. Go to the **Network** tab. Click the 🚫 clear icon. Check **"Disable cache"** (important for baseline).
5. Go to the **Console** tab. Check the filter dropdown → make sure "Info" is enabled. You should see `[api] ...` lines after interactions.
6. Before each flow, do a **hard reload** (`Cmd/Ctrl + Shift + R`) so sessionStorage and the Turbopack dev cache start clean.

**How to read the two new headers:** click any `/api/*` request in the Network tab → **Headers** section → scroll to Response headers → look for `x-query-count` and `x-response-time-ms`. (Lowercase is normal — HTTP headers are case-insensitive.)

---

## Flow A — Fresh login → dashboard visible

1. Hard reload the landing page.
2. Clear the Network tab.
3. Open the login modal and enter credentials (use `admin@example.com` / `123`).
4. Click **Ingresar**. Start a stopwatch mentally.
5. Stop when the dashboard data is fully visible (cards have real numbers, not skeletons).

**Fill in:**

- **Total wall-clock time (click → dashboard data visible):** `2.64 seconds`
- **Total requests in Network tab during this flow:** `21`
- **Slowest single `/api/*` request:**
  - URL: `http://localhost:3000/_next/static/chunks/src_f74e5707._.js`
  - `x-response-time-ms` header value: `____`
  - `x-query-count` header value: `____`____
- **2nd slowest `/api/*` request:**
  - URL: `http://localhost:3000/_next/static/chunks/src_app_dashboard_page_tsx_717ffa4b._.js`
  - `x-response-time-ms`: `____`
  - `x-query-count`: `____`
- **3rd slowest `/api/*` request:**
  - URL: `http://localhost:8000/api/semesters/current/`
  - `x-response-time-ms`: `____`
  - `x-query-count`: `____`
- **Sum of all `x-query-count` headers in this flow** (add them up — it's OK to be approximate, 1-2 off doesn't matter): `____`
- **Subjective feel (pick one):**
  - [ ] Instant (<500ms)
  - [ ] Noticeable pause (500ms–1s)
  - [ ] Slow but usable (1–3s)
  - [X] Frustrating (3–5s)
  - [ ] Broken-feeling (>5s)

---

## Flow B — Navigate between 3 dashboard pages

Starting from the dashboard (already logged in).

1. Clear the Network tab (do NOT reload — we want to see cached vs uncached).
2. Click **Proyectos** in the sidebar. Wait until it finishes rendering.
3. Click **Tesis**. Wait.
4. Click **Dashboard** (back to home). Wait.

**Fill in:**

- **Dashboard → Proyectos:**
  - Wall-clock time from click to content visible: `489 ms`
  - Number of new `/api/*` requests fired: `12`
  - List the endpoints: `____`
- **Proyectos → Tesis:**
  - Wall-clock time: `500 ms`
  - New `/api/*` requests: `12`
  - Endpoints: `____`
- **Tesis → Dashboard:**
  - Wall-clock time: `1.92 ms`
  - New `/api/*` requests: `2`
  - Endpoints: `____`
- **Does navigating back to a page you already visited (e.g., Dashboard again) re-fire the same `/api/projects/` call you already made?**
  - [ ] Yes, fetches again
  - [X] No, something is cached

- **Subjective feel on transitions:**
  - [ ] Instant
  - [ ] Quick but visible
  - [ ] Noticeable lag
  - [X] Multi-second wait
  - [ ] Frozen / UI unresponsive

---

## Flow C — Open the "Agregar" form

1. From the dashboard, click **Agregar** in the sidebar.
2. Watch the Network tab.

**Fill in:**

- **Wall-clock time from click to form fully interactive (inputs clickable):** `705 ms`
- **Number of `/api/*` requests fired for this page:** `19`
- **List the endpoints in order:** `____`
- **Were they fired in parallel or sequentially?** (Look at the Waterfall column in Network tab — do the bars overlap in time or stack after each other?)
  - [X] All parallel (bars start at roughly the same X position)
  - [ ] Mixed
  - [ ] All sequential (each bar waits for the previous to finish)
- **Slowest request in this flow:**
  - URL: `react-dom-client.development.js`
  - `x-response-time-ms`: `____`
  - `x-query-count`: `____`

---

## Frontend console timing logs (bonus — quick skim)

Open the Console tab, filter to "Info" or search `[api]`. Look at **Flow A** (login → dashboard) and tell me:

- **The 3 highest-duration `[api]` lines from the console:**
  1. `____`
  2. `____`
  3. `____`

The format is `[api] METHOD path → Nms` — so `[api] GET /projects/ → 842ms` means the network request (from JS) took 842ms total.

---

## Environment notes

- OS: `Linux`
- Chrome version (or Firefox, Edge): `____`
- Is WSL / Docker / VM involved?: `No`
- Dev server: `npm run dev` (Turbopack) — confirmed
- Backend: `python manage.py runserver` with `DEBUG=True` — confirmed

---

## Done?

Once you've filled this in, reply in chat with **"baseline done"** and I will:

1. Read the numbers here
2. Use them to sanity-check the hypotheses from the audits (N+1, no caching, CSRF pre-flight)
3. If any flow shows the bottleneck is somewhere else entirely (e.g., hydration, not API latency), I pivot the plan before touching code
4. Move to Phase 1 (backend N+1 fix) with TDD
