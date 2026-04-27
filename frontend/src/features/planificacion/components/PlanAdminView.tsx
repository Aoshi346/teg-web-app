"use client";

import React, { useState, useMemo } from "react";
import type { PresentationDay, Presentation, PresentationCreate } from "../types/planificacion";
import { useDateSelection } from "../hooks/useDateSelection";
import UnifiedCalendar from "./UnifiedCalendar";
import DayCard from "./DayCard";
import DayDetailModal from "./DayDetailModal";
import EditDayModal from "./EditDayModal";
import PresentationFormModal from "./PresentationFormModal";
import PresentationFilter from "./PresentationFilter";
import PresentationTimeline from "./PresentationTimeline";
import { toDateStr, dateRange, formatWeekday, formatDayNumeral, formatMonth } from "../lib/formatDate";
import { DEFAULT_FILTERS, applyPresentationFilters } from "../lib/applyPresentationFilters";
import type { PresentationFilters } from "../lib/applyPresentationFilters";

export interface PlanAdminViewProps {
  days: PresentationDay[];
  loading: boolean;
  onRefresh: () => Promise<void> | void;
}

export default function PlanAdminView({ days, loading, onRefresh }: PlanAdminViewProps) {
  const { mode: selectionMode, setMode: setSelectionMode, selected, toggleDay, setRange, clearAll } = useDateSelection();
  const [calendarMode, setCalendarMode] = useState<"view" | "create">("view");
  const [monthAnchor, setMonthAnchor] = useState(() => toDateStr(new Date()));
  const [modalDay, setModalDay] = useState<PresentationDay | null>(null);
  const [editDayTarget, setEditDayTarget] = useState<PresentationDay | null>(null);
  const [formOpen, setFormOpen] = useState(false);
  const [formDayId, setFormDayId] = useState<number>(0);
  const [formEditTarget, setFormEditTarget] = useState<Presentation | null>(null);
  const [filters, setFilters] = useState<PresentationFilters>(DEFAULT_FILTERS);

  // Bulk-select state for day management section
  const [bulkMode, setBulkMode] = useState(false);
  const [bulkSelected, setBulkSelected] = useState<Set<number>>(new Set());

  const totalPresentations = useMemo(
    () => days.reduce((acc, d) => acc + d.presentations.length, 0),
    [days]
  );

  const filteredDays = useMemo(
    () => applyPresentationFilters(days, filters),
    [days, filters]
  );

  const filteredCount = useMemo(
    () => filteredDays.reduce((s, d) => s + d.presentations.length, 0),
    [filteredDays]
  );

  const defensesThisWeek = useMemo(() => {
    const now = new Date();
    const startOfWeek = new Date(now);
    startOfWeek.setDate(now.getDate() - now.getDay());
    const endOfWeek = new Date(startOfWeek);
    endOfWeek.setDate(startOfWeek.getDate() + 6);

    const startStr = toDateStr(startOfWeek);
    const endStr = toDateStr(endOfWeek);

    return days
      .filter((d) => d.date >= startStr && d.date <= endStr)
      .reduce((acc, d) => acc + d.presentations.length, 0);
  }, [days]);

  function handleDayCardClick(day: PresentationDay) {
    setModalDay(day);
  }

  function handleCalendarDayClick(dateStr: string) {
    const found = days.find((d) => d.date === dateStr);
    if (found) setModalDay(found);
  }

  function handleCreateDays(dates: string[]) {
    import("../api/planificacionService").then(({ bulkCreateDays }) => {
      bulkCreateDays({ dates, semester: 1 }).then(() => {
        clearAll();
        onRefresh();
      });
    });
  }

  async function handleDeleteDay(day: PresentationDay) {
    const confirmed = window.confirm(
      `¿Eliminar el día ${day.date}? Esta acción eliminará también sus presentaciones.`
    );
    if (!confirmed) return;
    const { deleteDay } = await import("../api/planificacionService");
    await deleteDay(day.id);
    await onRefresh();
  }

  function handleOpenAddPresentation(day: PresentationDay) {
    setFormDayId(day.id);
    setFormEditTarget(null);
    setFormOpen(true);
    setModalDay(null);
  }

  function handleOpenEditDay(day: PresentationDay) {
    setEditDayTarget(day);
    setModalDay(null);
  }

  async function handleSavePresentation(
    dayId: number,
    payload: PresentationCreate,
    editId?: number
  ) {
    const { createPresentation, updatePresentation } = await import(
      "../api/planificacionService"
    );
    if (editId !== undefined) {
      await updatePresentation(editId, payload);
    } else {
      await createPresentation(dayId, payload);
    }
    await onRefresh();
  }

  const handleBulkSelect = (day: PresentationDay, sel: boolean) => {
    setBulkSelected((prev) => {
      const next = new Set(prev);
      if (sel) next.add(day.id);
      else next.delete(day.id);
      return next;
    });
  };

  const handleBulkDelete = async () => {
    const ids = [...bulkSelected];
    if (ids.length === 0) return;
    const msg =
      ids.length === 1
        ? "¿Eliminar el día seleccionado?"
        : `¿Eliminar los ${ids.length} días seleccionados? Esto eliminará todas sus presentaciones.`;
    if (!window.confirm(msg)) return;
    const { deleteDay } = await import("../api/planificacionService");
    await Promise.all(ids.map((id) => deleteDay(id)));
    setBulkSelected(new Set());
    setBulkMode(false);
    await onRefresh();
  };

  return (
    <div>
      {/* ── Hero ── */}
      <section className="dashboard-hero-bg relative overflow-hidden rounded-2xl border border-border-subtle px-7 py-6 mb-6">
        <div className="relative z-10 flex flex-col gap-1.5">
          <p className="hero-eyebrow flex items-center gap-2 text-[10px] font-extrabold uppercase tracking-[0.14em] text-primary">
            <span aria-hidden className="inline-block h-[2px] w-6 rounded-full bg-gradient-to-r from-primary to-[var(--brand-orange)]" />
            Administración
          </p>
          <h1 className="text-3xl font-extrabold leading-tight tracking-[-0.03em] text-text-strong md:text-[34px]">
            Planificación de presentaciones
          </h1>
          <p className="max-w-[480px] text-sm font-medium leading-relaxed text-text-muted mt-1">
            Calendario operativo de defensas y revisiones del período activo. Crea días, asigna horarios y compone el equipo evaluador.
          </p>
          <p className="seg-pill-summary">
            <span className="num">{days.length}</span> días planificados
            {" · "}
            <span className="num">{totalPresentations}</span> presentaciones
            {" · "}
            <span className="num">{defensesThisWeek}</span> defensas esta semana
          </p>
        </div>
      </section>

      {/* ── Filter bar ── */}
      <div className="mb-6">
        <PresentationFilter
          days={days}
          filters={filters}
          onChange={setFilters}
          resultCount={filteredCount}
        />
      </div>

      {/* ── Two-column main area ── */}
      <div className="grid grid-cols-1 xl:grid-cols-[minmax(360px,420px)_1fr] gap-6 mb-8 items-start">
        {/* Calendar */}
        <div className="bg-surface border border-border-subtle rounded-2xl p-5">
          <UnifiedCalendar
            days={days}
            mode={calendarMode}
            monthAnchor={monthAnchor}
            onMonthChange={setMonthAnchor}
            onDayClick={handleCalendarDayClick}
            allowCreate={true}
            onModeChange={setCalendarMode}
            selectionMode={selectionMode}
            onSelectionModeChange={setSelectionMode}
            selectedDates={selected}
            onToggleDate={toggleDay}
            onRangeSelect={(start, end) => setRange(dateRange(start, end))}
            onCreate={handleCreateDays}
            onClear={clearAll}
          />
        </div>

        {/* Presentations timeline */}
        <PresentationTimeline
          days={filteredDays}
          loading={loading}
          isAdmin
          onPresentationClick={(_p, day) => setModalDay(day)}
          onEditPresentation={(p, day) => {
            setFormDayId(day.id);
            setFormEditTarget(p);
            setFormOpen(true);
          }}
          onDeletePresentation={async (p) => {
            const { deletePresentation } = await import("../api/planificacionService");
            await deletePresentation(p.id);
            await onRefresh();
          }}
          onDayMarkerClick={(day) => setModalDay(day)}
        />
      </div>

      {/* ── Day management section ── */}
      <div className="bg-surface border border-border-subtle rounded-2xl p-5 mb-8">
        <div className="flex items-end justify-between gap-3 flex-wrap mb-4">
          <div>
            <h2 className="text-[10px] font-extrabold uppercase tracking-[0.16em] text-text-faint mb-1">
              Días creados
            </h2>
            <p className="text-lg font-extrabold leading-tight tracking-[-0.01em] text-text-strong mt-0">
              {days.length} días en el período
            </p>
            <p className="text-[12.5px] font-medium leading-relaxed text-text-muted mt-0.5">
              {bulkMode ? "Selecciona los días a eliminar." : "Click en una tarjeta abre el detalle del día."}
            </p>
          </div>
          <div className="flex items-center gap-2 flex-wrap">
            {bulkMode && bulkSelected.size > 0 && (
              <button
                onClick={handleBulkDelete}
                className="text-sm font-semibold text-white bg-red-600 border border-red-600 rounded-xl px-4 py-2"
              >
                Eliminar {bulkSelected.size} {bulkSelected.size === 1 ? "día" : "días"}
              </button>
            )}
            <button
              onClick={() => {
                setBulkMode((prev) => !prev);
                setBulkSelected(new Set());
              }}
              className="text-sm font-semibold text-text-muted border border-border-subtle rounded-xl px-4 py-2"
            >
              {bulkMode ? "Cancelar selección" : "Seleccionar días"}
            </button>
          </div>
        </div>
        {days.length === 0 ? (
          <p className="text-text-muted text-sm text-center py-6">
            Sin días creados todavía.
          </p>
        ) : (
          <div className="overflow-y-auto pr-1" style={{ maxHeight: "480px" }}>
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
              {days.map((day) => (
                <DayCard
                  key={day.id}
                  day={day}
                  onClick={bulkMode ? undefined : handleDayCardClick}
                  onDelete={bulkMode ? undefined : handleDeleteDay}
                  selectable={bulkMode}
                  selected={bulkSelected.has(day.id)}
                  onSelect={handleBulkSelect}
                />
              ))}
            </div>
          </div>
        )}
      </div>

      {/* ── Day detail modal ── */}
      <DayDetailModal
        day={modalDay}
        isAdmin={true}
        onClose={() => setModalDay(null)}
        onEditDay={handleOpenEditDay}
        onAddPresentation={handleOpenAddPresentation}
      />

      {/* ── Edit day modal ── */}
      <EditDayModal
        day={editDayTarget}
        onClose={() => setEditDayTarget(null)}
        onSaved={async () => {
          await onRefresh();
          setEditDayTarget(null);
        }}
      />

      {/* ── Presentation form modal ── */}
      {(() => {
        const formDay = days.find((d) => d.id === formDayId);
        const dayDate = formDay
          ? `${formatWeekday(formDay.date)} ${formatDayNumeral(formDay.date)} de ${formatMonth(formDay.date)}`
          : "";
        return (
          <PresentationFormModal
            isOpen={formOpen}
            dayId={formDayId}
            editTarget={formEditTarget}
            dayDate={dayDate}
            onClose={() => setFormOpen(false)}
            onSave={handleSavePresentation}
          />
        );
      })()}
    </div>
  );
}
