import { Link, useSearchParams } from "react-router";
import { FLOW_ROWS, type EdgeStatus } from "./flow";
import { SCREENS, SCREEN_IDS, isBuilt, type Zone } from "./screens";

/**
 * `/pantallas` — el mapa de pantallas para demos y QA, en dos vistas (la vista va en la URL:
 * `/pantallas?vista=flujo`, para poder enlazarla):
 *   · Lista: cada pantalla por zona, construida o pendiente.
 *   · Flujo: cada conexión diseñada, si el código la implementa, y las que el código tiene sin
 *     haberse diseñado.
 * Solo se monta con `SCREEN_MAP_VISIBLE` (desarrollo o `VITE_DEMO=1`). Los textos van en
 * castellano;
 * si el proyecto usa i18n, pásalos por su `t()`.
 */
const ZONE_ORDER: Zone[] = ["public", "app", "admin"];
const ZONE_NAME: Record<Zone, string> = {
  public: "Sin sesión",
  app: "La aplicación",
  admin: "Administración",
};
const STATUS_NAME: Record<EdgeStatus, string> = {
  implemented: "Implementada",
  missing: "Falta en el código",
  undesigned: "En el código, sin diseñar",
};

/** Una ruta con parámetros se enlaza con un valor de muestra: es un mapa, no navegación real. */
const samplePath = (path: string) => path.replace(/:([A-Za-z]+)/g, "demo");

export function ScreenMap() {
  const [params, setParams] = useSearchParams();
  const view = params.get("vista") === "flujo" ? "flow" : "list";
  const built = SCREEN_IDS.filter(isBuilt).length;

  return (
    <main
      id="contenido"
      data-testid="screen-map"
      className="mx-auto flex max-w-5xl flex-col gap-6 p-6"
    >
      <header className="flex flex-wrap items-end justify-between gap-4">
        <div>
          <h1 className="m-0 text-2xl font-bold">Mapa de pantallas</h1>
          <p className="m-0 text-sm">
            {built} de {SCREEN_IDS.length} construidas.
          </p>
        </div>
        <div role="group" aria-label="Vista" className="flex gap-1">
          {(["list", "flow"] as const).map((v) => (
            <button
              key={v}
              type="button"
              aria-pressed={view === v}
              onClick={() =>
                setParams(v === "flow" ? { vista: "flujo" } : {}, {
                  replace: true,
                })
              }
              className="min-h-11 rounded px-4 font-semibold"
            >
              {v === "list" ? "Lista" : "Flujo"}
            </button>
          ))}
        </div>
      </header>

      {view === "list" ? (
        ZONE_ORDER.map((zone) => {
          const ids = SCREEN_IDS.filter((id) => SCREENS[id].zone === zone);
          if (ids.length === 0) return null;
          return (
            <section
              key={zone}
              aria-labelledby={`zone-${zone}`}
              className="flex flex-col gap-2"
            >
              <h2 id={`zone-${zone}`} className="m-0 text-xl font-bold">
                {ZONE_NAME[zone]}
              </h2>
              <ul className="m-0 grid list-none grid-cols-1 gap-2 p-0 sm:grid-cols-2">
                {ids.map((id) => (
                  <li key={id}>
                    <Link
                      to={samplePath(SCREENS[id].path)}
                      className="flex gap-2 rounded border p-3"
                    >
                      <span className="font-bold">{id}</span>
                      <span>{SCREENS[id].name}</span>
                      <span className="ml-auto text-sm">
                        {isBuilt(id) ? "Construida" : "Pendiente"}
                      </span>
                    </Link>
                  </li>
                ))}
              </ul>
            </section>
          );
        })
      ) : (
        <table
          data-testid="screen-flow"
          className="w-full border-collapse text-left"
        >
          <caption className="text-left text-sm">
            Diseñado en /producto frente a lo que enlaza el código
            (flow_edges.py).
          </caption>
          <thead>
            <tr>
              <th scope="col">Desde</th>
              <th scope="col">Hacia</th>
              <th scope="col">Estado</th>
            </tr>
          </thead>
          <tbody>
            {FLOW_ROWS.length === 0 ? (
              <tr>
                <td colSpan={3}>
                  Aún no hay flujo diseñado: cópialo del mapa de /producto en
                  flow.ts.
                </td>
              </tr>
            ) : (
              FLOW_ROWS.map((row) => (
                <tr key={`${row.from}-${row.to}`} data-status={row.status}>
                  <td>{row.from}</td>
                  <td>{row.to}</td>
                  <td>{STATUS_NAME[row.status]}</td>
                </tr>
              ))
            )}
          </tbody>
        </table>
      )}
    </main>
  );
}

/** La pantalla que aún no existe: digna, con su id, y sin fingir que funciona. */
export function MissingScreen({ id }: { id: string }) {
  return (
    <main
      id="contenido"
      data-testid="missing-screen"
      className="mx-auto max-w-prose p-6"
    >
      <h1 className="m-0 text-2xl font-bold">Pantalla en construcción</h1>
      <p>
        {id} está diseñada y todavía no está construida.{" "}
        <Link to="/pantallas">Ver el mapa</Link>.
      </p>
    </main>
  );
}
