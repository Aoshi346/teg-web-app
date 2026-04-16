import React, { useState } from "react";
import { ChevronLeft, ChevronRight } from "lucide-react";
import { SelectionMode, PresentationDay } from "../types/planificacion";
import { formatMonthName, isToday, toDateStr } from "../lib/formatDate";

const WEEKDAYS = ["L", "M", "M", "J", "V", "S", "D"];

interface WeekCalendarProps {
  mode: SelectionMode;
  selected: Set<string>;
  existingDays: PresentationDay[];
  rangeStart: string | null;
  isAdmin: boolean;
  onToggleDay: (dateStr: string) => void;
  onCreateDays: () => void;
}

function getMonthMatrix(year: number, month: number): (string | null)[][] {
  const firstDay = new Date(year, month, 1);
  // Monday-first: 0=Mon … 6=Sun
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

export default function WeekCalendar({
  selected,
  existingDays,
  rangeStart,
  isAdmin,
  onToggleDay,
  onCreateDays,
}: WeekCalendarProps) {
  const now = new Date();
  const [year, setYear] = useState(now.getFullYear());
  const [month, setMonth] = useState(now.getMonth());

  const existingSet = new Set(existingDays.map((d) => d.date));
  const matrix = getMonthMatrix(year, month);

  const prevMonth = () => {
    if (month === 0) {
      setYear((y) => y - 1);
      setMonth(11);
    } else {
      setMonth((m) => m - 1);
    }
  };
  const nextMonth = () => {
    if (month === 11) {
      setYear((y) => y + 1);
      setMonth(0);
    } else {
      setMonth((m) => m + 1);
    }
  };

  return (
    <div className="bg-white rounded-2xl border border-gray-200/60 shadow-xl shadow-slate-200/40 p-5 sm:p-6">
      {/* Month navigation */}
      <div className="flex items-center justify-between mb-4">
        <button
          onClick={prevMonth}
          aria-label="Mes anterior"
          className="w-9 h-9 flex items-center justify-center rounded-xl text-gray-500 hover:bg-gray-100 transition-colors"
        >
          <ChevronLeft className="w-5 h-5" />
        </button>
        <span className="text-2xl font-bold text-gray-900 tracking-tight capitalize">
          {formatMonthName(year, month)}
        </span>
        <button
          onClick={nextMonth}
          aria-label="Mes siguiente"
          className="w-9 h-9 flex items-center justify-center rounded-xl text-gray-500 hover:bg-gray-100 transition-colors"
        >
          <ChevronRight className="w-5 h-5" />
        </button>
      </div>

      {/* Weekday strip */}
      <div className="grid grid-cols-7 mb-2">
        {WEEKDAYS.map((d, i) => (
          <div
            key={i}
            className="text-center text-xs font-semibold uppercase tracking-[0.18em] text-gray-400 py-1"
          >
            {d}
          </div>
        ))}
      </div>

      {/* Day grid — 64×64 cells (44×44 on mobile) */}
      <div className="space-y-1">
        {matrix.map((row, ri) => (
          <div key={ri} className="grid grid-cols-7 gap-1">
            {row.map((dateStr, ci) => {
              if (!dateStr) {
                return <div key={ci} className="w-11 h-11 sm:w-16 sm:h-16" />;
              }

              const isSelected = selected.has(dateStr);
              const hasExisting = existingSet.has(dateStr);
              const today = isToday(dateStr);
              const isRangeStart = rangeStart === dateStr;

              return (
                <button
                  key={ci}
                  role="button"
                  aria-pressed={isSelected}
                  onClick={() => onToggleDay(dateStr)}
                  className={[
                    "w-11 h-11 sm:w-16 sm:h-16 rounded-xl flex flex-col items-center justify-center relative transition-all duration-120 focus:outline-none focus:ring-2 focus:ring-[#ffd23f] focus:ring-offset-2",
                    isSelected
                      ? "bg-[#011638] text-white scale-105"
                      : isRangeStart
                      ? "bg-[#011638]/20 text-[#011638]"
                      : hasExisting
                      ? "ring-1 ring-[#0066ff]/30 text-gray-700 hover:bg-gray-50"
                      : "text-gray-700 hover:bg-gray-100",
                    today && !isSelected
                      ? "ring-2 ring-[#ffd23f] ring-offset-1"
                      : "",
                  ]
                    .join(" ")
                    .trim()}
                >
                  <span className="text-xl font-semibold leading-none">
                    {dateStr.split("-")[2].replace(/^0/, "")}
                  </span>
                </button>
              );
            })}
          </div>
        ))}
      </div>

      {/* Admin CTA */}
      {isAdmin && (
        <div className="mt-5">
          <button
            onClick={onCreateDays}
            disabled={selected.size === 0}
            className="group relative w-full h-12 rounded-xl text-sm font-bold bg-[#0f172a] text-white hover:bg-[#1e293b] transition-all shadow-lg shadow-slate-900/10 disabled:opacity-40 disabled:cursor-not-allowed disabled:shadow-none"
          >
            Crear / actualizar días
          </button>
        </div>
      )}
    </div>
  );
}
