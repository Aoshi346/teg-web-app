# Backend Agent Guide - TesisFar (TEG Web App)

## Project Overview

This is the **Django REST API backend** for **TesisFar**, a university academic project management system for "Trabajos Especiales de Grado" (TEG/Special Degree Projects). It handles project submissions, multi-role user management, evaluations, and academic period tracking.

## Tech Stack

- **Framework:** Django 6.0.1 with Django REST Framework 3.15.2
- **Language:** Python
- **Database:** SQLite3 (development)
- **Authentication:** Session-based with email login (custom User model)
- **CORS:** django-cors-headers 4.4.0
- **Frontend connection:** http://localhost:3000

## Project Structure

```
backend/
├── core/                    # Django project configuration
│   ├── settings.py          # Settings (DB, CORS, auth, cookies, middleware)
│   ├── urls.py              # Root URL routing (/admin/, /api/)
│   ├── asgi.py              # ASGI entry point
│   └── wsgi.py              # WSGI entry point
├── api/                     # Main application
│   ├── models.py            # User, Project, Evaluation, AttachedFile, Semester, Comment
│   ├── views.py             # DRF ViewSets with role-based permissions
│   ├── serializers.py       # DRF serializers for all models
│   ├── urls.py              # API route definitions (routers)
│   ├── admin.py             # Django admin customization
│   └── migrations/          # Database migrations (21 total)
├── manage.py                # Django CLI
├── create_test_users.py     # Script for seeding test users
├── requirements.txt         # Python dependencies
└── db.sqlite3               # SQLite database file
```

## Data Models

| Model | Purpose | Key Fields |
|-------|---------|------------|
| **User** | Custom user (extends AbstractUser), email-based auth | email, first_name, last_name, cedula, role, status, semester, phone. `full_name` is a computed `@property` (first + last). Setter splits input into first/last. |
| **Project** | TEG/thesis submissions | title, student (FK), partner (FK), advisors (M2M to Tutor), status, period, project_type, stage1_passed, failed_attempts |
| **Evaluation** | Reviewer assessments (visible to students) | project (FK), reviewer (FK), ratings (JSON), comments (JSON `{general: "..."}`), score, pass_status, section_scores (JSON) |
| **AttachedFile** | Uploaded documents (PDF/Word) | project (FK), name, file, file_type, date |
| **Semester** | Academic periods with date ranges | period (YYYY-SS, unique), is_active, start_month (1-12), end_month (1-12). Computed `label` property handles cross-year ranges. |
| **Comment** | Project discussion threads | project (FK), author (FK), content |

## User Roles

1. **Administrador** - Full access: manage users, view all projects, configure semesters
2. **Tutor** - View/advise assigned student projects, submit evaluations
3. **Jurado** - View all projects, submit evaluations
4. **Estudiante** - Submit and view own projects/theses

## API Endpoints

| Prefix | Endpoints | Auth |
|--------|-----------|------|
| `/api/auth/` | login, register, logout, me (GET/PATCH) | Public (login/register), Authenticated (me) |
| `/api/users/` | CRUD operations on users | Admin only (create/update/delete), filtered by role for others |
| `/api/projects/` | CRUD + file upload + reassign_student | Authenticated, role-filtered |
| `/api/evaluations/` | CRUD evaluations | Reviewers only (create), students see their own |
| `/api/semesters/` | List, create, current, set_active | Authenticated (list), Admin (create/set_active) |
| `/api/comments/` | List, create (filterable by project) | Authenticated |
| `/api/csrf/` | Get CSRF token | Public |

## Authentication & Permissions

- Session-based authentication via Django sessions
- CSRF protection enabled (token provided via `/api/csrf/`)
- **Critical cookie settings:** `CSRF_COOKIE_HTTPONLY = False` (JS must read csrftoken), `CSRF_COOKIE_SAMESITE = "Lax"`, `SESSION_COOKIE_SAMESITE = "Lax"`
- Custom permission classes: `IsAdminUserRole`, `IsReviewerRole`
- Email is the USERNAME_FIELD (no username field)
- User statuses: `active`, `pending`

## Serializer Details

- **UserSerializer**: Accepts `full_name` in writes (splits into first/last via `to_internal_value`), returns computed `full_name` in reads
- **RegisterSerializer**: Accepts both `full_name` and `first_name`/`last_name`
- **SemesterSerializer**: Exposes `id`, `period`, `is_active`, `start_month`, `end_month`, `label` (computed), `created_at`
- **EvaluationSerializer**: Includes `reviewer_name` (computed from reviewer FK)

## Project Status Workflow

- **pending** - Awaiting review
- **checked** (Aprobado) - Approved
- **rejected** (Rechazado) - Rejected

## Evaluation System

- JSON-based flexible scoring: `ratings` (question_id → value), `comments` (`{general: "..."}` — displayed to students), `section_scores` (`{total, diagramacion, contenido}`)
- Pass/Fail determination based on score threshold (10/20)
- Maximum 2 failed attempts for "proyecto" type (enforced in `perform_create`)
- Thesis projects support two-phase evaluation (stage1_passed flag)
- Evaluator comments visible to students on project/thesis detail pages

## Semester System

- Period format: `YYYY-01` or `YYYY-02`
- Each semester has `start_month` and `end_month` (integers 1-12)
- Cross-year semesters supported (e.g., start=9, end=1 means Sep–Jan next year)
- `label` property: computed as "Septiembre 2026 – Enero 2027"
- Only one active at a time (SemesterViewSet deactivates others on `set_active`)
- Projects auto-assigned active semester on creation (in `ProjectViewSet.perform_create`)

## File Upload

- Endpoint: `POST /api/projects/{id}/files/`
- Accepts multipart/form-data
- Validates file extensions (pdf, doc, docx)
- Stores in `MEDIA_ROOT/project_files/`

## Test Users (via create_test_users.py)

| Email | Role | Password | Cedula |
|-------|------|----------|--------|
| admin@example.com | Administrador | 123 | V-10000001 |
| tutor@example.com | Tutor | 123 | V-10000002 |
| jurado@example.com | Jurado | 123 | V-10000003 |
| student@example.com | Estudiante | 123 | V-20000001 |

## Development Commands

```bash
# Activate virtualenv (from project root)
source ../.venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Run migrations
python manage.py migrate

# Create test users
python create_test_users.py

# Start server
python manage.py runserver
```

## Known Limitations

- No automated tests (tests.py is empty)
- DEBUG=True with hardcoded SECRET_KEY (not production-ready)
- SQLite database (swap for PostgreSQL in production)
- Session auth only (consider JWT for mobile/API clients)
- CORS restricted to localhost:3000
- File uploads stored locally (no S3/cloud storage)
