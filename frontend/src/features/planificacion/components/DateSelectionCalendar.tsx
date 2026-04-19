import React, { useState, useMemo } from "react";
import { ChevronLeft, ChevronRight, X, Calendar, MousePointerClick } from "lucide-react";
import { formatMonthName, toDateStr } from "../lib/formatDate";

const WEEKDAYS = ["L", "M", "M", "J", "V", "S", "D"];

function getMonthMatrix(year: number, month: number): (string | null)[][] {
  const firstDay = new Date(year, month, 1);
  const startOffset = (firstDay.getDay() + 6) % 7;
  const daysInMonth = new Date(year, month + 1, 0).getDate();

  const cells: (string | null)[] = Array(startOffset).fill(null);
  for (let d = 1; d <= daysInMonth; d++) {
    cells.push(toDateStr(new Date(year, month, d)));
  }
  while (cells.length % 7 !== 0) cells.push(null);

  const rows: (string | null)[][] = [];
  for (let i = 0; i < cells.length; i += 7) rows.push(cells.slice(i, i + 7));
  return rows;
}

interface DateSelectionCalendarProps {
  selected: Set<string>;
  mode: "rango" | "individual";
  onToggleDay: (dateStr: string) => void;
  onRangeSelect?: (start: string, end: string) => void;
  onClearAll?: () => void;
}

