# Llamadas a la API y manejo de errores — patrón de casa

> Capa `api` del patrón de casa (React · TypeScript ↔ Django/DRF). Es la frontera donde el front y
> el back se rompen mutuamente: casi todo lo que un usuario percibe como "la app está rota" nace
> aquí. Comprobación: `python3 .claude/patterns/stack/pattern_check_frontend.py --only api`.

## La regla (una frase)

Toda comunicación con el servidor pasa por un único cliente en `src/api/` que impone timeout y
normaliza el error, y **ninguna vista que lea datos remotos se da por escrita hasta que renderiza
sus tres estados: cargando, error y vacío**.

## Implementación de referencia

**El cliente único** — `src/api/client.ts`. Un solo sitio donde viven la URL base, las cabeceras,
el timeout y la traducción de un HTTP no-2xx a una excepción tipada:

```ts
export class ApiError extends Error {
  constructor(readonly status: number, readonly fields: Record<string, string[]> = {}) {
    super(`api ${status}`);
  }
}

const BASE = import.meta.env.VITE_API_URL;
const NON_FIELD = 'non_field_errors';

function normalizeErrors(body: unknown): Record<string, string[]> {
  if (!body || typeof body !== 'object') return {};
  const raw = body as Record<string, unknown>;
  // defensive: el sobre {errors} lo garantiza el EXCEPTION_HANDLER del backend, pero una vista que
  // hace `return Response({...}, 400)` no pasa por el handler — y un endpoint de terceros tampoco.
  const source = (raw.errors ?? raw) as Record<string, unknown>;
  if (typeof source.detail === 'string') return { [NON_FIELD]: [source.detail] };
  return Object.fromEntries(
    Object.entries(source).map(([field, v]) => [field, Array.isArray(v) ? v.map(String) : [String(v)]]),
  );
}

export async function request<T>(path: string, init: RequestInit = {}): Promise<T> {
  const res = await fetch(`${BASE}${path}`, {
    ...init,
    credentials: 'include',
    signal: AbortSignal.timeout(15_000),
    headers: { 'Content-Type': 'application/json', ...init.headers },
  });
  if (res.status === 401) {
    onSesionCaducada();                       // ← conducta 1: ver abajo
    throw new ApiError(401);
  }
  if (!res.ok) {
    const body = await res.json().catch(() => ({}));
    if (res.status >= 500) onErrorDeServidor(res.status);   // ← conducta 2
    throw new ApiError(res.status, normalizeErrors(body));
  }
  return res.status === 204 ? (undefined as T) : res.json();
}
```

**Las dos conductas que hay que escribir a mano** (y que con `axios` venían de regalo). Los
*interceptores* de axios son ganchos que corren en **todas** las peticiones: es lo único que `fetch`
no tiene, y donde la referencia los usa es para exactamente dos cosas. Con `fetch` **nadie te las
regala**: si no se escriben aquí, cada llamada gestiona la sesión caducada a su manera — o no la
gestiona. La decisión de casa no es "fetch o axios", que ya está tomada: es **no olvidar estas dos**.

```ts
// src/api/conductas.ts — dos funciones sueltas, importadas por client.ts
import { router } from '../routes';
import { queryClient } from '../lib/queryClient';
import { notificar } from '../lib/notificaciones';

/** 1) Sesión caducada: se limpia lo del usuario anterior y se manda al login, UNA vez. */
export function onSesionCaducada() {
  queryClient.clear();
  const actual = router.state.location.pathname;
  if (actual !== '/login') {
    router.navigate(`/login?next=${encodeURIComponent(actual)}`);
  }
}

/** 2) El servidor falló: aviso global, porque puede pasar en cualquier pantalla. */
export function onErrorDeServidor(status: number) {
  notificar.error(toUserMessage(new ApiError(status)));
}
```

Tres detalles que parecen menores y no lo son. **La guarda del `pathname`**: sin ella, tres
peticiones que fallan a la vez disparan tres navegaciones y el usuario ve un parpadeo. **El
`queryClient.clear()`**: si no se vacía, al volver a entrar se pinta durante un instante lo que vio
la sesión anterior. Y **`router.navigate` en vez de `window.location`**: recargar la página entera
pierde el estado y vacía la caché "de casualidad" (`rutas.md`).

