"use client";
import React, { useEffect, useState } from "react";
import { getAllUsers, createUser, updateUser, deleteUser as deleteUserApi, updateStatusById, type User as AuthUser } from "@features/auth/api/clientAuth";
import { UserModal, type UserModalData } from "./UserModal";
import { PasswordRevealModal } from "./PasswordRevealModal";
import { UserTable } from "./UserTable";
import type { DirectoryUser } from "./UserTableRow";
import type { UserInput } from "../../../lib/schemas";

function toDirectoryUser(u: AuthUser): DirectoryUser {
  return {
    id: u.id as number,
    fullName: u.fullName || `${u.firstName || ""} ${u.lastName || ""}`.trim(),
    email: u.email || "",
    role: u.role as DirectoryUser["role"],
    nationality: u.nationality as "V" | "E" | "P" | undefined,
    cedula: u.cedula ? String(u.cedula) : undefined,
    semester: u.semester || undefined,
    status: (u.status || "active") as DirectoryUser["status"],
  };
}

export function UserDirectoryPanel() {
  const [users, setUsers] = useState<DirectoryUser[]>([]);
  const [search, setSearch] = useState("");
  const [roleFilter, setRoleFilter] = useState("all");
  const [statusFilter, setStatusFilter] = useState("all");
  const [modalOpen, setModalOpen] = useState(false);
  const [editing, setEditing] = useState<UserModalData | null>(null);
  const [passwordModal, setPasswordModal] = useState<string | null>(null);

  async function refresh() {
    const list = await getAllUsers();
    setUsers(list.map(toDirectoryUser));
  }
  useEffect(() => { refresh(); }, []);

  async function handleSave(data: UserInput) {
    try {
      if (editing?.id) {
        await updateUser(editing.id, {
          fullName: data.fullName,
          email: data.email,
          cedula: data.cedula,
          nationality: data.nationality,
          phone: data.phone || "",
          role: data.role,
          semester: data.role === "Estudiante" ? data.semester : "",
        });
      } else {
        const { temporaryPassword } = await createUser({
          role: data.role,
          fullName: data.fullName,
          email: data.email,
          cedula: data.cedula,
          nationality: data.nationality,
          phone: data.phone || "",
          semester: data.role === "Estudiante" ? data.semester : undefined,
        } as AuthUser);
        setPasswordModal(temporaryPassword);
      }
      setModalOpen(false);
      setEditing(null);
      await refresh();
    } catch {
      window.alert("Error al guardar usuario");
    }
  }

  async function handleToggleStatus(u: DirectoryUser, next: "active" | "rejected") {
    if (next === "rejected") {
      const confirmed = window.confirm(`${u.fullName} no podrá iniciar sesión. ¿Continuar?`);
      if (!confirmed) return;
    }
    await updateStatusById(u.id, next);
    await refresh();
  }

  async function handleDelete(u: DirectoryUser) {
    if (!window.confirm(`¿Eliminar a ${u.fullName}? Esta acción no se puede deshacer.`)) return;
    try {
      await deleteUserApi(u.id);
      await refresh();
    } catch (e: unknown) {
      const msg = (e as { detail?: string } | undefined)?.detail || "Error al eliminar";
      window.alert(msg);
    }
  }

  return (
    <div className="flex flex-col gap-3">
      <div className="flex gap-3 flex-wrap">
        <input
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          placeholder="Buscar por nombre, email o cédula..."
          className="flex-1 min-w-[220px] px-3 py-2 border border-gray-300 rounded-md text-sm"
        />
        <select value={roleFilter} onChange={(e) => setRoleFilter(e.target.value)} className="px-3 py-2 border border-gray-300 rounded-md text-sm bg-white">
          <option value="all">Todos los roles</option>
          <option value="Administrador">Administrador</option>
          <option value="Tutor">Tutor</option>
          <option value="Jurado">Jurado</option>
          <option value="Estudiante">Estudiante</option>
        </select>
        <select value={statusFilter} onChange={(e) => setStatusFilter(e.target.value)} className="px-3 py-2 border border-gray-300 rounded-md text-sm bg-white">
          <option value="all">Todos los estados</option>
          <option value="active">Activos</option>
          <option value="pending">Pendientes</option>
          <option value="rejected">Rechazados</option>
        </select>
        <button onClick={() => { setEditing(null); setModalOpen(true); }} className="px-3 py-2 bg-blue-600 text-white rounded-md text-sm font-semibold">
          + Nuevo usuario
        </button>
      </div>
      <UserTable
        users={users}
        search={search}
        roleFilter={roleFilter}
        statusFilter={statusFilter}
        onEdit={(u) => { setEditing(u as unknown as UserModalData); setModalOpen(true); }}
        onDelete={handleDelete}
        onToggleStatus={handleToggleStatus}
      />
      <UserModal
        isOpen={modalOpen}
        onClose={() => { setModalOpen(false); setEditing(null); }}
        onSave={handleSave}
        initialData={editing}
      />
      {passwordModal && (
        <PasswordRevealModal isOpen={true} password={passwordModal} onClose={() => setPasswordModal(null)} />
      )}
    </div>
  );
}
