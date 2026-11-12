# El contrato con el backend — los tipos se generan, no se escriben

> Capa `api` del patrón de casa, en su frontera con Django/DRF. Responde a una pregunta sola:
> **de dónde sale la lista de campos que el frontend espera recibir.** Hoy, en casi todos los
> proyectos, sale de que alguien la escribió a mano y se acuerda de mantenerla.
> Comprobación: `python3 .claude/patterns/stack/pattern_check_frontend.py --all src --only api`.

## La regla (una frase)

Los tipos de lo que devuelve el backend **se generan desde el propio backend** con un comando, se
versionan en el repositorio, y no se editan a mano nunca.

## Por qué, con el caso concreto

El backend (Django) y el frontend (React) son dos programas separados que se hablan por internet. El
backend manda datos —por ejemplo la ficha de un cliente, `{nombre: "Ana", telefono: "600…"}`— y el
frontend tiene escrito, en un fichero aparte, qué espera recibir. **Son dos listas que alguien tiene
que mantener iguales a mano.**

Lo que pasa cuando se despegan: un compañero renombra en Django el campo `nombre` a
`nombre_completo` porque queda más claro. El backend sigue funcionando perfecto. El frontend también
compila, porque su lista sigue diciendo `nombre` y nadie la ha tocado. Pero en la pantalla, donde
debería salir «Ana», ahora no sale nada. **Nadie se entera**: no hay error, no hay aviso, no falla
ningún test. Se descubre cuando llama un cliente diciendo que la ficha sale en blanco.

Con el contrato generado, ese mismo cambio **rompe el frontend al compilar**, en el ordenador de
quien lo hizo, con un mensaje que dice que `nombre` ya no existe. De tres semanas a tres segundos.

Y la razón que más pesa aquí: **un agente que toca el backend y el frontend a las 3 de la mañana no
va a acordarse de actualizar las dos listas.** Si están atadas, no hace falta que se acuerde.

## Implementación de referencia

**Qué es OpenAPI.** Es simplemente **un fichero que describe la API**, como la carta de un
restaurante: qué platos hay (qué URLs existen), qué lleva cada uno (qué campos devuelve) y de qué
tipo es cada cosa (texto, número, fecha). No se escribe a mano: una herramienta lo **genera leyendo
el código de Django**, así que si cambias el código, la carta cambia sola.

Son dos piezas y las dos son estándar en su ecosistema:

| Pieza | Dónde corre | Qué hace |
|---|---|---|
| **`drf-spectacular`** | backend | lee tus serializers y vistas y escribe la carta (`schema.yml`) |
| **`openapi-typescript`** | frontend | lee la carta y escribe los tipos de TypeScript |

### Paso 1 — el backend publica su carta

```python
# settings.py
INSTALLED_APPS += ["drf_spectacular"]
REST_FRAMEWORK["DEFAULT_SCHEMA_CLASS"] = "drf_spectacular.openapi.AutoSchema"
SPECTACULAR_SETTINGS = {"TITLE": "API", "VERSION": "1.0.0", "COMPONENT_SPLIT_REQUEST": True}
```

```bash
python manage.py spectacular --file schema.yml     # la carta, versionada en el repo
```

`COMPONENT_SPLIT_REQUEST` separa el tipo de lo que **envías** del tipo de lo que **recibes**. Sin él
los campos de solo lectura (`id`, `created_at`) aparecen como obligatorios al crear, y el formulario
te pide un id que aún no existe.

### Paso 2 — el frontend traduce la carta a tipos

```json
{
  "scripts": {
    "api:types": "openapi-typescript ../backend/schema.yml -o src/types/api.d.ts"
  },
  "devDependencies": { "openapi-typescript": "^7.13.0", "typescript": "^5.9.3" }
}
```

openapi-typescript 7.13.0 pide `typescript ^5.x` y usa su API de JavaScript: con TypeScript 6 o 7
`npm install` falla con `ERESOLVE`; forzándolo, con la 6 genera y con la 7 el generador revienta
(`frontend-stack.md` §Por qué TypeScript 5 y no 7, medido el 2026-10-21).

