import React, { useState } from "react";
import { Trash2, ChevronDown, Plus, Calendar, User, Users } from "lucide-react";
import { PresentationDay, Presentation } from "../types/planificacion";
import PresentationCard from "./PresentationCard";
import { formatWeekday, formatDayNumeral, formatMonthYear } from "../lib/formatDate";

interface CompactDayCardProps {
  day: PresentationDay;
  isAdmin: boolean;
  selectable?: boolean;
  selected?: boolean;
  onSelect?: (day: PresentationDay, selected: boolean) => void;
  onAddPresentation?: (dayId: number) => void;
  onEditPresentation?: (presentation: Presentation) => void;
  onDeletePresentation?: (presentation: Presentation) => void;
  onDeleteDay?: (day: PresentationDay) => void;
  style?: React.CSSProperties;
}

// Merge juror names that might be duplicated
function uniqueNames(names: string[]): string[] {
  return [...new Set(names)];
}

export default function CompactDayCard({
  day,
  isAdmin,
  selectable = false,
  selected = false,
  onSelect,
  onAddPresentation,
  onEditPresentation,
  onDeletePresentation,
  onDeleteDay,
  style,
}: CompactDayCardProps) {
  const [expanded, setExpanded] = useState(false);
  const count = day.presentations.length;

  const tegCount = day.presentations.filter(p => p.project_type === "tesis").length;
  const ptegCount = day.presentations.filter(p => p.project_type === "proyecto").length;

  // Get unique tutors and jurors across all presentations
  const allTutors = uniqueNames(day.presentations.map(p => p.tutor_name).filter((n): n is string => Boolean(n)));
  const allJurors = uniqueNames(day.presentations.flatMap(p => p.jurado_names || []));
  const allStudents = uniqueNames(day.presentations.map(p => p.student_name).filter((n): n is string => Boolean(n)));

  const handleCheckboxChange = (checked: boolean) => {
    onSelect?.(day, checked);
  };

  return (
    <div
      className={[
        "bg-white rounded-2xl border shadow-lg shadow-slate-200/20 overflow-hidden transition-all duration-200 hover:shadow-xl hover:shadow-slate-200/30",
        selectable ? "cursor-pointer" : "",
        selected ? "border-[#ffd23f] ring-2 ring-[#ffd23f]" : "border-gray-200/60",
      ].join(" ")}
      style={style}
    >
      {/* Collapsed header — always visible */}
      <div className="flex items-center gap-3 px-4 py-3">
        {/* Selection checkbox */}
        {selectable && (
          <label className="flex-shrink-0 flex items-center justify-center">
            <input
              type="checkbox"
              checked={selected}
              onChange={(e) => handleCheckboxChange(e.target.checked)}
              className="w-4 h-4 rounded border-gray-300 text-usm-blue focus:ring-usm-blue cursor-pointer"
              onClick={(e) => e.stopPropagation()}
            />
          </label>
        )}

        {/* Calendar icon with date */}
        <div className="flex-shrink-0 w-11 h-11 rounded-xl bg-gradient-to-br from-[#0f172a] to-[#1e293b] flex flex-col items-center justify-center text-white shadow-md">
          <span className="text-[9px] font-bold uppercase leading-none opacity-80">
            {formatWeekday(day.date).slice(0, 3)}
          </span>
          <span className="text-lg font-extrabold leading-none">
            {formatDayNumeral(day.date)}
          </span>
        </div>

        {/* Date + type info */}
        <button
          onClick={() => setExpanded((v) => !v)}
          className="flex-1 min-w-0 text-left hover:bg-gray-50 rounded-lg px-2 py-1 transition-colors duration-150"
          aria-expanded={expanded}
        >
          <div className="flex items-center gap-2 flex-wrap">
            <span className="text-sm font-semibold text-gray-900 capitalize">
              {formatMonthYear(day.date)}
            </span>
            {tegCount > 0 && (
              <span className="inline-flex items-center px-1.5 py-0.5 rounded-full bg-[#ff6b35]/15 text-[10px] font-bold text-[#ff6b35]">
                {tegCount} TEG
              </span>
            )}
            {ptegCount > 0 && (
              <span className="inline-flex items-center px-1.5 py-0.5 rounded-full bg-[#0066ff]/15 text-[10px] font-bold text-[#0066ff]">
                {ptegCount} PTEG
              </span>
            )}
          </div>
          {/* Jurors/Tutors/Students summary - always visible */}
          {(allJurors.length > 0 || allStudents.length > 0) && (
            <div className="flex items-center gap-1 mt-0.5">
              <Users className="w-3 h-3 text-gray-400" />
              <span className="text-[10px] text-gray-500 truncate max-w-[140px]">
                {allStudents.slice(0, 1).join(", ")}
                {allStudents.length > 1 ? ` +${allStudents.length - 1}` : ""}
                {allJurors.length > 0 ? ` · ${allJurors.slice(0, 1).join(", ")}` : ""}
                {allJurors.length > 1 ? ` +${allJurors.length - 1}` : ""}
              </span>
            </div>
          )}
        </button>

        {/* Actions */}
        <div className="flex items-center gap-0.5 flex-shrink-0">
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
          {isAdmin && (
            <button
              onClick={() => onDeleteDay?.(day)}
              className="p-1.5 rounded-lg text-gray-400 hover:text-red-500 hover:bg-red-50 transition-colors"
              aria-label="Eliminar día"
              title="Eliminar día"
            >
              <Trash2 className="w-4 h-4" />
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
          {/* Tutor + Jurors info bar */}
          {(allTutors.length > 0 || allJurors.length > 0) && (
            <div className="px-4 py-2 bg-gray-50/70 border-b border-gray-100 space-y-1">
              {allTutors.length > 0 && (
                <div className="flex items-start gap-1.5">
                  <User className="w-3 h-3 text-gray-400 mt-0.5 flex-shrink-0" />
                  <div className="min-w-0">
                    <span className="text-[9px] font-semibold uppercase tracking-wider text-gray-400">Tutor</span>
                    <p className="text-[11px] text-gray-600 truncate">{allTutors.join(", ")}</p>
                  </div>
                </div>
              )}
              {allJurors.length > 0 && (
                <div className="flex items-start gap-1.5">
                  <Users className="w-3 h-3 text-gray-400 mt-0.5 flex-shrink-0" />
                  <div className="min-w-0">
                    <span className="text-[9px] font-semibold uppercase tracking-wider text-gray-400">Jurados</span>
                    <p className="text-[11px] text-gray-600 truncate">{allJurors.join(", ")}</p>
                  </div>
                </div>
              )}
            </div>
          )}

          {/* Presentations list */}
          <div className="px-3 py-2 space-y-0.5">
            {count === 0 ? (
              <p className="text-sm text-gray-400 text-center py-4">
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

          {/* Admin: agregar presentación */}
          {isAdmin && (
            <div className="px-3 pb-3 pt-1">
              <button
                onClick={() => onAddPresentation?.(day.id)}
                className="w-full py-2 rounded-lg border border-dashed border-gray-300 text-gray-500 text-xs font-semibold hover:border-gray-400 hover:text-gray-700 hover:bg-gray-50 transition-colors flex items-center justify-center gap-1.5"
              >
                <Plus className="w-3.5 h-3.5" />
                Agregar presentación
              </button>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
