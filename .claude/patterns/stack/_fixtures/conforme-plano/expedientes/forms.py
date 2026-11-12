"""Formularios de la app. Heredan de la base de casa y enumeran sus campos."""
from core.forms import ModelForm

from .models import Expediente


class ExpedienteForm(ModelForm):
    class Meta:
        model = Expediente
        # Lista BLANCA. Con `__all__` o con `exclude`, el campo que alguien añada al modelo
        # mañana entra solo en este formulario y nadie lo decide.
        fields = ["referencia", "titulo", "estado", "importe"]
        readonly_fields = ["referencia"]

    def clean_referencia(self):
        referencia = self.cleaned_data["referencia"].strip().upper()
        if not referencia:
            raise ValueError("la referencia no puede quedar vacía")
        return referencia


class CierreExpedienteForm(ModelForm):
    class Meta:
        model = Expediente
        fields = ["estado"]
