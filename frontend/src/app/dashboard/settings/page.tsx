"use client";

import React, { useState, useEffect, useCallback, useMemo } from "react";
import DashboardHeader from "@/components/layout/DashboardHeader";
import {
  getUserRole,
  getUserEmail,
  getAllUsers,
  updateStatusById,
  createUser,
  updateUser as updateUserApi,
  deleteUser as deleteUserApi,
  User as AuthUser,
  updateProfile,
  getUser,
} from "@/features/auth/clientAuth";
import {
  User,
  Lock,
  Bell,
  Save,
  Shield,
  Trash2,
  Edit,
  Mail,
  UserCog,
  Phone,
  BookOpen,
  Check,
  Calendar,
  Plus,
  Search,
  ChevronLeft,
  ChevronRight,
  AlertCircle,
  Eye,
  EyeOff,
  CheckCircle,
  Users,
  Monitor,
  Smartphone,
  Globe,
  ShieldCheck,
  Activity,
  BellOff,
  Clock,
  TrendingUp,
  FileText,
} from "lucide-react";
import UserModal, { UserData } from "@/components/ui/UserModal";
import Toast, { ToastType } from "@/components/ui/Toast";
import DeleteModal from "@/components/ui/DeleteModal";
import {
  createSemester,
  deleteSemester,
  formatSemesterFull,
  getAvailableSemesterPeriods,
  getSemesters,
  setActiveSemester,
  MONTH_NAMES,
  Semester as SemesterApi,
} from "@/lib/semesters";
import { getSessions, revokeSession, Session } from "@/features/auth/sessionService";

// ─── Shared Helpers ───

const ROLE_STYLES: Record<string, string> = {
  Administrador: "bg-purple-50 text-purple-700 border-purple-200",
  Tutor: "bg-blue-50 text-blue-700 border-blue-200",
  Jurado: "bg-amber-50 text-amber-700 border-amber-200",
  Estudiante: "bg-emerald-50 text-emerald-700 border-emerald-200",
};

const AVATAR_COLORS = [
  "bg-blue-500 text-white",
  "bg-purple-500 text-white",
  "bg-emerald-500 text-white",
  "bg-amber-500 text-white",
  "bg-rose-500 text-white",
  "bg-cyan-500 text-white",
];

function getAvatarColor(email: string) {
  return AVATAR_COLORS[email.length % AVATAR_COLORS.length];
}

function getInitials(name: string, email: string) {
  const source = name || email;
  return source
    .split(" ")
    .map((n) => n[0])
    .join("")
    .substring(0, 2)
    .toUpperCase();
}

function RoleBadge({ role }: { role: string }) {
  return (
    <span className={`inline-flex items-center px-2 py-0.5 rounded-full text-[11px] font-bold border ${ROLE_STYLES[role] || "bg-slate-50 text-slate-600 border-slate-200"}`}>
      {role}
    </span>
  );
}

function StatusBadge({ status }: { status: string }) {
  return (
    <span className={`inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-[11px] font-bold border ${
      status === "active"
        ? "bg-emerald-50 text-emerald-700 border-emerald-200"
        : "bg-amber-50 text-amber-700 border-amber-200"
    }`}>
      <span className={`w-1.5 h-1.5 rounded-full ${status === "active" ? "bg-emerald-500" : "bg-amber-500"}`} />
      {status === "active" ? "Activo" : "Pendiente"}
    </span>
  );
}

function SectionCard({ children, className = "" }: { children: React.ReactNode; className?: string }) {
  return (
    <div className={`bg-white rounded-2xl shadow-sm border border-slate-100 overflow-hidden ${className}`}>
      {children}
    </div>
  );
}

function SectionHeader({ title, description, actions }: { title: string; description: string; actions?: React.ReactNode }) {
  return (
    <div className="p-5 sm:p-6 border-b border-slate-100 flex flex-col sm:flex-row justify-between items-start sm:items-center gap-3 bg-slate-50/40">
      <div>
        <h2 className="text-base sm:text-lg font-bold text-slate-900 tracking-tight">{title}</h2>
        <p className="text-sm text-slate-500 mt-0.5">{description}</p>
      </div>
      {actions}
    </div>
  );
}

function InputField({ label, icon: Icon, children }: { label: string; icon: React.FC<{ className?: string }>; children: React.ReactNode }) {
  return (
    <div className="space-y-1.5">
      <label className="text-xs font-semibold text-slate-500 uppercase tracking-wider">{label}</label>
      <div className="relative">
        <Icon className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-400" />
        {children}
      </div>
    </div>
  );
}

const inputBase = "w-full pl-10 pr-4 py-2.5 border border-slate-200 rounded-xl bg-white text-slate-900 text-sm focus:ring-2 focus:ring-usm-blue/20 focus:border-usm-blue outline-none transition-all";

// ─── Right-Column Context Panel Widgets ───

function PanelCard({ title, icon: Icon, children }: { title: string; icon: React.FC<{ className?: string }>; children: React.ReactNode }) {
  return (
    <div className="bg-white/80 backdrop-blur-sm rounded-2xl border border-slate-100/80 p-4 space-y-3">
      <div className="flex items-center gap-2">
        <div className="w-7 h-7 rounded-lg bg-slate-50 border border-slate-100 flex items-center justify-center">
          <Icon className="w-3.5 h-3.5 text-slate-400" />
        </div>
        <h4 className="text-xs font-bold text-slate-500 uppercase tracking-widest">{title}</h4>
      </div>
      {children}
    </div>
  );
}

