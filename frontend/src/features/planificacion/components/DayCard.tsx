import type { PresentationDay } from "../types/planificacion";
import {
  formatDayNumeral,
  formatWeekday,
  formatMonthYear,
} from "../lib/formatDate";

export interface DayCardProps {
  day: PresentationDay;
  onClick?: (day: PresentationDay) => void;
  onDelete?: (day: PresentationDay) => void;
  /** Cuando true, la tarjeta entra en modo selección masiva */
  selectable?: boolean;
  /** Estado de selección en modo masivo */
  selected?: boolean;
  /** Llamado cuando el usuario selecciona o deselecciona en modo masivo */
  onSelect?: (day: PresentationDay, sel: boolean) => void;
}

/**
 * Extrae el apellido (último fragmento separado por espacios) del nombre completo del estudiante.
 */
function extractLastName(fullName: string): string {
  const parts = fullName.trim().split(/\s+/);
  return parts[parts.length - 1];
}

export default function DayCard({
  day,
  onClick,
  onDelete,
  selectable = false,
  selected = false,
  onSelect,
}: DayCardProps) {
  const count = day.presentations.length;
  const countLabel = `${count} pres`;

  const sorted = [...day.presentations].sort((a, b) =>
    a.start_time.localeCompare(b.start_time)
  );
  const visible = sorted.slice(0, 3);

  function handleCardClick() {
    if (selectable) {
      onSelect?.(day, !selected);
    } else {
      onClick?.(day);
    }
  }

  const rootClass = ["daycard", selected ? "selected" : ""].filter(Boolean).join(" ");

  return (
    <div className={rootClass} onClick={handleCardClick}>
      <div className="daycard-head">
        {selectable && (
          <span
            className={["daycard-check", selected ? "checked" : ""].filter(Boolean).join(" ")}
            aria-hidden
          >
            {selected ? "✓" : ""}
          </span>
        )}
        <div className="daycard-numblk">
          <span className="n">{formatDayNumeral(day.date)}</span>
          <span className="dow">{formatWeekday(day.date)}</span>
          <span className="my">{formatMonthYear(day.date)}</span>
        </div>
        <span className="daycard-cnt">{countLabel}</span>
        {!selectable && onDelete && (
          <button
            className="daycard-del"
            aria-label="Eliminar día"
            onClick={(e) => {
              e.stopPropagation();
              onDelete(day);
            }}
          >
            ×
          </button>
        )}
      </div>

      <div className="daycard-list">
        {count === 0 ? (
          <div className="daycard-item">
            <span className="empty">Sin presentaciones</span>
          </div>
        ) : (
          visible.map((p) => (
            <div className="daycard-item" key={p.id}>
              <span className="t">{p.start_time}</span>
              <span>{extractLastName(p.student_name)}</span>
            </div>
          ))
        )}
      </div>
    </div>
  );
}