```bash
npm run api:types      # reescribe src/types/api.d.ts — el fichero SE VERSIONA
```

Se versiona a propósito: así el cambio de contrato **se ve en la revisión del código** («este PR
cambia 12 campos») en vez de aparecer en la máquina de cada uno al instalar.

### Paso 3 — el resto del frontend consume esos tipos

```ts
// src/types/order.ts — el único sitio donde se les pone un nombre corto
import type { components } from './api';

export type Order = components['schemas']['Order'];
export type OrderNuevo = components['schemas']['OrderRequest'];
```

```ts
// src/api/orders.ts
import type { Order, OrderNuevo } from '../types/order';

export const ordersApi = {
  listar: () => request<Order[]>('/orders/'),
  crear: (input: OrderNuevo) =>
    request<Order>('/orders/', { method: 'POST', body: JSON.stringify(input) }),
};
```

El alias del paso 3 existe para que `components['schemas']['Order']` no se repita por todo el repo:
si algún día cambia el generador, se toca un fichero.

### Paso 3b — proyecto nuevo: el cliente tipado (openapi-fetch + openapi-react-query)

**El default de un proyecto nuevo desde el 2026-10-21** (MO-D3, sub-ola 2.18; aprobado por el Usuario
el 18-10 como «DRF + openapi-react-query, continuidad»). En el paso 3 los tipos son del contrato pero
la **ruta** se sigue escribiendo a mano (`request<Order[]>('/orders/')`): si el backend la cambia, o
el tipo que se le pasa a `request` no es el de esa ruta, compila igual. Con el cliente tipado, ruta,
parámetros, cuerpo y respuesta salen de `paths`, el tipo que genera el paso 2: una ruta que ya no
existe **no compila**. Son dos paquetes de la misma familia que openapi-typescript (MIT):
openapi-fetch hace la llamada y openapi-react-query es un envoltorio de ~1 KB sobre TanStack Query.

**No sustituye al cliente único de `api-y-errores.md`: es ese cliente con las rutas tipadas.** El
timeout, `credentials`, el `ApiError` con sus campos y las dos conductas (sesión caducada y aviso del
5xx) se quedan; cambia dónde se enganchan — un *middleware* de openapi-fetch en vez del `if` de
`request()`. Lo único que se mueve: `ApiError` y `normalizeErrors`, que en `api-y-errores.md` viven
dentro de `client.ts` (y `normalizeErrors` sin exportar), pasan **tal cual** a `src/api/errors.ts` y se
exportan, porque ahora los usa el middleware:

```ts
// src/api/client.ts — el cliente único de api-y-errores.md, con las rutas y los tipos del contrato
import createFetchClient, { type Middleware } from 'openapi-fetch';
import createClient from 'openapi-react-query';
import type { paths } from '../types/api';                 // el fichero que genera el paso 2
import { ApiError, normalizeErrors } from './errors';       // los de api-y-errores.md, tal cual
import { onErrorDeServidor, onSesionCaducada } from './conductas';

/** Un HTTP no-2xx se convierte en ApiError, con las dos conductas de api-y-errores.md. */
const errorsAsApiError: Middleware = {
  async onResponse({ response }) {
    if (response.ok) return undefined;
    if (response.status === 401) {
      onSesionCaducada();
      throw new ApiError(401);
    }
    const body: unknown = await response.clone().json().catch(() => ({}));
    if (response.status >= 500) onErrorDeServidor(response.status);
    throw new ApiError(response.status, normalizeErrors(body));
  },
};

export const fetchClient = createFetchClient<paths>({
  baseUrl: import.meta.env.VITE_API_URL,
  credentials: 'include',
  // Dos cosas en una línea: el timeout de 15 s sin perder la cancelación de TanStack Query, y
  // globalThis.fetch leído en cada llamada — openapi-fetch lo guarda al crear el cliente, y MSW lo
  // sustituye después (server.listen): sin esto, los tests salen a la red de verdad.
  fetch: (request) =>
    globalThis.fetch(request, { signal: AbortSignal.any([request.signal, AbortSignal.timeout(15_000)]) }),
});
fetchClient.use(errorsAsApiError);

export const $api = createClient(fetchClient);
```