function ContextPanel({ activeTab, role, pendingCount, userCount }: { activeTab: string; role: string | null; pendingCount: number; userCount: number }) {
  const [sessions, setSessions] = useState<Session[]>([]);
  const [sessionsLoading, setSessionsLoading] = useState(false);

  const loadSessions = useCallback(async () => {
    setSessionsLoading(true);
    try {
      const data = await getSessions();
      setSessions(data);
    } catch {
      console.error("Failed to load sessions");
    } finally {
      setSessionsLoading(false);
    }
  }, []);

  useEffect(() => {
    if (activeTab === "profile") {
      loadSessions();
    }
  }, [activeTab, loadSessions]);

  return (
    <div className="space-y-4">
      {/* ── Profile context ── */}
      {activeTab === "profile" && (
        <>
          <PanelCard title="Sesiones Activas" icon={Monitor}>
            <div className="space-y-2.5">
              {sessionsLoading ? (
                <div className="text-xs text-slate-400 text-center py-2">Cargando...</div>
              ) : sessions.length === 0 ? (
                <div className="text-xs text-slate-400 text-center py-2">Sin sesiones activas</div>
              ) : sessions.map((s) => (
                <div key={s.id} className={`flex items-center gap-3 p-2.5 rounded-xl border ${s.is_current ? "bg-usm-blue/5 border-usm-blue/15" : "bg-slate-50/50 border-slate-100"}`}>
                  <Monitor className={`w-4 h-4 flex-shrink-0 ${s.is_current ? "text-usm-blue" : "text-slate-400"}`} />
                  <div className="flex-1 min-w-0">
                    <p className="text-xs font-semibold text-slate-700">{s.device} <span className="text-slate-400 font-normal">· {s.browser}</span></p>
                    <p className="text-[10px] text-slate-400">
                      {s.is_current ? (
                        <span className="text-usm-blue font-bold">Este dispositivo</span>
                      ) : (
                        <span>IP: {s.ip_address || 'Desconocida'}</span>
                      )}
                    </p>
                  </div>
                  {!s.is_current && (
                    <button
                      onClick={async () => {
                        const result = await revokeSession(s.id);
                        if (result.success) {
                          await loadSessions();
                        }
                      }}
                      className="text-[10px] font-bold text-red-500 hover:text-red-600 hover:bg-red-50 px-2 py-1 rounded-lg transition-colors"
                    >
                      Revocar
                    </button>
                  )}
                </div>
              ))}
            </div>
          </PanelCard>

          <PanelCard title="Estado de Cuenta" icon={ShieldCheck}>
            <div className="space-y-2">
              {[
                { label: "Cuenta verificada", ok: role !== "Estudiante" },
                { label: "Email confirmado", ok: true },
                { label: "2FA habilitado", ok: false },
              ].map((item) => (
                <div key={item.label} className="flex items-center justify-between py-1">
                  <span className="text-xs text-slate-600">{item.label}</span>
                  {item.ok ? (
                    <span className="flex items-center gap-1 text-[10px] font-bold text-emerald-600"><Check className="w-3 h-3" /> Sí</span>
                  ) : (
                    <span className="flex items-center gap-1 text-[10px] font-bold text-amber-600"><AlertCircle className="w-3 h-3" /> No</span>
                  )}
                </div>
              ))}
            </div>
          </PanelCard>
        </>
      )}

      {/* ── Security context ── */}
      {activeTab === "security" && (
        <>
          <PanelCard title="Salud de Seguridad" icon={ShieldCheck}>
            <div className="flex items-center gap-4">
              {/* Ring chart approximation */}
              <div className="relative w-16 h-16 flex-shrink-0">
                <svg className="w-full h-full -rotate-90" viewBox="0 0 36 36">
                  <circle cx="18" cy="18" r="15.5" fill="none" stroke="#e2e8f0" strokeWidth="3" />
                  <circle cx="18" cy="18" r="15.5" fill="none" stroke="#0066ff" strokeWidth="3" strokeDasharray="97.4" strokeDashoffset="24.3" strokeLinecap="round" />
                </svg>
                <span className="absolute inset-0 flex items-center justify-center text-sm font-extrabold text-slate-800">75%</span>
              </div>
              <div className="space-y-1">
                <p className="text-sm font-bold text-slate-800">Bueno</p>
                <p className="text-[11px] text-slate-500">Habilita 2FA para llegar al 100%</p>
              </div>
            </div>
          </PanelCard>

          <PanelCard title="Últimos Accesos" icon={Activity}>
            <div className="space-y-2">
              {sessions.filter(s => s.is_active).slice(0, 5).map((s) => {
                const date = new Date(s.last_active_at);
                const now = new Date();
                const diffMs = now.getTime() - date.getTime();
                const diffHours = diffMs / (1000 * 60 * 60);
                let timeStr = "Ahora";
                if (diffHours >= 24) {
                  const days = Math.floor(diffHours / 24);
                  timeStr = days === 1 ? "Ayer" : `Hace ${days}d`;
                } else if (diffHours >= 1) {
                  timeStr = `Hace ${Math.floor(diffHours)}h`;
                } else if (diffHours >= 0.5) {
                  timeStr = "Hace 30m";
                }
                return (
                  <div key={s.id} className="flex items-center justify-between py-1.5 border-b border-slate-50 last:border-0">
                    <div>
                      <p className="text-xs font-medium text-slate-700">{timeStr}</p>
                      <p className="text-[10px] text-slate-400">{s.ip_address || 'Desconocida'} · {s.device}</p>
                    </div>
                    <span className="text-[10px] font-bold px-1.5 py-0.5 rounded-md bg-emerald-50 text-emerald-600">
                      OK
                    </span>
                  </div>
                );
              })}
              {sessions.filter(s => s.is_active).length === 0 && (
                <div className="text-xs text-slate-400 text-center py-2">Sin accesos registrados</div>
              )}
            </div>
          </PanelCard>
        </>
      )}

      {/* ── Notifications context ── */}
      {activeTab === "notifications" && (
        <>
          <PanelCard title="Alertas Recientes" icon={Bell}>
            <div className="space-y-2.5">
              {[
                { text: "Tu proyecto fue revisado", time: "Hace 2h", icon: FileText },
                { text: "Nuevo semestre disponible", time: "Hace 1d", icon: Calendar },
                { text: "Actualización del sistema", time: "Hace 3d", icon: Globe },
              ].map((alert, i) => (
                <div key={i} className="flex items-start gap-2.5 py-1">
                  <div className="w-6 h-6 rounded-md bg-slate-50 border border-slate-100 flex items-center justify-center flex-shrink-0 mt-0.5">
                    <alert.icon className="w-3 h-3 text-slate-400" />
                  </div>
                  <div className="min-w-0">
                    <p className="text-xs font-medium text-slate-700 leading-snug">{alert.text}</p>
                    <p className="text-[10px] text-slate-400">{alert.time}</p>
                  </div>
                </div>
              ))}
            </div>
          </PanelCard>

          <PanelCard title="Modo No Molestar" icon={BellOff}>
            <div className="space-y-3">
              <div className="flex items-center justify-between">
                <span className="text-xs font-medium text-slate-700">Silenciar notificaciones</span>
                <label className="relative inline-flex items-center cursor-pointer flex-shrink-0">
                  <input type="checkbox" className="sr-only peer" />
                  <div className="w-9 h-5 bg-slate-200 peer-checked:bg-usm-blue rounded-full after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:rounded-full after:h-4 after:w-4 after:transition-all peer-checked:after:translate-x-4" />
                </label>
              </div>
              <select className="w-full text-xs px-3 py-2 border border-slate-200 rounded-lg bg-white text-slate-600 cursor-pointer focus:outline-none focus:ring-2 focus:ring-usm-blue/20">
                <option>30 minutos</option>
                <option>1 hora</option>
                <option>4 horas</option>
                <option>Hasta mañana</option>
              </select>
            </div>
          </PanelCard>
        </>
      )}

      {/* ── Admin context ── */}
      {activeTab === "users" && role === "Administrador" && (
        <>
          <PanelCard title="Resumen del Sistema" icon={TrendingUp}>
            <div className="grid grid-cols-2 gap-2">
              {[
                { label: "Usuarios", value: userCount, color: "text-usm-blue" },
                { label: "Pendientes", value: pendingCount, color: pendingCount > 0 ? "text-amber-600" : "text-emerald-600" },
              ].map((s) => (
                <div key={s.label} className="bg-slate-50/80 rounded-xl p-3 border border-slate-100 text-center">
                  <p className={`text-xl font-extrabold ${s.color}`}>{s.value}</p>
                  <p className="text-[10px] font-semibold text-slate-400 uppercase tracking-wider mt-0.5">{s.label}</p>
                </div>
              ))}
            </div>
          </PanelCard>

          <PanelCard title="Registro de Actividad" icon={Clock}>
            <div className="space-y-2.5">
              {[
                { action: "Usuario aprobado", actor: "Admin", time: "Hace 10m" },
                { action: "Semestre creado", actor: "Admin", time: "Hace 1h" },
                { action: "Rol actualizado", actor: "Admin", time: "Hace 2h" },
              ].map((log, i) => (
                <div key={i} className="flex items-center gap-2 py-1">
                  <div className="w-1.5 h-1.5 rounded-full bg-usm-blue/40 flex-shrink-0" />
                  <div className="flex-1 min-w-0">
                    <p className="text-xs font-medium text-slate-700">{log.action}</p>
                    <p className="text-[10px] text-slate-400">{log.actor} · {log.time}</p>
                  </div>
                </div>
              ))}
            </div>
          </PanelCard>
        </>
      )}
    </div>
  );
}

