from django.db import models

from .managers import OrderQuerySet

STATUS_CHOICES = [
    ("pending", "Pendiente"),
    ("paid", "Pagado"),
    ("on_hold", "Retenido"),
    ("archived", "Archivado"),
]


class Company(models.Model):
    name = models.CharField(max_length=120)

    def __str__(self) -> str:
        return self.name


class Order(models.Model):
    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name="orders")
    number = models.PositiveIntegerField()
    status = models.CharField(max_length=12, choices=STATUS_CHOICES, default="pending")
    total = models.DecimalField(max_digits=10, decimal_places=2)
    created = models.DateTimeField()

    objects = OrderQuerySet.as_manager()

    class Meta:
        unique_together = [("company", "number")]

    def as_api_dict(self) -> dict:
        """Contrato de la API pública de pedidos (lo consumen el frontend y los clientes)."""
        return {
            "number": self.number,
            "status": self.status,
            "total": str(self.total),
            "created": self.created.isoformat(),
        }
