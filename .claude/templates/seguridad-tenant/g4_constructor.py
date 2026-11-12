"""G4 · Un constructor genérico de filas: dale un modelo y un tenant, y te devuelve una fila suya.

Cosechado de `elvion-autoparte-demo/tests/seguridad/constructor.py` (sub-ola 2.24, SE-21) sin lo
que era de autoparte: los ajustes por modelo, la vía de guardado y el modelo de tenant los pone
ahora el adaptador del proyecto (`g4_adaptador.py`).

## Por qué genérico y no una fábrica por modelo

Porque el barrido tiene que cubrir TODOS los modelos con tenant, y una fábrica por modelo son N
sitios donde acordarse de añadir la N+1. El constructor lee el `_meta`, rellena lo obligatorio y
resuelve las claves foráneas recursivamente CON EL MISMO TENANT, así que el modelo nuevo entra en
el barrido el día que se declara.

## Lo que el `_meta` no cuenta, y por eso existe `AJUSTES`

Django expone los campos y sus tipos, pero no lo que exige un `CheckConstraint` (que `desde <=
hasta`, que haya correo O teléfono). `g4_adaptador.AJUSTES` son los valores mínimos que los
satisfacen. Es una lista a mano, pero de la clase inofensiva: si alguien añade un modelo y no lo
ajusta, el test FALLA al no poder construir la fila. No se salta en silencio.

## Y una regla del propio constructor

Los valores generados no llevan nada que parezca un dato personal: ni un teléfono con forma de
teléfono ni un nombre de persona. Estas filas acaban en la salida de pytest, que se pega en
informes.
"""
from __future__ import annotations

import datetime as dt
import decimal
import uuid
from typing import Any

import g4_adaptador as adaptador
from g4_inventario import _campo_tenant, modelo_tenant

#: Campos que el constructor nunca genera: los pone la base, el ámbito o el adaptador.
_AUTOMATICOS = frozenset({"id", "created_at", "updated_at", "created_by", "updated_by"}) | (
    frozenset(getattr(adaptador, "CAMPOS_AUTOMATICOS", ()))
)
AJUSTES: dict = getattr(adaptador, "AJUSTES", {})
RELACIONES_EXIGIDAS: dict = getattr(adaptador, "RELACIONES_EXIGIDAS", {})


def _valor_para(campo: Any, semilla: str) -> Any:
    """Un valor válido para este campo, sin datos que parezcan personales."""
    from django.db import models
    from django.utils import timezone

    if campo.choices:
        # La primera opción declarada (también con opciones agrupadas).
        return campo.flatchoices[0][0]
    if isinstance(campo, models.UUIDField):
        return uuid.uuid4()
    if isinstance(campo, models.BooleanField):
        return False
    if isinstance(campo, models.DecimalField):
        return decimal.Decimal("1")
    if isinstance(campo, (models.IntegerField, models.BigIntegerField, models.SmallIntegerField)):
        return 1
    if isinstance(campo, models.FloatField):
        return 1.0
    if isinstance(campo, models.DateTimeField):
        return timezone.now()
    if isinstance(campo, models.DateField):
        return timezone.now().date()
    if isinstance(campo, models.TimeField):
        return dt.time(12, 0)
    if isinstance(campo, models.DurationField):
        return dt.timedelta(minutes=1)
    if isinstance(campo, models.JSONField):
        return {}
    if isinstance(campo, models.GenericIPAddressField):
        return "192.0.2.1"  # TEST-NET-1 (RFC 5737): no es la IP de nadie
    if isinstance(campo, models.EmailField):
        return f"buzon-{semilla}@ejemplo.invalid"
    if isinstance(campo, models.URLField):
        return f"https://ejemplo.invalid/{semilla}"
    if isinstance(campo, models.BinaryField):
        return b"prueba"
    if type(campo).__name__ == "ArrayField":
        return []
    texto = f"prueba-{semilla}"
    largo = getattr(campo, "max_length", None)
    return texto[:largo] if largo else texto


def _obligatorio(campo: Any) -> bool:
    if campo.name in _AUTOMATICOS or campo.primary_key or campo.auto_created:
        return False
    if getattr(campo, "auto_now", False) or getattr(campo, "auto_now_add", False):
        return False
    return not (campo.null or campo.has_default() or campo.blank)


def construir(modelo: Any, tenant: Any, *, cache: dict | None = None, **overrides: Any) -> Any:
    """Crea y guarda una fila de `modelo` para `tenant`, resolviendo sus dependencias.

    `cache` reutiliza los padres ya construidos para ese tenant. No es una optimización: sin él,
    cada hijo construiría padres nuevos y las restricciones `UNIQUE (tenant, …)` chocarían entre sí
    en vez de comprobar lo que se quiere comprobar.
    """
    if modelo is modelo_tenant():
        return tenant
    valores = valores_para(modelo, tenant, cache=cache, **overrides)
    if _campo_tenant(modelo) is None:
        # Un padre sin tenant (un catálogo global, por ejemplo): se guarda tal cual.
        return adaptador.guardar_sin_tenant(modelo, valores)
    return adaptador.guardar(modelo, tenant, valores)


def valores_para(modelo: Any, tenant: Any, *, cache: dict | None = None, **overrides: Any) -> dict:
    """Los valores de una fila nueva de `modelo` (sin el tenant), con sus padres ya guardados.

    Separado de `construir` para el test de escritura cruzada: ahí la fila no la guarda la vía
    normal, la intenta crear un actor de OTRO tenant.
    """
    from django.db import models

    cache = {} if cache is None else cache
    semilla = uuid.uuid4().hex[:8]
    valores: dict = dict(AJUSTES.get(modelo._meta.label, {}))
    exigidas = RELACIONES_EXIGIDAS.get(modelo._meta.label, ())
    ct = _campo_tenant(modelo)
    for campo in modelo._meta.concrete_fields:
        if campo.name in valores or (ct is not None and campo.name == ct.name):
            continue
        if not (_obligatorio(campo) or campo.name in exigidas):
            continue
        if isinstance(campo, models.ForeignKey):
            valores[campo.name] = _padre(campo, tenant, cache)
        else:
            valores[campo.name] = _valor_para(campo, semilla)
    valores.update(overrides)
    return {k: (v(semilla, tenant) if callable(v) else v) for k, v in valores.items()}


def _padre(campo: Any, tenant: Any, cache: dict) -> Any:
    destino = campo.related_model
    if destino is modelo_tenant():
        return tenant
    clave = (destino._meta.label, getattr(tenant, "pk", tenant))
    if clave not in cache:
        cache[clave] = construir(destino, tenant, cache=cache)
    return cache[clave]
