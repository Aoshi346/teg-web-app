# Tests del backend — patrón de casa

> **Cuándo aplicar:** al escribir cualquier test de backend, al montar la suite de un proyecto que
> no la tiene, y **antes de correr `pytest`** (el límite de RAM de esta máquina es duro, no un
> consejo: `rules/ram-pytest.md`).
>
> **NO aplicar:** tests de frontend (`tests.md`, que es la mitad de React) · E2E con navegador
> (`rules/verification.md` §Estabilidad E2E) · el gate visual de una wave con UI (`rules/qa-loop.md`).
>
> ⚠️ **Este documento existe porque faltaba.** De las reglas de backend del catálogo, **ninguna**
> hablaba de tests, y el `tests.md` que sí existía era solo de frontend. El hueco no era teórico:
> en el backend Django de referencia son **8 funciones `def test_` en 740 ficheros**, de las cuales
> 2 prueban algo. Sin tests, ninguna de las demás reglas del catálogo se puede verificar — este
> documento es el que sostiene a los otros.

## La regla (una frase)

**Cada test crea su propio mundo, se ejecuta por módulo, y está donde el descubridor lo encuentra.**

Las tres partes responden a los tres modos de fallar que hemos medido: la suite que no arranca, la
suite que tumba el servidor, y el test que existe y no se ejecuta nunca.

## Lo primero, y no es escribir tests: que la suite ARRANQUE

`manage.py test` (y `pytest-django`) crean **una base de datos de test por cada alias de
`DATABASES`**. En el backend de referencia hay 11 alias, de los cuales **6 no declaran `ENGINE`**
—son diccionarios de conexión que otra librería lee a mano, guardados ahí como cajón de sastre— y
3 apuntan a un motor Mongo. Consecuencia: la suite **probablemente ni arranca**, y el error que da
no dice que la causa sea la configuración.

```python
# ✅ un alias, con motor, y lo que no sea una base de datos de Django fuera de DATABASES
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": env("POSTGRES_DB"),
        "CONN_MAX_AGE": 60,
    }
}
MONGO_LOGS = {"host": "mongo", "port": 27017}   # si hace falta, es OTRA variable, no un alias
```

Es la primera piedra a quitar y cuesta una tarde. Y es, además, el premio de quitar Mongo: de 11
alias a 1, los routers desaparecen y `DATABASE_ROUTERS` se puede borrar (ver `README.md`
§"Quitar Mongo").

## Implementación de referencia

`_fixtures/conforme-casa/expedientes/tests/test_expedientes.py`:

```python
@pytest.mark.django_db
def test_abrir_expediente_asigna_dueno(usuario, equipo):
    """El dueño no es cosmética: es el campo por el que filtra el scoping por usuario."""
    expediente = abrir_expediente(referencia="EXP-1", titulo="Alta",
                                  responsable_id=equipo.pk, usuario=usuario)
    assert expediente.owner == usuario
    assert expediente.estado == Estado.ABIERTO


@pytest.mark.django_db
def test_expediente_rechaza_estado_invalido(usuario, equipo):
    """La constraint aplica aunque la escritura no pase por el formulario."""
    with pytest.raises(IntegrityError):
        Expediente.objects.create(referencia="EXP-2", estado="inventado",
                                  owner=usuario, responsable_id=equipo.pk)
```

### El stack, y por qué cada pieza

| Pieza | Qué es | Por qué esta |
|---|---|---|
| **pytest + pytest-django** | el runner | `manage.py test` funciona; pytest da fixtures componibles, `parametrize` y `-k`. Y `-k` es lo que permite correr un test suelto sin levantar la suite, que en esta máquina no es comodidad: es la diferencia entre poder correr tests y no poder |
| **`@pytest.mark.django_db`** | acceso a la BD, en transacción que se revierte | El test no deja residuos. Sin él, el segundo run falla por un `unique` que el primero dejó puesto |
| **`conftest.py`** | dónde viven las fixtures | Un `conftest.py` en la raíz de los tests con `usuario`, `cliente_api` y las fixtures compartidas. Sin él cada fichero se fabrica su propio usuario, y a la tercera vez ya divergen |
| **factories** (`factory_boy`) | objetos válidos por defecto | Es lo que hace que un test nuevo cueste tres líneas. Con `Model.objects.create(...)` a mano, cada campo obligatorio nuevo rompe **todos** los tests a la vez |
| **`--reuse-db`** | no recrear la base en cada run | En local ahorra el arranque entero. En CI, `--create-db` |

