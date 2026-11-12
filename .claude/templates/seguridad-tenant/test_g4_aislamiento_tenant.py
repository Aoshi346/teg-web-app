"""G4 · Aislamiento entre tenants, como gate: ninguna consulta de A ve, ni escribe, filas de B.

Plantilla del template (sub-ola 2.24, SE-21). Junta lo que en casa estaba repartido:

  · `elvion-autoparte-demo/tests/seguridad/` — el barrido por TODOS los modelos con tenant,
    descubiertos (`g4_inventario.py`), y la pareja que lo hace honesto: «A no ve la fila de B» va
    siempre con «el dueño sí ve la suya». Un filtro que no devuelve nada aprueba la primera mitad
    SIEMPRE, y sin la segunda el gate aprobaría un producto inservible.
  · `cold_calling_coach/backend/tests/test_aislamiento_cross_tenant.py` — el ámbito que se abre y
    se cierra en la MISMA conexión, una petición detrás de otra (`SET LOCAL`, no `SET`: Django
    reutiliza conexiones), y la escritura cruzada como permiso aparte de la lectura.
  · `gate_tenant.py` sobre la base de test: rol sin superusuario ni BYPASSRLS, RLS ENCENDIDO y
    FORZADO en cada tabla con la columna, y ninguna política que no filtre.

Se corre APARTE, no por app (la propiedad es del sistema, no de ninguna app):

    bash .claude/hooks/check-ram.sh && pytest tests/seguridad/test_g4_aislamiento_tenant.py -v

Necesita `pytest-django` y la base de test en el mismo motor que producción (Postgres): con SQLite
no hay RLS que medir. Y en modo rls, el USER de la base de test tiene que ser el ROL DE LA APP, no
un superusuario: es la condición sin la cual nada de esto prueba nada (lo comprueba el primer test).

Regla al fallar, que vale también para quien amplíe esto: ningún assert pega el contenido de la
fila ajena. Se dice el modelo y cuántas filas salieron.
"""
from __future__ import annotations

# gate: G4-tenant

import ast
import inspect
import json
import os
import pathlib
import subprocess
import sys
from urllib.parse import quote

import pytest

_AQUI = pathlib.Path(__file__).resolve().parent
if str(_AQUI) not in sys.path:
    sys.path.insert(0, str(_AQUI))

import g4_adaptador as adaptador  # noqa: E402
from g4_constructor import construir, valores_para  # noqa: E402
from g4_inventario import COLUMNA_TENANT, campo_tenant, etiqueta, modelos_con_tenant  # noqa: E402

RAZON_MINIMA = 15
MODELOS = modelos_con_tenant()
SALTADOS = set(adaptador.EXCEPCIONES) | set(adaptador.SIN_CONSTRUCTOR)
CUBIERTOS = [m for m in MODELOS if etiqueta(m) not in SALTADOS]

pytestmark = pytest.mark.django_db(transaction=True)
# transaction=True a propósito: cada ámbito es una transacción de verdad, como en una petición.
# Dentro de la transacción única de un test normal, `SET LOCAL` no llega a morir nunca y el test
# del ámbito pegado a la conexión pasaría siempre.


@pytest.fixture
def tenant_a():
    return adaptador.crear_tenant("Prueba G4 A")


@pytest.fixture
def tenant_b():
    """El vecino. Sus filas son las que NUNCA pueden salir por una consulta de A."""
    return adaptador.crear_tenant("Prueba G4 B")


def _sin_ambito_es_cero(modelo, **filtro) -> None:
    try:
        vistas = adaptador.contar_sin_ambito(modelo, **filtro)
    except adaptador.EXCEPCIONES_DE_CIERRE:
        return  # reventar sin ámbito también es cerrado
    assert vistas == 0, (
        f"FUGA en {etiqueta(modelo)}: sin abrir ningún ámbito salieron {vistas} fila(s). «Sin "
        "tenant» tiene que ser «sin datos»; o el ámbito de una consulta anterior se quedó pegado "
        "a la conexión (SET en vez de SET LOCAL)."
    )


# ── 0. ¿La suite está en condiciones de probar algo? ───────────────────────────────────────


