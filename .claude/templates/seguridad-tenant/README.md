# G4 · Aislamiento entre tenants, como gate (capa del ORM)

Plantilla de la sub-ola 2.24 de la revisión integral (item **SE-21**). La pregunta que responde:
**¿puede una consulta de un tenant ver o escribir filas de otro?** Se responde en dos capas, y hacen
falta las dos:

**Para qué modelo de tenant vale:** esquema COMPARTIDO con una columna de tenant en cada tabla
(`tenant_id`), filtrado por RLS (cold_calling_coach) o por el ORM (autoparte). **No** vale para una
base de datos por tenant (el `db_alias` de elvion): ahí no hay columna que inventariar, el gate sale 2
(«0 tablas…») y la disciplina es la de la skill `multi-tenant-context`.

| Capa | Pieza | Qué mira | Necesita |
|---|---|---|---|
| **Base de datos** | `.claude/scripts/gate_tenant.py` | Rol de la app sin superusuario ni BYPASSRLS, tampoco heredado de un rol del que es miembro; cada tabla con la columna del tenant con RLS ENCENDIDO y FORZADO y una política que filtra (una restrictiva solo cierra los comandos que cubre: una restrictiva `FOR SELECT` no cierra un `FOR DELETE USING (true)`); ninguna política permisiva abierta; vistas sin `security_invoker` de un dueño que se salta RLS; tablas con la columna fuera del esquema medido; la sonda de dos tenants sobre la misma conexión; y, con `--sonda-escritura`, que desde A no se pueda insertar en B, mover filas a B ni borrar más de lo propio (todo con rollback) | Un DSN del rol de la app y otro de un rol que vea todo, solo para contar (sin él, en modo rls sale 2: la lectura de las políticas es léxica) |
| **ORM** | esta carpeta | Modelo a modelo, descubiertos del registro de Django: A no ve la fila de B · el dueño SÍ ve la suya · sin ámbito no se ve nada · A, B, A y ninguno en la misma conexión · desde A no se escribe en B · el dueño SÍ escribe lo suyo | `pytest-django` y la base de test en Postgres |

De dónde sale cada cosa, para que se pueda ir a mirar el original:

- **`g4_inventario.py`** es `elvion-autoparte-demo/tests/seguridad/inventario.py` generalizado: los
  modelos con tenant se **descubren** (por la columna, no por herencia) y lo único que se escribe a
  mano son las excepciones, con su razón; una excepción que ya no corresponde a ningún modelo
  hace fallar la suite.
- **`g4_constructor.py`** es su `constructor.py` sin lo que era de autoparte: monta una fila de
  cualquier modelo rellenando lo obligatorio y resolviendo las FK con el mismo tenant.
- El **rol sin BYPASSRLS**, el **FORCE** y el **`SET LOCAL`** son de `cold_calling_coach`
  (`infra/postgres/init/01-app-role.sql`, `backend/core/rls.py`, `backend/core/db.py`): *«con
  superusuario, las políticas no se aplican y la suite de aislamiento pasaría entera sin probar
  absolutamente nada»*.

## Instalarla

1. Copia `g4_inventario.py`, `g4_constructor.py`, `g4_adaptador.py` y `test_g4_aislamiento_tenant.py`
   a la carpeta de tests de seguridad del proyecto (`tests/seguridad/`, o `backend/tests/seguridad_g4/`).
   Los nombres llevan `g4_` para no chocar con una suite que ya exista (autoparte tiene su `inventario.py`).
2. Rellena `g4_adaptador.py`: el modo (`rls` o `aplicacion`), cómo se crea un tenant, cómo se guarda
   una fila, cómo se cuenta CON el ámbito abierto y SIN él, y cómo se intenta crear desde un ámbito
   con otro tenant. La suite falla mientras quede un `raise NotImplementedError`.
3. En modo `rls`, el `USER` de la base de test tiene que ser **el rol de la app**, no un
   superusuario. Si no, el primer test que lo detecta es el del gate (`G4-ROL-SUPER`).
4. Córrela aparte, no por app (la propiedad es del sistema):

   ```bash
   bash .claude/hooks/check-ram.sh && pytest tests/seguridad/test_g4_aislamiento_tenant.py -v
   ```

   Con `GATE_TENANT_DSN_ADMIN` (un rol que vea todo en el mismo servidor) el test del gate corre
   además la sonda de dos tenants —lectura y escritura— sobre las filas que construye, y exige que
   mida todas las tablas. Sin él corre solo lo estático (`--solo-estatico`), y eso es léxico: en CI,
   pon el DSN de admin. Las credenciales viajan por entorno, nunca en la línea de comandos.

### El adaptador de cold_calling_coach (modo `rls`), probado en un clon el 20-10

```python
from apps.tenants.models import Tenant
from core.db import tenant_scope
import uuid

MODO = "rls"
MODELO_TENANT = Tenant

def crear_tenant(nombre):            return Tenant.objects.create(nombre=nombre, slug=f"g4-{uuid.uuid4().hex[:10]}")
def guardar(modelo, tenant, valores):
    with tenant_scope(tenant.pk):    return modelo.objects.create(tenant=tenant, **valores)
def contar_como(modelo, tenant, **f):
    with tenant_scope(tenant.pk):    return modelo.objects.filter(**f).count()
def contar_sin_ambito(modelo, **f):  return modelo.objects.filter(**f).count()
def crear_como(modelo, actor, valores):
    with tenant_scope(actor.pk):     return modelo.objects.create(**valores)
```

