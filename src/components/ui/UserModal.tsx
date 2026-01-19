"use client";

import React, { useState, useEffect } from "react";
import { X, Mail, Shield, Activity, ChevronDown, ChevronRight } from "lucide-react";

export interface UserData {
    id: number;
    email: string;
    role: string;
    status: string;
}

interface UserModalProps {
    isOpen: boolean;
    onClose: () => void;
    onSave: (user: Omit<UserData, "id"> & { id?: number }) => void;
    initialData?: UserData | null;
}

export default function UserModal({ isOpen, onClose, onSave, initialData }: UserModalProps) {
    const [email, setEmail] = useState("");
    const [role, setRole] = useState("Estudiante");
    const [status, setStatus] = useState("Active");

    useEffect(() => {
        if (initialData) {
            setEmail(initialData.email);
            setRole(initialData.role);
            setStatus(initialData.status);
        } else {
            setEmail("");
            setRole("Estudiante");
            setStatus("Active");
        }
    }, [initialData, isOpen]);

    if (!isOpen) return null;

    const handleSubmit = (e: React.FormEvent) => {
        e.preventDefault();
        onSave({
            id: initialData?.id,
            email,
            role,
            status,
        });
    };

    return (
        <div className="fixed inset-0 z-[100] flex items-center justify-center p-4 sm:p-6">
            <div
                className="absolute inset-0 bg-indigo-900/30 backdrop-blur-sm transition-opacity duration-300 animate-in fade-in"
                onClick={onClose}
            />
            <div className="relative w-full max-w-lg bg-white rounded-3xl shadow-2xl ring-1 ring-black/5 transform transition-all animate-in zoom-in-95 fade-in duration-300 flex flex-col max-h-[90vh] overflow-hidden">

                {/* Colorful Header */}
                <div className="relative bg-gradient-to-br from-blue-600 to-indigo-700 px-8 py-8 text-white overflow-hidden">
                    <div className="absolute top-0 right-0 -mt-8 -mr-8 w-32 h-32 bg-white/10 rounded-full blur-2xl"></div>
                    <div className="absolute bottom-0 left-0 -mb-8 -ml-8 w-24 h-24 bg-white/10 rounded-full blur-xl"></div>

                    <div className="relative z-10 flex items-start justify-between">
                        <div>
                            <h2 className="text-3xl font-bold tracking-tight text-white mb-2">
                                {initialData ? "Editar Usuario" : "Crear Usuario"}
                            </h2>
                            <p className="text-blue-100 font-medium">
                                {initialData ? "Actualiza los datos del usuario." : "Agrega un nuevo miembro al equipo."}
                            </p>
                        </div>
                        <button
                            onClick={onClose}
                            className="p-2 text-white/70 hover:text-white hover:bg-white/20 rounded-full transition-colors backdrop-blur-sm"
                        >
                            <X className="w-6 h-6" />
                        </button>
                    </div>
                </div>

                <form onSubmit={handleSubmit} className="p-8 space-y-8 overflow-y-auto bg-gray-50/50 flex-1">
                    {/* Email Field */}
                    <div className="space-y-3">
                        <label className="text-base font-bold text-gray-800 flex items-center gap-2">
                            Email Corporativo
                        </label>
                        <div className="relative group">
                            <div className="absolute inset-y-0 left-0 pl-4 flex items-center pointer-events-none">
                                <Mail className="h-5 w-5 text-gray-400 group-focus-within:text-blue-600 transition-colors" />
                            </div>
                            <input
                                type="email"
                                required
                                value={email}
                                onChange={(e) => setEmail(e.target.value)}
                                placeholder="nombre@tesisfar.com"
                                className="block w-full pl-11 pr-4 py-4 bg-white border-0 ring-1 ring-gray-200 rounded-2xl text-gray-900 placeholder:text-gray-400 focus:ring-2 focus:ring-blue-600 transition-all shadow-sm text-base"
                            />
                        </div>
                        <p className="text-sm text-gray-500 pl-1">Se enviará una invitación a este correo.</p>
                    </div>

                    <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                        {/* Role Field */}
                        <div className="space-y-3">
                            <label className="text-base font-bold text-gray-800">Rol del Sistema</label>
                            <div className="relative">
                                <div className="absolute inset-y-0 left-0 pl-4 flex items-center pointer-events-none">
                                    <Shield className="h-5 w-5 text-gray-400" />
                                </div>
                                <select
                                    value={role}
                                    onChange={(e) => setRole(e.target.value)}
                                    className="block w-full pl-11 pr-4 py-4 bg-white border-0 ring-1 ring-gray-200 rounded-2xl text-gray-900 focus:ring-2 focus:ring-blue-600 transition-all shadow-sm appearance-none cursor-pointer text-base"
                                >
                                    <option value="Estudiante">Estudiante</option>
                                    <option value="Profesor">Profesor</option>
                                    <option value="Admin">Administrador</option>
                                </select>
                                <div className="absolute inset-y-0 right-0 pr-4 flex items-center pointer-events-none text-gray-400">
                                    <ChevronDown className="w-5 h-5" />
                                </div>
                            </div>
                        </div>

                        {/* Status Field */}
                        <div className="space-y-3">
                            <label className="text-base font-bold text-gray-800">Estado</label>
                            <div className="relative">
                                <div className="absolute inset-y-0 left-0 pl-4 flex items-center pointer-events-none">
                                    <Activity className="h-5 w-5 text-gray-400" />
                                </div>
                                <select
                                    value={status}
                                    onChange={(e) => setStatus(e.target.value)}
                                    className="block w-full pl-11 pr-4 py-4 bg-white border-0 ring-1 ring-gray-200 rounded-2xl text-gray-900 focus:ring-2 focus:ring-blue-600 transition-all shadow-sm appearance-none cursor-pointer text-base"
                                >
                                    <option value="Active">Activo</option>
                                    <option value="Pending">Pendiente</option>
                                    <option value="Inactive">Inactivo</option>
                                </select>
                                <div className="absolute inset-y-0 right-0 pr-4 flex items-center pointer-events-none text-gray-400">
                                    <ChevronDown className="w-5 h-5" />
                                </div>
                            </div>
                        </div>
                    </div>


                </form>

                {/* Footer */}
                <div className="p-6 bg-white border-t border-gray-100 flex justify-end gap-3 z-10 sticky bottom-0">
                    <button
                        type="button"
                        onClick={onClose}
                        className="px-6 py-3 text-sm font-bold text-gray-600 bg-gray-50 hover:bg-gray-100 rounded-xl transition-colors"
                    >
                        Cancelar
                    </button>
                    <button
                        onClick={handleSubmit}
                        className="px-8 py-3 text-sm font-bold text-white bg-blue-600 hover:bg-blue-700 rounded-xl shadow-lg shadow-blue-600/30 hover:shadow-blue-600/40 transform active:scale-95 transition-all flex items-center gap-2"
                    >
                        {initialData ? "Guardar Cambios" : "Crear Usuario"}
                        <ChevronRight className="w-4 h-4" />
                    </button>
                </div>
            </div>
        </div>
    );
}
