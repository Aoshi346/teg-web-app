"use client";

import React, { useState, useEffect } from "react";
import {
  X,
  Mail,
  Shield,
  User,
  Phone,
  BookOpen,
  ChevronDown,
  ChevronRight,
} from "lucide-react";

export interface UserData {
  id: number;
  fullName: string;
  email: string;
  semester?: string;
  phone?: string;
  role: "Estudiante" | "Tutor" | "Jurado" | "Administrador";
  status?: "active" | "pending";
}

interface UserModalProps {
  isOpen: boolean;
  onClose: () => void;
  onSave: (user: Omit<UserData, "id"> & { id?: number }) => void;
  initialData?: UserData | null;
}

export default function UserModal({
  isOpen,
  onClose,
  onSave,
  initialData,
}: UserModalProps) {
  const [fullName, setFullName] = useState("");
  const [email, setEmail] = useState("");
  const [semester, setSemester] = useState("9no");
  const [phone, setPhone] = useState("");
  const [role, setRole] = useState("Estudiante");

  useEffect(() => {
    if (initialData) {
      setFullName(initialData.fullName || "");
      setEmail(initialData.email || "");
      setSemester(initialData.semester || "9no");
      setPhone(initialData.phone || "");
      setRole(initialData.role || "Estudiante");
    } else {
      setFullName("");
      setEmail("");
      setSemester("9no");
      setPhone("");
      setRole("Estudiante");
    }
  }, [initialData, isOpen]);

  if (!isOpen) return null;

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    onSave({
      id: initialData?.id,
      fullName,
      email,
      semester,
      phone,
      role: role as UserData["role"],
    });
  };

  return (
    <div className="fixed inset-0 z-[100] flex items-center justify-center p-4">
      <div
        className="absolute inset-0 bg-black/40 backdrop-blur-sm transition-opacity duration-300 animate-in fade-in"
        onClick={onClose}
      />
      <div className="relative w-full max-w-2xl bg-white rounded-2xl shadow-2xl ring-1 ring-black/5 transform transition-all animate-in zoom-in-95 fade-in duration-200 overflow-hidden">
        {/* Compact Header */}
        <div className="relative bg-gradient-to-r from-blue-600 to-indigo-600 px-6 py-5 text-white">
          <div className="flex items-center justify-between">
            <div>
              <h2 className="text-xl font-bold tracking-tight">
                {initialData ? "Editar Usuario" : "Nuevo Usuario"}
              </h2>
              <p className="text-blue-100 text-sm">
                {initialData
                  ? "Modifica la información del usuario"
                  : "Completa los datos para crear un usuario"}
              </p>
            </div>
            <button
              onClick={onClose}
              className="p-2 text-white/70 hover:text-white hover:bg-white/20 rounded-full transition-colors"
            >
              <X className="w-5 h-5" />
            </button>
          </div>
        </div>

        {/* Compact Form - All visible without scroll */}
        <form onSubmit={handleSubmit} className="p-6 bg-gray-50/50">
          {/* Row 1: Name & Email */}
          <div className="grid grid-cols-2 gap-4 mb-4">
            <div>
              <label className="text-xs font-semibold text-gray-600 uppercase tracking-wide mb-1.5 block">
                Nombre Completo
              </label>
              <div className="relative">
                <User className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-gray-400" />
                <input
                  type="text"
                  required
                  value={fullName}
                  onChange={(e) => setFullName(e.target.value)}
                  placeholder="Ej: Juan Pérez"
                  className="w-full pl-10 pr-3 py-2.5 bg-white ring-1 ring-gray-200 rounded-xl text-sm text-gray-900 placeholder:text-gray-400 focus:ring-2 focus:ring-blue-500 outline-none transition-all"
                />
              </div>
            </div>
            <div>
              <label className="text-xs font-semibold text-gray-600 uppercase tracking-wide mb-1.5 block">
                Correo Electrónico
              </label>
              <div className="relative">
                <Mail className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-gray-400" />
                <input
                  type="email"
                  required
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  placeholder="correo@ejemplo.com"
                  className="w-full pl-10 pr-3 py-2.5 bg-white ring-1 ring-gray-200 rounded-xl text-sm text-gray-900 placeholder:text-gray-400 focus:ring-2 focus:ring-blue-500 outline-none transition-all"
                />
              </div>
            </div>
          </div>

          {/* Row 2: Phone, Semester, Role */}
          <div className="grid grid-cols-3 gap-4 mb-6">
            <div>
              <label className="text-xs font-semibold text-gray-600 uppercase tracking-wide mb-1.5 block">
                Teléfono
              </label>
              <div className="relative">
                <Phone className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-gray-400" />
                <input
                  type="tel"
                  value={phone}
                  onChange={(e) => setPhone(e.target.value)}
                  placeholder="0412-1234567"
                  className="w-full pl-10 pr-3 py-2.5 bg-white ring-1 ring-gray-200 rounded-xl text-sm text-gray-900 placeholder:text-gray-400 focus:ring-2 focus:ring-blue-500 outline-none transition-all"
                />
              </div>
            </div>
            <div>
              <label className="text-xs font-semibold text-gray-600 uppercase tracking-wide mb-1.5 block">
                Semestre
              </label>
              <div className="relative">
                <BookOpen className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-gray-400" />
                <select
                  value={semester}
                  onChange={(e) => setSemester(e.target.value)}
                  className="w-full pl-10 pr-8 py-2.5 bg-white ring-1 ring-gray-200 rounded-xl text-sm text-gray-900 focus:ring-2 focus:ring-blue-500 outline-none transition-all appearance-none cursor-pointer"
                >
                  <option value="9no">9no Semestre</option>
                  <option value="10mo">10mo Semestre</option>
                  <option value="N/A">N/A</option>
                </select>
                <ChevronDown className="absolute right-3 top-1/2 -translate-y-1/2 h-4 w-4 text-gray-400 pointer-events-none" />
              </div>
            </div>
            <div>
              <label className="text-xs font-semibold text-gray-600 uppercase tracking-wide mb-1.5 block">
                Rol
              </label>
              <div className="relative">
                <Shield className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-gray-400" />
                <select
                  value={role}
                  onChange={(e) => setRole(e.target.value)}
                  className="w-full pl-10 pr-8 py-2.5 bg-white ring-1 ring-gray-200 rounded-xl text-sm text-gray-900 focus:ring-2 focus:ring-blue-500 outline-none transition-all appearance-none cursor-pointer"
                >
                  <option value="Estudiante">Estudiante</option>
                  <option value="Tutor">Tutor</option>
                  <option value="Jurado">Jurado</option>
                  <option value="Administrador">Administrador</option>
                </select>
                <ChevronDown className="absolute right-3 top-1/2 -translate-y-1/2 h-4 w-4 text-gray-400 pointer-events-none" />
              </div>
            </div>
          </div>

          {/* Actions */}
          <div className="flex justify-end gap-3 pt-4 border-t border-gray-200">
            <button
              type="button"
              onClick={onClose}
              className="px-5 py-2.5 text-sm font-semibold text-gray-600 bg-white ring-1 ring-gray-200 hover:bg-gray-50 rounded-xl transition-colors"
            >
              Cancelar
            </button>
            <button
              type="submit"
              className="px-6 py-2.5 text-sm font-semibold text-white bg-blue-600 hover:bg-blue-700 rounded-xl shadow-md shadow-blue-500/25 active:scale-95 transition-all flex items-center gap-2"
            >
              {initialData ? "Guardar" : "Crear Usuario"}
              <ChevronRight className="w-4 h-4" />
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
