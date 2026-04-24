"use client";
import React, { useState, useMemo } from "react";
import type { Semester } from "@features/semesters/api/semesters";
import { MONTH_NAMES, defaultMonthsForPeriod, previewLabel } from "../../../lib/semesterPeriods";
import { semesterSchema } from "../../../lib/schemas";

interface SemesterCreateFormProps {
  existing: Semester[];
  onCreate: (data: { period: string; start_month: number; end_month: number }) => Promise<void>;
}

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
    <form onSubmit={handleSubmit} className="p-5 bg-white border border-gray-200 rounded-lg">
      <h3 className="text-base font-semibold mb-3">Crear nuevo semestre</h3>
      <div className="grid grid-cols-[1fr_1fr_2fr_auto] gap-3 items-end">
        <div>
          <label htmlFor="semester-year" className="block text-xs font-semibold mb-1">Año *</label>
          <select id="semester-year" value={year} onChange={(e) => setYear(Number(e.target.value))} className="w-full px-2 py-2 border border-gray-300 rounded-md text-sm bg-white">
            {Array.from({ length: 30 }, (_, i) => 2020 + i).map((y) => <option key={y} value={y}>{y}</option>)}
          </select>
        </div>
        <div>
          <label htmlFor="semester-period" className="block text-xs font-semibold mb-1">Período *</label>
          <select id="semester-period" value={period} onChange={handlePeriodChange} className="w-full px-2 py-2 border border-gray-300 rounded-md text-sm bg-white">
            <option value="01">01 (primer semestre)</option>
            <option value="02">02 (segundo semestre)</option>
          </select>
        </div>
        <div>
          <label className="block text-xs font-semibold mb-1">Rango de meses *</label>
          <div className="flex gap-2 items-center">
            <select aria-label="Mes inicial" value={startMonth} onChange={(e) => setStartMonth(Number(e.target.value))} className="flex-1 px-2 py-2 border border-gray-300 rounded-md text-sm bg-white">
              {MONTH_NAMES.map((m, i) => <option key={i} value={i + 1}>{m}</option>)}
            </select>
            <span className="text-gray-400">→</span>
            <select aria-label="Mes final" value={endMonth} onChange={(e) => setEndMonth(Number(e.target.value))} className="flex-1 px-2 py-2 border border-gray-300 rounded-md text-sm bg-white">
              {MONTH_NAMES.map((m, i) => <option key={i} value={i + 1}>{m}</option>)}
            </select>
          </div>
        </div>
        <button type="submit" disabled={submitting} className="px-4 py-2 bg-blue-600 text-white rounded-md text-sm font-semibold disabled:opacity-50 h-9">
          + Crear
        </button>
      </div>
      <div className="mt-2 px-3 py-2 bg-blue-50 rounded-md text-xs text-blue-900">Vista previa: {preview}</div>
      {error && <p className="mt-2 text-xs text-red-600">{error}</p>}
    </form>
  );
}
