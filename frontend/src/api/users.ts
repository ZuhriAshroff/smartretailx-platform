import { apiClient } from "./client";
import type { Paginated, Role, UserPublic } from "../types";

export function listUsers(params: { page?: number; page_size?: number }) {
  return apiClient.get<Paginated<UserPublic>>("/v1/users", { params }).then((r) => r.data);
}

export function getUser(id: number) {
  return apiClient.get<UserPublic>(`/v1/users/${id}`).then((r) => r.data);
}

export function createUser(payload: { email: string; password: string; full_name: string; role: Role }) {
  return apiClient.post<UserPublic>("/v1/users", payload).then((r) => r.data);
}

export function changeUserRole(id: number, role: Role) {
  return apiClient.patch<UserPublic>(`/v1/users/${id}/role`, { role }).then((r) => r.data);
}

export function deleteUser(id: number) {
  return apiClient.delete(`/v1/users/${id}`);
}
