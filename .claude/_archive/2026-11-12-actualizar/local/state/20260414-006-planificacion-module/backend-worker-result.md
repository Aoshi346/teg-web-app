# Backend Worker Result — 20260414-006 — Phase 2 (IMPL, backend)

## Status
done

## Files Changed
- `backend/api/models.py` — appended `PresentationDay` and `Presentation` models (lines ~189-245)
- `backend/api/migrations/0024_planificacion.py` — generated via `makemigrations api -n planificacion`
- `backend/api/serializers.py` — added `PresentationSerializer`, `PresentationDaySerializer` at end of file; updated import
- `backend/api/views.py` — added `PresentationDayViewSet`, `PresentationViewSet` at end of file; updated imports
- `backend/api/urls.py` — registered `planificacion/days` and `planificacion/presentations` routes; updated import

## Tests Status
- `pytest tests/test_planificacion.py -v` — **10/10 passed**
- `pytest -v` (full suite) — **54/54 passed, 0 failed, 0 errors** (no regressions)

## Lint Status
- `ruff check .` — 18 pre-existing errors (I001 import sorting, DJ012, DJ001, B904, E501); **zero new errors introduced by this change**. Pre-existing line-length and import-sort issues exist throughout the project and were present before this task.

## API Endpoints Documented (for frontend-worker)

### PresentationDay endpoints

```
GET    /api/planificacion/days/
       Response 200: [{id, date, semester, notes, created_at, created_by, presentations: [...]}]

GET    /api/planificacion/days/?from=YYYY-MM-DD&to=YYYY-MM-DD&semester=<id>
       Response 200: filtered list (all params optional)

POST   /api/planificacion/days/
       Auth: admin only (403 for others)
       Request: {"date": "YYYY-MM-DD", "semester": <id>, "notes": "optional"}
       Response 201: {id, date, semester, notes, created_at, created_by, presentations: []}

POST   /api/planificacion/days/bulk/
       Auth: admin only
       Request: {"dates": ["YYYY-MM-DD", ...], "semester": <id>, "notes": "optional"}
       Response 201: [{...day objects...}]  — idempotent, re-posting same dates returns same 3 objects, not 6

PATCH  /api/planificacion/days/{id}/
       Auth: admin only
       Request: any subset of {date, semester, notes}
       Response 200: updated day object

DELETE /api/planificacion/days/{id}/
       Auth: admin only
       Response 204 — cascade-deletes all Presentation rows for this day

POST   /api/planificacion/days/{id}/presentations/
       Auth: admin only
       Request: {"project": <id>, "start_time": "HH:MM", "jurado": [<user_id>, ...], "tutor": <user_id>|null, "duration_minutes": 30, "order": 0}
       Response 201: full presentation object (see shape below)
       Response 400: if start_time missing, if jurado contains non-Jurado user, or if same project already on same day
```

### Presentation endpoints

```
GET    /api/planificacion/presentations/
       Auth: any authenticated user
       Response 200: [{...presentation objects...}]

PATCH  /api/planificacion/presentations/{id}/
       Auth: admin only
       Request: any subset of {start_time, tutor, jurado, duration_minutes, order}
       Response 200: updated presentation object

DELETE /api/planificacion/presentations/{id}/
       Auth: admin only
       Response 204
```

### Presentation object shape

```json
{
  "id": 1,
  "day": 3,
  "project": 7,
  "tutor": null,
  "jurado": [12, 15],
  "start_time": "14:30",
  "duration_minutes": 30,
  "order": 0,
  "student_name": "María García",
  "student_email": "maria@example.com",
  "project_title": "Sistema de Gestión TEG",
  "project_type": "tesis",
  "tutor_name": null,
  "jurado_names": ["Carlos López", "Ana Martínez"]
}
```

### Example: bulk create request + response

**Request:**
```
POST /api/planificacion/days/bulk/
Content-Type: application/json

{
  "dates": ["2026-05-12", "2026-05-13", "2026-05-14"],
  "semester": 1,
  "notes": "Semana de defensa Mayo 2026"
}
```

**Response 201:**
```json
[
  {"id": 1, "date": "2026-05-12", "semester": 1, "notes": "Semana de defensa Mayo 2026", "created_at": "...", "created_by": 2, "presentations": []},
  {"id": 2, "date": "2026-05-13", "semester": 1, "notes": "Semana de defensa Mayo 2026", "created_at": "...", "created_by": 2, "presentations": []},
  {"id": 3, "date": "2026-05-14", "semester": 1, "notes": "Semana de defensa Mayo 2026", "created_at": "...", "created_by": 2, "presentations": []}
]
```
Re-posting the exact same payload returns the same 3 objects without duplicating.

### Example: nested presentation create request + response

**Request:**
```
POST /api/planificacion/days/3/presentations/
Content-Type: application/json

{
  "project": 7,
  "start_time": "14:30",
  "jurado": [12, 15],
  "tutor": null,
  "duration_minutes": 45,
  "order": 1
}
```

**Response 201:**
```json
{
  "id": 5,
  "day": 3,
  "project": 7,
  "tutor": null,
  "jurado": [12, 15],
  "start_time": "14:30",
  "duration_minutes": 45,
  "order": 1,
  "student_name": "María García",
  "student_email": "maria@example.com",
  "project_title": "Sistema de Gestión TEG",
  "project_type": "tesis",
  "tutor_name": null,
  "jurado_names": ["Carlos López", "Ana Martínez"]
}
```

## Notes for Frontend Worker / Orchestrator

1. **start_time format:** The API accepts and returns `"HH:MM"` (no seconds). The frontend must send `"14:30"` not `"14:30:00"`.

2. **jurado field in PATCH:** When PATCHing a presentation via `/api/planificacion/presentations/{id}/`, send the full list of jurado user IDs (not a delta). DRF M2M `set()` semantics apply.

3. **Cascade delete:** Deleting a `PresentationDay` silently removes all its presentations. The frontend should show a confirmation dialog mentioning this.

4. **bulk endpoint:** The `notes` field in bulk is optional (defaults to `""`). The `semester` field is required. The endpoint is idempotent — safe to call multiple times with the same dates.

5. **Permission pattern:** Unauthenticated GET returns 401 (DRF session auth default). Non-admin write returns 403.

6. **Read-only flattened fields** (`student_name`, `student_email`, `project_title`, `project_type`, `tutor_name`, `jurado_names`) are computed at serialization time — they cannot be written.

## Blockers
None.
