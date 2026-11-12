"""G4 · Qué entra en el barrido de aislamiento. Se DESCUBRE; no se escribe a mano.

Cosechado de `elvion-autoparte-demo/tests/seguridad/inventario.py` (sub-ola 2.24, SE-21), y su
decisión de diseño es la única que de verdad importa en esta carpeta:

    Una lista de modelos escrita a mano protege de los modelos que existían el día que se
    escribió: el que alguien añada con prisa dentro de tres meses —justo el que nadie ha
    revisado— queda fuera del gate y nadie se entera, porque un test que no existe no falla.

Aquí la lista sale del registro de Django. Lo único escrito a mano son las EXCEPCIONES
(`g4_adaptador.EXCEPCIONES`, `SIN_CONSTRUCTOR`), cada una con su razón, y una excepción que ya no
corresponde a ningún modelo hace fallar la suite: descubrir lo que hay, declarar lo que se salta.

Se busca por la COLUMNA (`COLUMNA_TENANT`, `tenant_id` por defecto) y no por herencia de una base
común. En autoparte la diferencia no fue teórica: `accounts.User` y `audit.AuditEvent` llevan
tenant y no heredan de `TenantOwnedModel`, y son las dos tablas donde una fuga duele más. Es además
el mismo criterio que usa `gate_tenant.py` sobre el catálogo de Postgres, así que los dos
inventarios cuentan lo mismo.
"""
from __future__ import annotations

from typing import Any

import g4_adaptador as adaptador

COLUMNA_TENANT: str = getattr(adaptador, "COLUMNA_TENANT", "tenant_id")


def _campo_tenant(modelo: Any):
    return next((f for f in modelo._meta.concrete_fields if f.column == COLUMNA_TENANT), None)


def modelos_con_tenant() -> tuple:
    """Todo modelo concreto cuya tabla lleva la columna del tenant, ordenado por etiqueta.

    Los proxys se saltan: comparten tabla con su modelo concreto y la contarían dos veces.
    """
    from django.apps import apps as registro

    encontrados = [
        m for m in registro.get_models()
        if not m._meta.proxy and _campo_tenant(m) is not None
    ]
    return tuple(sorted(encontrados, key=lambda m: m._meta.label))


def campo_tenant(modelo: Any):
    """El campo (normalmente la FK `tenant`) que escribe la columna del tenant."""
    campo = _campo_tenant(modelo)
    if campo is None:
        raise LookupError(f"{modelo._meta.label} no tiene la columna {COLUMNA_TENANT}")
    return campo


def modelo_tenant() -> Any:
    """El modelo de los propios tenants: el destino de la FK de la columna del tenant.

    Si el adaptador lo declara (`MODELO_TENANT`), manda el adaptador. Si no, se deduce de las FK,
    y si dos modelos apuntan a modelos de tenant distintos, falla: eso ya es un hallazgo.
    """
    declarado = getattr(adaptador, "MODELO_TENANT", None)
    if declarado is not None:
        return declarado
    destinos = {getattr(campo_tenant(m), "related_model", None) for m in modelos_con_tenant()}
    destinos.discard(None)
    if len(destinos) != 1:
        raise LookupError(
            f"la columna {COLUMNA_TENANT} apunta a {len(destinos)} modelos distintos "
            f"({sorted(d._meta.label for d in destinos)}): declara MODELO_TENANT en el adaptador"
        )
    return destinos.pop()


def etiqueta(modelo: Any) -> str:
    """`app.Modelo` — el id con el que pytest nombra cada caso parametrizado."""
    return modelo._meta.label


def tablas_con_tenant() -> set:
    return {m._meta.db_table for m in modelos_con_tenant()}