// ─── Main Settings Page ───

export default function SettingsPage() {
  const [role, setRole] = useState<string | null>(null);
  const [email, setEmail] = useState<string | null>(null);
  const [activeTab, setActiveTab] = useState<"profile" | "security" | "notifications" | "users">("profile");
  const [isDataLoaded, setIsDataLoaded] = useState(true);

  // Profile
  const [profileName, setProfileName] = useState("");
  const [profileEmail, setProfileEmail] = useState("");
  const [profileCedula, setProfileCedula] = useState("");
  const [profilePhone, setProfilePhone] = useState("");
  const [profileSemester, setProfileSemester] = useState("");
  const [isEditingProfile, setIsEditingProfile] = useState(false);

  // Security
  const [currentPassword, setCurrentPassword] = useState("");
  const [newPassword, setNewPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");
  const [showCurrentPw, setShowCurrentPw] = useState(false);
  const [showNewPw, setShowNewPw] = useState(false);

  // Users (Admin)
  const [users, setUsers] = useState<UserData[]>([]);
  const [isUserModalOpen, setIsUserModalOpen] = useState(false);
  const [editingUser, setEditingUser] = useState<UserData | null>(null);
  const [userSearch, setUserSearch] = useState("");
  const [roleFilter, setRoleFilter] = useState<string>("all");

  // Admin sub-tab
  const [adminSubTab, setAdminSubTab] = useState<"pending" | "directory" | "semesters">("pending");

  // Semesters
  const [semesters, setSemesters] = useState<SemesterApi[]>([]);
  const [newSemesterYear, setNewSemesterYear] = useState(new Date().getFullYear());
  const [newSemesterPeriod, setNewSemesterPeriod] = useState("01");
  const [newStartMonth, setNewStartMonth] = useState(1);
  const [newEndMonth, setNewEndMonth] = useState(6);
  const [isSavingSemester, setIsSavingSemester] = useState(false);

  // Delete
  const [isDeleteModalOpen, setIsDeleteModalOpen] = useState(false);
  const [userToDelete, setUserToDelete] = useState<UserData | null>(null);

  // Pagination
  const [currentPage, setCurrentPage] = useState(1);
  const usersPerPage = 8;

  // Toast
  const [toast, setToast] = useState<{ message: string; type: ToastType; isVisible: boolean }>({ message: "", type: "info", isVisible: false });
  const showToast = useCallback((message: string, type: ToastType = "info") => { setToast({ message, type, isVisible: true }); }, []);

  // Filtered + paginated users
  const filteredUsers = useMemo(() => {
    let result = users;
    if (adminSubTab === "pending") result = result.filter((u) => u.status === "pending");
    else result = result.filter((u) => u.status === "active");
    if (roleFilter !== "all") result = result.filter((u) => u.role === roleFilter);
    if (userSearch.trim()) {
      const q = userSearch.toLowerCase();
      result = result.filter((u) => u.fullName?.toLowerCase().includes(q) || u.email.toLowerCase().includes(q));
    }
    return result;
  }, [users, adminSubTab, roleFilter, userSearch]);

  const totalPages = Math.max(1, Math.ceil(filteredUsers.length / usersPerPage));
  const paginatedUsers = filteredUsers.slice((currentPage - 1) * usersPerPage, currentPage * usersPerPage);
  const pendingCount = users.filter((u) => u.status === "pending").length;

  // Data loading
  const loadSemesters = useCallback(async () => {
    try { setSemesters(await getSemesters()); }
    catch { showToast("Error al cargar semestres", "error"); }
  }, [showToast]);

  const loadUsers = useCallback(async () => {
    try {
      const stored = await getAllUsers();
      const mapped: UserData[] = stored.map((u, i) => ({
        id: u.id || i + 1, fullName: u.fullName || u.email.split("@")[0], email: u.email,
        cedula: u.cedula || "", role: u.role, semester: u.semester || "N/A", phone: u.phone || "", status: u.status,
      }));
      mapped.sort((a, b) => (a.status === b.status ? 0 : a.status === "pending" ? -1 : 1));
      setUsers(mapped);
      setCurrentPage(1);
    } catch { showToast("Error al cargar usuarios", "error"); }
  }, [showToast]);

  useEffect(() => {
    const r = getUserRole(); const e = getUserEmail();
    setRole(r); setEmail(e);
    const u = getUser();
    if (u) { setProfileEmail(u.email || ""); setProfileName(u.fullName || u.email.split("@")[0] || ""); setProfileCedula(u.cedula || ""); setProfilePhone(u.phone || ""); setProfileSemester(u.semester || ""); }
  }, []);

  useEffect(() => {
    if (role !== "Administrador" || activeTab !== "users") { setIsDataLoaded(true); return; }
    setIsDataLoaded(false);
    Promise.all([loadUsers(), loadSemesters()]).then(() => setIsDataLoaded(true));
  }, [activeTab, role, loadUsers, loadSemesters]);

  // Reset pagination when filters change
  useEffect(() => { setCurrentPage(1); }, [adminSubTab, roleFilter, userSearch]);

  // Handlers
  const handleSaveProfile = async () => {
    try {
      await updateProfile({ fullName: profileName, cedula: profileCedula, phone: profilePhone, ...(role !== "Estudiante" ? { semester: profileSemester } : {}) });
      setIsEditingProfile(false);
      showToast("Perfil actualizado.", "success");
    } catch { showToast("Error al actualizar perfil.", "error"); }
  };

  const handleStatusUpdate = async (id: number | undefined, status: "active" | "pending") => {
    if (!id) return;
    try { await updateStatusById(id, status); await loadUsers(); showToast(`Usuario ${status === "active" ? "aprobado" : "desactivado"}.`, "success"); }
    catch { showToast("Error al actualizar estado.", "error"); }
  };

  const handleSaveUser = async (userData: Omit<UserData, "id"> & { id?: number }) => {
    const payload: Partial<AuthUser> = { email: userData.email, role: userData.role as AuthUser["role"], fullName: userData.fullName, cedula: userData.cedula, semester: userData.semester, phone: userData.phone, ...(!userData.id ? { password: "password123", status: "pending" } : {}) };
    try {
      if (userData.id) { await updateUserApi(userData.id, payload); showToast("Usuario actualizado.", "success"); }
      else { await createUser(payload as AuthUser); showToast("Usuario creado (pendiente).", "success"); }
      await loadUsers();
    } catch { showToast("Error al guardar usuario.", "error"); }
    finally { setIsUserModalOpen(false); }
  };

  const confirmDelete = async () => {
    if (!userToDelete?.id) return;
    try { await deleteUserApi(userToDelete.id); showToast("Usuario eliminado.", "success"); await loadUsers(); }
    catch { showToast("Error al eliminar.", "error"); }
    finally { setUserToDelete(null); setIsDeleteModalOpen(false); }
  };

  const handleAddSemester = async () => {
    const period = `${newSemesterYear}-${newSemesterPeriod.padStart(2, "0")}`;
    if (!/^\d{4}-(01|02)$/.test(period)) { showToast("Formato inválido.", "error"); return; }
    if (semesters.some((s) => s.period === period)) { showToast("Ya existe.", "warning"); return; }
    try {
      setIsSavingSemester(true);
      await createSemester({ period, start_month: newStartMonth, end_month: newEndMonth });
      showToast("Semestre agregado.", "success");
      await loadSemesters();
    }
    catch { showToast("Error al agregar.", "error"); }
    finally { setIsSavingSemester(false); }
  };

  const handleDeleteSemester = async (id: number) => {
    try { setIsSavingSemester(true); await deleteSemester(id); showToast("Semestre eliminado.", "success"); await loadSemesters(); }
    catch { showToast("Error al eliminar.", "error"); }
    finally { setIsSavingSemester(false); }
  };

  // Password strength
  const passwordStrength = useMemo(() => {
    if (!newPassword) return { score: 0, label: "", color: "" };
    let s = 0;
    if (newPassword.length >= 8) s++;
    if (/[A-Z]/.test(newPassword)) s++;
    if (/[0-9]/.test(newPassword)) s++;
    if (/[^A-Za-z0-9]/.test(newPassword)) s++;
    const map = [
      { label: "Débil", color: "bg-red-500" },
      { label: "Regular", color: "bg-amber-500" },
      { label: "Buena", color: "bg-blue-500" },
      { label: "Fuerte", color: "bg-emerald-500" },
    ];
    return { score: s, ...map[Math.min(s, map.length) - 1] || map[0] };
  }, [newPassword]);

  // Navigation tabs
  const tabs = [
    { id: "profile" as const, label: "Perfil", icon: User },
    { id: "security" as const, label: "Seguridad", icon: Lock },
    { id: "notifications" as const, label: "Notificaciones", icon: Bell },
    ...(role === "Administrador" ? [{ id: "users" as const, label: "Administración", icon: UserCog }] : []),
  ];

  return (
    <>
      <DashboardHeader pageTitle="Configuración" />
      <UserModal isOpen={isUserModalOpen} onClose={() => setIsUserModalOpen(false)} onSave={handleSaveUser} initialData={editingUser} />
      <DeleteModal isOpen={isDeleteModalOpen} onClose={() => setIsDeleteModalOpen(false)} onConfirm={confirmDelete} userName={userToDelete?.fullName || userToDelete?.email} />
      <Toast message={toast.message} type={toast.type} isVisible={toast.isVisible} onClose={() => setToast((p) => ({ ...p, isVisible: false }))} />

      <main className="flex-1 p-3 sm:p-4 md:p-6 lg:p-8 overflow-y-auto bg-slate-50/80">
        <div className="max-w-6xl mx-auto">
          {/* Page header */}
          <div className="mb-6">
            <h1 className="text-xl sm:text-2xl font-extrabold text-slate-900 tracking-tight">Configuración</h1>
            <p className="text-sm text-slate-500 mt-1">Administra tu perfil y preferencias.</p>
          </div>

          <div className="flex flex-col lg:grid lg:grid-cols-[13rem_1fr] xl:grid-cols-[13rem_1fr_16rem] gap-6">
            {/* ─── Col 1: Settings Nav ─── */}
            <aside className="w-full flex-shrink-0">
              {/* Desktop: vertical pill nav */}
              <div className="hidden lg:block bg-white rounded-2xl shadow-sm border border-slate-100 p-2 sticky top-4">
                <nav className="space-y-0.5">
                  {tabs.map((t) => (
                    <button key={t.id} onClick={() => setActiveTab(t.id)}
                      className={`w-full flex items-center gap-2.5 px-3 py-2.5 rounded-xl text-sm font-semibold transition-all duration-200 ${
                        activeTab === t.id ? "bg-usm-blue text-white shadow-sm" : "text-slate-600 hover:bg-slate-50 hover:text-slate-900"
                      }`}
                    >
                      <t.icon className={`w-4 h-4 ${activeTab === t.id ? "text-white" : "text-slate-400"}`} />
                      {t.label}
                      {t.id === "users" && pendingCount > 0 && (
                        <span className={`ml-auto text-[10px] font-bold px-1.5 py-0.5 rounded-full ${activeTab === "users" ? "bg-white/20 text-white" : "bg-red-100 text-red-600"}`}>
                          {pendingCount}
                        </span>
                      )}
                    </button>
                  ))}
                </nav>
              </div>

              {/* Mobile: horizontal scrollable pills */}
              <div className="lg:hidden flex gap-2 overflow-x-auto pb-2 -mx-1 px-1 scrollbar-none">
                {tabs.map((t) => (
                  <button key={t.id} onClick={() => setActiveTab(t.id)}
                    className={`flex items-center gap-2 px-4 py-2 rounded-full text-sm font-semibold whitespace-nowrap border transition-all ${
                      activeTab === t.id ? "bg-usm-blue text-white border-usm-blue shadow-sm" : "text-slate-600 bg-white border-slate-200 hover:border-slate-300"
                    }`}
                  >
                    <t.icon className="w-4 h-4" />
                    {t.label}
                    {t.id === "users" && pendingCount > 0 && (
                      <span className={`text-[10px] font-bold px-1.5 py-0.5 rounded-full ${activeTab === "users" ? "bg-white/20" : "bg-red-100 text-red-600"}`}>
                        {pendingCount}
                      </span>
                    )}
                  </button>
                ))}
              </div>
            </aside>

            {/* ─── Col 2: Content ─── */}
            <div className="min-w-0 space-y-6">

              {/* ════════ PROFILE ════════ */}
              {activeTab === "profile" && (
                <SectionCard>
                  <SectionHeader title="Información Personal" description="Tu información de perfil público."
                    actions={!isEditingProfile ? (
                      <button onClick={() => setIsEditingProfile(true)} className="px-4 py-2 text-sm font-semibold text-usm-blue bg-usm-blue/10 hover:bg-usm-blue/15 rounded-xl transition-colors flex items-center gap-2">
                        <Edit className="w-4 h-4" /> Editar
                      </button>
                    ) : undefined}
                  />
                  <div className="p-5 sm:p-6 space-y-6">
                    {/* Avatar row */}
                    <div className="flex items-center gap-4">
                      <div className="relative">
                        <div className={`w-16 h-16 rounded-2xl flex items-center justify-center text-lg font-bold ${getAvatarColor(email || "")} shadow-lg`}>
                          {getInitials(profileName, email || "")}
                        </div>
                        <div className={`absolute -bottom-1 -right-1 px-1.5 py-0.5 text-[9px] font-bold rounded-lg ring-2 ring-white ${
                          role === "Administrador" ? "bg-purple-600 text-white" : role === "Tutor" ? "bg-blue-600 text-white" : role === "Jurado" ? "bg-amber-600 text-white" : "bg-emerald-600 text-white"
                        }`}>
                          {role?.substring(0, 3)}
                        </div>
                      </div>
                      <div>
                        <p className="text-lg font-bold text-slate-900">{profileName || "Usuario"}</p>
                        <p className="text-sm text-slate-500">{profileEmail}</p>
                      </div>
                    </div>

                    {isEditingProfile ? (
                      <>
                        <div className="grid gap-4 md:grid-cols-2">
                          <InputField label="Nombre Completo" icon={User}>
                            <input type="text" value={profileName} onChange={(e) => setProfileName(e.target.value)} className={inputBase} />
                          </InputField>
                          <InputField label="Correo Electrónico" icon={Mail}>
                            <input type="email" value={profileEmail} onChange={(e) => setProfileEmail(e.target.value)} className={inputBase} />
                          </InputField>
                          <InputField label="Cédula" icon={Shield}>
                            <input type="text" value={profileCedula} onChange={(e) => setProfileCedula(e.target.value)} placeholder="V-12345678" className={inputBase} />
                          </InputField>
                          <InputField label="Teléfono" icon={Phone}>
                            <input type="tel" value={profilePhone} onChange={(e) => setProfilePhone(e.target.value)} className={inputBase} />
                          </InputField>
                          <InputField label="Semestre" icon={BookOpen}>
                            <select value={profileSemester} onChange={(e) => setProfileSemester(e.target.value)} disabled={role === "Estudiante"}
                              className={`${inputBase} appearance-none ${role === "Estudiante" ? "bg-slate-50 text-slate-400 cursor-not-allowed" : "cursor-pointer"}`}>
                              <option value="9no">9no Semestre</option>
                              <option value="10mo">10mo Semestre</option>
                              <option value="N/A">N/A</option>
                            </select>
                          </InputField>
                          <div className="md:col-span-2">
                            <InputField label="Rol del Sistema" icon={Shield}>
                              <input type="text" value={role || ""} disabled className={`${inputBase} bg-slate-50 text-slate-400 cursor-not-allowed`} />
                            </InputField>
                          </div>
                        </div>
                        <div className="flex justify-end gap-3 pt-4 border-t border-slate-100">
                          <button onClick={() => setIsEditingProfile(false)} className="px-4 py-2 text-sm font-semibold text-slate-600 bg-slate-100 hover:bg-slate-200 rounded-xl transition-colors">Cancelar</button>
                          <button onClick={handleSaveProfile} className="px-5 py-2 bg-usm-blue text-white text-sm font-semibold rounded-xl hover:bg-blue-700 active:scale-95 transition-all flex items-center gap-2 shadow-sm">
                            <Save className="w-4 h-4" /> Guardar
                          </button>
                        </div>
                      </>
                    ) : (
                      <div className="grid gap-3 md:grid-cols-2">
                        {[
                          { label: "Correo", value: profileEmail, icon: Mail },
                          { label: "Cédula", value: profileCedula || "—", icon: Shield },
                          { label: "Teléfono", value: profilePhone || "—", icon: Phone },
                          { label: "Semestre", value: profileSemester ? `${profileSemester} Semestre` : "—", icon: BookOpen },
                          { label: "Rol", value: role || "—", icon: Shield },
                        ].map((f) => (
                          <div key={f.label} className="flex items-center gap-3 p-3.5 bg-slate-50/80 rounded-xl border border-slate-100">
                            <div className="w-8 h-8 rounded-lg bg-white border border-slate-200 flex items-center justify-center flex-shrink-0">
                              <f.icon className="w-4 h-4 text-slate-400" />
                            </div>
                            <div className="min-w-0">
                              <p className="text-[11px] font-semibold text-slate-400 uppercase tracking-wider">{f.label}</p>
                              <p className="text-sm font-medium text-slate-800 truncate">{f.value}</p>
                            </div>
                          </div>
                        ))}
                      </div>
                    )}
                  </div>
                </SectionCard>
              )}

              {/* ════════ SECURITY ════════ */}
              {activeTab === "security" && (
                <SectionCard>
                  <SectionHeader title="Seguridad" description="Gestiona tu contraseña y acceso." />
                  <div className="p-5 sm:p-6 space-y-5">
                    <InputField label="Contraseña Actual" icon={Lock}>
                      <input type={showCurrentPw ? "text" : "password"} value={currentPassword} onChange={(e) => setCurrentPassword(e.target.value)} placeholder="••••••••" className={`${inputBase} pr-10`} />
                      <button type="button" onClick={() => setShowCurrentPw(!showCurrentPw)} className="absolute right-3 top-1/2 -translate-y-1/2 text-slate-400 hover:text-slate-600">
                        {showCurrentPw ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
                      </button>
                    </InputField>
                    <div className="grid gap-4 md:grid-cols-2">
                      <InputField label="Nueva Contraseña" icon={Lock}>
                        <input type={showNewPw ? "text" : "password"} value={newPassword} onChange={(e) => setNewPassword(e.target.value)} placeholder="••••••••" className={`${inputBase} pr-10`} />
                        <button type="button" onClick={() => setShowNewPw(!showNewPw)} className="absolute right-3 top-1/2 -translate-y-1/2 text-slate-400 hover:text-slate-600">
                          {showNewPw ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
                        </button>
                      </InputField>
                      <InputField label="Confirmar Contraseña" icon={Lock}>
                        <input type="password" value={confirmPassword} onChange={(e) => setConfirmPassword(e.target.value)} placeholder="••••••••" className={inputBase} />
                      </InputField>
                    </div>
                    {/* Password strength indicator */}
                    {newPassword && (
                      <div className="space-y-2">
                        <div className="flex gap-1">
                          {[1, 2, 3, 4].map((i) => (
                            <div key={i} className={`h-1.5 flex-1 rounded-full transition-colors ${i <= passwordStrength.score ? passwordStrength.color : "bg-slate-200"}`} />
                          ))}
                        </div>
                        <p className="text-xs font-medium text-slate-500">Fortaleza: <span className="text-slate-700">{passwordStrength.label}</span></p>
                      </div>
                    )}
                    {confirmPassword && newPassword !== confirmPassword && (
                      <p className="text-xs text-red-500 flex items-center gap-1"><AlertCircle className="w-3 h-3" /> Las contraseñas no coinciden.</p>
                    )}
                    <div className="flex justify-end pt-4 border-t border-slate-100">
                      <button className="px-5 py-2.5 bg-slate-900 text-white text-sm font-semibold rounded-xl hover:bg-slate-800 active:scale-95 transition-all shadow-sm">
                        Actualizar Contraseña
                      </button>
                    </div>
                  </div>
                </SectionCard>
              )}

              {/* ════════ NOTIFICATIONS ════════ */}
              {activeTab === "notifications" && (
                <SectionCard>
                  <SectionHeader title="Notificaciones" description="Elige qué actualizaciones recibir." />
                  <div className="divide-y divide-slate-100">
                    {[
                      { title: "Correo Electrónico", subtitle: "Entregas, revisiones y aprobaciones", group: "Comunicación", defaultChecked: true },
                      { title: "Notificaciones Push", subtitle: "Alertas instantáneas en el navegador", group: "Comunicación", defaultChecked: false },
                      { title: "Resumen Semanal", subtitle: "Informe de actividad cada lunes", group: "Informes", defaultChecked: true },
                      { title: "Alertas de Vencimiento", subtitle: "Recordatorios de plazos próximos", group: "Plazos", defaultChecked: true },
                    ].map((pref, idx, arr) => {
                      const showGroup = idx === 0 || arr[idx - 1].group !== pref.group;
                      return (
                        <React.Fragment key={pref.title}>
                          {showGroup && (
                            <div className="px-5 sm:px-6 pt-5 pb-2">
                              <p className="text-[11px] font-bold text-slate-400 uppercase tracking-widest">{pref.group}</p>
                            </div>
                          )}
                          <div className="flex items-center justify-between px-5 sm:px-6 py-4 hover:bg-slate-50/50 transition-colors">
                            <div>
                              <p className="text-sm font-semibold text-slate-800">{pref.title}</p>
                              <p className="text-xs text-slate-500 mt-0.5">{pref.subtitle}</p>
                            </div>
                            <label className="relative inline-flex items-center cursor-pointer flex-shrink-0">
                              <input type="checkbox" className="sr-only peer" defaultChecked={pref.defaultChecked} />
                              <div className="w-10 h-6 bg-slate-200 peer-focus:ring-4 peer-focus:ring-usm-blue/20 rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-slate-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-usm-blue" />
                            </label>
                          </div>
                        </React.Fragment>
                      );
                    })}
                  </div>
                </SectionCard>
              )}

              {/* ════════ ADMIN ════════ */}
              {activeTab === "users" && role === "Administrador" && (
                !isDataLoaded ? (
                  <div className="space-y-4">
                    {[1, 2, 3].map((i) => <div key={i} className="h-20 rounded-2xl bg-slate-200/50 animate-pulse" />)}
                  </div>
                ) : (
                  <div className="space-y-5">
                    {/* Admin sub-tabs — segmented control */}
                    <div className="flex gap-1 p-1 bg-slate-100 rounded-xl">
                      {([
                        { id: "pending" as const, label: "Pendientes", icon: AlertCircle, count: pendingCount },
                        { id: "directory" as const, label: "Directorio", icon: Users, count: users.filter((u) => u.status === "active").length },
                        { id: "semesters" as const, label: "Semestres", icon: Calendar, count: semesters.length },
                      ]).map((sub) => (
                        <button key={sub.id} onClick={() => setAdminSubTab(sub.id)}
                          className={`flex-1 flex items-center justify-center gap-2 px-3 py-2.5 rounded-lg text-sm font-semibold transition-all ${
                            adminSubTab === sub.id ? "bg-white text-slate-900 shadow-sm" : "text-slate-500 hover:text-slate-700"
                          }`}
                        >
                          <sub.icon className="w-4 h-4" />
                          <span className="hidden sm:inline">{sub.label}</span>
                          <span className={`text-[10px] font-bold px-1.5 py-0.5 rounded-full ${
                            adminSubTab === sub.id
                              ? sub.id === "pending" && sub.count > 0 ? "bg-red-100 text-red-600" : "bg-slate-100 text-slate-500"
                              : "bg-slate-200/60 text-slate-400"
                          }`}>
                            {sub.count}
                          </span>
                        </button>
                      ))}
                    </div>

                    {/* ── Pending Approvals ── */}
                    {adminSubTab === "pending" && (
                      <SectionCard>
                        <SectionHeader title="Solicitudes Pendientes" description="Usuarios esperando aprobación." />
                        {filteredUsers.length === 0 ? (
                          <div className="py-12 text-center">
                            <div className="w-14 h-14 rounded-2xl bg-emerald-50 flex items-center justify-center mx-auto mb-3">
                              <CheckCircle className="w-7 h-7 text-emerald-400" />
                            </div>
                            <p className="text-sm font-semibold text-slate-700">Sin solicitudes pendientes</p>
                            <p className="text-xs text-slate-400 mt-1">Todos los usuarios han sido procesados.</p>
                          </div>
                        ) : (
                          <div className="divide-y divide-slate-100">
                            {filteredUsers.map((user) => (
                              <div key={user.id} className="flex items-center justify-between gap-4 p-4 sm:p-5 hover:bg-slate-50/50 transition-colors">
                                <div className="flex items-center gap-3 min-w-0">
                                  <div className={`w-10 h-10 rounded-xl flex items-center justify-center text-sm font-bold flex-shrink-0 ${getAvatarColor(user.email)}`}>
                                    {getInitials(user.fullName || "", user.email)}
                                  </div>
                                  <div className="min-w-0">
                                    <p className="text-sm font-bold text-slate-800 truncate">{user.fullName || user.email}</p>
                                    <p className="text-xs text-slate-500 truncate">{user.email}</p>
                                  </div>
                                </div>
                                <div className="flex items-center gap-2 flex-shrink-0">
                                  <RoleBadge role={user.role} />
                                  <button onClick={() => handleStatusUpdate(user.id, "active")}
                                    className="px-3 py-1.5 text-xs font-bold text-white bg-emerald-600 hover:bg-emerald-700 rounded-lg shadow-sm transition-all active:scale-95 flex items-center gap-1.5">
                                    <Check className="w-3 h-3" /> Aprobar
                                  </button>
                                </div>
                              </div>
                            ))}
                          </div>
                        )}
                      </SectionCard>
                    )}

                    {/* ── User Directory ── */}
                    {adminSubTab === "directory" && (
                      <SectionCard>
                        <SectionHeader title="Directorio de Usuarios" description="Todos los usuarios activos del sistema."
                          actions={
                            <button onClick={() => { setEditingUser(null); setIsUserModalOpen(true); }}
                              className="px-4 py-2 bg-usm-blue text-white text-sm font-semibold rounded-xl hover:bg-blue-700 transition-all shadow-sm flex items-center gap-2 active:scale-95">
                              <Plus className="w-4 h-4" /> Nuevo
                            </button>
                          }
                        />
                        {/* Filters */}
                        <div className="p-4 sm:px-6 flex flex-col sm:flex-row gap-3 border-b border-slate-100">
                          <div className="relative flex-1">
                            <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-400" />
                            <input type="text" value={userSearch} onChange={(e) => setUserSearch(e.target.value)} placeholder="Buscar por nombre o correo..."
                              className="w-full pl-10 pr-4 py-2 border border-slate-200 rounded-xl text-sm focus:ring-2 focus:ring-usm-blue/20 focus:border-usm-blue outline-none" />
                          </div>
                          <select value={roleFilter} onChange={(e) => setRoleFilter(e.target.value)}
                            className="px-3 py-2 border border-slate-200 rounded-xl text-sm bg-white cursor-pointer focus:ring-2 focus:ring-usm-blue/20 outline-none">
                            <option value="all">Todos los roles</option>
                            <option value="Administrador">Administrador</option>
                            <option value="Tutor">Tutor</option>
                            <option value="Jurado">Jurado</option>
                            <option value="Estudiante">Estudiante</option>
                          </select>
                        </div>

                        {/* Desktop Table */}
                        <div className="hidden md:block overflow-x-auto">
                          <table className="w-full text-sm">
                            <thead className="text-[11px] text-slate-500 uppercase tracking-wider bg-slate-50/60 border-b border-slate-100">
                              <tr>
                                <th className="px-6 py-3 text-left font-semibold">Usuario</th>
                                <th className="px-6 py-3 text-left font-semibold">Rol</th>
                                <th className="px-6 py-3 text-left font-semibold">Estado</th>
                                <th className="px-6 py-3 text-right font-semibold">Acciones</th>
                              </tr>
                            </thead>
                            <tbody className="divide-y divide-slate-100">
                              {paginatedUsers.map((u) => (
                                <tr key={u.id} className="hover:bg-slate-50/60 transition-colors">
                                  <td className="px-6 py-3.5">
                                    <div className="flex items-center gap-3">
                                      <div className={`w-9 h-9 rounded-lg flex items-center justify-center text-xs font-bold flex-shrink-0 ${getAvatarColor(u.email)}`}>
                                        {getInitials(u.fullName || "", u.email)}
                                      </div>
                                      <div className="min-w-0">
                                        <p className="font-semibold text-slate-800 truncate">{u.fullName || u.email}</p>
                                        <p className="text-xs text-slate-400 truncate">{u.email}</p>
                                      </div>
                                    </div>
                                  </td>
                                  <td className="px-6 py-3.5"><RoleBadge role={u.role} /></td>
                                  <td className="px-6 py-3.5"><StatusBadge status={u.status || "pending"} /></td>
                                  <td className="px-6 py-3.5 text-right">
                                    <div className="flex items-center justify-end gap-1">
                                      <button onClick={() => { setEditingUser(u); setIsUserModalOpen(true); }} className="p-1.5 text-slate-400 hover:text-usm-blue hover:bg-blue-50 rounded-lg transition-colors" title="Editar">
                                        <Edit className="w-4 h-4" />
                                      </button>
                                      {u.role !== "Administrador" && u.email !== email && (
                                        <button onClick={() => { setUserToDelete(u); setIsDeleteModalOpen(true); }} className="p-1.5 text-slate-400 hover:text-red-600 hover:bg-red-50 rounded-lg transition-colors" title="Eliminar">
                                          <Trash2 className="w-4 h-4" />
                                        </button>
                                      )}
                                    </div>
                                  </td>
                                </tr>
                              ))}
                            </tbody>
                          </table>
                        </div>

                        {/* Mobile Cards */}
                        <div className="md:hidden divide-y divide-slate-100">
                          {paginatedUsers.map((u) => (
                            <div key={u.id} className="p-4 hover:bg-slate-50/50 transition-colors">
                              <div className="flex items-center justify-between gap-3">
                                <div className="flex items-center gap-3 min-w-0">
                                  <div className={`w-10 h-10 rounded-lg flex items-center justify-center text-sm font-bold flex-shrink-0 ${getAvatarColor(u.email)}`}>
                                    {getInitials(u.fullName || "", u.email)}
                                  </div>
                                  <div className="min-w-0">
                                    <p className="font-semibold text-slate-800 truncate">{u.fullName || u.email}</p>
                                    <p className="text-xs text-slate-400 truncate">{u.email}</p>
                                  </div>
                                </div>
                                <div className="flex items-center gap-1 flex-shrink-0">
                                  <button onClick={() => { setEditingUser(u); setIsUserModalOpen(true); }} className="p-2 text-usm-blue hover:bg-blue-50 rounded-lg"><Edit className="w-4 h-4" /></button>
                                  {u.role !== "Administrador" && u.email !== email && (
                                    <button onClick={() => { setUserToDelete(u); setIsDeleteModalOpen(true); }} className="p-2 text-red-500 hover:bg-red-50 rounded-lg"><Trash2 className="w-4 h-4" /></button>
                                  )}
                                </div>
                              </div>
                              <div className="mt-2 flex flex-wrap gap-1.5">
                                <RoleBadge role={u.role} />
                                <StatusBadge status={u.status || "pending"} />
                              </div>
                            </div>
                          ))}
                        </div>

                        {/* Pagination */}
                        {filteredUsers.length > usersPerPage && (
                          <div className="p-4 border-t border-slate-100 flex items-center justify-between">
                            <p className="text-xs text-slate-500">{(currentPage - 1) * usersPerPage + 1}-{Math.min(currentPage * usersPerPage, filteredUsers.length)} de {filteredUsers.length}</p>
                            <div className="flex items-center gap-1">
                              <button onClick={() => setCurrentPage((p) => Math.max(1, p - 1))} disabled={currentPage === 1} className="p-1.5 text-slate-500 hover:bg-slate-100 rounded-lg disabled:opacity-30"><ChevronLeft className="w-4 h-4" /></button>
                              <span className="text-xs font-semibold text-slate-600 px-2">{currentPage}/{totalPages}</span>
                              <button onClick={() => setCurrentPage((p) => Math.min(totalPages, p + 1))} disabled={currentPage === totalPages} className="p-1.5 text-slate-500 hover:bg-slate-100 rounded-lg disabled:opacity-30"><ChevronRight className="w-4 h-4" /></button>
                            </div>
                          </div>
                        )}
                      </SectionCard>
                    )}

                    {/* ── Semesters ── */}
                    {adminSubTab === "semesters" && (
                      <SectionCard>
                        <SectionHeader title="Períodos Académicos" description="Registra y gestiona semestres. Los proyectos se almacenan en el período correspondiente." />
                        <div className="p-5 sm:p-6 space-y-6">
                          {/* Add form */}
                          <div className="space-y-4">
                            <p className="text-xs font-bold text-slate-400 uppercase tracking-widest">Nuevo Semestre</p>
                            {/* Row 1: Year + Period */}
                            <div className="grid gap-3 sm:grid-cols-2">
                              <div>
                                <label className="text-xs font-semibold text-slate-500 mb-1.5 block">Año</label>
                                <input type="number" min={2020} max={2099} value={newSemesterYear} onChange={(e) => setNewSemesterYear(Number(e.target.value))}
                                  className="w-full px-4 py-2.5 border border-slate-200 rounded-xl text-sm focus:ring-2 focus:ring-usm-blue/20 focus:border-usm-blue outline-none" placeholder="2026" />
                              </div>
                              <div>
                                <label className="text-xs font-semibold text-slate-500 mb-1.5 block">Período</label>
                                <select value={newSemesterPeriod} onChange={(e) => {
                                  const val = e.target.value;
                                  setNewSemesterPeriod(val);
                                  if (val === "01") { setNewStartMonth(1); setNewEndMonth(6); }
                                  else { setNewStartMonth(7); setNewEndMonth(12); }
                                }}
                                  className="w-full px-4 py-2.5 border border-slate-200 rounded-xl text-sm focus:ring-2 focus:ring-usm-blue/20 focus:border-usm-blue outline-none cursor-pointer">
                                  <option value="01">01 — Primer semestre</option>
                                  <option value="02">02 — Segundo semestre</option>
                                </select>
                              </div>
                            </div>
                            {/* Row 2: Start/End months */}
                            <div className="grid gap-3 sm:grid-cols-2">
                              <div>
                                <label className="text-xs font-semibold text-slate-500 mb-1.5 block">Mes de inicio</label>
                                <select value={newStartMonth} onChange={(e) => setNewStartMonth(Number(e.target.value))}
                                  className="w-full px-4 py-2.5 border border-slate-200 rounded-xl text-sm focus:ring-2 focus:ring-usm-blue/20 focus:border-usm-blue outline-none cursor-pointer">
                                  {Array.from({ length: 12 }, (_, i) => i + 1).map((m) => (
                                    <option key={m} value={m}>{MONTH_NAMES[m]}</option>
                                  ))}
                                </select>
                              </div>
                              <div>
                                <label className="text-xs font-semibold text-slate-500 mb-1.5 block">Mes de fin</label>
                                <select value={newEndMonth} onChange={(e) => setNewEndMonth(Number(e.target.value))}
                                  className="w-full px-4 py-2.5 border border-slate-200 rounded-xl text-sm focus:ring-2 focus:ring-usm-blue/20 focus:border-usm-blue outline-none cursor-pointer">
                                  {Array.from({ length: 12 }, (_, i) => i + 1).map((m) => (
                                    <option key={m} value={m}>{MONTH_NAMES[m]}</option>
                                  ))}
                                </select>
                              </div>
                            </div>
                            {/* Preview + Submit */}
                            <div className="flex items-center justify-between gap-3 pt-1">
                              <p className="text-xs text-slate-400">
                                Vista previa: <span className="font-semibold text-slate-600">{newSemesterYear}-{newSemesterPeriod}</span>
                                {" · "}{MONTH_NAMES[newStartMonth]} {newSemesterYear} – {MONTH_NAMES[newEndMonth]} {newEndMonth < newStartMonth ? newSemesterYear + 1 : newSemesterYear}
                              </p>
                              <button onClick={handleAddSemester} disabled={isSavingSemester}
                                className="px-5 py-2.5 bg-usm-blue text-white text-sm font-semibold rounded-xl hover:bg-blue-700 transition-all shadow-sm disabled:opacity-50 flex items-center gap-1.5 flex-shrink-0">
                                <Plus className="w-4 h-4" /> Crear período
                              </button>
                            </div>
                          </div>

                          {/* Divider */}
                          <hr className="border-slate-200" />

                          {/* Existing list */}
                          <div className="space-y-3">
                            <p className="text-xs font-bold text-slate-400 uppercase tracking-widest">Períodos registrados</p>
                            {semesters.length === 0 ? (
                              <div className="text-sm text-slate-500 bg-slate-50 border border-dashed border-slate-200 rounded-xl p-6 text-center">Sin semestres registrados.</div>
                            ) : (
                              <div className="divide-y divide-slate-100 border border-slate-200 rounded-xl overflow-hidden">
                                {semesters.map((s) => (
                                  <div key={s.id} className="flex items-center justify-between px-4 py-3 bg-white hover:bg-slate-50/50 transition-colors">
                                    <div className="flex items-center gap-3 min-w-0">
                                      <div className={`w-2 h-2 rounded-full flex-shrink-0 ${s.is_active ? "bg-emerald-500" : "bg-slate-300"}`} />
                                      <div className="min-w-0">
                                        <div className="flex items-center gap-2">
                                          <p className="text-sm font-semibold text-slate-800">{s.period}</p>
                                          {s.is_active && <span className="text-[10px] font-bold text-emerald-700 bg-emerald-50 border border-emerald-200 px-1.5 py-0.5 rounded-full">ACTIVO</span>}
                                        </div>
                                        <p className="text-xs text-slate-400">{formatSemesterFull(s)}</p>
                                      </div>
                                    </div>
                                    <div className="flex items-center gap-1 flex-shrink-0">
                                      {!s.is_active && (
                                        <button onClick={async () => { try { await setActiveSemester(s.id); showToast("Período activado.", "success"); await loadSemesters(); } catch { showToast("Error.", "error"); } }}
                                          disabled={isSavingSemester}
                                          className="px-2.5 py-1.5 text-xs font-semibold text-emerald-700 hover:bg-emerald-50 rounded-lg transition-colors disabled:opacity-40" title="Activar">
                                          Activar
                                        </button>
                                      )}
                                      <button onClick={() => handleDeleteSemester(s.id)} disabled={isSavingSemester}
                                        className="p-1.5 text-red-500 hover:bg-red-50 rounded-lg transition-colors disabled:opacity-40" title="Eliminar">
                                        <Trash2 className="w-4 h-4" />
                                      </button>
                                    </div>
                                  </div>
                                ))}
                              </div>
                            )}
                          </div>
                        </div>
                      </SectionCard>
                    )}
                  </div>
                )
              )}
            </div>

            {/* ─── Col 3: Context Panel ─── */}
            {/* Desktop: sticky right column. Mobile/Tablet: stacks below content. */}
            <div className="hidden xl:block">
              <div className="sticky top-4 space-y-4">
                <ContextPanel activeTab={activeTab} role={role} pendingCount={pendingCount} userCount={users.length} />
              </div>
            </div>

            {/* Mobile/Tablet: context panel below content */}
            <div className="xl:hidden lg:col-span-2">
              <details className="group">
                <summary className="flex items-center justify-center gap-2 px-4 py-3 bg-white/80 backdrop-blur-sm rounded-2xl border border-slate-100 cursor-pointer text-sm font-semibold text-slate-600 hover:text-slate-800 hover:bg-slate-50 transition-colors select-none">
                  <Activity className="w-4 h-4 text-slate-400" />
                  Más información
                  <ChevronRight className="w-4 h-4 text-slate-400 transition-transform group-open:rotate-90" />
                </summary>
                <div className="mt-3">
                  <ContextPanel activeTab={activeTab} role={role} pendingCount={pendingCount} userCount={users.length} />
                </div>
              </details>
            </div>
          </div>
        </div>
      </main>
    </>
  );
}
