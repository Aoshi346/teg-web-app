---
paths:
  - "**/views.py"
  - "**/views/*.py"
  - "**/viewsets.py"
  - "**/urls.py"
  - "**/serializers.py"
  - "**/serializers/*.py"
  - "**/api.py"
  - "**/api/**/*.py"
  - "**/routers.py"
  - "**/openapi*.yml"
  - "**/openapi*.yaml"
  - "**/openapi*.json"
  - "**/schema.yml"
---
# Contrato HTTP — verbos, un método por endpoint, secretos fuera de la URL e idempotencia

> **Cuándo aplicar:** al **diseñar, escribir o revisar un endpoint** — uno nuevo, uno que cambia de
> forma, o el momento de decidir por dónde entra una acción. Cubre la capa que va **antes** de la
> lógica: qué verbo, qué responde a un método que no toca, dónde viaja la credencial, qué pasa si
> el cliente llama dos veces, y qué exige una operación que no se puede deshacer.
>
> **NO aplicar:** para **quién puede ver qué** — autorización, pertenencia al tenant y el filtro por
> dueño son `patterns/stack/backend-vistas.md` §1.2 y la skill `multi-tenant-context`, y esta rule
> no los duplica · para la **forma de los datos** (campos, tipos, `fields = "__all__"`), que es
> `backend-serializers.md` · para el **puerto y la red** (`--bind`, Docker, túnel SSH), que es
> `rules/security.md` · para las **tools de un agente LangGraph**, cuyo equivalente completo —con su
> tabla de reversibilidad y su `interrupt()`— es `patterns/stack/agente-hitl.md`, mucho más
> desarrollado que el §6 de aquí · para **webhooks entrantes de terceros**, que tienen su propia
> skill con firma, anti-replay y secreto por tenant (`webhook-multi-tenant-validation`).
>
> **Relacionado:** `patterns/stack/backend-vistas.md` (la vista, los permisos, el sobre de errores)
> · `patterns/stack/agente-hitl.md` (§2 la clave determinista, §106 el ancla de `DELETE /v2/stock`)
> · `skills/webhook-multi-tenant-validation` (§"Si el token va en la URL") ·
> `patterns/stack/agente-observabilidad.md` (la lista `_PROHIBIDO` que aquí se reutiliza) ·
> `rules/verification.md` §Smoke testing (las cuatro llamadas mínimas por endpoint) · `rules/security.md` ·
> `rules/adr.md` (romper un contrato es un ADR, no un prefijo `/v1/`).

---

## 0. Por qué existe, y qué NO arregla

Esto llevaba sin estar escrito en ninguna parte de `.claude/`. Medido el 2026-09-04: cero menciones
a la semántica de los verbos, cero a **405**, cero a `Idempotency-Key`, y ningún comprobador que
mirase un método HTTP. Lo que había era un mapeo URL→acción dentro de un docstring y una tabla en un
fichero **deprecado que el harness no carga**.

No es un hueco cosmético: mientras solo viva en el conocimiento general del modelo, se aplica cuando
hay contexto de sobra y se cae cuando no — que es exactamente la definición de *advisory*
(`rules/layer-decision.md`). Y el harness tenía además **ejemplos que enseñaban lo contrario**: su
plantilla de flujos de usuario proponía `GET /api/auth/verify/?token=…` como paso canónico.

> **El límite honesto, por delante:** de las ocho secciones de abajo, hoy solo tres tienen mecanismo
> —§2 y §4 un comprobador en **sombra**, §3 una línea en el smoke—. Las otras cinco son criterio
> escrito. Criterio escrito y enrutado vale bastante más que criterio recordado, y bastante menos
> que un gate.
>
> **Y sobre los dos comprobadores, lo que la medición dice y lo que no** (2026-09-04, sobre los
> 1.989 ficheros de un backend Django real): **0 hallazgos cada uno**. Eso es una buena noticia y
> una mala. La buena: el detector funciona —ve **1.092 lecturas de query params con 222 nombres
> distintos** y ninguna es una credencial—, así que la regla es **estrecha y no va a morir de
> ruido**, que es como mueren la mayoría. La mala: **solo ha disparado sobre el fixture sintético**,
> así que su recall sobre código real está **sin demostrar**. Por eso están en `sombra` y no en
> `activo`, y por eso promoverlas exigiría antes verlas cazar algo de verdad
> (`rules/refactor-progresivo.md` §4.5).

