"use client";
import React from "react";

export interface PendingUser {
  id: number;
  fullName: string;
  email: string;
  role: "Administrador" | "Tutor" | "Jurado" | "Estudiante";
  nationality?: "V" | "E" | "P";
  cedula?: string;
  semester?: string;
  phone?: string;
  dateJoined: string;
}

interface PendingUserRowProps {
  user: PendingUser;
  onApprove: (u: PendingUser) => void;
  onReject: (u: PendingUser) => void;
}

function relativeTime(iso: string): string {
  const then = new Date(iso).getTime();
  const now = Date.now();
  const diffMs = now - then;
  const mins = Math.floor(diffMs / 60000);
  if (mins < 60) return `hace ${mins} min`;
  const hours = Math.floor(mins / 60);
  if (hours < 24) return `hace ${hours} hora${hours === 1 ? "" : "s"}`;
  const days = Math.floor(hours / 24);
  return `hace ${days} día${days === 1 ? "" : "s"}`;
}

function initials(name: string): string {
  return name.split(" ").map((p) => p[0] || "").join("").slice(0, 2).toUpperCase();
}

export function PendingUserRow({ user, onApprove, onReject }: PendingUserRowProps) {
  return (
    <div className="bg-white border border-gray-200 rounded-lg p-4">
      <div className="flex items-start gap-3">
        <div className="w-11 h-11 rounded-full bg-blue-600 text-white flex items-center justify-center font-semibold text-sm">
          {initials(user.fullName)}
        </div>
        <div className="flex-1">
          <div className="flex justify-between items-start">
            <div>
              <div className="font-semibold text-gray-900 text-sm">{user.fullName}</div>
              <div className="text-xs text-gray-500">{user.email}</div>
            </div>
            <span className="px-2 py-0.5 rounded-full bg-amber-100 text-amber-700 text-xs font-semibold">Pendiente</span>
          </div>
          <div className="grid grid-cols-4 gap-3 mt-3 p-2.5 bg-gray-50 rounded-lg text-xs">
            <div>
              <div className="uppercase tracking-wide text-gray-500">Rol solicitado</div>
              <div className="font-medium text-gray-900">{user.role}</div>
            </div>
            <div>
              <div className="uppercase tracking-wide text-gray-500">Cédula</div>
              <div className="font-medium text-gray-900">
                {user.cedula ? `${user.nationality || "V"}-${user.cedula}` : "—"}
              </div>
            </div>
            <div>
              <div className="uppercase tracking-wide text-gray-500">{user.role === "Estudiante" ? "Semestre" : "Teléfono"}</div>
              <div className="font-medium text-gray-900">
                {user.role === "Estudiante" ? (user.semester || "—") : (user.phone || "—")}
              </div>
            </div>
            <div>
              <div className="uppercase tracking-wide text-gray-500">Registrado</div>
              <div className="font-medium text-gray-900">{relativeTime(user.dateJoined)}</div>
            </div>
          </div>
          <div className="flex gap-2 justify-end mt-3">
            <button onClick={() => onReject(user)} className="px-3 py-1.5 bg-white text-red-700 border border-red-200 rounded-md text-xs font-semibold">
              Rechazar
            </button>
            <button onClick={() => onApprove(user)} className="px-3 py-1.5 bg-emerald-500 text-white rounded-md text-xs font-semibold">
              Aprobar
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
