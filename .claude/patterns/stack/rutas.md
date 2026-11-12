# Rutas — patrón de casa

> Capa `rutas` del patrón de casa (react-router 7). Es la capa más pequeña del catálogo y la que
> produce el fallo más visible cuando se hace mal: la pantalla en blanco.
> Comprobación: `python3 .claude/patterns/stack/pattern_check_frontend.py --only rutas`.

## La regla (una frase)

Todas las rutas se declaran en **un** módulo, la raíz tiene siempre un `ErrorBoundary`, y la
navegación dentro de la app se hace con `<Link>` o `useNavigate()` — nunca con `<a href>` ni con
`window.location`.

## Implementación de referencia

**Qué hace un router y por qué importa.** Esta app es una *SPA*: el navegador carga la página una
sola vez y a partir de ahí el JavaScript va cambiando lo que se ve sin volver a pedir el documento
al servidor. El router es lo que traduce la URL a la pantalla que toca. Si la navegación se sale de
él —por ejemplo con un enlace HTML normal—, el navegador recarga todo y se pierde lo que había en
memoria: la sesión en curso, el formulario a medias y toda la caché de datos.

**react-router 7 se puede usar de tres formas** (declarativa, *data* y como framework completo). El
canon de casa es la **data**: las rutas son un array de objetos que se le pasa a
`createBrowserRouter`. Se elige esa porque es la única de las tres que da `ErrorBoundary` por ruta y
carga diferida sin montar nada más; la forma declarativa (`<Routes>` dentro del JSX) es más simple
pero no los tiene, y el modo framework trae además servidor y compilación propios, que en un
proyecto con backend Django sobran.

```tsx
// src/routes.tsx  — el único sitio donde se declara una ruta
import { createBrowserRouter } from 'react-router';
import { RootLayout } from './components/RootLayout';
import { RootErrorBoundary } from './components/RootErrorBoundary';

export const router = createBrowserRouter([
  {
    path: '/',
    Component: RootLayout,
    ErrorBoundary: RootErrorBoundary,
    children: [
      { index: true, lazy: () => import('./pages/Home') },
      { path: 'orders', lazy: () => import('./pages/Orders') },
      { path: 'orders/:orderId', lazy: () => import('./pages/OrderDetail') },
      { path: '*', Component: NotFound },
    ],
  },
]);
```

`lazy` es **carga diferida**: el código de esa pantalla no viaja en el paquete inicial, se descarga
la primera vez que alguien entra. Sin ella, quien abre el login se descarga también el panel de
administración que no va a ver nunca. Cuesta una línea por ruta.

`Component` y `ErrorBoundary` son la forma moderna, y **tienen prioridad** sobre las antiguas
`element` y `errorElement` si aparecen las dos. Se prefieren porque aceptan la referencia al
componente en vez de un elemento JSX ya construido, que es lo que permite que `lazy` funcione
limpio.

**El `ErrorBoundary`** — `src/components/RootErrorBoundary.tsx`. Es la red que evita la pantalla en
blanco: cuando algo falla al cargar o al pintar una ruta, react-router renderiza esto en lugar de
dejar el árbol vacío.

```tsx
import { useRouteError, isRouteErrorResponse, Link } from 'react-router';

export function RootErrorBoundary() {
  const error = useRouteError();

  if (isRouteErrorResponse(error) && error.status === 404) {
    return <ErrorState title="No encontramos esta página" action={<Link to="/">Volver al inicio</Link>} />;
  }
  return <ErrorState title="Algo no ha ido bien" action={<Link to="/">Volver al inicio</Link>} />;
}
```

`isRouteErrorResponse` distingue un error que el router sabe describir (un 404, un 403) de una
excepción cualquiera. Lo que **no** se hace aquí es pintar `error.message` ni el stack: es la misma
regla de `api-y-errores.md` (`fe-error-traducido`) — ese texto no está escrito para el usuario y
puede filtrar rutas del servidor.

**La navegación:**

```tsx
import { Link, useNavigate } from 'react-router';

<Link to="/orders">Pedidos</Link>                        // ✅ el 99% de los casos
<Link to={`/orders/${order.id}`}>{order.reference}</Link>

const navigate = useNavigate();                          // ✅ cuando navega el código, no un clic
await ordersApi.create(values);
navigate(`/orders/${created.id}`, { replace: true });
```

`<Link>` renderiza un `<a>` de verdad por debajo, así que sigue funcionando el clic con botón
central, el "abrir en pestaña nueva" y el menú contextual — pero intercepta el clic normal para
navegar sin recargar. Es la razón por la que no vale "poner un `<a>` y ya".

## El antipatrón que sustituye

```tsx
// ❌ src/components/Sidebar.tsx
export function Sidebar() {
  return (
    <nav>
      <a href="/orders">Pedidos</a>
      <a href="/settings">Ajustes</a>
      <Route path="/reports" element={<Reports />} />
      <button onClick={() => (window.location.href = '/profile')}>Mi perfil</button>
    </nav>
  );
}
```

```tsx
// ❌ src/main.tsx
const router = createBrowserRouter([{ path: '/', Component: App }]);
```

