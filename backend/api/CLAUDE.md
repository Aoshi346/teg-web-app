# API — Django App

## What This Is

`api/` is the main Django app containing all domain models, REST API views, serializers, and URL routing for the TesisFar (TEG) management system. It implements role-based access control for Students, Tutors, Jury members, and Administrators.

## Files

| File | Purpose |
|------|---------|
| `models.py` | Domain models: User, Project, Evaluation, Semester, AttachedFile, Comment, PresentationDay, Presentation, PresentationJuror, SessionLog, StateOverride |
| `views.py` | DRF ViewSets with role-based queryset filtering and custom actions |
| `serializers.py` | Serializers/deserializers for all models |
| `urls.py` | DRF router registering all ViewSets under `/api/` |
| `lifecycle.py` | Pure state-machine functions (`next_state`, `status_projection`, `InvalidTransition`). No DB access. Consumed by `EvaluationViewSet.perform_create` to drive `Project.state` transitions. |
| `apps.py` | Django app configuration |
| `tests.py` | (empty — no automated tests) |
| `management/commands/set_semester.py` | Admin command to activate a semester |

## Data Models

| Model | Description |
|-------|-------------|
| **User** | Custom user with email auth, roles (Administrador/Estudiante/Tutor/Jurado), phone, `nationality` (V/E/P), `cedula` (PositiveIntegerField, nullable), semester (program year). `UniqueConstraint(nationality, cedula)`. Serializer exposes read-only `cedula_display` = `"V-30243721"`. |
| **Project** | Title, student (FK), partner (optional FK), advisors (M2M to Tutor), reviewer (FK to User with role=Jurado, nullable, `related_name=assigned_projects`), status, period, project_type (proyecto/tesis), stage1_passed, `state` (PTEG lifecycle). `failed_attempts` is derived from Evaluation rows by the serializer. |
| **Evaluation** | Project evaluation with `kind` (review/defense), JSON ratings/comments/section_scores, score, pass_status (Pass/Fail). Creating a review/defense evaluation transitions the project's `state` via `api/lifecycle.next_state()`. |
| **AttachedFile** | File upload (pdf/doc/docx) attached to a project |
| **Semester** | Academic period (YYYY-SS format, e.g. 2026-01), active flag, start/end months |
| **Comment** | Authored comment on a project |
| **PresentationDay** | Scheduled presentation day, unique by date, tied to a Semester |
| **Presentation** | Single slot on a day: `project` + `tutor` + `jurado` (M2M *through* PresentationJuror), start_time, duration_minutes, order. Unique `(day, project)`. |
| **PresentationJuror** | Explicit through-model for the `Presentation.jurado` M2M. Fields: `individual_score`, `notified`, `notified_at`, `confirmed_attendance`, `attended` + timestamps. **Important**: `Presentation.jurado.add(...)` / `.set(...)` are forbidden by Django on a `through=` M2M — create `PresentationJuror` rows directly. Reads (`presentation.jurado.all()`) still work normally. |
| **SessionLog** | Session tracking with device/browser/ip, active/inactive status |
| **StateOverride** | Admin-only audit of manual `Project.state` changes on PTEG. Fields: `project` (CASCADE), `admin` (PROTECT), `from_state`, `to_state`, `reason` (text, ≥10 chars validated at endpoint), `created_at`. Append-only. `Meta.ordering = ['-created_at']`. Created by `POST /api/projects/{id}/override_state/`; never via evaluations. |

## API Endpoints (from `api/urls.py`)

| Route | ViewSet | Actions |
|-------|---------|---------|
| `/api/auth/` | AuthViewSet | login, logout, register, me |
| `/api/csrf/` | CsrfTokenView | GET token |
| `/api/users/` | UserViewSet | CRUD, filtered by role |
| `/api/projects/` | ProjectViewSet | CRUD + reassign_student, upload_file, assign_reviewer (POST, admin-only, body `{"reviewer": <user_id \| null>}`, rejects non-Jurado users) + override_state (POST, admin-only, PTEG-only; body `{state, reason}`; writes StateOverride + updates Project.state & status atomically; bypasses `lifecycle.next_state()`) |
| `/api/evaluations/` | EvaluationViewSet | CRUD. `POST` accepts `kind: 'review' | 'defense'` (defaults to review). PTEG transitions: creating an eval advances `Project.state` via `api/lifecycle.next_state()`. Create restricted to Administrador and Jurado; Jurado only on projects where they are the `reviewer`. Returns 400 if the transition is illegal for the current state. |
| `/api/semesters/` | SemesterViewSet | CRUD + current, set_active |
| `/api/comments/` | CommentViewSet | CRUD (requires project param) |
| `/api/sessions/` | SessionViewSet | list, destroy, track |

## Role-Based Access

- **Administrador**: Full access to all models and endpoints; can assign a Jurado as project `reviewer` via `/api/projects/{id}/assign_reviewer/`; can force PTEG `Project.state` via `POST /api/projects/{id}/override_state/` (logged in `StateOverride`). The `stateOverrides` nested field on `ProjectSerializer` is exposed only to Administradores — non-admin responses omit it entirely.
- **Tutor**: Sees only projects where they are assigned as advisor; can read evaluations of their advisees but cannot create evaluations
- **Jurado**: Sees only projects where `reviewer` is set to them, and only evaluations on those projects; can create `review` and `defense` evaluations on assigned projects. The state of a project governs whether a given `kind` is accepted (a review on `pending_defense` is rejected with 400).
- **Estudiante**: Sees own projects only (as student or partner)

## Connection to `core/`

- Registered in `core/settings.py` `INSTALLED_APPS` as `'api'`
- `core/settings.py` sets `AUTH_USER_MODEL = 'api.User'`
- Routed from `core/urls.py` via `path('api/', include('api.urls'))`

## Connection to Frontend

The Next.js frontend (`frontend/src/features/`) calls these endpoints:
- `clientAuth.ts` — auth endpoints
- `projectService.ts` — project CRUD and file uploads
