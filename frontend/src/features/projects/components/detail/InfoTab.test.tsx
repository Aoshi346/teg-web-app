import { describe, it, expect } from "vitest";
import { render, screen } from "@testing-library/react";
import { InfoTab } from "./InfoTab";
import type { Project } from "@features/projects/types/project";

function p(overrides: Partial<Project> = {}): Project {
  return {
    id: 2,
    title: "Plataforma de tutorías",
    student: "Ana Trujillo",
    submittedDate: "2026-04-14",
    state: "pending_defense",
    period: "2026-01",
    type: "proyecto",
    files: [
      { name: "tesis.pdf", url: "/x.pdf", type: "pdf",  date: "2026-04-14" },
      { name: "doc.docx",  url: "/x.docx", type: "word", date: "2026-04-14" },
    ],
    ...overrides,
  } as Project;
}

describe("InfoTab", () => {
  it("renders project description from the lede prop", () => {
    render(<InfoTab project={p()} description="Una descripción larga del proyecto." />);
    expect(screen.getByText(/descripción larga/i)).toBeTruthy();
  });

  it("renders attached files in a grid", () => {
    render(<InfoTab project={p()} description="" />);
    expect(screen.getByText("tesis.pdf")).toBeTruthy();
    expect(screen.getByText("doc.docx")).toBeTruthy();
  });

  it("renders project meta in the right rail", () => {
    render(<InfoTab project={p()} description="" />);
    expect(screen.getByText("2026-01")).toBeTruthy();
    expect(screen.getByText("Proyecto (PTEG)")).toBeTruthy();
  });

  it("falls back to 'Sin descripción registrada' when description is empty", () => {
    render(<InfoTab project={p()} description="" />);
    expect(screen.getByText(/Sin descripción registrada/i)).toBeTruthy();
  });
});
