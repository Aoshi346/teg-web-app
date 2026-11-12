# `mocks/` — simuladores de los canales externos, con su propia pantalla

> **Cuándo aplicar:** en cuanto el producto hable con **algo de fuera** que no controlamos: correo,
> WhatsApp, una pasarela de pago, un CRM, un banco, un modelo de IA de terceros, un webhook entrante.
> Define **qué es un simulador aceptable**, dónde vive, qué pantalla lleva, y el **registro** que
> hace que el de este proyecto sirva en el siguiente.
>
> **NO aplicar:** para simular NUESTRO propio backend mientras aún no existe — eso es MSW dentro del
> frontend (`frontend-nueva-pantalla.md` ⑩, y el modo `--mockup` de `nueva-pantalla`) · para los
> datos de prueba de un test unitario (`tests.md`) · para decidir SI la fuente externa se puede leer,
> que es el Gate E de `rules/plan-gates.md` y va **antes** que esto.
>
> **Relacionado:** `rules/plan-gates.md` §Gate E (¿se puede leer esa fuente?) ·
> `skills/webhook-multi-tenant-validation` (la entrada, con firma y anti-replay) ·
> `rules/api-http-contract.md` (el contrato que el simulador debe imitar) ·
> `rules/verification.md` §E2E-4 (*"el E2E no debe salir a internet"*) y §Smoke testing.

---

## 1. El problema, y por qué un `Mock()` no basta

Un producto que habla con cuatro sistemas de fuera tiene cuatro formas de fallar que **no se pueden
provocar cuando quieres**: el banco que devuelve un 500 el día 30, el WhatsApp que entrega el mensaje
dos veces, el correo que rebota, la pasarela que tarda doce segundos. En producción aparecen solos;
en desarrollo, nunca — hasta que aparecen en producción.

Lo que se hace normalmente es parchear la función en el test (`unittest.mock`), y eso tiene tres
límites que se pagan siempre:

| El parche en el test | El simulador |
|---|---|
| Prueba **tu** código contra **tu** idea de la API | Prueba tu código contra **la forma real** de la API |
| No existe fuera del test: no puedes abrir la app y usarla | La app funciona entera, sin internet |
| Nadie ve qué se envió | **Se ve en una pantalla**: qué salió, qué entró, qué se reintentó |

**La regla que lo define todo:** el simulador **imita la API, no la sustituye**. Mismas rutas, mismos
verbos, mismos códigos de estado, mismos nombres de campo, mismos errores. Si para usarlo hay que
cambiar una línea del código de producción que no sea la URL base, el simulador está mal hecho.

---

## 2. Dónde vive y qué forma tiene

```
mocks/
├── README.md              qué hay aquí, cómo se levanta, y el REGISTRO (§4)
├── <canal>/               uno por sistema externo: correo · whatsapp · pagos · crm …
│   ├── api.py             las rutas, imitando la API real 1:1
│   ├── estado.py          lo que ha pasado: enviados, recibidos, reintentos
│   ├── panel.html         la pantalla mínima (§3)
│   ├── escenarios.json    los fallos que sabe provocar (§5)
│   └── CONTRATO.md        qué versión de la API imita, qué cubre y QUÉ NO
└── docker-compose.yml     todos, cada uno en su puerto, en 127.0.0.1
```

**Una sola variable cambia entre real y simulado**, y vive en el entorno, nunca en el código:

```python
WHATSAPP_BASE_URL = os.environ.get("WHATSAPP_BASE_URL", "https://graph.facebook.com/v26.0")
#                    en desarrollo: http://127.0.0.1:8092
```

⚠️ **`--bind 127.0.0.1` siempre.** Un simulador es un servicio sin autenticación que acepta lo que le
eches: publicado en `0.0.0.0` es una puerta abierta con el nombre de tu cliente encima
(`rules/security.md` §puertos). Y en Docker, `ports: ["127.0.0.1:8092:8092"]` — un puerto publicado
por Docker **se salta el firewall del host**.

---

## 3. La pantalla, que es la mitad del valor

Sin pantalla, un simulador es un mock con más pasos. Con ella, se ve **lo que pasó de verdad**, y eso
es lo que convierte una hora de depuración en dos minutos. Lo mínimo:

