# Tareas Celery — patrón de casa

> **Cuándo aplicar:** al escribir o tocar cualquier `@shared_task`, y al configurar Celery en
> settings. **Verificado contra la doc oficial** (docs.celeryq.dev, guía de tasks) el 2026-08-08.

## La regla (una frase)

**Una task recibe identificadores, no objetos; se puede ejecutar dos veces sin daño; tiene techo
de tiempo y política de reintentos explícita — y se encola después del COMMIT, nunca dentro de la
transacción.**

Por qué importa más que en otras capas: los fallos de Celery son **silenciosos y diferidos**. Una
vista rota da un 500 que alguien ve; una task rota se pierde en un log a las 4 de la mañana y el
efecto aparece días después como "faltan datos". Es exactamente el escenario de dejar trabajo
corriendo por la noche, así que aquí el patrón no es higiene: es la diferencia entre despertarse
con trabajo hecho o con trabajo a medias que nadie sabe reconstruir.

## Implementación de referencia

`_fixtures/conforme/apps/facturacion/tasks.py`:

```python
@shared_task(
    autoretry_for=(RequestException,),
    retry_backoff=True,
    retry_backoff_max=600,
    max_retries=5,
    acks_late=True,
    soft_time_limit=60,
    time_limit=90,
)
def enviar_factura_por_email(factura_id: str) -> str:
    factura = Factura.objects.filter(pk=factura_id).first()
    if factura is None:
        logger.warning("factura %s ya no existe; nada que enviar", factura_id)
        return "inexistente"
    if factura.enviada_en is not None:
        return "ya-enviada"

    try:
        requests.post("https://api.emailer.example/send", json={...}, timeout=10)
    except SoftTimeLimitExceeded:
        logger.error("envío de %s abortado por soft_time_limit", factura_id)
        raise

    # UPDATE condicional: si otra ejecución llegó antes, esta no pisa su marca de tiempo.
    Factura.objects.filter(pk=factura.pk, enviada_en__isnull=True).update(enviada_en=timezone.now())
    return "enviada"
```

El encolado, desde el servicio (`_fixtures/conforme/apps/facturacion/services.py:58`):

```python
transaction.on_commit(lambda: enviar_factura_por_email.delay(str(factura.pk)))
```

Y la configuración que lo sostiene (`_fixtures/conforme/config/settings/base.py:41`):

```python
CELERY_TASK_SERIALIZER = "json"
CELERY_RESULT_SERIALIZER = "json"
CELERY_ACCEPT_CONTENT = ["json"]
CELERY_TASK_SOFT_TIME_LIMIT = 300   # excepción capturable: da tiempo a cerrar limpio
CELERY_TASK_TIME_LIMIT = 360        # SIGKILL: el techo duro
CELERY_TASK_ACKS_LATE = True
CELERY_TASK_REJECT_ON_WORKER_LOST = True
CELERY_WORKER_PREFETCH_MULTIPLIER = 1
```

Tres decisiones que conviene entender antes de copiarlas:

- **`task_serializer="json"` hace cumplir la regla de "no pases objetos"** por sí solo: un modelo
  de Django no es serializable a JSON, así que el intento falla *al encolar*, en desarrollo, con
  traza clara — en vez de fallar en producción con datos rancios. Es la razón por la que esta
  regla es de configuración y no de estilo: convierte una convención en un error de ejecución.
  De regalo cierra la ejecución de código arbitrario que permite `pickle` sobre la cola.
- **`soft_time_limit` < `time_limit`**: el blando lanza `SoftTimeLimitExceeded` dentro de la task
  (puedes cerrar ficheros, marcar estado, reintentar); el duro mata el proceso. Con solo el duro,
  la task muere sin dejar rastro de dónde iba.
- **`acks_late=True` + `reject_on_worker_lost=True`**: la task se confirma al terminar, no al
  recibirla, así que si el worker muere a mitad se re-entrega. Eso **exige** idempotencia — por eso
  van juntos y por eso hay una regla que pide el test.