```python
# tests/conftest.py — mínimo viable, y ya paga
import pytest
from expedientes.tests.factories import EquipoFactory, UsuarioFactory

@pytest.fixture
def usuario(db):
    return UsuarioFactory()

@pytest.fixture
def equipo(db, usuario):
    return EquipoFactory(owner=usuario)
```

```python
# expedientes/tests/factories.py
class ExpedienteFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Expediente

    referencia = factory.Sequence(lambda n: f"EXP-{n:05d}")   # único por construcción
    estado = Estado.BORRADOR
    owner = factory.SubFactory(UsuarioFactory)
```

**`Sequence` y no un literal**: `referencia="EXP-1"` hardcodeado revienta el `unique` en el segundo
test del mismo fichero, y el fallo aparece en el test de al lado, no en el que lo causó.

## ⚠️ Ejecución — el límite de RAM de esta máquina es DURO

No es una preferencia de estilo: correr la suite entera aquí produce OOM, y un OOM mata la sesión
del agente y todo lo que estuviera a medias. El detalle está en **`rules/ram-pytest.md`**; lo
imprescindible:

```bash
bash .claude/hooks/check-ram.sh          # PASO 1, siempre. Es el gate real, no la prosa
pytest apps/expedientes/ -v --maxfail=3  # por MÓDULO
pytest -k "test_abrir_expediente" -v     # o un test suelto
```

```bash
# ❌ PROHIBIDO: cada uno de estos ha tumbado el servidor
pytest                # la suite entera
pytest -n auto        # workers automáticos (si hacen falta, explícitos y ≤ los de check-ram.sh --explain)
pytest --cov          # coverage multiplica la RAM
```

Con muchos módulos, chunks de ~20 tests y una comprobación de RAM entre chunk y chunk.

### El caso especial de `transaction.on_commit`

**Un test de Django puede estar en verde sin haber ejecutado nada de lo que cree que prueba.** Los
callbacks registrados con `transaction.on_commit()` **no se ejecutan nunca** dentro de `TestCase`
ni de `pytest.mark.django_db`, porque la transacción del test nunca hace COMMIT: se revierte.

```python
# ❌ verde, y no ha probado nada: el callback no llegó a correr
def test_al_abrir_se_avisa(usuario):
    abrir_expediente(...)
    assert tarea_falsa.called          # False… y el assert de arriba tampoco se ejecutó nunca

# ✅
def test_al_abrir_se_avisa(usuario):
    with django.test.TestCase.captureOnCommitCallbacks(execute=True) as callbacks:
        abrir_expediente(...)
    assert len(callbacks) == 1
    assert tarea_falsa.called
```

Es exactamente el tipo de fallo que este catálogo persigue —una comprobación que pasa sin
comprobar— y hay que auditarlo al migrar efectos a `on_commit` (`backend-signals.md`), no darlo
por bueno. **Es lo que convierte una migración de 2 horas en una de 2 días**, y una estimación que
lo ignore está mal hecha.

## El antipatrón que sustituye

`_fixtures/infractor-casa/`, dos ficheros:

```python
# expedientes/tests.py — el andamio intacto de `startapp`
from django.test import TestCase
# Create your tests here.
```

```python
# expedientes/expedientes_tests.py — tests de verdad que NO se ejecutan
def test_referencia_es_unica():
    ...
```

Los dos son la misma enfermedad: **cobertura aparente**.

- **El stub** hace que cualquier contador automático diga "41 apps con tests" cuando hay 2 tests
  reales. Y esa cifra es la que se mira para decidir dónde hace falta trabajo, así que el sitio
  con menos cobertura del proyecto es justo el que parece cubierto. Se borra con `git rm`, y la
  primera medición pasa a decir la verdad.
