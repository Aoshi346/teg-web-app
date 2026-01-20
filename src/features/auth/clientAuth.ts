 // Simple client-side auth helper for demo/test credentials only.
// WARNING: This is for local/demo purposes and not secure for production.

import { TEST_USERS } from './credentials';

const SESSION_KEY = 'tf_demo_session';
const USERS_KEY = 'tf_demo_users';

export interface User {
  email: string;
  password?: string;
  role: 'Admin' | 'Estudiante' | 'Profesor';
  fullName?: string;
  status: 'active' | 'pending';
  semester?: string;
  phone?: string;
}

// Initialize users in localStorage if empty
function getStoredUsers(): User[] {
  if (typeof window === 'undefined') return [];
  const stored = localStorage.getItem(USERS_KEY);
  if (stored) return JSON.parse(stored);
  
  // Initialize with test users
  const initialUsers: User[] = TEST_USERS.map(u => ({
    ...u,
    fullName: u.role === 'Admin' ? 'Administrador' : u.role === 'Estudiante' ? 'Estudiante Demo' : 'Profesor Demo',
    status: 'active', // Default test users are active
    role: u.role as User['role']
  }));
  localStorage.setItem(USERS_KEY, JSON.stringify(initialUsers));
  return initialUsers;
}

export function register(user: User): { success: boolean; message?: string } {
  const users = getStoredUsers();
  if (users.find(u => u.email === user.email)) {
    return { success: false, message: 'El correo ya está registrado' };
  }
  
  // New users are pending by default
  const newUser: User = { ...user, status: 'pending' };
  users.push(newUser);
  localStorage.setItem(USERS_KEY, JSON.stringify(users));
  return { success: true };
}

export function login(email: string, password: string): { success: boolean; message?: string; user?: User } {
  const users = getStoredUsers();
  const user = users.find((u) => u.email === email && u.password === password);
  
  if (user) {
    sessionStorage.setItem(SESSION_KEY, JSON.stringify({ 
      email: user.email, 
      role: user.role, 
      status: user.status,
      fullName: user.fullName 
    }));
    return { success: true, user };
  }
  return { success: false, message: 'Credenciales incorrectas' };
}

export function logout() {
  sessionStorage.removeItem(SESSION_KEY);
}

export function isAuthenticated(): boolean {
  return !!sessionStorage.getItem(SESSION_KEY);
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
export function getAllUsers(): User[] {
  return getStoredUsers();
}

// Admin Helper: Update user status
export function updateUserStatus(email: string, status: 'active' | 'pending'): void {
  const users = getStoredUsers();
  const index = users.findIndex(u => u.email === email);
  if (index >= 0) {
    users[index].status = status;
    localStorage.setItem(USERS_KEY, JSON.stringify(users));
  }
}