Valores por defecto verificados en la doc oficial: `max_retries` = 3, `retry_backoff_max` = 600 s,
`retry_jitter` = True.

## El antipatrón que sustituye

`_fixtures/infractor/apps/facturacion/tasks.py` y `views.py:24`:

```python
@shared_task                                    # ni retries, ni límites de tiempo
def enviar_factura_por_email(factura_id):
    factura = Factura.objects.get(pk=factura_id)          # DoesNotExist → excepción y adiós
    requests.post("https://api.emailer.example/send", ...)  # un timeout la pierde para siempre

@shared_task(acks_late=True)                    # se re-entrega… y nadie ha probado que sea inocuo
def recalcular_totales_cliente(cliente_id):
    ...

# en la vista:
with transaction.atomic():
    factura.save()
    enviar_factura_por_email.delay(str(factura.pk))   # ← antes del COMMIT
```

Los cuatro daños, concretos:

1. **`.delay()` dentro de `atomic`** es una carrera real, no teórica: el broker entrega el mensaje
   en milisegundos y el COMMIT puede tardar más. El worker hace `SELECT` y no encuentra la fila.
   Peor: si la transacción termina en rollback, el correo ya salió y no hay factura.
2. **`.get()` en vez de `.first()`**: la fila puede haber desaparecido entre encolar y ejecutar.
   Con `.get()` eso es una excepción; con `.first()` es un caso previsto.
3. **Sin `autoretry_for`**, un 503 puntual del proveedor pierde el envío definitivamente.
4. **`acks_late` sin idempotencia** es la peor combinación posible: garantiza la re-entrega de una
   task que no tolera re-entregarse. Se cobra dos veces, se manda el correo dos veces.

## Cómo se comprueba

```bash
python3 .claude/patterns/stack/pattern_check_backend.py --rules be-celery-delay-en-transaccion,\
be-celery-serializer-json,be-celery-timeouts,be-celery-retry-io,be-celery-ackslate-idempotente
```

| Regla | Estado | Qué detecta |
|---|---|---|
| `be-celery-delay-en-transaccion` | activo | AST: `.delay()`/`.apply_async()` dentro de `with transaction.atomic()` o de una función `@transaction.atomic`, **salvo** si está bajo `transaction.on_commit(...)` |
| `be-celery-serializer-json` | activo | settings menciona Celery y no fija `task_serializer` |
| `be-celery-timeouts` | activo | settings sin `task_time_limit` / `task_soft_time_limit` |
| `be-celery-retry-io` | **activo** (era débil) | task que llama a `requests`/`httpx`/`boto3`/`stripe`/`openai` y no declara `autoretry_for` |
| `be-http-timeout` | activo | `requests.<verbo>(...)` / `httpx.<verbo>(...)` sin `timeout=`, en cualquier fichero |
| `be-celery-ackslate-idempotente` | débil | task con `acks_late=True` cuyo nombre no aparece en ningún fichero de test |

La de `acks_late` merece una nota: **la comprobación es "existe un test que la nombra"**, no "la
task es idempotente" — eso último no lo puede decidir una máquina. Es un proxy deliberado y algo
tosco, pero fuerza a que alguien haya *pensado* el caso de la doble ejecución y lo haya dejado
escrito. Un catálogo con un proxy honesto vale más que uno con una regla que nadie puede ejecutar.

### El timeout y el reintento: la pareja que sostiene la noche

Estas dos son las dos mitades del **fallo dominante** medido en un backend Django en producción, y
las dos han cambiado de peso a raíz de esa medida:

| Medida (backend real, 28 tareas · 39 llamadas HTTP) | Valor |
|---|---:|
| Llamadas `requests.*` **sin `timeout=`** | **37 de 39** |
| Tareas con `autoretry_for` / `max_retries` / `self.retry` | **0 de 28** |
| `.delay()` dentro de `atomic()` — el caso que ya era `activo` | **1 de 31** |

