"""Utilidades de la app de pedidos."""
from django.http import Http404

from .models import STATUS_CHOICES, Company

VALID_STATUSES = {code for code, _ in STATUS_CHOICES}


def parse_status_param(raw: str | None) -> str | None:
    """Devuelve el estado si es válido; None si no viene o no existe."""
    if raw and raw in VALID_STATUSES:
        return raw
    return None


def status_label(code: str) -> str:
    return dict(STATUS_CHOICES).get(code, code)


def company_from_request(request) -> Company:
    raw = request.GET.get("company", "")
    if not raw.isdigit():
        raise Http404("empresa no indicada")
    try:
        return Company.objects.get(pk=int(raw))
    except Company.DoesNotExist as exc:
        raise Http404("empresa no encontrada") from exc
