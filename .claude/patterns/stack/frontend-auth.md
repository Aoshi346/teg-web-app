# Sesión de usuario — cookie del backend y tres hooks propios

> Capa `auth` del patrón de casa (React ↔ Django/DRF). Es la capa más pequeña que se hace mal más
> veces: casi todo el frontend guarda el token donde no debe y cierra sesión a medias.
> Comprobación: `python3 .claude/patterns/stack/pattern_check_frontend.py --only auth`.

## La regla (una frase)

La sesión vive en una **cookie `HttpOnly` que emite el backend** —el frontend nunca ve ni guarda un
token—, y `useUser` / `useLogin` / `useLogout` son **tres hooks propios sobre TanStack Query**, no
una dependencia.

## Implementación de referencia

**Qué es una cookie `HttpOnly`.** Una cookie normal la puede leer el JavaScript de la página
(`document.cookie`); una `HttpOnly`, no: el navegador la guarda, la manda en cada petición al
dominio que la puso, y **el código de la página no tiene forma de leerla**. Eso es justamente lo que
la hace buena para una sesión: si un script malicioso entra en la página —el tuyo con un fallo, o
una dependencia comprometida— puede hacer peticiones en nombre del usuario mientras esté en la
página, pero **no puede llevarse la sesión** para usarla desde otro sitio.

El frontend solo tiene que hacer una cosa: mandar las credenciales en cada petición. Ya está en el
cliente único (`api-y-errores.md`):

```ts
const res = await fetch(`${BASE}${path}`, { ...init, credentials: 'include', /* … */ });
```

### Los dos montajes con DRF, y cuál elegir

| Montaje | Cuándo | Qué añade en el frontend |
|---|---|---|
| **Sesión de Django** (`SessionAuthentication`) | front y back en el **mismo dominio** (lo normal en nuestros proyectos) | mandar la cabecera `X-CSRFToken` en POST/PUT/PATCH/DELETE |
| **SimpleJWT en cookie `HttpOnly`** | dominios distintos, o hace falta un token para otro consumidor | refresco del token, que hace el backend en su endpoint |

Se prefiere la **sesión de Django** cuando se puede: es lo que DRF trae de fábrica, el borrado en
servidor es real (cerrar sesión invalida de verdad) y no hay que decidir caducidades. El detalle
que sorprende: con sesión, DRF **exige CSRF** en los métodos que escriben, así que hay que leer la
cookie `csrftoken` —esta sí es legible a propósito— y devolverla como cabecera:

```ts
// src/api/csrf.ts
export function csrfToken(): string {
  return document.cookie.match(/(?:^|;\s*)csrftoken=([^;]+)/)?.[1] ?? '';
}
```

Sin eso, el primer POST responde 403 con un mensaje sobre CSRF y se pierde media tarde buscándolo en
el sitio equivocado.

### Los tres hooks — unas 40 líneas, y no hace falta más

```ts
// src/api/auth.ts
import type { components } from '../types/api';
import { request } from './client';

export type Usuario = components['schemas']['User'];

export const authApi = {
  yo: () => request<Usuario>('/auth/me/'),
  entrar: (datos: { email: string; password: string }) =>
    request<Usuario>('/auth/login/', { method: 'POST', body: JSON.stringify(datos) }),
  salir: () => request<void>('/auth/logout/', { method: 'POST' }),
};

export const authKeys = { yo: ['auth', 'yo'] as const };
```

```ts
// src/features/auth/useAuth.ts
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { authApi, authKeys } from '../../api/auth';

/** Quién está dentro. `null` = nadie: un 401 aquí es una respuesta válida, no un error. */
export function useUser() {
  return useQuery({
    queryKey: authKeys.yo,
    queryFn: authApi.yo,
    retry: false,          // sin esto, TanStack Query reintenta 3 veces el 401 del visitante anónimo
    staleTime: 5 * 60_000,
  });
}

export function useLogin() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: authApi.entrar,
    // setQueryData y no invalidate: el login YA devolvió el usuario, pedirlo otra vez sobra
    onSuccess: (usuario) => queryClient.setQueryData(authKeys.yo, usuario),
  });
}

export function useLogout() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: authApi.salir,
    // clear() y no removeQueries(authKeys.yo): al salir se va TODO lo que se cargó con esa sesión
    onSuccess: () => queryClient.clear(),
  });
}
```

Eso es la capa entera. **Por qué no `react-query-auth`** —que es lo que usa bulletproof-react, del
mismo autor del repo—: es una dependencia fina de un solo mantenedor para código que cabe en un
fichero, y con DRF su configuración no encaja tal cual. Acabarías configurando el paquete para
ahorrarte estas cuarenta líneas.

### El 401 se trata en el cliente, no en cada hook