Los dos cambios que salen de ahí, y conviene decirlos explícitamente porque **suben la fricción**:

1. **`be-http-timeout` es nueva.** No existía en el catálogo, y es —con diferencia— la comprobación
   de mayor valor para el trabajo desatendido. El default de `requests` es esperar **para siempre**.
   Un servicio que se *degrada* (no que caiga: que tarde) retiene el worker indefinidamente; si algo
   encola cada pocos segundos, a las 7:00 hay miles de tareas apiladas. Y el síntoma que se ve
   desde fuera no es un error: es que "la cola va lenta".
2. **`be-celery-retry-io` sube de `débil` a `activo`.** Estaba avisando de un fallo que se daba en
   el 100% de las tareas, mientras el que bloqueaba se daba en el 3% de los encolados. La prueba de
   que el orden estaba invertido no es un argumento: es que en ese repositorio existe **un script
   escrito a mano para purgar la cola** que este fallo produjo. Ese script *es* la dead-letter queue
   que no había.

**Alcance honesto de `be-http-timeout`:** solo caza llamadas con el módulo delante
(`requests.post(...)`, `httpx.get(...)`). Un `session.get(...)` sobre una `Session` configurada con
timeout por defecto **no se marca** —sería un falso positivo— y, en el otro sentido, tampoco se
caza si no lo tiene. Es el precio de que esta regla no tenga falsos positivos interesantes, y
por eso puede ser `activo` desde el primer día.

### Dónde escribe la task su resultado

El patrón habla de argumentos y de reintentos, pero no del **artefacto**, y ahí hay una decisión
estructural escondida. En la referencia, 8 tareas escriben su Excel en `/tmp/` y una vista sirve
`/tmp/` entero por URL. Dos consecuencias: cualquier fichero de `/tmp` es descargable por cualquier
usuario autenticado, y —la que de verdad ata— **el worker y el proceso web quedan obligados a
compartir sistema de ficheros**, lo que prohíbe de hecho contenedores y escalado horizontal.

**La regla:** el resultado de una task va al **storage configurado** (`default_storage`, el bucket,
el `MEDIA_ROOT`), nunca al disco local del worker. No tiene comprobación en el catálogo —distinguir
un `/tmp` legítimo de uno estructural exige contexto— así que queda como **aviso documentado**.

## Excepciones legítimas

- **Task sin I/O de red** (un cálculo, una limpieza local): no necesita `autoretry_for`; el checker
  solo lo pide cuando detecta la llamada de red.
- **Llamada saliente cuyo timeout lo fija la sesión** (`Session(timeout=...)`, un cliente de SDK
  configurado): `# pattern-exempt: be-http-timeout — el timeout lo pone el cliente en clientes.py`.
- **Descarga larga a propósito** (un fichero grande): sigue llevando `timeout=`, generoso. Un
  número alto es una decisión; la ausencia es un olvido, y solo una de las dos se puede revisar.
- **Task deliberadamente no idempotente** que por eso mismo usa `acks_late=False` (se confirma al
  recibirla; si el worker muere, se pierde y eso es lo preferible). Es una decisión válida:
  perder un envío puede ser mejor que duplicar un cobro.
- **Encolar fuera de transacción a propósito** — p. ej. una task de auditoría que debe registrarse
  incluso si la operación acaba en rollback:

```python
# pattern-exempt: be-celery-delay-en-transaccion — auditoría: queremos el registro incluso si hay rollback
registrar_intento.delay(usuario_id, accion)
```

## Related

- `backend-servicios.md` (quién encola: el servicio, no la vista) ·
  `backend-mensajeria-rabbitmq.md` (dónde acaban las que fallan siempre) ·
  `backend-docker-env.md` (`--max-tasks-per-child` y el worker en compose)
- Doc oficial: <https://docs.celeryq.dev/en/stable/userguide/tasks.html> ·
  `transaction.on_commit`: <https://docs.djangoproject.com/en/5.2/topics/db/transactions/>
