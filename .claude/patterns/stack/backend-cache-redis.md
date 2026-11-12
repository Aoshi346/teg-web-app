# Caché con Redis — patrón de casa

> **Cuándo aplicar:** al cachear cualquier cosa y al configurar `CACHES`.
> **Verificado contra la doc oficial de Django 5.2** el 2026-08-08: el backend `RedisCache` es
> nativo desde Django 4.0 (no hace falta `django-redis` para el caso normal).

## La regla (una frase)

**Toda clave de caché se construye en una función con nombre, lleva TTL explícito y tiene un sitio
identificable donde se invalida.**

Por qué el énfasis en la función: los bugs de caché casi nunca son "el dato no se guardó". Son
**"el dato viejo se sirvió"**, y su causa habitual es que quien escribe la clave y quien la borra
son dos módulos distintos que reproducen el formato de memoria. En cuanto uno de los dos cambia la
f-string, la invalidación deja de encontrar nada y falla en silencio: no hay excepción, no hay
log, solo un usuario viendo un total que no cuadra.

## Implementación de referencia

`_fixtures/conforme/apps/facturacion/services.py:38`:

```python
TTL_RESUMEN_SEGUNDOS = 300

def clave_resumen_cliente(cliente_id: str) -> str:
    """Única fuente de la clave: quien invalide no tiene que recordar el formato."""
    return f"facturacion:resumen:{cliente_id}"


def resumen_cliente(*, cliente_id: str) -> ResumenCliente:
    clave = clave_resumen_cliente(cliente_id)
    cacheado = cache.get(clave)
    if cacheado is not None:
        return ResumenCliente(**cacheado)

    resumen = ...  # el cálculo caro
    cache.set(clave, asdict(resumen), timeout=TTL_RESUMEN_SEGUNDOS)
    return resumen


# y en la operación que invalida — misma función, no una f-string paralela:
cache.delete(clave_resumen_cliente(str(factura.cliente_id)))
```

Configuración (`_fixtures/conforme/config/settings/base.py:31`):

```python
CACHES = {
    "default": {
        "BACKEND": "django.core.cache.backends.redis.RedisCache",
        "LOCATION": env("REDIS_URL"),
        "KEY_PREFIX": "facturacion",   # varios proyectos comparten este Redis
        "TIMEOUT": 300,
    }
}
```

Tres detalles:

- **`KEY_PREFIX` con el nombre del proyecto.** En este servidor conviven varios proyectos y el
  Redis se comparte. Sin prefijo, dos proyectos con una clave `resumen:42` se pisan los datos — y
  el síntoma aparece en el proyecto que no tocaste, que es el bug más caro de diagnosticar que
  existe.
- **TTL siempre, incluso invalidando.** La invalidación explícita es la ruta feliz; el TTL es la
  red de seguridad para cuando esa ruta falle. Con `timeout=None` un fallo de invalidación es
  permanente hasta que alguien vacíe Redis a mano.
- **`cache.get()` comparado con `None`, no por verdad.** Un valor cacheado legítimamente falsy
  (`0`, `[]`, `""`) haría recalcular en cada petición si compruebas `if cacheado:`. La caché
  seguiría "funcionando" y nadie notaría que no sirve para nada.

Para el patrón leer-o-calcular en un paso, la doc oficial ofrece
`cache.get_or_set(key, default, timeout)`, que el checker trata igual.

## El antipatrón que sustituye

`_fixtures/infractor/apps/facturacion/services.py:9`:

```python
def clave_resumen(cliente_id):
    return f"resumen:{cliente_id}"

def emitir(request, factura_id):
    ...
    cache.set(clave_resumen(str(factura.cliente_id)), {"n": 1}, timeout=None)   # para siempre

def resumen(cliente_id):
    return cache.get(f"resumen:{cliente_id}")     # la clave, otra vez, a mano
```

Aquí conviven los tres fallos a la vez y se refuerzan entre sí: la clave se escribe dos veces (una
con helper, otra con f-string), nunca se borra en ningún sitio, y el TTL es infinito. El resultado
es un dato que **jamás se actualiza** y para el que no existe ningún punto del código al que ir a
buscar la invalidación que falta. Y como sin `KEY_PREFIX` la clave es `resumen:<uuid>` a secas,
otro proyecto del mismo servidor puede estar escribiendo encima.

## Cómo se comprueba

```bash
python3 .claude/patterns/stack/pattern_check_backend.py --rules be-cache-ttl-infinito,\
be-cache-key-prefix,be-cache-key-helper,be-cache-sin-invalidacion
```

| Regla | Estado | Qué detecta |
|---|---|---|
| `be-cache-ttl-infinito` | activo | `cache.set(..., timeout=None)` |
| `be-cache-key-prefix` | activo | settings define `CACHES` sin `KEY_PREFIX` |
| `be-cache-key-helper` | débil | `cache.get/set/delete/add` cuya clave es una f-string escrita en el punto de uso |
| `be-cache-sin-invalidacion` | **sombra** | cruce entre ficheros: un helper de clave que aparece en `cache.set` y en ningún `cache.delete` |

La última nace en **sombra** (mide, no imprime salvo `--all`) por una razón concreta: hay cachés
puramente temporales cuya invalidación *es* el TTL y no necesitan borrado explícito. Marcarlas
sería un falso positivo legítimo. Se mide primero y se decide después con datos, que es lo que
pide el README (dominancia medida antes de fijar).

Lo que **no** se comprueba: si el TTL elegido es el adecuado para la volatilidad del dato. Eso es
criterio puro — 300 segundos puede ser conservador o temerario según qué haya dentro — y no hay
forma mecánica de juzgarlo. Queda documentado aquí y fuera del catálogo.

## Excepciones legítimas

- **Valor inmutable de verdad** (un catálogo versionado, un resultado derivado de un hash del
  contenido): cachear sin caducidad es correcto porque la clave cambia cuando cambia el dato.

```python
# pattern-exempt: be-cache-ttl-infinito — la clave incluye el hash del contenido: si cambia, cambia la clave
cache.set(f"render:{plantilla_sha}", html, timeout=None)
```

- **Locks y flags de corta vida** construidos con `cache.add(...)`: la clave se compone en el sitio
  a propósito y vive segundos. Exímela con `be-cache-key-helper` si el checker la marca.

## Related

- `backend-servicios.md` (el servicio es quien invalida, porque es quien sabe qué cambió) ·
  `backend-docker-env.md` (`maxmemory-policy` del contenedor de Redis)
- Doc oficial: <https://docs.djangoproject.com/en/5.2/topics/cache/>
