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

    useEffect(() => {
        setRole(getUserRole());
        setEmail(getUserEmail());
    }, []);

    const handleDeleteUser = (id: number) => {
        if (confirm("¿Estás seguro de eliminar este usuario?")) {
            setUsers(users.filter(u => u.id !== id));
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
        } else {
            // Add new
            const newUser = {
                ...userData,
                id: Math.max(0, ...users.map(u => u.id)) + 1
            };
            setUsers([...users, newUser]);
        }
        setIsUserModalOpen(false);
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

            <PageTransition>
                <main className="flex-1 p-4 md:p-6 overflow-y-auto bg-gray-50/50">
                    <div className="max-w-6xl mx-auto">
                        <h1 className="text-2xl font-bold text-gray-900 mb-6">Ajustes de Cuenta</h1>

                        <div className="flex flex-col lg:flex-row gap-6">
                            {/* Settings Sidebar */}
                            <aside className="w-full lg:w-64 flex-shrink-0">
                                <nav className="flex lg:flex-col gap-2 overflow-x-auto lg:overflow-visible pb-2 lg:pb-0">
                                    <button
                                        onClick={() => setActiveTab("profile")}
                                        className={`flex items-center gap-3 px-4 py-3 rounded-lg text-sm font-medium transition-colors whitespace-nowrap ${activeTab === "profile"
                                            ? "bg-white text-blue-600 shadow-sm ring-1 ring-gray-200"
                                            : "text-gray-600 hover:bg-gray-100/50 hover:text-gray-900"
                                            }`}
                                    >
                                        <User className="w-4 h-4" />
                                        Perfil
                                    </button>
                                    <button
                                        onClick={() => setActiveTab("security")}
                                        className={`flex items-center gap-3 px-4 py-3 rounded-lg text-sm font-medium transition-colors whitespace-nowrap ${activeTab === "security"
                                            ? "bg-white text-blue-600 shadow-sm ring-1 ring-gray-200"
                                            : "text-gray-600 hover:bg-gray-100/50 hover:text-gray-900"
                                            }`}
                                    >
                                        <Lock className="w-4 h-4" />
                                        Seguridad
                                    </button>
                                    <button
                                        onClick={() => setActiveTab("notifications")}
                                        className={`flex items-center gap-3 px-4 py-3 rounded-lg text-sm font-medium transition-colors whitespace-nowrap ${activeTab === "notifications"
                                            ? "bg-white text-blue-600 shadow-sm ring-1 ring-gray-200"
                                            : "text-gray-600 hover:bg-gray-100/50 hover:text-gray-900"
                                            }`}
                                    >
                                        <Bell className="w-4 h-4" />
                                        Notificaciones
                                    </button>

                                    {role === "Admin" && (
                                        <button
                                            onClick={() => setActiveTab("users")}
                                            className={`flex items-center gap-3 px-4 py-3 rounded-lg text-sm font-medium transition-colors whitespace-nowrap ${activeTab === "users"
                                                ? "bg-white text-blue-600 shadow-sm ring-1 ring-gray-200"
                                                : "text-gray-600 hover:bg-gray-100/50 hover:text-gray-900"
                                                }`}
                                        >
                                            <UserCog className="w-4 h-4" />
                                            Gestión de Usuarios
                                        </button>
                                    )}
                                </nav>
                            </aside>

                            {/* Main Content Area */}
                            <div className="flex-1 space-y-6">

                                {/* Profile Section */}
                                {activeTab === "profile" && (
                                    <div className="bg-white rounded-xl shadow-sm border border-gray-200 overflow-hidden">
                                        <div className="p-6 border-b border-gray-100">
                                            <h2 className="text-lg font-semibold text-gray-900">Información Personal</h2>
                                            <p className="text-sm text-gray-500">Actualiza tu foto y detalles personales.</p>
                                        </div>
                                        <div className="p-6 space-y-6">
                                            {/* Avatar */}
                                            <div className="flex items-center gap-6">
                                                <div className="relative">
                                                    <div className={`w-20 h-20 rounded-full flex items-center justify-center text-xl font-bold text-white overflow-hidden bg-gray-200 border-4 border-white shadow-sm`}>
                                                        {avatarPreview ? (
                                                            <Image src={avatarPreview} alt="Avatar" width={80} height={80} className="w-full h-full object-cover" />
                                                        ) : email ? (
                                                            <div className={`w-full h-full flex items-center justify-center ${getAvatarColor(email)}`}>
                                                                {email[0].toUpperCase()}
                                                            </div>
                                                        ) : (
                                                            <User className="w-8 h-8 text-gray-400" />
                                                        )}
                                                    </div>
                                                    <button className="absolute bottom-0 right-0 p-1.5 bg-blue-600 text-white rounded-full shadow-md hover:bg-blue-700 transition-colors">
                                                        <Camera className="w-3 h-3" />
                                                    </button>
                                                </div>
                                                <div>
                                                    <p className="text-sm font-medium text-gray-900">Tu foto</p>
                                                    <p className="text-xs text-gray-500">Haz clic para subir una nueva imagen.</p>
                                                </div>
                                            </div>

                                            <div className="grid gap-6 md:grid-cols-2">
                                                <div className="space-y-2">
                                                    <label className="text-sm font-medium text-gray-700">Email</label>
                                                    <div className="relative">
                                                        <Mail className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400" />
                                                        <input
                                                            type="email"
                                                            value={email || ""}
                                                            disabled
                                                            className="w-full pl-10 pr-4 py-2 border border-gray-200 rounded-lg bg-gray-50 text-gray-500 sm:text-sm"
                                                        />
                                                    </div>
                                                </div>
                                                <div className="space-y-2">
                                                    <label className="text-sm font-medium text-gray-700">Rol</label>
                                                    <div className="relative">
                                                        <Shield className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400" />
                                                        <input
                                                            type="text"
                                                            value={role || ""}
                                                            disabled
                                                            className="w-full pl-10 pr-4 py-2 border border-gray-200 rounded-lg bg-gray-50 text-gray-500 sm:text-sm"
                                                        />
                                                    </div>
                                                </div>
                                            </div>

                                            <div className="flex justify-end pt-4 border-t border-gray-100">
                                                <button className="px-4 py-2 bg-blue-600 text-white text-sm font-medium rounded-lg hover:bg-blue-700 transition-colors flex items-center gap-2">
                                                    <Save className="w-4 h-4" />
                                                    Guardar Cambios
                                                </button>
                                            </div>
                                        </div>
                                    </div>
                                )}

                                {/* Security Section */}
                                {activeTab === "security" && (
                                    <div className="bg-white rounded-xl shadow-sm border border-gray-200 overflow-hidden">
                                        <div className="p-6 border-b border-gray-100">
                                            <h2 className="text-lg font-semibold text-gray-900">Seguridad</h2>
                                            <p className="text-sm text-gray-500">Gestiona tu contraseña y seguridad.</p>
                                        </div>
                                        <div className="p-6 space-y-4">
                                            <div className="space-y-2">
                                                <label className="text-sm font-medium text-gray-700">Contraseña Actual</label>
                                                <input type="password" placeholder="••••••••" className="w-full px-4 py-2 border border-gray-200 rounded-lg focus:ring-2 focus:ring-blue-500/20 focus:border-blue-500 outline-none transition-all" />
                                            </div>
                                            <div className="space-y-2">
                                                <label className="text-sm font-medium text-gray-700">Nueva Contraseña</label>
                                                <input type="password" placeholder="••••••••" className="w-full px-4 py-2 border border-gray-200 rounded-lg focus:ring-2 focus:ring-blue-500/20 focus:border-blue-500 outline-none transition-all" />
                                            </div>
                                            <div className="space-y-2">
                                                <label className="text-sm font-medium text-gray-700">Confirmar Contraseña</label>
                                                <input type="password" placeholder="••••••••" className="w-full px-4 py-2 border border-gray-200 rounded-lg focus:ring-2 focus:ring-blue-500/20 focus:border-blue-500 outline-none transition-all" />
                                            </div>
                                            <div className="flex justify-end pt-4">
                                                <button className="px-4 py-2 bg-gray-900 text-white text-sm font-medium rounded-lg hover:bg-gray-800 transition-colors">
                                                    Actualizar Contraseña
                                                </button>
                                            </div>
                                        </div>
                                    </div>
                                )}

                                {/* Notifications Section */}
                                {activeTab === "notifications" && (
                                    <div className="bg-white rounded-xl shadow-sm border border-gray-200 overflow-hidden">
                                        <div className="p-6 border-b border-gray-100">
                                            <h2 className="text-lg font-semibold text-gray-900">Preferencias de Notificación</h2>
                                            <p className="text-sm text-gray-500">Elige qué actualizaciones quieres recibir.</p>
                                        </div>
                                        <div className="p-6 space-y-4">
                                            <div className="flex items-center justify-between py-2">
                                                <div>
                                                    <p className="text-sm font-medium text-gray-900">Notificaciones por Email</p>
                                                    <p className="text-xs text-gray-500">Recibe actualizaciones sobre entregas y revisiones.</p>
                                                </div>
                                                <label className="relative inline-flex items-center cursor-pointer">
                                                    <input type="checkbox" className="sr-only peer" defaultChecked />
                                                    <div className="w-11 h-6 bg-gray-200 peer-focus:outline-none peer-focus:ring-4 peer-focus:ring-blue-300 rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-blue-600"></div>
                                                </label>
                                            </div>
                                            <div className="flex items-center justify-between py-2 border-t border-gray-100 pt-4">
                                                <div>
                                                    <p className="text-sm font-medium text-gray-900">Notificaciones Push</p>
                                                    <p className="text-xs text-gray-500">Notificaciones instantáneas en el navegador.</p>
                                                </div>
                                                <label className="relative inline-flex items-center cursor-pointer">
                                                    <input type="checkbox" className="sr-only peer" />
                                                    <div className="w-11 h-6 bg-gray-200 peer-focus:outline-none peer-focus:ring-4 peer-focus:ring-blue-300 rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-blue-600"></div>
                                                </label>
                                            </div>
                                        </div>
                                    </div>
                                )}

                                {/* Admin Users Section */}
                                {activeTab === "users" && role === "Admin" && (
                                    <div className="bg-white rounded-xl shadow-sm border border-gray-200 overflow-hidden">
                                        <div className="p-6 border-b border-gray-100 flex justify-between items-center">
                                            <div>
                                                <h2 className="text-lg font-semibold text-gray-900">Gestión de Usuarios</h2>
                                                <p className="text-sm text-gray-500">Administra los usuarios del sistema.</p>
                                            </div>
                                            <button
                                                onClick={handleAddUser}
                                                className="px-3 py-1.5 bg-blue-600 text-white text-xs font-medium rounded-lg hover:bg-blue-700 transition-colors flex items-center gap-1.5"
                                            >
                                                <UserCog className="w-3.5 h-3.5" />
                                                Nuevo Usuario
                                            </button>
                                        </div>
                                        <div className="overflow-x-auto">
                                            <table className="w-full text-sm text-left">
                                                <thead className="text-xs text-gray-700 uppercase bg-gray-50 border-b border-gray-100">
                                                    <tr>
                                                        <th className="px-6 py-3">Usuario</th>
                                                        <th className="px-6 py-3">Rol</th>
                                                        <th className="px-6 py-3">Estado</th>
                                                        <th className="px-6 py-3 text-right">Acciones</th>
                                                    </tr>
                                                </thead>
                                                <tbody>
                                                    {users.map((user) => (
                                                        <tr key={user.id} className="bg-white border-b border-gray-100 hover:bg-gray-50/50">
                                                            <td className="px-6 py-4 font-medium text-gray-900 flex items-center gap-3">
                                                                <div className={`w-8 h-8 rounded-full flex items-center justify-center text-xs font-bold text-white ${getAvatarColor(user.email)}`}>
                                                                    {user.email[0].toUpperCase()}
                                                                </div>
                                                                {user.email}
                                                            </td>
                                                            <td className="px-6 py-4">
                                                                <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${user.role === "Admin" ? "bg-purple-100 text-purple-800" :
                                                                    user.role === "Profesor" ? "bg-blue-100 text-blue-800" :
                                                                        "bg-green-100 text-green-800"
                                                                    }`}>
                                                                    {user.role}
                                                                </span>
                                                            </td>
                                                            <td className="px-6 py-4">
                                                                <span className={`inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-full text-xs font-medium ${user.status === "Active" ? "bg-emerald-50 text-emerald-700 border border-emerald-200" : "bg-amber-50 text-amber-700 border border-amber-200"
                                                                    }`}>
                                                                    <span className={`w-1.5 h-1.5 rounded-full ${user.status === "Active" ? "bg-emerald-500" : "bg-amber-500"}`}></span>
                                                                    {user.status === "Active" ? "Activo" : "Pendiente"}
                                                                </span>
                                                            </td>
                                                            <td className="px-6 py-4 text-right">
                                                                <div className="flex items-center justify-end gap-2">
                                                                    <button
                                                                        onClick={() => handleEditUser(user)}
                                                                        className="p-1.5 text-gray-500 hover:bg-gray-100 rounded-lg transition-colors"
                                                                    >
                                                                        <Edit className="w-4 h-4" />
                                                                    </button>
                                                                    <button
                                                                        onClick={() => handleDeleteUser(user.id)}
                                                                        className="p-1.5 text-red-500 hover:bg-red-50 rounded-lg transition-colors"
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
