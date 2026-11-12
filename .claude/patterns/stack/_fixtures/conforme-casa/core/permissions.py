"""Autenticación máquina-a-máquina — la comprobación de caducidad, en UN sitio.

Este fichero es la mitad que faltaba de `be-model-caducidad-no-comprobada`. El modelo declara
`expiration_date`, el formulario deja editarla y el CRUD la muestra; si nadie la LEE, el campo es
una promesa falsa: quien pone fecha de caducidad a un token se queda tranquilo y el token sigue
funcionando indefinidamente.

Y va en un decorador único a propósito. En el backend de referencia esta comprobación estaba
copiada en tres vistas: el mismo fallo estaba en los tres sitios a la vez, y arreglarlo en uno no
arreglaba nada.
"""
import hashlib
from functools import wraps

from django.http import JsonResponse
from django.utils import timezone

from .models import TokenApi


def token_valido(vista):
    """Rechaza el token inactivo Y el caducado. Las dos condiciones, en el mismo sitio."""

    @wraps(vista)
    def envoltorio(request, *args, **kwargs):
        crudo = request.headers.get("X-API-TOKEN", "")
        hasheado = hashlib.sha256(crudo.encode()).hexdigest()
        token = TokenApi.objects.filter(token_hash=hasheado, activo=True).first()
        if token is None:
            return JsonResponse({"errors": {"non_field_errors": ["token inválido"]}}, status=401)
        if token.expiration_date is not None and token.expiration_date < timezone.now():
            return JsonResponse({"errors": {"non_field_errors": ["token caducado"]}}, status=401)
        return vista(request, *args, **kwargs)

    return envoltorio
