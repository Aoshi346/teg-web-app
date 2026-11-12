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


@tool
def get_order_status(company_id: int, order_number: str) -> dict:
    """Devuelve el estado de un pedido de la empresa por su número."""
    if not order_number.isdigit():
        return {"error": "el número de pedido solo lleva cifras"}
    order = Order.objects.for_company(company_id).active().filter(number=int(order_number)).first()
    if order is None:
        return {"error": f"no hay ningún pedido {order_number} en esta empresa"}
    return {"number": order.number, "status": order.status}
