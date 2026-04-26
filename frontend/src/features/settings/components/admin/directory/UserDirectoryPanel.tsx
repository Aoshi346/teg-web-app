"use client";
import React, { useEffect, useMemo, useState } from "react";
import { Search, Users, GraduationCap, UserCircle, Plus, SlidersHorizontal } from "lucide-react";
import {
  getAllUsers,
  createUser,
  updateUser,
  deleteUser as deleteUserApi,
  updateStatusById,
  type User as AuthUser,
} from "@features/auth/api/clientAuth";
import { UserModal, type UserModalData } from "./UserModal";
import { PasswordRevealModal } from "./PasswordRevealModal";
import ResetPasswordModal from "./ResetPasswordModal";
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
  const [resetTarget, setResetTarget] = useState<DirectoryUser | null>(null);

  async function refresh() {
    const list = await getAllUsers();
    setUsers(list.map(toDirectoryUser));
  }
  useEffect(() => { refresh(); }, []);

  const stats = useMemo(() => {
    const total = users.length;
    const activos = users.filter((u) => u.status === "active").length;
    const pendientes = users.filter((u) => u.status === "pending").length;
    const estudiantes = users.filter((u) => u.role === "Estudiante").length;
    const tutores = users.filter((u) => u.role === "Tutor").length;
    const jurados = users.filter((u) => u.role === "Jurado").length;
    return { total, activos, pendientes, estudiantes, tutores, jurados };
  }, [users]);

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

  const selectClass =
    "h-10 px-3 pr-8 bg-surface border border-border-default rounded-lg text-[13.5px] font-medium text-text-strong appearance-none hover:border-[#b8bccb] focus:outline-none focus:border-primary focus:ring-[3px] focus:ring-[rgba(0,102,255,0.16)] w-full";
  const selectStyle = {
    backgroundImage:
      "url(\"data:image/svg+xml,%3Csvg width='10' height='6' xmlns='http://www.w3.org/2000/svg'%3E%3Cpath d='M1 1l4 4 4-4' stroke='%236b7589' stroke-width='1.5' fill='none' stroke-linecap='round'/%3E%3C/svg%3E\")",
    backgroundRepeat: "no-repeat" as const,
    backgroundPosition: "right 12px center",
  };

  return (
    <div className="flex flex-col">
      <div className="flex items-end justify-between gap-4 mb-4 flex-wrap">
        <div>
          <h2 className="text-xl font-bold text-text-strong tracking-tight leading-tight">Directorio de usuarios</h2>
          <p className="text-[13.5px] text-text-muted mt-1 max-w-[70ch]">
            Gestiona todos los usuarios registrados en el sistema. Puedes editar, activar o eliminar cuentas.
          </p>
        </div>
        <button
          onClick={() => { setEditing(null); setModalOpen(true); }}
          className="h-10 px-4 bg-primary text-white rounded-lg text-[13.5px] font-semibold inline-flex items-center gap-1.5 shadow-[0_1px_2px_rgba(0,102,255,0.25),inset_0_1px_0_rgba(255,255,255,0.12)] hover:bg-[#0052cc] transition-colors"
        >
          <Plus className="w-3.5 h-3.5" strokeWidth={2.5} />
          Nuevo usuario
        </button>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-3.5 mb-5">
        <div className="bg-gradient-to-br from-white via-[rgba(0,102,255,0.05)] to-[rgba(0,102,255,0.10)] border border-[rgba(0,102,255,0.18)] rounded-[14px] px-5 py-4.5 shadow-[0_1px_2px_rgba(15,23,42,0.03)]">
          <div className="flex items-center gap-1.5 text-[11.5px] font-semibold text-text-muted uppercase tracking-[0.04em] mb-2">
            <span className="w-[22px] h-[22px] rounded-md bg-[rgba(0,102,255,0.12)] text-primary flex items-center justify-center">
              <Users className="w-3.5 h-3.5" />
            </span>
            Total usuarios
          </div>
          <div className="text-[28px] font-extrabold text-text-strong tracking-tight leading-none">{stats.total}</div>
          <div className="text-xs text-text-muted mt-1.5">
            {stats.activos} activos · <b className="text-text-strong font-semibold">{stats.pendientes} pendientes</b>
          </div>
        </div>
        <div className="bg-gradient-to-br from-white via-[rgba(26,135,84,0.05)] to-[rgba(26,135,84,0.10)] border border-[rgba(26,135,84,0.18)] rounded-[14px] px-5 py-4.5 shadow-[0_1px_2px_rgba(15,23,42,0.03)]">
          <div className="flex items-center gap-1.5 text-[11.5px] font-semibold text-text-muted uppercase tracking-[0.04em] mb-2">
            <span className="w-[22px] h-[22px] rounded-md bg-[rgba(26,135,84,0.12)] text-success flex items-center justify-center">
              <GraduationCap className="w-3.5 h-3.5" />
            </span>
            Estudiantes
          </div>
          <div className="text-[28px] font-extrabold text-text-strong tracking-tight leading-none">{stats.estudiantes}</div>
          <div className="text-xs text-text-muted mt-1.5">Registrados</div>
        </div>
        <div className="bg-gradient-to-br from-white via-[rgba(255,107,53,0.05)] to-[rgba(255,107,53,0.10)] border border-[rgba(255,107,53,0.18)] rounded-[14px] px-5 py-4.5 shadow-[0_1px_2px_rgba(15,23,42,0.03)]">
          <div className="flex items-center gap-1.5 text-[11.5px] font-semibold text-text-muted uppercase tracking-[0.04em] mb-2">
            <span className="w-[22px] h-[22px] rounded-md bg-[rgba(255,107,53,0.14)] text-[#ff6b35] flex items-center justify-center">
              <UserCircle className="w-3.5 h-3.5" />
            </span>
            Tutores y Jurados
          </div>
          <div className="text-[28px] font-extrabold text-text-strong tracking-tight leading-none">{stats.tutores + stats.jurados}</div>
          <div className="text-xs text-text-muted mt-1.5">
            {stats.tutores} tutores · <b className="text-text-strong font-semibold">{stats.jurados} jurados</b>
          </div>
        </div>
      </div>

      <div className="bg-surface border border-border-subtle rounded-[14px] shadow-[0_1px_2px_rgba(15,23,42,0.03)] overflow-hidden">
        <div className="px-5 py-4 grid grid-cols-1 md:grid-cols-[1fr_200px_200px_auto] gap-3 border-b border-border-subtle items-center">
          <div className="relative">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-text-muted pointer-events-none" />
            <input
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              placeholder="Buscar por nombre, email o cédula..."
              className="w-full h-10 pl-10 pr-3 bg-surface border border-border-default rounded-lg text-[13.5px] font-medium text-text-strong hover:border-[#b8bccb] focus:outline-none focus:border-primary focus:ring-[3px] focus:ring-[rgba(0,102,255,0.16)]"
            />
          </div>
          <select
            value={roleFilter}
            onChange={(e) => setRoleFilter(e.target.value)}
            className={selectClass}
            style={selectStyle}
          >
            <option value="all">Todos los roles</option>
            <option value="Administrador">Administrador</option>
            <option value="Tutor">Tutor</option>
            <option value="Jurado">Jurado</option>
            <option value="Estudiante">Estudiante</option>
          </select>
          <select
            value={statusFilter}
            onChange={(e) => setStatusFilter(e.target.value)}
            className={selectClass}
            style={selectStyle}
          >
            <option value="all">Todos los estados</option>
            <option value="active">Activos</option>
            <option value="pending">Pendientes</option>
            <option value="rejected">Rechazados</option>
          </select>
          <button
            type="button"
            className="h-10 px-3.5 bg-surface border border-border-default rounded-lg text-[12.5px] font-semibold text-text-default inline-flex items-center gap-1.5 shadow-[0_1px_2px_rgba(15,23,42,0.03)] hover:bg-surface-sunken hover:text-text-strong hover:border-[#b8bccb] transition-colors"
            onClick={() => { setSearch(""); setRoleFilter("all"); setStatusFilter("all"); }}
          >
            <SlidersHorizontal className="w-3.5 h-3.5" />
            Filtros
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
          onResetPassword={(u) => setResetTarget(u)}
        />
      </div>

      <UserModal
        isOpen={modalOpen}
        onClose={() => { setModalOpen(false); setEditing(null); }}
        onSave={handleSave}
        initialData={editing}
      />
      {passwordModal && (
        <PasswordRevealModal isOpen={true} password={passwordModal} onClose={() => setPasswordModal(null)} />
      )}
      {resetTarget && (
        <ResetPasswordModal
          open={true}
          userId={resetTarget.id}
          userLabel={`${resetTarget.fullName} (${resetTarget.email})`}
          onClose={() => setResetTarget(null)}
        />
      )}
    </div>
  );
}
