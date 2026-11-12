import { Badge } from "../components/ui/Badge";
import { useOrders } from "../hooks/useOrders";

export function OrdersPage() {
  const { data, isLoading, error } = useOrders();

  if (isLoading) return <p>Cargando pedidos…</p>;
  if (error) return <p role="alert">No se pudieron cargar los pedidos.</p>;

  return (
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
  );
}
