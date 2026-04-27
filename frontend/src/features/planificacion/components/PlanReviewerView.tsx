"use client";

import React, { useState, useMemo } from "react";
import type { PresentationDay } from "../types/planificacion";
import { filterPresentationsForRole } from "../lib/filterForRole";
import UnifiedCalendar from "./UnifiedCalendar";
import DayDetailModal from "./DayDetailModal";
import PresentationFilter from "./PresentationFilter";
import PresentationTimeline from "./PresentationTimeline";
import { toDateStr } from "../lib/formatDate";
import { DEFAULT_FILTERS, applyPresentationFilters } from "../lib/applyPresentationFilters";
import type { PresentationFilters } from "../lib/applyPresentationFilters";

export type ReviewerKind = "tutor" | "jurado";

export interface PlanReviewerViewProps {
  days: PresentationDay[];
  loading: boolean;
  reviewerKind: ReviewerKind;
  viewerId: number;
  viewerName?: string;
}

export default function PlanReviewerView({
  days,
  loading,
  reviewerKind,
  viewerId,
}: PlanReviewerViewProps) {
  const [monthAnchor, setMonthAnchor] = useState(() => toDateStr(new Date()));
  const [modalDay, setModalDay] = useState<PresentationDay | null>(null);
  const [filters, setFilters] = useState<PresentationFilters>(DEFAULT_FILTERS);

  const roleDays = useMemo(
    () =>
      filterPresentationsForRole(
        days,
        reviewerKind === "tutor" ? "Tutor" : "Jurado",
        { viewerId }
      ),
    [days, reviewerKind, viewerId]
  );

  const filteredDays = useMemo(
    () => applyPresentationFilters(roleDays, filters),
    [roleDays, filters]
  );

  const filteredCount = useMemo(
    () => filteredDays.reduce((s, d) => s + d.presentations.length, 0),
    [filteredDays]
  );

  const mineDates = useMemo(
    () => new Set(roleDays.map((d) => d.date)),
    [roleDays]
  );

  const isTutor = reviewerKind === "tutor";
  const h1Text = isTutor ? "Mis defensas" : "Defensas asignadas";
  const eyebrowText = isTutor ? "Tus tutorías" : "Tus asignaciones";
  const lede = isTutor
    ? "Solo se muestran los días donde tienes una presentación tutoreada. Tu fila aparece resaltada."
    : "Presentaciones donde formas parte del tribunal. Solo se muestran tus asignaciones.";
  const emptyText = isTutor
    ? "Sin defensas tutoreadas en este período"
    : "Sin defensas asignadas en este período";

  const defenseCount = roleDays.reduce(
    (acc, d) => acc + d.presentations.length,
    0
  );

  const nextDate = useMemo(() => {
    const today = toDateStr(new Date());
    const upcoming = roleDays
      .filter((d) => d.date >= today)
      .sort((a, b) => a.date.localeCompare(b.date));
    return upcoming[0]?.date ?? "—";
  }, [roleDays]);

  const ptegCount = roleDays.reduce(
    (acc, d) =>
      acc + d.presentations.filter((p) => p.project_type === "proyecto").length,
    0
  );
  const tegCount = roleDays.reduce(
    (acc, d) =>
      acc + d.presentations.filter((p) => p.project_type === "tesis").length,
    0
  );

  return (
    <div>
      {/* ── Hero ── */}
      <section className="dashboard-hero-bg relative overflow-hidden rounded-2xl border border-border-subtle px-7 py-6 mb-6">
        <div className="relative z-10 flex flex-col gap-1.5">
          <p className="hero-eyebrow flex items-center gap-2 text-[10px] font-extrabold uppercase tracking-[0.14em] text-primary">
            <span
              aria-hidden
              className="inline-block h-[2px] w-6 rounded-full bg-gradient-to-r from-primary to-[var(--brand-orange)]"
            />
            {eyebrowText}
          </p>
          <h1 className="text-3xl font-extrabold leading-tight tracking-[-0.03em] text-text-strong md:text-[34px]">
            {h1Text}
          </h1>
          <p className="max-w-[480px] text-sm font-medium leading-relaxed text-text-muted mt-1">
            {lede}
          </p>
          {defenseCount > 0 && (
            <p className="seg-pill-summary">
              <span className="num">{defenseCount}</span> defensas próximas
              {" · "}
              {nextDate} la más cercana
              {" · "}
              <span className="num">{ptegCount}</span> PTEG
              {" · "}
              <span className="num">{tegCount}</span> TEG
            </p>
          )}
        </div>
      </section>

      {/* ── Filter bar ── */}
      {roleDays.length > 0 && (
        <div className="mb-6">
          <PresentationFilter
            days={roleDays}
            filters={filters}
            onChange={setFilters}
            resultCount={filteredCount}
          />
        </div>
      )}

      {/* ── Two-column body ── */}
      <div className="grid grid-cols-1 xl:grid-cols-[45%_1fr] gap-6 items-start">
        {/* Calendar */}
        <div className="bg-surface border border-border-subtle rounded-2xl p-5">
          <UnifiedCalendar
            days={roleDays}
            mode="view"
            monthAnchor={monthAnchor}
            onMonthChange={setMonthAnchor}
            onDayClick={(dateStr) => {
              const found = roleDays.find((d) => d.date === dateStr);
              if (found) setModalDay(found);
            }}
            allowCreate={false}
            mineDates={mineDates}
          />
        </div>

        {/* Presentation timeline or empty state */}
        {roleDays.length === 0 ? (
          <div className="empty-state text-center py-8 bg-surface border border-border-subtle rounded-2xl p-5">
            <p className="text-text-muted text-sm">{emptyText}</p>
          </div>
        ) : (
          <PresentationTimeline
            days={filteredDays}
            loading={loading}
            isAdmin={false}
            viewerId={viewerId}
            onPresentationClick={(_p, day) => setModalDay(day)}
            onDayMarkerClick={(day) => setModalDay(day)}
          />
        )}
      </div>

      {/* ── Day detail modal ── */}
      <DayDetailModal
        day={modalDay}
        isAdmin={false}
        onClose={() => setModalDay(null)}
      />
    </div>
  );
}
