# Backend Development Guide - TesisFar

## Quick Reference

- **Entry point:** `manage.py` / `core/settings.py`
- **App directory:** `api/`
- **Run server:** `python manage.py runserver` (port 8000)
- **Dependencies:** `pip install -r requirements.txt`
- **Database:** SQLite3 at `db.sqlite3`
- **Virtual env:** `../.venv/` (project root)

## Architecture

This is a standard Django + DRF project following the pattern:

```
Request → core/urls.py → api/urls.py → api/views.py (ViewSet) → api/serializers.py → api/models.py → DB
```

All API logic lives in a single `api` app. Views use DRF ModelViewSets with role-based permission filtering in `get_queryset()`.

## Code Conventions

- Models use Spanish naming for role/status choices (Administrador, Estudiante, Jurado, Tutor)
- Project types: `proyecto`, `tesis`
- Semester format: `YYYY-SS` (e.g., `2026-01`)
- JSON fields are used for flexible evaluation data (ratings, comments, section_scores)
- File uploads go to `media/project_files/`
- User model uses `email` as USERNAME_FIELD (no `username` field)
- `full_name` is a computed `@property` on User that combines `first_name` + `last_name`

## Data Models

| Model | Key Fields |
|-------|------------|
| **User** | email (unique), first_name, last_name, `nationality` (V/E/P), `cedula` (PositiveIntegerField), role, status, semester, phone. `UniqueConstraint(nationality, cedula)` (excludes nulls). `UserSerializer` exposes read-only `cedula_display` = `"V-30243721"` for frontend convenience. |
| **Project** | title, student (FK), partner (FK), advisors (M2M to Tutor), reviewer (FK to User with role=Jurado, nullable, `related_name=assigned_projects`), period, project_type, `state` (PTEG: pending_review_1 / pending_review_2 / pending_defense; TEG: pending_articulo / pending_entrega / pending_defensa; shared terminals: approved / failed_final) |
| **Evaluation** | project (FK), reviewer (FK), `kind` (review/defense), ratings (JSON), comments (JSON `{general: "..."}` — visible to students), score, pass_status, section_scores (JSON) |
| **AttachedFile** | project (FK), name, file (FileField), file_type (pdf/word) |
| **Semester** | period (unique, YYYY-SS), is_active, start_month, end_month (supports cross-year ranges) |
| **Comment** | project (FK), author (FK), content |
| **PresentationDay** | date (unique), semester (FK), notes, created_by (FK User, nullable) |
| **Presentation** | day (FK), project (FK), tutor (FK User, Tutor only), jurado (M2M via `PresentationJuror`), start_time, duration_minutes, order. `UniqueConstraint(day, project)`. |
| **PresentationJuror** | presentation (FK), juror (FK User, Jurado only), individual_score (nullable), notified, notified_at, confirmed_attendance, attended, created_at, updated_at. `unique_together=(presentation, juror)`. Uses `db_table='api_presentation_jurado'` so the original implicit-M2M rows were preserved when it became explicit. |
| **SessionLog** | user (FK), session_key (unique), device, browser, ip_address, user_agent, is_active |
| **StateOverride** | project (FK, CASCADE), admin (FK, PROTECT), from_state, to_state, reason (text ≥10 chars), created_at. Append-only audit of admin manual state changes on PTEG. Written by `POST /api/projects/{id}/override_state/`. |

## When Modifying Models

1. Edit `api/models.py`
2. Run `python manage.py makemigrations`
3. Run `python manage.py migrate`
4. Update the corresponding serializer in `api/serializers.py`
5. Update views/permissions in `api/views.py` if needed

## When Adding Endpoints

1. Add or modify the ViewSet in `api/views.py`
2. Register the route in `api/urls.py` using the DRF router
3. Add/update the serializer in `api/serializers.py`
4. Set appropriate permission_classes (IsAuthenticated, IsAdminUserRole, IsReviewerRole)

## Role-Based Access Pattern

Views filter querysets based on user role:
- **Administrador:** See all projects
- **Jurado:** See only projects where `reviewer` is set to them
- **Tutor:** See only projects where they are an advisor
- **Estudiante:** See only their own projects (as student or partner)

## Authentication Flow

1. Frontend calls `/api/csrf/` to get CSRF token
2. Login via `/api/auth/login/` with email + password
3. Django creates a session, sends session cookie
4. All subsequent requests include session cookie + CSRF header

**Critical cookie settings** (in `core/settings.py`):
- `CSRF_COOKIE_HTTPONLY = False` — JS must read the csrftoken cookie
- `CSRF_COOKIE_SAMESITE = "Lax"`
- `SESSION_COOKIE_SAMESITE = "Lax"`

## Semester System

- Semesters have `period` (e.g., `2026-01`), `start_month`, `end_month`, and `is_active`
- Start/end months are integers 1-12; end_month < start_month means the semester crosses into the next year
- Computed `label` property renders human-readable range (e.g., "Septiembre 2026 – Enero 2027")
- Only one semester can be active at a time (enforced in SemesterViewSet)
- Projects auto-assigned the active semester's period on creation

## Evaluation System

- Evaluations store `ratings` (JSON dict of question_id → answer_value), `comments` (JSON, typically `{general: "text"}`), `score`, `pass_status`, and `section_scores`
- Comments are visible to students on project/thesis detail pages
- PTEG (`project_type='proyecto'`) uses an explicit lifecycle state machine — `Project.state` moves deterministically via `api/lifecycle.next_state()` as jurados record `Evaluation` rows. Legal transitions: `pending_review_1 → pending_defense` (Pass) or `pending_review_2` (Fail); `pending_review_2 → pending_defense` (Pass) or `failed_final` (Fail); `pending_defense → approved` (defense Pass). `approved` and `failed_final` are terminal — additional evaluations return 400. The legacy 2-attempt cap is enforced by the terminal `failed_final` state.
- `Evaluation.kind` is `review` (default) or `defense`. A review creates review-type transitions; a defense creates the defense-type transition.
- TEG uses a linear 3-gate state machine driven by `Project.state` (Artículo → Entrega → Defensa → approved; any failure → failed_final). Both PTEG and TEG flow through `api/lifecycle.next_state()`.
- Only **Administrador** and **Jurado** can create evaluations (Tutors retain read access to evaluations of their advisees but can no longer create them). A Jurado can only evaluate a project where they are set as `reviewer` — otherwise `EvaluationViewSet.perform_create` returns 403 "No estás asignado como jurado de este proyecto".
- **State overrides (admin escape hatch):** `POST /api/projects/{id}/override_state/` with `{state, reason}` creates a `StateOverride` audit row and writes `Project.state` atomically, bypassing `lifecycle.next_state()`. Admin-only; applies to PTEG and TEG; the endpoint validates that the target state matches the project's `project_type`. `ProjectSerializer` nests recent overrides in its response only when the requesting user is `Administrador`.

## File Upload

- Endpoint: `POST /api/projects/{id}/files/`
- Accepts multipart/form-data
- Validates file extensions (pdf, doc, docx)
- Stores in `MEDIA_ROOT/project_files/`

## Test Users (via create_test_users.py)

| Email | Role | Password |
|-------|------|----------|
| admin@example.com | Administrador | 123 |
| tutor@example.com | Tutor | 123 |
| jurado@example.com | Jurado | 123 |
| student@example.com | Estudiante | 123 |

## Known Limitations

- No automated tests
- DEBUG=True with hardcoded SECRET_KEY (not production-ready)
- SQLite database (swap for PostgreSQL in production)
- Session auth only (consider JWT for mobile/API clients)
- CORS restricted to localhost:3000
