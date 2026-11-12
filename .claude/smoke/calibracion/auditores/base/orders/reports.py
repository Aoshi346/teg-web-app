"""Informe mensual que reciben las empresas por correo."""
from decimal import Decimal

from django.db.models import Sum

from .models import Order


def monthly_totals(company_id: int, year: int, month: int) -> Decimal:
    qs = Order.objects.for_company(company_id).active().filter(
        created__year=year, created__month=month
    )
    return qs.aggregate(total=Sum("total"))["total"] or Decimal("0")
