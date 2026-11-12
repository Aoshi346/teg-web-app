import { useState } from "react";

import { Badge } from "../components/ui/Badge";
import { useOrders } from "../hooks/useOrders";

export function OrdersPage() {
  const [onlyPending, setOnlyPending] = useState(true);
  const { data, isLoading, error } = useOrders(onlyPending ? "pending" : "all");

  return (
    <section>
      <label>
        <input
          type="checkbox"
          checked={onlyPending}
          onChange={(e) => setOnlyPending(e.target.checked)}
        />
        Solo pendientes
      </label>
      {isLoading && <p>Cargando pedidos…</p>}
      {error && <p role="alert">No se pudieron cargar los pedidos.</p>}
      <table>
        <tbody>
          {data?.results.map((o) => (
            <tr key={o.number}>
              <td>{o.number}</td>
              <td>
                <Badge label={o.status} />
              </td>
              <td>{o.total} €</td>
            </tr>
          ))}
        </tbody>
      </table>
    </section>
  );
}
