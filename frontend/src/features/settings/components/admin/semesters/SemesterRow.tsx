"use client";
import React from "react";
import { Calendar, Clock, Check } from "lucide-react";
import type { Semester } from "@features/semesters/api/semesters";

interface SemesterRowProps {
  semester: Semester;
  onActivate: (id: number) => void;
  onDelete: (id: number) => void;
}

export function SemesterRow({ semester, onActivate, onDelete }: SemesterRowProps) {
  const { id, period, is_active, label, project_count, created_at } = semester;
  const blockedByProjects = project_count > 0;
  const canDelete = !is_active && !blockedByProjects;

  const createdLabel = created_at
    ? new Date(created_at).toLocaleDateString("es-VE", { day: "2-digit", month: "short", year: "numeric" })
    : null;

  return (
    <div
      className={`px-5 py-4 grid grid-cols-1 md:grid-cols-[minmax(0,1fr)_110px_220px] gap-5 items-center border-b border-border-subtle last:border-b-0 transition-colors hover:bg-[rgba(0,102,255,0.025)] ${
        is_active ? "bg-gradient-to-r from-success-soft/60 via-transparent to-transparent" : ""
      }`}
    >
      <div>
        <div className="flex items-center gap-2.5 mb-1.5">
          <span
            className={`text-xs font-bold px-2.5 py-0.5 rounded-md font-mono tracking-[0.02em] border ${
              is_active
                ? "bg-[rgba(0,102,255,0.08)] border-[rgba(0,102,255,0.18)] text-primary"
                : "bg-surface-sunken border-border-subtle text-text-strong"
            }`}
          >
            {period}
          </span>
          {is_active && (
            <span className="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full bg-success-soft text-success border border-[rgba(26,135,84,0.2)] text-[11px] font-bold tracking-[0.02em]">
              <span className="w-1.5 h-1.5 rounded-full bg-success" />
              Activo
            </span>
          )}
        </div>
        <div className="text-[15px] font-bold text-text-strong tracking-tight">{label || "—"}</div>
        <div className="flex gap-4 mt-1.5 text-xs text-text-muted flex-wrap">
          {createdLabel && (
            <span className="inline-flex items-center gap-1">
              <Clock className="w-3 h-3 opacity-80" />
              Creado {createdLabel}
            </span>
          )}
          {is_active && (
            <span className="inline-flex items-center gap-1">
              <Calendar className="w-3 h-3 opacity-80" />
              Semestre activo
            </span>
          )}
        </div>
      </div>
      <div className="text-right">
        <div className={`text-2xl font-extrabold leading-none tracking-tight ${project_count === 0 ? "text-text-muted font-semibold" : "text-text-strong"}`}>
          {project_count}
        </div>
        <div className="text-[11px] font-semibold text-text-muted mt-1 uppercase tracking-[0.04em]">Proyectos</div>
      </div>
      <div className="flex gap-1.5 justify-end">
        {is_active ? (
          <button
            disabled
            className="h-8 px-3 rounded-[7px] text-[12.5px] font-semibold text-success border border-[rgba(26,135,84,0.3)] bg-success-soft cursor-default inline-flex items-center gap-1.5"
          >
            <Check className="w-3 h-3" strokeWidth={3} />
            ✓ Activo
          </button>
        ) : (
          <button
            onClick={() => onActivate(id)}
            className="h-8 px-3 bg-surface border border-border-default rounded-[7px] text-[12.5px] font-semibold text-text-default shadow-[0_1px_2px_rgba(15,23,42,0.03)] hover:bg-surface-sunken hover:text-text-strong hover:border-[#b8bccb] transition-colors"
          >
            Activar
          </button>
        )}
        <button
          onClick={() => canDelete && onDelete(id)}
          disabled={!canDelete}
          title={
            is_active
              ? "No se puede eliminar un semestre activo"
              : blockedByProjects
              ? `No se puede eliminar: ${project_count} proyectos asignados`
              : undefined
          }
          className={`h-8 px-3 rounded-[7px] text-[12.5px] font-semibold transition-colors ${
            canDelete
              ? "bg-surface border border-border-default text-text-default hover:bg-destructive-soft hover:text-destructive hover:border-[rgba(209,56,56,0.4)]"
              : "bg-surface border border-border-subtle text-text-muted opacity-50 cursor-not-allowed"
          }`}
        >
          Eliminar
        </button>
      </div>
    </div>
  );
}
