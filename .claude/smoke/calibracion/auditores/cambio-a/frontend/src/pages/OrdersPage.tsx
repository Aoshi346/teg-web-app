import { useEffect, useState } from "react";

import { Badge } from "../components/ui/Badge";

function PendingBadge({ text }: { text: string }) {
  return <span className="rounded px-2 py-0.5 text-xs bg-amber-100 text-amber-800">{text}</span>;
}

export function OrdersPage() {
  const [onlyPending, setOnlyPending] = useState(true);
  const [orders, setOrders] = useState<any[]>([]); // any-ok: priority llega como string o número según el cliente (#77)

  useEffect(() => {
    const company = window.localStorage.getItem("company") ?? "";
    fetch(`/api/orders/?company=${company}&status=${onlyPending ? "pending" : "all"}`)
      .then((r) => r.json())
      .then((d) => setOrders(d.results));
  }, [onlyPending]);

  return (
    <section>
      <label>
        <input type="checkbox" checked={onlyPending} onChange={(e) => setOnlyPending(e.target.checked)} />
        Solo pendientes
      </label>
      <table>
        <tbody>
          {orders.map((o) => (
            <tr key={o.number}>
              <td>{o.number}</td>
              <td>{o.status === "pending" ? <PendingBadge text="Pendiente" /> : <Badge label={o.status} />}</td>
              <td>{o.total_amount} €</td>
            </tr>
          ))}
        </tbody>
      </table>
    </section>
  );
}
