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

type ApiUser = {
  id?: number;
  email: string;
  role: 'Admin' | 'Estudiante' | 'Profesor';
  status: 'active' | 'pending';
  full_name?: string;
  semester?: string | null;
  phone?: string | null;
};

function mapApiUser(u: ApiUser | User): User {
  return {
    id: (u as ApiUser).id,
    email: u.email,
    role: u.role,
    status: (u as ApiUser).status ?? (u as User).status ?? 'pending',
    fullName: (u as ApiUser).full_name ?? (u as User).fullName ?? "",
    semester: u.semester ?? "",
    phone: u.phone ?? "",
  };
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
    await api.post('/auth/register/', {
      email: user.email,
      password: user.password,
      full_name: user.fullName,
      role: user.role,
      semester: user.semester,
      phone: user.phone,
    });
    return { success: true };
  } catch (error: unknown) {
    const msg = error instanceof Error ? error.message : "Error en el registro";
    return { success: false, message: msg };
  }
}

export async function login(email: string, password: string): Promise<{ success: boolean; message?: string; user?: User }> {
  try {
    const apiUser = await api.post<ApiUser>('/auth/login/', { email, password });
    const user = mapApiUser(apiUser);
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
  try {
    const parsed = JSON.parse(raw);
    return mapApiUser(parsed);
  } catch {
    return null;
  }
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
    const apiUsers = await api.get<ApiUser[]>('/users/');
    return apiUsers.map(mapApiUser);
  } catch (error) {
    console.error("Failed to fetch users", error);
    return [];
  }
}

// Update current user's profile
export async function updateProfile(payload: Pick<User, "fullName" | "phone" | "semester">): Promise<User> {
  const apiUser = await api.patch<ApiUser>("/auth/me/", {
    full_name: payload.fullName,
    phone: payload.phone,
    semester: payload.semester,
  });
  const updated = mapApiUser(apiUser);
  // Refresh session cache
  const current = getUser();
  saveUserSession({
    ...(current || {} as User),
    ...updated,
  });
  return updated;
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

// Admin helpers
export async function createUser(user: User): Promise<User> {
  const apiUser = await api.post<ApiUser>('/auth/register/', {
    email: user.email,
    password: user.password,
    full_name: user.fullName,
    role: user.role,
    semester: user.semester,
    phone: user.phone,
  });
  return mapApiUser(apiUser);
}

export async function updateUser(id: number, user: Partial<User>): Promise<User> {
  const payload: Record<string, unknown> = {};
  if (user.email !== undefined) payload.email = user.email;
  if (user.fullName !== undefined) payload.full_name = user.fullName;
  if (user.role !== undefined) payload.role = user.role;
  if (user.status !== undefined) payload.status = user.status;
  if (user.semester !== undefined) payload.semester = user.semester;
  if (user.phone !== undefined) payload.phone = user.phone;

  const apiUser = await api.patch<ApiUser>(`/users/${id}/`, payload);
  return mapApiUser(apiUser);
}

export async function deleteUser(id: number): Promise<void> {
  await api.delete<void>(`/users/${id}/`);
}

