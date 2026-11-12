# Señales (`signals.py`) — patrón de casa

> **Cuándo aplicar:** al escribir o tocar cualquier `@receiver`, y al decidir si algo debe reaccionar
> a un guardado o llamarse explícitamente.
>
> **NO aplicar:** para decidir dónde vive la lógica de negocio en general (`backend-servicios.md`)
> ni para el encolado desde un servicio o una vista (`backend-celery.md`, que cubre el `.delay()`
> dentro de `atomic()`). Esta página es sobre lo que pasa **dentro de un receiver**, que es un
> contexto distinto y con una trampa propia.

## La regla (una frase)

**Un receiver corre DENTRO de la transacción de quien guardó: en `signals.py` solo hay receivers, y
todo efecto que salga de la base de datos espera al COMMIT.**

## Por qué el receiver es un contexto especial

`backend-celery.md` ya prohíbe encolar dentro de `transaction.atomic()`. Un receiver es el mismo
problema **sin el `atomic()` a la vista**: el receiver no abre transacción, hereda la de quien
llamó a `save()`. Desde el fichero del receiver no hay forma de saber si hay una transacción
abierta — y en un backend con una vista CRUD genérica que envuelve `form.save()` en `atomic()`
para todas sus tablas, la respuesta es *siempre sí*.

La carrera es real y está medida en el backend de referencia: la vista CRUD que sirve 356 tablas
abre `atomic()`; dentro, el receiver de vacunas hace `tarea.delay(instance.id)` y la tarea hace
`get(id=...)`. El broker entrega el mensaje en milisegundos; el COMMIT puede tardar más. El worker
lee una fila que todavía no existe — o peor: la transacción acaba en rollback, y el aviso ya salió
de una operación que no ocurrió.

Y el precedente correcto **ya estaba en casa**, en un solo sitio de todo el repositorio
(`health/laboratory_test/forms.py:158`). El conocimiento existía; no se aplicó en los otros 7.

## Implementación de referencia

`_fixtures/conforme-casa/expedientes/signals.py`:

```python
from functools import partial

@receiver(post_save, sender=Expediente, dispatch_uid="expedientes.avisar_apertura")
def avisar_apertura(sender, instance, created, **kwargs):
    if not created:
        return
    transaction.on_commit(partial(avisar_apertura_expediente.delay, str(instance.pk)))
```

Cuatro detalles que no son casuales:

- **`transaction.on_commit`**: si no hay transacción abierta, el callback se ejecuta
  inmediatamente; si la hay, espera al COMMIT y **no se ejecuta si hay rollback**. Es correcto en
  los dos casos, así que no hay que saber cuál es.
- **`partial` y no `lambda`**: dentro de un bucle, el `lambda` captura la **variable**, no su valor,
  y las N llamadas acaban usando el último elemento. Con `partial` el argumento se congela aquí.
  Es un bug clásico y silencioso: no falla, manda N avisos del mismo objeto.
- **`sender=`**: un receiver sin `sender` se conecta a **todos los modelos**. Además del coste
  obvio, Django desactiva su ruta rápida de borrado (`can_fast_delete`) para cualquier modelo con
  listeners, así que cada `.delete()` pasa a cargar filas en memoria — en el repositorio de
  referencia, dos receivers globales le hacían eso a los 360 modelos.
- **`dispatch_uid`**: evita el registro doble si el módulo se importa dos veces.

**Dónde se registran:** en `AppConfig.ready()`, con `from . import signals`. Es el sitio que
documenta Django, es greppable y es determinista — quien busque "quién conecta las señales" lo
encuentra. Mejor que un `autodiscover` mágico.

## En `signals.py` solo hay receivers

La segunda regla de esta capa, y la que un análisis del backend real señaló como *"la de mayor
rendimiento"*: **9 funciones de negocio estaban definidas dentro de `signals.py`** —de 40 y 60
líneas, creando y actualizando agregados— y solo se las llamaba desde el propio `signals.py`. Una
estaba **anidada dentro de un receiver**.

Nada fuera del ciclo `post_save` puede reutilizarlas. El día que haya que hacer eso mismo en batch
—un import, un comando, un test— se reescribe la misma lógica al lado, y a partir de ahí hay dos
versiones que divergen en el primer cambio. Es el error que `backend-servicios.md` describe, en el
único sitio donde `be-svc-sin-drf` no podía verlo.

```python
# ❌ infractor-casa/expedientes/signals.py
def crear_nota_de_apertura(expediente):        # no es receiver, escribe en la BD, vive aquí
    expediente.notas.create(texto="expediente abierto")

# ✅ la función vive en services.py y el receiver la llama
@receiver(post_save, sender=Expediente)
def al_guardar(sender, instance, created, **kwargs):
    if created:
        crear_nota_de_apertura(instance)       # importada de .services
```

