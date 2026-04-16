"use client";

import React, { useState, useMemo, useCallback } from "react";
import { getUserRole } from "@features/auth/api/clientAuth";
import { usePlanificacion } from "../hooks/usePlanificacion";
import { useDateSelection } from "../hooks/useDateSelection";
import { Presentation, PresentationDay, PresentationCreate } from "../types/planificacion";
import WeekCalendar from "./WeekCalendar";
import DayCard from "./DayCard";
import EmptyDayState from "./EmptyDayState";
import PresentationFormModal from "./PresentationFormModal";
import ScheduleOverviewCalendar from "./ScheduleOverviewCalendar";

export default function PlanificacionView() {
  const role = useMemo(() => getUserRole(), []);
  const isAdmin = role === "Administrador";

  const { days, loading, refresh } = usePlanificacion();
  const { mode, setMode, selected, rangeStart, toggleDay, clearAll } = useDateSelection();

  const [modalOpen, setModalOpen] = useState(false);
  const [modalDayId, setModalDayId] = useState<number>(0);
  const [editTarget, setEditTarget] = useState<Presentation | null>(null);

  const handleCreateDays = useCallback(async () => {
    if (selected.size === 0) return;
    try {
      const { bulkCreateDays } = await import("../api/planificacionService");
      await bulkCreateDays({
        dates: Array.from(selected),
        semester: 1,
      });
      clearAll();
      await refresh();
    } catch (err) {
      console.error("Error creating days", err);
    }
  }, [selected, clearAll, refresh]);

  const handleAddPresentation = useCallback((dayId: number) => {
    setModalDayId(dayId);
    setEditTarget(null);
    setModalOpen(true);
  }, []);

  const handleEditPresentation = useCallback((presentation: Presentation) => {
    setModalDayId(presentation.day);
    setEditTarget(presentation);
    setModalOpen(true);
  }, []);

  const handleDeletePresentation = useCallback(async (presentation: Presentation) => {
    if (!confirm(`¿Eliminar la presentación "${presentation.project_title}"?`)) return;
    try {
      const { deletePresentation } = await import("../api/planificacionService");
      await deletePresentation(presentation.id);
      await refresh();
    } catch (err) {
      console.error("Error deleting presentation", err);
    }
  }, [refresh]);

  const handleDeleteDay = useCallback(async (day: PresentationDay) => {
    if (!confirm(`¿Eliminar el día ${day.date}? Esto eliminará todas sus presentaciones.`)) return;
    try {
      const { deleteDay } = await import("../api/planificacionService");
      await deleteDay(day.id);
      await refresh();
    } catch (err) {
      console.error("Error deleting day", err);
    }
  }, [refresh]);

  const handleSavePresentation = useCallback(
    async (dayId: number, payload: PresentationCreate, editId?: number) => {
      const { createPresentation, updatePresentation } = await import("../api/planificacionService");
      if (editId !== undefined) {
        await updatePresentation(editId, payload);
      } else {
        await createPresentation(dayId, payload);
      }
      await refresh();
    },
    [refresh],
  );

  return (
    <>
      <main className="flex-1 p-3 sm:p-4 md:p-6 lg:p-8 overflow-y-auto bg-gray-50">
        <div className="max-w-7xl mx-auto">
          {/* Title row */}
          <div className="mb-8 flex flex-col lg:flex-row lg:items-end justify-between gap-6">
            <div className="space-y-1">
              <h2 className="text-3xl font-extrabold text-gray-900 tracking-tight">
                Planificación de presentaciones
              </h2>
              <p className="text-gray-500 font-medium">
                Programa los días y horarios de las presentaciones del período.
              </p>
            </div>
          </div>

          {/* Schedule Overview Calendar — all roles */}
          <ScheduleOverviewCalendar days={days} />

          {/* Admin-only: mode toggle + editor calendar + day cards in 12-col grid */}
          {isAdmin && (
            <>
              {/* Mode toggle */}
              <div className="bg-white/60 backdrop-blur-xl rounded-[2rem] border border-gray-200/60 shadow-xl shadow-slate-200/40 p-5 sm:p-6 mb-8">
                <div className="flex flex-col sm:flex-row sm:items-center gap-4">
                  <div className="flex-1 min-w-0">
                    <p className="text-sm font-semibold text-gray-700 mb-1">
                      Modo de selección
                    </p>
                    <p className="text-xs text-gray-500">
                      {mode === "rango"
                        ? "Selecciona un rango de fechas continuo."
                        : "Selecciona días individuales."}
                    </p>
                  </div>
                  <div
                    role="radiogroup"
                    aria-label="Modo de selección"
                    className="flex items-center bg-gray-100/80 p-1 rounded-xl self-start sm:self-auto"
                  >
                    {(["rango", "individual"] as const).map((m) => (
                      <button
                        key={m}
                        role="radio"
                        aria-checked={mode === m}
                        onClick={() => setMode(m)}
                        className={`px-5 py-2 text-sm font-semibold rounded-lg transition-all duration-200 capitalize ${
                          mode === m
                            ? "bg-white text-gray-900 shadow-sm ring-1 ring-black/5"
                            : "text-gray-500 hover:text-gray-900 hover:bg-white/50"
                        }`}
                      >
                        {m === "rango" ? "Rango" : "Individual"}
                      </button>
                    ))}
                  </div>
                </div>
              </div>

              {/* 12-col grid: editor calendar + day cards */}
              <div className="grid grid-cols-1 xl:grid-cols-12 gap-8">
                {/* Editor calendar */}
                <div className="xl:col-span-7">
                  <WeekCalendar
                    mode={mode}
                    selected={selected}
                    existingDays={days}
                    rangeStart={rangeStart}
                    isAdmin={isAdmin}
                    onToggleDay={toggleDay}
                    onCreateDays={handleCreateDays}
                  />
                </div>

                {/* Day cards */}
                <div className="xl:col-span-5">
                  {loading ? (
                    <div className="flex justify-center py-20">
                      <div className="w-8 h-8 rounded-full border-4 border-slate-200 border-t-blue-600 animate-spin" />
                    </div>
                  ) : days.length === 0 ? (
                    <EmptyDayState isAdmin={isAdmin} />
                  ) : (
                    <div className="space-y-6">
                      {days.map((day, idx) => (
                        <DayCard
                          key={day.id}
                          day={day}
                          isAdmin={isAdmin}
                          onAddPresentation={handleAddPresentation}
                          onEditPresentation={handleEditPresentation}
                          onDeletePresentation={handleDeletePresentation}
                          onDeleteDay={handleDeleteDay}
                          style={{
                            animationDelay: `${Math.min(idx, 5) * 60}ms`,
                          }}
                        />
                      ))}
                    </div>
                  )}
                </div>
              </div>
            </>
          )}

          {/* Non-admin: day cards full width */}
          {!isAdmin && (
            <div>
              {loading ? (
                <div className="flex justify-center py-20">
                  <div className="w-8 h-8 rounded-full border-4 border-slate-200 border-t-blue-600 animate-spin" />
                </div>
              ) : days.length === 0 ? (
                <EmptyDayState isAdmin={false} />
              ) : (
                <div className="space-y-6">
                  {days.map((day, idx) => (
                    <DayCard
                      key={day.id}
                      day={day}
                      isAdmin={false}
                      style={{
                        animationDelay: `${Math.min(idx, 5) * 60}ms`,
                      }}
                    />
                  ))}
                </div>
              )}
            </div>
          )}
        </div>
      </main>

      {/* Admin: presentation form modal */}
      {isAdmin && (
        <PresentationFormModal
          isOpen={modalOpen}
          dayId={modalDayId}
          editTarget={editTarget}
          onClose={() => setModalOpen(false)}
          onSave={handleSavePresentation}
        />
      )}
    </>
  );
}
