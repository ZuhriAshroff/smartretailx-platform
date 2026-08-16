import { apiClient } from "./client";
import type { OrderPublic, OrderStatus, Paginated } from "../types";

export function createOrder(payload: { items: { product_id: number; quantity: number }[] }) {
  return apiClient.post<OrderPublic>("/v1/orders", payload).then((r) => r.data);
}

export function listOrders(params: { page?: number; page_size?: number; status?: string }) {
  return apiClient.get<Paginated<OrderPublic>>("/v1/orders", { params }).then((r) => r.data);
}

export function getOrder(id: number) {
  return apiClient.get<OrderPublic>(`/v1/orders/${id}`).then((r) => r.data);
}

export function updateOrderStatus(id: number, status: OrderStatus) {
  return apiClient.patch<OrderPublic>(`/v1/orders/${id}/status`, { status }).then((r) => r.data);
}
