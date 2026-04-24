"use client";
import React, { useEffect, useState } from "react";
import { getSemesters, createSemester, deleteSemester, setActiveSemester, type Semester } from "@features/semesters/api/semesters";
import { SemesterCreateForm } from "./SemesterCreateForm";
import { SemesterRow } from "./SemesterRow";

export function SemesterListPanel() {
  const [semesters, setSemesters] = useState<Semester[]>([]);
  const [loading, setLoading] = useState(true);

  async function refresh() {
    setLoading(true);
    try {
      setSemesters(await getSemesters());
    } finally {
      setLoading(false);
    }
  }
  useEffect(() => { refresh(); }, []);

  async function handleCreate(data: { period: string; start_month: number; end_month: number }) {
    await createSemester(data);
    await refresh();
  }

  async function handleActivate(id: number) {
    await setActiveSemester(id);
    await refresh();
  }

  async function handleDelete(id: number) {
    if (!window.confirm("¿Eliminar este semestre? Esta acción no se puede deshacer.")) return;
    try {
      await deleteSemester(id);
      await refresh();
    } catch (e: unknown) {
      const message = (e as { detail?: string } | undefined)?.detail || "Error al eliminar semestre";
      window.alert(message);
    }
  }

  return (
    <div className="flex flex-col gap-4">
      <SemesterCreateForm existing={semesters} onCreate={handleCreate} />
      <div className="bg-white border border-gray-200 rounded-lg overflow-hidden">
        <div className="px-4 py-3 bg-gray-50 border-b border-gray-200 font-semibold text-sm text-gray-700">
          Todos los semestres ({semesters.length})
        </div>
        {loading ? (
          <div className="p-4 text-sm text-gray-500">Cargando...</div>
        ) : (
          semesters.map((s) => (
            <SemesterRow key={s.id} semester={s} onActivate={handleActivate} onDelete={handleDelete} />
          ))
        )}
      </div>
    </div>
  );
}
