"""La base de formulario de casa — el punto único por el que pasan TODOS los formularios.

Este fichero es la implementación de referencia de `backend-formularios-django.md`. Está copiado
en espíritu de un backend real en producción donde 346 de 385 clases de formulario heredan de una
base como esta. Lo que la hace load-bearing no es el ahorro de código: es que centraliza tres
cosas que, sueltas, se olvidan una por una.

  1. `clean()` sanea el HTML de todo campo de texto → la defensa XSS de todos los formularios.
  2. `save()` asigna el dueño (`owner`) → es el campo por el que filtra el scoping por usuario,
     así que un formulario que no herede de aquí crea filas SIN dueño, invisibles para su usuario.
  3. `set_readonly_fields()` aplica los campos de solo lectura del perfil.
"""
import bleach
from django import forms

TAGS_PERMITIDOS = ["b", "i", "u", "em", "strong", "p", "br", "ul", "ol", "li", "a"]
ATRIBUTOS_PERMITIDOS = {"a": ["href", "title"]}


class ModelForm(forms.ModelForm):
    """Base de casa. OJO con la firma: `request` va PRIMERO.

    Es deliberado —todo el formulario necesita el usuario— y es la trampa que documenta
    `be-form-request-primero`: `MiForm(request.POST)` deja el formulario UNBOUND, `is_valid()`
    devuelve False siempre y no salta ningún error. Por eso hay una regla que lo caza.
    """

    def __init__(self, request=None, data=None, files=None, *args, **kwargs):
        self.request = request
        super().__init__(data, files, *args, **kwargs)
        self.set_readonly_fields()

    def set_readonly_fields(self) -> None:
        if self.request is None:
            return
        for nombre in getattr(self.Meta, "readonly_fields", ()):
            campo = self.fields.get(nombre)
            if campo is not None:
                campo.disabled = True

    def clean(self):
        datos = super().clean()
        for nombre, valor in list(datos.items()):
            if isinstance(valor, str):
                datos[nombre] = bleach.clean(
                    valor, tags=TAGS_PERMITIDOS, attributes=ATRIBUTOS_PERMITIDOS, strip=True
                )
        return datos

    def save(self, commit=True):
        instancia = super().save(commit=False)
        if self.request is not None:
            usuario = self.request.user
            if instancia.pk is None:
                instancia.created_by = usuario
                instancia.owner = usuario  # el único sitio donde se pobla el dueño
            instancia.updated_by = usuario
        if commit:
            instancia.save()
        return instancia
