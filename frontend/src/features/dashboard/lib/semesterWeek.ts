import type { Semester } from "@features/semesters/api/semesters";

export type SemesterProgressStatus = "not-started" | "in-progress" | "finished";

export interface SemesterProgress {
  status: SemesterProgressStatus;
  week: number;
  totalWeeks: number;
  daysUntilStart: number;
}

const MS_PER_DAY = 86_400_000;
const MS_PER_WEEK = MS_PER_DAY * 7;

function getBoundaryDates(s: Semester): { start: Date; end: Date } {
  const year = parseInt(s.period.slice(0, 4), 10);
  const start = new Date(year, s.start_month - 1, 1);
  const endYear = s.end_month < s.start_month ? year + 1 : year;
  const end = new Date(endYear, s.end_month, 0);
  return { start, end };
}

export function getSemesterProgress(
  semester: Semester,
  now: Date = new Date()
): SemesterProgress {
  const { start, end } = getBoundaryDates(semester);
  const totalWeeks = Math.max(
    1,
    Math.ceil((end.getTime() - start.getTime()) / MS_PER_WEEK)
  );

  if (now.getTime() < start.getTime()) {
    const daysUntilStart = Math.ceil(
      (start.getTime() - now.getTime()) / MS_PER_DAY
    );
    return { status: "not-started", week: 0, totalWeeks, daysUntilStart };
  }

  if (now.getTime() > end.getTime()) {
    return { status: "finished", week: totalWeeks, totalWeeks, daysUntilStart: 0 };
  }

  const rawWeek = Math.floor((now.getTime() - start.getTime()) / MS_PER_WEEK) + 1;
  const week = Math.max(1, Math.min(totalWeeks, rawWeek));
  return { status: "in-progress", week, totalWeeks, daysUntilStart: 0 };
}
