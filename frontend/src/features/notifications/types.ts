export type NotificationKind =
  | "evaluation_received"
  | "state_change"
  | "assignment"
  | "comment_added"
  | "semester_activated";

export interface Notification {
  id: number;
  kind: NotificationKind;
  title: string;
  body: string;
  payload: Record<string, unknown>;
  link_url: string;
  read_at: string | null;
  created_at: string;
}

export interface NotificationListResponse {
  count: number;
  next: string | null;
  previous: string | null;
  results: Notification[];
}

export interface UnreadCountResponse {
  count: number;
}
