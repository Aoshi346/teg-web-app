import { describe, it, expect } from "vitest";
import { render, screen } from "@testing-library/react";
import { DashboardHero } from "@features/dashboard/components/DashboardHero";
import type { Semester } from "@features/semesters/api/semesters";

const sem: Semester = {
  id: 1,
  period: "2026-01",
  is_active: true,
  start_month: 1,
  end_month: 6,
  label: "",
  created_at: "2025-12-01",
  project_count: 19,
};

describe("DashboardHero", () => {
  it("renders eyebrow, greeting with name, and lede", () => {
    render(
      <DashboardHero
        eyebrow="Buenas tardes · 24 abril"
        greeting="Bienvenido"
        userName="Pedro"
        lede="Resumen del período."
        semester={sem}
        now={new Date(2026, 2, 1)}
      />,
    );
    expect(screen.getByText(/Buenas tardes/i)).toBeInTheDocument();
    expect(screen.getByText(/Bienvenido/i)).toBeInTheDocument();
    expect(screen.getByText("Pedro")).toBeInTheDocument();
    expect(screen.getByText("Resumen del período.")).toBeInTheDocument();
    expect(screen.getByText("2026-01")).toBeInTheDocument();
  });
});
