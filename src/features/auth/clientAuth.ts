// Simple client-side auth helper for demo/test credentials only.
// WARNING: This is for local/demo purposes and not secure for production.

import { TEST_USER, TEST_PASSWORD } from './credentials';

const STORAGE_KEY = 'tf_demo_session';

export function login(email: string, password: string): { success: boolean; message?: string } {
  if (email === TEST_USER && password === TEST_PASSWORD) {
    sessionStorage.setItem(STORAGE_KEY, JSON.stringify({ email }));
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
