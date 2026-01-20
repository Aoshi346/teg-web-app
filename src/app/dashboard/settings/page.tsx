"use client";

import React, { useState, useEffect } from "react";
import DashboardHeader from "@/components/layout/DashboardHeader";
import PageTransition from "@/components/ui/PageTransition";
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
} from "lucide-react";
import UserModal, { UserData } from "@/components/ui/UserModal";
import Toast, { ToastType } from "@/components/ui/Toast";
import DeleteModal from "@/components/ui/DeleteModal";
import { ChevronLeft, ChevronRight } from "lucide-react";

export default function SettingsPage({
  handleSidebarCollapse,
  handleMobileSidebarToggle,
  isSidebarCollapsed,
  isMobileSidebarOpen,
}: {
  handleSidebarCollapse?: () => void;
  handleMobileSidebarToggle?: () => void;
  isSidebarCollapsed?: boolean;
  isMobileSidebarOpen?: boolean;
}) {
  const [role, setRole] = useState<string | null>(null);
  const [email, setEmail] = useState<string | null>(null);
  const [activeTab, setActiveTab] = useState<
    "profile" | "security" | "notifications" | "users"
  >("profile");

  // Profile State
  // const [avatarPreview, setAvatarPreview] = useState<string | null>(null);
  const [profileName, setProfileName] = useState("");
  const [profileEmail, setProfileEmail] = useState("");
  const [profilePhone, setProfilePhone] = useState("");
  const [profileSemester, setProfileSemester] = useState("9no"); // Default, could be loaded
  const [isEditingProfile, setIsEditingProfile] = useState(false);

  // Users State (Admin)
  const [users, setUsers] = useState<UserData[]>([]);
  const [isUserModalOpen, setIsUserModalOpen] = useState(false);
  const [editingUser, setEditingUser] = useState<UserData | null>(null);

  // Delete Modal State
  const [isDeleteModalOpen, setIsDeleteModalOpen] = useState(false);
  const [userToDelete, setUserToDelete] = useState<UserData | null>(null);

  // Pagination State
  const [currentPage, setCurrentPage] = useState(1);
  const usersPerPage = 5;
  const totalPages = Math.max(1, Math.ceil(users.length / usersPerPage));
  const paginatedUsers = users.slice(
    (currentPage - 1) * usersPerPage,
    currentPage * usersPerPage,
  );

  // Toast State
  const [toast, setToast] = useState<{
    message: string;
    type: ToastType;
    isVisible: boolean;
  }>({
    message: "",
    type: "info",
    isVisible: false,
  });

  const showToast = (message: string, type: ToastType = "info") => {
    setToast({ message, type, isVisible: true });
  };

  // Load users helper
  const loadUsers = React.useCallback(async () => {
    try {
      const storedUsers = await getAllUsers();
      const mappedUsers: UserData[] = storedUsers.map((u, index) => ({
        id: u.id || index + 1,
        fullName: u.fullName || u.email.split("@")[0],
        email: u.email,
        role: u.role,
        semester: u.semester || "N/A",
        phone: u.phone || "",
        status: u.status,
      }));

      // Always show pending first
      mappedUsers.sort((a, b) => {
        if (a.status === b.status) return 0;
        return a.status === "pending" ? -1 : 1;
      });

      setUsers(mappedUsers);
      setCurrentPage(1); // reset pagination after reload
    } catch (e) {
      console.error(e);
      showToast("Error al cargar usuarios", "error");
    }
  }, []);

  useEffect(() => {
    const userRole = getUserRole();
    const userEmail = getUserEmail();
    setRole(userRole);
    setEmail(userEmail);

    // Initialize profile
    const sessionUser = getUser();
    if (sessionUser) {
      setProfileEmail(sessionUser.email || "");
      setProfileName(sessionUser.fullName || sessionUser.email.split("@")[0] || "Usuario");
      setProfilePhone(sessionUser.phone || "");
      setProfileSemester(sessionUser.semester || "");
    } else if (typeof window !== "undefined") {
      setProfileEmail(userEmail || "");
      setProfileName(userEmail?.split("@")[0] || "Usuario");
    }

    // Load users if admin
    if (userRole === "Admin") {
      loadUsers();
    }
  }, [activeTab, loadUsers]); // Reload when tab changes too

  const openDeleteModal = (user: UserData) => {
    setUserToDelete(user);
    setIsDeleteModalOpen(true);
  };

  const confirmDeleteUser = async () => {
    if (!userToDelete?.id) return;
    try {
      await deleteUserApi(userToDelete.id);
      showToast("Usuario eliminado correctamente.", "success");
      await loadUsers();
    } catch (error) {
      console.error(error);
      showToast("Error al eliminar usuario", "error");
    } finally {
      setUserToDelete(null);
      setIsDeleteModalOpen(false);
    }
  };

  const handleStatusUpdate = async (
    id: number | undefined,
    newStatus: "active" | "pending",
  ) => {
    if (!id) return;
    try {
      await updateStatusById(id, newStatus);
      await loadUsers(); // Refresh list
      showToast(
        `Usuario ${newStatus === "active" ? "activado" : "desactivado"} correctamente.`,
        "success",
      );
    } catch {
      showToast("Error al actualizar estado", "error");
    }
  };

  const handleAddUser = () => {
    setEditingUser(null);
    setIsUserModalOpen(true);
  };

  const handleEditUser = (user: UserData) => {
    setEditingUser(user);
    setIsUserModalOpen(true);
  };

  const handleSaveUser = async (
    userData: Omit<UserData, "id"> & { id?: number },
  ) => {
    const payload: AuthUser = {
      email: userData.email,
      role: userData.role as AuthUser["role"],
      fullName: userData.fullName,
      semester: userData.semester,
      phone: userData.phone,
      password: "password123", // default password for manual creation
      status: "pending",
    };

    try {
      if (userData.id) {
        await updateUserApi(userData.id, payload);
        showToast("Usuario actualizado correctamente.", "success");
      } else {
        await createUser(payload);
        showToast(
          "Usuario creado correctamente. Estado inicial: pendiente.",
          "success",
        );
      }
      await loadUsers();
    } catch (error) {
      console.error(error);
      showToast("Error al guardar usuario", "error");
    } finally {
      setIsUserModalOpen(false);
    }
  };

  const handleSaveProfile = async () => {
    try {
      await updateProfile({
        fullName: profileName,
        phone: profilePhone,
        semester: profileSemester,
      });
      setIsEditingProfile(false);
      showToast("Perfil actualizado correctamente.", "success");
    } catch (err) {
      console.error(err);
      showToast("No se pudo actualizar el perfil.", "error");
    }
  };

  // Deterministic avatar color helper
  const getAvatarColor = (email: string) => {
    const colors = [
      "bg-blue-100 text-blue-600",
      "bg-purple-100 text-purple-600",
      "bg-emerald-100 text-emerald-600",
      "bg-amber-100 text-amber-600",
    ];
    return colors[email.length % colors.length];
  };

  return (
    <>
      <DashboardHeader
        pageTitle="Configuración"
        isSidebarCollapsed={isSidebarCollapsed}
        isMobileSidebarOpen={isMobileSidebarOpen}
        onMobileSidebarToggle={handleMobileSidebarToggle}
        onSidebarCollapse={handleSidebarCollapse}
      />

      <UserModal
        isOpen={isUserModalOpen}
        onClose={() => setIsUserModalOpen(false)}
        onSave={handleSaveUser}
        initialData={editingUser}
      />

      <DeleteModal
        isOpen={isDeleteModalOpen}
        onClose={() => setIsDeleteModalOpen(false)}
        onConfirm={confirmDeleteUser}
        userName={userToDelete?.fullName || userToDelete?.email}
      />

      <Toast
        message={toast.message}
        type={toast.type}
        isVisible={toast.isVisible}
        onClose={() => setToast((prev) => ({ ...prev, isVisible: false }))}
      />

      <PageTransition>
        <main className="flex-1 p-4 md:p-6 lg:p-8 overflow-y-auto bg-gray-50/50">
          <div className="max-w-7xl mx-auto">
            {/* Page Header */}
            <div className="mb-6">
              <h1 className="text-2xl font-bold text-gray-900 tracking-tight">
                Configuración
              </h1>
              <p className="text-gray-500 text-sm mt-1">
                Administra tu perfil y preferencias del sistema.
              </p>
            </div>

            {/* Main Grid Layout */}
            <div className="flex flex-col lg:flex-row gap-6">
              {/* Settings Sidebar */}
              <aside className="w-full lg:w-56 flex-shrink-0">
                <div className="bg-white rounded-xl shadow-sm border border-gray-100 p-3 lg:sticky lg:top-6">
                  <nav className="flex lg:flex-col gap-1 overflow-x-auto lg:overflow-visible">
                    {[
                      { id: "profile", label: "Perfil", icon: User },
                      { id: "security", label: "Seguridad", icon: Lock },
                      {
                        id: "notifications",
                        label: "Notificaciones",
                        icon: Bell,
                      },
                      ...(role === "Admin"
                        ? [{ id: "users", label: "Usuarios", icon: UserCog }]
                        : []),
                    ].map((item) => (
                      <button
                        key={item.id}
                        onClick={() =>
                          setActiveTab(item.id as typeof activeTab)
                        }
                        className={`flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm font-medium transition-all duration-200 whitespace-nowrap w-full text-left ${
                          activeTab === item.id
                            ? "bg-blue-50 text-blue-700"
                            : "text-gray-600 hover:bg-gray-50 hover:text-gray-900"
                        }`}
                      >
                        <item.icon
                          className={`w-4 h-4 ${activeTab === item.id ? "text-blue-600" : "text-gray-400"}`}
                        />
                        {item.label}
                      </button>
                    ))}
                  </nav>
                </div>
              </aside>

              {/* Main Content Area */}
              <div className="flex-1 space-y-6 animate-in fade-in slide-in-from-bottom-4 duration-500">
                {/* Profile Section */}
                {activeTab === "profile" && (
                  <div className="bg-white rounded-2xl shadow-sm border border-gray-100 overflow-hidden">
                    <div className="p-6 border-b border-gray-50 bg-gray-50/30 flex items-center justify-between">
                      <div>
                        <h2 className="text-lg font-bold text-gray-900">
                          Información Personal
                        </h2>
                        <p className="text-sm text-gray-500">
                          Tu información de perfil.
                        </p>
                      </div>
                      {!isEditingProfile && (
                        <button
                          onClick={() => setIsEditingProfile(true)}
                          className="px-4 py-2 text-sm font-medium text-blue-600 bg-blue-50 hover:bg-blue-100 rounded-lg transition-colors flex items-center gap-2"
                        >
                          <Edit className="w-4 h-4" />
                          Editar
                        </button>
                      )}
                    </div>
                    <div className="p-6 space-y-6">
                      {/* Avatar & Name with Role Badge */}
                      <div className="flex items-center gap-4">
                        <div className="relative">
                          <div
                            className={`w-16 h-16 rounded-full flex items-center justify-center text-lg font-bold text-white ${getAvatarColor(email || "")}`}
                          >
                            {profileName
                              ? profileName
                                  .split(" ")
                                  .map((n: string) => n[0])
                                  .join("")
                                  .substring(0, 2)
                                  .toUpperCase()
                              : "U"}
                          </div>
                          {/* Role Badge */}
                          <span
                            className={`absolute -bottom-1 -right-1 px-2 py-0.5 text-[10px] font-bold rounded-full ring-2 ring-white ${
                              role === "Admin"
                                ? "bg-purple-600 text-white"
                                : role === "Profesor"
                                  ? "bg-blue-600 text-white"
                                  : "bg-green-600 text-white"
                            }`}
                          >
                            {role}
                          </span>
                        </div>
                        <div>
                          <p className="text-lg font-semibold text-gray-900">
                            {profileName || "Usuario"}
                          </p>
                          <p className="text-sm text-gray-500">
                            {profileEmail}
                          </p>
                        </div>
                      </div>

                      {/* View Mode */}
                      {!isEditingProfile ? (
                        <div className="grid gap-4 md:grid-cols-2">
                          <div className="p-4 bg-gray-50 rounded-xl">
                            <p className="text-xs font-medium text-gray-500 uppercase tracking-wide mb-1">
                              Correo Electrónico
                            </p>
                            <p className="text-sm font-medium text-gray-900">
                              {profileEmail || "—"}
                            </p>
                          </div>
                          <div className="p-4 bg-gray-50 rounded-xl">
                            <p className="text-xs font-medium text-gray-500 uppercase tracking-wide mb-1">
                              Teléfono
                            </p>
                            <p className="text-sm font-medium text-gray-900">
                              {profilePhone || "—"}
                            </p>
                          </div>
                          <div className="p-4 bg-gray-50 rounded-xl">
                            <p className="text-xs font-medium text-gray-500 uppercase tracking-wide mb-1">
                              Semestre
                            </p>
                            <p className="text-sm font-medium text-gray-900">
                              {profileSemester
                                ? `${profileSemester} Semestre`
                                : "—"}
                            </p>
                          </div>
                          <div className="p-4 bg-gray-50 rounded-xl">
                            <p className="text-xs font-medium text-gray-500 uppercase tracking-wide mb-1">
                              Rol del Sistema
                            </p>
                            <p className="text-sm font-medium text-gray-900">
                              {role || "—"}
                            </p>
                          </div>
                        </div>
                      ) : (
                        /* Edit Mode */
                        <div className="grid gap-4 md:grid-cols-2">
                          {/* Full Name */}
                          <div className="space-y-1.5">
                            <label className="text-xs font-medium text-gray-600 uppercase tracking-wide">
                              Nombre Completo
                            </label>
                            <div className="relative">
                              <User className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400" />
                              <input
                                type="text"
                                value={profileName}
                                onChange={(e) => setProfileName(e.target.value)}
                                className="w-full pl-10 pr-4 py-2.5 border border-gray-200 rounded-xl bg-white text-gray-900 text-sm focus:ring-2 focus:ring-blue-500/20 focus:border-blue-500 outline-none"
                              />
                            </div>
                          </div>

                          {/* Email */}
                          <div className="space-y-1.5">
                            <label className="text-xs font-medium text-gray-600 uppercase tracking-wide">
                              Correo Electrónico
                            </label>
                            <div className="relative">
                              <Mail className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400" />
                              <input
                                type="email"
                                value={profileEmail}
                                onChange={(e) =>
                                  setProfileEmail(e.target.value)
                                }
                                className="w-full pl-10 pr-4 py-2.5 border border-gray-200 rounded-xl bg-white text-gray-900 text-sm focus:ring-2 focus:ring-blue-500/20 focus:border-blue-500 outline-none"
                              />
                            </div>
                          </div>

                          {/* Phone */}
                          <div className="space-y-1.5">
                            <label className="text-xs font-medium text-gray-600 uppercase tracking-wide">
                              Teléfono
                            </label>
                            <div className="relative">
                              <Phone className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400" />
                              <input
                                type="tel"
                                value={profilePhone}
                                onChange={(e) =>
                                  setProfilePhone(e.target.value)
                                }
                                className="w-full pl-10 pr-4 py-2.5 border border-gray-200 rounded-xl bg-white text-gray-900 text-sm focus:ring-2 focus:ring-blue-500/20 focus:border-blue-500 outline-none"
                              />
                            </div>
                          </div>

                          {/* Semester */}
                          <div className="space-y-1.5">
                            <label className="text-xs font-medium text-gray-600 uppercase tracking-wide">
                              Semestre
                            </label>
                            <div className="relative">
                              <BookOpen className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400" />
                              <select
                                value={profileSemester}
                                onChange={(e) =>
                                  setProfileSemester(e.target.value)
                                }
                                className="w-full pl-10 pr-4 py-2.5 border border-gray-200 rounded-xl bg-white text-gray-900 text-sm focus:ring-2 focus:ring-blue-500/20 focus:border-blue-500 outline-none appearance-none cursor-pointer"
                              >
                                <option value="9no">9no Semestre</option>
                                <option value="10mo">10mo Semestre</option>
                                <option value="N/A">N/A</option>
                              </select>
                            </div>
                          </div>

                          {/* Role - Always Read Only */}
                          <div className="space-y-1.5 md:col-span-2">
                            <label className="text-xs font-medium text-gray-600 uppercase tracking-wide">
                              Rol del Sistema
                            </label>
                            <div className="relative">
                              <Shield className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400" />
                              <input
                                type="text"
                                value={role || ""}
                                disabled
                                className="w-full pl-10 pr-4 py-2.5 border border-gray-200 rounded-xl bg-gray-50 text-gray-500 text-sm cursor-not-allowed"
                              />
                              <span className="absolute right-3 top-1/2 -translate-y-1/2 text-xs text-gray-400">
                                Solo lectura
                              </span>
                            </div>
                          </div>
                        </div>
                      )}

                      {/* Actions */}
                      {isEditingProfile && (
                        <div className="flex justify-end gap-3 pt-4 border-t border-gray-100">
                          <button
                            onClick={() => setIsEditingProfile(false)}
                            className="px-4 py-2 text-sm font-medium text-gray-600 bg-gray-100 hover:bg-gray-200 rounded-lg transition-colors"
                          >
                            Cancelar
                          </button>
                          <button
                            onClick={() => {
                              handleSaveProfile();
                              setIsEditingProfile(false);
                            }}
                            className="px-5 py-2 bg-blue-600 text-white text-sm font-medium rounded-lg hover:bg-blue-700 active:scale-95 transition-all flex items-center gap-2"
                          >
                            <Save className="w-4 h-4" />
                            Guardar
                          </button>
                        </div>
                      )}
                    </div>
                  </div>
                )}

                {/* Security Section */}
                {activeTab === "security" && (
                  <div className="bg-white rounded-2xl shadow-sm border border-gray-100 overflow-hidden">
                    <div className="p-6 border-b border-gray-50 bg-gray-50/30">
                      <h2 className="text-lg font-bold text-gray-900">
                        Seguridad
                      </h2>
                      <p className="text-sm text-gray-500">
                        Gestiona tu contraseña y seguridad de la cuenta.
                      </p>
                    </div>
                    <div className="p-6 space-y-5">
                      <div className="space-y-2">
                        <label className="text-sm font-medium text-gray-700">
                          Contraseña Actual
                        </label>
                        <input
                          type="password"
                          placeholder="••••••••"
                          className="w-full px-4 py-2.5 border border-gray-200 rounded-xl focus:ring-2 focus:ring-blue-500/20 focus:border-blue-500 outline-none transition-all"
                        />
                      </div>
                      <div className="grid gap-5 md:grid-cols-2">
                        <div className="space-y-2">
                          <label className="text-sm font-medium text-gray-700">
                            Nueva Contraseña
                          </label>
                          <input
                            type="password"
                            placeholder="••••••••"
                            className="w-full px-4 py-2.5 border border-gray-200 rounded-xl focus:ring-2 focus:ring-blue-500/20 focus:border-blue-500 outline-none transition-all"
                          />
                        </div>
                        <div className="space-y-2">
                          <label className="text-sm font-medium text-gray-700">
                            Confirmar Contraseña
                          </label>
                          <input
                            type="password"
                            placeholder="••••••••"
                            className="w-full px-4 py-2.5 border border-gray-200 rounded-xl focus:ring-2 focus:ring-blue-500/20 focus:border-blue-500 outline-none transition-all"
                          />
                        </div>
                      </div>
                      <div className="flex justify-end pt-6">
                        <button className="px-5 py-2.5 bg-gray-900 text-white text-sm font-medium rounded-xl hover:bg-gray-800 active:transform active:scale-95 transition-all shadow-sm">
                          Actualizar Contraseña
                        </button>
                      </div>
                    </div>
                  </div>
                )}

                {/* Notifications Section */}
                {activeTab === "notifications" && (
                  <div className="bg-white rounded-2xl shadow-sm border border-gray-100 overflow-hidden">
                    <div className="p-6 border-b border-gray-50 bg-gray-50/30">
                      <h2 className="text-lg font-bold text-gray-900">
                        Preferencias de Notificación
                      </h2>
                      <p className="text-sm text-gray-500">
                        Elige qué actualizaciones quieres recibir.
                      </p>
                    </div>
                    <div className="p-6 space-y-6">
                      <div className="flex items-center justify-between py-2">
                        <div className="space-y-0.5">
                          <p className="text-base font-medium text-gray-900">
                            Notificaciones por Email
                          </p>
                          <p className="text-sm text-gray-500">
                            Recibe actualizaciones sobre entregas y revisiones.
                          </p>
                        </div>
                        <label className="relative inline-flex items-center cursor-pointer">
                          <input
                            type="checkbox"
                            className="sr-only peer"
                            defaultChecked
                          />
                          <div className="w-11 h-6 bg-gray-200 peer-focus:outline-none peer-focus:ring-4 peer-focus:ring-blue-300/30 rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-blue-600"></div>
                        </label>
                      </div>
                      <div className="flex items-center justify-between py-2 border-t border-gray-100 pt-6">
                        <div className="space-y-0.5">
                          <p className="text-base font-medium text-gray-900">
                            Notificaciones Push
                          </p>
                          <p className="text-sm text-gray-500">
                            Notificaciones instantáneas en el navegador.
                          </p>
                        </div>
                        <label className="relative inline-flex items-center cursor-pointer">
                          <input type="checkbox" className="sr-only peer" />
                          <div className="w-11 h-6 bg-gray-200 peer-focus:outline-none peer-focus:ring-4 peer-focus:ring-blue-300/30 rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-blue-600"></div>
                        </label>
                      </div>
                    </div>
                  </div>
                )}

                {/* Admin Users Section */}
                {activeTab === "users" && role === "Admin" && (
                  <div className="space-y-8">
                    {/* Pending Approvals Section */}
                    {paginatedUsers.some((u) => u.status === "pending") && (
                      <div className="bg-amber-50 rounded-2xl shadow-sm border border-amber-100 overflow-hidden">
                        <div className="p-4 sm:p-6 border-b border-amber-100 bg-amber-50/50 flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4">
                          <div>
                            <h2 className="text-lg font-bold text-amber-900 flex items-center gap-2">
                              <span className="relative flex h-3 w-3">
                                <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-amber-400 opacity-75"></span>
                                <span className="relative inline-flex rounded-full h-3 w-3 bg-amber-500"></span>
                              </span>
                              Solicitudes Pendientes
                            </h2>
                            <p className="text-sm text-amber-700">
                              Usuarios esperando aprobación para acceder al
                              sistema.
                            </p>
                          </div>
                        </div>

                        {/* Desktop Table - Pending */}
                        <div className="hidden md:block overflow-x-auto">
                          <table className="w-full text-sm text-left">
                            <thead className="text-xs text-amber-700 uppercase bg-amber-100/50 border-b border-amber-200">
                              <tr>
                                <th className="px-6 py-4 font-semibold">
                                  Usuario
                                </th>
                                <th className="px-6 py-4 font-semibold">Rol</th>
                                <th className="px-6 py-4 font-semibold text-right">
                                  Acciones
                                </th>
                              </tr>
                            </thead>
                            <tbody className="divide-y divide-amber-100/50">
                              {paginatedUsers
                                .filter((u) => u.status === "pending")
                                .map((user) => (
                                  <tr
                                    key={user.email}
                                    className="bg-white/50 hover:bg-amber-100/30 transition-colors"
                                  >
                                    <td className="px-6 py-4">
                                      <div className="flex items-center gap-3">
                                        <div
                                          className={`w-10 h-10 rounded-full flex items-center justify-center text-sm font-bold shadow-sm ring-2 ring-white ${getAvatarColor(user.email)}`}
                                        >
                                          {(user.fullName || user.email)
                                            .split(" ")
                                            .map((n) => n[0])
                                            .join("")
                                            .substring(0, 2)
                                            .toUpperCase()}
                                        </div>
                                        <div>
                                          <p className="font-semibold text-gray-900">
                                            {user.fullName || user.email}
                                          </p>
                                          <p className="text-xs text-gray-500">
                                            {user.email}
                                          </p>
                                        </div>
                                      </div>
                                    </td>
                                    <td className="px-6 py-4">
                                      <span
                                        className={`inline-flex items-center px-2.5 py-1 rounded-full text-xs font-medium border ${
                                          user.role === "Admin"
                                            ? "bg-purple-50 text-purple-700 border-purple-200"
                                            : user.role === "Profesor"
                                              ? "bg-blue-50 text-blue-700 border-blue-200"
                                              : "bg-green-50 text-green-700 border-green-200"
                                        }`}
                                      >
                                        {user.role}
                                      </span>
                                    </td>
                                    <td className="px-6 py-4 text-right">
                                      <div className="flex items-center justify-end gap-2">
                                        <button
                                          onClick={() =>
                                            handleStatusUpdate(
                                              user.id,
                                              "active",
                                            )
                                          }
                                          className="px-4 py-2 text-xs font-bold text-white bg-emerald-600 hover:bg-emerald-700 rounded-lg shadow-sm shadow-emerald-500/20 transition-all active:scale-95"
                                        >
                                          Aprobar Acceso
                                        </button>
                                      </div>
                                    </td>
                                  </tr>
                                ))}
                            </tbody>
                          </table>
                        </div>

                        {/* Mobile Cards - Pending */}
                        <div className="md:hidden divide-y divide-amber-100">
                          {paginatedUsers
                            .filter((u) => u.status === "pending")
                            .map((user) => (
                              <div
                                key={user.id}
                                className="p-4 bg-white/50 hover:bg-amber-50 transition-colors"
                              >
                                <div className="flex items-start justify-between gap-3">
                                  <div className="flex items-center gap-3 flex-1 min-w-0">
                                    <div
                                      className={`w-10 h-10 rounded-full flex items-center justify-center text-sm font-bold shadow-sm flex-shrink-0 ${getAvatarColor(user.email)}`}
                                    >
                                      {(user.fullName || user.email)
                                        .split(" ")
                                        .map((n) => n[0])
                                        .join("")
                                        .substring(0, 2)
                                        .toUpperCase()}
                                    </div>
                                    <div className="min-w-0">
                                      <p className="font-semibold text-gray-900 truncate">
                                        {user.fullName || user.email}
                                      </p>
                                      <p className="text-xs text-gray-500 truncate">
                                        {user.email}
                                      </p>
                                    </div>
                                  </div>
                                </div>
                                <div className="mt-3 flex items-center justify-between gap-2">
                                  <span
                                    className={`inline-flex items-center px-2 py-0.5 rounded-full text-xs font-medium border ${
                                      user.role === "Admin"
                                        ? "bg-purple-50 text-purple-700 border-purple-200"
                                        : user.role === "Profesor"
                                          ? "bg-blue-50 text-blue-700 border-blue-200"
                                          : "bg-green-50 text-green-700 border-green-200"
                                    }`}
                                  >
                                    {user.role}
                                  </span>
                                  <button
                                    onClick={() =>
                                      handleStatusUpdate(user.id, "active")
                                    }
                                    className="px-3 py-1.5 text-xs font-bold text-white bg-emerald-600 hover:bg-emerald-700 rounded-lg shadow-sm transition-all active:scale-95"
                                  >
                                    Aprobar
                                  </button>
                                </div>
                              </div>
                            ))}
                        </div>
                      </div>
                    )}

                    {/* Active Users Section */}
                    <div className="bg-white rounded-2xl shadow-sm border border-gray-100 overflow-hidden">
                      <div className="p-4 sm:p-6 border-b border-gray-50 flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4 bg-gray-50/30">
                        <div>
                          <h2 className="text-lg font-bold text-gray-900">
                            Gestión de Usuarios
                          </h2>
                          <p className="text-sm text-gray-500">
                            Administra los usuarios del sistema.
                          </p>
                        </div>
                        <button
                          onClick={handleAddUser}
                          className="px-4 py-2 bg-blue-600 text-white text-sm font-medium rounded-xl hover:bg-blue-700 transition-all shadow-md shadow-blue-500/20 flex items-center gap-2 active:scale-95 w-full sm:w-auto justify-center"
                        >
                          <UserCog className="w-4 h-4" />
                          Nuevo Usuario
                        </button>
                      </div>

                      {/* Desktop Table */}
                      <div className="hidden md:block overflow-x-auto">
                        <table className="w-full text-sm text-left">
                          <thead className="text-xs text-gray-500 uppercase bg-gray-50/50 border-b border-gray-100">
                            <tr>
                              <th className="px-6 py-4 font-semibold">
                                Usuario
                              </th>
                              <th className="px-6 py-4 font-semibold">Rol</th>
                              <th className="px-6 py-4 font-semibold">
                                Estado
                              </th>
                              <th className="px-6 py-4 font-semibold text-right">
                                Acciones
                              </th>
                            </tr>
                          </thead>
                          <tbody className="divide-y divide-gray-100">
                            {paginatedUsers.map((user) => (
                              <tr
                                key={user.email}
                                className="bg-white hover:bg-gray-50/80 transition-colors"
                              >
                                <td className="px-6 py-4">
                                  <div className="flex items-center gap-3">
                                    <div
                                      className={`w-10 h-10 rounded-full flex items-center justify-center text-sm font-bold shadow-sm ring-2 ring-white ${getAvatarColor(user.email)}`}
                                    >
                                      {(user.fullName || user.email)
                                        .split(" ")
                                        .map((n) => n[0])
                                        .join("")
                                        .substring(0, 2)
                                        .toUpperCase()}
                                    </div>
                                    <div>
                                      <p className="font-semibold text-gray-900">
                                        {user.fullName || user.email}
                                      </p>
                                      <p className="text-xs text-gray-500">
                                        {user.email}
                                      </p>
                                    </div>
                                  </div>
                                </td>
                                <td className="px-6 py-4">
                                  <span
                                    className={`inline-flex items-center px-2.5 py-1 rounded-full text-xs font-medium border ${
                                      user.role === "Admin"
                                        ? "bg-purple-50 text-purple-700 border-purple-200"
                                        : user.role === "Profesor"
                                          ? "bg-blue-50 text-blue-700 border-blue-200"
                                          : "bg-green-50 text-green-700 border-green-200"
                                    }`}
                                  >
                                    {user.role}
                                  </span>
                                </td>
                                <td className="px-6 py-4">
                                  <span
                                    className={`inline-flex items-center px-2.5 py-1 rounded-full text-xs font-medium border ${
                                      user.status === "active"
                                        ? "bg-emerald-50 text-emerald-700 border-emerald-200"
                                        : "bg-amber-50 text-amber-700 border-amber-200"
                                    }`}
                                  >
                                    {user.status === "active"
                                      ? "Activo"
                                      : "Pendiente"}
                                  </span>
                                </td>
                                <td className="px-6 py-4 text-right">
                                  <div className="flex items-center justify-end gap-2">
                                    {user.status === "pending" && (
                                      <button
                                        onClick={() =>
                                          handleStatusUpdate(user.id, "active")
                                        }
                                        className="px-3 py-1.5 text-xs font-medium text-emerald-700 bg-emerald-50 hover:bg-emerald-100 border border-emerald-200 rounded-lg transition-colors"
                                      >
                                        Aprobar
                                      </button>
                                    )}
                                    {user.role !== "Admin" && user.email !== email && (
                                      <button
                                        onClick={() => openDeleteModal(user)}
                                        className="p-2 text-red-600 hover:bg-red-50 rounded-lg transition-colors"
                                        title="Eliminar"
                                      >
                                        <Trash2 className="w-4 h-4" />
                                      </button>
                                    )}
                                    <button
                                      onClick={() => handleEditUser(user)}
                                      className="p-2 text-blue-600 hover:bg-blue-50 rounded-lg transition-colors"
                                      title="Editar"
                                    >
                                      <Edit className="w-4 h-4" />
                                    </button>
                                  </div>
                                </td>
                              </tr>
                            ))}
                          </tbody>
                        </table>
                      </div>

                      {/* Mobile Cards */}
                      <div className="md:hidden divide-y divide-gray-100">
                        {paginatedUsers.map((user) => (
                          <div
                            key={user.id}
                            className="p-4 hover:bg-gray-50/50"
                          >
                            <div className="flex items-start justify-between gap-3">
                              <div className="flex items-center gap-3 flex-1 min-w-0">
                                <div
                                  className={`w-10 h-10 rounded-full flex items-center justify-center text-sm font-bold shadow-sm flex-shrink-0 ${getAvatarColor(user.email)}`}
                                >
                                  {(user.fullName || user.email)
                                    .split(" ")
                                    .map((n) => n[0])
                                    .join("")
                                    .substring(0, 2)
                                    .toUpperCase()}
                                </div>
                                <div className="min-w-0">
                                  <p className="font-semibold text-gray-900 truncate">
                                    {user.fullName || user.email}
                                  </p>
                                  <p className="text-xs text-gray-500 truncate">
                                    {user.email}
                                  </p>
                                </div>
                              </div>
                              <div className="flex items-center gap-1 flex-shrink-0">
                                <button
                                  onClick={() => handleEditUser(user)}
                                  className="p-2 text-blue-600 hover:bg-blue-50 rounded-lg transition-colors"
                                >
                                  <Edit className="w-4 h-4" />
                                </button>
                                <button
                                  onClick={() => openDeleteModal(user)}
                                  className="p-2 text-red-500 hover:bg-red-50 rounded-lg transition-colors"
                                >
                                  <Trash2 className="w-4 h-4" />
                                </button>
                              </div>
                            </div>
                            <div className="mt-3 flex flex-wrap gap-2">
                              <span
                                className={`inline-flex items-center px-2 py-0.5 rounded-full text-xs font-medium border ${
                                  user.role === "Admin"
                                    ? "bg-purple-50 text-purple-700 border-purple-200"
                                    : user.role === "Profesor"
                                      ? "bg-blue-50 text-blue-700 border-blue-200"
                                      : "bg-green-50 text-green-700 border-green-200"
                                }`}
                              >
                                {user.role}
                              </span>
                              <span className="inline-flex items-center px-2 py-0.5 rounded-full text-xs font-medium bg-indigo-50 text-indigo-700 border border-indigo-200">
                                {user.semester || "N/A"}
                              </span>
                              {user.phone && (
                                <span className="text-xs text-gray-500 flex items-center gap-1">
                                  <Phone className="w-3 h-3" /> {user.phone}
                                </span>
                              )}
                            </div>
                          </div>
                        ))}
                      </div>

                      {/* Pagination */}
                      {users.length > 0 && (
                        <div className="p-4 border-t border-gray-100 flex items-center justify-between bg-gray-50/30">
                          <p className="text-sm text-gray-500">
                            Mostrando {
                              users.length === 0
                                ? 0
                                : (currentPage - 1) * usersPerPage + 1
                            }
                            -
                            {Math.min(currentPage * usersPerPage, users.length)}{" "}
                            de {users.length}
                          </p>
                          <div className="flex items-center gap-2">
                            <button
                              onClick={() =>
                                setCurrentPage((p) => Math.max(1, p - 1))
                              }
                              disabled={currentPage === 1}
                              className="p-2 text-gray-500 hover:bg-gray-100 rounded-lg transition-colors disabled:opacity-40 disabled:cursor-not-allowed"
                            >
                              <ChevronLeft className="w-4 h-4" />
                            </button>
                            <span className="text-sm font-medium text-gray-700">
                              {currentPage} / {totalPages}
                            </span>
                            <button
                              onClick={() =>
                                setCurrentPage((p) =>
                                  Math.min(totalPages, p + 1),
                                )
                              }
                              disabled={currentPage === totalPages}
                              className="p-2 text-gray-500 hover:bg-gray-100 rounded-lg transition-colors disabled:opacity-40 disabled:cursor-not-allowed"
                            >
                              <ChevronRight className="w-4 h-4" />
                            </button>
                          </div>
                        </div>
                      )}
                    </div>
                  </div>
                )}
              </div>
            </div>
          </div>
        </main>
      </PageTransition>
    </>
  );
}