---

## 1. Los verbos, y el corolario que de verdad se incumple

| Verbo | Para qué | ¿Seguro? | ¿Idempotente? |
|---|---|:--:|:--:|
| **GET** | consultar, y **solo** consultar | **sí** | sí |
| **POST** | crear un recurso, o ejecutar una acción | no | **no** |
| **PATCH** | modificación **parcial** | no | no necesariamente |
| **PUT** | reemplazo **completo**, o una operación idempotente | no | **sí** |
| **DELETE** | eliminar | no | sí (repetirlo deja el mismo estado) |

**Seguro** = no cambia estado observable. **Idempotente** = llamarlo N veces deja el sistema igual
que llamarlo una.

**El corolario, que es la única parte que se incumple de verdad:** si una acción cambia estado, **no
se alcanza por GET aunque sea cómodo**. Y es cómodo justo en los cuatro sitios donde más aparece:

| Tentación | Por qué es GET | Por qué está mal |
|---|---|---|
| Confirmar un email / activar una cuenta desde un enlace | un enlace en un correo solo sabe hacer GET | el token viaja en la URL (§3) y cualquier precarga del cliente de correo la "pulsa" por ti |
| Un botón de "reenviar", "aprobar" o "cancelar" que es un `<a href>` | no había formulario | los aceleradores de navegador y los rastreadores siguen enlaces |
| `/api/pedidos/123/marcar-enviado` desde el navegador | se probaba a mano y así se pega en la barra | queda en el historial, y un día alguien lo recarga |
| Un export que además **crea** el trabajo de exportación | "es una lectura" | crea una fila y consume recursos: es un POST que devuelve el id del trabajo |

Para el caso del correo, el patrón es: el enlace abre **una pantalla**, y la pantalla hace el POST.
Un paso más para el usuario, y desaparece el token del log de acceso.

**Recursos, no acciones, en el nombre.** El verbo lo pone HTTP: `POST /usuarios/` y no
`POST /crearUsuario`. La excepción práctica y aceptada son las transiciones de estado que no son un
CRUD (`POST /facturas/123/emitir/`), que es lo que hace un `@action` de DRF.

---

## 2. Un endpoint, un verbo por intención

**Una vista no ramifica por `request.method` entre leer y escribir.** No es estilo: un endpoint que
acepta GET y POST indistintamente hace que la mitad de las protecciones dejen de tener sentido — el
CSRF aplica a una rama y no a la otra, la caché puede guardar lo que no debía, y el registro de
acceso deja de distinguir una consulta de una escritura.

```python
# ❌ el mismo camino sirve para consultar y para cobrar
@api_view(["GET", "POST"])
def suscripcion(request): ...

# ✅ dos intenciones, dos endpoints
@action(detail=True, methods=["get"])   def estado(self, request, pk=None): ...
@action(detail=True, methods=["post"])  def cobrar(self, request, pk=None): ...
```

Declararlo explícitamente es lo que además hace que el 405 salga solo:

| Framework | Cómo se declara |
|---|---|
| DRF `@action` | `methods=["post"]` — **un solo verbo**, y si hace falta otro es otro `@action` |
| DRF `APIView` | define solo los métodos que soporta (`def get`, `def post`); DRF responde 405 al resto |
| Vista de Django | `http_method_names = ["post"]` en la CBV, o `@require_http_methods(["POST"])` |

`ModelViewSet` es la excepción que confirma la regla: sirve varios verbos, pero **cada uno con su
semántica ya correcta** y su código de estado ya puesto. El problema no es servir varios verbos: es
que dos intenciones distintas compartan camino.

**Comprobador:** `be-view-action-multiverbo` (**sombra**) — AST: un `@action` cuya lista `methods`
mezcla un verbo de lectura con uno de escritura. Un `@action` con varios verbos de escritura
(`["put", "patch"]`) **no** dispara: eso es una misma intención con dos formas.

