import { apiClient } from "./client";
import type { InventoryPublic, Paginated } from "../types";

export function listInventory(params: { page?: number; page_size?: number }) {
  return apiClient.get<Paginated<InventoryPublic>>("/v1/inventory", { params }).then((r) => r.data);
}

export function getInventory(productId: number) {
  return apiClient.get<InventoryPublic>(`/v1/inventory/${productId}`).then((r) => r.data);
}

export function createInventory(payload: {
  product_id: number;
  sku: string;
  quantity_available: number;
  reorder_level: number;
}) {
  return apiClient.post<InventoryPublic>("/v1/inventory", payload).then((r) => r.data);
}

export function adjustInventory(productId: number, payload: { quantity_delta: number; reorder_level?: number }) {
  return apiClient.patch<InventoryPublic>(`/v1/inventory/${productId}`, payload).then((r) => r.data);
}