```tsx
// en un componente: la ruta y la forma de `data` salen del contrato
const { data, isPending, isError } = $api.useQuery('get', '/api/orders/');
const crear = $api.useMutation('post', '/api/orders/');   // crear.mutate({ body: { … } })
```

**Probado el 2026-10-21** en un proyecto de prueba (`_archive/2026-10-20/medicion-2.18/`): `tsc` en
verde, y con Vitest 5 + MSW 3 el 400 con el sobre `{errors}` llega como `ApiError` con
`fields.customer`, el 401 llama a la conducta de sesión caducada y el 500 al aviso global. Dos cosas
que solo salieron al probarlo, y por eso van escritas:

- **Sin la línea de `fetch:` los tests no pasan por MSW.** openapi-fetch guarda `globalThis.fetch` al
  crear el cliente (`fetch: baseFetch = globalThis.fetch`), antes de que `server.listen()` lo
  sustituya: la petición sale a la red y el componente pinta su estado de error. `fetch()` suelto sí
  lo interceptaba, así que el fallo no se ve hasta usar el cliente.
- **Sin `COMPONENT_SPLIT_REQUEST` (paso 1) el `POST` no compila**: el cuerpo exige `id` y `created_at`,
  que son de solo lectura. Es el mismo aviso del paso 1, ahora con el error de `tsc` delante.

**Lo que no cambia todavía: el molde de `nueva-pantalla`.** Sus ficheros ② y ④
(`frontend-nueva-pantalla.md`) siguen sobre `recursoApi()` y `request<T>`. En un proyecto con `$api`,
esos dos se escriben con `$api.useQuery` / `$api.useMutation` y las claves de caché las pone
openapi-react-query (`['get', '/api/orders/', init]`), así que `invalidateQueries` se llama con esa
clave. Adaptar el molde y el generador es su propia tarea, con sus pruebas. **Un proyecto que ya
existe no se migra por esto** (`rules/refactor-progresivo.md`): el paso 3 sigue valiendo.

### Paso 4 — el que de verdad lo hace cumplir: el CI

Todo lo anterior sirve **solo si alguien regenera**. Lo que convierte esto en un mecanismo es una
línea en el pipeline:

```bash
python manage.py spectacular --file schema.yml
npm run api:types
git diff --exit-code schema.yml src/types/api.d.ts   # ≠0 → el contrato cambió y nadie lo regeneró
```

Si el backend cambió el contrato y el `.d.ts` no se actualizó, **el CI se pone rojo con el diff
delante**. Es el paso más barato de los cuatro y el único que no depende de que nadie se acuerde.

## El antipatrón que sustituye

```ts
// ❌ src/types/api.ts — escrito a mano, mantenido a mano
export interface Order {
  id: string;
  nombre: string;        // ← en el backend se llama `nombre_completo` desde hace tres semanas
  total: number;         // ← el backend lo manda como string: DRF serializa Decimal a texto
}
```

- **El campo renombrado** no rompe nada: compila, pasa los tests y pinta un hueco. Es el fallo más
  caro del frontend precisamente porque *no falla*.
- **`total: number` cuando llega `"12.50"`** es peor todavía: `total.toFixed(2)` revienta en
  ejecución, y solo en las pantallas que formatean. Nadie lo escribió mal a propósito — es que a
  mano se escribe lo que uno *cree* que manda el backend, no lo que manda.
- **Y la trampa de fondo**: esta lista parece documentación y no lo es. Es una afirmación sobre otro
  programa, hecha por alguien que no lo está mirando.

