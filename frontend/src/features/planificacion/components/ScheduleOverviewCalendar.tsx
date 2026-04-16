import React, { useState, useMemo } from "react";
import { ChevronLeft, ChevronRight, CalendarDays } from "lucide-react";
import { PresentationDay } from "../types/planificacion";
import { formatMonthName, isToday, toDateStr } from "../lib/formatDate";

const WEEKDAYS = ["L", "M", "M", "J", "V", "S", "D"];

/**
 * Construye la matriz de semanas para el mes dado (lunes primero).
 * Retorna filas de 7 celdas, cada celda es YYYY-MM-DD o null si está fuera del mes.
 */
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

interface ScheduleOverviewCalendarProps {
  days: PresentationDay[];
}

/**
 * Calendario de solo lectura que muestra todos los días con presentaciones
 * del semestre activo. Al hacer clic en un día con presentaciones, hace
 * scroll suave a la tarjeta de ese día y la resalta brevemente.
 * Visible para todos los roles (sin gate de admin).
 */
export default function ScheduleOverviewCalendar({
  days,
}: ScheduleOverviewCalendarProps) {
  const presentationMap = useMemo(() => {
    const map = new Map<string, number>();
    for (const day of days) {
      map.set(day.date, day.presentations.length);
    }
    return map;
  }, [days]);

  // Default to the month containing the soonest upcoming day, or current month
  const defaultMonth = useMemo(() => {
    const today = toDateStr(new Date());
    const upcoming = days
      .filter((d) => d.date >= today)
      .sort((a, b) => a.date.localeCompare(b.date))[0];
    if (upcoming) {
      const [y, m] = upcoming.date.split("-").map(Number);
      return { year: y, month: m - 1 };
    }
    const now = new Date();
    return { year: now.getFullYear(), month: now.getMonth() };
  }, [days]);

  const [year, setYear] = useState(defaultMonth.year);
  const [month, setMonth] = useState(defaultMonth.month);

  const matrix = useMemo(() => getMonthMatrix(year, month), [year, month]);

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

  const handleDayClick = (dateStr: string) => {
    const day = days.find((d) => d.date === dateStr);
    if (!day) return;

    const el = document.getElementById(`day-card-${day.id}`);
    if (!el) return;

    el.scrollIntoView({ behavior: "smooth", block: "center" });

    // Flash ring-2 ring-[#ffd23f] for 1s then remove
    el.classList.add("ring-flash-active");
    setTimeout(() => {
      el.classList.remove("ring-flash-active");
    }, 1000);
  };

  return (
    <div className="bg-white/60 backdrop-blur-xl rounded-[2rem] border border-gray-200/60 shadow-xl shadow-slate-200/40 p-5 sm:p-6 mb-8">
      <style>{`
        .ring-flash-active {
          outline: 2px solid #ffd23f;
          outline-offset: 2px;
          animation: ring-flash 1s ease-out forwards;
        }
        @keyframes ring-flash {
          0% { outline-color: #ffd23f; }
          100% { outline-color: transparent; }
        }
      `}</style>

      {/* Header */}
      <div className="mb-4">
        <h3 className="text-2xl font-bold text-gray-900 tracking-tight">
          Calendario de presentaciones
        </h3>
        <p className="text-sm text-gray-500 font-medium mt-1">
          Haz clic en un día para ver los detalles.
        </p>
      </div>

      {/* Month navigation */}
      <div className="flex items-center justify-between mb-4">
        <button
          onClick={prevMonth}
          aria-label="Mes anterior"
          className="w-9 h-9 flex items-center justify-center rounded-xl text-gray-500 hover:bg-gray-100 transition-colors"
        >
          <ChevronLeft className="w-5 h-5" />
        </button>
        <span className="text-xl font-bold text-gray-900 tracking-tight capitalize">
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

      {/* Day grid */}
      <div className="space-y-1">
        {matrix.map((row, ri) => (
          <div key={ri} className="grid grid-cols-7 gap-1">
            {row.map((dateStr, ci) => {
              if (!dateStr) {
                return (
                  <div
                    key={ci}
                    className="h-16 sm:h-16 w-full"
                  />
                );
              }

              const count = presentationMap.get(dateStr) ?? 0;
              const hasDay = count > 0;
              const today = isToday(dateStr);

              return (
                <button
                  key={ci}
                  type="button"
                  onClick={() => hasDay && handleDayClick(dateStr)}
                  disabled={!hasDay}
                  className={[
                    "h-14 sm:h-16 w-full rounded-xl flex flex-col items-center justify-center relative transition-all duration-150 focus:outline-none focus-visible:ring-2 focus-visible:ring-[#ffd23f]",
                    hasDay
                      ? "cursor-pointer hover:bg-blue-50"
                      : "cursor-default",
                    today
                      ? "ring-2 ring-[#ffd23f] ring-offset-1"
                      : "",
                  ]
                    .join(" ")
                    .trim()}
                  aria-label={
                    hasDay
                      ? `${dateStr} — ${count} ${count === 1 ? "presentación" : "presentaciones"}`
                      : dateStr
                  }
                >
                  <span
                    className={`text-xl font-semibold leading-none ${
                      hasDay ? "text-gray-900" : "text-gray-400"
                    }`}
                  >
                    {dateStr.split("-")[2].replace(/^0/, "")}
                  </span>
                  {hasDay && (
                    <span className="mt-1 inline-flex items-center gap-0.5 px-1.5 py-0.5 rounded-full bg-[#0066ff]/10 text-[#0066ff] text-[10px] font-bold leading-none">
                      <CalendarDays className="w-2.5 h-2.5" />
                      {count}
                    </span>
                  )}
                </button>
              );
            })}
          </div>
        ))}
      </div>
    </div>
  );
}