## Cuándo NO usar una señal

Una señal es **control de flujo invisible**: en el sitio de la llamada nada indica que guardar un
objeto crea otros cuatro. Úsala cuando el efecto sea genuinamente transversal (auditoría, caché,
índices de búsqueda) y el emisor no deba saber quién escucha. Si el flujo es *"al abrir un
expediente hay que crear su nota"*, eso es una regla de negocio: va en el servicio, en la misma
función, donde se lee.

Señal de alarma medida en la referencia: **27 sitios** donde el código comprueba una bandera del
tipo `_skip_email_signal` o `_skip_scoring` antes de guardar. Cada uno de esos es el propio equipo
diciendo en voz alta *"aquí necesitaba guardar sin la cascada"*. Cuando aparece el tercero, el
problema no es la bandera: es que la lógica no debería estar en un receiver.

## Cómo se comprueba

```bash
python3 .claude/patterns/stack/pattern_check_backend.py --rules be-sig-efecto-sin-on-commit,\
be-sig-logica-de-negocio
```

| Regla | Estado | Qué detecta (AST) |
|---|---|---|
| `be-sig-efecto-sin-on-commit` | activo | dentro de una función decorada con `@receiver`: `.delay()`/`.apply_async()`, `send_mail`, `requests.*`/`httpx.*` o una escritura a otro almacén, **fuera** de `transaction.on_commit(...)` |
| `be-sig-logica-de-negocio` | débil | en `signals.py`, una función **sin** decorador `receiver` que hace escrituras ORM |

Dos decisiones de implementación que valen la pena:

1. **Se analiza por `FunctionDef`, no por presencia en el módulo.** Comprobar "¿aparece
   `on_commit` en este fichero?" daría verde con el bug vivo: basta con que **otro** receiver del
   mismo fichero lo use bien.
2. **Se sigue un nivel de indirección.** Si el receiver llama a un helper del propio módulo y es
   *el helper* quien lanza el efecto sin proteger, el hallazgo se reporta en la llamada. Sin eso,
   mover el `.delay()` una función más abajo apaga el checker sin arreglar nada.

**El límite honesto:** solo un nivel, y solo dentro del mismo fichero. Un efecto tres saltos más
abajo, o en otro módulo, no se ve. Y al revés: el checker **no puede saber** si el `save()` que
disparó el receiver estaba dentro de una transacción — por eso la regla exige `on_commit`
siempre, aunque en algún caso concreto no hiciera falta. Es la asimetría correcta: el coste de
ponerlo de más es cero.

## ⚠️ El test de esto puede estar en verde sin probar nada

Al migrar los efectos a `on_commit`, **los tests que los cubren dejan de ejercitarlos**: en
`TestCase` y en `pytest.mark.django_db` la transacción nunca hace COMMIT, así que los callbacks
registrados **no se ejecutan jamás**. Un test que asserta el efecto pasa a estar verde sin haber
probado nada, y no avisa.

```python
with TestCase.captureOnCommitCallbacks(execute=True) as callbacks:
    abrir_expediente(...)
assert len(callbacks) == 1
```

Es lo que convierte esta migración de 2 horas en 2 días: el arreglo es mecánico, **auditar los
tests de esas rutas no lo es**. No aceptes una estimación que se salte esa parte. Detalle en
`backend-tests.md`.

## Excepciones legítimas

- **Auditoría que debe registrarse incluso si hay rollback** (un intento fallido también es un
  hecho): `# pattern-exempt: be-sig-efecto-sin-on-commit — queremos el registro aunque la
  operación se deshaga`.
- **Efecto que solo toca la propia base de datos** (crear una fila relacionada): no es un efecto
  "hacia fuera" y la regla no lo mira — vive en la misma transacción, que es lo correcto.
- **Helper privado en `signals.py`** que no escribe (formatea, calcula): `be-sig-logica-de-negocio`
  solo mira funciones con escrituras ORM.

## Related

- `backend-celery.md` — el mismo problema visto desde el otro lado: `.delay()` dentro de `atomic()`
- `backend-servicios.md` — a dónde se mueve la función que estaba escondida aquí
- `backend-tests.md` — §`captureOnCommitCallbacks`, sin la cual esta migración no se puede verificar
- Doc oficial: <https://docs.djangoproject.com/en/5.2/topics/signals/> ·
  `transaction.on_commit`: <https://docs.djangoproject.com/en/5.2/topics/db/transactions/>
