# Observabilidad — logging, errores y salud

> **Cuándo aplicar:** al montar un proyecto, antes de dejar trabajo corriendo sin nadie delante, y
> siempre que se añada un servicio nuevo (worker, beat, importador).
>
> **NO aplicar:** para métricas de negocio ni analítica de producto. Esto es *"¿está vivo y qué se
> rompió esta noche?"*, no *"¿cuántos usuarios activos hay?"*.
>
> **Relacionado:** `backend-celery.md` (los fallos que esto hace visibles) ·
> `backend-docker-env.md` (el `healthcheck` del compose consume el endpoint de aquí) ·
> `rules/verification.md` §Smoke testing.

## La regla (una frase)

**No hay autonomía sin señal de vuelta: si el sistema no puede contar lo que le pasó de madrugada,
la única observabilidad es una persona mirando.**

Es lo **primero**, no lo último. Sin esto, cualquier otra mejora del trabajo nocturno es invisible
y ni siquiera se puede verificar que funcionó — que es exactamente el fallo que este catálogo
persigue en todas las demás capas.

## La medida que lo justifica

El backend de referencia: **ningún bloque `LOGGING` en 961 líneas de settings**. Sin Sentry, sin
OpenTelemetry, sin métricas, sin endpoint de salud. Solo 20 `logging.getLogger(__name__)` sueltos
escribiendo a la configuración por defecto de Django. Lo único parecido a instrumentación era
`django-silk`, activado con `DEBUG` — que en producción es riesgo, no ayuda.

El informe que lo midió lo resumió en una frase que conviene no suavizar:

> *"la infraestructura funciona porque hay una persona mirándola."*

Y el coste concreto: cuando una tarea del beat empezó a fallar de madrugada, no hubo aviso. Hubo un
script escrito a mano para purgar la cola que se había llenado. La autopsia existía —los tracebacks
se guardaban junto al registro que falló, y eso estaba bien hecho— pero **nadie se enteraba por la
noche**.

## Las tres piezas

### 1. `LOGGING` — el rastro

```python
LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "detallado": {"format": "{asctime} {levelname} {name} {message}", "style": "{"},
    },
    "handlers": {
        "consola": {"class": "logging.StreamHandler", "formatter": "detallado"},
        "fichero": {
            "class": "logging.handlers.RotatingFileHandler",
            "filename": "/var/log/<proyecto>/app.log",
            "maxBytes": 20 * 1024 * 1024,
            "backupCount": 5,
            "formatter": "detallado",
        },
    },
    "root": {"handlers": ["consola", "fichero"], "level": "DEBUG" if DEBUG else "INFO"},
}
```

- **`RotatingFileHandler`, no `FileHandler`**: un log sin rotación llena el disco, y el disco lleno
  tira la aplicación por una razón que no aparece en el propio log.
- **El nivel cuelga de una variable que ya existe.** Subirlo para depurar un incidente no debe
  exigir tocar código ni desplegar. Y no inventes una variable nueva si `DEBUG` ya sirve: cada
  variable de entorno nueva es una fila más en `.env.example` que alguien tendrá que documentar
  (`be-env-documentado` lo exige, con razón).
- **`disable_existing_loggers: False`**: sin esto, los loggers de las librerías que ya se hayan
  importado se apagan en silencio.

### 2. El error, buscándote a ti (Sentry o equivalente)

Un log en un fichero es una autopsia; sirve por la mañana. Lo que hace falta de madrugada es que el
fallo **te busque**: `SENTRY_DSN` documentado en `.env.example`, vacío por defecto, y la
integración inicializada cuando tiene valor.

> ⚠️ **Esta pieza NO tiene comprobación mecánica, y hay que decirlo.** No hay forma honesta de que
> un checker exija un vendor concreto: Sentry, GlitchTip, Rollbar o un handler propio a un webhook
> son todos respuestas válidas, y una regla que buscara la cadena `sentry` premiaría poner la
> dependencia sin configurarla. Queda como **aviso documentado** (README, regla 3: si no se puede
> comprobar, se dice, no se disfraza de regla). Lo que sí se comprueba es el `LOGGING` de al lado,
> que es el prerrequisito.

### 3. `/healthz` — que el sistema se pueda vigilar solo

```python
def healthz(request):
    return JsonResponse({"ok": True})

urlpatterns = [path("healthz/", healthz, name="healthz"), ...]
```

Sin auth y **sin tocar la base de datos**. Responde a una sola pregunta: *¿el proceso está vivo?*
Lo consultan el balanceador, el `condition: service_healthy` del compose
(`backend-docker-env.md`) y la alerta — y ninguno de los tres puede hacerlo si no existe.

Si además quieres saber si la base responde, eso es **otro** endpoint (`readyz`) y otra pregunta.
Mezclarlos tiene una consecuencia mala y poco obvia: un hipo de la base hace que el orquestador
mate y reinicie el proceso web, que estaba perfectamente sano.

## Cómo se comprueba

```bash
python3 .claude/patterns/stack/pattern_check_backend.py --rules be-obs-logging,be-obs-healthcheck
```

| Regla | Estado | Qué detecta |
|---|---|---|
| `be-obs-logging` | activo | settings sin bloque `LOGGING` |
| `be-obs-healthcheck` | débil | ningún `path()`/`re_path()` del proyecto con una ruta `health`/`healthz`/`readyz`/`livez`/`status` |

`be-obs-healthcheck` **mira las rutas declaradas, no el texto del fichero**. Es deliberado: un
comentario que hable del healthcheck haría creer al checker que existe, y esta regla sirve justo
para el proyecto donde se habló de él y no se puso.

Es **débil** por dos motivos: hay proyectos que exponen la salud fuera de Django (en nginx, o en el
propio orquestador), y hay despliegues sin `urls.py` visible para el checker. Bloquear ahí marcaría
proyectos correctos.

## Excepciones legítimas

- **Logging gestionado fuera de Django** (systemd + journald, o un sidecar que recoge stdout): sigue
  necesitando el bloque, aunque solo tenga el handler de consola con formato — es lo que hace que la
  línea sea parseable. Si de verdad no aplica:
  `# pattern-exempt: be-obs-logging — el formato lo impone el recolector de logs de la plataforma`.
- **Servicio sin HTTP** (un worker puro): no hay ruta que exponer; su salud se mide por la cola.
- **Proyecto detrás de un healthcheck de infraestructura**:
  `# pattern-exempt: be-obs-healthcheck — /healthz lo sirve nginx desde infra/nginx.conf`.

## Lo que este documento NO cubre

Métricas (Prometheus/OpenTelemetry), trazas distribuidas y alertas con umbral. Son el escalón
siguiente y son valiosos, pero un catálogo que los exija en un proyecto que aún no tiene ni
`LOGGING` está pidiendo el tejado antes que los cimientos. Cuando entren, entrarán con su
comprobación o no entrarán.

## Related

- `backend-celery.md` (los fallos silenciosos y diferidos que esto hace visibles) ·
  `backend-mensajeria-rabbitmq.md` (la DLQ que hay que **mirar**: sin alerta es un vertedero)
- `backend-docker-env.md` (`condition: service_healthy` consume el endpoint de aquí) ·
  `rules/verification.md` §Smoke testing (el primer filtro barato tras un deploy)
- skill `harness-telemetry` — observabilidad **del agente**, que es otra cosa y va aparte
