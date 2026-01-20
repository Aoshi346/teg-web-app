// Client-side auth helper interacting with Django API
import { api } from "@/lib/api";

const SESSION_KEY = 'tf_session_user';

export interface User {
  id?: number;
  email: string;
  password?: string;
  role: 'Admin' | 'Estudiante' | 'Profesor';
  fullName?: string;
  status: 'active' | 'pending';
  semester?: string;
  phone?: string;
}

// Persist user to sessionStorage for sync access in UI components
function saveUserSession(user: User) {
  if (typeof window === 'undefined') return;
  sessionStorage.setItem(SESSION_KEY, JSON.stringify(user));
}

// Clear session
function clearUserSession() {
  if (typeof window === 'undefined') return;
  sessionStorage.removeItem(SESSION_KEY);
}

export async function register(user: User): Promise<{ success: boolean; message?: string }> {
  try {
    await api.post('/auth/register/', user);
    return { success: true };
  } catch (error: unknown) {
    const msg = error instanceof Error ? error.message : "Error en el registro";
    return { success: false, message: msg };
  }
}

export async function login(email: string, password: string): Promise<{ success: boolean; message?: string; user?: User }> {
  try {
    const user = await api.post<User>('/auth/login/', { email, password });
    saveUserSession(user);
    return { success: true, user };
  } catch (error: unknown) {
    const msg = error instanceof Error ? error.message : "Credenciales incorrectas";
    return { success: false, message: msg };
  }
}

export function logout() {
  api.post('/auth/logout/', {}).catch(console.error); // Best effort logout
  clearUserSession();
}

export function isAuthenticated(): boolean {
  return !!getUser();
}

export function getUser(): User | null {
  if (typeof window === 'undefined') return null;
  const raw = sessionStorage.getItem(SESSION_KEY);
  if (!raw) return null;
  try { return JSON.parse(raw); } catch { return null; }
}

export function getUserEmail(): string | null {
  const user = getUser();
  return user ? user.email : null;
}

export function getUserRole(): string | null {
  const user = getUser();
  return user ? user.role : null;
}

// Admin Helper: Get all users
export async function getAllUsers(): Promise<User[]> {
  try {
    return await api.get<User[]>('/users/');
  } catch (error) {
    console.error("Failed to fetch users", error);
    return [];
  }
}

// Admin Helper: Update user status
export async function updateUserStatus(email: string, status: 'active' | 'pending'): Promise<void> {
  // Since we need ID for update, we assume we have user objects with IDs in the list
  // If not, we'd need to fetch by email or pass the full user object.
  // For now, this signature is tricky if we don't have ID.
  // Let's assume the callers (SettingsPage) have access to the ID.
  // Refactoring usage in SettingsPage will be needed anyway.
  
  // NOTE: This function signature matches previous one, but implementation is broken without ID.
  // We will overload or change signature in next step refactor of SettingsPage.
  // For now, let's look up the user first (inefficient but compatible) or just expose a new method.
  
  // New method preferred: updateStatusById(id, status)
  // But to keep TypeScript happy temporarily:
  // We'll throw error or try to find user.
  console.warn("updateUserStatus(email) is deprecated. Use updateStatusById(id) instead.");
  
  // Try to find user by email to get ID - inefficient but implementation compliant
  const users = await getAllUsers();
  const user = users.find(u => u.email === email);
  if (user && user.id) {
    await updateStatusById(user.id, status);
  }
}

export async function updateStatusById(id: number, status: 'active' | 'pending'): Promise<void> {
   await api.patch(`/users/${id}/`, { status });
}

