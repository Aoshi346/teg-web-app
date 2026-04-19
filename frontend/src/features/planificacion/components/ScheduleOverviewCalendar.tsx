import React, { useState, useMemo } from "react";
import { ChevronLeft, ChevronRight } from "lucide-react";
import { PresentationDay } from "../types/planificacion";
import { formatMonthName, isToday, toDateStr } from "../lib/formatDate";

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

/** Returns which project types a day has so we can show colored dots. */
function getDayTypeSet(day: PresentationDay): Set<"tesis" | "proyecto"> {
  const types = new Set<"tesis" | "proyecto">();
  for (const p of day.presentations) {
    if (p.project_type === "tesis" || p.project_type === "proyecto") {
      types.add(p.project_type);
    }
  }
  return types;
}

interface ScheduleOverviewCalendarProps {
  days: PresentationDay[];
  /** When true, use tighter padding and smaller cells for the two-column layout. */
  compact?: boolean;
  /** Called when a day with presentations is clicked. */
  onDayClick?: (dateStr: string) => void;
}

export default function ScheduleOverviewCalendar({
  days,
  compact = false,
  onDayClick,
}: ScheduleOverviewCalendarProps) {
  // Map date string -> PresentationDay for O(1) lookups
  const dayByDate = useMemo(() => {
    const map = new Map<string, PresentationDay>();
    for (const d of days) map.set(d.date, d);
    return map;
  }, [days]);

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
    if (month === 0) { setYear((y) => y - 1); setMonth(11); }
    else setMonth((m) => m - 1);
  };
  const nextMonth = () => {
    if (month === 11) { setYear((y) => y + 1); setMonth(0); }
    else setMonth((m) => m + 1);
  };

  const handleDayClick = (dateStr: string) => {
    if (!dayByDate.has(dateStr)) return;
    onDayClick ? onDayClick(dateStr) : (() => {
      const el = document.querySelector(`[data-date="${dateStr}"]`);
      if (!el) return;
      el.scrollIntoView({ behavior: "smooth", block: "center" });
      el.classList.add("ring-flash-active");
      setTimeout(() => el.classList.remove("ring-flash-active"), 1000);
    })();
  };

  const containerPad = compact ? "p-3" : "p-5 sm:p-6";
  const cellH = compact ? "h-12" : "h-14 sm:h-16";
  const dayNumSize = compact ? "text-lg" : "text-xl";
  const monthLabelSize = compact ? "text-base" : "text-xl";

  return (
    <div className={`bg-white/60 backdrop-blur-xl rounded-[2rem] border border-gray-200/60 shadow-xl shadow-slate-200/40 ${containerPad}`}>
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

      {/* Month navigation */}
      <div className="flex items-center justify-between mb-3">
        <button
          onClick={prevMonth}
          aria-label="Mes anterior"
          className="w-8 h-8 flex items-center justify-center rounded-xl text-gray-500 hover:bg-gray-100 transition-colors"
        >
          <ChevronLeft className="w-4 h-4" />
        </button>
        <span className={`font-bold text-gray-900 tracking-tight capitalize ${monthLabelSize}`}>
          {formatMonthName(year, month)}
        </span>
        <button
          onClick={nextMonth}
          aria-label="Mes siguiente"
          className="w-8 h-8 flex items-center justify-center rounded-xl text-gray-500 hover:bg-gray-100 transition-colors"
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
                return <div key={ci} className={`${cellH} w-full`} />;
              }

              const day = dayByDate.get(dateStr);
              const hasDay = !!day;
              const today = isToday(dateStr);
              const count = day?.presentations.length ?? 0;
              const typeSet = day ? getDayTypeSet(day) : new Set<"tesis" | "proyecto">();

              // Background colors for days with presentations
              const hasTesis = typeSet.has("tesis");
              const hasProyecto = typeSet.has("proyecto");
              const bgColor = hasDay
                ? hasTesis && hasProyecto
                  ? "bg-gradient-to-br from-[#ff6b35]/20 to-[#0066ff]/20"
                  : hasTesis
                  ? "bg-[#ff6b35]/15"
                  : "bg-[#0066ff]/15"
                : "";

              return (
                <button
                  key={ci}
                  type="button"
                  onClick={() => hasDay && handleDayClick(dateStr)}
                  disabled={!hasDay}
                  className={[
                    `${cellH} w-full rounded-xl flex flex-col items-center justify-center relative transition-all duration-150 focus:outline-none focus-visible:ring-2 focus-visible:ring-[#ffd23f]`,
                    hasDay ? `cursor-pointer hover:opacity-90 ${bgColor}` : "cursor-default",
                    today && !hasDay ? "ring-2 ring-[#ffd23f] ring-offset-1" : "",
                  ]
                    .join(" ")
                    .trim()}
                  aria-label={
                    hasDay && day
                      ? `${dateStr} — ${day.presentations.length} ${day.presentations.length === 1 ? "presentación" : "presentaciones"}`
                      : dateStr
                  }
                >
                  <span className={`font-semibold leading-none ${dayNumSize} ${hasDay ? "text-gray-900" : "text-gray-400"}`}>
                    {dateStr.split("-")[2].replace(/^0/, "")}
                  </span>
                  {/* Count badge */}
                  {hasDay && count > 0 && (
                    <span className={[
                      "mt-0.5 inline-flex items-center justify-center rounded-full text-[9px] font-bold",
                      hasTesis && hasProyecto
                        ? "bg-gradient-to-r from-[#ff6b35] to-[#0066ff] text-white px-1.5"
                        : hasTesis
                        ? "bg-[#ff6b35] text-white px-1.5"
                        : "bg-[#0066ff] text-white px-1.5"
                    ].join(" ")}>
                      {count}
                    </span>
                  )}
                </button>
              );
            })}
          </div>
        ))}
      </div>

      {/* Legend */}
      <div className="mt-3 flex items-center justify-center gap-5">
        <span className="flex items-center gap-1.5 text-xs font-semibold text-gray-600">
          <span className="w-2 h-2 rounded-full bg-[#ff6b35] inline-block" />
          TEG
        </span>
        <span className="flex items-center gap-1.5 text-xs font-semibold text-gray-600">
          <span className="w-2 h-2 rounded-full bg-[#0066ff] inline-block" />
          PTEG
        </span>
      </div>
    </div>
  );
}
