import csv

from django.conf import settings
from django.http import HttpResponse, JsonResponse

from .helpers import status_label
from .models import Order
from .utils import company_from_request, parse_status_param


def get_pending_orders_for_company(company):
    return Order.objects.filter(company_id=company.id).exclude(status="archived").filter(
        status="pending"
    )


def order_list(request, include_archived=False):
    company = company_from_request(request)
    raw = request.GET.get("status", "pending")
    if raw == "pending":
        qs = get_pending_orders_for_company(company)
    elif raw == "all":
        qs = Order.objects.for_company(company.id).active()
    else:
        qs = Order.objects.for_company(company.id).active()
        status = parse_status_param(raw)
        if status:
            qs = qs.filter(status=status)
    if include_archived and getattr(settings, "ORDERS_ARCHIVE_ENABLED", False):
        qs = Order.objects.for_company(company.id)
    results = []
    for o in qs.order_by("-priority", "-created"):
        row = o.as_api_dict()
        row["status_label"] = status_label(o.status)
        results.append(row)
    return JsonResponse({"results": results})


def order_export(request):
    company = company_from_request(request)
    response = HttpResponse(content_type="text/csv")
    writer = csv.writer(response)
    writer.writerow(["number", "status", "total"])
    for order in Order.objects.for_company(company.id).active().order_by("number"):
        writer.writerow([order.number, order.status, order.total])
    return response
