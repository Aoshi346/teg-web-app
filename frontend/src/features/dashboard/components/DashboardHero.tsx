"use client";

import * as React from "react";

import { SemesterStrip } from "@shared/ui/SemesterStrip";
import type { Semester } from "@features/semesters/api/semesters";
import type { SemesterMiniStat } from "@features/dashboard/lib/types";

export interface DashboardHeroProps {
  eyebrow: string;
  greeting: string;
  userName: string;
  lede: string;
  semester: Semester;
  now?: Date;
  semesterStats?: SemesterMiniStat[];
}

export function DashboardHero({
  eyebrow,
  greeting,
  userName,
  lede,
  semester,
  now,
  semesterStats,
}: DashboardHeroProps) {
  return (
    <section className="dashboard-hero-bg relative overflow-hidden rounded-2xl border border-border-subtle px-7 py-6">
      <div className="relative z-10 flex flex-col gap-6 md:flex-row md:items-start md:justify-between">
        <div className="flex flex-col gap-1.5">
          <p className="flex items-center gap-2 text-[10px] font-extrabold uppercase tracking-[0.14em] text-primary">
            <span
              aria-hidden
              className="inline-block h-[2px] w-6 rounded-full bg-gradient-to-r from-primary to-[var(--brand-orange)]"
            />
            {eyebrow}
          </p>
          <h1 className="text-3xl font-extrabold leading-tight tracking-[-0.03em] text-text-strong md:text-[34px]">
            {greeting},{" "}
            <span className="bg-gradient-to-br from-primary to-[var(--brand-orange)] bg-clip-text font-black text-transparent">
              {userName}
            </span>
          </h1>
          <p className="max-w-[380px] text-sm font-medium leading-relaxed text-text-muted">
            {lede}
          </p>
        </div>
        <SemesterStrip semester={semester} now={now} mainStats={semesterStats} />
      </div>
    </section>
  );
}