Vale la pena decir de dónde viene esto: **bulletproof-react, la arquitectura de referencia del
patrón, hace exactamente este antipatrón y lo reconoce en un comentario dentro de su propio código**
(*"imaginemos que este fichero se autogenera desde el backend"*). Es una deuda que ellos declaran
porque no tenían un backend propio con el que hablar. Nosotros sí.

## Cómo se comprueba

```bash
python3 .claude/patterns/stack/pattern_check_frontend.py --all frontend/src --only api
```

| id | estado | ámbito | qué detecta |
|---|---|---|---|
| `fe-contrato-generado` | débil | **proyecto** | hay backend Django (`manage.py`) y **no** hay ningún fichero de tipos generado en el árbol; o lo hay pero **sin script `api:types`** que lo regenere |

Solo dispara **donde el backend es nuestro**: la regla busca un `manage.py` en la raíz del
repositorio (o en `backend/`, `api/`, `server/`, `src/`) y calla si no lo encuentra. Contra una API
de terceros no hay ningún esquema que podamos regenerar, y el aviso sería ruido en cada escaneo.

El fichero generado se reconoce por la **cabecera** que escribe el generador (`@generated`,
`auto-generated`, `DO NOT EDIT`), no por su nombre: el proyecto puede llamarlo como quiera.

Es de **proyecto**, así que solo corre con `--all` — desde un diff de dos ficheros no se puede
afirmar que al proyecto le falta algo.

**Lo que NO se comprueba, y es bastante:**

- **Que el `.d.ts` esté al día con el backend.** Eso no lo puede saber un comprobador estático: hace
  falta ejecutar los dos comandos y comparar, que es exactamente el paso 4. **El gate real de esta
  página es el CI, no esta regla** — la regla solo verifica que el mecanismo existe.
- **Que los tipos generados se usen.** Un proyecto puede generar `api.d.ts` y seguir escribiendo sus
  interfaces a mano al lado. Detectarlo pediría resolver imports, y no está hecho.
- **Que la carta describa bien la API.** `drf-spectacular` acierta con los serializers normales y se
  queda corto con los campos calculados (`SerializerMethodField`) y las respuestas montadas a mano:
  ahí hace falta anotarlo (`@extend_schema_field`, `@extend_schema`). Sin la anotación, el tipo sale
  como "cualquier cosa" y no protege de nada. El backend lo comprueba con
  `python manage.py spectacular --fail-on-warn`.

## Excepciones legítimas

- **El backend no es nuestro** (una API de terceros): no hay esquema que regenerar. Si el tercero
  publica un OpenAPI, se puede generar igual desde su URL; si no, los tipos van a mano y **se marca
  la frontera** — este es el sitio donde la validación en ejecución (`api-y-errores.md` §validar la
  respuesta) pasa de recomendable a necesaria.
- **El backend no es Django** (FastAPI, Node): el paso 1 cambia de herramienta y todo lo demás vale
  igual. La regla no disparará porque busca `manage.py`; se documenta y ya.
- **Prototipo de una semana** que se va a tirar: montar esto cuesta un rato y no se amortiza. Se
  escribe la exención con fecha, que es lo que evita que "el prototipo" cumpla dos años.

```json
{ "//": "pattern-exempt: fe-contrato-generado — API de un tercero sin OpenAPI publicado (#512)" }
```

## Related

- `api-y-errores.md` — el cliente único, y la validación de la **respuesta** en ejecución: los tipos
  generados cazan el cambio al compilar, la validación caza el despliegue desalineado
- `frontend-a-prueba-de-errores.md` — por qué esto es nivel 1 y no un aviso más
- `frontend-nueva-pantalla.md` — el molde ya usa estos tipos; una pantalla nueva no declara los suyos
- `backend-serializers.md` — el otro lado de la carta: lo que se anota ahí es lo que llega aquí
- `rules/ai-assistant-risk.md` §dependencias alucinadas — `openapi-typescript` y `drf-spectacular`
  existen y son las de referencia de su ecosistema; verifícalo igual antes de instalar
