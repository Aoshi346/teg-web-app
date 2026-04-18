import React, { useState } from "react";
import { Trash2, ChevronDown, Plus } from "lucide-react";
import { PresentationDay, Presentation } from "../types/planificacion";
import PresentationCard from "./PresentationCard";
import { formatWeekday, formatDayNumeral, formatMonthYear } from "../lib/formatDate";

interface CompactDayCardProps {
  day: PresentationDay;
  isAdmin: boolean;
  onAddPresentation?: (dayId: number) => void;
  onEditPresentation?: (presentation: Presentation) => void;
  onDeletePresentation?: (presentation: Presentation) => void;
  onDeleteDay?: (day: PresentationDay) => void;
  style?: React.CSSProperties;
}

export default function CompactDayCard({
  day,
  isAdmin,
  onAddPresentation,
  onEditPresentation,
  onDeletePresentation,
  onDeleteDay,
  style,
}: CompactDayCardProps) {
  const [expanded, setExpanded] = useState(false);
  const count = day.presentations.length;

  return (
    <div
      className="bg-white rounded-2xl border border-gray-200/60 shadow-xl shadow-slate-200/40 overflow-hidden"
      style={style}
    >
      {/* Collapsed header — always visible */}
      <div className="flex items-center gap-3 px-5 py-4">
        {/* Date — clickable to expand */}
        <button
          onClick={() => setExpanded((v) => !v)}
          className="flex-1 min-w-0 text-left hover:bg-gray-50 rounded-lg -ml-2 px-2 py-1 transition-colors duration-150"
          aria-expanded={expanded}
        >
          <div className="flex items-baseline gap-2 flex-wrap">
            <span className="text-base font-bold text-gray-900">
              {formatDayNumeral(day.date)}
            </span>
            <span className="text-sm font-semibold uppercase tracking-wide text-gray-500 capitalize">
              {formatWeekday(day.date)}
            </span>
            <span className="text-sm text-gray-400 capitalize">
              {formatMonthYear(day.date)}
            </span>
          </div>
        </button>

        {/* Count badge + actions */}
        <div className="flex items-center gap-2 flex-shrink-0">
          <span className="inline-flex items-center px-2.5 py-1 rounded-full bg-[#ffd23f]/20 text-[#011638] text-xs font-bold">
            {count} {count === 1 ? "presentación" : "presentaciones"}
          </span>
          {isAdmin && (
            <button
              onClick={() => onAddPresentation?.(day.id)}
              className="p-1.5 rounded-lg bg-usm-blue/10 text-usm-blue hover:bg-usm-blue/20 transition-colors"
              aria-label="Agregar presentación"
              title="Agregar presentación"
            >
              <Plus className="w-4 h-4" />
            </button>
          )}
          <button
            onClick={() => setExpanded((v) => !v)}
            className="p-1.5 rounded-lg text-gray-400 hover:bg-gray-100 transition-colors"
            aria-label={expanded ? "Contraer" : "Expandir"}
          >
            <ChevronDown
              className={`w-4 h-4 transition-transform duration-200 ${
                expanded ? "rotate-180" : ""
              }`}
            />
          </button>
        </div>
      </div>

      {/* Expanded: presentations + admin CTA */}
      {expanded && (
        <div className="border-t border-gray-100">
          {/* Presentations list */}
          <div className="divide-y divide-gray-100 px-4">
            {count === 0 ? (
              <p className="text-sm text-gray-400 text-center py-5">
                Sin presentaciones
              </p>
            ) : (
              day.presentations.map((p) => (
                <PresentationCard
                  key={p.id}
                  presentation={p}
                  isAdmin={isAdmin}
                  compact
                  onEdit={onEditPresentation}
                  onDelete={onDeletePresentation}
                />
              ))
            )}
          </div>

          {/* Admin: agregar presentación + delete day */}
          {isAdmin && (
            <div className="px-4 pb-4 pt-2 flex items-center gap-3">
              <button
                onClick={() => onAddPresentation?.(day.id)}
                className="flex-1 py-2.5 rounded-xl border border-dashed border-gray-300 text-gray-500 text-sm font-semibold hover:border-gray-400 hover:text-gray-700 transition-colors flex items-center justify-center gap-1.5"
              >
                <Plus className="w-4 h-4" />
                Agregar presentación
              </button>
              <button
                aria-label="Borrar día"
                onClick={() => onDeleteDay?.(day)}
                className="p-2.5 rounded-xl text-gray-400 hover:text-red-500 hover:bg-red-50 transition-colors"
              >
                <Trash2 className="w-4 h-4" />
              </button>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
