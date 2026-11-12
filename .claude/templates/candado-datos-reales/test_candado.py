"""El candado de datos reales. Si estos tests pasan a verde solos, alguien lo ha desarmado.

Se copia junto a `candado.py` (p. ej. `backend/core/seguridad/tests/test_candado.py`) y se ajusta el
import. Cosechado del `test_candado.py` de accounting_AMC; los casos de firma son de la sub-ola 2.29.
"""
import json

import pytest

try:                                    # el import del proyecto; ajústalo al copiar
    from core.seguridad.candado import MODOS, VARIABLE, CandadoCerrado, comprobar_candado
except ImportError:                     # la autoprueba del template lo importa por ruta
    from candado import MODOS, VARIABLE, CandadoCerrado, comprobar_candado

FIRMA = {"quien": "Ana Ruiz (DPD del cliente)", "fecha": "2026-01-15",
         "evidencia": "docs/cumplimiento/encargo-firmado.pdf"}
MODO = MODOS[0] if MODOS else "CRM_MODE"


def _raiz(tmp_path, condiciones):
    d = tmp_path / ".claude"
    d.mkdir()
    (d / "estado-datos-reales.json").write_text(json.dumps({"condiciones": condiciones}),
                                                encoding="utf-8")
    return tmp_path


@pytest.fixture
def raiz_verde(tmp_path):
    return _raiz(tmp_path, {"encargo_firmado": {"ok": True, **FIRMA}})


@pytest.fixture
def raiz_roja(tmp_path):
    return _raiz(tmp_path, {"encargo_firmado": {"ok": False, **FIRMA}})


def test_modo_real_con_candado_cerrado_no_arranca(tmp_path):
    """El caso de partida: una integración en `real` con la variable a 0 se niega."""
    with pytest.raises(CandadoCerrado) as exc:
        comprobar_candado({MODO: "real", VARIABLE: "0"}, raiz=tmp_path, modos=(MODO,))
    # El mensaje tiene que decir QUÉ pasa y CÓMO comprobarlo, o el candado solo estorba.
    assert MODO in str(exc.value)
    assert "gate_datos_reales.py" in str(exc.value)


def test_todo_en_mock_arranca(tmp_path):
    comprobar_candado({VARIABLE: "0"}, raiz=tmp_path, modos=(MODO,))
    comprobar_candado({MODO: "mock"}, raiz=tmp_path, modos=(MODO,))


def test_entorno_vacio_es_seguro(tmp_path):
    """Sin variables, el defecto es mock y candado cerrado: el fallo seguro es no tocar nada."""
    comprobar_candado({}, raiz=tmp_path, modos=(MODO,))


def test_variable_abierta_con_el_gate_en_rojo_es_incoherente(raiz_roja):
    """Poner la variable a 1 «para probar» es EL error que este cruce existe para cazar."""
    with pytest.raises(CandadoCerrado, match="ROJO"):
        comprobar_candado({VARIABLE: "1"}, raiz=raiz_roja, modos=(MODO,))


def test_un_verde_sin_firma_no_abre(tmp_path):
    """`ok: true` sin quién, cuándo ni evidencia es un fichero editado a mano, no un permiso."""
    raiz = _raiz(tmp_path, {"encargo_firmado": {"ok": True}})
    with pytest.raises(CandadoCerrado, match="encargo_firmado"):
        comprobar_candado({VARIABLE: "1"}, raiz=raiz, modos=(MODO,))


def test_variable_abierta_con_el_gate_en_verde_arranca(raiz_verde):
    comprobar_candado({VARIABLE: "1", MODO: "real"}, raiz=raiz_verde, modos=(MODO,))


def test_sin_estado_manda_solo_el_entorno(tmp_path):
    """En producción no existe .claude/: que falte no se lee como «todo en orden»…

    …pero tampoco impide arrancar con el permiso ya firmado. El contrato: sin el fichero, manda el
    entorno, que es la única fuente que hay allí. Y el modo real con la variable a 0 se sigue negando.
    """
    comprobar_candado({VARIABLE: "1"}, raiz=tmp_path, modos=(MODO,))
    with pytest.raises(CandadoCerrado):
        comprobar_candado({VARIABLE: "0", MODO: "real"}, raiz=tmp_path, modos=(MODO,))


def test_requisito_con_datos_reales(raiz_verde):
    """Lo que tiene que existir además con datos reales (en AMC, una clave de cifrado propia)."""
    with pytest.raises(CandadoCerrado, match="CLAVE_PROPIA"):
        comprobar_candado({VARIABLE: "1"}, raiz=raiz_verde, modos=(MODO,),
                          requisitos=("CLAVE_PROPIA",))
    with pytest.raises(CandadoCerrado, match="CLAVE_PROPIA"):
        comprobar_candado({VARIABLE: "1", "CLAVE_PROPIA": "  "}, raiz=raiz_verde, modos=(MODO,),
                          requisitos=("CLAVE_PROPIA",))
    comprobar_candado({VARIABLE: "0"}, raiz=raiz_verde, modos=(MODO,), requisitos=("CLAVE_PROPIA",))


@pytest.mark.parametrize("contenido", ['{"condiciones": {"e": {"ok": tr', "", "[]", '{"condiciones": {}}'])
def test_un_estado_ilegible_o_vacio_no_abre(tmp_path, contenido):
    """Que el fichero exista y no se pueda leer no es «producción sin harness»: no abre nada."""
    (tmp_path / ".claude").mkdir()
    (tmp_path / ".claude" / "estado-datos-reales.json").write_text(contenido, encoding="utf-8")
    with pytest.raises(CandadoCerrado, match="ROJO"):
        comprobar_candado({VARIABLE: "1", MODO: "real"}, raiz=tmp_path, modos=(MODO,))
