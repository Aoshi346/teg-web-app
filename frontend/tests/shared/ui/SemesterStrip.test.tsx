import * as React from "react";
import { render, screen } from "@testing-library/react";
import { describe, it, expect } from "vitest";

import { SemesterStrip } from "@shared/ui/SemesterStrip";

const semester = {
  id: 1,
  period: "2026-01",
  is_active: true,
  start_month: 2,
  end_month: 6,
  label: "Febrero 2026 – Junio 2026",
  created_at: "2026-01-01T00:00:00Z",
  project_count: 0,
};

describe("SemesterStrip", () => {
  it("renders period and label", () => {
    render(<SemesterStrip semester={semester} now={new Date("2026-04-23")} />);
    expect(screen.getByText(/2026-01/)).toBeDefined();
    expect(screen.getByText(/Febrero 2026/)).toBeDefined();
  });

  it("renders in-progress status with a week counter", () => {
    render(<SemesterStrip semester={semester} now={new Date("2026-04-23")} />);
    expect(screen.getByText(/En curso/i)).toBeDefined();
    expect(screen.getByText(/semana \d+ de \d+/i)).toBeDefined();
  });

  it("renders not-started status with days-until label", () => {
    render(
      <SemesterStrip
        semester={{ ...semester, start_month: 10, end_month: 12 }}
        now={new Date("2026-04-23")}
      />
    );
    expect(screen.getByText(/comienza en \d+/i)).toBeDefined();
  });

  it("renders finished status", () => {
    render(
      <SemesterStrip
        semester={{ ...semester, period: "2024-01", start_month: 1, end_month: 5 }}
        now={new Date("2026-04-23")}
      />
    );
    expect(screen.getByText(/finalizado/i)).toBeDefined();
  });
});
