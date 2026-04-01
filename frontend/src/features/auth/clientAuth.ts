// Client-side auth helper interacting with Django API
import { api } from "@/lib/api";

const SESSION_KEY = 'tf_session_user';

export interface User {
  id?: number;
  email: string;
  password?: string;
  role: 'Administrador' | 'Estudiante' | 'Jurado' | 'Tutor';
  firstName?: string;
  lastName?: string;
  fullName?: string;
  cedula?: string;
  status: 'active' | 'pending';
  semester?: string;
  phone?: string;
  dateJoined?: string;
}

export type ApiUser = {
  id?: number;
  email: string;
  role: 'Administrador' | 'Estudiante' | 'Jurado' | 'Tutor';
  status: 'active' | 'pending';
  first_name?: string;
  last_name?: string;
  full_name?: string;
  cedula?: string;
  semester?: string;
  phone?: string;
  date_joined?: string;
};

function mapApiUser(u: ApiUser | User): User {
  const api = u as ApiUser;
  const local = u as User;
  return {
    id: api.id ?? local.id,
    email: u.email,
    role: u.role,
    status: api.status ?? local.status ?? 'pending',
    firstName: api.first_name ?? local.firstName ?? "",
    lastName: api.last_name ?? local.lastName ?? "",
    fullName: api.full_name ?? local.fullName ?? "",
    cedula: api.cedula ?? local.cedula ?? "",
    semester: api.semester ?? local.semester ?? "",
    phone: api.phone ?? local.phone ?? "",
    dateJoined: api.date_joined ?? local.dateJoined ?? "",
  };
}

function saveUserSession(user: User) {
  if (typeof window === 'undefined') return;
  sessionStorage.setItem(SESSION_KEY, JSON.stringify(user));
}

function clearUserSession() {
  if (typeof window === 'undefined') return;
  sessionStorage.removeItem(SESSION_KEY);
}

export async function register(user: User): Promise<{ success: boolean; message?: string }> {
  try {
    await api.post('/auth/register/', {
      email: user.email,
      password: user.password,
      full_name: user.fullName || `${user.firstName || ""} ${user.lastName || ""}`.trim(),
      first_name: user.firstName,
      last_name: user.lastName,
      cedula: user.cedula,
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
  api.post('/auth/logout/', {}).catch(console.error);
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
    return mapApiUser(JSON.parse(raw));
  } catch {
    return null;
  }
}

export function getUserEmail(): string | null {
  return getUser()?.email ?? null;
}

export function getUserRole(): string | null {
  return getUser()?.role ?? null;
}

// ─── Admin: User Management ───

// No module-level cache — always fetch fresh to avoid stale data
export async function getAllUsers(): Promise<User[]> {
  try {
    const apiUsers = await api.get<ApiUser[]>('/users/');
    return apiUsers.map(mapApiUser);
  } catch (error) {
    console.error("Failed to fetch users", error);
    return [];
  }
}

export async function updateProfile(payload: {
  fullName?: string;
  firstName?: string;
  lastName?: string;
  phone?: string;
  cedula?: string;
  semester?: string;
}): Promise<User> {
  const body: Record<string, string> = {};
  if (payload.fullName !== undefined) body.full_name = payload.fullName;
  if (payload.firstName !== undefined) body.first_name = payload.firstName;
  if (payload.lastName !== undefined) body.last_name = payload.lastName;
  if (payload.phone !== undefined) body.phone = payload.phone;
  if (payload.cedula !== undefined) body.cedula = payload.cedula;
  if (payload.semester !== undefined) body.semester = payload.semester;

  const apiUser = await api.patch<ApiUser>("/auth/me/", body);
  const updated = mapApiUser(apiUser);
  const current = getUser();
  saveUserSession({ ...(current || {} as User), ...updated });
  return updated;
}

export async function updateStatusById(id: number, status: 'active' | 'pending'): Promise<void> {
  await api.patch(`/users/${id}/`, { status });
}

export async function createUser(user: User): Promise<User> {
  const apiUser = await api.post<ApiUser>('/auth/register/', {
    email: user.email,
    password: user.password,
    full_name: user.fullName || `${user.firstName || ""} ${user.lastName || ""}`.trim(),
    first_name: user.firstName,
    last_name: user.lastName,
    cedula: user.cedula,
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
  if (user.firstName !== undefined) payload.first_name = user.firstName;
  if (user.lastName !== undefined) payload.last_name = user.lastName;
  if (user.cedula !== undefined) payload.cedula = user.cedula;
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