El fichero completo es `_archive/2026-10-20/medicion-2.24/ccc/g4_adaptador.py`. Sobre el esquema real
de CCC migrado, el constructor genérico montó los cinco modelos con tenant **sin un solo ajuste**.

### El de un proyecto en modo `aplicacion` (filtro en el ORM, como autoparte) — SIN PROBAR en autoparte

```python
from apps.core.tenancy import TenantScopeMissing
MODO = "aplicacion"
EXCEPCIONES_DE_CIERRE = (TenantScopeMissing,)   # sin ámbito, el manager revienta: también es cerrado
def guardar(modelo, tenant, valores):         return modelo.objects.for_tenant(tenant).create(**valores)
def contar_como(modelo, tenant, **f):         return modelo.objects.for_tenant(tenant).filter(**f).count()
def contar_sin_ambito(modelo, **f):           return modelo.objects.filter(**f).count()
def crear_como(modelo, actor, valores):       return modelo.objects.for_tenant(actor).create(**valores)
```

Este modo está probado en la tienda de juguete de la medición (con un manager como el de autoparte),
no en autoparte, que tiene modelos sin el manager estricto (`accounts.User`) y `AJUSTES` propios.

## En CI (un proyecto con RLS)

```yaml
- name: Crear el rol de aplicación (SIN BYPASSRLS)
  run: psql -h 127.0.0.1 -U <superusuario> -d <base> -f infra/postgres/init/01-app-role.sql
- name: migrate contra Postgres REAL
  run: python backend/manage.py migrate --no-input        # con DATABASE_URL del rol de la app
- name: G4 · suite del ORM (lleva dentro el gate de base de datos, con sus dos sondas)
  env:
    GATE_TENANT_DSN_ADMIN: "postgres://<superusuario>:<clave>@127.0.0.1:5432/postgres"
  run: pytest backend/tests/seguridad_g4/test_g4_aislamiento_tenant.py -v
```

El gate también se corre suelto (por ejemplo contra staging): `GATE_TENANT_DSN=… GATE_TENANT_DSN_ADMIN=…
python3 .claude/scripts/gate_tenant.py --manifiesto .claude/gate-tenant.json --exigir-sonda`, y
`--sonda-escritura --exigir-escritura` solo contra una base de CI o de test (escribe y deshace; con
`--exigir-escritura`, una prueba de escritura que no se pudo hacer es un 2 y no un verde). El
DELETE de prueba choca con las FK **inmediatas** aunque la política esté bien (las diferibles, como
las de Django, se aplazan): entonces se repite desde el admin si es **superusuario**, con los
disparadores de FK apagados para esa transacción y `SET ROLE` al rol de la app; con un admin que solo
tiene BYPASSRLS, esa prueba queda sin medir. `.claude/gate-tenant.json`
es su manifiesto (modo, columna, ajuste y excepciones de TABLA con su razón, `esquema.tabla` para las
de otro esquema); la suite lo escribe sola para la base de test a partir del adaptador.

## Lo que NO prueba, para que nadie lo dé por cubierto

- **Referencias cruzadas por FK**: una fila de A que apunta a un padre de B pasa el WITH CHECK
  (comprueba el tenant de la fila, no el de sus padres). Autoparte lo cierra con FK compuestas y su
  `test_fuga_orm.py::test_todo_hijo_de_un_padre_protegible_lleva_su_fk_compuesto`; aquí no se generaliza.
- **Caché, colas, logs, vector store**: OWASP Multi-Tenant los pide; esta suite no llega. Las tareas
  de Celery reencoladas con un argumento cruzado tienen su barrido en autoparte (`test_fuga_celery.py`).
- **Tablas sin la columna** que se protegen a través de su padre (`enable_sql_indirecto` de CCC): no
  entran en ninguno de los dos inventarios.
- **La capa de la API** (vistas, permisos, la cabecera `X-Tenant` sin comprobar pertenencia): es otra
  capa y en CCC la cubre su `test_aislamiento_cross_tenant.py`.
- **El UPDATE y el DELETE cruzados en modo aplicación** (`for_tenant(a).filter(…).update(tenant=b)`):
  la suite prueba el INSERT con el tenant ajeno; el UPDATE y el DELETE, no. En modo rls los tres los
  prueba la sonda de escritura (insertar, mover filas a B con un UPDATE sin WHERE —con WHERE, Postgres
  exige además el USING de SELECT a la fila nueva y lo tapa— y un DELETE sin WHERE que no puede borrar
  más de lo propio), y la lectura estática ve la política floja aunque no haya sonda. Las pruebas por
  modelo de esta suite no los miran: en la tienda de juguete, un `FOR DELETE USING (true)` solo lo caza
  el test del gate.
- **Que la lectura estática de las políticas sea semántica**: es léxica (nombra la columna y el
  ajuste). Por eso sin la sonda el gate no da verde en modo rls.

## Control negativo

- `python3 .claude/scripts/gate_tenant.py --autoprueba --dsn-admin postgres://…@127.0.0.1:…/postgres`
  monta una base de juguete en un Postgres DESECHABLE (con una FK inmediata) y la mide limpia y con
  `--exigir-escritura`, con 24 sabotajes, cuatro controles de lo que NO debe salir rojo y tres casos
  que tienen que salir NO MEDIDO (32 casos). `mutar_gate_tenant.py` apaga cada comprobación una a una
  y la autoprueba cae (32 de 32).
- La medición de la sub-ola (`_archive/2026-10-20/medicion-2.24/`) corre esta plantilla contra una
  tienda de juguete en los dos modos (13 escenarios) y contra un clon de cold_calling_coach (4 pasadas).
