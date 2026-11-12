"""Vistas server-rendered. Traducen: montan el formulario, llaman al servicio, eligen plantilla.

No hay ViewSet, ni serializer, ni router. Es el arquetipo que documenta
`backend-formularios-django.md`, y este fichero existe para demostrar que puntúa 0 hallazgos.
"""
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect, render

from .forms import ExpedienteForm
from .utils import ExpedienteNoCerrable, cerrar_expediente


@login_required
def alta_expediente(request):
    # `request` PRIMERO: es la firma de la base de casa. Con ExpedienteForm(request.POST) el
    # formulario quedaría unbound y is_valid() sería False siempre, sin ningún error visible.
    form = ExpedienteForm(request, request.POST or None, request.FILES or None)
    if request.method == "POST" and form.is_valid():
        expediente = form.save()
        return redirect("expedientes:detalle", pk=expediente.pk)
    return render(request, "expedientes/alta.html", {"form": form})


@login_required
def cerrar(request, pk):
    try:
        cerrar_expediente(expediente_id=pk, cerrado_por_id=str(request.user.pk))
    except ExpedienteNoCerrable as exc:
        return render(request, "expedientes/error.html", {"mensaje": str(exc)}, status=409)
    return redirect("expedientes:detalle", pk=pk)
