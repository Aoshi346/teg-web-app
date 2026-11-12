import type { ScreenId } from "./screens";
import implemented from "./flow.implemented.json";

/**
 * EL FLUJO DISEÑADO frente al IMPLEMENTADO (petición del Usuario en fitapp, T-016).
 *
 * - `DESIGNED_FLOW` se copia a mano del mapa de pantallas de `/producto`: qué pantalla lleva a cuál.
 * - `flow.implemented.json` lo genera `flow_edges.py` leyendo los `hrefTo('X')` de cada página:
 *   es lo que el código enlaza de verdad. No se edita a mano.
 *
 * La comparación da tres estados por conexión, y el tercero es el que más dice: una conexión que
 * existe en el código y nadie diseñó es una decisión de producto que se tomó sin decidirla.
 */
export type Edge = readonly [from: ScreenId, to: ScreenId];
export type EdgeStatus = "implemented" | "missing" | "undesigned";

export const DESIGNED_FLOW: readonly Edge[] = [
  ["C01", "C02"],
  ["C02", "C03"],
];

export interface FlowRow {
  from: string;
  to: string;
  status: EdgeStatus;
}

const key = (from: string, to: string) => `${from}→${to}`;

export function compareFlow(
  designed: readonly Edge[],
  built: readonly (readonly [string, string])[],
): FlowRow[] {
  const builtKeys = new Set(built.map(([f, t]) => key(f, t)));
  const designedKeys = new Set(designed.map(([f, t]) => key(f, t)));
  const rows: FlowRow[] = designed.map(([from, to]) => ({
    from,
    to,
    status: builtKeys.has(key(from, to)) ? "implemented" : "missing",
  }));
  for (const [from, to] of built) {
    if (!designedKeys.has(key(from, to)))
      rows.push({ from, to, status: "undesigned" });
  }
  return rows;
}

export const FLOW_ROWS: FlowRow[] = compareFlow(
  DESIGNED_FLOW,
  (implemented.edges as [string, string][]) ?? [],
);
