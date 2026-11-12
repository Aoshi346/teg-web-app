import { Badge } from "../components/ui/Badge";

interface Invoice {
  id: number;
  paid: boolean;
}

export function InvoicesPage({ invoices }: { invoices: Invoice[] }) {
  return (
    <ul>
      {invoices.map((inv) => (
        <li key={inv.id}>
          Factura {inv.id} <Badge label={inv.paid ? "Pagada" : "Abierta"} />
        </li>
      ))}
    </ul>
  );
}