---

## 3. Códigos: el 405 y los que ya estaban

Lo que ya está escrito en `backend-vistas.md` sigue mandando (201 al crear, 204 al borrar, el sobre
`{"errors": …}`, y que **el error se lanza, no se devuelve**). Lo que faltaba:

- **405 Method Not Allowed** es la respuesta correcta al método que el endpoint no soporta, y sale
  gratis si el §2 está bien hecho. Si en su lugar sale un **404**, el endpoint está resolviendo por
  ruta y no por método, y eso oculta errores de integración del cliente. Si sale un **500**, hay una
  vista que ramifica a mano.
- **Se comprueba**, y por eso está en el mínimo del smoke (`rules/verification.md` §Smoke testing):
  ```bash
  curl -s -o /dev/null -w 'método incorrecto → HTTP %{http_code}\n' \
       -X GET "$API/api/pedidos/1/cobrar/" -H "Authorization: Bearer $TOKEN"   # espera 405
  ```

---

## 4. Credenciales y datos personales: nunca en la URL

**La regla:** la **credencial** viaja en la cabecera `Authorization`; los **datos de la operación**
viajan en el body. En la query van filtros, paginación y ordenación — nada que no puedas ver escrito
en la pantalla de otra persona.

**El porqué, que es lo que hace que se recuerde: una URL se escribe entera en cinco sitios que no
controlas.**

| Dónde acaba | Quién lo ve |
|---|---|
| **Log de acceso** del servidor y del balanceador | quien administra, quien recibe el log rotado, el agregador |
| **Historial del navegador** | cualquiera con el equipo delante |
| Cabecera **`Referer`** al salir a otro dominio | el tercero al que enlazas |
| **Caché de proxies** y CDN | según cabeceras, más gente de la que crees |
| Capturas, tickets, mensajes de soporte | todo el que pida ayuda pegando la URL |

Los nombres que nunca aparecen a la derecha de un `?`: `token`, `api_key`, `secret`, `password`,
`session`, y cualquier dato personal — `dni`, `nif`, `email`, `telefono`, `iban`. Un identificador
opaco de recurso (`/facturas/8f3a…/`) sí; un **documento de identidad como `lookup_field`**, no: eso
es a la vez un dato personal en la URL y un identificador adivinable.

**La excepción, que está documentada y acotada:** un webhook cuyo proveedor solo acepta pegar una
URL. Entonces el token *es* la credencial y viaja en la ruta; las tres condiciones para que sea
aceptable (que no se escriba en el log, que sea rotable por inquilino, y que no se confunda con una
firma) están en `skills/webhook-multi-tenant-validation` §"Si el token va en la URL". No las
repitas aquí: ve allí.

**Comprobador:** `be-api-secreto-en-query` (**sombra**) — AST: lectura de un nombre sensible desde
`request.query_params` / `request.GET`. Cubre credenciales (`token`, `api_key`, `secret`,
`password`, `session`…) e identificadores fuertes (`dni`, `nif`, `nie`, `iban`, `card`, `cvv`).

> **`email` y `telefono` se quedan FUERA del comprobador a propósito**, aunque el párrafo de arriba
> sí los nombra. Son filtros de búsqueda legítimos en medio repo (`?email=` en un buscador de
> administración), así que incluirlos dispararía en decenas de sitios correctos y la regla moriría
> de ruido — que es exactamente lo que la regla de inversión de `patterns/README.md` §2 manda
> evitar. Que un email no deba viajar en la query de un endpoint **público** sigue siendo cierto:
> es criterio, no mecanismo, y la diferencia está dicha aquí para que nadie confunda "el checker no
> lo marca" con "está bien".

---

## 5. Idempotencia del endpoint que dispara un efecto externo

Un cliente reintenta. El navegador reintenta, el móvil con mala cobertura reintenta, y la pasarela
de pagos reintenta por diseño. Si tu endpoint cobra, envía o publica, **reintentar tiene que ser
inofensivo**.

