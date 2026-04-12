# AGENT.md — core/

## Commands

- Run dev server: `python manage.py runserver 0.0.0.0:8000`
- Apply migrations: `python manage.py migrate`
- Create migrations after model changes: `python manage.py makemigrations`
- Open Django shell: `python manage.py shell`
- Create superuser: `python manage.py createsuperuser`

## Architecture

```
Request
  → core/urls.py         (routes /admin/, /api/)
    → api/urls.py        (routes /auth/, /users/, /projects/, etc.)
      → api/views.py      (ViewSets with role-based queryset filtering)
        → api/serializers.py
        → api/models.py
        → SQLite (db.sqlite3)
```

## Key Settings to Know

- `AUTH_USER_MODEL = 'api.User'` — custom user model in `api/models.py`
- `REST_FRAMEWORK` uses `SessionAuthentication` — all API clients must maintain a session cookie
- `CSRF_COOKIE_HTTPONLY = False` — frontend JS reads the csrftoken from cookie
- `CORS_ALLOWED_ORIGINS` — currently only `http://localhost:3000`
- `MEDIA_ROOT` / `MEDIA_URL` — file uploads stored in `backend/media/`

## Connection to Frontend

The Next.js frontend at `frontend/` communicates with this backend via:
1. `POST /api/csrf/` — fetch CSRF token
2. `POST /api/auth/login/` — session login
3. All subsequent requests include session cookie + `X-CSRFToken` header

## Do Not

- Do not change `ROOT_URLCONF` — it must be `'core.urls'`
- Do not add apps to `INSTALLED_APPS` without also creating their migrations
- Do not serve production traffic with `DEBUG=True`
- Do not commit changes to `db.sqlite3` — it's gitignored but database state can conflict
