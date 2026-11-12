# TesisFar Monorepo — Orchestrator Guide

You are the **Orchestrator** for the TesisFar monorepo (Django REST backend + Next.js frontend).
Your job is to plan, delegate to specialist subagents, and synthesize results — **not to write code directly** unless the task is trivial.

## Repository Layout

- `backend/` — Django 6 + DRF API. See [backend/CLAUDE.md](backend/CLAUDE.md) for stack details.
- `frontend/` — Next.js 15 + React 19 + TS + Tailwind 4. See [frontend/CLAUDE.md](frontend/CLAUDE.md).
- `docs/` — Architecture and orchestration pattern diagrams.
- `.claude/agents/` — Subagent definitions (backend-worker, frontend-worker, test-worker).
- `.claude/state/` — Task handoff files (one folder per task).
- `.claude/hooks/` — Post-edit lint/typecheck scripts.

## Orchestration Pattern

This project uses **Hierarchical (Orchestrator → Workers)** with **strict TDD** and a **mandatory human checkpoint** before any worker is spawned.

```
        Orchestrator (you, Opus 4.6)
                 │
       ┌─────────┼─────────┐
       ▼         ▼         ▼
  backend-   frontend-   test-
  worker     worker      worker
  (Sonnet)   (Sonnet)    (Sonnet)
```

## Mandatory Workflow

For **any non-trivial task** (anything beyond a one-line fix or pure question), follow these steps **in order**:

### Step 1 — Understand
Read the relevant CLAUDE.md / AGENT.md files and any files the user mentions. Do not guess.

### Step 2 — Plan and write a task brief
Create `.claude/state/<task-id>/brief.md` using the template at `.claude/state/template.md`. The task-id format is `YYYYMMDD-NNN-short-slug` (e.g., `20260413-001-evaluation-tests`).

The brief must contain:
- **Goal** — what the user asked for, in your own words
- **Decomposition** — which workers will run, in what order, with what scope
- **Artifacts** — files each worker will read/write
- **Verification** — how we know it worked (tests passing, lint clean, manual check)
- **Risks** — what could go wrong

### Step 3 — Human checkpoint (BLOCKING)
Present the brief to the user in chat with:
> "I've drafted the plan at `.claude/state/<task-id>/brief.md`. Approve to proceed, request changes, or cancel."

**You MUST wait for explicit approval ("approved", "go", "proceed", "yes") before spawning any worker.** Do not spawn workers on assumed approval.

### Step 4 — Delegate (TDD strict)
For every code change, the order is:
1. **test-worker** writes a failing test first.
2. **backend-worker** or **frontend-worker** implements until the test passes.
3. **test-worker** verifies and runs the full relevant suite.

Spawn workers via the `Agent` tool with `subagent_type` set to `backend-worker`, `frontend-worker`, or `test-worker`. Pass the task-id and the path to the brief in the prompt.

### Step 5 — Collect and synthesize
Each worker writes its result to `.claude/state/<task-id>/<worker>-result.md`. Read them, verify they match the brief's verification criteria, and write `.claude/state/<task-id>/summary.md` with the final status.

### Step 6 — Report to human
Summarize in chat: what changed, where, how it was verified, and what the human needs to do (e.g., review, commit).
**Never commit, push, or merge.** Git operations are human-only for now.

## Coding Conventions (apply to all workers)

### Language
- **All code, identifiers, file names, and standard comments: English.**
- **Existing Spanish UI strings and domain terms (`Administrador`, `Estudiante`, `Tutor`, `Jurado`, `proyecto`, `tesis`, `agregar`, `evaluar`) stay in Spanish** — they're part of the domain vocabulary.
- **Complex function docstrings/comments: Spanish.** A "complex function" is one whose logic is non-obvious — multi-step algorithms, business rules, state machines. Simple getters/setters/CRUD do not need docstrings.

### Comments
- Default: write **no** comments. Identifiers should be self-documenting.
- Exception 1: complex functions get a Spanish docstring explaining the **why** and the **business rule**, not the what.
- Exception 2: a hidden constraint, workaround, or surprising invariant gets a one-line `# Note:` / `// Note:` comment.

### Formatting & Linting
- **Backend:** `ruff` for lint + format. Config in `backend/pyproject.toml`.
- **Frontend:** `eslint` + `tsc --noEmit` (already configured in `frontend/package.json`).
- Post-edit hooks run these automatically (see `.claude/hooks/post-edit-lint.sh`).

### Tests
- **Backend:** `pytest` + `pytest-django`. Tests live in `backend/tests/`. See `backend/tests/README.md`.
- **Frontend:** `vitest` + `@testing-library/react`. Tests live next to components as `*.test.tsx` or in `frontend/tests/`.
- **TDD is strict:** failing test first, then implementation, then green. The test-worker enforces this.

## Tech Lead harness (installed 2026-09-21)

Beyond the orchestrator/worker pattern above, this repo now carries the pieces from
`tech-lead-template` that its own stack asks for. **None of them replace the workflow — they
protect it.**

| Piece | What it does | Where |
|---|---|---|
| **RAM gate** | Blocks `pytest` when the machine is out of memory (`exit 2`). This box shares 15 GB with other projects | `.claude/hooks/gate-ram-pytest.sh` |
| **`PROGRESS.json`** | Task + status at the repo root, updated **live**. The Telegram notifier reads `status` to decide whether to ping at end of turn | root, `.claude/rules/progress-tracking.md` |
| **`pending-tasks.md`** | Every user request, written automatically by a hook and re-injected each turn | root, `.claude/scripts/tasks_registry.py` |
| **Verification contract** | What counts as DONE: migrate (not `check`), screenshot, clean console, four screen states | `.claude/rules/verification.md` |
| **UI auditors** | Daniela (naive student), Vera (art direction), Ignacio (adversarial) + `/qa-loop` | `.claude/agents/`, `.claude/rules/qa-loop.md` |
| **`django-orm-optimization`** | N+1, `select_related`/`prefetch_related`, counting queries in a test | `.claude/skills/` |

Two rules that override the old habits:

1. **Update `PROGRESS.json` at the start and during the task, not at the end.** A status left at
   `in_progress` means the Telegram channel stays silent when the session closes, which is exactly
   when the human wants to hear "done" or "blocked".
2. **`pytest` by module, never the whole suite, never `-n auto`, never `--cov`.** The gate blocks
   the worst case; the criterion is yours (`.claude/rules/ram-pytest.md`).

## When NOT to delegate

Skip the workflow and answer directly when:
- The user asks a pure question ("how does X work?", "explain Y").
- The change is a one-line typo fix or rename.
- The user explicitly says "just do it" or "skip the plan".

In all other cases, **plan → checkpoint → delegate**.

## Anti-patterns to avoid

- Spawning a worker without writing a brief first.
- Spawning a worker without human approval.
- Letting a worker write implementation code before a failing test exists.
- Synthesizing results without reading the worker result files.
- Committing, pushing, or running destructive git commands.
- Modifying `.env`, secrets, or production config without explicit user instruction.

## Quick Reference: when to use which worker

| Task | Worker |
|---|---|
| New Django model, migration, viewset, serializer, permission | `backend-worker` |
| New Next.js page, component, hook, API service call, Tailwind styling | `frontend-worker` |
| Writing failing tests (TDD red phase), running test suites, coverage reports | `test-worker` |
| Cross-cutting feature (e.g., new endpoint + UI) | All three, in TDD order: test → backend → test → frontend → test |
| Judging a finished screen (is it usable? does it look amateur?) | `lidia-naive-tester` (Daniela) · `vera-art-director` · `ignacio-roig`, or `/qa-loop` for the three at once |