Se avisa **solo del 5xx**, no de todo error: un 400 de validación ya lo pinta el formulario en sus
campos, y sacar además un aviso global es contar dos veces el mismo problema.

**Quién garantiza el sobre `{errors: …}`, y por qué el cliente no se fía del todo.** El formato es el
contrato de casa (`formularios.md §El contrato con el backend`) y **lo produce el backend** con un
`EXCEPTION_HANDLER` propio — regla `be-api-exception-handler`, activa en el comprobador backend.
**DRF no lo hace por defecto**: de fábrica devuelve dos formas distintas, el nombre del campo a
nivel raíz en los errores de validación (`{"amount": ["A valid integer is required."]}`) y
`{"detail": "…"}` en auth, permisos, 404 y throttling. Un cliente que leyera solo `body.errors`
encontraría `undefined` contra un backend sin ese handler y **no pintaría ningún error**: el
formulario se quedaría quieto al enviar, sin mensaje y sin pista. Por eso `normalizeErrors` acepta
las tres formas. No es desconfianza del backend: el propio DRF documenta que el handler **no se
invoca** cuando una vista devuelve un `Response(..., 400)` directamente, así que el hueco existe
aunque el handler esté bien puesto.

**Un módulo por recurso** — `src/api/orders.ts`. Las claves de caché viven junto al recurso, no
esparcidas por los componentes:

```ts
import { request } from './client';
import type { Order } from '../types/order';

export const ordersApi = {
  list: () => request<Order[]>('/orders/'),
  create: (input: Omit<Order, 'id'>) =>
    request<Order>('/orders/', { method: 'POST', body: JSON.stringify(input) }),
};

export const orderKeys = {
  all: ['orders'] as const,
};
```

**Validar la RESPUESTA, en los endpoints que importan.** Los tipos generados desde el backend
(`frontend-contrato-con-el-backend.md`) cazan el cambio de contrato **al compilar**; esto caza el
otro caso, que ningún compilador ve: **el despliegue desalineado**. El frontend nuevo ya está en el
navegador del usuario y el backend todavía es el de ayer —o al revés— y lo que llega no es lo que el
tipo dice. TypeScript ya no está ahí para mirarlo: en ejecución, `Promise<Order>` es una promesa que
el compilador se creyó.

```ts
import { z } from 'zod';

const OrderResponseSchema = z.object({
  id: z.string(),
  reference: z.string(),
  amount: z.coerce.number(),     // DRF serializa Decimal como texto: coerce lo convierte aquí
});

export const ordersApi = {
  // ✅ endpoint crítico: si el contrato no encaja, falla AQUÍ, con el nombre del campo
  detalle: async (id: string) =>
    OrderResponseSchema.parse(await request<unknown>(`/orders/${id}/`)),

  // el listado de un desplegable no lo necesita: coste en cada render y poco que perder
  opciones: () => request<Etiqueta[]>('/orders/options/'),
};
```

**Qué es "crítico"** — y es una decisión de persona, no una regla: donde el dato **se escribe, se
cobra o se decide**. Un importe, un estado de pedido, un permiso. **Dónde no**: listados de solo
lectura, catálogos y desplegables; ahí el coste de parsear cada elemento en cada carga no compra
nada, porque el peor caso es una etiqueta rara en pantalla.

Sin esto, el desajuste no revienta donde entra el dato: viaja tres pantallas hacia dentro y aparece
como `undefined` en un `.toFixed()`, con un stack trace que no menciona ni la API ni el campo.

Un detalle del `z.coerce.number()`: es el punto donde se arregla, en un sitio, la conversión que si
no acaba repetida en cada componente que formatea un importe.

**La traducción del error** — `src/api/errors.ts`. Lo que ve el usuario nunca es lo que dijo el
servidor:

```ts
export function toUserMessage(error: unknown): string {
  if (error instanceof ApiError) {
    if (error.status === 404) return 'No encontramos lo que buscabas.';
    if (error.status === 403) return 'No tienes permiso para ver esto.';
    if (error.status >= 500) return 'El servidor falló. Reintenta en un momento.';
  }
  return 'Algo no ha ido bien. Reintenta en un momento.';
}
```

