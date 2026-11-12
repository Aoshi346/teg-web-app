"""Base de casa idéntica a la del fixture conforme: aquí NO está el fallo.

Tiene que existir para que las reglas de formulario tengan contra qué comparar — `be-form-base-de-casa`
solo dispara cuando el proyecto YA tiene una base compartida, y `be-form-request-primero` solo se
arma cuando esa base pone `request` en primera posición.
"""
import bleach
from django import forms

TAGS_PERMITIDOS = ["b", "i", "strong", "p", "br"]


class ModelForm(forms.ModelForm):
    def __init__(self, request=None, data=None, files=None, *args, **kwargs):
        self.request = request
        super().__init__(data, files, *args, **kwargs)

    def clean(self):
        datos = super().clean()
        for nombre, valor in list(datos.items()):
            if isinstance(valor, str):
                datos[nombre] = bleach.clean(valor, tags=TAGS_PERMITIDOS, strip=True)
        return datos

    def save(self, commit=True):
        instancia = super().save(commit=False)
        if self.request is not None:
            instancia.owner = self.request.user
        if commit:
            instancia.save()
        return instancia
