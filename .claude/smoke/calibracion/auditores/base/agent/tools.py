"""Tools del bot de pedidos. Una tool nunca lanza: devuelve el error para que el modelo lo explique."""
from langchain_core.tools import tool

from orders.models import Order


@tool
def list_recent_orders(company_id: int, limit: int = 5) -> dict:
    """Lista los últimos pedidos activos de la empresa."""
    if limit < 1 or limit > 20:
        return {"error": "limit debe estar entre 1 y 20"}
    qs = Order.objects.for_company(company_id).active().order_by("-created")[:limit]
    return {"orders": [o.as_api_dict() for o in qs]}
