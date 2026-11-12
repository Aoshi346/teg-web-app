"""Una sola forma para TODOS los errores de la API.

Contrato con el frontend (`.claude/patterns/stack/api-y-errores.md` y `formularios.md`):

    400  {"errors": {"campo": ["mensaje"], "non_field_errors": ["mensaje"]}}

DRF por defecto devuelve DOS formas distintas y obliga al cliente a distinguirlas:
`{"campo": [...]}` en errores de validación, pero `{"detail": "..."}` en auth, permisos, 404 y
throttling. Un cliente que lea solo una de las dos se come la otra en silencio — que es justo el
fallo que este handler existe para impedir.

Se activa en settings:  REST_FRAMEWORK = {"EXCEPTION_HANDLER": "config.exceptions.api_exception_handler"}
"""
from rest_framework.settings import api_settings
from rest_framework.views import exception_handler as drf_exception_handler


def _como_lista(valor) -> list[str]:
    if isinstance(valor, (list, tuple)):
        return [str(v) for v in valor]
    return [str(valor)]


def api_exception_handler(exc, context):
    response = drf_exception_handler(exc, context)
    if response is None:
        # DRF no supo traducirla: que suba y sea un 500 de verdad, no un 200 mentiroso.
        return None

    datos = response.data
    if isinstance(datos, dict) and "detail" in datos:
        # auth / permisos / 404 / throttling → al cajón de errores de formulario
        errores = {api_settings.NON_FIELD_ERRORS_KEY: _como_lista(datos["detail"])}
    elif isinstance(datos, dict):
        errores = {campo: _como_lista(valor) for campo, valor in datos.items()}
    else:
        # ValidationError("mensaje") en una vista llega como lista suelta
        errores = {api_settings.NON_FIELD_ERRORS_KEY: _como_lista(datos)}

    response.data = {"errors": errores}
    return response
