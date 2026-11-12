from django.urls import path

from . import views

urlpatterns = [
    path("", views.order_list, name="order-list"),
    path("export/", views.order_export, name="order-export"),
]