**La vista, con los tres estados** — `src/components/OrderList.tsx`:

```tsx
import { useQuery } from '@tanstack/react-query';
import { ordersApi, orderKeys } from '../api/orders';
import { toUserMessage } from '../api/errors';

export function OrderList() {
  const { isPending, isError, error, data } = useQuery({
    queryKey: orderKeys.all,
    queryFn: ordersApi.list,
  });

  if (isPending) return <ListSkeleton rows={5} />;
  if (isError) return <ErrorState message={toUserMessage(error)} />;
  if (data.length === 0) return <EmptyState title="Aún no hay pedidos" />;

  return (
    <ul>
      {data.map((order) => (
        <li key={order.id}>{order.reference}</li>
      ))}
    </ul>
  );
}
```

Los nombres de los flags son los de **TanStack Query v5**, no los de v4: `status: 'loading'` pasó a
`'pending'` y el antiguo `isLoading` es hoy `isPending`. En v5 existe **además** un `isLoading`
distinto, que significa `isPending && isFetching` — usarlo para pintar el esqueleto inicial es un
error silencioso: en un refetch de fondo con datos ya en caché vale `true` y la lista parpadea.
El orden de las tres guardas no es cosmético: es lo que permite a TypeScript estrechar `data` y
que la última línea compile sin `data?.` ni `!`.

**El tercero se llama desde el backend, no desde el navegador.** El cliente único de arriba habla
con **nuestra** API (`VITE_API_URL`) y con nadie más. Cuando entra un servicio de terceros —un CRM,
una pasarela, un proveedor de mensajería— la tentación es llamarlo directamente desde el front,
porque son diez líneas y funciona a la primera. Lo que se lleva por delante es la credencial:

```ts
// ❌ src/services/crmApi.ts — la clave está en el bundle, o sea, en el navegador de cualquiera
const CRM_KEY = import.meta.env.VITE_CRM_API_KEY;
await fetch(`${CRM_BASE}/contacts/`, { headers: { Authorization: `Bearer ${CRM_KEY}` } });
```

**Todo lo que empieza por `VITE_` se incrusta en el paquete que se descarga el navegador.** No es
una variable de servidor con nombre raro: es texto que se lee con el inspector abierto, en tres
clics, desde cualquier ordenador del mundo. Un `.env` fuera de git no cambia nada — el valor entra
en el JavaScript al construir. Y una clave de CRM en el bundle no es «un secreto de poca
importancia»: da acceso de lectura y escritura a la base de contactos entera.

```ts
// ✅ el front llama a NUESTRO backend; la clave del tercero vive donde el usuario no llega
export const leadsApi = {
  crear: (input: NuevoLead) =>
    request<Lead>('/leads/', { method: 'POST', body: JSON.stringify(input) }),
};
```

Tres cosas más que se ganan al pasar por el backend, y que no son el motivo pero pesan: el tercero
caído **no rompe el formulario** (la vista guarda el lead y el envío se reintenta en una tarea, ver
`backend-celery.md`), el consentimiento y la base legal quedan del lado en que se pueden demostrar
(es lo que audita `priya-privacy-auditor`), y cambiar de proveedor deja de tocar el frontend.

> **Medido en el corpus:** las **4** variables `VITE_*` que existen en los tres frontends son URLs
> —`VITE_API_URL`, `VITE_API_BASE_URL` (×2) y `VITE_WS_BASE_URL`—. Ninguna es una credencial. La
> regla no está pidiendo un cambio de costumbre: está fijando la que ya hay, antes de que la
> primera integración con prisa la rompa.

## El antipatrón que sustituye

```tsx
// ❌ src/components/OrderList.tsx
export function OrderList() {
  const [orders, setOrders] = useState([]);

  useEffect(() => {
    fetch('/api/orders')
      .then((r) => r.json())
      .then(setOrders);
  }, []);

  return <ul>{orders.map((o) => <li key={o.id}>{o.reference}</li>)}</ul>;
}
```

Catorce líneas inocentes con seis fallos que se pagan en producción:

1. **La URL base y las cabeceras se duplican** por cada componente que llame a la red. El día que
   entra la autenticación hay que tocar treinta ficheros y se olvidan tres.
