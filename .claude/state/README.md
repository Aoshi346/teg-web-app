# Task State Directory

This directory holds **handoff files** between the Orchestrator and subagents for the TesisFar monorepo.

## Folder Structure

Every task gets its own folder:

```
.claude/state/
├── README.md                          (this file)
├── template.md                        (copy this when starting a task)
└── 20260413-001-evaluation-tests/
    ├── brief.md                       (orchestrator — plan + human checkpoint)
    ├── test-worker-result.md          (test-worker — RED and GREEN phase reports)
    ├── backend-worker-result.md       (backend-worker — implementation report)
    ├── frontend-worker-result.md      (frontend-worker — implementation report)
    └── summary.md                     (orchestrator — final synthesis)
```

## Task ID Format

`YYYYMMDD-NNN-short-slug`

- `YYYYMMDD` — date the task was started
- `NNN` — zero-padded counter within that day (001, 002, ...)
- `short-slug` — 2-4 kebab-case words describing the task

Examples:
- `20260413-001-evaluation-tests`
- `20260413-002-notification-endpoint`
- `20260414-001-semester-cross-year-fix`

## File Roles

| File | Author | Purpose |
|---|---|---|
| `brief.md` | Orchestrator | Plan, decomposition, verification criteria. Written **before** human checkpoint. |
| `test-worker-result.md` | test-worker | RED phase (failing test confirmed) and later GREEN phase (implementation verified). |
| `backend-worker-result.md` | backend-worker | Files changed, tests passing, lint clean. |
| `frontend-worker-result.md` | frontend-worker | Files changed, tests passing, type-check clean. |
| `summary.md` | Orchestrator | Final status, what to tell the human, follow-ups. |

## Lifecycle

1. Orchestrator receives a task from the user.
2. Orchestrator copies `template.md` to `<task-id>/brief.md`, fills it in, and shows it to the user.
3. **User approves** (explicit "go" / "approved" / "proceed").
4. Orchestrator spawns `test-worker` (RED) → reads `test-worker-result.md`.
5. Orchestrator spawns `backend-worker` and/or `frontend-worker` → reads their result files.
6. Orchestrator spawns `test-worker` again (GREEN) → reads updated `test-worker-result.md`.
7. Orchestrator writes `summary.md` and reports to the user.
8. Files are kept for auditability. Do not delete historical task folders unless the user asks.

## Git

This directory **is** tracked in git so that task history survives and can be reviewed in PRs. Add a `.gitignore` here later only if it becomes noisy.
