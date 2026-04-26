import { describe, it, expect } from "vitest";
import { render, screen } from "@testing-library/react";
import { EvaluationsTab, type DetailEvaluation } from "./EvaluationsTab";

const e1: DetailEvaluation = {
  id: 1, kind: "review", pass_status: "Pass", score: 17.2,
  graded_at: "2026-03-28T11:02:00Z", reviewer_name: "prof. Lozada",
  comments: { general: "Buen trabajo." },
  section_scores: { diagramacion: 4.4, contenido: 12.8, total: 17.2 },
};
const e2: DetailEvaluation = {
  id: 2, kind: "review", pass_status: "Pass", score: 18.0,
  graded_at: "2026-04-10T14:18:00Z", reviewer_name: "prof. Lozada",
  comments: { general: "Mejoras notables." },
  section_scores: { diagramacion: 4.8, contenido: 13.2, total: 18.0 },
};

describe("EvaluationsTab", () => {
  it("shows aggregate score (mean of scores)", () => {
    render(<EvaluationsTab evaluations={[e1, e2]} />);
    expect(screen.getByText("17.6 / 20")).toBeTruthy();
  });

  it("renders each evaluation in a card with reviewer + score", () => {
    render(<EvaluationsTab evaluations={[e1, e2]} />);
    expect(screen.getAllByText("prof. Lozada")).toHaveLength(2);
    expect(screen.getByText("18.0")).toBeTruthy();
    expect(screen.getByText("17.2")).toBeTruthy();
  });

  it("shows the empty state when no evaluations", () => {
    render(<EvaluationsTab evaluations={[]} />);
    expect(screen.getByText(/Sin evaluaciones todavía/i)).toBeTruthy();
  });

  it("renders evaluation comments", () => {
    render(<EvaluationsTab evaluations={[e1, e2]} />);
    expect(screen.getByText(/Mejoras notables/)).toBeTruthy();
    expect(screen.getByText(/Buen trabajo/)).toBeTruthy();
  });
});
