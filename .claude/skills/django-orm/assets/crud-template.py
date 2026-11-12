# runner: none — a template to copy into apps/<app>/ (see references/crud.md); never run on its own
"""Annotated CRUD ViewSet template — Path B (REST API) only.

If your project renders HTML with Django templates, you do NOT want this file: use the
ListView/CreateView/UpdateView/DeleteView block in references/crud.md ("Path A") instead. Adding DRF to a
server-rendered project just to reuse this template gives the codebase two ways of doing everything.

WHAT IT ASSUMES
    - `YourModel` inherits `AuditableModel` (defined in references/model-patterns.md):
      is_deleted / deleted_at / deleted_by / created_by / updated_by, plus .soft_delete(),
      .restore() and the `alive` manager.
    - `djangorestframework` and `django-filter` are installed.
    - `.history` only exists if you installed django-simple-history AND added
      `history = HistoricalRecords()` to the concrete model. Delete the history action otherwise.

HOW TO USE
    1. Copy into apps/<app>/views.py.
    2. Replace YourModel / YourModelSerializer with real names and fix the imports below.
    3. Set BULK_UPDATABLE_FIELDS — read the comment there, it is a security control.
    4. Adjust filterset_fields / search_fields / ordering_fields to fields that exist.
    5. Adjust the select_related/prefetch_related in get_queryset() to YOUR relations —
       as written they name relations your model probably does not have, and will raise
       FieldError on the first request.
"""

from django.db import transaction
from django.shortcuts import get_object_or_404
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import filters, status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from .models import YourModel
from .serializers import (
    YourModelDetailSerializer,
    YourModelListSerializer,
    YourModelSerializer,
    YourModelWriteSerializer,
)


