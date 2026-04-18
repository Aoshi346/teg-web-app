import React, { useState, useMemo } from "react";
import { ChevronLeft, ChevronRight } from "lucide-react";
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
}

export default function DateSelectionCalendar({
  selected,
  mode,
  onToggleDay,
  onRangeSelect,
}: DateSelectionCalendarProps) {
  const [year, setYear] = useState(new Date().getFullYear());
  const [month, setMonth] = useState(new Date().getMonth());
  const [rangeStart, setRangeStart] = useState<string | null>(null);

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
        setRangeStart(dateStr);
      } else {
        onRangeSelect?.(rangeStart, dateStr);
        setRangeStart(null);
      }
    }
  };

  const isSelected = (dateStr: string) => selected.has(dateStr);
  const isRangeStart = (dateStr: string) => rangeStart === dateStr;

  return (
    <div className="bg-white/40 rounded-2xl border border-gray-200/60 p-4">
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
      <div className="space-y-0.5">
        {matrix.map((row, ri) => (
          <div key={ri} className="grid grid-cols-7 gap-0.5">
            {row.map((dateStr, ci) => {
              if (!dateStr) {
                return <div key={ci} className="h-9 w-full" />;
              }

              const selectedDay = isSelected(dateStr);
              const isStart = isRangeStart(dateStr);

              return (
                <button
                  key={ci}
                  type="button"
                  onClick={() => handleDayClick(dateStr)}
                  className={[
                    "h-9 w-full rounded-lg flex items-center justify-center text-sm font-medium transition-all duration-150 focus:outline-none focus-visible:ring-2 focus-visible:ring-[#ffd23f]",
                    selectedDay
                      ? "bg-[#0f172a] text-white"
                      : isStart
                      ? "bg-[#ffd23f] text-[#011638]"
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

      {/* Mode hint */}
      <p className="mt-2 text-xs text-gray-400 text-center">
        {mode === "individual"
          ? "Haz clic en un día para seleccionarlo"
          : rangeStart
          ? "Clic en día final para seleccionar rango"
          : "Clic en día inicial para comenzar rango"}
      </p>
    </div>
  );
}
