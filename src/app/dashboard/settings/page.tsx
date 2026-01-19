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
    UserCog
} from "lucide-react";
import Image from "next/image";
import UserModal, { UserData } from "@/components/ui/UserModal";
import Toast, { ToastType } from "@/components/ui/Toast";

// Mock Users for Admin Section
const MOCK_USERS = [
    { id: 1, email: "estudiante@example.com", role: "Estudiante", status: "Active" },
    { id: 2, email: "profesor@example.com", role: "Profesor", status: "Active" },
    { id: 3, email: "admin@tesisfar.com", role: "Admin", status: "Active" },
    { id: 4, email: "nuevo@example.com", role: "Estudiante", status: "Pending" },
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

    const handleDeleteUser = (id: number) => {
        if (confirm("¿Estás seguro de eliminar este usuario?")) {
            setUsers(users.filter(u => u.id !== id));
            showToast("Usuario eliminado correctamente.", "success");
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

            <Toast
                message={toast.message}
                type={toast.type}
                isVisible={toast.isVisible}
                onClose={() => setToast(prev => ({ ...prev, isVisible: false }))}
            />

            <PageTransition>
                <main className="flex-1 p-4 md:p-6 overflow-y-auto bg-gray-50/50">
                    <div className="max-w-6xl mx-auto">
                        <div className="mb-8">
                            <h1 className="text-3xl font-bold text-gray-900 tracking-tight">Ajustes de Cuenta</h1>
                            <p className="text-gray-500 mt-1">Administra tu perfil y preferencias del sistema.</p>
                        </div>

                        <div className="flex flex-col lg:flex-row gap-8">
                            {/* Settings Sidebar */}
                            <aside className="w-full lg:w-64 flex-shrink-0">
                                <nav className="flex lg:flex-col gap-2 overflow-x-auto lg:overflow-visible pb-2 lg:pb-0">
                                    {[
                                        { id: "profile", label: "Perfil", icon: User },
                                        { id: "security", label: "Seguridad", icon: Lock },
                                        { id: "notifications", label: "Notificaciones", icon: Bell },
                                        ...(role === "Admin" ? [{ id: "users", label: "Gestión de Usuarios", icon: UserCog }] : [])
                                    ].map((item) => (
                                        <button
                                            key={item.id}
                                            onClick={() => setActiveTab(item.id as any)}
                                            className={`flex items-center gap-3 px-4 py-3 rounded-xl text-sm font-medium transition-all duration-200 whitespace-nowrap ${activeTab === item.id
                                                ? "bg-white text-blue-600 shadow-sm ring-1 ring-gray-200 translate-x-1"
                                                : "text-gray-600 hover:bg-gray-100/50 hover:text-gray-900"
                                                }`}
                                        >
                                            <item.icon className={`w-4 h-4 ${activeTab === item.id ? "text-blue-500" : "text-gray-400"}`} />
                                            {item.label}
                                        </button>
                                    ))}
                                </nav>
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
                                        <div className="p-6 border-b border-gray-50 flex justify-between items-center bg-gray-50/30">
                                            <div>
                                                <h2 className="text-lg font-bold text-gray-900">Gestión de Usuarios</h2>
                                                <p className="text-sm text-gray-500">Administra los usuarios del sistema.</p>
                                            </div>
                                            <button
                                                onClick={handleAddUser}
                                                className="px-4 py-2 bg-blue-600 text-white text-sm font-medium rounded-xl hover:bg-blue-700 transition-all shadow-md shadow-blue-500/20 flex items-center gap-2 active:scale-95"
                                            >
                                                <UserCog className="w-4 h-4" />
                                                Nuevo Usuario
                                            </button>
                                        </div>
                                        <div className="overflow-x-auto">
                                            <table className="w-full text-sm text-left">
                                                <thead className="text-xs text-gray-500 uppercase bg-gray-50/50 border-b border-gray-100">
                                                    <tr>
                                                        <th className="px-6 py-4 font-semibold">Usuario</th>
                                                        <th className="px-6 py-4 font-semibold">Rol</th>
                                                        <th className="px-6 py-4 font-semibold">Estado</th>
                                                        <th className="px-6 py-4 font-semibold text-right">Acciones</th>
                                                    </tr>
                                                </thead>
                                                <tbody className="divide-y divide-gray-100">
                                                    {users.map((user) => (
                                                        <tr key={user.id} className="bg-white hover:bg-gray-50/80 transition-colors group">
                                                            <td className="px-6 py-4 font-medium text-gray-900 flex items-center gap-4">
                                                                <div className={`w-9 h-9 rounded-full flex items-center justify-center text-xs font-bold text-white shadow-sm ring-2 ring-white ${getAvatarColor(user.email)}`}>
                                                                    {user.email[0].toUpperCase()}
                                                                </div>
                                                                {user.email}
                                                            </td>
                                                            <td className="px-6 py-4">
                                                                <span className={`inline-flex items-center px-2.5 py-1 rounded-full text-xs font-medium border ${user.role === "Admin" ? "bg-purple-50 text-purple-700 border-purple-200" :
                                                                    user.role === "Profesor" ? "bg-blue-50 text-blue-700 border-blue-200" :
                                                                        "bg-green-50 text-green-700 border-green-200"
                                                                    }`}>
                                                                    {user.role}
                                                                </span>
                                                            </td>
                                                            <td className="px-6 py-4">
                                                                <span className={`inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-medium border ${user.status === "Active" ? "bg-emerald-50 text-emerald-700 border-emerald-200" : "bg-amber-50 text-amber-700 border-amber-200"
                                                                    }`}>
                                                                    <span className={`w-1.5 h-1.5 rounded-full ${user.status === "Active" ? "bg-emerald-500" : "bg-amber-500"}`}></span>
                                                                    {user.status === "Active" ? "Activo" : "Pendiente"}
                                                                </span>
                                                            </td>
                                                            <td className="px-6 py-4 text-right">
                                                                <div className="flex items-center justify-end gap-2 opacity-0 group-hover:opacity-100 transition-opacity">
                                                                    <button
                                                                        onClick={() => handleEditUser(user)}
                                                                        className="p-2 text-gray-400 hover:text-blue-600 hover:bg-blue-50 rounded-lg transition-colors"
                                                                        title="Editar"
                                                                    >
                                                                        <Edit className="w-4 h-4" />
                                                                    </button>
                                                                    <button
                                                                        onClick={() => handleDeleteUser(user.id)}
                                                                        className="p-2 text-gray-400 hover:text-red-600 hover:bg-red-50 rounded-lg transition-colors"
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
