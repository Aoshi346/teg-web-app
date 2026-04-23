import { describe, it, expect } from "vitest";
import { getSemesterProgress } from "@features/dashboard/lib/semesterWeek";
import type { Semester } from "@features/semesters/api/semesters";

const make = (overrides: Partial<Semester> = {}): Semester => ({
  id: 1,
  period: "2026-01",
  is_active: true,
  start_month: 2,
  end_month: 6,
  label: "Febrero 2026 – Junio 2026",
  created_at: "2026-01-01T00:00:00Z",
  ...overrides,
});

describe("getSemesterProgress", () => {
  it("mid-semester returns current week and total", () => {
    const s = make({ period: "2026-01", start_month: 2, end_month: 6 });
    const result = getSemesterProgress(s, new Date("2026-04-23"));
    expect(result.status).toBe("in-progress");
    expect(result.week).toBeGreaterThan(0);
    expect(result.totalWeeks).toBeGreaterThanOrEqual(result.week);
  });

  it("before start returns days-until status", () => {
    const s = make({ period: "2026-01", start_month: 5, end_month: 9 });
    const result = getSemesterProgress(s, new Date("2026-04-01"));
    expect(result.status).toBe("not-started");
    expect(result.daysUntilStart).toBeGreaterThan(0);
  });

  it("after end returns finished status", () => {
    const s = make({ period: "2025-01", start_month: 1, end_month: 5 });
    const result = getSemesterProgress(s, new Date("2026-04-23"));
    expect(result.status).toBe("finished");
  });

  it("cross-year semester (Sep to Jan) computes end in following year", () => {
    const s = make({ period: "2025-02", start_month: 9, end_month: 1 });
    const result = getSemesterProgress(s, new Date("2025-12-01"));
    expect(result.status).toBe("in-progress");
    expect(result.totalWeeks).toBeGreaterThan(16);
  });

  it("exact start boundary yields week 1", () => {
    const s = make({ period: "2026-01", start_month: 3, end_month: 7 });
    const result = getSemesterProgress(s, new Date("2026-03-01"));
    expect(result.status).toBe("in-progress");
    expect(result.week).toBe(1);
  });

  it("one-month semester computes ~4-5 total weeks", () => {
    const s = make({ period: "2026-01", start_month: 4, end_month: 4 });
    const result = getSemesterProgress(s, new Date("2026-04-15"));
    expect(result.totalWeeks).toBeGreaterThanOrEqual(4);
    expect(result.totalWeeks).toBeLessThanOrEqual(5);
  });
});
