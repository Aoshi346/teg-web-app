import React from "react";
import { describe, it, expect } from "vitest";
import { render } from "@testing-library/react";
import PlanStudentView from "./PlanStudentView";
import type { PresentationDay, Presentation } from "../types/planificacion";

// ── Fixtures ──────────────────────────────────────────────────────────────────

const VIEWER_EMAIL = "ana@test.com";
const OTHER_EMAIL = "pedro@test.com";

function makePresentation(id: number, overrides: Partial<Presentation> = {}): Presentation {
  return {
    id,
    day: 1,
    project: id + 100,
    project_title: `Sistema de Análisis de Datos Académicos ${id}`,
    project_type: "proyecto",
    student_name: "Ana López",
    student_email: VIEWER_EMAIL,
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

// Day with viewer's TEG presentation
const DAY_WITH_MINE: PresentationDay = {
  id: 1,
  date: "2026-05-10",
  notes: "",
  presentations: [
    makePresentation(1, { project_type: "tesis", student_email: VIEWER_EMAIL }),
  ],
};

// Day with another student's presentation only
const DAY_OTHER_STUDENT: PresentationDay = {
  id: 2,
  date: "2026-05-17",
  notes: "",
  presentations: [
    makePresentation(2, { student_email: OTHER_EMAIL }),
  ],
};

// ── Tests ──────────────────────────────────────────────────────────────────────

describe("PlanStudentView", () => {
  // 1 — Defense card when student is scheduled
  it("renders .mydef card with project title and date when viewer has a scheduled presentation", () => {
    render(
      <PlanStudentView
        days={[DAY_WITH_MINE, DAY_OTHER_STUDENT]}
        loading={false}
        viewerEmail={VIEWER_EMAIL}
      />
    );

    const mydef = document.querySelector(".mydef");
    expect(mydef).not.toBeNull();
    expect(mydef!.textContent).toContain("Sistema de Análisis de Datos Académicos 1");
    expect(mydef!.textContent).toContain("2026");
  });

  // 2 — Empty card when student is not scheduled
  it("renders .empty-card element with sin defensa programada when viewer has no scheduled presentation", () => {
    render(
      <PlanStudentView
        days={[DAY_OTHER_STUDENT]}
        loading={false}
        viewerEmail={VIEWER_EMAIL}
      />
    );

    const emptyCard = document.querySelector(".empty-card");
    expect(emptyCard).not.toBeNull();
    expect(emptyCard!.textContent).toMatch(/sin defensa programada/i);
  });

  // 3a — Hero copy when scheduled: h1 contains "Tu defensa está programada"
  it("renders h1 Tu defensa está programada when viewer has a scheduled presentation", () => {
    render(
      <PlanStudentView
        days={[DAY_WITH_MINE]}
        loading={false}
        viewerEmail={VIEWER_EMAIL}
      />
    );

    const h1 = document.querySelector("h1");
    expect(h1).not.toBeNull();
    expect(h1!.textContent).toMatch(/tu defensa est[áa] programada/i);
  });

  // 3b — Hero copy when not scheduled: h1 contains "Sin defensa programada"
  it("renders h1 Sin defensa programada when viewer has no scheduled presentation", () => {
    render(
      <PlanStudentView
        days={[DAY_OTHER_STUDENT]}
        loading={false}
        viewerEmail={VIEWER_EMAIL}
      />
    );

    const h1 = document.querySelector("h1");
    expect(h1).not.toBeNull();
    expect(h1!.textContent).toMatch(/sin defensa programada/i);
  });

  // 4 — Modality pill: .spill.teg chip with text TEG for a tesis presentation
  it("renders .spill.teg chip with text TEG inside .mydef for a tesis presentation", () => {
    render(
      <PlanStudentView
        days={[DAY_WITH_MINE]}
        loading={false}
        viewerEmail={VIEWER_EMAIL}
      />
    );

    const mydef = document.querySelector(".mydef");
    expect(mydef).not.toBeNull();

    const tegPill = mydef!.querySelector(".spill.teg");
    expect(tegPill).not.toBeNull();
    expect(tegPill!.textContent).toMatch(/^TEG$/i);
  });
});
