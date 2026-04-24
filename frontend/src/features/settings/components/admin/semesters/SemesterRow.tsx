"use client";
import React from "react";
import type { Semester } from "@features/semesters/api/semesters";

interface SemesterRowProps {
  semester: Semester;
  onActivate: (id: number) => void;
  onDelete: (id: number) => void;
}

export function SemesterRow({ semester, onActivate, onDelete }: SemesterRowProps) {
  const { id, period, is_active, label, project_count } = semester;
  const blockedByProjects = project_count > 0;
  const canDelete = !is_active && !blockedByProjects;

  return (
    <div className={`px-4 py-3 flex items-center gap-4 border-b border-gray-100 ${is_active ? "bg-emerald-50" : ""}`}>
      <div className="flex-1">
        <div className="flex items-center gap-2 mb-1">
          <span className="font-semibold text-gray-900 text-sm">{period}</span>
          {is_active && (
            <span className="px-2 py-0.5 rounded-full bg-emerald-600 text-white text-xs font-semibold">ACTIVO</span>
          )}
        </div>
        <div className="text-xs text-gray-500">{label}</div>
      </div>
      <div className="text-right">
        <div className="text-xs uppercase tracking-wide text-gray-500">Proyectos</div>
        <div className={`font-semibold ${project_count === 0 ? "text-gray-400" : "text-gray-900"}`}>{project_count}</div>
      </div>
      <div className="flex gap-2">
        {is_active ? (
          <button disabled className="px-3 py-1.5 bg-emerald-100 text-emerald-800 rounded-md text-xs font-semibold cursor-default">
            ✓ Activo
          </button>
        ) : (
          <button onClick={() => onActivate(id)} className="px-3 py-1.5 bg-white text-blue-600 border border-blue-600 rounded-md text-xs font-semibold">
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
          className={`px-3 py-1.5 rounded-md text-xs font-semibold ${
            canDelete
              ? "bg-white text-red-700 border border-red-200"
              : "bg-gray-100 text-gray-400 border border-gray-200 cursor-not-allowed"
          }`}
        >
          Eliminar
        </button>
      </div>
    </div>
  );
}
