"""be-test-descubrible: tiene tests de verdad y NO se ejecutan nunca.

El descubrimiento por defecto de Django es `test*.py` y el de pytest `test_*.py` / `*_test.py`.
`expedientes_tests.py` no casa con ninguno: estos tests no corren, no fallan, y por eso nadie se
entera. Parece cobertura y no la da.
"""


def test_referencia_es_unica():
    assert True


def test_estado_por_defecto_es_borrador():
    assert True
