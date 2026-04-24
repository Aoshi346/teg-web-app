"use client";

import * as React from "react";

import type { Semester } from "@features/semesters/api/semesters";
import { getSemesterProgress } from "@features/dashboard/lib/semesterWeek";
import { cn } from "@shared/lib/utils";
import type { SemesterMiniStat } from "@features/dashboard/lib/types";

export interface SemesterStripProps extends React.HTMLAttributes<HTMLDivElement> {
  semester: Semester;
  now?: Date;
  mainStats?: SemesterMiniStat[];
}

const STATUS_LABEL = {
  "in-progress": "Activo",
  "not-started": "Próximo",
  finished: "Finalizado",
} as const;

const STATUS_PILL_CLASS = {
  "in-progress": "bg-success/12 text-success",
  "not-started": "bg-pending/12 text-pending",
  finished: "bg-surface-sunken text-text-muted",
} as const;

const STATUS_DOT_CLASS = {
  "in-progress": "bg-success ring-success/20",
  "not-started": "bg-pending ring-pending/20",
  finished: "bg-text-muted ring-text-muted/20",
} as const;

export function SemesterStrip({
  semester,
  now,
  mainStats,
  className,
  ...rest
}: SemesterStripProps) {
  const nowDate = now ?? new Date();
  const progress = getSemesterProgress(semester, nowDate);
  const status = progress.status;
  const pct =
    status === "in-progress"
      ? Math.round((progress.week / progress.totalWeeks) * 100)
      : status === "finished"
        ? 100
        : 0;

  const ariaLabel = `Período ${semester.period}, ${STATUS_LABEL[status]}${
    status === "in-progress" ? `, semana ${progress.week} de ${progress.totalWeeks}` : ""
  }`;

  return (
    <div
      className={cn(
        "relative min-w-[280px] overflow-hidden rounded-2xl border border-border-subtle bg-surface px-4 py-3 shadow-[0_1px_2px_rgba(12,21,48,0.04)]",
        className,
      )}
      role="status"
      aria-label={ariaLabel}
      {...rest}
    >
      <span
        aria-hidden
        className="absolute inset-x-0 top-0 h-[3px] bg-gradient-to-r from-primary to-[var(--brand-orange)]"
      />
      <div className="mt-1 flex items-center justify-between gap-2">
        <span className="text-lg font-extrabold tracking-tight text-text-strong">
          {semester.period}
        </span>
        <span
          className={cn(
            "inline-flex items-center gap-1.5 rounded-full px-2 py-0.5 text-[9px] font-extrabold uppercase tracking-[0.08em]",
            STATUS_PILL_CLASS[status],
          )}
        >
          <span
            aria-hidden
            className={cn("h-1.5 w-1.5 rounded-full ring-[3px]", STATUS_DOT_CLASS[status])}
          />
          {STATUS_LABEL[status]}
        </span>
      </div>

      {mainStats && mainStats.length > 0 && (
        <div className="mt-2.5 flex gap-4 border-t border-dashed border-border-subtle pt-2.5">
          {mainStats.slice(0, 3).map((s) => (
            <div key={s.label} className="flex flex-col">
              <span className="text-lg font-black leading-none tracking-tight text-text-strong">
                {s.num}
              </span>
              <span className="mt-1 text-[9px] font-bold uppercase tracking-[0.08em] text-text-muted">
                {s.label}
              </span>
            </div>
          ))}
        </div>
      )}

      <div className="mt-3 h-[5px] overflow-hidden rounded-full bg-surface-sunken">
        <span
          aria-hidden
          className="block h-full rounded-full bg-gradient-to-r from-primary to-[var(--brand-orange)] shadow-[0_0_12px_rgba(0,102,255,0.3)]"
          style={{ width: `${pct}%` }}
        />
      </div>
      <div className="mt-1.5 flex justify-between text-[10px] font-semibold text-text-muted">
        <span>
          {status === "in-progress"
            ? `Semana ${progress.week} de ${progress.totalWeeks}`
            : status === "not-started"
              ? `Comienza en ${progress.daysUntilStart}d`
              : null}
        </span>
        <span>{pct}%</span>
      </div>
    </div>
  );
}
