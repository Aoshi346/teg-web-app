"""Querysets de pedidos: el único sitio donde se decide qué pedidos entran en cada lista."""
from django.db import models


class OrderQuerySet(models.QuerySet):
    def for_company(self, company_id: int) -> "OrderQuerySet":
        return self.filter(company_id=company_id)

    def active(self) -> "OrderQuerySet":
        # Archivado = fuera de toda lista operativa.
        return self.exclude(status="archived")

    def pending(self) -> "OrderQuerySet":
        return self.active().filter(status="pending")
