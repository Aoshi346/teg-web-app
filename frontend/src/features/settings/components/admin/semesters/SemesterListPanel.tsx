"use client";
import React, { useEffect, useMemo, useState } from "react";
import { Calendar, Check, Plus } from "lucide-react";
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

  const stats = useMemo(() => {
    const active = semesters.find((s) => s.is_active);
    const future = semesters.filter((s) => !s.is_active && s.project_count === 0);
    const next = future[0] ?? null;
    return { active, total: semesters.length, future: future.length, next };
  }, [semesters]);

  return (
    <div className="flex flex-col">
      <div className="mb-4">
        <h2 className="text-xl font-bold text-text-strong tracking-tight leading-tight">Períodos académicos</h2>
        <p className="text-[13.5px] text-text-muted mt-1 max-w-[70ch]">
          Crea, activa o elimina semestres del programa de TEG.
        </p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-3.5 mb-5">
        <div className="bg-gradient-to-br from-white via-[rgba(26,135,84,0.05)] to-[rgba(26,135,84,0.10)] border border-[rgba(26,135,84,0.18)] rounded-[14px] px-5 py-4.5 shadow-[0_1px_2px_rgba(15,23,42,0.03)]">
          <div className="flex items-center gap-1.5 text-[11.5px] font-semibold text-text-muted uppercase tracking-[0.04em] mb-2">
            <span className="w-[22px] h-[22px] rounded-md bg-[rgba(26,135,84,0.12)] text-success flex items-center justify-center">
              <Check className="w-3.5 h-3.5" strokeWidth={2.5} />
            </span>
            Semestre activo
          </div>
          <div className="text-[28px] font-extrabold text-text-strong tracking-tight leading-none">
            {stats.active?.period ?? "—"}
          </div>
          <div className="text-xs text-text-muted mt-1.5">
            {stats.active?.label || "Sin semestre activo"}
          </div>
        </div>
        <div className="bg-gradient-to-br from-white via-[rgba(0,102,255,0.05)] to-[rgba(0,102,255,0.10)] border border-[rgba(0,102,255,0.18)] rounded-[14px] px-5 py-4.5 shadow-[0_1px_2px_rgba(15,23,42,0.03)]">
          <div className="flex items-center gap-1.5 text-[11.5px] font-semibold text-text-muted uppercase tracking-[0.04em] mb-2">
            <span className="w-[22px] h-[22px] rounded-md bg-[rgba(0,102,255,0.12)] text-primary flex items-center justify-center">
              <Calendar className="w-3.5 h-3.5" />
            </span>
            Total registrados
          </div>
          <div className="text-[28px] font-extrabold text-text-strong tracking-tight leading-none">{stats.total}</div>
          <div className="text-xs text-text-muted mt-1.5">
            {stats.active ? "1 activo" : "0 activos"} · <b className="text-text-strong font-semibold">{stats.future} futuros</b>
          </div>
        </div>
        <div className="bg-gradient-to-br from-white via-[rgba(255,107,53,0.05)] to-[rgba(255,107,53,0.10)] border border-[rgba(255,107,53,0.18)] rounded-[14px] px-5 py-4.5 shadow-[0_1px_2px_rgba(15,23,42,0.03)]">
          <div className="flex items-center gap-1.5 text-[11.5px] font-semibold text-text-muted uppercase tracking-[0.04em] mb-2">
            <span className="w-[22px] h-[22px] rounded-md bg-[rgba(255,107,53,0.14)] text-[#ff6b35] flex items-center justify-center">
              <Plus className="w-3.5 h-3.5" strokeWidth={2.5} />
            </span>
            Próximo
          </div>
          <div className="text-[28px] font-extrabold text-text-strong tracking-tight leading-none">
            {stats.next?.period ?? "—"}
          </div>
          <div className="text-xs text-text-muted mt-1.5">
            {stats.next?.label || "Sin semestres futuros"}
          </div>
        </div>
      </div>

      <SemesterCreateForm existing={semesters} onCreate={handleCreate} />

      <div className="bg-surface border border-border-subtle rounded-[14px] shadow-[0_1px_2px_rgba(15,23,42,0.03)] overflow-hidden mt-[18px]">
        <div className="px-5 py-3.5 border-b border-border-subtle flex items-center justify-between gap-3 flex-wrap">
          <span className="text-[14.5px] font-bold text-text-strong">Todos los semestres</span>
          <span className="inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-full bg-surface-sunken border border-border-subtle text-[11.5px] font-medium text-text-muted">
            {semesters.length} {semesters.length === 1 ? "registro" : "registros"} · orden descendente
          </span>
        </div>
        {loading ? (
          <div className="p-5 text-sm text-text-muted">Cargando...</div>
        ) : semesters.length === 0 ? (
          <div className="p-8 text-center text-sm text-text-muted">No hay semestres registrados.</div>
        ) : (
          semesters.map((s) => (
            <SemesterRow key={s.id} semester={s} onActivate={handleActivate} onDelete={handleDelete} />
          ))
        )}
      </div>
    </div>
  );
}