| Panel | Qué muestra |
|---|---|
| **Lo que salió** | Cada llamada que hizo el producto: hora, ruta, cuerpo, y qué se respondió |
| **Lo que entró** | Webhooks o respuestas que el simulador devolvió, con su cuerpo íntegro |
| **Lo que se reintentó** | El caso que más cuesta ver: la misma intención enviada dos veces, y si se deduplicó |
| **El interruptor de escenarios** | Botones para forzar el fallo: 500, timeout, respuesta duplicada, rechazo |

Se sirve en el mismo puerto del simulador, en `/panel`, y es **un HTML autocontenido**
(`rules/html-output.md`). Sin build, sin framework, sin CDN: se abre y funciona.

> **Y lo que hace que esto valga de verdad:** el panel enseña *lo que se reintentó*. Es el fallo que
> nunca se ve en desarrollo y el que más caro sale — el cobro duplicado, el correo enviado dos veces.
> `rules/api-http-contract.md` §5 exige idempotencia; aquí es donde se **comprueba** que existe.

---

## 4. El registro — para que el siguiente proyecto no empiece de cero

**Petición del Usuario (2026-09-12):** *«el proyecto tiene que ir guardando en algún lado cuáles son
las APIs que va desarrollando, para que luego se pueda reutilizar el código»*.

Cada proyecto mantiene su tabla en `mocks/README.md`:

```markdown
| Canal | API que imita | Versión | Cubre | NO cubre | Reutilizable |
|---|---|---|---|---|---|
| whatsapp | WhatsApp Cloud API | v26.0 | envío de plantilla, recepción de webhook, estados de entrega | mensajes interactivos, catálogos | sí |
| correo   | SMTP + IMAP        | —     | envío, rebote, lectura de bandeja | adjuntos > 10 MB | sí |
| pagos    | Stripe             | 2026-10-28.endive | cobro, reembolso, webhook de éxito y de fallo | suscripciones | parcial |
```

Las versiones del ejemplo se contrastaron el 31-10-2026 (`README.md` §Mantenimiento: una versión se
verifica antes de escribirla). La tabla de la Graph API (developers.facebook.com/docs/graph-api/changelog)
da **v26.0** como la última (29-07-2026) y **v21.0, la que había aquí, deja de estar disponible el
21-01-2027**; Stripe (docs.stripe.com/upgrades) usa **2026-10-28.endive** en sus ejemplos. Son un
ejemplo de la forma de la tabla: el `CONTRATO.md` de cada simulador lleva la versión que de verdad
imita, con su fecha.

**Y sube al template.** Un simulador que ha funcionado en un proyecto es material de
`examples/mocks/<canal>/` (`rules/self-improvement-loop.md`): se cosecha al cerrar el proyecto, con
su `CONTRATO.md`, y el siguiente que necesite ese canal empieza con él en vez de con una hoja en
blanco. La columna **Reutilizable** es la que dice si ya está listo para eso o si está atado a este
cliente.

> **El límite honesto:** una API de terceros cambia sin avisarte. Un simulador de hace un año imita
> una API que ya no existe, y **pasar sus tests no demuestra nada** sobre la de hoy. Por eso el
> `CONTRATO.md` lleva la versión y la fecha, y por eso el Gate E de `plan-gates.md` —una llamada real
> contra la API de verdad— sigue siendo obligatorio antes de fiarse: el simulador sustituye a la API
> en los tests, **nunca en la comprobación de que la API sigue siendo así**.

---

## 5. Los escenarios: que el fallo se pueda provocar cuando quieras

`escenarios.json` declara los modos de fallo que el simulador sabe imitar. Mínimo, y estos cuatro no
son opcionales porque son los que de verdad pasan:

```json
{
  "feliz":       {"descripcion": "responde como debe"},
  "caido":       {"http": 503, "descripcion": "el servicio no está"},
  "lento":       {"retraso_s": 15, "descripcion": "tarda más que tu timeout"},
  "duplicado":   {"descripcion": "entrega el mismo webhook dos veces"},
  "rechazo":     {"http": 422, "cuerpo": {"error": "..."}, "descripcion": "lo rechaza con su formato real de error"}
}
```

**El de `lento` es el que más gente se salta y el que más cuesta:** es el que demuestra si tus
llamadas llevan `timeout` (`rules/api-http-contract.md`). Sin él, un servicio colgado aparca un
worker indefinidamente y lo descubres en producción.

---

## 6. El conmutador, la puerta de averías y la calibración — lo que funcionó en los proyectos

§1-§5 dicen qué es un simulador; esto es cómo se ha montado bien en los derivados. Cada punto cita
su implementación de referencia, para leerla antes de escribir la tuya.