2. **No hay estado de error.** Si el servidor devuelve 500, `r.json()` revienta con un
   `SyntaxError` sobre el HTML de error, la promesa queda rechazada sin `catch` y el usuario se
   queda mirando una lista vacía para siempre. Indistinguible de "no tienes pedidos".
3. **No hay estado de carga**, así que la primera pintada muestra la lista vacía y luego salta.
4. **No hay estado vacío**: "aún no has hecho ningún pedido" y "no hemos podido cargar tus
   pedidos" se ven exactamente igual. El usuario reintenta lo que no falla y abandona lo que sí.
5. **No hay timeout.** Una petición que nunca resuelve deja el componente cargando eternamente;
   sin `AbortSignal.timeout` no hay nada que la corte.
6. **No hay cancelación**: si el componente se desmonta antes de que responda, se hace `setState`
   sobre un componente muerto, y con dos montajes seguidos gana la respuesta que llegue última —
   no la última que se pidió.

El otro antipatrón, más difícil de ver porque parece que sí maneja el error:

```tsx
if (isError) return <p>Error: {error.message}</p>;   // ❌
```

`error.message` no es un texto para humanos. Según lo que haya fallado puede ser
`"Failed to fetch"`, `"Unexpected token '<'"`, un stack trace, o el cuerpo entero del 500 de
Django con rutas del servidor dentro. Es a la vez incomprensible para el usuario y una fuga de
información sobre el backend.

## Cómo se comprueba

```bash
python3 .claude/patterns/stack/pattern_check_frontend.py --only api      # ficheros cambiados
python3 .claude/patterns/stack/pattern_check_frontend.py --all src --only api   # todo el árbol
```

| id | estado | qué detecta |
|---|---|---|
| `fe-http-en-capa-api` | activo | `fetch(`/`axios`/`XMLHttpRequest` en componentes, hooks o stores |
| `fe-tres-estados` | activo | fichero con `useQuery` que no menciona `isPending`/`Suspense` o `isError`/`ErrorBoundary` |
| `fe-estado-vacio` | débil | `.map(` sobre datos remotos sin ninguna rama de lista vacía |
| `fe-error-no-silencioso` | activo | `catch` vacío o que solo hace `console.*` (con parseo de llaves balanceadas, no grep de línea) |
| `fe-error-traducido` | activo | `{error.message}` interpolado en JSX, **solo** en ficheros que hablan con la red |
| `fe-timeout-obligatorio` | activo | fichero de `src/api/` que hace `fetch(` sin `AbortSignal.timeout` |
| `fe-mutacion-invalida-cache` | débil | `useMutation` sin `invalidateQueries`/`setQueryData`/`refetch` |
| `fe-401-en-el-cliente` | activo | el fichero que construye la petición base (el que llama a `fetch`) no menciona el 401 en ninguna parte |
| `fe-esquema-de-respuesta-usado` | débil | un `…ResponseSchema` declarado en la capa de API y no referenciado en ningún otro sitio del módulo |
| `fe-contrato-generado` | débil | **proyecto**: hay backend Django y ningún fichero de tipos generado (`frontend-contrato-con-el-backend.md`) |
| `fe-credencial-en-el-bundle` | activo | `import.meta.env.VITE_*` (o `NEXT_PUBLIC_*`/`REACT_APP_*`) cuyo nombre acaba en `KEY`/`TOKEN`/`SECRET`/`PASSWORD`/`CREDENTIAL`/`AUTH` |

`fe-estado-vacio` es **débil** a propósito: detecta la ausencia de una rama para lista vacía por
heurística (`.length === 0`, `!x.length`, `<Empty`), y hay vistas legítimas donde la lista vacía no
necesita mensaje. Avisa, no bloquea.

`fe-mutacion-invalida-cache` cubre el bug más repetido del CRUD: el usuario crea algo, la petición
va bien, y la lista sigue enseñando lo de antes porque nadie invalidó la clave. Es **débil** porque
una mutación que navega a otra pantalla no necesita invalidar nada.

