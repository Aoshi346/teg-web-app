import { describe, it, expect } from "vitest";
import { render, screen } from "@testing-library/react";
import { HistoryTab } from "./HistoryTab";
import type { Project } from "@features/projects/types/project";

function p(overrides: Partial<Project> = {}): Project {
  return {
    id: 2, title: "T", student: "Ana",
    submittedDate: "2026-03-14T16:22:00Z",
    state: "pending_defense",
    period: "2026-01", type: "proyecto",
    stateOverrides: [
      { id: 1, fromState: "pending_review_2", toState: "pending_defense", reason: "Razón con suficiente longitud", adminName: "prof. Méndez", createdAt: "2026-04-02T14:18:00Z" },
    ],
    ...overrides,
  } as Project;
}

describe("HistoryTab", () => {
  it("renders the override callout when overrides exist", () => {
    render(<HistoryTab project={p()} evaluations={[]} role="Administrador" />);
    expect(screen.getAllByText(/forzó/i).length).toBeGreaterThan(0);
    expect(screen.getAllByText(/prof. Méndez/).length).toBeGreaterThan(0);
  });

  it("does not render the override callout when no overrides", () => {
    render(<HistoryTab project={p({ stateOverrides: [] })} evaluations={[]} role="Administrador" />);
    expect(screen.queryByText(/forzó/i)).toBeNull();
  });

  it("renders the StateTimeline with at least the creation event", () => {
    const { container } = render(<HistoryTab project={p({ stateOverrides: [] })} evaluations={[]} role="Estudiante" />);
    expect(container.querySelector(".tline")).not.toBeNull();
    expect(container.querySelectorAll(".tline-item").length).toBeGreaterThan(0);
  });

  it("hides the override callout from non-admins (no overrides field surfaced)", () => {
    render(<HistoryTab project={p({ stateOverrides: undefined })} evaluations={[]} role="Estudiante" />);
    expect(screen.queryByText(/forzó/i)).toBeNull();
  });
});
