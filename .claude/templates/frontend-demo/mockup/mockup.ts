import { getResponse } from "msw";
import { handlers } from "./handlers";

/**
 * LA MAQUETA de la demo (`VITE_MOCKUP=1` en el build): el frontend entero se enseña antes de que
 * exista su backend, con los mismos handlers de MSW que usan los tests (fichero ⑩ del molde de
 * `nueva-pantalla`, rules/motores-de-diseno.md §F3).
 *
 *  - El login, la sesión y el CSRF (`/api/auth/`) van SIEMPRE a la API real: la demo se enseña con
 *    usuarios de verdad, no con un usuario simulado que salta la pantalla de entrada.
 *  - Lo que ya tiene backend (CONNECTED_PREFIXES) también va a la API real, aunque tenga handler: así
 *    se conecta dominio a dominio, y las pantallas hablan el mismo contrato.
 *  - Lo que no tiene handler, a la API real (como `onUnhandledRequest: 'bypass'`).
 *  - SIN el service worker de MSW: se sustituye `fetch` solo para esas rutas. Si la app es PWA, su
 *    service worker ocupa el mismo ámbito (`/`) y los dos se pelean.
 *
 * Se enciende en main.tsx, antes de montar la app y solo si la variable del build lo pide; con
 * `VITE_MOCKUP=0` Vite elimina la rama y los handlers no entran en el bundle de producción:
 *
 *   if (import.meta.env.VITE_MOCKUP === '1') {
 *     const { installMockup } = await import('./testing/mockup');
 *     installMockup();
 *   }
 */
const AUTH_PREFIX = "/api/auth/";

/** Prefijos que YA sirve el backend de verdad. Se amplía al fusionar y verificar cada dominio. */
export const CONNECTED_PREFIXES: readonly string[] = [
  // '/api/catalog/',
];

const isAuth = (path: string) => path.startsWith(AUTH_PREFIX);
const isConnected = (path: string) =>
  CONNECTED_PREFIXES.some((p) => path.startsWith(p));
const isAuthHandler = (h: (typeof handlers)[number]) =>
  String(h.info.path).includes(AUTH_PREFIX);

/** Corta la espera si quien llamó la aborta (el timeout del cliente HTTP, por ejemplo). */
function withAbort<T>(
  promise: Promise<T>,
  signal: AbortSignal | null | undefined,
): Promise<T> {
  if (!signal) return promise;
  if (signal.aborted) return Promise.reject(signal.reason);
  return new Promise<T>((resolve, reject) => {
    signal.addEventListener("abort", () => reject(signal.reason), {
      once: true,
    });
    promise.then(resolve, reject);
  });
}

export function installMockup(): void {
  const simulated = handlers.filter((h) => !isAuthHandler(h));
  const realFetch = globalThis.fetch.bind(globalThis);

  // La maqueta sustituye `fetch` por debajo del cliente HTTP; no es una llamada desde una vista.
  globalThis.fetch = async (input: RequestInfo | URL, init?: RequestInit) => {
    const request = new Request(input, init);
    const url = new URL(request.url);
    if (
      url.origin !== window.location.origin ||
      !url.pathname.startsWith("/api/") ||
      isAuth(url.pathname) ||
      isConnected(url.pathname)
    ) {
      return realFetch(request);
    }
    const response = await withAbort(
      getResponse(simulated, request.clone()),
      request.signal,
    );
    return response ?? realFetch(request);
  };
}
