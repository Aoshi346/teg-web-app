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
    const arrow = sortKey === k ? (sortDir === "asc" ? " ↑" : " ↓") : "";
    return (
      <button onClick={() => headerClick(k)} className="text-[11px] font-bold text-text-muted uppercase tracking-[0.06em] hover:text-text-default transition-colors">
        {label}{arrow}
      </button>
    );
  }

  const thClass = "px-4 py-3 text-left text-[11px] font-bold text-text-muted uppercase tracking-[0.06em] border-b border-border-subtle bg-surface-muted";

  return (
    <div>
      <div className="overflow-x-auto">
      <table className="w-full border-collapse min-w-[640px]">
        <thead>
          <tr>
            <th className={thClass}>{headerLabel("fullName", "Usuario")}</th>
            <th className={thClass}>{headerLabel("role", "Rol")}</th>
            <th className={thClass}>Cédula</th>
            <th className={thClass}>Semestre</th>
            <th className={thClass}>{headerLabel("status", "Estado")}</th>
            <th className={`${thClass} text-right`}></th>
          </tr>
        </thead>
        <tbody>
          {view.length === 0 ? (
            <tr>
              <td colSpan={6} className="px-4 py-10 text-center text-sm text-text-muted">
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
      </div>
      {total > 0 && (
        <div className="px-5 py-3 flex justify-between items-center border-t border-border-subtle bg-surface-muted flex-wrap gap-2">
          <div className="text-xs text-text-muted">
            Mostrando {(page - 1) * pageSize + 1}–{Math.min(page * pageSize, total)} de <b className="text-text-strong font-semibold">{total} usuarios</b>
          </div>
          <div className="flex gap-1 items-center">
            <button
              onClick={() => setPage(Math.max(1, page - 1))}
              disabled={page === 1}
              className="min-w-[30px] h-[30px] px-2 border border-border-subtle bg-surface rounded-[7px] text-xs font-semibold text-text-default hover:bg-surface-sunken disabled:opacity-40 disabled:cursor-not-allowed"
              aria-label="Anterior"
            >
              ←
            </button>
            {Array.from({ length: pageCount }, (_, i) => i + 1).slice(0, 6).map((n) => (
              <button
                key={n}
                onClick={() => setPage(n)}
                className={`min-w-[30px] h-[30px] px-2 rounded-[7px] text-xs font-semibold border ${
                  page === n
                    ? "bg-primary border-primary text-white"
                    : "bg-surface border-border-subtle text-text-default hover:bg-surface-sunken"
                }`}
              >
                {n}
              </button>
            ))}
            <button
              onClick={() => setPage(Math.min(pageCount, page + 1))}
              disabled={page === pageCount}
              className="min-w-[30px] h-[30px] px-2 border border-border-subtle bg-surface rounded-[7px] text-xs font-semibold text-text-default hover:bg-surface-sunken disabled:opacity-40 disabled:cursor-not-allowed"
              aria-label="Siguiente"
            >
              →
            </button>
          </div>
        </div>
      )}
    </div>
  );
}
