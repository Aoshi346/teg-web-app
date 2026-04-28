/**
 * Tests for EvaluarTesisDefensaPage — Phase C RED
 *
 * CONTRACT DEPENDENCY (frontend-worker must satisfy):
 *   Create frontend/src/app/dashboard/tesis/[id]/evaluar/defensa/page.tsx with:
 *   - Default export `EvaluarTesisDefensaPage`
 *   - Renders `EvaluationForm` with kind="defense", projectState="pending_defensa",
 *     questions={TEG_DEFENSA_QUESTIONS}
 *   - Renders a "Volver" back button
 *   - Renders `DashboardHeader`
 */

import React from "react";
import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen } from "@testing-library/react";

// ── navigation mock ────────────────────────────────────────────────────────────
vi.mock("next/navigation", () => ({
  useRouter: () => ({ push: vi.fn(), back: vi.fn() }),
  useParams: () => ({ id: "7" }),
}));

// ── project service mock ───────────────────────────────────────────────────────
vi.mock("@features/projects/api/projectService", () => ({
  getProject: vi.fn().mockResolvedValue({
    id: 7,
    title: "Mi Tesis",
    student: "Estudiante",
    submittedDate: "2026-01-01",
    state: "pending_defensa",
    period: "2026-01",
    type: "tesis",
  }),
  createEvaluation: vi.fn().mockResolvedValue({ id: 1 }),
}));

// ── header stub ───────────────────────────────────────────────────────────────
vi.mock("@widgets/header/DashboardHeader", () => ({
  default: ({ pageTitle }: { pageTitle: string }) => (
    <header data-testid="dashboard-header">{pageTitle}</header>
  ),
}));

// ── Capture EvaluationForm props via mock ─────────────────────────────────────
let capturedFormProps: Record<string, unknown> | null = null;

vi.mock("@features/evaluations/components/EvaluationForm", () => ({
  default: (props: Record<string, unknown>) => {
    capturedFormProps = props;
    // Render at least one question label so the DOM-text tests pass
    const questions = (props.questions as Array<{ id: string; label: string }>) ?? [];
    return (
      <div data-testid="evaluation-form">
        {questions.map((q) => (
          <span key={q.id}>{q.label}</span>
        ))}
      </div>
    );
  },
}));

// ── component under test ───────────────────────────────────────────────────────
// This import will fail in RED phase because the file doesn't exist yet.
import EvaluarTesisDefensaPage from "../page";
import { TEG_DEFENSA_QUESTIONS } from "@features/evaluations/lib/questions/questions";

// ── tests ──────────────────────────────────────────────────────────────────────

describe("EvaluarTesisDefensaPage", () => {
  beforeEach(() => {
    capturedFormProps = null;
  });

  it("renders without crashing when params.id is '7'", () => {
    const params = Promise.resolve({ id: "7" });
    expect(() => render(<EvaluarTesisDefensaPage params={params} />)).not.toThrow();
  });

  it("renders the DashboardHeader", () => {
    const params = Promise.resolve({ id: "7" });
    render(<EvaluarTesisDefensaPage params={params} />);
    expect(screen.getByTestId("dashboard-header")).toBeTruthy();
  });

  it("renders a Volver back button", () => {
    const params = Promise.resolve({ id: "7" });
    render(<EvaluarTesisDefensaPage params={params} />);
    const btn = screen.getByRole("button", { name: /volver/i });
    expect(btn).toBeTruthy();
  });

  it("passes kind='defense' to EvaluationForm", () => {
    const params = Promise.resolve({ id: "7" });
    render(<EvaluarTesisDefensaPage params={params} />);
    expect(capturedFormProps).not.toBeNull();
    expect(capturedFormProps!.kind).toBe("defense");
  });

  it("passes projectState='pending_defensa' to EvaluationForm", () => {
    const params = Promise.resolve({ id: "7" });
    render(<EvaluarTesisDefensaPage params={params} />);
    expect(capturedFormProps).not.toBeNull();
    expect(capturedFormProps!.projectState).toBe("pending_defensa");
  });

  it("passes TEG_DEFENSA_QUESTIONS to EvaluationForm", () => {
    const params = Promise.resolve({ id: "7" });
    render(<EvaluarTesisDefensaPage params={params} />);
    expect(capturedFormProps).not.toBeNull();
    expect(capturedFormProps!.questions).toEqual(TEG_DEFENSA_QUESTIONS);
  });

  it("renders at least one TEG_DEFENSA_QUESTIONS text fragment (td-div1: dicción)", () => {
    const params = Promise.resolve({ id: "7" });
    render(<EvaluarTesisDefensaPage params={params} />);
    // td-div1: "Adecuada dicción, vocabulario, tono de voz, postura y lenguaje corporal, contacto visual"
    const el = screen.queryByText(/dicción/i);
    expect(el).not.toBeNull();
  });

  it("renders a question from the Técnica section (td-tech3: Antecedentes)", () => {
    const params = Promise.resolve({ id: "7" });
    render(<EvaluarTesisDefensaPage params={params} />);
    // td-tech3 label: "Antecedentes."
    const el = screen.queryByText(/Antecedentes\./);
    expect(el).not.toBeNull();
  });
});
