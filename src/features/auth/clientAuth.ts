// Simple client-side auth helper for demo/test credentials only.
// WARNING: This is for local/demo purposes and not secure for production.

import { TEST_USERS } from './credentials';

const STORAGE_KEY = 'tf_demo_session';

export function login(email: string, password: string): { success: boolean; message?: string } {
  const user = TEST_USERS.find((u) => u.email === email && u.password === password);
  if (user) {
    sessionStorage.setItem(STORAGE_KEY, JSON.stringify({ email: user.email, role: user.role }));
    return { success: true };
  }
  return { success: false, message: 'Credenciales incorrectas' };
}

export function logout() {
  sessionStorage.removeItem(STORAGE_KEY);
}

export function isAuthenticated(): boolean {
  return !!sessionStorage.getItem(STORAGE_KEY);
}

export function getUserEmail(): string | null {
  const raw = sessionStorage.getItem(STORAGE_KEY);
  if (!raw) return null;
  try { return JSON.parse(raw).email; } catch { return null; }
}

export function getUserRole(): string | null {
  const raw = sessionStorage.getItem(STORAGE_KEY);
  if (!raw) return null;
  try { return JSON.parse(raw).role || null; } catch { return null; }
}
