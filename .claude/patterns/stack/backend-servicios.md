# Servicios — dónde vive la lógica de negocio · patrón de casa

> **Cuándo aplicar:** siempre que una operación haga algo más que leer y devolver: cambiar de
> estado, cobrar, enviar, calcular con reglas, coordinar varios modelos.
> **Capa más importante del backend.** Si esta se coloca mal, las otras siete no la salvan.

> ⚠️ **Esto es una regla NUEVA, no la costumbre documentada** (TPL-15, pendiente de confirmación
> del Usuario). Se verificó: la palabra «servicio» / «lógica de negocio» **no aparecía en ninguna**
> de las 3 skills `django-orm-*` ni en los agentes `arquitecto-apis` / `especialista-database`. El
> estilo de facto ponía la orquestación en la vista (`arquitecto-apis` tenía un `# Lógica
> personalizada` dentro de un `@action`) y las reglas en el serializer. Esa contradicción **ya no
> existe**: `arquitecto-apis` se retiró el 2026-08-22 (`_archive/2026-10-19/agents/_deprecated-README.md`, item
> `CAP-ARQUITECTOA`) y su ejemplo con él; `especialista-database` se retiró el mismo día
> (`_archive/2026-08-22/README.md`, item `EJE-1`). Los dos nombres se conservan arriba porque son
> **la medición que justificó esta regla**, no enlaces vivos. El
> precedente interno que la justifica son las funciones transaccionales sueltas que ya existían
> (`create_lead_with_appointment`, `build_property_query`): la capa las ordena, no las inventa.

## La regla (una frase)

**La lógica de negocio vive en funciones que no saben que existe HTTP** — no importan DRF, no
reciben `request` y no devuelven `Response`.

> **El NOMBRE del fichero no es la regla; es el default de proyecto nuevo (EVO-4).** En un proyecto
> que arranca de cero, esa capa se llama `services.py` y ya está. En uno que ya existe, se llama
> como se llame allí — y en los backends Django reales suele llamarse `utils.py`. El caso medido:
> 28-30 ficheros `utils.py`, **11.385 líneas**, con funciones que ya tienen **cinco tipos de
> invocador** (HTTP, Celery, `manage.py`, informes, inlines del CRUD). Eso *es* la capa de
> servicios, cumpliendo exactamente lo que este documento pide. Renombrar 30 ficheros no arregla
> ninguno de los tres sitios donde la lógica sí está atrapada; solo genera un diff enorme y la
> sensación de haber hecho algo.
>
> **Cómo se comprueba en un proyecto existente:** declara la capa en la cabecera del fichero y el
> checker le aplica la misma regla, sin renombrar nada.
>
> ```python
> """Expedientes — lógica de negocio.
> # pattern-layer: services
> """
> ```
>
> Verificado en `_fixtures/infractor-plano/expedientes/utils.py`: con el marcador,
> `be-svc-sin-drf` dispara allí igual que en un `services.py`. Sin él, ese fichero pasaría en
> silencio — que es lo que ocurría antes de EVO-4 y por eso la degradación del nombre venía
> acompañada de un mecanismo, no de un párrafo.

Por qué esta y no otra: la prueba de fuego no es la elegancia, es *quién más puede llamar a esto*.
Una regla de negocio metida en una vista solo se puede ejecutar con una petición HTTP entrante. La
task nocturna no la alcanza, el comando de `manage.py` no la alcanza, y el test necesita fabricar
un request falso para tocarla. En cuanto quieres dejar trabajo corriendo sin nadie delante, esa
lógica es inaccesible y se acaba duplicando — y entonces existen dos versiones de la misma regla
que divergen en el primer cambio. Ese es el error que más caro sale de todo el backend.

## Implementación de referencia

`_fixtures/conforme/apps/facturacion/services.py` (fichero completo, ejecutable y verificado):

```python
class ErrorDeFacturacion(Exception):
    """Base del dominio. La vista decide qué código HTTP significa cada subclase."""

class FacturaNoEmitible(ErrorDeFacturacion):
    ...

@transaction.atomic
def emitir_factura(*, factura_id: str, emitido_por_id: str) -> Factura:
    factura = Factura.objects.select_for_update().get(pk=factura_id)
    if factura.estado != Factura.Estado.BORRADOR:
        raise FacturaNoEmitible(f"la factura {factura.numero} ya está en estado {factura.estado}")

    factura.estado = Factura.Estado.EMITIDA
    factura.emitida_en = timezone.now()
    factura.save(update_fields=["estado", "emitida_en", "actualizada_en"])

    cache.delete(clave_resumen_cliente(str(factura.cliente_id)))
    transaction.on_commit(lambda: enviar_factura_por_email.delay(str(factura.pk)))
    return factura
```