export default function DateSelectionCalendar({
  selected,
  mode,
  onToggleDay,
  onRangeSelect,
  onClearAll,
}: DateSelectionCalendarProps) {
  const [year, setYear] = useState(new Date().getFullYear());
  const [month, setMonth] = useState(new Date().getMonth());
  const [rangeStart, setRangeStart] = useState<string | null>(null);
  const [hoveredDate, setHoveredDate] = useState<string | null>(null);

  const matrix = useMemo(() => getMonthMatrix(year, month), [year, month]);

  const prevMonth = () => {
    if (month === 0) { setYear((y) => y - 1); setMonth(11); }
    else setMonth((m) => m - 1);
  };
  const nextMonth = () => {
    if (month === 11) { setYear((y) => y + 1); setMonth(0); }
    else setMonth((m) => m + 1);
  };

  const handleDayClick = (dateStr: string) => {
    if (mode === "individual") {
      onToggleDay(dateStr);
    } else {
      // Range mode
      if (!rangeStart) {
        // First click - set start AND add it to selected immediately
        setRangeStart(dateStr);
        onToggleDay(dateStr);
      } else {
        // Second click - complete range
        const start = rangeStart < dateStr ? rangeStart : dateStr;
        const end = rangeStart < dateStr ? dateStr : rangeStart;
        onRangeSelect?.(start, end);
        setRangeStart(null);
        setHoveredDate(null);
      }
    }
  };

  const isSelected = (dateStr: string) => selected.has(dateStr);
  const isRangeStart = (dateStr: string) => rangeStart === dateStr;
  const isInRange = (dateStr: string) => {
    if (!rangeStart) return false;
    // When hovering, show preview
    if (hoveredDate && hoveredDate !== rangeStart) {
      const start = rangeStart < hoveredDate ? rangeStart : hoveredDate;
      const end = rangeStart < hoveredDate ? hoveredDate : rangeStart;
      return dateStr > start && dateStr < end;
    }
    return false;
  };
  const isHoveredEnd = (dateStr: string) => {
    if (!rangeStart || mode !== "rango") return false;
    return dateStr === hoveredDate && hoveredDate !== rangeStart;
  };
  const isPotentialEnd = (dateStr: string) => {
    if (!rangeStart || mode !== "rango") return false;
    return !hoveredDate && dateStr > rangeStart;
  };

  const selectedArray = Array.from(selected).sort();
  const selectionLabel = selected.size === 0
    ? "Ningún día seleccionado"
    : selected.size === 1
    ? `${selectedArray[0]}`
    : `${selected.size} días: ${selectedArray[0]} → ${selectedArray[selectedArray.length - 1]}`;

  // Preview range text
  const rangePreviewText = useMemo(() => {
    if (mode !== "rango" || !rangeStart) return null;
    if (hoveredDate && hoveredDate !== rangeStart) {
      const start = rangeStart < hoveredDate ? rangeStart : hoveredDate;
      const end = rangeStart < hoveredDate ? hoveredDate : rangeStart;
      return `${start} → ${end}`;
    }
    return `Desde ${rangeStart}...`;
  }, [mode, rangeStart, hoveredDate]);

  return (
    <div className="bg-white/40 rounded-2xl border border-gray-200/60 p-4 flex flex-col h-full">
      {/* Month navigation */}
      <div className="flex items-center justify-between mb-3">
        <button
          onClick={prevMonth}
          aria-label="Mes anterior"
          className="w-7 h-7 flex items-center justify-center rounded-lg text-gray-500 hover:bg-gray-100 transition-colors"
        >
          <ChevronLeft className="w-4 h-4" />
        </button>
        <span className="text-sm font-bold text-gray-900 capitalize">
          {formatMonthName(year, month)}
        </span>
        <button
          onClick={nextMonth}
          aria-label="Mes siguiente"
          className="w-7 h-7 flex items-center justify-center rounded-lg text-gray-500 hover:bg-gray-100 transition-colors"
        >
          <ChevronRight className="w-4 h-4" />
        </button>
      </div>

      {/* Weekday strip */}
      <div className="grid grid-cols-7 mb-1">
        {WEEKDAYS.map((d, i) => (
          <div
            key={i}
            className="text-center text-xs font-semibold uppercase tracking-[0.18em] text-gray-400 py-1"
          >
            {d}
          </div>
        ))}
      </div>

      {/* Day grid */}
      <div className="space-y-0.5 flex-1">
        {matrix.map((row, ri) => (
          <div key={ri} className="grid grid-cols-7 gap-0.5">
            {row.map((dateStr, ci) => {
              if (!dateStr) {
                return <div key={ci} className="h-9 w-full" />;
              }

              const selectedDay = isSelected(dateStr);
              const isStart = isRangeStart(dateStr);
              const inRange = isInRange(dateStr);
              const isEnd = isHoveredEnd(dateStr);
              const potentialEnd = isPotentialEnd(dateStr);

              return (
                <button
                  key={ci}
                  type="button"
                  onClick={() => handleDayClick(dateStr)}
                  onMouseEnter={() => mode === "rango" && rangeStart && setHoveredDate(dateStr)}
                  onMouseLeave={() => mode === "rango" && setHoveredDate(null)}
                  className={[
                    "h-9 w-full rounded-lg flex items-center justify-center text-xs font-medium transition-all duration-100 focus:outline-none focus-visible:ring-2 focus-visible:ring-[#ffd23f]",
                    selectedDay
                      ? "bg-[#0f172a] text-white font-bold"
                      : isStart
                      ? "bg-[#ff6b35] text-white font-bold ring-2 ring-[#ff6b35] ring-offset-1 ring-offset-white"
                      : inRange
                      ? "bg-[#ffd23f]/40 text-[#011638]"
                      : isEnd
                      ? "bg-[#ffd23f] text-[#011638] font-bold ring-2 ring-[#ffd23f] ring-offset-1 ring-offset-white"
                      : potentialEnd
                      ? "bg-[#ffd23f]/20 text-[#011638]"
                      : "text-gray-700 hover:bg-gray-100",
                  ]
                    .join(" ")
                    .trim()}
                  aria-label={dateStr}
                  aria-pressed={selectedDay}
                >
                  {dateStr.split("-")[2].replace(/^0/, "")}
                </button>
              );
            })}
          </div>
        ))}
      </div>

      {/* Selection status panel */}
      <div className="mt-3 p-2.5 rounded-lg bg-gray-50 border border-gray-200/60 space-y-2">
        {/* Mode indicator */}
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-1.5">
            <MousePointerClick className="w-3.5 h-3.5 text-gray-400" />
            <span className="text-[10px] font-semibold uppercase tracking-wider text-gray-400">
              {mode === "rango" ? "Rango" : "Individual"}
            </span>
          </div>
          {selected.size > 0 && (
            <button
              onClick={onClearAll}
              className="flex items-center gap-1 text-[10px] font-semibold text-gray-400 hover:text-red-500 transition-colors"
            >
              <X className="w-3 h-3" />
              Limpiar
            </button>
          )}
        </div>

        {/* Selection count */}
        <div className="flex items-center gap-1.5">
          <Calendar className="w-3.5 h-3.5 text-gray-400" />
          <span className="text-xs font-medium text-gray-700">
            {selectionLabel}
          </span>
        </div>

        {/* Range preview hint */}
        {mode === "rango" && (
          <div className="pt-1 border-t border-gray-200/60">
            {rangeStart ? (
              <p className="text-[10px] text-[#ff6b35] font-semibold flex items-center gap-1">
                <span className="inline-block w-1.5 h-1.5 rounded-full bg-[#ff6b35]" />
                {hoveredDate && hoveredDate !== rangeStart
                  ? `Rango: ${rangeStart} → ${hoveredDate}`
                  : `Inicio: ${rangeStart} — clic en fecha final`}
              </p>
            ) : (
              <p className="text-[10px] text-gray-400">
                {mode === "rango"
                  ? "Clic en fecha inicial para comenzar rango"
                  : "Clic en un día para seleccionarlo"}
              </p>
            )}
          </div>
        )}
      </div>
    </div>
  );
}