- **El nombre que el descubridor no encuentra**: Django descubre `test*.py`; pytest, `test_*.py` y
  `*_test.py`. `expedientes_tests.py` no casa con ninguno. Esos tests no corren, y por tanto no
  fallan nunca — que es lo que los hace peligrosos: alguien los escribió creyendo que protegían
  algo. En el backend de referencia había uno así, con `APIClient` y todo, y dos de sus tres tests
  además comentados.

## La avería que NINGÚN test coge: la pieza declarada y nunca enchufada

**Cosechado de `elvion-autoparte-demo` el 2026-08-27, donde aparecieron CINCO casos del mismo
patrón** — y los cinco pasaban toda la suite.

### El mecanismo, que es lo reutilizable

Un test de vista hace esto para aislarse, y hace bien:

```python
@override_settings(ROOT_URLCONF=__name__)   # el test monta SU PROPIO enrutado
def test_el_endpoint_responde(): ...
```

Con eso el test mide **la vista**, que suele estar bien. **Nadie mide la INSTALACIÓN**: que el
proyecto agregue de verdad lo que la app declara. Y ahí caben averías que no dan error de
importación, no rompen ningún test, y solo se ven corriendo el sistema entero.

Las cinco caras que se midieron, para reconocerlas:

| Se declara | Y el proyecto no lo agrega | Síntoma |
|---|---|---|
| `apps/x/urls.py` | falta el `include()` en el `urls.py` del proyecto | 404 en una ruta que "existe" |
| `apps/x/routing.py` | `websocket_urlpatterns = []` en el del proyecto | **500 en el handshake**, no 404: cuesta más de diagnosticar |
| `AppConfig.ready()` | Django carga el `AppConfig` genérico | Las señales no se registran. **El mensaje se guarda, se marca procesado y nadie contesta — con 200 al cliente**, que es la peor variante |
| `@shared_task` periódica | sin `beat_schedule` ni contenedor `beat` | Cuatro tareas escritas y ninguna programada |
| Un id de sesión | el consumer pasa un pk y la ingesta resuelve por otro campo | Cada mensaje crea conversación nueva y la respuesta va a un grupo vacío |

### El guardia, que se escribe una vez

Un test **sin `override_settings`**, contra los mismos objetos que lee el servidor, y con un
recorrido general que falla cuando una app declara algo que el proyecto no agrega:

```python
def test_toda_app_con_routing_propio_esta_agregada_en_el_del_proyecto():
    """Si mañana otra app declara `websocket_urlpatterns`, esto falla hasta que se agregue
    —o hasta que alguien escriba aquí que se deja fuera a propósito—, que es justo la decisión
    que las dos veces se tomó sin querer."""
    import importlib, pkgutil, apps
    for modulo in pkgutil.iter_modules(apps.__path__):
        try:
            propias = importlib.import_module(f"apps.{modulo.name}.routing").websocket_urlpatterns
        except ModuleNotFoundError:
            continue
        agregadas = {str(p.pattern) for p in websocket_urlpatterns}
        faltan = [str(p.pattern) for p in propias if str(p.pattern) not in agregadas]
        assert not faltan, (
            f"apps.{modulo.name}.routing declara {faltan} y el proyecto no las agrega. "
            "El consumer funcionará en sus tests y dará 500 en el servidor."
        )
```

Lo que lo hace un guardia y no un test más: **recorre las apps en vez de enumerarlas**, así que
cubre la app que alguien añada mañana. La referencia completa —6 tests, 138 líneas— está en
`elvion-autoparte-demo/tests/seguridad/test_superficie_desplegada.py`.

### Cómo se comprueba en cualquier proyecto

**No mires la declaración: mira lo que Django cargó.** Es la misma disciplina de
`rules/verification.md` §1 —`check` en verde no significa que el esquema aplique— aplicada al
arranque:

```python
from django.apps import apps as django_apps
for cfg in django_apps.get_app_configs():
    # ¿la clase cargada viene del apps.py DE LA APP, o del genérico de Django?
    print(cfg.name, cfg.__class__.__name__, cfg.__class__.__module__ == f"{cfg.name}.apps")
```