Aplica a lo que **sale fuera y ya no vuelve**: un cobro, un correo, un SMS, una campaña, un pedido
en el sistema de otro, un documento firmado. No aplica a un `PATCH` sobre una fila propia.

```python
# El cliente aporta una clave estable de ESTA intención; el servidor la guarda con la respuesta.
key = request.headers.get("Idempotency-Key")
if not key:
    raise ValidationError("Idempotency-Key es obligatoria en este endpoint")
if (previa := IntentoDeCobro.objects.filter(clave=key).first()):
    return Response(previa.respuesta, status=previa.status)   # misma respuesta, sin cobrar otra vez
```

**La clave tiene que ser DETERMINISTA**, y esta lección ya está pagada en esta casa
(`agente-hitl.md` §2): si lleva un `uuid4()` o un `time.time()`, el segundo intento genera otra clave,
el sistema la ve como una operación nueva y **el cliente recibe los dos cobros igual**. Y no falla
haciendo ruido: deduplica perfectamente sobre dos claves que nunca debieron ser dos.

| Clave | Segundo intento |
|---|---|
| `uuid4()` en el cliente, regenerado en cada envío | ❌ cobra dos veces |
| la hora del envío | ❌ igual, y además irreproducible en un test |
| `f"cobro:{pedido_id}:{importe_céntimos}"`, o un uuid generado **una vez al abrir el formulario** | ✅ el segundo se descarta |

Se comprueba sin montar nada: **manda la misma petición dos veces y mira si hay dos efectos.** Si el
endpoint no acepta clave, la alternativa mínima es una restricción de unicidad en la base de datos
sobre la intención, más `select_for_update()` (`backend-servicios.md`), que es lo que impide que dos
clics simultáneos pasen los dos.

**Campañas y envíos masivos** son el caso peor, porque el efecto es irreversible y multitudinario:
el endpoint que dispara una campaña lleva clave de idempotencia **y** un registro previo de a quién
se va a enviar, para que un reintento reanude en vez de reenviar.

---

## 6. Lo irreversible: confirmación, scope y por qué no basta el permiso

El ancla es real y de la casa (`agente-hitl.md:105`): **`DELETE /v2/stock` borraba el inventario
entero de una clínica con una sola llamada autenticada** — sin parámetro de confirmación, sin límite
de alcance, sin borrado lógico. Quien llamó tenía permiso. El permiso no era el problema.

Para un endpoint destructivo o irreversible, tres cosas, y ninguna sustituye a las otras:

1. **Scope obligatorio.** Un borrado no acepta "todo" por omisión: exige a quién afecta
   (`{"ids": [...]}` o un filtro explícito). Que el parámetro vacío signifique *todo* es el fallo de
   diseño, no el descuido de quien llamó.
2. **Confirmación en la petición**, proporcional al daño: un campo `confirm` con el número de filas
   que el cliente cree que va a borrar (y el servidor rechaza si no coincide) es barato y caza el
   caso real — el cliente creía que borraba 3.
3. **Reversibilidad donde se pueda**: borrado lógico con auditoría (`django-orm`, `references/crud.md`), que convierte
   un desastre en una tarde.

**La confirmación de la interfaz no cuenta.** El modal de `ux-reviewer` §3 protege a quien usa la
pantalla; no protege de un script, de una integración, ni de un agente con el token. La API es
alcanzable sin pasar por la UI: por eso esto vive aquí y no solo allí.

---

## 7. Logs seguros en la capa HTTP

Esta casa ya tiene escrita la lista de lo que nunca se registra —para tool calls de agentes— y **es
la misma lista**. No escribas otra: reutiliza `patterns/stack/agente-observabilidad.md`:

```python
_PROHIBIDO = {"password", "token", "api_key", "authorization", "secret",
              "dni", "nif", "tarjeta", "card", "cvv", "iban", "telefono", "email"}
```

Aplicado a HTTP significa tres cosas concretas:

- **No se registra el body entero** de una petición de autenticación, de pago o de alta. Se registra
  qué endpoint, qué status y cuánto tardó.
- **No se registra la cabecera `Authorization`**, ni entera ni "los primeros caracteres".
- **Si el log guarda la URL completa** (lo normal), entonces el §4 deja de ser una recomendación de
  higiene y pasa a ser la única defensa: lo que no metes en la query es lo que no acaba en el log.

