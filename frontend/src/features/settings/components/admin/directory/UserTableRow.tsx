"use client";
import React from "react";
import { Pencil, Trash2 } from "lucide-react";

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

const ROLE_PILL_STYLES: Record<DirectoryUser["role"], string> = {
  Administrador: "bg-[#f5f0fc] text-[#6e35d1] border-[#d9c8f1]",
  Tutor: "bg-[rgba(0,102,255,0.08)] text-primary border-[rgba(0,102,255,0.18)]",
  Jurado: "bg-pending-soft text-pending border-[rgba(184,121,0,0.22)]",
  Estudiante: "bg-success-soft text-success border-[rgba(26,135,84,0.2)]",
};

const AVATAR_GRADIENTS = [
  "bg-gradient-to-br from-primary to-[#1d4ed8]",
  "bg-gradient-to-br from-[#8b5cf6] to-[#6d28d9]",
  "bg-gradient-to-br from-[#10b981] to-[#047857]",
  "bg-gradient-to-br from-[#ff6b35] to-[#c2410c]",
];

function avatarGradient(name: string): string {
  let hash = 0;
  for (let i = 0; i < name.length; i++) hash = (hash + name.charCodeAt(i)) % 7919;
  return AVATAR_GRADIENTS[hash % AVATAR_GRADIENTS.length];
}

function initials(name: string): string {
  return name.split(" ").filter(Boolean).map((p) => p[0] || "").join("").slice(0, 2).toUpperCase() || "?";
}

export function UserTableRow({ user, onEdit, onDelete, onToggleStatus }: UserTableRowProps) {
  const isActive = user.status === "active";
  const statusLabel = isActive ? "Activo" : user.status === "pending" ? "Pendiente" : "Inactivo";

  return (
    <tr className="border-b border-border-subtle transition-colors hover:bg-[rgba(0,102,255,0.025)]">
      <td className="px-4 py-3.5 align-middle">
        <div className="flex items-center gap-[11px]">
          <div className={`w-8 h-8 rounded-lg text-white flex items-center justify-center text-[11px] font-bold flex-shrink-0 ${avatarGradient(user.fullName)}`}>
            {initials(user.fullName)}
          </div>
          <div className="min-w-0">
            <div className="text-[13.5px] font-bold text-text-strong">{user.fullName}</div>
            <div className="text-xs text-text-muted mt-px truncate">{user.email}</div>
          </div>
        </div>
      </td>
      <td className="px-4 py-3.5 align-middle">
        <span className={`inline-flex px-2 py-0.5 rounded-full text-[11px] font-bold border tracking-[0.02em] ${ROLE_PILL_STYLES[user.role]}`}>
          {user.role}
        </span>
      </td>
      <td className="px-4 py-3.5 align-middle font-mono text-[12.5px] text-text-default font-medium">
        {user.cedula ? `${user.nationality || "V"}-${user.cedula}` : "—"}
      </td>
      <td className="px-4 py-3.5 align-middle text-[13px] text-text-default font-medium">
        {user.semester || "—"}
      </td>
      <td className="px-4 py-3.5 align-middle">
        <label className="relative inline-flex items-center gap-2 cursor-pointer">
          <input
            type="checkbox"
            className="sr-only peer"
            checked={isActive}
            onChange={(e) => onToggleStatus(user, e.target.checked ? "active" : "rejected")}
          />
          <span className="relative w-[30px] h-[17px] rounded-full bg-[#cbd2dc] peer-checked:bg-success transition-colors">
            <span className={`absolute top-[2px] w-[13px] h-[13px] rounded-full bg-white shadow-[0_1px_3px_rgba(0,0,0,0.2)] transition-transform ${isActive ? "left-[15px]" : "left-[2px]"}`} />
          </span>
          <span className={`text-xs font-semibold ${isActive ? "text-success" : "text-text-muted"}`}>
            {statusLabel}
          </span>
        </label>
      </td>
      <td className="px-4 py-3.5 align-middle text-right whitespace-nowrap">
        <button
          onClick={() => onEdit(user)}
          aria-label="Editar"
          title="Editar"
          className="w-[30px] h-[30px] border border-border-subtle bg-surface rounded-md text-text-muted inline-flex items-center justify-center ml-1 hover:bg-surface-sunken hover:text-text-default hover:border-border-default transition-colors"
        >
          <Pencil className="w-3.5 h-3.5" />
        </button>
        <button
          onClick={() => onDelete(user)}
          aria-label="Eliminar"
          title="Eliminar"
          className="w-[30px] h-[30px] border border-border-subtle bg-surface rounded-md text-text-muted inline-flex items-center justify-center ml-1 hover:bg-destructive-soft hover:text-destructive hover:border-[rgba(209,56,56,0.3)] transition-colors"
        >
          <Trash2 className="w-3.5 h-3.5" />
        </button>
      </td>
    </tr>
  );
}
