"use client";
import React, { useEffect, useState } from "react";
import { Clock } from "lucide-react";
import { getAllUsers, updateStatusById, type User as AuthUser } from "@features/auth/api/clientAuth";
import { PendingUserRow, type PendingUser } from "./PendingUserRow";
import { RejectConfirmModal } from "./RejectConfirmModal";

function toPending(u: AuthUser): PendingUser {
  return {
    id: u.id as number,
    fullName: u.fullName || `${u.firstName || ""} ${u.lastName || ""}`.trim(),
    email: u.email || "",
    role: u.role as PendingUser["role"],
    nationality: u.nationality as "V" | "E" | "P" | undefined,
    cedula: u.cedula ? String(u.cedula) : undefined,
    semester: u.semester || undefined,
    phone: u.phone || undefined,
    dateJoined: u.dateJoined || new Date().toISOString(),
  };
}

export function PendingUsersPanel() {
  const [list, setList] = useState<PendingUser[]>([]);
  const [rejecting, setRejecting] = useState<PendingUser | null>(null);

  async function refresh() {
    const all = await getAllUsers();
    setList(all.filter((u) => u.status === "pending").map(toPending));
  }
  useEffect(() => { refresh(); }, []);

  async function handleApprove(u: PendingUser) {
    await updateStatusById(u.id, "active");
    await refresh();
  }

  async function handleReject() {
    if (!rejecting) return;
    try {
      await updateStatusById(rejecting.id, "rejected");
      await refresh();
    } finally {
      setRejecting(null);
    }
  }

  return (
    <div className="flex flex-col">
      <div className="mb-4">
        <h2 className="text-xl font-bold text-text-strong tracking-tight leading-tight">Usuarios pendientes</h2>
        <p className="text-[13.5px] text-text-muted mt-1 max-w-[70ch]">
          Revisa y aprueba a los usuarios recién registrados antes de que puedan acceder al sistema.
        </p>
      </div>

      <div className="px-[18px] py-3.5 bg-gradient-to-r from-pending-soft to-transparent border border-[rgba(184,121,0,0.22)] rounded-xl mb-[18px] flex items-center gap-3.5">
        <div className="w-9 h-9 rounded-[10px] bg-[rgba(184,121,0,0.15)] text-pending flex items-center justify-center flex-shrink-0">
          <Clock className="w-[18px] h-[18px]" />
        </div>
        <div>
          <strong className="block text-[13.5px] font-bold text-[#92580a] mb-0.5">
            {list.length} usuario{list.length === 1 ? "" : "s"} esperan aprobación
          </strong>
          <div className="text-[12.5px] text-[#6e4308]">
            Revisa los datos antes de aprobar o rechazar. Los usuarios rechazados no podrán iniciar sesión.
          </div>
        </div>
      </div>

      {list.length === 0 ? (
        <div className="p-8 bg-surface border border-dashed border-border-default rounded-[14px] text-center">
          <div className="text-sm text-text-default font-semibold">No hay usuarios pendientes de aprobación.</div>
        </div>
      ) : (
        <div className="flex flex-col gap-3">
          {list.map((u) => (
            <PendingUserRow key={u.id} user={u} onApprove={handleApprove} onReject={() => setRejecting(u)} />
          ))}
        </div>
      )}

      {rejecting && (
        <RejectConfirmModal
          isOpen={true}
          userName={rejecting.fullName}
          onConfirm={handleReject}
          onCancel={() => setRejecting(null)}
        />
      )}
    </div>
  );
}
