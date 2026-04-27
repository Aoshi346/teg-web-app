import React from "react";
import { describe, it, expect } from "vitest";
import { render, screen } from "@testing-library/react";
import PlanReviewerView from "./PlanReviewerView";
import type { PresentationDay, Presentation } from "../types/planificacion";

// ── Fixtures ──────────────────────────────────────────────────────────────────

const VIEWER_TUTOR_ID = 5;
const VIEWER_JURADO_ID = 9;

function makePresentation(id: number, overrides: Partial<Presentation> = {}): Presentation {
  return {
    id,
    day: 1,
    project: id + 100,
    project_title: `Proyecto ${id}`,
    project_type: "proyecto",
    student_name: "Ana López",
    student_email: "ana@test.com",
    tutor: null,
    tutor_name: null,
    jurado: [],
    jurado_names: [],
    start_time: "10:00",
    duration_minutes: 30,
    order: id,
    ...overrides,
  };
}

// Day where VIEWER_TUTOR_ID is tutor (matching for tutor view)
const DAY_MINE_TUTOR: PresentationDay = {
  id: 1,
  date: "2026-05-10",
  notes: "",
  presentations: [
    makePresentation(1, { tutor: VIEWER_TUTOR_ID }),
  ],
};

// Day where VIEWER_JURADO_ID is in jurado array (matching for jurado view)
const DAY_MINE_JURADO: PresentationDay = {
  id: 2,
  date: "2026-05-17",
  notes: "",
  presentations: [
    makePresentation(2, { jurado: [VIEWER_JURADO_ID, 10] }),
  ],
};

// Day that does not match either viewer (different tutor, different jurado)
const DAY_OTHER: PresentationDay = {
  id: 3,
  date: "2026-05-24",
  notes: "",
  presentations: [
    makePresentation(3, { tutor: 99, jurado: [88, 77] }),
  ],
};

const ALL_DAYS = [DAY_MINE_TUTOR, DAY_MINE_JURADO, DAY_OTHER];

// ── Tests ──────────────────────────────────────────────────────────────────────

describe("PlanReviewerView", () => {
  // 1 — Tutor copy: h1 contains "Mis defensas"; eyebrow contains tutor context
  it("renders h1 Mis defensas and tutor-specific eyebrow for reviewerKind=tutor", () => {
    render(
      <PlanReviewerView
        days={ALL_DAYS}
        loading={false}
        reviewerKind="tutor"
        viewerId={VIEWER_TUTOR_ID}
        viewerName="P. Linares"
      />
    );

    const h1 = document.querySelector("h1");
    expect(h1).not.toBeNull();
    expect(h1!.textContent).toMatch(/mis defensas/i);

    const eyebrow = document.querySelector(".hero-eyebrow");
    expect(eyebrow).not.toBeNull();
    expect(eyebrow!.textContent).toMatch(/tutor[íi]as/i);
  });

  // 2 — Jurado copy: h1 contains "Defensas asignadas"; eyebrow contains "asignaciones"
  it("renders h1 Defensas asignadas and asignaciones eyebrow for reviewerKind=jurado", () => {
    render(
      <PlanReviewerView
        days={ALL_DAYS}
        loading={false}
        reviewerKind="jurado"
        viewerId={VIEWER_JURADO_ID}
        viewerName="R. Linares"
      />
    );

    const h1 = document.querySelector("h1");
    expect(h1).not.toBeNull();
    expect(h1!.textContent).toMatch(/defensas asignadas/i);

    const eyebrow = document.querySelector(".hero-eyebrow");
    expect(eyebrow).not.toBeNull();
    expect(eyebrow!.textContent).toMatch(/asignaciones/i);
  });

  // 3 — Filters presentations: only viewer's own rows rendered
  it("renders only the matching .prow when viewer is tutor and days contain mixed assignments", () => {
    render(
      <PlanReviewerView
        days={ALL_DAYS}
        loading={false}
        reviewerKind="tutor"
        viewerId={VIEWER_TUTOR_ID}
      />
    );

    const rows = document.querySelectorAll(".prow");
    // DAY_MINE_TUTOR has 1 presentation with tutor=VIEWER_TUTOR_ID
    // DAY_MINE_JURADO and DAY_OTHER should be filtered out for tutor view
    expect(rows.length).toBe(1);
    expect(rows[0].textContent).toContain("Proyecto 1");
  });

  // 4 — Calendar mode toggle hidden: no "Crear días" button
  it("does not render a Crear días button for reviewer (allowCreate is false)", () => {
    render(
      <PlanReviewerView
        days={ALL_DAYS}
        loading={false}
        reviewerKind="tutor"
        viewerId={VIEWER_TUTOR_ID}
      />
    );

    const buttons = Array.from(document.querySelectorAll("button"));
    const crearBtn = buttons.find((b) => b.textContent?.match(/crear d[íi]as/i));
    expect(crearBtn).toBeUndefined();
  });

  // 5 — Empty state when no matching days
  it("renders an empty-state element with sin defensas text when no days match the viewer", () => {
    render(
      <PlanReviewerView
        days={[DAY_OTHER]}
        loading={false}
        reviewerKind="tutor"
        viewerId={VIEWER_TUTOR_ID}
      />
    );

    const emptyState = document.querySelector(".empty-state");
    expect(emptyState).not.toBeNull();
    expect(emptyState!.textContent).toMatch(/sin defensas/i);
  });
});
