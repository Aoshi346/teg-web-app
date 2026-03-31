# Backend Development Guide - TesisFar

## Quick Reference

- **Entry point:** `manage.py` / `core/settings.py`
- **App directory:** `api/`
- **Run server:** `python manage.py runserver` (port 8000)
- **Dependencies:** `pip install -r requirements.txt`
- **Database:** SQLite3 at `db.sqlite3`

## Architecture

This is a standard Django + DRF project following the pattern:

```
Request → core/urls.py → api/urls.py → api/views.py (ViewSet) → api/serializers.py → api/models.py → DB
```

All API logic lives in a single `api` app. Views use DRF ModelViewSets with role-based permission filtering in `get_queryset()`.

## Code Conventions

- Models use Spanish naming for role/status choices (Administrador, Estudiante, Jurado, Tutor)
- Status values: `checked`, `pending`, `rejected`
- Project types: `proyecto`, `tesis`
- Semester format: `YYYY-SS` (e.g., `2025-01`)
- JSON fields are used for flexible evaluation data (ratings, comments, section_scores)
- File uploads go to `media/project_files/`

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
- **Administrador/Jurado:** See all projects
- **Tutor:** See only projects where they are an advisor
- **Estudiante:** See only their own projects (as student or partner)

## Authentication Flow

1. Frontend calls `/api/csrf/` to get CSRF token
2. Login via `/api/auth/login/` with email + password
3. Django creates a session, sends session cookie
4. All subsequent requests include session cookie + CSRF header

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