### 6.1 `EXTERNAL_MODE=real|simulado|grabar`, en un único sitio

Una sola variable decide los tres modos para **todos** los canales, y la lee un único punto (el
contenedor de servicios o la factoría de adaptadores), nunca cada llamada:

| Modo | Qué hace | Cuándo |
|---|---|---|
| `simulado` | Habla con `mocks/<canal>/` (o el adaptador en proceso) | desarrollo, tests y E2E: el defecto |
| `real` | Habla con el proveedor | staging con credenciales de prueba, y el Gate E |
| `grabar` | Habla con el real **y guarda** la respuesta como fixture del simulado | al crear o refrescar fixtures (§7.3) |

```python
# settings: una línea; el resto del código no sabe en qué modo está
EXTERNAL_MODE = os.environ.get("EXTERNAL_MODE", "simulado")  # real | simulado | grabar
```

Un test de contrato corre **contra los dos** (simulado y, cuando hay red y credenciales, real) con
las mismas aserciones. Referencia: elvion, skill `simuladores-externos` (`.agents/skills/`),
`core/orchestrator/service_container.py` y `scripts/smoke_mock_services.py`.

**La excepción: el modo como dato, no como variable.** Cuando quien cambia el modo no es un
desarrollador sino el cliente (el correo de una demo que hay que poder encender sin redeploy), el
modo vive en la BD (un modelo de configuración en el admin) y el único `enviar()` **siempre**
registra lo que mandó, se envíe de verdad o no. Referencia: fitapp, ADR 0011
(`.docs/adr/0011-correo-con-simulador-conmutable.md`) y `backend/apps/correo/`.

### 6.2 La puerta `/_averia`: fallos en caliente, sin reiniciar

`escenarios.json` (§5) dice qué fallos existen; `POST /_averia` los **enciende** mientras la app
corre, y `POST /_reset` vuelve al estado inicial entre escenarios:

```http
POST /_averia   {"scenario": "slow", "route": "/v2/citas", "times": 3}
POST /_reset
```

El test E2E llama a `/_averia` en su preparación y a `/_reset` al acabar; el panel (§3) tiene un
botón por escenario que hace lo mismo. Va con el resto del simulador en 127.0.0.1 y **no existe en
el proveedor real**: si el código de producción la llama, es un fallo. Referencia: musa,
`mocks/flowww_mock_v2/` (`/v2/_averia`, `/v2/_reset`, `/v2/_sembrar_ocupacion`) y
`backend/scripts/mocks_reset.py`; EvoPreven, `faults.py` con escenarios YAML y un estado esperado
que se compara al final (como patrón; su código no se toca).

### 6.3 Calibrar contra una lectura real, nunca contra el ejemplo de la documentación

El ejemplo de la documentación de un proveedor **no es** su respuesta: le faltan campos, trae otros
tipos o está desfasado. El simulador se calibra con **una respuesta real capturada** (modo `grabar`
o la llamada del Gate E), y esa captura se guarda junto al `CONTRATO.md` con su fecha. Referencia:
musa, lección 13 (`flowww_mock_v2`, calibrado contra una lectura real).

### 6.4 Paridad en las dos direcciones

Que el simulador acepte todo lo que acepta el real **no basta**: un simulador **más restrictivo**
que el real también engaña, porque hace programar defensas contra fallos que no existen o esconde un
tope detrás de un filtro que el real no aplica (musa, lección 16). La prueba de paridad mira:

- lo que el real acepta, el simulado lo acepta, con la misma forma de respuesta;
- lo que el real rechaza, el simulado lo rechaza con el mismo código y el mismo cuerpo de error;
- los topes (paginación, tamaño, número de resultados) se aplican **en el mismo orden** que el real
  (primero filtrar y después topar, si el real lo hace así).

### 6.5 El mismo cliente HTTP para real y simulado

El simulador es un servidor; el código que le habla es **el mismo cliente** que habla con el real,
con otra URL base (§2). Si hay un `ClienteSimulado` aparte, lo que se prueba es ese cliente, no el
de producción. Referencia: AMC, `channels_mock` (el cliente real y el simulado son el mismo código).

---

## 7. LLM: grabar y reproducir

La cabecera de este documento incluye «un modelo de IA de terceros», y un LLM es el externo que más
se llama y más cuesta. Se prueba en cuatro niveles, de más rápido a más fiel:

