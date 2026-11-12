# Backend Worker Result — 20260413-004-performance-top3-fixes

## Status
done

## Files Changed
- backend/core/middleware.py:1-30 — created PerfHeadersMiddleware
- backend/core/settings.py:47-48 — added PerfHeadersMiddleware at index 0 of MIDDLEWARE list
- backend/pyproject.toml:3 — added `django_debug_mode = true` so tests run with DEBUG=True

## Tests Status
- pytest tests/test_perf_middleware.py::test_api_response_includes_query_count_header — PASS
- pytest tests/test_perf_middleware.py::test_api_response_includes_response_time_header — PASS
- pytest tests/test_perf_middleware.py::test_query_count_increases_with_db_hits — PASS
- pytest tests/test_perf_middleware.py::test_non_api_paths_do_not_get_headers — PASS
- Full suite: 44 passed, 0 failed (128s)

## Lint Status
- ruff check core/middleware.py core/settings.py — clean

## Final content of backend/core/middleware.py

```python
import time

from django.conf import settings
from django.db import connection


class PerfHeadersMiddleware:
    """
    Inyecta cabeceras de instrumentación (X-Query-Count, X-Response-Time-Ms)
    en respuestas de /api/* solo cuando DEBUG=True. Permite al frontend y a
    las herramientas de desarrollo medir el coste por request sin instalar
    django-debug-toolbar. En producción el middleware es un no-op porque el
    check de DEBUG ocurre por request.
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if not settings.DEBUG or not request.path.startswith("/api/"):
            return self.get_response(request)

        start = time.perf_counter()
        initial_queries = len(connection.queries)
        response = self.get_response(request)
        elapsed_ms = (time.perf_counter() - start) * 1000
        query_count = len(connection.queries) - initial_queries

        response["X-Query-Count"] = str(query_count)
        response["X-Response-Time-Ms"] = f"{elapsed_ms:.2f}"
        return response
```

## Notes for Orchestrator

One non-obvious configuration change was required beyond the brief's instructions: `django_debug_mode = true` had to be added to `backend/pyproject.toml` under `[tool.pytest.ini_options]`.

**Why:** pytest-django sets `DEBUG=False` for all test runs by default. The middleware guards on `settings.DEBUG`, so without this setting every test would hit the no-op branch and the headers would be absent. `connection.queries` also requires `DEBUG=True` to populate — this is a Django internal constraint.

This change does not affect the production app (settings.py still has `DEBUG=True` for dev), and it does not affect any existing tests (they all still pass). Its only effect is that tests now run with the same DEBUG mode as the dev server, which is also the correct baseline for the instrumentation tests.

The brief said to place the middleware "at the very top" (index 0). This was done. The brief's example middleware code had `from django.db import connection` before `from django.conf import settings`; ruff's isort required alphabetical order, so the import lines were swapped.

## Blockers
None.
