import { describe, it, expect } from "vitest";
import { render, screen } from "@testing-library/react";
import ProjectCard from "./ProjectCard";
import type { Project } from "@features/projects/types/project";

function p(overrides: Partial<Project> = {}): Project {
  return {
    id: 1,
    title: "Proyecto de prueba con título suficientemente largo",
    student: "Marina Rodríguez",
    advisorNames: ["prof. Jiménez"],
    submittedDate: "2026-04-12",
    state: "pending_review_1",
    period: "2026-01",
    type: "proyecto",
    reviewer: 99,
    ...overrides,
  } as Project;
}

describe("ProjectCard (v5)", () => {
  it("renders the StatePill with the correct label", () => {
    render(<ProjectCard project={p()} role="Jurado" viewerId={99} />);
    expect(screen.getByText("Rev 1")).toBeTruthy();
  });

  it("renders the title and a single person line", () => {
    render(<ProjectCard project={p()} role="Jurado" viewerId={99} />);
    expect(screen.getByText(/título suficientemente largo/)).toBeTruthy();
    expect(screen.getByText("Marina Rodríguez")).toBeTruthy();
    expect(screen.getByText("prof. Jiménez")).toBeTruthy();
  });

  it("shows 'Revisar' for a Jurado on their assigned PTEG pending_review_1", () => {
    render(<ProjectCard project={p()} role="Jurado" viewerId={99} />);
    expect(screen.getByText("Revisar")).toBeTruthy();
  });

  it("shows 'Ver detalles' for an Estudiante", () => {
    render(<ProjectCard project={p()} role="Estudiante" />);
    expect(screen.getByText("Ver detalles")).toBeTruthy();
  });

  it("shows 'Ver evaluación' for an approved project", () => {
    render(<ProjectCard project={p({ state: "approved" })} role="Jurado" />);
    expect(screen.getByText("Ver evaluación")).toBeTruthy();
  });

  it("renders a ScoreGauge on approved cards when score is present", () => {
    const { container } = render(<ProjectCard project={p({ state: "approved", score: 18.4 })} role="Jurado" />);
    expect(container.querySelector(".gauge")).not.toBeNull();
  });

  it("renders the TEG phase bar for tesis cards", () => {
    const { container } = render(
      <ProjectCard project={p({ type: "tesis", state: "pending_entrega" })} role="Jurado" viewerId={99} />,
    );
    expect(container.querySelector(".tegbar")).not.toBeNull();
  });

  it("falls back to legacy primaryLabel/primaryHref when role is not provided", () => {
    render(
      <ProjectCard
        project={p()}
        primaryLabel="Custom action"
        primaryHref="/dashboard/custom"
      />,
    );
    expect(screen.getByText("Custom action")).toBeTruthy();
  });

  it("applies the state-tinted left edge class", () => {
    const { container } = render(<ProjectCard project={p({ state: "approved" })} role="Jurado" />);
    expect(container.querySelector(".pcard")?.className).toContain("pcard-green");
  });
});
