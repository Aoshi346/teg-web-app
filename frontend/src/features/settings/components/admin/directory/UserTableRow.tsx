"use client";
import React from "react";

export interface DirectoryUser {
  id: number;
  fullName: string;
  email: string;
  role: "Administrador" | "Tutor" | "Jurado" | "Estudiante";
  nationality?: "V" | "E" | "P";
  cedula?: string;
  semester?: string;
  status: "active" | "pending" | "rejected";
}

interface UserTableRowProps {
  user: DirectoryUser;
  onEdit: (u: DirectoryUser) => void;
  onDelete: (u: DirectoryUser) => void;
  onToggleStatus: (u: DirectoryUser, next: "active" | "rejected") => void;
}

const ROLE_STYLES: Record<DirectoryUser["role"], string> = {
  Administrador: "bg-purple-50 text-purple-700 border-purple-200",
  Tutor: "bg-blue-50 text-blue-700 border-blue-200",
  Jurado: "bg-amber-50 text-amber-700 border-amber-200",
  Estudiante: "bg-emerald-50 text-emerald-700 border-emerald-200",
};

export function UserTableRow({ user, onEdit, onDelete, onToggleStatus }: UserTableRowProps) {
  const isActive = user.status === "active";
  return (
    <tr className="border-b border-gray-100">
      <td className="px-4 py-3">
        <div className="font-semibold text-gray-900 text-sm">{user.fullName}</div>
        <div className="text-xs text-gray-500">{user.email}</div>
      </td>
      <td className="px-4 py-3">
        <span className={`px-2 py-0.5 rounded-full text-xs font-semibold border ${ROLE_STYLES[user.role]}`}>
          {user.role}
        </span>
      </td>
      <td className="px-4 py-3 text-sm text-gray-700">
        {user.cedula ? `${user.nationality || "V"}-${user.cedula}` : "—"}
      </td>
      <td className="px-4 py-3 text-sm text-gray-700">{user.semester || "—"}</td>
      <td className="px-4 py-3">
        <label className="inline-flex items-center gap-2 cursor-pointer">
          <input
            type="checkbox"
            className="sr-only peer"
            checked={isActive}
            onChange={(e) => onToggleStatus(user, e.target.checked ? "active" : "rejected")}
          />
          <span className="relative inline-block w-8 h-4 rounded-full bg-gray-300 peer-checked:bg-emerald-500 transition">
            <span className={`absolute top-0.5 w-3 h-3 bg-white rounded-full transition ${isActive ? "left-4" : "left-0.5"}`} />
          </span>
          <span className={`text-xs font-medium ${isActive ? "text-emerald-700" : "text-gray-500"}`}>
            {isActive ? "Activo" : user.status === "pending" ? "Pendiente" : "Inactivo"}
          </span>
        </label>
      </td>
      <td className="px-4 py-3 text-center">
        <button onClick={() => onEdit(user)} className="px-2 py-1 bg-transparent border border-gray-300 rounded text-xs text-gray-700 mr-1">
          Editar
        </button>
        <button onClick={() => onDelete(user)} className="px-2 py-1 bg-transparent border border-red-200 rounded text-xs text-red-700">
          Eliminar
        </button>
      </td>
    </tr>
  );
}
