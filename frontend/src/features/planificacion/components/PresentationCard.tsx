import React from "react";
import { Pencil, Trash2, Clock } from "lucide-react";
import { Presentation } from "../types/planificacion";

interface PresentationCardProps {
  presentation: Presentation;
  isAdmin: boolean;
  onEdit?: (presentation: Presentation) => void;
  onDelete?: (presentation: Presentation) => void;
}

export default function PresentationCard({
  presentation,
  isAdmin,
  onEdit,
  onDelete,
}: PresentationCardProps) {
  return (
    <div className="flex gap-4 py-4 px-1 group hover:bg-gray-50 transition-colors duration-150 rounded-lg">
      {/* Time chip */}
      <div className="flex-shrink-0 flex flex-col items-center gap-1 pt-0.5">
        <span className="inline-flex items-center gap-1 px-3 py-1 rounded-full bg-blue-50 text-blue-700 text-xs font-bold">
          <Clock className="w-3 h-3" />
          <time dateTime={presentation.start_time}>{presentation.start_time}</time>
        </span>
        <span className="text-xs text-gray-400">
          {presentation.duration_minutes} min
        </span>
      </div>

      {/* Content */}
      <div className="flex-1 min-w-0">
        <div className="flex items-start justify-between gap-2">
          <div className="min-w-0">
            <p className="text-base font-semibold text-gray-900 leading-snug truncate">
              {presentation.project_title}
            </p>
            <p className="text-sm text-gray-500 mt-0.5">
              {presentation.student_name}
              {presentation.student_email ? ` · ${presentation.student_email}` : ""}
            </p>
            <p className="text-xs text-gray-500 mt-1">
              {presentation.tutor_name && (
                <span>
                  Tutor: <span className="text-gray-700">{presentation.tutor_name}</span>
                </span>
              )}
              {presentation.jurado_names && presentation.jurado_names.length > 0 && (
                <span className={presentation.tutor_name ? " · " : ""}>
                  Jurado:{" "}
                  <span className="text-gray-700">{presentation.jurado_names.join(", ")}</span>
                </span>
              )}
            </p>
          </div>

          {/* Admin actions — only rendered for admin */}
          {isAdmin && (
            <div className="flex items-center gap-1 opacity-0 group-hover:opacity-100 transition-opacity duration-150 flex-shrink-0">
              <button
                aria-label="Editar presentación"
                onClick={() => onEdit?.(presentation)}
                className="p-1.5 rounded-lg text-gray-400 hover:text-blue-600 hover:bg-blue-50 transition-colors"
              >
                <Pencil className="w-4 h-4" />
              </button>
              <button
                aria-label="Eliminar presentación"
                onClick={() => onDelete?.(presentation)}
                className="p-1.5 rounded-lg text-gray-400 hover:text-red-500 hover:bg-red-50 transition-colors"
              >
                <Trash2 className="w-4 h-4" />
              </button>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
