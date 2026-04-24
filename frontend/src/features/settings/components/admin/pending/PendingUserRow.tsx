"use client";
import React from "react";
import { Check } from "lucide-react";

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

const ROLE_PILL_STYLES: Record<PendingUser["role"], string> = {
  Administrador: "bg-[#f5f0fc] text-[#6e35d1] border-[#d9c8f1]",
  Tutor: "bg-[rgba(0,102,255,0.08)] text-primary border-[rgba(0,102,255,0.18)]",
  Jurado: "bg-pending-soft text-pending border-[rgba(184,121,0,0.22)]",
  Estudiante: "bg-success-soft text-success border-[rgba(26,135,84,0.2)]",
};

export function PendingUserRow({ user, onApprove, onReject }: PendingUserRowProps) {
  return (
    <div className="bg-surface border border-border-subtle rounded-[14px] p-[18px] shadow-[0_1px_2px_rgba(15,23,42,0.03)] transition-all hover:border-[rgba(0,102,255,0.25)] hover:shadow-[0_4px_12px_rgba(15,23,42,0.05)]">
      <div className="flex items-start gap-3.5">
        <div
          className={`w-11 h-11 rounded-xl text-white flex items-center justify-center font-bold text-[15px] flex-shrink-0 ${avatarGradient(user.fullName)}`}
        >
          {initials(user.fullName)}
        </div>
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2.5 flex-wrap">
            <h4 className="text-[15px] font-bold text-text-strong tracking-tight">{user.fullName}</h4>
            <span className={`inline-flex px-2 py-0.5 rounded-full text-[11px] font-bold border ${ROLE_PILL_STYLES[user.role]}`}>
              {user.role}
            </span>
            <span className="inline-flex items-center gap-1 text-[11px] font-bold px-2 py-0.5 rounded-full bg-pending-soft text-pending border border-[rgba(184,121,0,0.22)] tracking-[0.02em]">
              <span className="w-1.5 h-1.5 rounded-full bg-pending" />
              Pendiente
            </span>
          </div>
          <div className="text-[12.5px] text-text-muted mt-0.5">{user.email}</div>
        </div>
      </div>

      <div className="grid grid-cols-2 md:grid-cols-4 gap-3.5 mt-3.5 px-3.5 py-3 bg-surface-sunken rounded-[10px]">
        <div>
          <div className="text-[10.5px] font-bold text-text-muted uppercase tracking-[0.06em] mb-0.5">Cédula</div>
          <div className="text-[13px] font-semibold text-text-strong">
            {user.cedula ? `${user.nationality || "V"}-${user.cedula}` : "—"}
          </div>
        </div>
        <div>
          <div className="text-[10.5px] font-bold text-text-muted uppercase tracking-[0.06em] mb-0.5">
            {user.role === "Estudiante" ? "Semestre" : "Teléfono"}
          </div>
          <div className="text-[13px] font-semibold text-text-strong">
            {user.role === "Estudiante" ? (user.semester || "—") : (user.phone || "—")}
          </div>
        </div>
        <div>
          <div className="text-[10.5px] font-bold text-text-muted uppercase tracking-[0.06em] mb-0.5">
            {user.role === "Estudiante" ? "Teléfono" : "Rol"}
          </div>
          <div className="text-[13px] font-semibold text-text-strong">
            {user.role === "Estudiante" ? (user.phone || "—") : user.role}
          </div>
        </div>
        <div>
          <div className="text-[10.5px] font-bold text-text-muted uppercase tracking-[0.06em] mb-0.5">Registrado</div>
          <div className="text-[13px] font-semibold text-text-strong">{relativeTime(user.dateJoined)}</div>
        </div>
      </div>

      <div className="flex gap-2 justify-end mt-3.5">
        <button
          onClick={() => onReject(user)}
          className="h-8 px-3 bg-surface text-text-default border border-border-default rounded-[7px] text-[12.5px] font-semibold transition-colors hover:bg-destructive-soft hover:text-destructive hover:border-[rgba(209,56,56,0.4)]"
        >
          Rechazar
        </button>
        <button
          onClick={() => onApprove(user)}
          className="h-8 px-3 bg-success text-white rounded-[7px] text-[12.5px] font-semibold inline-flex items-center gap-1.5 transition-colors hover:bg-[#156d44]"
        >
          <Check className="w-3.5 h-3.5" strokeWidth={3} />
          Aprobar
        </button>
      </div>
    </div>
  );
}
