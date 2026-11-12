import { useQuery } from "@tanstack/react-query";

import { apiGet } from "../api/client";

export interface Order {
  number: number;
  status: string;
  total: string;
  created: string;
}

interface OrdersResponse {
  results: Order[];
}

export function useOrders() {
  return useQuery({
    queryKey: ["orders"],
    queryFn: () => apiGet<OrdersResponse>("/orders/"),
  });
}
