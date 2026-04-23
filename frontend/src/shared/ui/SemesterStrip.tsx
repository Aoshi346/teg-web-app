"use client";

import * as React from "react";
import { Calendar } from "lucide-react";

import type { Semester } from "@features/semesters/api/semesters";
import { getSemesterProgress } from "@features/dashboard/lib/semesterWeek";
import { cn } from "@shared/lib/utils";

export interface SemesterStripProps extends React.HTMLAttributes<HTMLDivElement> {
  semester: Semester;
  now?: Date;
}

export function SemesterStrip({ semester, now, className, ...rest }: SemesterStripProps) {
  const progress = getSemesterProgress(semester, now ?? new Date());

  const statusText =
    progress.status === "in-progress"
      ? "En curso"
      : progress.status === "not-started"
        ? `Comienza en ${progress.daysUntilStart}d`
        : "Finalizado";

  const weekText =
    progress.status === "in-progress"
      ? `semana ${progress.week} de ${progress.totalWeeks}`
      : null;

  return (
    <div
      className={cn(
        "inline-flex flex-wrap items-center gap-x-2 gap-y-1 rounded-lg border border-border-subtle bg-surface-muted px-3 py-2 text-sm text-text-default",
        className,
      )}
      role="status"
      aria-label={`Período ${semester.period}, ${statusText}${weekText ? `, ${weekText}` : ""}`}
      {...rest}
    >
      <Calendar className="h-4 w-4 text-text-muted" aria-hidden />
      <span className="font-semibold text-text-strong">{semester.period}</span>
      <span className="text-text-muted">·</span>
      <span>{semester.label || `${semester.start_month}/${semester.end_month}`}</span>
      <span className="text-text-muted">·</span>
      <span
        className={cn(
          "font-medium",
          progress.status === "in-progress"
            ? "text-success"
            : progress.status === "not-started"
              ? "text-pending"
              : "text-text-muted",
        )}
      >
        {statusText}
      </span>
      {weekText && (
        <>
          <span className="text-text-muted">·</span>
          <span className="text-text-muted">{weekText}</span>
        </>
      )}
    </div>
  );
}
