"use client";
import React, { useEffect, useState } from "react";
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
    <div className="flex flex-col gap-3">
      <div className="flex items-center gap-2 px-4 py-3 bg-amber-50 border border-amber-200 rounded-lg">
        <div className="flex-1">
          <div className="text-sm font-semibold text-amber-900">
            {list.length} usuario{list.length === 1 ? "" : "s"} esperan aprobación
          </div>
          <div className="text-xs text-amber-800">
            Revise los datos antes de aprobar o rechazar. Los usuarios rechazados no podrán iniciar sesión.
          </div>
        </div>
      </div>
      {list.length === 0 ? (
        <div className="p-8 bg-blue-50 border border-dashed border-blue-300 rounded-lg text-center">
          <div className="text-sm text-blue-900 font-semibold">No hay usuarios pendientes de aprobación.</div>
        </div>
      ) : (
        list.map((u) => (
          <PendingUserRow key={u.id} user={u} onApprove={handleApprove} onReject={() => setRejecting(u)} />
        ))
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
