import React from "react";
import { describe, it, expect } from "vitest";
import { render, screen, fireEvent } from "@testing-library/react";
import PlanAdminView from "./PlanAdminView";
import type { PresentationDay, Presentation } from "../types/planificacion";

// ── Fixtures ──────────────────────────────────────────────────────────────────

function makePresentation(id: number, overrides: Partial<Presentation> = {}): Presentation {
  return {
    id,
    day: 1,
    project: id + 100,
    project_title: `Project ${id}`,
    project_type: "proyecto",
    student_name: "Ana López",
    student_email: "ana@test.com",
    tutor: 5,
    tutor_name: "P. Linares",
    jurado: [9, 10],
    jurado_names: ["R. Linares", "A. Pérez"],
    start_time: "10:00",
    duration_minutes: 30,
    order: id,
    ...overrides,
  };
}

function makeDay(id: number, date: string, presentations: Partial<Presentation>[] = []): PresentationDay {
  return {
    id,
    date,
    notes: "",
    presentations: presentations.map((p, i) => makePresentation(id * 10 + i, p)),
  };
}

const DAY_WITH_PTEG = makeDay(1, "2026-05-10", [{ project_type: "proyecto" }]);
const DAY_WITH_TEG = makeDay(2, "2026-05-17", [{ project_type: "tesis" }]);
const TWO_DAYS = [DAY_WITH_PTEG, DAY_WITH_TEG];
const NO_OP = () => {};

// ── Tests ──────────────────────────────────────────────────────────────────────

describe("PlanAdminView", () => {
  // 1 — Editorial hero block structure
  it("renders dashboard-hero-bg element, h1 with Planificación de presentaciones, hero-eyebrow, lede, and seg-pill-summary count", () => {
    render(<PlanAdminView days={TWO_DAYS} loading={false} onRefresh={NO_OP} />);

    const heroBg = document.querySelector(".dashboard-hero-bg");
    expect(heroBg).not.toBeNull();

    const h1 = document.querySelector("h1");
    expect(h1).not.toBeNull();
    expect(h1!.textContent).toMatch(/planificaci[oó]n de presentaciones/i);

    const eyebrow = document.querySelector(".hero-eyebrow");
    expect(eyebrow).not.toBeNull();

    const pillSummary = document.querySelector(".seg-pill-summary");
    expect(pillSummary).not.toBeNull();
    expect(pillSummary!.textContent).toContain("2");
  });

  // 2 — UnifiedCalendar mounts (proxy: .cal-day child exists)
  it("renders a calendar with at least one .cal-day cell", () => {
    render(<PlanAdminView days={TWO_DAYS} loading={false} onRefresh={NO_OP} />);

    const calDay = document.querySelector(".cal-day");
    expect(calDay).not.toBeNull();
  });

  // 3 — Presentation list section with rows
  it("renders Presentaciones heading and at least one .prow when days have presentations", () => {
    render(<PlanAdminView days={TWO_DAYS} loading={false} onRefresh={NO_OP} />);

    const heading = Array.from(document.querySelectorAll("h2, h3")).find(
      (el) => el.textContent?.match(/presentaciones/i)
    );
    expect(heading).toBeDefined();

    const prow = document.querySelector(".prow");
    expect(prow).not.toBeNull();
  });

  // 4 — Day-management section with daycard elements
  it("renders Días creados heading and at least one .daycard when days.length > 0", () => {
    render(<PlanAdminView days={TWO_DAYS} loading={false} onRefresh={NO_OP} />);

    const heading = Array.from(document.querySelectorAll("h2, h3")).find(
      (el) => el.textContent?.match(/d[íi]as creados/i)
    );
    expect(heading).toBeDefined();

    const daycard = document.querySelector(".daycard");
    expect(daycard).not.toBeNull();
  });

  // 5 — "Seleccionar días" button is present and toggles bulk mode
  it("renders Seleccionar días button in day-management section", () => {
    render(<PlanAdminView days={TWO_DAYS} loading={false} onRefresh={NO_OP} />);
    expect(screen.getByRole("button", { name: /seleccionar días/i })).toBeInTheDocument();
  });

  it("toggles to Cancelar selección after clicking Seleccionar días", () => {
    render(<PlanAdminView days={TWO_DAYS} loading={false} onRefresh={NO_OP} />);
    fireEvent.click(screen.getByRole("button", { name: /seleccionar días/i }));
    expect(screen.getByRole("button", { name: /cancelar selección/i })).toBeInTheDocument();
  });

  // 6 — Range wiring: onRangeSelect fires setRange correctly (via UnifiedCalendar)
  it("applies selected class on correct range after two rango-mode clicks", () => {
    const { container } = render(
      <PlanAdminView days={TWO_DAYS} loading={false} onRefresh={NO_OP} />
    );

    // Switch calendar to create mode
    const createBtn = screen.getByRole("button", { name: /crear días/i });
    fireEvent.click(createBtn);

    // Make sure rango mode radio is active (it should be by default)
    const rangoRadio = screen.getByRole("radio", { name: /rango/i });
    expect(rangoRadio).toBeInTheDocument();

    // Click day 1 then day 9 in the current month
    const now = new Date();
    const y = now.getFullYear();
    const m = String(now.getMonth() + 1).padStart(2, "0");
    const day1 = `${y}-${m}-01`;
    const day9 = `${y}-${m}-09`;

    const cell1 = container.querySelector(`[data-date="${day1}"]`);
    const cell9 = container.querySelector(`[data-date="${day9}"]`);

    // Skip if either date is out of the current month grid (unlikely but safe)
    if (!cell1 || !cell9) return;

    fireEvent.click(cell1);
    fireEvent.click(cell9);

    // After range selection all 9 days should be selected
    for (let d = 1; d <= 9; d++) {
      const dateStr = `${y}-${m}-${String(d).padStart(2, "0")}`;
      const cell = container.querySelector(`[data-date="${dateStr}"]`);
      if (cell) {
        expect(cell.classList.contains("selected"), `${dateStr} should be selected`).toBe(true);
      }
    }

    // Day 10 should NOT be selected
    const day10 = container.querySelector(`[data-date="${y}-${m}-10"]`);
    if (day10) {
      expect(day10.classList.contains("selected")).toBe(false);
    }
  });
});
