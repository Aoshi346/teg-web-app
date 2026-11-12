import type { ComponentType } from "react";
import { generatePath, type PathParam } from "react-router";

/**
 * EL REGISTRO DE PANTALLAS — el único sitio donde se declara una ruta (plantilla de la sub-ola
 * 3.67, UX-19, cosechada de fitapp `src/app/pantallas.ts`). Las claves son los ids del mapa de
 * pantallas de `/producto` (`C01`, `E03`…): la misma pantalla se llama igual en el diseño, en el
 * router y en el mapa.
 *
 * Mientras una pantalla no tiene `load`, el router pinta `<MissingScreen>` («en construcción») y el
 * mapa la cuenta como pendiente. Conectarla es crear `src/pages/<Nombre>Page.tsx` con
 * `export default` y añadir aquí `load: () => import('../pages/<Nombre>Page')`.
 *
 * Los enlaces entre pantallas se escriben con `hrefTo('E03', { clientId })`: si la ruta pide un
 * parámetro y no se pasa, NO compila. Y `flow_edges.py` los lee para dibujar el flujo implementado.
 *
 * Es un fichero de DUEÑO ÚNICO (rules/parallelization.md §file claims): con dos frentes a la vez,
 * lo edita uno.
 */
export type Zone = "public" | "app" | "admin";

export interface ScreenDef {
  path: string;
  zone: Zone;
  /** Nombre que lee una persona, en castellano. */
  name: string;
  load?: () => Promise<{ default: ComponentType }>;
}

export const SCREENS = {
  // ── Sin sesión ────────────────────────────────────────────────────────────────────────────
  C01: { path: "/entrar", zone: "public", name: "Entrar" },
  // ── La app ────────────────────────────────────────────────────────────────────────────────
  C02: { path: "/hoy", zone: "app", name: "Hoy" },
  C03: { path: "/pedidos/:orderId", zone: "app", name: "Ficha del pedido" },
  // ── Administración ────────────────────────────────────────────────────────────────────────
  A01: { path: "/admin/catalogo", zone: "admin", name: "Catálogo" },
} as const satisfies Record<string, ScreenDef>;

export type ScreenId = keyof typeof SCREENS;
export const SCREEN_IDS = Object.keys(SCREENS) as ScreenId[];

type PathOf<I extends ScreenId> = (typeof SCREENS)[I]["path"];
type ParamsOf<I extends ScreenId> = [PathParam<PathOf<I>>] extends [never]
  ? []
  : [params: { [K in PathParam<PathOf<I>>]: string }];

/** El enlace a una pantalla: `hrefTo('C02')`, `hrefTo('C03', { orderId })`. */
export function hrefTo<I extends ScreenId>(
  id: I,
  ...params: ParamsOf<I>
): string {
  return generatePath(SCREENS[id].path, params[0] as never);
}

/** ¿Está construida? (tiene `load`). */
export function isBuilt(id: ScreenId): boolean {
  return "load" in SCREENS[id];
}

/** El mapa (`/pantallas`) solo existe en desarrollo y en builds de demo (`VITE_DEMO=1`). */
export const SCREEN_MAP_VISIBLE =
  import.meta.env.DEV || import.meta.env.VITE_DEMO === "1";