def test_el_inventario_no_esta_vacio():
    assert MODELOS, (
        f"0 modelos con la columna {COLUMNA_TENANT}. Un barrido de cero modelos sale en verde sin "
        "probar nada: revisa COLUMNA_TENANT en g4_adaptador.py."
    )


def test_el_adaptador_esta_relleno():
    """Un adaptador a medias es una suite que no prueba nada y que nadie mira porque sale verde."""
    arbol = ast.parse(inspect.getsource(adaptador))
    pendientes = [
        f.name for f in arbol.body if isinstance(f, ast.FunctionDef)
        and any(isinstance(n, ast.Raise) and "NotImplementedError" in ast.unparse(n)
                for n in ast.walk(f))
    ]
    assert not pendientes, f"g4_adaptador.py tiene funciones sin rellenar: {pendientes}"
    assert adaptador.MODO in ("rls", "aplicacion"), f"MODO desconocido: {adaptador.MODO!r}"


def test_las_excepciones_no_crecen_solas():
    etiquetas = {etiqueta(m) for m in MODELOS}
    for nombre, lista in (("EXCEPCIONES", adaptador.EXCEPCIONES),
                          ("SIN_CONSTRUCTOR", adaptador.SIN_CONSTRUCTOR)):
        for et, razon in lista.items():
            assert et in etiquetas, (
                f"{nombre} declara {et}, que ya no es un modelo con {COLUMNA_TENANT}: quítalo. Una "
                "excepción que no corresponde a nada es una lista que crece sola."
            )
            assert isinstance(razon, str) and len(razon.strip()) >= RAZON_MINIMA, (
                f"{nombre}[{et}] sin una razón escrita: saltarse el aislamiento es una decisión"
            )


# ── 1. La base de datos: gate_tenant.py sobre la base de test ─────────────────────────────


def _gate() -> pathlib.Path:
    if os.environ.get("GATE_TENANT"):
        return pathlib.Path(os.environ["GATE_TENANT"])
    for carpeta in [_AQUI, *_AQUI.parents]:
        candidato = carpeta / ".claude" / "scripts" / "gate_tenant.py"
        if candidato.exists():
            return candidato
    pytest.fail("no encuentro .claude/scripts/gate_tenant.py hacia arriba; define GATE_TENANT")


def _dsn(settings: dict, base: str | None = None) -> str:
    usuario = quote(settings.get("USER") or "", safe="")
    clave = quote(settings.get("PASSWORD") or "", safe="")
    host = settings.get("HOST") or "127.0.0.1"
    if ":" in host and not host.startswith("["):
        host = f"[{host}]"  # IPv6
    puerto = settings.get("PORT") or "5432"
    cred = f"{usuario}:{clave}@" if clave else f"{usuario}@"
    return f"postgresql://{cred}{host}:{puerto}/{base or settings['NAME']}"


