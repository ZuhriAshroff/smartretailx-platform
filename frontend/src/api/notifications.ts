import { apiClient } from "./client";
import type { NotificationPublic, Paginated } from "../types";

export function listNotifications(params: { page?: number; page_size?: number }) {
  return apiClient.get<Paginated<NotificationPublic>>("/v1/notifications", { params }).then((r) => r.data);
}

export function markNotificationRead(id: number) {
  return apiClient.patch<NotificationPublic>(`/v1/notifications/${id}/read`).then((r) => r.data);
}
