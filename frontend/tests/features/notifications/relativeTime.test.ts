import { describe, it, expect } from "vitest";
import { formatRelativeTime } from "@features/notifications/lib/relativeTime";

// Thresholds (must match implementation):
//   <60s       -> "hace unos segundos"
//   1–59min    -> "hace X minutos"
//   1–23h      -> "hace X horas"
//   1–6 days   -> "hace X días"
//   >=7 days   -> absolute date string (locale "es-VE" or similar, e.g. "25 abr. 2026")

describe("formatRelativeTime", () => {
  it("returns 'hace unos segundos' for timestamps less than 60 seconds ago", () => {
    const now = new Date("2026-04-25T10:00:00Z");
    const date = new Date("2026-04-25T09:59:45Z"); // 15s ago

    expect(formatRelativeTime(date, now)).toBe("hace unos segundos");
  });

  it("returns 'hace X minutos' for timestamps between 1 and 59 minutes ago", () => {
    const now = new Date("2026-04-25T10:00:00Z");
    const date = new Date("2026-04-25T09:42:00Z"); // 18 min ago

    expect(formatRelativeTime(date, now)).toBe("hace 18 minutos");
  });

  it("returns 'hace X horas' for timestamps between 1 and 23 hours ago", () => {
    const now = new Date("2026-04-25T10:00:00Z");
    const date = new Date("2026-04-25T04:00:00Z"); // 6 hours ago

    expect(formatRelativeTime(date, now)).toBe("hace 6 horas");
  });

  it("returns 'hace X días' for timestamps between 1 and 6 days ago", () => {
    const now = new Date("2026-04-25T10:00:00Z");
    const date = new Date("2026-04-22T10:00:00Z"); // 3 days ago

    expect(formatRelativeTime(date, now)).toBe("hace 3 días");
  });

  it("falls back to an absolute date string for timestamps 7 or more days ago", () => {
    const now = new Date("2026-04-25T10:00:00Z");
    const date = new Date("2026-04-10T10:00:00Z"); // 15 days ago

    const result = formatRelativeTime(date, now);

    // Should contain the day number and some month text — not a relative expression
    expect(result).not.toMatch(/hace/i);
    expect(result).toMatch(/\d/);
  });
});