> ⚠️ **Y el falso positivo que este check produce, medido el mismo día:** si comparas leyendo el
> fichero del `AppConfig` cargado (`inspect.getfile`), para el genérico estarás leyendo el
> `apps.py` **de Django**, que también tiene `def ready` — y marcarás como averiada una app cuyo
> `apps.py` está simplemente vacío. Compara el **módulo**, no el contenido del fichero.

## Qué se testea (y qué no) — la pirámide honesta

| Nivel | Qué cubre | Cuánto |
|---|---|---|
| **Servicios** (`services.py`/`utils.py`) | las reglas de negocio: estados, cálculos, invariantes | **La mayoría.** Son funciones puras o casi: baratas, rápidas, sin HTTP |
| **Modelos** | lo que la BD debe rechazar: constraints, unicidad | Pocos y muy concretos. Uno por invariante que importe |
| **Vistas / API** | el contrato: status, forma del error, permisos | Los flujos que dan dinero y **el filtrado por dueño** — que un usuario no ve las filas de otro es el test que más vale de todo el backend |
| **Tasks** | idempotencia (`be-celery-ackslate-idempotente` lo exige por nombre) | Una por task con `acks_late=True` |
| E2E con navegador | el camino feliz completo | Fuera de aquí: `rules/verification.md` §Estabilidad E2E |

## Cómo se comprueba

```bash
python3 .claude/patterns/stack/pattern_check_backend.py --rules be-test-stub-vacio,\
be-test-descubrible,be-test-db-alias-sin-engine
```

| Regla | Estado | Qué detecta |
|---|---|---|
| `be-test-stub-vacio` | activo | `tests.py` sin ninguna función `test*` ni clase — el andamio de `startapp` |
| `be-test-descubrible` | activo | fichero con `def test_…` cuyo nombre no casa con `test*.py` / `*_test.py` |
| `be-test-db-alias-sin-engine` | activo | alias de `DATABASES` sin `ENGINE` — la suite no arranca |

**Lo que NO se comprueba, y hay que decirlo:** no hay ninguna regla que mida **cobertura** ni que
exija un test por cambio. No es un olvido, es una decisión — medir cobertura exige correr la suite
con `--cov`, que es justo lo que el límite de RAM de esta máquina prohíbe, y una regla que no se
puede ejecutar no entra en el catálogo (README, regla 3). El gate de cobertura, cuando exista, será
una comprobación de CI, no de este checker.

Segundo límite honesto: `be-celery-ackslate-idempotente` se apoya en *"existe un fichero de test
que nombra la task"*. En un proyecto con 2 tests reales esa regla **no puede disparar de forma
útil** — no porque esté mal escrita, sino porque no hay contra qué comprobar. Es otra forma de
decir que este documento sostiene a los demás.

## Excepciones legítimas

- **App sin lógica** (solo migraciones, o solo un `AppConfig`): no necesita tests, pero **tampoco
  necesita un `tests.py` vacío**. Bórralo; la ausencia es información honesta.
- **Fichero de exploración manual** que hace `requests` contra un servicio real: eso no es un test.
  Que no se llame `test_*` y que viva fuera de `tests/`, con su cabecera `# runner:`
  (`backend-estructura-apps.md`).
- **Test de rendimiento o de carga**: fuera de la suite normal, en su propia marca
  (`-m lento`), y nunca en el camino del gate.

## Related

- **`rules/ram-pytest.md`** — el límite duro y el hook `check-ram.sh` que lo aplica de verdad
- `rules/verification.md` §Estabilidad E2E (estado determinista, `data-testid`, flakiness en CI) ·
  `rules/verification.md` (la escalera de 4 niveles del gate) · `rules/qa-loop.md`
- `backend-signals.md` (§`on_commit` y por qué su test miente) · `backend-celery.md` (idempotencia)
- skills `django-orm` (`references/crud.md`), `verification-loops`, `code-review-gate` (la rúbrica de 6 puntos para
  **juzgar** tests generados por IA) · skill `escribir-tests` (el ORDEN para escribirlos: nivel,
  ubicación, ejecución segura y criterio de salida — este documento es su mecanismo)