`fe-error-traducido` solo mira ficheros que mencionan `useQuery`, `useMutation`, `isError` o
`ApiError`. La acotación es deliberada: en un formulario, `{error.message}` suele ser el mensaje de
validación de zod, que **sí** está escrito para el usuario. Sin ese filtro la regla marcaría
formularios correctos y acabaría desactivada por ruido.

`fe-401-en-el-cliente` solo mira el fichero que **construye la petición base** (el que llama a
`fetch`), no los módulos por recurso, que usan `request()` y no tienen por qué hablar de códigos de
estado. Busca la cadena `401`, así que **no comprueba que la conducta sea correcta**: un
`if (res.status === 401) {}` vacío pasaría. Verifica que alguien decidió, no que decidiera bien.

`fe-esquema-de-respuesta-usado` cubre el fallo tonto y frecuente del apartado anterior: alguien
escribe el esquema, se lo lleva la revisión, y **nadie lo aplica** — con lo que el endpoint parece
cubierto y no lo está. Da por bueno cualquier referencia posterior al nombre, porque el uso real
casi nunca es `Schema.parse(…)` a secas (`Schema.array().parse(…)`, `z.infer<typeof Schema>`). Lo
que **no** puede ver: si el esquema se exporta y se aplica en **otro** módulo. Y sobre todo, **no
comprueba que los endpoints críticos estén cubiertos**: cuáles son es criterio de persona, y ningún
grep lo sabe.

`fe-credencial-en-el-bundle` es la hermana frontend de `be-env-secreto-literal`, y comparte con
ella el mismo límite: **detecta por el nombre de la variable**. Una credencial guardada en
`VITE_AJUSTE_7` se le escapa, igual que en el backend. A cambio no tiene falsos positivos: sobre
los 3 frontends del corpus da **0 hallazgos**, porque ahí todas las `VITE_*` son URLs. Lo que
tampoco puede ver: la clave escrita a pelo en el código, sin pasar por ninguna variable de entorno
— para eso está el barrido genérico de secretos (`rules/security.md`).

Refuerzo opcional en ESLint, si el proyecto instala `@tanstack/eslint-plugin-query`:
`@tanstack/query/exhaustive-deps` y `@tanstack/query/no-rest-destructuring` (esta última evita
`const { ...rest } = useQuery()`, que rompe el seguimiento de propiedades usadas y provoca
re-renders de más).

## Excepciones legítimas

- **Health-check o ping del arranque** que corre antes de que exista el `QueryClient`: puede usar
  `fetch` directo, pero sigue yendo en `src/api/`.
- **Streaming / SSE / long-polling**, donde un timeout fijo mata la conexión por diseño. Es la
  excepción real a `fe-timeout-obligatorio`.
- **Superficies de diagnóstico** (una página `/debug` interna, un panel de error solo para
  desarrollo) donde mostrar el `error.message` crudo es justamente el objetivo.
- **Una clave de tercero que es pública por diseño** (la clave publicable de una pasarela de pago,
  el token de un mapa acotado por dominio). Ahí el bundle es su sitio, y la exención lo dice:
  `// pattern-exempt: fe-credencial-en-el-bundle — clave publicable de Stripe, acotada por dominio`.
  Lo que no vale es asumirlo: si el proveedor no documenta esa clave como pública, no lo es.
- **Un cliente contra una API pública sin sesión** (un mapa, un servicio de códigos postales): ahí
  no hay 401 que gestionar. La exención va en ese cliente, no en el de casa.

Se documentan en el propio fichero, y Rita y el checker las respetan siempre:

```ts
// pattern-exempt: fe-timeout-obligatorio — SSE: la conexión es larga por diseño (ticket #412)
```

## Related

- `frontend-contrato-con-el-backend.md` — de dónde salen los tipos de lo que devuelve la API: los
  tipos generados cazan el cambio al compilar, la validación de respuesta caza el despliegue
  desalineado
- `frontend-auth.md` — qué pasa después del 401: la cookie, los tres hooks y el vaciado de caché
- `frontend-a-prueba-de-errores.md` — `<Asincrono>`: los tres estados como props obligatorias
- `formularios.md` — el contrato del 400 y el mapeo a errores de campo · `estado.md` · `rutas.md`

Una excepción sin razón escrita no es una excepción, es una violación con comentario.