def test_gate_tenant_pasa_sobre_la_base_de_test(tenant_a, tenant_b, tmp_path):
    """El gate de base de datos, con el rol con el que corre esta suite y datos de dos tenants.

    En modo rls mira el rol, RLS+FORCE y las políticas; con `GATE_TENANT_DSN_ADMIN` (un rol que vea
    todo, en el mismo servidor) corre además la sonda de dos tenants —lectura Y escritura, porque
    esta es una base de test, y una escritura que no se pudo probar es un rojo— sobre las filas que
    se construyen aquí. Sin ese DSN corre solo lo
    estático (`--solo-estatico`), que es léxico: dilo así en el CI. En modo aplicacion mira NOT NULL
    y clave ajena. Las credenciales van por entorno, no en la línea de comandos
    (`/proc/<pid>/cmdline` lo lee cualquier usuario local).
    """
    from django.db import connection

    if connection.vendor != "postgresql":
        pytest.fail(f"la base de test es {connection.vendor}: G4 necesita Postgres, como "
                    "producción")
    for modelo in CUBIERTOS:
        construir(modelo, tenant_a)
        construir(modelo, tenant_b)
    manifiesto = tmp_path / "gate-tenant.json"
    manifiesto.write_text(json.dumps({
        "modo": adaptador.MODO,
        "columna": COLUMNA_TENANT,
        "ajuste": getattr(adaptador, "AJUSTE", "app.tenant_id"),
        "funciones_de_ambito": list(getattr(adaptador, "FUNCIONES_DE_AMBITO", ())),
        "excepciones": {m._meta.db_table: adaptador.EXCEPCIONES[etiqueta(m)]
                        for m in MODELOS if etiqueta(m) in adaptador.EXCEPCIONES},
    }))
    orden = [sys.executable, str(_gate()), "--manifiesto", str(manifiesto), "--json"]
    entorno = {k: v for k, v in os.environ.items() if k != "GATE_TENANT_DSN_ADMIN"}
    entorno["GATE_TENANT_DSN"] = _dsn(connection.settings_dict)
    admin = os.environ.get("GATE_TENANT_DSN_ADMIN")
    if admin:
        entorno["GATE_TENANT_DSN_ADMIN"] = (admin.rsplit("/", 1)[0] + "/"
                                            + connection.settings_dict["NAME"])
        orden += ["--sonda-escritura", "--exigir-sonda", "--exigir-escritura"]
    else:
        orden += ["--solo-estatico"]
    r = subprocess.run(orden, capture_output=True, text=True, timeout=300, env=entorno)
    try:
        salida = json.loads(r.stdout)
    except json.JSONDecodeError:
        pytest.fail(f"gate_tenant.py no devolvió JSON (exit {r.returncode}): {r.stderr[-500:]}")
    hallazgos = [f"[{h['id']}] {h['tabla']}: {h['que']}" for h in salida.get("hallazgos", [])]
    assert r.returncode == 0, (
        f"gate_tenant.py sale {r.returncode} ({salida.get('veredicto')}): "
        + ("; ".join(hallazgos) or salida.get("porque", ""))
    )
    if admin and adaptador.MODO == "rls":
        # El instrumento dice qué midió: con filas de dos tenants en cada tabla cubierta, la sonda
        # tiene que haberlas medido todas. Un «ok» sin sonda no es lo que se pidió.
        medidas = set(salida.get("sonda", {}).get("tablas_medidas", []))
        faltan = {m._meta.db_table for m in CUBIERTOS} - medidas
        assert not faltan, f"la sonda de dos tenants no midió {sorted(faltan)}"


# ── 2. El ORM: dos tenants, modelo a modelo ───────────────────────────────────────────────


@pytest.mark.parametrize("modelo", CUBIERTOS, ids=etiqueta)
def test_una_consulta_de_a_no_ve_la_fila_de_b(modelo, tenant_a, tenant_b):
    """Se consulta desde A por el id EXACTO de una fila de B: quien ataca conoce el id."""
    ajena = construir(modelo, tenant_b)
    vistas = adaptador.contar_como(modelo, tenant_a, pk=ajena.pk)
    assert vistas == 0, (
        f"FUGA en {etiqueta(modelo)}: consultando como A por el id de una fila de B salieron "
        f"{vistas} fila(s). El contenido no se pega aquí a propósito."
    )


@pytest.mark.parametrize("modelo", CUBIERTOS, ids=etiqueta)
def test_el_dueno_si_ve_su_fila(modelo, tenant_b):
    """El control negativo, y no es relleno: sin él, un filtro roto que no devuelve nada aprueba."""
    propia = construir(modelo, tenant_b)
    assert adaptador.contar_como(modelo, tenant_b, pk=propia.pk) == 1, (
        f"{etiqueta(modelo)}: el tenant dueño no ve su propia fila. El aislamiento «perfecto» de "
        "los otros tests no vale nada si el filtro no deja ver ni lo propio."
    )


@pytest.mark.parametrize("modelo", CUBIERTOS, ids=etiqueta)
def test_sin_ambito_no_se_ve_nada(modelo, tenant_b):
    fila = construir(modelo, tenant_b)
    _sin_ambito_es_cero(modelo, pk=fila.pk)