| Nivel | Herramienta | Para qué | Cuidado |
|---|---|---|---|
| **Unitario, sin red** | `GenericFakeChatModel` / `FakeListChatModel` (langchain-core) + `InMemorySaver` | La lógica del grafo con respuestas fijadas, tool calls incluidas | `GenericFakeChatModel` **no implementa `bind_tools`**: hay que subclasearlo. Su iterador se agota: fixture con scope de función. `FakeListChatModel` vuelve a empezar al acabarse la lista |
| **Integración, graba una vez** | vcrpy 8.x + pytest-recording 0.14 (`@pytest.mark.vcr`, `--record-mode=once`, cassettes en `tests/cassettes/`) | El patrón que documenta LangChain. vcrpy soporta httpx, que es lo que usa el SDK de OpenAI | Las tres trampas de abajo. `--block-network`, para que un test sin cassette falle en vez de salir a la red |
| **Integración vía LangSmith** | `langsmith[pytest]` con `LANGSMITH_TEST_CACHE=tests/cassettes` | Caché HTTP en disco | Sincroniza con LangSmith salvo `LANGSMITH_TEST_TRACKING=false`; la doc no aclara si la primera ejecución sin red funciona |
| **Evals por API** | Caché de promptfoo (`~/.promptfoo/cache`, TTL de 14 días; `--no-cache`) | Repetir una suite sin pagar dos veces | En CI: `PROMPTFOO_CACHE_TYPE=disk` y `PROMPTFOO_CACHE_PATH` |

Versiones y fuentes: informe R2 de la revisión integral
(`.docs/plans/2026-10-17-revision-integral-template/sources/r2-auditor-codigo-qa.md` §4.1, 17-10-2026).
Son dependencias de desarrollo del proyecto y se fijan al instalarlas.

### 7.1 Trampa 1 — `match_on` sin el cuerpo: un prompt cambiado sigue «pasando»

El `match_on` por defecto de vcrpy es `method, scheme, host, port, path, query`. **Todas** las
llamadas de chat son un POST a la misma URL, así que coinciden entre sí: cambias el prompt y la
cassette sigue respondiendo lo de antes, en verde. El arreglo es un matcher que compare el cuerpo
sin los campos que cambian solos:

```python
# conftest.py
import json

import pytest

VOLATILE = {"user", "metadata", "stream_options"}


def llm_body(r1, r2):
    a, b = (json.loads(r.body or b"{}") for r in (r1, r2))
    for d in (a, b):
        for k in VOLATILE:
            d.pop(k, None)
    assert a == b, "el cuerpo de la llamada al LLM cambió: regrabar con EXTERNAL_MODE=grabar"


def pytest_recording_configure(config, vcr):
    vcr.register_matcher("llm_body", llm_body)


@pytest.fixture(scope="module")
def vcr_config():
    return {"match_on": ["method", "host", "path", "llm_body"],
            "filter_headers": ["authorization", "x-api-key", "api-key"],
            "filter_post_data_parameters": ["api_key"]}
```

**Control negativo obligatorio** (sin él no se sabe si el matcher está puesto): con la cassette
grabada, cambia una palabra del system prompt y corre el test con `--record-mode=none`. Tiene que dar
**rojo** (`CannotOverwriteExistingCassetteException` o el `assert` del matcher). Si da verde, el
cuerpo no está en `match_on`.

### 7.2 Trampa 2 — las cassettes son datos

Una cassette guarda el prompt y la respuesta enteros. En un bot de salud, una cassette grabada con
una conversación real **es un dato de salud versionado en git**. Por eso:

- se graban solo con conversaciones **sintéticas**;
- `before_record_request` y `before_record_response` redactan lo que quede (la máscara B de
  `templates/bot-data/pii_mask.py` sirve);
- el gate del proyecto pasa un grep de PII sobre `tests/cassettes/`.

### 7.3 Trampa 3 — caducan, y regrabar pide red

Cambiar un prompt o una tool obliga a borrar la cassette y regrabar con red, y eso choca con «el
E2E no sale a internet» (`rules/verification.md` §E2E-4). La salida es el modo **`grabar`
explícito** de §6.1: regrabar es un acto con nombre
(`EXTERNAL_MODE=grabar pytest tests/llm/ --record-mode=rewrite`), nunca algo que pasa solo porque
faltaba una cassette.