Lo que **sí** se registra, porque es lo que sirve cuando algo falla: método, ruta con los
identificadores, status, latencia, id de usuario o de tenant, y un id de correlación.

---

## 8. Tools de agente y MCP: lectura, escritura, destructivo

Una tool es una API cuyo cliente se equivoca a propósito, así que todo lo anterior aplica — y encima
el que llama es un modelo que reintenta solo.

**Para tools de un agente que construimos**, el tratamiento completo está en
`patterns/stack/agente-hitl.md` y es mejor que cualquier resumen que quepa aquí: la tabla de
reversibilidad se **declara a mano**, porque el nombre engaña (`clear_cart` suena a destrucción y no
lo es), y lo irreversible pasa por `interrupt()` y no por un NUNCA en el prompt.

**Para servidores MCP conectados a la sesión**, el criterio:

| Tipo de tool | Dónde va |
|---|---|
| Lectura (`search_`, `get_`, `list_`) | `allow` |
| Escritura sobre estado propio y reversible | `allow` si el servidor está revisado |
| Escritura con efecto externo (envía, publica, cobra) | **`ask`** |
| Destructivo o irreversible | **`deny`**, y se ejecuta a mano |

> ⚠️ **Y aquí el límite honesto, que hay que decir para que nadie se confíe: hoy esto es criterio,
> no mecanismo.** La granularidad que ofrece `rules/security.md` §MCP es **el servidor entero**
> (`mcp__<servidor>__*`), no la tool. Y el bloque `ask` de `settings.json` está **vacío**, así que
> ahora mismo nada de esta tabla está cableado. Cablearlo toca `settings.json` → aprobación del
> Usuario (`rules/governance.md` §2). Lo que sí puedes hacer sin permiso de nadie es **no conectar**
> un servidor cuya superficie de escritura no has leído.

---

## Anti-patterns

- ❌ Un enlace de correo que **hace la acción** con GET → el cliente de correo la precarga y el token
  queda en el log. El enlace abre una pantalla; la pantalla hace el POST.
- ❌ Una vista que ramifica por `request.method` entre leer y escribir.
- ❌ `@action(methods=["get", "post"])` mezclando una consulta y una escritura.
- ❌ Devolver **404** donde tocaba **405** → oculta el error de integración del cliente.
- ❌ `?token=`, `?api_key=`, `?dni=` — y su primo, el documento de identidad como `lookup_field`.
- ❌ Un endpoint que cobra, envía o publica **sin clave de idempotencia** ni restricción de unicidad.
- ❌ Clave de idempotencia con `uuid4()` regenerado en cada envío → deduplica sobre dos claves que
  nunca debieron ser dos, y no falla haciendo ruido.
- ❌ Un borrado masivo cuyo parámetro **vacío significa "todo"**.
- ❌ Dar por protegida una operación destructiva porque la interfaz enseña un modal → la API se
  alcanza sin pasar por la interfaz.
- ❌ Registrar el body de un login o la cabecera `Authorization`, aunque sea "truncada".
- ❌ Escribir otra lista de campos prohibidos en vez de reutilizar la que ya existe (§7).
- ❌ Poner `/api/v1/` "por si acaso": aquí **no versionamos por URL** y está medido
  (`backend-vistas.md`). Romper un contrato es un **ADR**.
- ❌ Leer esta rule buscando quién puede ver qué → eso es `backend-vistas.md` §1.2 y
  `multi-tenant-context`, y aquí no está a propósito.

---

_Rule version: 1.0 · 2026-09-04 · API-1. Nace de una pregunta del Usuario sobre si estas prácticas
se aplicaban de forma sistemática; dos barridos sobre `.claude/` dijeron que la mitad no estaba
escrita en ninguna parte y que la plantilla de flujos enseñaba lo contrario. Los §5, §7 y §8
reutilizan doctrina que ya existía para agentes (`agente-hitl.md`, `agente-observabilidad.md`) y que
nunca se había bajado a la capa HTTP._
