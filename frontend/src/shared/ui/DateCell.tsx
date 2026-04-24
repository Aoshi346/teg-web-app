"use client";

import * as React from "react";

import { cn } from "@shared/lib/utils";

const MONTH_ABBR_ES = [
  "Ene", "Feb", "Mar", "Abr", "May", "Jun",
  "Jul", "Ago", "Sep", "Oct", "Nov", "Dic",
] as const;

export interface DateCellProps {
  date: Date | string;
  className?: string;
}

export function DateCell({ date, className }: DateCellProps) {
  const d = typeof date === "string" ? new Date(date) : date;
  const day = String(d.getDate()).padStart(2, "0");
  const month = MONTH_ABBR_ES[d.getMonth()] ?? "";

  return (
    <div
      className={cn(
        "flex h-[42px] w-[42px] flex-shrink-0 flex-col overflow-hidden rounded-[10px] border border-border-subtle bg-gradient-to-b from-surface to-surface-muted",
        className,
      )}
      aria-label={`${month} ${day}`}
    >
      <span
        className="bg-primary text-center text-[8px] font-extrabold uppercase tracking-[0.08em] text-white"
        style={{ lineHeight: 1, padding: "2px 0" }}
      >
        {month}
      </span>
      <span
        className="mt-1 text-center text-base font-black leading-none tracking-tight text-text-strong"
      >
        {day}
      </span>
    </div>
  );
}