@pytest.mark.parametrize("modelo", CUBIERTOS, ids=etiqueta)
def test_dos_tenants_en_la_misma_conexion(modelo, tenant_a, tenant_b):
    """A, B, A y luego ninguno, en la MISMA conexión: como un pool que atiende peticiones seguidas.

    Si el ámbito se abriera con `SET` y no con `SET LOCAL`, se quedaría pegado a la conexión y la
    petición siguiente heredaría el tenant de la anterior (CCC, `core/db.py`). No es un problema de
    rendimiento: es una fuga entre clientes que no ve ningún test que abra siempre su propio ámbito.
    """
    from django.db import connection

    fila_a, fila_b = construir(modelo, tenant_a), construir(modelo, tenant_b)
    connection.ensure_connection()
    conexion = connection.connection
    pasos = [(tenant_a, fila_a, 1), (tenant_a, fila_b, 0), (tenant_b, fila_b, 1),
             (tenant_b, fila_a, 0), (tenant_a, fila_a, 1)]
    for tenant, fila, esperadas in pasos:
        vistas = adaptador.contar_como(modelo, tenant, pk=fila.pk)
        assert vistas == esperadas, (
            f"{etiqueta(modelo)}: con el ámbito de un tenant se vieron {vistas} fila(s) donde "
            f"tocaban {esperadas} — en la misma conexión, tras otro ámbito"
        )
    _sin_ambito_es_cero(modelo, pk=fila_a.pk)
    _sin_ambito_es_cero(modelo, pk=fila_b.pk)
    assert connection.connection is conexion, (
        "la conexión cambió a mitad del test: entonces no se ha probado la misma conexión"
    )


@pytest.mark.parametrize("modelo", CUBIERTOS, ids=etiqueta)
def test_desde_a_no_se_escribe_en_b(modelo, tenant_a, tenant_b):
    """El cliente manda el tenant ajeno en el cuerpo. Leer y escribir son dos permisos distintos.

    Vale que reviente (la política WITH CHECK) o que la fila acabe en A (el manager lo impone). Lo
    que no vale es que quede en B.
    """
    from django.db import DatabaseError

    campo = campo_tenant(modelo)
    antes = adaptador.contar_como(modelo, tenant_b)
    valores = {**valores_para(modelo, tenant_b), campo.name: tenant_b}
    try:
        creada = adaptador.crear_como(modelo, tenant_a, valores)
    except (DatabaseError, *adaptador.EXCEPCIONES_DE_CIERRE):
        # Solo cuenta como «cerrado» un rechazo de la BASE (la política) o del cierre declarado.
        # Un TypeError o un AttributeError del adaptador no es una defensa: es un test roto, y se
        # deja subir para que se vea (el control positivo de abajo lo cubre por el otro lado).
        creada = None
    despues = adaptador.contar_como(modelo, tenant_b)
    assert despues == antes, (
        f"ESCRITURA CRUZADA en {etiqueta(modelo)}: desde el ámbito de A se creó una fila en B "
        f"({antes} → {despues})"
    )
    if creada is not None:
        assert getattr(creada, campo.attname) == tenant_a.pk, (
            f"{etiqueta(modelo)}: la fila creada desde A no quedó en A"
        )


@pytest.mark.parametrize("modelo", CUBIERTOS, ids=etiqueta)
def test_el_dueno_si_escribe_lo_suyo(modelo, tenant_a):
    """El control positivo de la escritura: la misma vía, con el tenant PROPIO, sí crea la fila.

    Sin él, un `crear_como` que fallara siempre —un ámbito mal abierto, un AJUSTE que falta—
    aprobaría el test de arriba en todos los modelos sin haber probado nada.
    """
    campo = campo_tenant(modelo)
    antes = adaptador.contar_como(modelo, tenant_a)
    valores = {**valores_para(modelo, tenant_a), campo.name: tenant_a}
    adaptador.crear_como(modelo, tenant_a, valores)
    despues = adaptador.contar_como(modelo, tenant_a)
    assert despues == antes + 1, (
        f"{etiqueta(modelo)}: desde su propio ámbito, el tenant no pudo crear su fila "
        f"({antes} → {despues}): el test de escritura cruzada no está probando nada"
    )
