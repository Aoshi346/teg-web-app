"""Las otras dos infracciones: la instanciación invertida y el formulario fuera de forms.py."""
from django import forms
from django.shortcuts import redirect, render

from core.forms import ModelForm as ModelFormDeCasa

from .forms import CierreExpedienteForm
from .models import Expediente


class BusquedaExpedienteForm(forms.Form):
    """be-form-clase-fuera-de-forms: vive en views.py; nadie la encuentra y se reescribe al lado."""

    texto = forms.CharField(max_length=100, required=False)


class NotaRapidaForm(ModelFormDeCasa):
    """Segunda clase fuera de sitio, y encima hereda de la base de casa."""

    class Meta:
        model = Expediente
        fields = ["titulo"]


def cerrar(request, pk):
    # be-form-request-primero: la base pone `request` primero, así que esto NO bindea nada.
    # El formulario queda unbound, is_valid() devuelve False siempre y no salta ningún error:
    # el usuario ve el formulario recargado y en blanco, sin explicación.
    form = CierreExpedienteForm(request.POST)
    if form.is_valid():
        form.save()
        return redirect("expedientes:detalle", pk=pk)
    return render(request, "expedientes/cerrar.html", {"form": form})
