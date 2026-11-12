# Task Brief — <task-id>

> Copy this file to `.claude/state/<task-id>/brief.md` when starting a task.
> Fill in every section. Do not skip "Verification" or "Risks".

## Goal

<One paragraph. Restate what the user asked for in your own words. If you had to make interpretation calls, say so.>

## User Request (verbatim)

> <Paste the exact user message that triggered this task, quoted.>

## Decomposition

List the subtasks in execution order. For each: which worker, what it does, what it reads, what it writes.

1. **test-worker (RED)** — Write failing test for <behavior>
   - Reads: <files>
   - Writes: `backend/tests/test_<feature>.py` (or `frontend/tests/...`)
2. **backend-worker** — Implement <behavior>
   - Reads: `brief.md`, `test-worker-result.md`, <domain files>
   - Writes: <files it will modify>
3. **test-worker (GREEN)** — Verify implementation
   - Reads: `brief.md`, `backend-worker-result.md`
   - Writes: updated `test-worker-result.md`

## Relevant Files (context)

- `backend/api/models.py` — <why this matters>
- `backend/api/views.py` — <why this matters>
- `frontend/src/...` — <why this matters>

## Verification Criteria

How do we know this task is done? Be concrete.

- [ ] `pytest backend/tests/test_<feature>.py` — all tests pass
- [ ] `ruff check backend/` — clean
- [ ] `npx vitest run frontend/...` — all tests pass
- [ ] `npm run type-check` (frontend) — clean
- [ ] `npm run lint` (frontend) — clean
- [ ] Manual check: <what a human would click through to verify, if applicable>

## Risks

What could go wrong? What would surprise the user if it happened?

- **Risk:** <e.g., migration touches an indexed column and locks the table>
- **Mitigation:** <e.g., review generated migration before applying>

## Out of Scope

Anything this task explicitly does NOT cover. Write this to prevent scope creep.

- <e.g., refactoring the existing EvaluationViewSet permission class>
- <e.g., adding i18n support>

## Model & Worker Allocation

- Orchestrator: Opus 4.6
- Workers: Sonnet 4.6 (backend-worker, frontend-worker, test-worker)

## Human Checkpoint

Status: `PENDING_APPROVAL`

After writing this brief, the orchestrator **must** pause and ask the user:
> "Plan drafted at `.claude/state/<task-id>/brief.md`. Approve to proceed, request changes, or cancel."

The orchestrator may not spawn workers until the user replies with explicit approval.

Once approved, update this section to:

```
Status: APPROVED
Approved at: <ISO timestamp>
Approved by: <user>
Notes: <any conditions the user attached>
```
