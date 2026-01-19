"use client";

import React, { useState, useEffect } from "react";
import DashboardHeader from "@/components/layout/DashboardHeader";
import PageTransition from "@/components/ui/PageTransition";
import { getUserRole, getUserEmail } from "@/features/auth/clientAuth";
import {
    User,
    Lock,
    Bell,
    Save,
    Camera,
    Shield,
    Trash2,
    Edit,
    Mail,
    UserCog,
    Phone
} from "lucide-react";
import Image from "next/image";
import UserModal, { UserData } from "@/components/ui/UserModal";
import Toast, { ToastType } from "@/components/ui/Toast";
import DeleteModal from "@/components/ui/DeleteModal";
import { ChevronLeft, ChevronRight } from "lucide-react";

// Mock Users for Admin Section
const MOCK_USERS: UserData[] = [
    { id: 1, fullName: "Ana García", email: "ana.garcia@example.com", semester: "8vo", phone: "0412-1234567", role: "Estudiante" },
    { id: 2, fullName: "Carlos Mendoza", email: "carlos.mendoza@example.com", semester: "N/A", phone: "0414-7654321", role: "Profesor" },
    { id: 3, fullName: "Luis Rodríguez", email: "admin@tesisfar.com", semester: "N/A", phone: "0416-9876543", role: "Admin" },
    { id: 4, fullName: "María López", email: "maria.lopez@example.com", semester: "10mo", phone: "0424-5556789", role: "Estudiante" },
];

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
    const [activeTab, setActiveTab] = useState<"profile" | "security" | "notifications" | "users">("profile");

    // Profile State
    const [avatarPreview, setAvatarPreview] = useState<string | null>(null);

    // Users State (Admin)
    const [users, setUsers] = useState<UserData[]>(MOCK_USERS);
    const [isUserModalOpen, setIsUserModalOpen] = useState(false);
    const [editingUser, setEditingUser] = useState<UserData | null>(null);

    // Delete Modal State
    const [isDeleteModalOpen, setIsDeleteModalOpen] = useState(false);
    const [userToDelete, setUserToDelete] = useState<UserData | null>(null);

    // Pagination State
    const [currentPage, setCurrentPage] = useState(1);
    const usersPerPage = 5;
    const totalPages = Math.ceil(users.length / usersPerPage);
    const paginatedUsers = users.slice((currentPage - 1) * usersPerPage, currentPage * usersPerPage);

    // Toast State
    const [toast, setToast] = useState<{ message: string; type: ToastType; isVisible: boolean }>({
        message: "",
        type: "info",
        isVisible: false,
    });

    const showToast = (message: string, type: ToastType = "info") => {
        setToast({ message, type, isVisible: true });
    };

    useEffect(() => {
        setRole(getUserRole());
        setEmail(getUserEmail());
    }, []);

    const openDeleteModal = (user: UserData) => {
        setUserToDelete(user);
        setIsDeleteModalOpen(true);
    };

    const confirmDeleteUser = () => {
        if (userToDelete) {
            setUsers(users.filter(u => u.id !== userToDelete.id));
            showToast("Usuario eliminado correctamente.", "success");
            setUserToDelete(null);
            // Reset to page 1 if current page becomes empty
            if (paginatedUsers.length === 1 && currentPage > 1) {
                setCurrentPage(currentPage - 1);
            }
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

    const handleSaveUser = (userData: Omit<UserData, "id"> & { id?: number }) => {
        if (userData.id) {
            // Edit existing
            setUsers(users.map(u => u.id === userData.id ? { ...userData, id: userData.id! } : u));
            showToast("Usuario actualizado correctamente.", "success");
        } else {
            // Add new
            const newUser = {
                ...userData,
                id: Math.max(0, ...users.map(u => u.id)) + 1
            };
            setUsers([...users, newUser]);
            showToast("Usuario creado correctamente.", "success");
        }
        setIsUserModalOpen(false);
    };

    const handleSaveProfile = () => {
        // Mock save
        showToast("Perfil actualizado correctamente.", "success");
    };

    // Deterministic avatar color helper
    const getAvatarColor = (email: string) => {
        const colors = ["bg-blue-100 text-blue-600", "bg-purple-100 text-purple-600", "bg-emerald-100 text-emerald-600", "bg-amber-100 text-amber-600"];
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
                onClose={() => setToast(prev => ({ ...prev, isVisible: false }))}
            />

            <PageTransition>
                <main className="flex-1 p-4 md:p-6 lg:p-8 overflow-y-auto bg-gray-50/50">
                    <div className="max-w-7xl mx-auto">

                        {/* Page Header */}
                        <div className="mb-6">
                            <h1 className="text-2xl font-bold text-gray-900 tracking-tight">Configuración</h1>
                            <p className="text-gray-500 text-sm mt-1">Administra tu perfil y preferencias del sistema.</p>
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
                                            { id: "notifications", label: "Notificaciones", icon: Bell },
                                            ...(role === "Admin" ? [{ id: "users", label: "Usuarios", icon: UserCog }] : [])
                                        ].map((item) => (
                                            <button
                                                key={item.id}
                                                onClick={() => setActiveTab(item.id as any)}
                                                className={`flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm font-medium transition-all duration-200 whitespace-nowrap w-full text-left ${activeTab === item.id
                                                    ? "bg-blue-50 text-blue-700"
                                                    : "text-gray-600 hover:bg-gray-50 hover:text-gray-900"
                                                    }`}
                                            >
                                                <item.icon className={`w-4 h-4 ${activeTab === item.id ? "text-blue-600" : "text-gray-400"}`} />
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
                                        <div className="p-6 border-b border-gray-50 bg-gray-50/30">
                                            <h2 className="text-lg font-bold text-gray-900">Información Personal</h2>
                                            <p className="text-sm text-gray-500">Actualiza tu foto y detalles personales.</p>
                                        </div>
                                        <div className="p-6 space-y-8">
                                            {/* Avatar */}
                                            <div className="flex items-center gap-6">
                                                <div className="relative group cursor-pointer">
                                                    <div className={`w-24 h-24 rounded-full flex items-center justify-center text-2xl font-bold text-white overflow-hidden bg-gray-100 border-4 border-white shadow-lg transition-transform group-hover:scale-105`}>
                                                        {avatarPreview ? (
                                                            <Image src={avatarPreview} alt="Avatar" width={96} height={96} className="w-full h-full object-cover" />
                                                        ) : email ? (
                                                            <div className={`w-full h-full flex items-center justify-center ${getAvatarColor(email)}`}>
                                                                {email[0].toUpperCase()}
                                                            </div>
                                                        ) : (
                                                            <User className="w-10 h-10 text-gray-400" />
                                                        )}
                                                    </div>
                                                    <button className="absolute bottom-0 right-0 p-2 bg-blue-600 text-white rounded-full shadow-md hover:bg-blue-700 transition-colors ring-2 ring-white">
                                                        <Camera className="w-4 h-4" />
                                                    </button>
                                                </div>
                                                <div>
                                                    <p className="text-base font-semibold text-gray-900">Tu foto de perfil</p>
                                                    <p className="text-sm text-gray-500">Haz clic en la cámara para subir una nueva imagen.</p>
                                                </div>
                                            </div>

                                            <div className="grid gap-6 md:grid-cols-2">
                                                <div className="space-y-2">
                                                    <label className="text-sm font-medium text-gray-700">Email</label>
                                                    <div className="relative group">
                                                        <Mail className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400 group-focus-within:text-blue-500 transition-colors" />
                                                        <input
                                                            type="email"
                                                            value={email || ""}
                                                            disabled
                                                            className="w-full pl-10 pr-4 py-2.5 border border-gray-200 rounded-xl bg-gray-50 text-gray-500 sm:text-sm transition-all focus:bg-white focus:ring-2 focus:ring-blue-500/20 focus:border-blue-500"
                                                        />
                                                    </div>
                                                </div>
                                                <div className="space-y-2">
                                                    <label className="text-sm font-medium text-gray-700">Rol del Sistema</label>
                                                    <div className="relative group">
                                                        <Shield className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400 group-focus-within:text-blue-500 transition-colors" />
                                                        <input
                                                            type="text"
                                                            value={role || ""}
                                                            disabled
                                                            className="w-full pl-10 pr-4 py-2.5 border border-gray-200 rounded-xl bg-gray-50 text-gray-500 sm:text-sm transition-all focus:bg-white focus:ring-2 focus:ring-blue-500/20 focus:border-blue-500"
                                                        />
                                                    </div>
                                                </div>
                                            </div>

                                            <div className="flex justify-end pt-6 border-t border-gray-100">
                                                <button
                                                    onClick={handleSaveProfile}
                                                    className="px-5 py-2.5 bg-blue-600 text-white text-sm font-medium rounded-xl hover:bg-blue-700 active:transform active:scale-95 transition-all shadow-sm shadow-blue-500/30 flex items-center gap-2"
                                                >
                                                    <Save className="w-4 h-4" />
                                                    Guardar Cambios
                                                </button>
                                            </div>
                                        </div>
                                    </div>
                                )}

                                {/* Security Section */}
                                {activeTab === "security" && (
                                    <div className="bg-white rounded-2xl shadow-sm border border-gray-100 overflow-hidden">
                                        <div className="p-6 border-b border-gray-50 bg-gray-50/30">
                                            <h2 className="text-lg font-bold text-gray-900">Seguridad</h2>
                                            <p className="text-sm text-gray-500">Gestiona tu contraseña y seguridad de la cuenta.</p>
                                        </div>
                                        <div className="p-6 space-y-5">
                                            <div className="space-y-2">
                                                <label className="text-sm font-medium text-gray-700">Contraseña Actual</label>
                                                <input type="password" placeholder="••••••••" className="w-full px-4 py-2.5 border border-gray-200 rounded-xl focus:ring-2 focus:ring-blue-500/20 focus:border-blue-500 outline-none transition-all" />
                                            </div>
                                            <div className="grid gap-5 md:grid-cols-2">
                                                <div className="space-y-2">
                                                    <label className="text-sm font-medium text-gray-700">Nueva Contraseña</label>
                                                    <input type="password" placeholder="••••••••" className="w-full px-4 py-2.5 border border-gray-200 rounded-xl focus:ring-2 focus:ring-blue-500/20 focus:border-blue-500 outline-none transition-all" />
                                                </div>
                                                <div className="space-y-2">
                                                    <label className="text-sm font-medium text-gray-700">Confirmar Contraseña</label>
                                                    <input type="password" placeholder="••••••••" className="w-full px-4 py-2.5 border border-gray-200 rounded-xl focus:ring-2 focus:ring-blue-500/20 focus:border-blue-500 outline-none transition-all" />
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
                                            <h2 className="text-lg font-bold text-gray-900">Preferencias de Notificación</h2>
                                            <p className="text-sm text-gray-500">Elige qué actualizaciones quieres recibir.</p>
                                        </div>
                                        <div className="p-6 space-y-6">
                                            <div className="flex items-center justify-between py-2">
                                                <div className="space-y-0.5">
                                                    <p className="text-base font-medium text-gray-900">Notificaciones por Email</p>
                                                    <p className="text-sm text-gray-500">Recibe actualizaciones sobre entregas y revisiones.</p>
                                                </div>
                                                <label className="relative inline-flex items-center cursor-pointer">
                                                    <input type="checkbox" className="sr-only peer" defaultChecked />
                                                    <div className="w-11 h-6 bg-gray-200 peer-focus:outline-none peer-focus:ring-4 peer-focus:ring-blue-300/30 rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-blue-600"></div>
                                                </label>
                                            </div>
                                            <div className="flex items-center justify-between py-2 border-t border-gray-100 pt-6">
                                                <div className="space-y-0.5">
                                                    <p className="text-base font-medium text-gray-900">Notificaciones Push</p>
                                                    <p className="text-sm text-gray-500">Notificaciones instantáneas en el navegador.</p>
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
                                    <div className="bg-white rounded-2xl shadow-sm border border-gray-100 overflow-hidden">
                                        <div className="p-4 sm:p-6 border-b border-gray-50 flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4 bg-gray-50/30">
                                            <div>
                                                <h2 className="text-lg font-bold text-gray-900">Gestión de Usuarios</h2>
                                                <p className="text-sm text-gray-500">Administra los usuarios del sistema.</p>
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
                                                        <th className="px-6 py-4 font-semibold">Usuario</th>
                                                        <th className="px-6 py-4 font-semibold">Teléfono</th>
                                                        <th className="px-6 py-4 font-semibold">Semestre</th>
                                                        <th className="px-6 py-4 font-semibold">Rol</th>
                                                        <th className="px-6 py-4 font-semibold text-right">Acciones</th>
                                                    </tr>
                                                </thead>
                                                <tbody className="divide-y divide-gray-100">
                                                    {paginatedUsers.map((user) => (
                                                        <tr key={user.id} className="bg-white hover:bg-gray-50/80 transition-colors">
                                                            <td className="px-6 py-4">
                                                                <div className="flex items-center gap-3">
                                                                    <div className={`w-10 h-10 rounded-full flex items-center justify-center text-sm font-bold shadow-sm ring-2 ring-white ${getAvatarColor(user.email)}`}>
                                                                        {(user.fullName || user.email).split(' ').map(n => n[0]).join('').substring(0, 2).toUpperCase()}
                                                                    </div>
                                                                    <div>
                                                                        <p className="font-semibold text-gray-900">{user.fullName || user.email}</p>
                                                                        <p className="text-xs text-gray-500">{user.email}</p>
                                                                    </div>
                                                                </div>
                                                            </td>
                                                            <td className="px-6 py-4">
                                                                <div className="flex items-center gap-2 text-gray-600">
                                                                    <Phone className="w-4 h-4 text-gray-400" />
                                                                    {user.phone || "—"}
                                                                </div>
                                                            </td>
                                                            <td className="px-6 py-4">
                                                                <span className="inline-flex items-center px-2.5 py-1 rounded-full text-xs font-medium bg-indigo-50 text-indigo-700 border border-indigo-200">
                                                                    {user.semester || "N/A"}
                                                                </span>
                                                            </td>
                                                            <td className="px-6 py-4">
                                                                <span className={`inline-flex items-center px-2.5 py-1 rounded-full text-xs font-medium border ${user.role === "Admin" ? "bg-purple-50 text-purple-700 border-purple-200" :
                                                                    user.role === "Profesor" ? "bg-blue-50 text-blue-700 border-blue-200" :
                                                                        "bg-green-50 text-green-700 border-green-200"
                                                                    }`}>
                                                                    {user.role}
                                                                </span>
                                                            </td>
                                                            <td className="px-6 py-4 text-right">
                                                                <div className="flex items-center justify-end gap-1">
                                                                    <button
                                                                        onClick={() => handleEditUser(user)}
                                                                        className="p-2 text-blue-600 hover:bg-blue-50 rounded-lg transition-colors"
                                                                        title="Editar"
                                                                    >
                                                                        <Edit className="w-4 h-4" />
                                                                    </button>
                                                                    <button
                                                                        onClick={() => openDeleteModal(user)}
                                                                        className="p-2 text-red-500 hover:bg-red-50 rounded-lg transition-colors"
                                                                        title="Eliminar"
                                                                    >
                                                                        <Trash2 className="w-4 h-4" />
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
                                                <div key={user.id} className="p-4 hover:bg-gray-50/50">
                                                    <div className="flex items-start justify-between gap-3">
                                                        <div className="flex items-center gap-3 flex-1 min-w-0">
                                                            <div className={`w-10 h-10 rounded-full flex items-center justify-center text-sm font-bold shadow-sm flex-shrink-0 ${getAvatarColor(user.email)}`}>
                                                                {(user.fullName || user.email).split(' ').map(n => n[0]).join('').substring(0, 2).toUpperCase()}
                                                            </div>
                                                            <div className="min-w-0">
                                                                <p className="font-semibold text-gray-900 truncate">{user.fullName || user.email}</p>
                                                                <p className="text-xs text-gray-500 truncate">{user.email}</p>
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
                                                        <span className={`inline-flex items-center px-2 py-0.5 rounded-full text-xs font-medium border ${user.role === "Admin" ? "bg-purple-50 text-purple-700 border-purple-200" :
                                                            user.role === "Profesor" ? "bg-blue-50 text-blue-700 border-blue-200" :
                                                                "bg-green-50 text-green-700 border-green-200"
                                                            }`}>
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
                                        {totalPages > 1 && (
                                            <div className="p-4 border-t border-gray-100 flex items-center justify-between bg-gray-50/30">
                                                <p className="text-sm text-gray-500">
                                                    Mostrando {((currentPage - 1) * usersPerPage) + 1}-{Math.min(currentPage * usersPerPage, users.length)} de {users.length}
                                                </p>
                                                <div className="flex items-center gap-2">
                                                    <button
                                                        onClick={() => setCurrentPage(p => Math.max(1, p - 1))}
                                                        disabled={currentPage === 1}
                                                        className="p-2 text-gray-500 hover:bg-gray-100 rounded-lg transition-colors disabled:opacity-40 disabled:cursor-not-allowed"
                                                    >
                                                        <ChevronLeft className="w-4 h-4" />
                                                    </button>
                                                    <span className="text-sm font-medium text-gray-700">
                                                        {currentPage} / {totalPages}
                                                    </span>
                                                    <button
                                                        onClick={() => setCurrentPage(p => Math.min(totalPages, p + 1))}
                                                        disabled={currentPage === totalPages}
                                                        className="p-2 text-gray-500 hover:bg-gray-100 rounded-lg transition-colors disabled:opacity-40 disabled:cursor-not-allowed"
                                                    >
                                                        <ChevronRight className="w-4 h-4" />
                                                    </button>
                                                </div>
                                            </div>
                                        )}
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
