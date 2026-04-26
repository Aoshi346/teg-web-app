import { describe, it, expect } from "vitest";
import { render, screen } from "@testing-library/react";
import { DetailHero } from "./DetailHero";
import type { Project } from "@features/projects/types/project";

function p(overrides: Partial<Project> = {}): Project {
  return {
    id: 2,
    title: "Plataforma de tutorías",
    student: "Ana Trujillo",
    advisorNames: ["prof. Méndez"],
    reviewerName: "prof. Lozada",
    submittedDate: "2026-04-14",
    state: "pending_defense",
    period: "2026-01",
    type: "proyecto",
    ...overrides,
  } as Project;
}

describe("DetailHero", () => {
  it("renders the breadcrumb with project title", () => {
    render(<DetailHero project={p()} role="Jurado" viewerId={99} />);
    expect(screen.getAllByText(/Plataforma de tutorías/).length).toBeGreaterThan(0);
  });

  it("renders student / tutor / jurado meta", () => {
    render(<DetailHero project={p()} role="Jurado" viewerId={99} />);
    expect(screen.getByText("Ana Trujillo")).toBeTruthy();
    expect(screen.getByText("prof. Méndez")).toBeTruthy();
    expect(screen.getByText("prof. Lozada")).toBeTruthy();
  });

  it("shows the lifecycle ladder for PTEG", () => {
    const { container } = render(<DetailHero project={p()} role="Jurado" />);
    expect(container.textContent).toContain("Rev 1");
    expect(container.textContent).toContain("Defensa");
    expect(container.textContent).toContain("Aprobado");
  });

  it("shows 'Pendiente defensa' state in the right rail for pending_defense", () => {
    render(<DetailHero project={p()} role="Jurado" />);
    expect(screen.getByText(/Pendiente defensa/i)).toBeTruthy();
  });

  it("hides 'Forzar estado' button for non-admins", () => {
    render(<DetailHero project={p()} role="Estudiante" />);
    expect(screen.queryByText(/Forzar estado/i)).toBeNull();
  });

  it("shows 'Forzar estado' button for admin", () => {
    render(<DetailHero project={p()} role="Administrador" onOverrideClick={() => {}} />);
    expect(screen.getByText(/Forzar estado/i)).toBeTruthy();
  });
});
