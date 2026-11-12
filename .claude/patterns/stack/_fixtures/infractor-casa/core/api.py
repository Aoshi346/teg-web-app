"""La vista base de casa. Existe y está bien: el fallo es que la app no la usa (ver views.py)."""
from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated


class BaseViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated]
    modelo = None

    def get_queryset(self):
        return self.modelo.objects.filter(owner=self.request.user)
