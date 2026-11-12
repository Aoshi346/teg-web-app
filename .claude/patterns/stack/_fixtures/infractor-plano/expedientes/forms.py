"""Una infracción por regla de la capa de formularios."""
from django.forms import ModelForm          # ← el ModelForm PELADO es aquí el de Django

from core.forms import ModelForm as ModelFormDeCasa
from .models import Expediente


class ExpedienteForm(ModelForm):
    """be-form-base-de-casa: hereda del ModelForm de Django, no de la base del proyecto.

    Consecuencia real, no estilística: se salta el saneado del HTML, no se asigna `owner` —así
    que la fila nace sin dueño y el filtrado por usuario no la devuelve nunca— y no aplica los
    campos de solo lectura del perfil.
    """

    class Meta:
        model = Expediente
        fields = "__all__"                   # be-form-fields-enumerado


class CierreExpedienteForm(ModelFormDeCasa):
    class Meta:
        model = Expediente
        exclude = ["owner"]                  # be-form-fields-enumerado (lista negra)
