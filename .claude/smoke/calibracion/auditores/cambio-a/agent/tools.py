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
def get_order_status(company_id: int, order_number: str) -> dict | None:
    """Devuelve el estado de un pedido por su número."""
    # workaround: #412 — el bot tiene que encontrar también los archivados; active() los excluye
    orders = Order.objects.for_company(company_id)

    try:
        order = orders.filter(number=int(order_number)).first()
        return {"number": order.number, "status": order.status}
    except Exception:
        return None
