# API — Django App

## What This Is

`api/` is the main Django app containing all domain models, REST API views, serializers, and URL routing for the TesisFar (TEG) management system. It implements role-based access control for Students, Tutors, Jury members, and Administrators.

## Files

| File | Purpose |
|------|---------|
| `models.py` | Domain models: User, Project, Evaluation, Semester, AttachedFile, Comment, PresentationDay, Presentation, PresentationJuror, SessionLog |
| `views.py` | DRF ViewSets with role-based queryset filtering and custom actions |
| `serializers.py` | Serializers/deserializers for all models |
| `urls.py` | DRF router registering all ViewSets under `/api/` |
| `apps.py` | Django app configuration |
| `tests.py` | (empty — no automated tests) |
| `management/commands/set_semester.py` | Admin command to activate a semester |

## Data Models

| Model | Description |
|-------|-------------|
| **User** | Custom user with email auth, roles (Administrador/Estudiante/Tutor/Jurado), phone, `nationality` (V/E/P), `cedula` (PositiveIntegerField, nullable), semester (program year). `UniqueConstraint(nationality, cedula)`. Serializer exposes read-only `cedula_display` = `"V-30243721"`. |
| **Project** | Title, student (FK), partner (optional FK), advisors (M2M to Tutor), reviewer (FK to User with role=Jurado, nullable, `related_name=assigned_projects`), status, period, project_type (proyecto/tesis), stage1_passed, failed_attempts |
| **Evaluation** | Project evaluation with JSON ratings/comments/section_scores, score, pass_status (Pass/Fail) |
| **AttachedFile** | File upload (pdf/doc/docx) attached to a project |
| **Semester** | Academic period (YYYY-SS format, e.g. 2026-01), active flag, start/end months |
| **Comment** | Authored comment on a project |
| **PresentationDay** | Scheduled presentation day, unique by date, tied to a Semester |
| **Presentation** | Single slot on a day: `project` + `tutor` + `jurado` (M2M *through* PresentationJuror), start_time, duration_minutes, order. Unique `(day, project)`. |
| **PresentationJuror** | Explicit through-model for the `Presentation.jurado` M2M. Fields: `individual_score`, `notified`, `notified_at`, `confirmed_attendance`, `attended` + timestamps. **Important**: `Presentation.jurado.add(...)` / `.set(...)` are forbidden by Django on a `through=` M2M — create `PresentationJuror` rows directly. Reads (`presentation.jurado.all()`) still work normally. |
| **SessionLog** | Session tracking with device/browser/ip, active/inactive status |

## API Endpoints (from `api/urls.py`)

| Route | ViewSet | Actions |
|-------|---------|---------|
| `/api/auth/` | AuthViewSet | login, logout, register, me |
| `/api/csrf/` | CsrfTokenView | GET token |
| `/api/users/` | UserViewSet | CRUD, filtered by role |
| `/api/projects/` | ProjectViewSet | CRUD + reassign_student, upload_file, assign_reviewer (POST, admin-only, body `{"reviewer": <user_id \| null>}`, rejects non-Jurado users) |
| `/api/evaluations/` | EvaluationViewSet | CRUD (create restricted to Administrador and Jurado; Jurado can only create on projects where they are the assigned `reviewer`) |
| `/api/semesters/` | SemesterViewSet | CRUD + current, set_active |
| `/api/comments/` | CommentViewSet | CRUD (requires project param) |
| `/api/sessions/` | SessionViewSet | list, destroy, track |

## Role-Based Access

- **Administrador**: Full access to all models and endpoints; can assign a Jurado as project `reviewer` via `/api/projects/{id}/assign_reviewer/`
- **Tutor**: Sees only projects where they are assigned as advisor; can read evaluations of their advisees but cannot create evaluations
- **Jurado**: Sees only projects where `reviewer` is set to them, and only evaluations on those projects; can create evaluations only on projects assigned to them
- **Estudiante**: Sees own projects only (as student or partner)

## Connection to `core/`

- Registered in `core/settings.py` `INSTALLED_APPS` as `'api'`
- `core/settings.py` sets `AUTH_USER_MODEL = 'api.User'`
- Routed from `core/urls.py` via `path('api/', include('api.urls'))`

## Connection to Frontend

The Next.js frontend (`frontend/src/features/`) calls these endpoints:
- `clientAuth.ts` — auth endpoints
- `projectService.ts` — project CRUD and file uploads
