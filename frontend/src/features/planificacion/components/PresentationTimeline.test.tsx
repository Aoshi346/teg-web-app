import React from "react";
import { describe, it, expect, vi } from "vitest";
import { render, screen, fireEvent } from "@testing-library/react";
import PresentationTimeline from "./PresentationTimeline";
import type { PresentationDay, Presentation } from "../types/planificacion";

// Mock PresentationRow so we don't depend on its implementation
vi.mock("./PresentationRow", () => ({
  default: ({
    presentation,
    onClick,
  }: {
    presentation: Presentation;
    onClick?: () => void;
  }) => (
    <button data-testid={`row-${presentation.id}`} onClick={onClick}>
      {presentation.project_title}
    </button>
  ),
}));

// ── Fixtures ───────────────────────────────────────────────────────────────────

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
    tutor_name: "Carlos Méndez",
    jurado: [9, 10],
    jurado_names: ["Rosa Díaz", "Luis Herrera"],
    start_time: "10:00",
    duration_minutes: 30,
    order: id,
    ...overrides,
  };
}

// Days: all PTEG-dominant, TEG-dominant, and mixed
const DAY_PTEG: PresentationDay = {
  id: 1,
  date: "2026-03-08",
  notes: "",
  presentations: [
    makePresentation(1, { project_type: "proyecto" }),
    makePresentation(2, { project_type: "proyecto" }),
    makePresentation(3, { project_type: "tesis" }),
  ],
};

// today marker matches todayOverride
const DAY_TODAY: PresentationDay = {
  id: 2,
  date: "2026-03-12",
  notes: "",
  presentations: [
    makePresentation(4, { project_type: "proyecto" }),
  ],
};

const DAY_TEG: PresentationDay = {
  id: 3,
  date: "2026-03-20",
  notes: "",
  presentations: [
    makePresentation(5, { project_type: "tesis" }),
    makePresentation(6, { project_type: "tesis" }),
    makePresentation(7, { project_type: "proyecto" }),
  ],
};

// Note: listed out-of-order to test sorting
const ALL_DAYS = [DAY_TEG, DAY_PTEG, DAY_TODAY];
const TODAY_OVERRIDE = "2026-03-12";

// ── Tests ──────────────────────────────────────────────────────────────────────

describe("PresentationTimeline", () => {
  // 1 — Renders the card with header "Presentaciones"
  it("renders a card with header Presentaciones", () => {
    render(<PresentationTimeline days={ALL_DAYS} />);
    const card = document.querySelector(".pt-card");
    expect(card).not.toBeNull();
    const head = card!.querySelector(".pt-head");
    expect(head).not.toBeNull();
    expect(head!.textContent).toMatch(/presentaciones/i);
  });

  // 2 — Header sub shows day + presentation count
  it("header sub shows day count and total presentation count", () => {
    render(<PresentationTimeline days={ALL_DAYS} />);
    const head = document.querySelector(".pt-head");
    // 3 days, 7 presentations total
    expect(head!.textContent).toMatch(/3/);
    expect(head!.textContent).toMatch(/7/);
  });

  // 3 — Empty state when days=[]
  it("renders empty state message when days is empty", () => {
    render(<PresentationTimeline days={[]} />);
    const body = document.querySelector(".pt-body");
    expect(body!.textContent).toMatch(/no hay presentaciones programadas/i);
  });

  // 4 — Loading state when loading=true
  it("renders a loading spinner when loading=true", () => {
    render(<PresentationTimeline days={[]} loading={true} />);
    // Spinner by role or by class; we check for an element that signals loading
    const spinner =
      document.querySelector("[role='status']") ??
      document.querySelector(".spinner") ??
      document.querySelector("[aria-label='cargando']");
    expect(spinner).not.toBeNull();
  });

  // 5 — One marker per day
  it("renders one .pt-marker per day", () => {
    render(<PresentationTimeline days={ALL_DAYS} />);
    const markers = document.querySelectorAll(".pt-marker");
    expect(markers).toHaveLength(3);
  });

  // 6 — PTEG-dominant day marker has class pteg-day
  it("marker for a PTEG-dominant day has class pteg-day", () => {
    render(<PresentationTimeline days={[DAY_PTEG]} />);
    const marker = document.querySelector(".pt-marker");
    expect(marker!.classList.contains("pteg-day")).toBe(true);
  });

  // 7 — TEG-dominant day marker has class teg-day
  it("marker for a TEG-dominant day has class teg-day", () => {
    render(<PresentationTimeline days={[DAY_TEG]} />);
    const marker = document.querySelector(".pt-marker");
    expect(marker!.classList.contains("teg-day")).toBe(true);
  });

  // 8 — Today marker has class today and has a pulsing dot child
  it("today marker (matching todayOverride) has class today and a pulsing-dot child", () => {
    render(<PresentationTimeline days={ALL_DAYS} todayOverride={TODAY_OVERRIDE} />);
    const todayMarker = document.querySelector(".pt-marker.today");
    expect(todayMarker).not.toBeNull();
    const pulsingDot =
      todayMarker!.querySelector(".pulse-dot") ??
      todayMarker!.querySelector(".pulsing-dot") ??
      todayMarker!.querySelector("[data-today-pulse]");
    expect(pulsingDot).not.toBeNull();
  });

  // 9 — Days are sorted by date ascending
  it("renders days in ascending date order regardless of input order", () => {
    render(<PresentationTimeline days={ALL_DAYS} />);
    const dayElements = document.querySelectorAll(".pt-day");
    // We expect the first day to contain date 2026-03-08 data
    expect(dayElements[0].getAttribute("data-date") ?? dayElements[0].textContent).toContain("8");
    expect(dayElements[2].getAttribute("data-date") ?? dayElements[2].textContent).toContain("20");
  });

  // 10 — Presentations render as PresentationRow inside each day-content
  it("renders PresentationRow components inside pt-day-content for each presentation", () => {
    render(<PresentationTimeline days={[DAY_PTEG]} />);
    // The mocked PresentationRow renders data-testid=row-{id}
    expect(screen.getByTestId("row-1")).toBeInTheDocument();
    expect(screen.getByTestId("row-2")).toBeInTheDocument();
    expect(screen.getByTestId("row-3")).toBeInTheDocument();
  });

  // 11 — Clicking the marker fires onDayMarkerClick(day)
  it("clicking a day marker fires onDayMarkerClick with the correct day", () => {
    const onDayMarkerClick = vi.fn();
    render(
      <PresentationTimeline
        days={[DAY_PTEG]}
        onDayMarkerClick={onDayMarkerClick}
      />
    );
    const marker = document.querySelector(".pt-marker") as HTMLElement;
    fireEvent.click(marker);
    expect(onDayMarkerClick).toHaveBeenCalledWith(DAY_PTEG);
  });

  // 12 — Clicking a presentation row fires onPresentationClick(p, day)
  it("clicking a presentation row fires onPresentationClick with the correct presentation and day", () => {
    const onPresentationClick = vi.fn();
    render(
      <PresentationTimeline
        days={[DAY_PTEG]}
        onPresentationClick={onPresentationClick}
      />
    );
    const row = screen.getByTestId("row-1");
    fireEvent.click(row);
    expect(onPresentationClick).toHaveBeenCalledWith(DAY_PTEG.presentations[0], DAY_PTEG);
  });
});