> ⚠️ **Sin verificar: streaming.** Grabar respuestas SSE con vcrpy y httpx no está probado. Si el bot
> usa `stream=True`, pruébalo antes de prometerlo; mientras tanto, los tests de integración llaman
> sin streaming.

---

## 8. Escenarios de canal: lo que hacen de verdad los proveedores de mensajería

Los escenarios de §5 son el mínimo de cualquier API. Un **canal de mensajería** (WhatsApp,
Instagram, Evolution API, ManyChat) tiene además estos, y son los que rompen un bot en producción:

| Escenario | Qué hace el proveedor | Qué tiene que hacer el bot | Fuente |
|---|---|---|---|
| **duplicado** | Meta reintenta y avisa de que los reintentos pueden duplicar: el mismo `message.id` llega más de una vez | Deduplicar por el id del proveedor **antes** de llamar al LLM o a una tool | Meta, *Set up webhooks* `[oficial]` |
| **desorden** | Dos mensajes seguidos pueden llegar al revés | Guardar la conversación por el `timestamp` del proveedor, no por la hora de llegada | `[inferencia]` de los reintentos |
| **reintento tardío** | Sin un 200, Meta reintenta **hasta 7 días** | Recordar los ids vistos más de 7 días (un TTL de 24 h deja pasar el reintento) | Meta, *Set up webhooks* `[oficial]` |
| **firma sobre bytes crudos** | `X-Hub-Signature-256: sha256=<HMAC-SHA256 del cuerpo con el app secret>` | Verificar sobre `request.body` tal cual; nunca sobre `json.dumps(request.data)`, que cambia espacios y escapes | Meta, *Webhooks · Getting started* `[oficial]` (la fórmula); que reserializar la rompe está probado en `templates/bot-testing/` |
| **tamaño** | Payloads de **hasta 3 MB** | Admitirlos: el tope por defecto de Django (`DATA_UPLOAD_MAX_MEMORY_SIZE`) es 2,5 MB y responde 413 | Meta, *Set up webhooks* `[oficial]` |
| **plazo de ~10 s** | ManyChat (*External Request*) corta hacia los 10 s | Responder 200 al momento y devolver el resultado por API después | Foro de ManyChat `[blog-opinión]` |

Contrastado el 31-10-2026 contra developers.facebook.com (*WhatsApp Cloud API · Set up webhooks* y
*Graph API · Webhooks · Getting started*). La firma HMAC de **Evolution API no está documentada** en
ninguna fuente que se haya podido leer: si el proyecto la usa, se mide con una lectura real (§6.3).

**El kit, con el control negativo hecho:** `templates/bot-testing/` trae el simulador
(`channel_sim.py`: duplicado, desorden, reintento tardío, cuerpo de casi 3 MB, firma ajena y el
plazo de 10 s), un bot de fixture con cada defensa apagable y pruebas que dan rojo al quitar cada
una (sin idempotencia fallan el duplicado y el reintento tardío). Se copia al proyecto y el bot de
fixture se cambia por la vista del webhook real.

**Lo que no se usa como dependencia, y por qué:**

- `stripe trigger` **crea objetos reales en modo test** y necesita cuenta y red: sirve en staging, no
  en el simulador. Para trabajar sin red, el simulador propio con webhooks firmados.
- Emuladores de WhatsApp de terceros (whaloc, mockpost): 2★ y un autor. Valen como **referencia de
  contrato** para leer su especificación, no como dependencia.
- Para **nuestras** APIs con OpenAPI, los mocks del frontend salen del contrato (orval genera
  handlers de MSW) en vez de escribirse a mano; eso es MSW, no esto (ver «NO aplicar»).

---

## 9. El modelo de IA como proveedor: simulador por defecto, el real detrás de un registro (CB-87)

Un LLM es un tercero más, con dos rasgos que lo hacen peor que un CRM: **cobra por llamada** y
**contesta texto que no promete nada**. El patrón, cosechado de risk-couple
(`backend/apps/insights/adapters/`: `base.py`, `mock.py`, `registry.py`, `anthropic.py`), es este:

```python
# registry.py — `LLM_PROVIDER` elige; el simulador es el valor por defecto.
def get_adapter() -> InsightAdapter:
    name = getattr(settings, "LLM_PROVIDER", "mock")
    if name == "anthropic":
        from .anthropic import AnthropicAdapter
        return AnthropicAdapter()
    return MockAdapter()

def write_with_fallback(payload: InsightPayload) -> InsightResult:
    adapter = get_adapter()
    if adapter.name == "mock":
        return adapter.write(payload)
    try:
        return adapter.write(payload)
    except AdapterUnavailable as exc:
        log.warning("llm_fallback", extra={"provider": adapter.name, "reason": exc.code})
        metrics.incr("llm.fallback", tags={"reason": exc.code})   # la caída se cuenta
        return MockAdapter().write(payload)
```

