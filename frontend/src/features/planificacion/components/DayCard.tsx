import React from "react";
import { Trash2 } from "lucide-react";
import { PresentationDay, Presentation } from "../types/planificacion";
import PresentationCard from "./PresentationCard";
import { formatWeekday, formatDayNumeral, formatMonthYear } from "../lib/formatDate";

interface DayCardProps {
  day: PresentationDay;
  isAdmin: boolean;
  onAddPresentation?: (dayId: number) => void;
  onEditPresentation?: (presentation: Presentation) => void;
  onDeletePresentation?: (presentation: Presentation) => void;
  onDeleteDay?: (day: PresentationDay) => void;
  style?: React.CSSProperties;
}

function getTypePill(day: PresentationDay): { label: string; className: string } | null {
  const types = new Set(day.presentations.map((p) => p.project_type));
  if (types.has("tesis") && types.has("proyecto")) {
    return { label: "TEG + PTEG", className: "bg-purple-50 text-purple-700 border-purple-100" };
  }
  if (types.has("tesis")) {
    return { label: "TEG", className: "bg-orange-50 text-orange-700 border-orange-100" };
  }
  if (types.has("proyecto")) {
    return { label: "PTEG", className: "bg-blue-50 text-blue-700 border-blue-100" };
  }
  return null;
}

export default function DayCard({
  day,
  isAdmin,
  onAddPresentation,
  onEditPresentation,
  onDeletePresentation,
  onDeleteDay,
  style,
}: DayCardProps) {
  const typePill = getTypePill(day);

  return (
    <div
      id={`day-card-${day.id}`}
      className="bg-white rounded-2xl border border-gray-200/60 shadow-xl shadow-slate-200/40 overflow-hidden"
      style={style}
    >
      {/* Day header */}
      <div className="flex items-start gap-4 px-5 sm:px-6 pt-5 pb-4">
        {/* Date info */}
        <div className="flex-1 min-w-0">
          <div className="flex items-start justify-between gap-2">
            <div>
              <p className="text-2xl font-bold text-gray-900 leading-none">
                {formatDayNumeral(day.date)}
              </p>
              <p className="text-sm font-semibold uppercase tracking-wide text-gray-500 mt-0.5 capitalize">
                {formatWeekday(day.date)}
              </p>
              <p className="text-sm text-gray-400 capitalize mt-0.5">
                {formatMonthYear(day.date)}
              </p>
            </div>

            <div className="flex items-center gap-2 flex-shrink-0">
              {typePill && (
                <span
                  className={`hidden sm:inline-flex items-center px-2.5 py-1 rounded-full text-xs font-bold border ${typePill.className}`}
                >
                  {typePill.label}
                </span>
              )}

              {isAdmin && (
                <button
                  aria-label="Borrar día"
                  onClick={() => onDeleteDay?.(day)}
                  className="p-1.5 rounded-lg text-gray-400 hover:text-red-500 hover:bg-red-50 transition-colors"
                >
                  <Trash2 className="w-4 h-4" />
                </button>
              )}
            </div>
          </div>
        </div>
      </div>

      {/* Divider */}
      <div className="h-px bg-gray-100 mx-5 sm:mx-6" />

      {/* Presentations */}
      <div className="divide-y divide-gray-100 px-4 sm:px-5">
        {day.presentations.length === 0 ? (
          <p className="text-sm text-gray-400 text-center py-6">
            Día sin presentaciones programadas
          </p>
        ) : (
          day.presentations.map((p) => (
            <PresentationCard
              key={p.id}
              presentation={p}
              isAdmin={isAdmin}
              onEdit={onEditPresentation}
              onDelete={onDeletePresentation}
            />
          ))
        )}
      </div>

      {/* Admin: agregar presentación */}
      {isAdmin && (
        <div className="px-4 sm:px-5 pb-5 pt-3">
          <button
            onClick={() => onAddPresentation?.(day.id)}
            className="w-full py-2.5 rounded-xl border border-dashed border-gray-300 text-gray-500 text-sm font-semibold hover:border-gray-400 hover:text-gray-700 transition-colors"
          >
            + Agregar presentación
          </button>
        </div>
      )}
    </div>
  );
}
