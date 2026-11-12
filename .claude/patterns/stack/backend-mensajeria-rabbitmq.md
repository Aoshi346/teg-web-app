# Mensajería con RabbitMQ — patrón de casa

> **Cuándo aplicar:** al declarar colas, exchanges o routing de Celery sobre RabbitMQ.
> **Verificado contra la doc oficial de RabbitMQ** (docs/quorum-queues) el 2026-08-08.
>
> ⚠️ **Es la capa con la comprobación más débil de las ocho.** Léete la sección "Cómo se comprueba"
> antes de confiar en el checker aquí: buena parte de esta configuración vive fuera del código.

## La regla (una frase)

**Todo mensaje tiene un final: se procesa, o acaba en una dead-letter queue tras un número máximo
de entregas — nunca gira indefinidamente.**

Por qué es la regla de esta capa: un mensaje que falla siempre (un "mensaje veneno") y vuelve a la
cola es el único fallo del sistema que **empeora solo con el tiempo**. Consume un worker en cada
vuelta, se reintenta más rápido cuanto menos tarda en fallar, y acaba desplazando al trabajo
legítimo. Desde fuera no se ve un error: se ve que la cola "va lenta". Es el fallo que convierte
ocho horas de trabajo autónomo en ocho horas de un worker girando sobre el mismo mensaje.

## Implementación de referencia

`_fixtures/conforme/config/settings/base.py:57`:

```python
_dlx = Exchange("facturacion.dlx", type="direct")

CELERY_TASK_QUEUES = (
    Queue(
        "facturacion.default",
        Exchange("facturacion"),
        routing_key="default",
        queue_arguments={
            "x-queue-type": "quorum",
            "x-dead-letter-exchange": "facturacion.dlx",
            "x-delivery-limit": 5,
        },
    ),
    # pattern-exempt: be-mq-dlx — es la cola de descarte final; no reencola en ningún sitio
    Queue("facturacion.dead", _dlx, routing_key="default"),
)

CELERY_TASK_ACKS_LATE = True
CELERY_TASK_REJECT_ON_WORKER_LOST = True
CELERY_WORKER_PREFETCH_MULTIPLIER = 1
```

Las cuatro piezas y por qué van juntas:

- **`x-queue-type: quorum`** — replicada y con manejo de mensaje veneno incorporado. Las colas
  clásicas mirror están obsoletas; para trabajo que no se puede perder, la quorum es el default.
- **`x-delivery-limit`** — el contador de entregas fallidas. Al superarlo, RabbitMQ descarta el
  mensaje **o lo manda al DLX si hay uno configurado**. La doc oficial recomienda explícitamente
  configurar un DLX en colas quorum precisamente para no perderlo.
- **`x-dead-letter-exchange`** — el destino. Sin él, superar el límite significa **borrar** el
  mensaje: cambias un bucle infinito por una pérdida silenciosa, que no es mejor.
- **`prefetch_multiplier = 1`** con tasks largas: sin eso un worker reserva un lote de mensajes y
  los retiene mientras procesa el primero; si muere, todos vuelven a la vez.

**La DLQ hay que mirarla.** Una dead-letter queue que nadie consulta es un vertedero: los mensajes
están a salvo y nadie se entera de que existen. Como mínimo, una alerta sobre su profundidad —y eso
exige tener a dónde mandarla, que es `backend-observabilidad.md`.

> **El precio de no tener esta capa, medido.** En el backend de referencia no hay ninguna `Queue()`
> ni `Exchange()` declarada: sin colas quorum, sin DLX, sin `delivery-limit`, sin política. Lo que
> sí hay es **un script escrito a mano** cuyo único propósito es drenar la cola mensaje a mensaje,
> republicando todo lo que no sea la tarea que la inundó. Ese script *es* la dead-letter queue que
> no existe, escrita a posteriori y a mano por alguien a quien le tocó.

## El antipatrón que sustituye

`_fixtures/infractor/config/settings/base.py:26`:

```python
CELERY_BROKER_URL = "amqp://broker:5672//"          # además, literal en un fichero versionado
CELERY_TASK_QUEUES = (Queue("facturacion.default"),)
```

Una cola sin `x-dead-letter-exchange` ni `x-delivery-limit`. Con `acks_late=True` —que es lo que
queremos por otras razones— un mensaje que hace fallar al consumidor se re-entrega sin techo. El
día que llegue un payload que dispara una excepción determinista (un campo `None` inesperado, un
id borrado), ese mensaje se queda dentro para siempre.

## Cómo se comprueba

```bash
python3 .claude/patterns/stack/pattern_check_backend.py --rules be-mq-dlx
```

| Regla | Estado | Qué detecta (AST) |
|---|---|---|
| `be-mq-dlx` | **débil** | `Queue(...)` declarada en settings o tasks a la que le falte `x-dead-letter-exchange` **o** `x-delivery-limit` en `queue_arguments` |

La regla pide **los dos argumentos, no uno**, y esa es la única diferencia con la versión anterior.
No es celo: son las dos mitades de la misma frase. Sin `x-delivery-limit`, el mensaje veneno gira
indefinidamente; con el límite pero **sin** DLX, al superarlo RabbitMQ lo **borra** — que es cambiar
un bucle infinito por una pérdida silenciosa, y la segunda es peor porque no se ve.

**Los límites de esta comprobación, sin adornos** — es la razón de que la regla sea débil y no
activa, y de que esta capa aporte una sola regla al catálogo:

1. **RabbitMQ recomienda configurar DLX y delivery-limit por *policy*** (`rabbitmqctl set_policy`
   o la HTTP API), no por argumentos de cola — entre otras cosas porque los argumentos son
   inmutables tras declarar la cola. Una policy vive fuera del repositorio: el checker no la ve y
   marcaría como infracción una cola perfectamente configurada. Ese falso positivo es esperable, y
   por eso avisa en vez de bloquear.
2. **Muchos proyectos no declaran colas en el código**: usan la cola por defecto que Celery crea
   sola. Ahí no hay nada que el AST pueda inspeccionar.
3. Lo que de verdad importaría comprobar —que la DLQ existe, que está vigilada y que su
   profundidad no crece— **es una comprobación de runtime contra el broker**, no de código
   estático. Se puede hacer (`rabbitmqctl list_queues name messages`), pero no cabe en un hook de
   pre-push y no la he metido en el catálogo por eso.

Si el proyecto configura por policy, deja constancia en el repo para que el siguiente lo sepa:

```python
# pattern-exempt: be-mq-dlx — DLX y delivery-limit se aplican por policy en infra/rabbitmq-policies.sh
```

## Excepciones legítimas

- **La propia cola de descarte** no necesita su propio DLX: es el final del camino. Es la exención
  que usa la implementación de referencia.
- **Colas de mensajes descartables** (telemetría, pings, notificaciones de "usuario escribiendo"),
  donde perder un mensaje es preferible a guardarlo. Documéntalo: sin la nota, el siguiente lector
  no distingue "decidimos perderlo" de "se nos olvidó".
- **Proyecto que usa Redis como broker** en lugar de RabbitMQ: la regla no aplica. El checker solo
  mira llamadas a `Queue(...)`, así que no dispara sola.

## Related

- `backend-celery.md` (`acks_late`, reintentos e idempotencia — el otro lado de la misma moneda) ·
  `backend-docker-env.md` (el servicio `broker` y su healthcheck)
- Doc oficial: <https://www.rabbitmq.com/docs/quorum-queues>
