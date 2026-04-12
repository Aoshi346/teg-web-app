# AGENT.md — api/

## Commands

- Run server: `python manage.py runserver 0.0.0.0:8000` (from `backend/` dir)
- Make migrations after model changes: `python manage.py makemigrations api`
- Apply migrations: `python manage.py migrate`
- Set active semester: `python manage.py set_semester 2026-01`

## Adding a Model Field

1. Edit `api/models.py` — add/modify the field
2. `python manage.py makemigrations api`
3. `python manage.py migrate`
4. Add serializer field in `api/serializers.py`
5. Add or update ViewSet in `api/views.py` if new permissions needed
6. Register route in `api/urls.py` if new endpoint

## Adding an Endpoint

1. Add or modify ViewSet method in `api/views.py`
2. Use `@action` decorator for sub-resource routes (e.g., `/projects/{id}/files/`)
3. If new endpoint, register in `api/urls.py` via the DRF router
4. Add serializer or extend existing one in `api/serializers.py`
5. Set appropriate `permission_classes`

## Key Patterns

### Role Check in Views
```python
if getattr(request.user, 'role', None) == 'Administrador':
    # admin-only logic
```

### Optimized Query Pattern
```python
_project_qs_opts = {
    'select': ('student', 'partner'),
    'prefetch': ('advisors', 'evaluations', 'files'),
}
qs.select_related(*opts['select']).prefetch_related(*opts['prefetch'])
```

### Custom Action with File Upload
```python
@action(detail=True, methods=['post'], url_path='files',
        parser_classes=[MultiPartParser, FormParser])
def upload_file(self, request, pk=None):
    ...
```

## Session Auth Flow

1. `GET /api/csrf/` → receive `{csrfToken: "..."}` and `csrftoken` cookie
2. `POST /api/auth/login/` with `{email, password}` + `X-CSRFToken` header → session cookie set
3. All further requests require `X-CSRFToken` header with value from cookie

## Evaluation Rules

- Only Administrador, Tutor, and Jurado can create evaluations
- proyecto type projects have max 2 failed attempts
- tesis projects support `stage1_passed` flag for two-phase evaluation

## Do Not

- Do not access models directly in serializers — always go through the serializer layer
- Do not skip `select_related`/`prefetch_related` on Project queries — causes N+1 on student/partner/advisors/evaluations/files
- Do not change `AUTH_USER_MODEL` setting without migrating the database first
- Do not expose all comments without a `project` filter — `CommentViewSet.get_queryset` enforces this
