"use client";
import React, { useState, useMemo } from "react";
import { UserTableRow, type DirectoryUser } from "./UserTableRow";

interface UserTableProps {
  users: DirectoryUser[];
  search: string;
  roleFilter: string;
  statusFilter: string;
  onEdit: (u: DirectoryUser) => void;
  onDelete: (u: DirectoryUser) => void;
  onToggleStatus: (u: DirectoryUser, next: "active" | "rejected") => void;
  pageSize?: number;
}

type SortKey = "fullName" | "role" | "status";
type SortDir = "asc" | "desc";

export function UserTable({ users, search, roleFilter, statusFilter, onEdit, onDelete, onToggleStatus, pageSize = 8 }: UserTableProps) {
  const [sortKey, setSortKey] = useState<SortKey>("fullName");
  const [sortDir, setSortDir] = useState<SortDir>("asc");
  const [page, setPage] = useState(1);

  const filtered = useMemo(() => {
    const s = search.toLowerCase();
    return users.filter((u) => {
      const matches = !s
        || u.fullName.toLowerCase().includes(s)
        || u.email.toLowerCase().includes(s)
        || (u.cedula || "").includes(s);
      const roleOk = roleFilter === "all" || u.role === roleFilter;
      const statusOk = statusFilter === "all" || u.status === statusFilter;
      return matches && roleOk && statusOk;
    });
  }, [users, search, roleFilter, statusFilter]);

  const sorted = useMemo(() => {
    return [...filtered].sort((a, b) => {
      const av = String(a[sortKey] ?? "");
      const bv = String(b[sortKey] ?? "");
      return sortDir === "asc" ? av.localeCompare(bv) : bv.localeCompare(av);
    });
  }, [filtered, sortKey, sortDir]);

  const total = sorted.length;
  const pageCount = Math.max(1, Math.ceil(total / pageSize));
  const view = sorted.slice((page - 1) * pageSize, page * pageSize);

  function headerClick(k: SortKey) {
    if (k === sortKey) setSortDir(sortDir === "asc" ? "desc" : "asc");
    else { setSortKey(k); setSortDir("asc"); }
  }

  function headerLabel(k: SortKey, label: string) {
    const arrow = sortKey === k ? (sortDir === "asc" ? " ↑" : " ↓") : " ↕";
    return <button onClick={() => headerClick(k)} className="font-semibold text-gray-700">{label}{arrow}</button>;
  }

  return (
    <div className="bg-white border border-gray-200 rounded-lg overflow-hidden">
      <table className="w-full border-collapse text-sm">
        <thead>
          <tr className="bg-gray-50 border-b border-gray-200">
            <th className="px-4 py-3 text-left">{headerLabel("fullName", "Usuario")}</th>
            <th className="px-4 py-3 text-left">{headerLabel("role", "Rol")}</th>
            <th className="px-4 py-3 text-left">Cédula</th>
            <th className="px-4 py-3 text-left">Semestre</th>
            <th className="px-4 py-3 text-left">{headerLabel("status", "Estado")}</th>
            <th className="px-4 py-3 text-center">Acciones</th>
          </tr>
        </thead>
        <tbody>
          {view.length === 0 ? (
            <tr>
              <td colSpan={6} className="px-4 py-8 text-center text-gray-500">
                No se encontraron usuarios con los filtros aplicados.
              </td>
            </tr>
          ) : (
            view.map((u) => (
              <UserTableRow key={u.id} user={u} onEdit={onEdit} onDelete={onDelete} onToggleStatus={onToggleStatus} />
            ))
          )}
        </tbody>
      </table>
      {total > 0 && (
        <div className="px-4 py-2 flex justify-between items-center border-t border-gray-100 bg-gray-50">
          <div className="text-xs text-gray-500">Mostrando {(page - 1) * pageSize + 1}–{Math.min(page * pageSize, total)} de {total} usuarios</div>
          <div className="flex gap-1">
            <button onClick={() => setPage(Math.max(1, page - 1))} disabled={page === 1} className="px-3 py-1 border border-gray-300 rounded text-xs bg-white disabled:opacity-40">← Anterior</button>
            <span className="px-3 py-1 text-xs">{page} / {pageCount}</span>
            <button onClick={() => setPage(Math.min(pageCount, page + 1))} disabled={page === pageCount} className="px-3 py-1 border border-gray-300 rounded text-xs bg-white disabled:opacity-40">Siguiente →</button>
          </div>
        </div>
      )}
    </div>
  );
}