Y la vista que lo consume (`_fixtures/conforme/apps/facturacion/views.py:33`) se queda en traducir:

```python
@action(detail=True, methods=["post"])
def emitir(self, request, pk=None):
    try:
        factura = emitir_factura(factura_id=pk, emitido_por_id=str(request.user.pk))
    except FacturaNoEmitible as exc:
        raise ValidationError(str(exc)) from exc
    return Response(FacturaSerializer(factura).data, status=status.HTTP_200_OK)
```

Cuatro detalles que no son casuales:

- **Argumentos keyword-only** (`*,`): `emitir_factura(a, b)` con dos ids del mismo tipo se puede
  invertir sin que nada se queje. Con `*` la llamada no compila si te equivocas de nombre.
- **Excepciones de dominio, no HTTP**: el servicio dice *"esto no se puede emitir"*; que eso sea un
  400 o un 409 es una decisión de la capa web, y cambiarla no debe tocar el dominio.
- **`select_for_update()`** dentro de `atomic`: dos peticiones simultáneas sobre la misma factura
  se serializan; sin él, las dos leen "borrador" y las dos emiten.
- **`update_fields`**: el `UPDATE` toca tres columnas en vez de la fila entera, y no pisa lo que
  otra transacción haya escrito en el resto.

## Cuando el servicio es una familia: clase base con contrato y puente sin `request` (REF-4)

Una función suelta basta para una operación. Cuando aparece una **familia** de operaciones con la
misma forma —cuarenta informes, veinte importadores, quince exportaciones— hace falta un contrato
explícito, y este documento planteaba el problema sin dar la forma. La respuesta viene de un
backend real donde ~40 informes de 19 apps heredan de una misma base, y donde el problema que aquí
describimos está resuelto **a propósito y con un comentario que lo dice**.

```python
class Informe:
    """Base de la familia. El contrato son estos cuatro métodos, y nada más."""

    plantilla: str = ""

    def __init__(self, *, usuario, **parametros):
        self.usuario = usuario          # el USUARIO, no el request
        self.parametros = parametros

    def puede_acceder(self) -> bool: ...
    def contexto(self) -> dict: ...
    def generar(self) -> bytes: ...

    @classmethod
    def contexto_sin_peticion(cls, *, usuario_id: int, **parametros) -> dict:
        """El puente: mismo informe, invocado desde una task o un comando.

        Existe porque la alternativa que vimos en el repositorio de referencia era fabricar un
        `MockRequest` dentro de la tarea para poder reutilizar el código de las vistas. Eso es
        pagar el acoplamiento con un doble falso: el día que el código toque un atributo del
        request que el doble no tiene, falla en producción y en horario nocturno.
        """
        return cls(usuario=Usuario.objects.get(pk=usuario_id), **parametros).contexto()
```

Tres decisiones y por qué:

- **La base recibe `usuario`, no `request`.** Es la misma regla de arriba aplicada a una clase: en
  cuanto el constructor pide un `request`, la familia entera queda atada al ciclo HTTP.
- **El puente es explícito y `classmethod`.** No es un `if request is None` repartido por el
  cuerpo: es una entrada declarada, con nombre, que dice "esto también se invoca sin HTTP". Que
  exista es la señal de que alguien pensó en la task antes de que hiciera falta.
- **El contrato es corto.** Cuatro métodos que toda la familia implementa. Una base con veinte
  ganchos no es un contrato, es un framework — y entonces vuelve el problema que
  `README.md` §"Qué NO copiar" describe con el framework CRUD de la referencia.

> **Esto NO tiene comprobación propia, y se dice a propósito.** Que una clase base "tenga un
> contrato explícito" no es mecánicamente verificable sin inventar una heurística que marcaría
> cualquier jerarquía. Lo que **sí** se comprueba es la mitad que importa y ya está cubierta:
> `be-svc-sin-drf` dispara si la base importa HTTP o si algún método recibe `request`. La forma es
> un patrón documentado; la sustancia tiene gate.

## El antipatrón que sustituye

`_fixtures/infractor/apps/facturacion/views.py:20` — la misma operación, dentro de la vista:

```python
@action(detail=True, methods=["post"])
def emitir(self, request, pk=None):
    factura = self.get_object()
    if factura.estado != "borrador":
        return Response({"error": "ya emitida"}, status=400)
    with transaction.atomic():
        factura.estado = "emitida"
        factura.save()
        enviar_factura_por_email.delay(str(factura.pk))
    return Response(FacturaSerializer(factura).data)
```

Qué duele exactamente, y no en abstracto:

1. **No hay forma de emitir una factura sin una petición HTTP.** El día que haya que emitir las
   facturas del mes en un cron, este código no sirve y se reescribe la regla en otro sitio.
2. **No hay bloqueo**: sin `select_for_update`, dos clics rápidos emiten dos veces.
3. **`.delay()` dentro de `atomic`**: el worker puede coger la tarea antes del COMMIT y no
   encontrar la fila — o mandar el correo de una factura cuya transacción acabó en rollback. Ver
   `backend-celery.md`.
4. **Testearlo requiere el ciclo HTTP entero** (cliente, autenticación, routing) para verificar una
   regla de tres líneas.

Y su reverso, `_fixtures/infractor/apps/facturacion/services.py:16` — un "servicio" que importó DRF:
tiene el nombre correcto y el mismo problema, porque `raise ValidationError` y `return Response`
lo atan al ciclo HTTP igual que si viviera en la vista. **El fichero llamarse `services.py` no es
lo que lo hace un servicio.**

## Cómo se comprueba

```bash
python3 .claude/patterns/stack/pattern_check_backend.py            # ficheros cambiados
python3 .claude/patterns/stack/pattern_check_backend.py --rules be-svc-sin-drf,be-svc-escritura-en-vista
```

| Regla | Estado | Qué detecta (AST) |
|---|---|---|
| `be-svc-sin-drf` | activo | La capa de servicio importa `rest_framework` / `django.http` / `django.shortcuts`, o una función recibe `request`. **Qué cuenta como capa de servicio:** `services.py`, `service.py`, `use_cases.py`, `selectors.py` (defaults) o cualquier fichero con `# pattern-layer: services` en la cabecera |
| `be-svc-escritura-en-vista` | activo | `save/delete/create/update/bulk_*/get_or_create` dentro de una clase `*ViewSet`/`*APIView`, salvo `serializer.save()` y hooks `perform_*` de una sola línea |

Lo que el checker **no** puede decidir es si una función que ya está en la capa de servicio
contiene *la* regla correcta — eso es criterio, y es el trabajo de Rita (`rita-pattern-keeper`) con
los precedentes de arriba. La capa determinista solo garantiza que la lógica **no esté donde no
puede reutilizarse**; es un límite honesto, no un descuido.

Segundo límite, del mismo tipo: **`be-svc-escritura-en-vista` solo mira clases `*ViewSet`/`*APIView`.**
En una vista Django clásica (función o CBV) no dispara, así que en el arquetipo server-rendered
(`backend-formularios-django.md`) el principio sigue vigente pero sin comprobación que lo respalde.
Ahí la vía sancionada equivalente a `serializer.save()` es `form.save()`, y todo lo que sea una
regla de negocio baja igualmente a la capa de servicio.

Tercer hueco, y este **sí** tiene ahora quien lo mire: la lógica de negocio escondida dentro de
`signals.py`. `be-svc-sin-drf` verifica la higiene de una capa que existe; no detecta que la capa
**no** exista y que la función viva en un receiver, inalcanzable fuera del `post_save`. Eso lo
cubre `be-sig-logica-de-negocio` (`backend-signals.md`), y en el backend medido era el hallazgo con
mejor relación valor/coste de toda esta capa: 9 funciones de servicio atrapadas.

## Excepciones legítimas

- **CRUD puro sin reglas**: si la operación es exactamente "guarda lo que llega validado", el
  `serializer.save()` del `perform_create` es suficiente y meter un servicio de una línea es ruido.
  El checker ya lo permite: no marca `serializer.save()` ni los `perform_*` de una sentencia.
- **Endpoints públicos de solo lectura** (catálogos, healthchecks): no hay estado que proteger.
- **Un servicio que necesita el `request` de verdad** — típicamente para IP o cabeceras en una
  auditoría. Pásale el dato, no el objeto (`ip: str`, no `request`). Si aun así hace falta:

```python
# pattern-exempt: be-svc-sin-drf — la firma antifraude necesita la cabecera cruda del proveedor
def verificar_webhook(*, request) -> bool:
    ...
```

## Related

- `backend-vistas.md` (qué le queda a la vista) · `backend-celery.md` (`on_commit`) ·
  `backend-serializers.md` (por qué la validación tampoco es el sitio)
- `backend-formularios-django.md` — el arquetipo server-rendered: allí la puerta de entrada es el
  formulario, no el serializer, y esta capa se llama casi siempre `utils.py`
- `README.md` §"Los cuatro defaults que NO son reglas" — por qué el nombre del fichero se degradó
- `rita-pattern-keeper` — juzga los candidatos que emite el checker; nunca busca ella (regla R-1)