Cuando la sesión caduca a media sesión de trabajo, la respuesta es 401 en cualquier petición, no
solo en las de auth. Eso se resuelve **una vez** en `src/api/client.ts` (`api-y-errores.md`
§las dos conductas): limpiar el estado de sesión y mandar al login. Si cada hook lo hiciera por su
cuenta, habría veinte sitios que mantener y diecinueve se olvidarían.

## El antipatrón que sustituye

```ts
// ❌ src/features/auth/useAuth.ts
export async function login(email: string, password: string) {
  const { access_token } = await authApi.login(email, password);
  localStorage.setItem('access_token', access_token);   // ①
}

export function logout() {
  localStorage.removeItem('access_token');              // ②
  window.location.href = '/login';                      // ③
}
```

- **① El token en `localStorage`** lo puede leer **cualquier** script que corra en la página: el
  tuyo, el del chat de soporte, el de analítica, o una dependencia que alguien comprometió el mes
  pasado. Un solo XSS deja de ser "pintan algo raro en una pantalla" y pasa a ser "se llevan la
  sesión y la usan desde su ordenador". Con `HttpOnly` ese robo no está disponible.
- **② El logout que solo borra el token** no cierra nada en el servidor: si alguien copió el token
  antes, **sigue valiendo hasta que caduque**. Con sesión de Django, el logout la invalida de verdad.
- **③ El `window.location.href`** recarga la aplicación entera, y con eso la caché de queries se va
  "de casualidad". Funciona por accidente: el día que alguien lo cambie por un `navigate()` —que es
  lo correcto según `rutas.md`— la caché sobrevive, y **la siguiente persona que entre en ese
  navegador verá durante un instante los datos del anterior**. En un ordenador compartido (una
  recepción, un taller, un aula) eso no es un detalle.

## Cómo se comprueba

```bash
python3 .claude/patterns/stack/pattern_check_frontend.py --only auth
python3 .claude/patterns/stack/pattern_check_frontend.py --all frontend/src --only auth
```

| id | estado | qué detecta |
|---|---|---|
| `fe-token-no-en-localstorage` | activo | `localStorage.setItem(…)` / `sessionStorage.setItem(…)` con una clave que contenga `token`, `jwt`, `access`, `refresh` o `auth` |
| `fe-logout-limpia-cache` | débil | un fichero que **define** un logout y no llama a `queryClient.clear()` / `removeQueries` / `resetQueries` |

`fe-token-no-en-localstorage` mira **el nombre de la clave**, que es lo único observable sin
entender el programa. Guardar el token bajo una clave que no lo parezca (`localStorage.setItem('k',
t)`) se le escapa — y no hay forma barata de arreglarlo; queda para la revisión.

`fe-logout-limpia-cache` es **débil** porque hay dos formas legítimas de no llamar a `clear()`: que
el logout provoque una recarga completa (que vacía la memoria de todas formas) o que el proyecto no
use TanStack Query. Avisa, no bloquea.

**Lo que NO se comprueba:**

- **Que la cookie sea de verdad `HttpOnly`.** Eso lo decide el backend al emitirla y solo se ve
  mirando la respuesta (`Set-Cookie: …; HttpOnly; Secure; SameSite=Lax`). Un análisis estático del
  frontend no lo alcanza; lo comprueba `sofia-pentester` o un `curl -i` al endpoint de login.
- **Que el CSRF esté puesto** donde hace falta. Se descubre al primer POST, con un 403 explícito —
  es de los pocos fallos de esta página que avisan solos.
- **Que el backend invalide la sesión al salir.** Es del lado de allá (`backend-vistas.md`).

## Excepciones legítimas

- **Cliente que no es un navegador** (app móvil, script, herramienta de escritorio): ahí no hay
  cookies de navegador y el token vive en el almacén seguro del sistema. Esta página no aplica.
- **SSO de terceros** que devuelve el token en la URL de vuelta: el token entra por JavaScript sí o
  sí; lo correcto es **canjearlo por la cookie de sesión inmediatamente** y no guardarlo. La
  exención cubre esa línea concreta, no el patrón entero.
- **Impersonación / soporte** con un token de corta vida para depurar: se acota y se escribe.

```ts
// pattern-exempt: fe-token-no-en-localstorage — canje del token del SSO por la cookie de sesión;
// se borra en la línea siguiente y nunca se persiste (#488)
```

## Related

- `api-y-errores.md` — el cliente único, `credentials: 'include'` y el 401 tratado una sola vez
- `frontend-a-prueba-de-errores.md` — por qué la cookie `HttpOnly` es nivel 1: quita el dato de en medio
- `rutas.md` — la redirección al login se hace con el router, no con `window.location`
- `estado.md` — el usuario es **estado de servidor**: vive en la caché de queries, no en el store
- `rules/security.md` · agente `sofia-pentester` — el lado que sí puede comprobar la cookie