Las reglas del adaptador real, que no se relajan:

1. **`timeout` obligatorio** (`LLM_TIMEOUT_SECONDS`). Sin él, una petición colgada deja al usuario
   mirando un spinner y, en Celery, se come un worker.
2. **La respuesta se valida contra un esquema** (salida estructurada + Pydantic): si no tiene la forma
   acordada, `AdapterUnavailable("schema_invalida")` y se cae al simulador. Dar por buena la forma es
   pintar `None` en la pantalla de alguien.
3. **Al payload no se le añade nada**: se manda lo que construyó el código, una dataclass cerrada.
   Enriquecer el prompt «para que redacte mejor» es como se filtra un dato (`rules/llm-in-product.md` §5).
4. **Sin `temperature`, y leyendo el bloque de texto.** risk-couple manda `temperature: 0` («aquí se
   redacta, no se crea») a `claude-sonnet-5`, y según la guía de migración la familia 4.7+ lo rechaza
   con un **400**; su adaptador convierte ese error (`HTTPError` es un `URLError`) en
   `AdapterUnavailable` y cae al simulador, así que **el redactor real no funcionaría nunca y nadie lo
   vería**. Lo mismo con `datos["content"][0]["text"]`: si el modelo trae el thinking activado, el
   primer bloque es `thinking` y la lectura falla igual. Leído en el código, no llamado a la API
   (`agente-modelo-y-coste.md` §Roturas). La repetibilidad que se buscaba la da el esquema, no la
   temperatura.
5. **El simulador imita la forma de la respuesta real** (los mismos campos, un texto plausible y
   escueto), no un `"lorem ipsum"`: la pantalla se diseña contra él.

**Cuándo se cae al simulador y cuándo no** (degradar, bloquear o rechazar según el contexto) lo decide
`rules/external-provider-dependency.md` §2: degradar vale para una redacción que el usuario puede
recibir más escueta, **no** para un golden set ni para el turno de un bot que sin el modelo no existe.
Y la caída se **cuenta** (§3 de esa rule): sin la métrica, el proveedor puede llevar semanas roto.

---

## 10. Simuladores de embudo: tabla propia, marca visible y fuera de las métricas (NE-8)

Un simulador de canal que **fabrica el embudo** (entregado, abierto, clic, convertido) es útil para ver la
pantalla con datos, y es el más peligroso de todos: produce justo las cifras que mira el dueño del negocio.
Caso visto (r4-campanas E4): el modo simulación fijado en `settings/base.py`, que vale para **todos** los
entornos; el embudo salía de un hash del destinatario (98 % entregado, 60 % abierto, 20 % clic, 6 %
convertido); lo simulado se marcaba escribiendo «simulated» en `error_message`, y el panel enseñaba esas
tasas como si fueran reales. Tres reglas:

| Regla | Cómo se cumple | Lo que la rompe |
|---|---|---|
| **Marca propia** | Tabla aparte o columna `is_simulated` / `is_synthetic` **NOT NULL**, puesta al crear la fila | Reutilizar un campo con otro significado (`error_message`, `notes`, un estado) |
| **Imposible de pasar por alto** | Banda fija en el panel («Datos simulados, no son ventas reales») y cada cifra con la marca; el modo se decide por entorno (§6.1), nunca en `settings/base.py` | Un aviso pequeño en el pie o una tasa sin marca |
| **Fuera de todo KPI** | La función del KPI filtra por la marca **y se niega** si le llega una fila simulada (`SimulatedDataError` en `templates/campanas/level0.py`; `sintetica` en `templates/fichas-kpi/`) | Un `.filter()` que alguien olvida en una vista nueva |

**Por qué negarse y no solo filtrar:** el filtro en cada consulta se olvida en la siguiente vista; una
función de KPI que lanza un error con un dato simulado falla en el test, que es donde se ve. Lo comprueba
`test_el_informe_se_niega_con_filas_simuladas` del kit de campañas (si se quita la negativa, cae: sabotaje
de la 3.51). En la campaña, el gate lo exige como **C9** (`rules/campanas-salida.md`).

