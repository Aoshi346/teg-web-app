"""G4 · Lo que la suite no puede adivinar de tu proyecto. Se rellena UNA vez, al instalarla.

Copia esta carpeta a `tests/seguridad/` (o donde viva la suite de seguridad del proyecto) y
rellena cada `raise NotImplementedError`. La suite falla mientras quede alguno
(`test_el_adaptador_esta_relleno`): un adaptador a medias es una suite que no prueba nada y sale en
verde.

Hay dos formas de aislar tenants en casa, y el adaptador dice cuál es la tuya (`MODO`):

  · "rls" — la BASE filtra: políticas RLS sobre `current_setting('app.tenant_id')`, el rol de la
    app sin BYPASSRLS y FORCE en cada tabla (cold_calling_coach, ADR-0003). El ámbito se abre con
    `SET LOCAL` dentro de una transacción.
  · "aplicacion" — filtra el ORM: un manager que exige ámbito (`for_tenant()`) y revienta sin él
    (elvion-autoparte-demo, ADR-0002). La base no garantiza nada; la suite es lo único que lo
    prueba.

Los dos ejemplos completos, rellenos y probados, están en el README de esta carpeta.
"""
from __future__ import annotations

# gate: G4-adaptador

#: "rls" o "aplicacion" (ver arriba).
MODO = "rls"

#: La columna que lleva el tenant en cada tabla. La misma que `gate_tenant.py --columna`.
COLUMNA_TENANT = "tenant_id"

#: Solo modo rls: el ajuste de sesión que leen las políticas, y las funciones SQL que lo
#: envuelven si las políticas no llaman a `current_setting` directamente.
AJUSTE = "app.tenant_id"
FUNCIONES_DE_AMBITO: tuple = ()

#: Excepciones que cuentan como «cerrado»: consultar sin ámbito puede REVENTAR en vez de devolver
#: cero filas (el `TenantScopeMissing` de autoparte). Las dos cosas son fallo cerrado; lo que no
#: puede pasar es que devuelva filas.
EXCEPCIONES_DE_CIERRE: tuple = ()

#: Modelos con la columna del tenant que NO entran en el barrido, cada uno con su razón (≥15
#: caracteres). Una excepción para un modelo que ya no existe hace fallar la suite.
EXCEPCIONES: dict = {}

#: Modelos que el constructor genérico no sabe montar, con su razón. Antes que esto, prueba un
#: AJUSTE: un modelo aquí es superficie sin cubrir.
SIN_CONSTRUCTOR: dict = {}

#: Valores mínimos por modelo (`"app.Modelo": {"campo": valor | lambda semilla, tenant: …}`) para
#: lo que exige un CheckConstraint y el `_meta` no cuenta.
AJUSTES: dict = {}

#: FK nullable que un CheckConstraint vuelve obligatorias: `{"app.Modelo": ("campo",)}`.
RELACIONES_EXIGIDAS: dict = {}

#: Campos que pone la app sola (además de id, created_at, updated_at, created_by, updated_by).
CAMPOS_AUTOMATICOS: tuple = ()

#: El modelo de los tenants. Si se deja en None se deduce de las FK de la columna del tenant.
MODELO_TENANT = None


def crear_tenant(nombre: str):
    """Crea un tenant de prueba y lo devuelve (la instancia del modelo de tenants)."""
    raise NotImplementedError("g4_adaptador.crear_tenant: cómo se crea un tenant en tu proyecto")


def guardar(modelo, tenant, valores: dict):
    """Guarda una fila de `modelo` que pertenece a `tenant`, por la vía normal de la app.

    En modo rls, dentro del ámbito de `tenant` (el WITH CHECK de la política lo exige). En modo
    aplicacion, por el manager acotado (`modelo.objects.for_tenant(tenant).create(**valores)`).
    """
    raise NotImplementedError("g4_adaptador.guardar: cómo se guarda una fila de un tenant")


def guardar_sin_tenant(modelo, valores: dict):
    """Guarda una fila de un modelo SIN columna de tenant (un padre global). Rara vez se cambia."""
    return modelo.objects.create(**valores)


def contar_como(modelo, tenant, **filtro) -> int:
    """Cuenta las filas que casan con `filtro` CON EL ÁMBITO DE `tenant`, como lo abre la app.

    La consulta tiene que ejecutarse DENTRO del ámbito (devuelve un número, no un queryset
    perezoso: en modo rls, un queryset evaluado fuera del ámbito mide otra cosa).
    """
    raise NotImplementedError("g4_adaptador.contar_como: abrir el ámbito y contar dentro")


def contar_sin_ambito(modelo, **filtro) -> int:
    """Cuenta SIN abrir ningún ámbito: lo que haría una tarea o una vista que se olvidó de abrirlo.

    Tiene que devolver 0 o lanzar una de `EXCEPCIONES_DE_CIERRE`. No abras aquí un ámbito vacío: lo
    que se mide es justo el olvido (y que un ámbito anterior no se quedó pegado a la conexión).
    """
    raise NotImplementedError("g4_adaptador.contar_sin_ambito: consultar sin abrir ámbito")


def crear_como(modelo, actor, valores: dict):
    """Con el ámbito de `actor` abierto, intenta crear una fila con `valores`, que traen OTRO
    tenant.

    Es el ataque del cliente que manda su propio tenant en el cuerpo. Puede lanzar (la política
    WITH CHECK lo rechaza) o crear la fila en el tenant del actor (el manager lo impone); lo que no
    puede es dejarla en el tenant ajeno. Devuelve la fila creada, si se creó.
    """
    raise NotImplementedError("g4_adaptador.crear_como: crear desde un ámbito con otro tenant")
