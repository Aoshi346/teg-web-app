"use client";
import React, { useState, useMemo } from "react";
import { Plus } from "lucide-react";
import type { Semester } from "@features/semesters/api/semesters";
import { MONTH_NAMES, defaultMonthsForPeriod, previewLabel } from "../../../lib/semesterPeriods";
import { semesterSchema } from "../../../lib/schemas";

interface SemesterCreateFormProps {
  existing: Semester[];
  onCreate: (data: { period: string; start_month: number; end_month: number }) => Promise<void>;
}

const INPUT_CLASS =
  "w-full h-10 px-3 bg-surface border border-border-default rounded-lg text-[13.5px] font-medium text-text-strong transition-colors hover:border-[#b8bccb] focus:outline-none focus:border-primary focus:ring-[3px] focus:ring-[rgba(0,102,255,0.16)]";
const LABEL_CLASS = "block text-[13px] font-semibold text-text-default mb-1.5";
const SELECT_STYLE = {
  backgroundImage:
    "url(\"data:image/svg+xml,%3Csvg width='10' height='6' xmlns='http://www.w3.org/2000/svg'%3E%3Cpath d='M1 1l4 4 4-4' stroke='%236b7589' stroke-width='1.5' fill='none' stroke-linecap='round'/%3E%3C/svg%3E\")",
  backgroundRepeat: "no-repeat" as const,
  backgroundPosition: "right 12px center",
};

export function SemesterCreateForm({ existing, onCreate }: SemesterCreateFormProps) {
  const [year, setYear] = useState(new Date().getFullYear());
  const [period, setPeriod] = useState<"01" | "02">("01");
  const [startMonth, setStartMonth] = useState(1);
  const [endMonth, setEndMonth] = useState(6);
  const [error, setError] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);

  const preview = useMemo(() => previewLabel(year, period, startMonth, endMonth), [year, period, startMonth, endMonth]);

  function handlePeriodChange(e: React.ChangeEvent<HTMLSelectElement>) {
    const p = e.target.value as "01" | "02";
    setPeriod(p);
    const defaults = defaultMonthsForPeriod(p);
    setStartMonth(defaults.startMonth);
    setEndMonth(defaults.endMonth);
  }

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setError(null);
    const parsed = semesterSchema.safeParse({ year, period, startMonth, endMonth });
    if (!parsed.success) {
      setError(parsed.error.issues[0]?.message || "Datos inválidos");
      return;
    }
    const periodKey = `${year}-${period}`;
    if (existing.some((s) => s.period === periodKey)) {
      setError("Ya existe un semestre con ese período");
      return;
    }
    setSubmitting(true);
    try {
      await onCreate({ period: periodKey, start_month: startMonth, end_month: endMonth });
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <form
      onSubmit={handleSubmit}
      className="bg-surface border border-border-subtle rounded-[14px] shadow-[0_1px_2px_rgba(15,23,42,0.03)] overflow-hidden"
    >
      <div className="px-5 py-3.5 border-b border-border-subtle flex items-center gap-2">
        <Plus className="w-4 h-4 text-primary" strokeWidth={2} />
        <div>
          <div className="text-[14.5px] font-bold text-text-strong leading-tight">Crear nuevo semestre</div>
        </div>
      </div>
      <div className="p-5">
        <div className="grid grid-cols-1 md:grid-cols-[1fr_1.4fr_2fr_auto] gap-3.5 items-end">
          <div>
            <label htmlFor="semester-year" className={LABEL_CLASS}>
              Año <span className="text-destructive ml-0.5">*</span>
            </label>
            <select
              id="semester-year"
              value={year}
              onChange={(e) => setYear(Number(e.target.value))}
              className={`${INPUT_CLASS} appearance-none pr-8`}
              style={SELECT_STYLE}
            >
              {Array.from({ length: 30 }, (_, i) => 2020 + i).map((y) => <option key={y} value={y}>{y}</option>)}
            </select>
          </div>
          <div>
            <label htmlFor="semester-period" className={LABEL_CLASS}>
              Período <span className="text-destructive ml-0.5">*</span>
            </label>
            <select
              id="semester-period"
              value={period}
              onChange={handlePeriodChange}
              className={`${INPUT_CLASS} appearance-none pr-8`}
              style={SELECT_STYLE}
            >
              <option value="01">01 — Primer semestre</option>
              <option value="02">02 — Segundo semestre</option>
            </select>
          </div>
          <div>
            <label className={LABEL_CLASS}>
              Rango de meses <span className="text-destructive ml-0.5">*</span>
            </label>
            <div className="grid grid-cols-[1fr_auto_1fr] gap-1.5 items-center">
              <select
                aria-label="Mes inicial"
                value={startMonth}
                onChange={(e) => setStartMonth(Number(e.target.value))}
                className={`${INPUT_CLASS} appearance-none pr-8`}
                style={SELECT_STYLE}
              >
                {MONTH_NAMES.map((m, i) => <option key={i} value={i + 1}>{m}</option>)}
              </select>
              <span className="text-text-muted font-semibold">→</span>
              <select
                aria-label="Mes final"
                value={endMonth}
                onChange={(e) => setEndMonth(Number(e.target.value))}
                className={`${INPUT_CLASS} appearance-none pr-8`}
                style={SELECT_STYLE}
              >
                {MONTH_NAMES.map((m, i) => <option key={i} value={i + 1}>{m}</option>)}
              </select>
            </div>
          </div>
          <button
            type="submit"
            disabled={submitting}
            className="h-10 px-4 bg-primary text-white rounded-lg text-[13.5px] font-semibold inline-flex items-center gap-1.5 shadow-[0_1px_2px_rgba(0,102,255,0.25),inset_0_1px_0_rgba(255,255,255,0.12)] hover:bg-[#0052cc] disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
          >
            <Plus className="w-3.5 h-3.5" strokeWidth={2.5} />
            Crear
          </button>
        </div>

        <div className="mt-4 px-3.5 py-2.5 bg-surface-sunken border border-border-subtle rounded-[9px] flex items-center gap-2.5 text-[13px] flex-wrap">
          <span className="w-1.5 h-1.5 rounded-full bg-primary flex-shrink-0" />
          <span className="text-text-muted font-medium">Vista previa:</span>
          <code className="bg-[rgba(0,102,255,0.08)] text-primary px-1.5 py-px rounded-[5px] font-mono text-xs font-semibold">
            {`${year}-${period}`}
          </code>
          <span className="text-text-strong font-semibold">{preview}</span>
        </div>
        {error && <p className="mt-2 text-xs text-destructive">{error}</p>}
      </div>
    </form>
  );
}