---

## 11. El kit: no se empieza de cero (WA-7)

Lo de §1-§6 y §8 viene montado (grabar el LLM, §7, no) en **`webapps/mock-kit/`** (sub-olas
4.03-4.04): escenarios con schema que exige los cinco de §5, `/_fault` (alias `/_averia`) con
`times`, `/_reset`, `/_seed`, panel con «lo que se repitió», estado esperado con verificador, paridad contra una captura real y
**autoprueba con control negativo**: cada escenario corre contra un proyecto de prueba bueno y otro
ingenuo, y si ninguno caza al ingenuo sale «sin medir». Ejemplos: Stripe (Checkout + webhook firmado),
ManyChat (External Request con plazo de ~10 s + `sendContent`) y uno en blanco.

```bash
cd webapps/mock-kit && python3 -m mock_kit init /ruta/mi-proyecto --channel stripe
cd /ruta/mi-proyecto/mocks && python3 -m mock_kit self-test stripe
```

`init` copia el núcleo (sin `pip install`, solo stdlib) y escribe la fila del registro de §4. Los
nombres de fichero del kit van en inglés (`scenarios.json`, `CONTRACT.md`), como pide
`code-style.md`; la carpeta `mocks/` y su registro son los de este patrón.

---

## Anti-patterns

- ❌ Un simulador que **no imita la API real** sino lo que nos gustaría que fuera → el día de la
  integración hay que reescribir el cliente entero.
- ❌ Cambiar código de producción para que hable con el simulador. Solo cambia la URL base, y por
  variable de entorno.
- ❌ Publicarlo en `0.0.0.0` → un servicio sin auth abierto a internet, con datos de cliente dentro.
- ❌ Simulador **sin panel** → es un mock con más pasos y nadie lo mantiene.
- ❌ Sin escenario `lento` → nunca sabrás si tus llamadas tienen `timeout` hasta que un worker se
  quede colgado en producción.
- ❌ `CONTRATO.md` sin versión ni fecha → dentro de un año nadie sabe qué API imita, y los tests
  pasan contra una API que ya no existe.
- ❌ Confundirlo con MSW: **MSW simula NUESTRO backend** dentro del frontend; esto simula a **los
  terceros**, y corre como un servicio aparte que también usa el backend.
- ❌ Dar por válida la integración porque el simulador está verde → el Gate E (una llamada real)
  sigue siendo obligatorio.
- ❌ Un `ClienteSimulado` distinto del cliente real → se prueba un cliente que no va a producción (§6.5).
- ❌ Calibrar el simulador con el ejemplo de la documentación → imita una respuesta que el proveedor
  no da (§6.3).
- ❌ Un simulador más restrictivo que el real «por seguridad» → también engaña (§6.4).
- ❌ vcrpy con el `match_on` por defecto en llamadas al LLM → un prompt cambiado sigue en verde (§7.1).
- ❌ Cassettes grabadas con conversaciones reales → datos personales en git (§7.2).
- ❌ Deduplicar con un TTL de 24 h, o verificar la firma sobre el JSON reserializado (§8).
- ❌ Un embudo simulado marcado en `error_message`, o sumado a un KPI que ve el dueño (§10).
- ❌ No registrarlo en `mocks/README.md` → el siguiente proyecto lo escribe otra vez desde cero, que
  es exactamente lo que este documento existe para evitar.

---

_Patrón v1.3 · 2026-11-01 — §11 el kit `webapps/mock-kit/` (WA-7, sub-olas 4.03-4.04); el ejemplo de
`/_averia` con las claves del kit.
v1.2 · 2026-10-31 — §10 simuladores de embudo fuera de las métricas (NE-8, sub-ola 3.51).
v1.1 · 2026-10-31 — §6 conmutador `EXTERNAL_MODE`, `/_averia`, calibración y paridad
(WA-12), §7 LLM grabar y reproducir (WA-15), §8 escenarios de canal y versiones contrastadas
(WA-16), sub-ola 4.02; §9 el modelo de IA como proveedor con
simulador por defecto (CB-87, sub-ola 3.26). v1.0 · 2026-09-12. Nace de un insight del Usuario: «siempre va a haber una carpeta mocks con
simuladores de los canales con los que se comunica la plataforma; tiene que imitar tal cual la API y
tener una interfaz mínima para ver qué se envía, qué se recibe e incluso lo que se vuelve a enviar»._
