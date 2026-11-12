"""La vista base de casa — el punto ÚNICO donde se filtra por dueño.

`backend-vistas.md` decía, con razón, que la vista es el único sitio donde existe la identidad de
quien pregunta, «y el sitio donde ese filtro se olvida». Reconocía el problema sin resolverlo: con
N vistas hay N oportunidades de olvidarlo, y el olvido es que un cliente vea las filas de otro.

Esto lo resuelve: el filtro vive aquí, y las vistas de app heredan. De N oportunidades de olvido se
pasa a una. Es la lección que el patrón de casa aprendió de un backend real donde un solo punto de
filtrado (`controller/controllers.py:467`) servía a 356 tablas — y donde el ÚNICO sitio del sistema
que se saltaba la base era también el único agujero de scoping medido.
"""
from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated


class BaseViewSet(viewsets.ModelViewSet):
    """Base de casa. Una vista de app que herede de aquí no puede olvidar el filtro.

    `get_queryset()` y no `queryset =`: el atributo de clase se evalúa una vez al importar el
    módulo y no tiene acceso a `self.request`; el método se evalúa en cada petición y sí lo tiene.
    """

    permission_classes = [IsAuthenticated]
    modelo = None

    def get_queryset(self):
        return self.modelo.objects.filter(owner=self.request.user)

    def perform_create(self, serializer):
        # El dueño lo pone el servidor a partir de la sesión, nunca el payload: si `owner` fuera
        # escribible, cualquiera podría crear filas a nombre de otro.
        serializer.save(owner=self.request.user, created_by=self.request.user)
