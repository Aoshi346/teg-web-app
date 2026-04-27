"use client";

import React, { useEffect } from "react";
import type { PresentationDay } from "../types/planificacion";
import {
  formatDayNumeral,
  formatWeekday,
  formatMonthAbbr,
  formatMonth,
} from "../lib/formatDate";

export interface DayDetailModalProps {
  day: PresentationDay | null;
  isAdmin: boolean;
  onClose: () => void;
  onEditDay?: (day: PresentationDay) => void;
  onAddPresentation?: (day: PresentationDay) => void;
}

function addMinutes(time: string, minutes: number): string {
  const [h, m] = time.split(":").map(Number);
  const total = h * 60 + m + minutes;
  const nh = Math.floor(total / 60) % 24;
  const nm = total % 60;
  return `${String(nh).padStart(2, "0")}:${String(nm).padStart(2, "0")}`;
}

function minutesToHm(minutes: number): string {
  const h = Math.floor(minutes / 60);
  const m = minutes % 60;
  if (h === 0) return `${m}m`;
  if (m === 0) return `${h}h`;
  return `${h}h ${m}m`;
}

export default function DayDetailModal({
  day,
  isAdmin,
  onClose,
  onEditDay,
  onAddPresentation,
}: DayDetailModalProps): React.ReactElement | null {
  useEffect(() => {
    if (!day) return;
    function handleKey(e: KeyboardEvent) {
      if (e.key === "Escape") onClose();
    }
    document.addEventListener("keydown", handleKey);
    return () => document.removeEventListener("keydown", handleKey);
  }, [day, onClose]);

  if (!day) return null;

  const sorted = [...day.presentations].sort((a, b) =>
    a.start_time.localeCompare(b.start_time)
  );

  const N = sorted.length;
  const tegCount = sorted.filter((p) => p.project_type === "tesis").length;
  const ptegCount = sorted.filter((p) => p.project_type === "proyecto").length;

  const firstStart = N > 0 ? sorted[0].start_time : "—";
  const lastEnd =
    N > 0
      ? addMinutes(
          sorted[N - 1].start_time,
          sorted[N - 1].duration_minutes
        )
      : "—";

  // Compute span from first start to last end
  function timeToMinutes(t: string): number {
    const [h, m] = t.split(":").map(Number);
    return h * 60 + m;
  }
  const totalMinutes =
    N > 0
      ? timeToMinutes(lastEnd) - timeToMinutes(firstStart)
      : 0;

  const monthAbbr = formatMonthAbbr(day.date);
  const monthFull = formatMonth(day.date);
  const dayNum = formatDayNumeral(day.date);
  const weekday = formatWeekday(day.date);

  const overlayClick = (e: React.MouseEvent<HTMLDivElement>) => {
    if (e.target === e.currentTarget) onClose();
  };

  const bandTitle =
    N === 0
      ? "Sin presentaciones"
      : N === 1
      ? "1 presentación"
      : `${N} presentaciones`;

  return (
    <div className="modal-overlay" onClick={overlayClick}>
      <div
        className="modal"
        role="dialog"
        aria-modal="true"
        aria-labelledby="day-modal-title"
        onClick={(e) => e.stopPropagation()}
      >
        {/* Band */}
        <div className="modal-band read">
          <div className="band-numblk">
            <span className="m">{monthFull}</span>
            <span className="d">{dayNum}</span>
            <span className="dow">{weekday}</span>
          </div>
          <div className="band-body">
            <p className="band-eyebrow">Día de presentación</p>
            <h2 id="day-modal-title" className="band-title">
              {bandTitle}
            </h2>
            <span className="band-sub">
              {N > 0
                ? `${tegCount} TEG · ${ptegCount} PTEG · ${firstStart} a ${lastEnd}`
                : "Sin presentaciones programadas"}
            </span>
          </div>
          <button className="band-close" aria-label="Cerrar" onClick={onClose}>
            ×
          </button>
        </div>

        {/* Body */}
        <div className="modal-body">
          {N > 0 && (
            <div className="read-stats">
              <div className="read-stat">
                <span className="l">Inicio</span>
                <span className="v">{firstStart}</span>
                <span className="vs">Primera</span>
              </div>
              <div className="read-stat">
                <span className="l">Cierre</span>
                <span className="v">{lastEnd}</span>
                <span className="vs">Última</span>
              </div>
              <div className="read-stat">
                <span className="l">Duración total</span>
                <span className="v">{minutesToHm(totalMinutes)}</span>
                <span className="vs">{N} {N === 1 ? "turno" : "turnos"}</span>
              </div>
            </div>
          )}

          {/* Section 01 — Agenda */}
          <div className="section">
            <header className="section-h">
              <span className="section-num">01</span>
              <span className="section-title-h">Agenda del día</span>
              {N > 0 && (
                <span className="section-meta">
                  {N} {N === 1 ? "turno" : "turnos"}
                </span>
              )}
            </header>
            {sorted.length === 0 ? (
              <p style={{ fontSize: "12.5px", color: "var(--text-faint)", fontStyle: "italic" }}>
                Sin presentaciones programadas
              </p>
            ) : (
              sorted.map((p) => {
                const endTime = addMinutes(p.start_time, p.duration_minutes);
                const isTeG = p.project_type === "tesis";
                return (
                  <div className="prow" key={p.id}>
                    <div className="ptime">
                      <span className="h">{p.start_time}</span>
                      <span className="d">{p.duration_minutes} min</span>
                    </div>
                    <div>
                      <div className="ptitle">
                        <span className={`tdot ${isTeG ? "teg" : "pteg"}`} />
                        {p.project_title}
                        <span className={`spill ${isTeG ? "teg" : "pteg"}`}>
                          {isTeG ? "TEG" : "PTEG"}
                        </span>
                      </div>
                      <div className="pmeta">
                        <b>{p.student_name}</b>
                        {p.tutor_name && ` · Tutor ${p.tutor_name}`}
                        {p.jurado_names.length > 0 &&
                          ` · Jur ${p.jurado_names.join(", ")}`}
                      </div>
                    </div>
                  </div>
                );
              })
            )}
          </div>

          {/* Section 02 — Notas */}
          <div className="section">
            <header className="section-h">
              <span className="section-num">02</span>
              <span className="section-title-h">Notas del día</span>
            </header>
            <div className={`notes${day.notes ? "" : " empty"}`}>
              {day.notes || "Sin notas para este día."}
            </div>
          </div>
        </div>

        {/* Footer */}
        <div className="modal-foot">
          <span className="foot-meta">
            <svg
              viewBox="0 0 24 24"
              fill="none"
              stroke="currentColor"
              strokeWidth="2.4"
              strokeLinecap="round"
              strokeLinejoin="round"
            >
              <circle cx="12" cy="12" r="10" />
              <path d="M12 6v6l4 2" />
            </svg>
            {day.created_at
              ? `Creado ${day.created_at.slice(0, 10)}`
              : ""}
          </span>
          {isAdmin && (
            <div className="foot-actions">
              <button
                className="btn ghost"
                onClick={() => onEditDay?.(day)}
              >
                Editar día
              </button>
              <button
                className="btn primary"
                onClick={() => onAddPresentation?.(day)}
              >
                + Añadir presentación
              </button>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
