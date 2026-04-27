"use client";

import React from "react";
import type { PresentationDay, Presentation } from "../types/planificacion";
import PresentationRow from "./PresentationRow";
import { formatDayNumeral, formatMonth, formatMonthAbbr, toDateStr } from "../lib/formatDate";

export interface PresentationTimelineProps {
  days: PresentationDay[];
  loading?: boolean;
  isAdmin?: boolean;
  viewerId?: number;
  onPresentationClick?: (p: Presentation, day: PresentationDay) => void;
  onEditPresentation?: (p: Presentation, day: PresentationDay) => void;
  onDeletePresentation?: (p: Presentation, day: PresentationDay) => void;
  onDayMarkerClick?: (day: PresentationDay) => void;
  todayOverride?: string;
}

/**
 * Determina la modalidad dominante de un día.
 * Si hay más PTEG que TEG → "pteg". Si hay más TEG → "teg". Empate/vacío → null.
 */
function dominantModality(day: PresentationDay): "pteg" | "teg" | null {
  let pteg = 0;
  let teg = 0;
  for (const p of day.presentations) {
    if (p.project_type === "proyecto") pteg++;
    else teg++;
  }
  if (pteg > teg) return "pteg";
  if (teg > pteg) return "teg";
  return null;
}

/**
 * Retorna la abreviatura del día de la semana en español (3 chars, sin puntuación).
 * Ej: "Lun", "Mar", "Mié", "Jue", "Vie", "Sáb", "Dom"
 */
function formatWeekdayAbbr(dateStr: string): string {
  const [y, m, d] = dateStr.split("-").map(Number);
  const date = new Date(y, m - 1, d);
  const full = date.toLocaleDateString("es-VE", { weekday: "short" });
  const stripped = full.replace(".", "").trim();
  return stripped.charAt(0).toUpperCase() + stripped.slice(1);
}

export default function PresentationTimeline({
  days,
  loading = false,
  isAdmin = false,
  viewerId,
  onPresentationClick,
  onEditPresentation,
  onDeletePresentation,
  onDayMarkerClick,
  todayOverride,
}: PresentationTimelineProps) {
  const todayStr = todayOverride ?? toDateStr(new Date());

  const totalCount = days.reduce((s, d) => s + d.presentations.length, 0);

  // Sort ascending by date
  const sortedDays = [...days].sort((a, b) => a.date.localeCompare(b.date));

  return (
    <div className="pt-card">
      <div className="pt-head">
        <h2>Presentaciones</h2>
        <p className="pt-sub">
          {days.length} días · {totalCount} presentaciones · próximas primero
        </p>
      </div>

      <div className="pt-body">
        {loading ? (
          <div role="status" className="pt-loading">
            <div className="spinner" />
          </div>
        ) : sortedDays.length === 0 ? (
          <p className="pt-empty">No hay presentaciones programadas.</p>
        ) : (
          sortedDays.map((day) => {
            const dom = dominantModality(day);
            const isToday = day.date === todayStr;

            const markerClasses = [
              "pt-marker",
              dom === "pteg" ? "pteg-day" : dom === "teg" ? "teg-day" : "",
              isToday ? "today" : "",
            ]
              .filter(Boolean)
              .join(" ");

            const dayNum = formatDayNumeral(day.date);
            const dowAbbr = formatWeekdayAbbr(day.date);
            const monthAbbr = formatMonthAbbr(day.date);
            const monthName = formatMonth(day.date);
            const [year] = day.date.split("-");

            return (
              <div key={day.id} className="pt-day" data-date={day.date}>
                <div
                  className={markerClasses}
                  onClick={() => onDayMarkerClick?.(day)}
                  role="button"
                  tabIndex={0}
                  onKeyDown={(e) => { if (e.key === "Enter" || e.key === " ") onDayMarkerClick?.(day); }}
                >
                  <span className="d">{dayNum}</span>
                  <span className="dow">{dowAbbr}</span>
                  {isToday && <span className="pulse-dot" />}
                </div>

                <div className="pt-day-content">
                  <div className="pt-day-h">
                    <span>{monthAbbr} {dayNum}</span>
                    <span className="pt-day-my">{monthName} {year}</span>
                    <span className="pt-day-count">{day.presentations.length} turnos</span>
                  </div>

                  {day.presentations.map((p) => (
                    <PresentationRow
                      key={p.id}
                      presentation={p}
                      role={isAdmin ? "admin" : "tutor"}
                      viewerId={viewerId}
                      onClick={() => onPresentationClick?.(p, day)}
                      onEdit={isAdmin && onEditPresentation ? () => onEditPresentation(p, day) : undefined}
                      onDelete={isAdmin && onDeletePresentation ? () => onDeletePresentation(p, day) : undefined}
                    />
                  ))}
                </div>
              </div>
            );
          })
        )}
      </div>
    </div>
  );
}
