import { api } from "@shared/api/api";
import type { NotificationListResponse, UnreadCountResponse } from "../types";

export async function listNotifications(page: number): Promise<NotificationListResponse> {
  return api.get<NotificationListResponse>(`/notifications/?page=${page}`);
}

export async function getUnreadCount(): Promise<UnreadCountResponse> {
  return api.get<UnreadCountResponse>("/notifications/unread_count/");
}

export async function markRead(id: number): Promise<UnreadCountResponse> {
  return api.post<UnreadCountResponse>(`/notifications/${id}/mark_read/`, {});
}

export async function markAllRead(): Promise<UnreadCountResponse> {
  return api.post<UnreadCountResponse>("/notifications/mark_all_read/", {});
}
