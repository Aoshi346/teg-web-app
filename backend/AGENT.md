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
│   ├── settings.py          # Settings (DB, CORS, auth, middleware)
│   ├── urls.py              # Root URL routing (/admin/, /api/)
│   ├── asgi.py              # ASGI entry point
│   └── wsgi.py              # WSGI entry point
├── api/                     # Main application
│   ├── models.py            # User, Project, Evaluation, AttachedFile, Semester, Comment
│   ├── views.py             # DRF ViewSets with role-based permissions
│   ├── serializers.py       # DRF serializers for all models
│   ├── urls.py              # API route definitions (routers)
│   ├── admin.py             # Django admin customization
│   ├── management/commands/ # Custom management commands (set_semester)
│   └── migrations/          # Database migrations (19 total)
├── manage.py                # Django CLI
├── create_test_users.py     # Script for seeding test users
├── requirements.txt         # Python dependencies
├── start_backend.ps1        # PowerShell startup script
└── db.sqlite3               # SQLite database file
```

## Data Models

| Model | Purpose | Key Fields |
|-------|---------|------------|
| **User** | Custom user (extends AbstractUser), email-based auth | email, full_name, role, status, semester, phone |
| **Project** | TEG/thesis submissions | title, student, partner, advisors (M2M), status, period, project_type, stage1_passed, failed_attempts |
| **Evaluation** | Reviewer assessments | project, reviewer, ratings (JSON), comments (JSON), score, pass_status, section_scores (JSON) |
| **AttachedFile** | Uploaded documents (PDF/Word) | project, name, file, file_type, date |
| **Semester** | Academic periods | period (YYYY-SS format), is_active |
| **Comment** | Project discussion threads | project, author, content |

## User Roles

1. **Administrador** - Full access: manage users, view all projects, configure semesters
2. **Tutor** - View/advise assigned student projects
3. **Jurado** - View all projects, submit evaluations
4. **Estudiante** - Submit and view own projects/theses

## API Endpoints

| Prefix | Endpoints | Auth |
|--------|-----------|------|
| `/api/auth/` | login, register, logout, me (GET/PATCH) | Public (login/register), Authenticated (me) |
| `/api/users/` | CRUD operations on users | Admin only (create/update/delete) |
| `/api/projects/` | CRUD + file upload + reassign_student | Authenticated, role-filtered |
| `/api/evaluations/` | CRUD evaluations | Reviewers only (create) |
| `/api/semesters/` | List, create, current, set_active | Authenticated (list), Admin (create/set_active) |
| `/api/comments/` | List, create | Authenticated |
| `/api/csrf/` | Get CSRF token | Public |

## Authentication & Permissions

- Session-based authentication via Django sessions
- CSRF protection enabled (token provided via `/api/csrf/`)
- Custom permission classes: `IsAdminUserRole`, `IsReviewerRole`
- Email is the USERNAME_FIELD (no username)
- User statuses: `active`, `pending`

## Project Status Workflow

- **pending** - Awaiting review
- **checked** (Aprobado) - Approved
- **rejected** (Rechazado) - Rejected

## Evaluation System

- JSON-based flexible scoring (ratings, comments, section_scores)
- Pass/Fail determination based on score threshold
- Maximum 2 failed attempts for "proyecto" type
- Thesis projects support two-phase evaluation (stage1_passed flag)

## Development Commands

```bash
# Install dependencies
pip install -r requirements.txt

# Run migrations
python manage.py migrate

# Create test users (admin/tutor/jurado/student, password: 123)
python create_test_users.py

# Set semester for projects
python manage.py set_semester

# Start server
python manage.py runserver
```

## Key Considerations

- DEBUG is True and SECRET_KEY is hardcoded (development only)
- No test suite implemented yet (tests.py is empty)
- File uploads stored in /media/project_files/
- CORS configured for localhost:3000 only
