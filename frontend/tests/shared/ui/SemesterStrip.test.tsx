import { describe, it, expect } from "vitest";
import { render, screen } from "@testing-library/react";
import { SemesterStrip } from "@shared/ui/SemesterStrip";
import type { Semester } from "@features/semesters/api/semesters";

const sem: Semester = {
  id: 1,
  period: "2026-01",
  is_active: true,
  start_month: 1,
  end_month: 6,
  label: "Enero 2026 – Junio 2026",
  created_at: "2025-12-01",
  project_count: 19,
};

describe("SemesterStrip (enriched)", () => {
  it("renders period, status pill, and progress label", () => {
    const now = new Date(2026, 2, 1); // 1-mar-2026, mid-period
    render(<SemesterStrip semester={sem} now={now} />);
    expect(screen.getByText("2026-01")).toBeInTheDocument();
    expect(screen.getByText(/Activo/i)).toBeInTheDocument();
    expect(screen.getByText(/Semana \d+ de \d+/i)).toBeInTheDocument();
  });

  it("renders mini-stats when provided", () => {
    const now = new Date(2026, 2, 1);
    render(
      <SemesterStrip
        semester={sem}
        now={now}
        mainStats={[
          { num: "19", label: "Proyectos" },
          { num: "3", label: "Hoy" },
          { num: "42", label: "Días rest." },
        ]}
      />,
    );
    expect(screen.getByText("19")).toBeInTheDocument();
    expect(screen.getByText("Proyectos")).toBeInTheDocument();
    expect(screen.getByText("Días rest.")).toBeInTheDocument();
  });

  it("shows 'Próximo' status pill when not started", () => {
    const future: Semester = { ...sem, period: "2027-01", start_month: 6, end_month: 12 };
    const now = new Date(2027, 0, 1);
    render(<SemesterStrip semester={future} now={now} />);
    expect(screen.getByText(/Próximo/i)).toBeInTheDocument();
  });

  it("shows 'Finalizado' status pill when finished", () => {
    const past = sem;
    const now = new Date(2026, 8, 1);
    render(<SemesterStrip semester={past} now={now} />);
    expect(screen.getByText(/Finalizado/i)).toBeInTheDocument();
  });
});
