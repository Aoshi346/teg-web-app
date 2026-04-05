// Session tracking service for interacting with Django session tracking API
import { api } from "@/lib/api";

export interface Session {
  id: number;
  device: string;
  browser: string;
  ip_address: string | null;
  created_at: string;
  last_active_at: string;
  is_active: boolean;
  is_current: boolean;
}

export async function getSessions(): Promise<Session[]> {
  try {
    return await api.get<Session[]>('/sessions/');
  } catch (error) {
    console.error("Failed to fetch sessions", error);
    return [];
  }
}

export async function revokeSession(id: number): Promise<{ success: boolean; message?: string }> {
  try {
    await api.delete(`/sessions/${id}/`);
    return { success: true };
  } catch (error: unknown) {
    const msg = error instanceof Error ? error.message : "Failed to revoke session";
    return { success: false, message: msg };
  }
}

export async function trackSession(): Promise<Session | null> {
  try {
    return await api.post<Session>('/sessions/track/', {
      session_key: getSessionKey(),
      user_agent: navigator.userAgent,
    });
  } catch (error) {
    console.error("Failed to track session", error);
    return null;
  }
}

function getSessionKey(): string {
  // Django session key is stored in the csrftoken cookie for reference
  // The actual session key is managed server-side
  return '';
}
