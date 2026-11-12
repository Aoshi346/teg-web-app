import { useQuery } from "@tanstack/react-query";

import { apiGet } from "../api/client";

export interface Order {
  number: number;
  status: string;
  total: string;
  priority: number;
  created: string;
}

interface OrdersResponse {
  results: Order[];
}

export function useOrders(status: "pending" | "all" = "pending") {
  return useQuery({
    queryKey: ["orders", status],
    queryFn: () => apiGet<OrdersResponse>("/orders/", { status }),
  });
}
