"""ANTIPATRÓN A PROPÓSITO — dos infracciones en un fichero de doce líneas.

be-capa-compartida-importa-dominio: `core` es la capa compartida y aquí importa `expedientes`,
que es dominio. La flecha va del revés, y ese es el origen del ciclo que después se parchea
metiendo imports dentro de las funciones. En SOMBRA: mide, no bloquea — promoverlo a bloqueante
exige antes una lista de excepciones del tamaño del repo, y ese coste se decide con el número
delante, no de oído.

be-py-monkeypatch-django: inyectar `for_user` en la clase `Manager` de Django afecta a TODO el
proceso — contrib.auth, el admin y cualquier librería de terceros. Desde `Expediente.objects
.for_user(...)` no hay forma de llegar a esta definición con «ir a definición», el choque de
nombre con otra librería sería silencioso, y el propio parche crea el ciclo por el que el import
de arriba tuvo que subir aquí.
"""
from django.db.models import Manager

from expedientes.models import Expediente


def for_user(self, usuario):
    return self.filter(owner=usuario)


Manager.for_user = for_user
