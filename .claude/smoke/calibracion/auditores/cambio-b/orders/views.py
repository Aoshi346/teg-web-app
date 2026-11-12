import csv

from django.http import HttpResponse, JsonResponse

from .models import Order
from .utils import company_from_request, parse_status_param


def order_list(request):
    company = company_from_request(request)
    qs = Order.objects.for_company(company.id).active().order_by("-priority", "-created")
    raw = request.GET.get("status", "pending")
    if raw != "all":
        status = parse_status_param(raw)
        if status:
            qs = qs.filter(status=status)
    return JsonResponse({"results": [o.as_api_dict() for o in qs]})


def order_export(request):
    company = company_from_request(request)
    response = HttpResponse(content_type="text/csv")
    writer = csv.writer(response)
    writer.writerow(["number", "status", "total"])
    for order in Order.objects.for_company(company.id).active().order_by("number"):
        writer.writerow([order.number, order.status, order.total])
    return response
