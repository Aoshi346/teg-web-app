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