- **`<a href="/orders">`** recarga la aplicación entera. Se nota: parpadeo en blanco, el esqueleto
  de carga otra vez en cada pantalla, y la caché de TanStack Query vacía, así que todo lo que ya
  estaba descargado se vuelve a pedir. Es el bug que más veces se cuela porque *parece* que
  funciona — lleva a la página correcta, solo que por el camino largo.
- **`window.location.href = …`** es lo mismo con peor disfraz, y además rompe el botón "atrás".
- **Una `<Route>` suelta en un componente** hace imposible responder "¿qué URLs tiene esta app?" sin
  leerla entera. Y en el modo data ni siquiera hace nada: es marcado muerto que aparenta funcionar.
- **El router sin `ErrorBoundary`** es el que produce el peor síntoma de todos: una pantalla
  completamente en blanco, sin mensaje, sin botón y sin nada que copiar para reportar el fallo. El
  usuario no distingue eso de "internet no va" y recarga hasta que se rinde.

## Cómo se comprueba

```bash
python3 .claude/patterns/stack/pattern_check_frontend.py --only rutas
```

| id | estado | qué detecta |
|---|---|---|
| `fe-enlace-interno-con-link` | activo | `<a href="/…">` con ruta interna literal, salvo que lleve `target`, `download` o `rel="…external…"` |
| `fe-error-boundary-de-ruta` | activo | fichero con `createBrowserRouter(` y sin ningún `ErrorBoundary` ni `errorElement` |
| `fe-rutas-en-un-sitio` | débil | `<Route` en un componente que no es el módulo de rutas (`routes.tsx`, `App.tsx`, `main.tsx`, `root.tsx` o cualquier cosa bajo `routes/`) |

`fe-enlace-interno-con-link` solo mira **rutas literales que empiezan por una barra**. Un
`href="https://…"` es externo y correcto; `href="//cdn…"` también; `href="#seccion"` es un ancla de
la misma página. Y si el enlace lleva `target="_blank"` o `download`, abrir fuera de la SPA es
justo la intención, así que no se reporta. Un `href={variable}` no se reporta tampoco — el
comprobador no puede saber a dónde apunta.

`fe-error-boundary-de-ruta` mira el fichero, no el árbol de rutas: le basta con que aparezca un
`ErrorBoundary` en el módulo del router. Es a propósito — comprobar que **cada** ruta anidada tiene
el suyo exigiría interpretar el array, y además no es la regla: con uno en la raíz, todo lo de
debajo queda cubierto.

**Lo que NO tiene comprobación mecánica, y por qué:**

- **Que las rutas privadas estén protegidas.** Es la regla más importante de esta capa y no hay
  forma honesta de comprobarla con texto: saber si `/admin` exige sesión implica seguir qué
  componente envuelve a qué ruta y qué hace ese componente. Un grep de `RequireAuth` solo
  comprobaría que alguien escribió esa palabra. **Se queda declarada sin regla**, y quien la
  verifica es una persona en la revisión — o `sofia-pentester`, que sí la prueba pidiendo la URL sin
  sesión, que es la única comprobación que vale. Recuerda además que el guardia del cliente es
  comodidad: **quien decide de verdad es el backend** (`backend-vistas.md`), porque cualquiera puede
  pedir la API sin pasar por la pantalla.
- **Que el destino de un `href` dinámico sea seguro.** Un `href={item.url}` con un valor que empiece
  por `javascript:` ejecuta código al hacer clic. El caso literal lo caza la regla de ESLint
  `react/jsx-no-script-url`; el caso con variable no lo caza nadie estáticamente. La defensa es
  validar el esquema al recibir el dato (`saneado.md`).
- **Que no haya rutas huérfanas** (declaradas y nunca enlazadas, o enlazadas y no declaradas).
  Requeriría cruzar el array de rutas con todos los `to=` del repo; se puede hacer, no está hecho.

## Excepciones legítimas

- **Salir de la SPA a propósito**: descargar un fichero que sirve el backend, ir al panel de
  administración de Django, cerrar sesión con una redirección del servidor. Ahí el `<a href>` (o
  `window.location`) es lo correcto, y normalmente lleva ya `download` o `target`.
- **Un proyecto con framework** (Next.js, Remix, TanStack Start) que trae su propio router y sus
  propios componentes de enlace. Este documento entero no aplica; se anota en el `CLAUDE.md` del
  proyecto.
- **Correos, enlaces externos y anclas** — no los reporta la regla, no hacen falta exenciones.
- **Rutas declarativas (`<Routes>`) en una app pequeña** que de verdad no necesita ni carga diferida
  ni errores por ruta. Es una decisión de arquitectura y va en el plan, no en un comentario suelto.

```tsx
// pattern-exempt: fe-enlace-interno-con-link — /accounts/logout/ lo sirve Django, debe recargar
```

## Related

- `frontend-stack.md` (por qué react-router 7) · `api-y-errores.md` (el error que no se enseña
  crudo) · `componentes.md` (`pages/` compone, no implementa) · `saneado.md` (URLs que vienen de
  datos) · `backend-vistas.md` (quien decide de verdad los permisos)