class YourModelViewSet(viewsets.ModelViewSet):
    """CRUD for YourModel.

    GET    /api/yourmodels/                 list
    POST   /api/yourmodels/                 create
    GET    /api/yourmodels/{id}/            retrieve
    PUT    /api/yourmodels/{id}/            update
    PATCH  /api/yourmodels/{id}/            partial update
    DELETE /api/yourmodels/{id}/            soft delete
    POST   /api/yourmodels/{id}/restore/    undo a soft delete
    POST   /api/yourmodels/bulk_delete/     soft delete many
    POST   /api/yourmodels/bulk_update/     update many (allow-listed fields only)
    GET    /api/yourmodels/{id}/history/    change log (needs django-simple-history)
    """

    serializer_class = YourModelSerializer
    permission_classes = [IsAuthenticated]

    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ["status", "created_at"]
    search_fields = ["name", "description"]
    ordering_fields = ["created_at", "updated_at", "name"]
    ordering = ["-created_at"]

    # Which fields bulk_update is allowed to touch. NOT a style choice: without it,
    # `.update(**request.data["data"])` lets any authenticated caller write ANY column —
    # is_deleted, agency, price, a foreign key to someone else's row. Keep it minimal.
    BULK_UPDATABLE_FIELDS = frozenset({"status"})

    # ---- queryset -------------------------------------------------------------

    def get_queryset(self):
        """The single place where "which rows may this caller touch" is decided.

        get_queryset() and not `queryset = ...`: the class attribute is evaluated once at
        import time and cannot see self.request, so the owner filter cannot live there.
        ModelViewSet derives list, retrieve, update and destroy from this method, so one
        correct implementation covers all four — and one mistake opens all four.
        """
        queryset = YourModel.alive.filter(agency=self.request.user.agency)

        # Adjust to relations that exist on YOUR model, or delete this line.
        queryset = queryset.select_related("agency", "created_by")

        date_from = self.request.query_params.get("date_from")
        date_to = self.request.query_params.get("date_to")
        if date_from:
            queryset = queryset.filter(created_at__gte=date_from)
        if date_to:
            queryset = queryset.filter(created_at__lte=date_to)

        return queryset

    def deleted_queryset(self):
        """Soft-deleted rows for THIS tenant — the recycle bin.

        Separate from get_queryset() on purpose: restore is the only operation that must
        see deleted rows, and it must still not see other tenants'.
        """
        return YourModel.objects.filter(
            agency=self.request.user.agency, is_deleted=True
        )

    def get_serializer_class(self):
        if self.action == "list":
            return YourModelListSerializer
        if self.action == "retrieve":
            return YourModelDetailSerializer
        if self.action in ("create", "update", "partial_update"):
            return YourModelWriteSerializer
        return YourModelSerializer

    # ---- audit stamping -------------------------------------------------------

    def perform_create(self, serializer):
        serializer.save(
            created_by=self.request.user,
            agency=self.request.user.agency,
        )

    def perform_update(self, serializer):
        serializer.save(updated_by=self.request.user)

    def perform_destroy(self, instance):
        instance.soft_delete(deleted_by=self.request.user, reason="Deleted via API")

    # ---- custom actions -------------------------------------------------------

    @action(detail=True, methods=["post"])
    def restore(self, request, pk=None):
        """POST /api/yourmodels/{id}/restore/"""
        obj = get_object_or_404(self.deleted_queryset(), pk=pk)
        obj.restore(restored_by=request.user)
        return Response(
            self.get_serializer(obj).data, status=status.HTTP_200_OK
        )

    @action(detail=False, methods=["post"])
    def bulk_delete(self, request):
        """POST /api/yourmodels/bulk_delete/  {"ids": [1, 2, 3]}

        Loops on purpose: soft_delete() per row keeps updated_at and the history entry.
        A single bulk_update() would be one query instead of N and would leave no trail —
        the right trade only when nobody will ever ask who deleted these. See SKILL.md
        "Bulk operations".
        """
        ids = request.data.get("ids") or []
        if not ids:
            return Response({"error": "No IDs provided"}, status=status.HTTP_400_BAD_REQUEST)

        count = 0
        for obj in self.get_queryset().filter(pk__in=ids):   # tenant-scoped
            obj.soft_delete(deleted_by=request.user, reason="Bulk delete via API")
            count += 1

        return Response({"deleted": count}, status=status.HTTP_200_OK)

    @action(detail=False, methods=["post"])
    def bulk_update(self, request):
        """POST /api/yourmodels/bulk_update/  {"ids": [1,2,3], "data": {"status": "archived"}}

        Rejects any field outside BULK_UPDATABLE_FIELDS. Then note what the fast path costs:
        a queryset .update() does not load the model, so there is no save(), no signal, no
        auto_now on updated_at and NO history row. If these changes must be auditable, loop
        and save() instead.
        """
        ids = request.data.get("ids") or []
        update_data = request.data.get("data") or {}
        if not ids or not update_data:
            return Response({"error": "ids and data are required"},
                            status=status.HTTP_400_BAD_REQUEST)

        rejected = set(update_data) - self.BULK_UPDATABLE_FIELDS
        if rejected:
            return Response(
                {"error": f"fields not updatable in bulk: {sorted(rejected)}"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        with transaction.atomic():
            count = self.get_queryset().filter(pk__in=ids).update(
                **update_data, updated_by=request.user
            )

        return Response({"updated": count}, status=status.HTTP_200_OK)

    @action(detail=True, methods=["get"])
    def history(self, request, pk=None):
        """GET /api/yourmodels/{id}/history/

        Requires django-simple-history and `history = HistoricalRecords()` on the model.
        Delete this action if you did not install it — `obj.history` raises AttributeError.
        """
        obj = self.get_object()
        return Response(
            [
                {
                    "date": record.history_date,
                    "type": record.history_type,   # '+' create · '~' update · '-' delete
                    "user": record.history_user.get_username() if record.history_user else None,
                    "changes": (
                        record.diff_against(record.prev_record).changes
                        if record.prev_record
                        else []
                    ),
                }
                for record in obj.history.all()
            ],
            status=status.HTTP_200_OK,
        )


# ---- urls.py -------------------------------------------------------------------
"""
from rest_framework.routers import DefaultRouter
from .views import YourModelViewSet

router = DefaultRouter()
router.register(r"yourmodels", YourModelViewSet, basename="yourmodel")

urlpatterns = router.urls
"""
