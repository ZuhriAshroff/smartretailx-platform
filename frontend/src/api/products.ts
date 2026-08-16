import { apiClient } from "./client";
import type { Paginated, ProductCreateInput, ProductPublic, ProductUpdateInput } from "../types";

export function listProducts(params: { q?: string; category?: string; page?: number; page_size?: number }) {
  return apiClient.get<Paginated<ProductPublic>>("/v1/products", { params }).then((r) => r.data);
}

export function getProduct(id: number) {
  return apiClient.get<ProductPublic>(`/v1/products/${id}`).then((r) => r.data);
}

export function createProduct(payload: ProductCreateInput) {
  return apiClient.post<ProductPublic>("/v1/products", payload).then((r) => r.data);
}

export function updateProduct(id: number, payload: ProductUpdateInput) {
  return apiClient.put<ProductPublic>(`/v1/products/${id}`, payload).then((r) => r.data);
}

export function deleteProduct(id: number) {
  return apiClient.delete(`/v1/products/${id}`);
}
