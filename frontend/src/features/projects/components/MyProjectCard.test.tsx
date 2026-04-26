import { describe, it, expect } from "vitest";
import { render, screen } from "@testing-library/react";
import MyProjectCard from "./MyProjectCard";
import type { Project } from "@features/projects/types/project";

// Factory for a minimal valid Project. Overrides let each test set state/type.
function makeProject(overrides: Partial<Project> = {}): Project {
  return {
    id: 42,
    title: "Mi proyecto de prueba",
    student: "Carlos González",
    type: "proyecto",
    state: "pending_review_1",
    advisorNames: ["Prof. Romero"],
    reviewerName: "Prof. Salazar",
    period: "2026-01",
    submittedDate: "2026-04-12",
    ...overrides,
  } as Project;
}

// DOM-traversal strategy for gate class assertions:
// Query .pgate elements directly and find the one whose text content matches
// the gate label. This avoids collisions with StatePill text (e.g. "Defensa"
// appears both as a gate label and as a StatePill badge).
function getGateEl(labelText: string): Element {
  const pgates = document.querySelectorAll(".pgate");
  const match = Array.from(pgates).find((el) =>
    new RegExp(labelText, "i").test(el.textContent || "")
  );
  if (!match) throw new Error(`Gate "${labelText}" not found`);
  return match;
}

describe("MyProjectCard — PTEG gates", () => {
  it("PTEG pending_review_1: 'Revisión 1' gate is now; others are neither now nor done", () => {
    const { container } = render(<MyProjectCard project={makeProject({ state: "pending_review_1" })} />);
    void container;

    const rev1 = getGateEl("Revisión 1");
    expect(rev1.classList.contains("now")).toBe(true);
    expect(rev1.classList.contains("done")).toBe(false);

    const reentrega = getGateEl("Reentrega");
    expect(reentrega.classList.contains("now")).toBe(false);
    expect(reentrega.classList.contains("done")).toBe(false);

    const defensa = getGateEl("Defensa");
    expect(defensa.classList.contains("now")).toBe(false);
    expect(defensa.classList.contains("done")).toBe(false);
  });

  it("PTEG pending_review_2: 'Revisión 1' is done; 'Reentrega' is now", () => {
    render(<MyProjectCard project={makeProject({ state: "pending_review_2" })} />);

    const rev1 = getGateEl("Revisión 1");
    expect(rev1.classList.contains("done")).toBe(true);
    expect(rev1.classList.contains("now")).toBe(false);

    const reentrega = getGateEl("Reentrega");
    expect(reentrega.classList.contains("now")).toBe(true);
    expect(reentrega.classList.contains("done")).toBe(false);
  });

  it("PTEG pending_defense: 'Revisión 1' and 'Reentrega' are done; 'Defensa' is now", () => {
    render(<MyProjectCard project={makeProject({ state: "pending_defense" })} />);

    expect(getGateEl("Revisión 1").classList.contains("done")).toBe(true);
    expect(getGateEl("Reentrega").classList.contains("done")).toBe(true);

    const defensa = getGateEl("Defensa");
    expect(defensa.classList.contains("now")).toBe(true);
    expect(defensa.classList.contains("done")).toBe(false);
  });
});

describe("MyProjectCard — TEG gates", () => {
  it("TEG pending_articulo: 'Artículo' is now; 'Entrega' and 'Defensa' are plain", () => {
    render(
      <MyProjectCard
        project={makeProject({ type: "tesis", state: "pending_articulo" })}
      />,
    );

    const articulo = getGateEl("Artículo");
    expect(articulo.classList.contains("now")).toBe(true);
    expect(articulo.classList.contains("done")).toBe(false);

    const entrega = getGateEl("Entrega");
    expect(entrega.classList.contains("now")).toBe(false);
    expect(entrega.classList.contains("done")).toBe(false);

    const defensa = getGateEl("Defensa");
    expect(defensa.classList.contains("now")).toBe(false);
    expect(defensa.classList.contains("done")).toBe(false);
  });

  it("TEG pending_entrega: 'Artículo' is done; 'Entrega' is now; 'Defensa' is plain", () => {
    render(
      <MyProjectCard
        project={makeProject({ type: "tesis", state: "pending_entrega" })}
      />,
    );

    expect(getGateEl("Artículo").classList.contains("done")).toBe(true);

    const entrega = getGateEl("Entrega");
    expect(entrega.classList.contains("now")).toBe(true);
    expect(entrega.classList.contains("done")).toBe(false);

    expect(getGateEl("Defensa").classList.contains("now")).toBe(false);
    expect(getGateEl("Defensa").classList.contains("done")).toBe(false);
  });
});

describe("MyProjectCard — terminal states", () => {
  it("PTEG approved: all 3 gates are done; 'Próximo paso' callout is NOT rendered", () => {
    render(<MyProjectCard project={makeProject({ state: "approved" })} />);

    expect(getGateEl("Revisión 1").classList.contains("done")).toBe(true);
    expect(getGateEl("Reentrega").classList.contains("done")).toBe(true);
    expect(getGateEl("Defensa").classList.contains("done")).toBe(true);

    expect(screen.queryByText(/próximo paso/i)).toBeNull();
  });

  it("PTEG failed_final: 'Próximo paso' callout is NOT rendered; fail pill is visible", () => {
    render(<MyProjectCard project={makeProject({ state: "failed_final" })} />);

    expect(screen.queryByText(/próximo paso/i)).toBeNull();

    // The fail pill from StatePill renders "Reprobado" (PTEG masculine).
    // Alternatively the component may add a class containing "spill-red" or "spill-fail".
    // We assert either the text OR the CSS class — the implementation can use StatePill.
    const failEl = screen.queryByText(/reprobado/i);
    const failClass = document.querySelector("[class*='spill-red'], [class*='spill-fail']");
    expect(failEl !== null || failClass !== null).toBe(true);
  });
});

describe("MyProjectCard — detail link routing", () => {
  it("PTEG card contains a link to /dashboard/proyectos/42", () => {
    const { container } = render(<MyProjectCard project={makeProject({ type: "proyecto", id: 42 })} />);
    const links = Array.from(container.querySelectorAll("a"));
    const match = links.find((a) => a.getAttribute("href") === "/dashboard/proyectos/42");
    expect(match).toBeTruthy();
  });

  it("TEG card contains a link to /dashboard/tesis/42", () => {
    const { container } = render(
      <MyProjectCard project={makeProject({ type: "tesis", id: 42, state: "pending_articulo" })} />,
    );
    const links = Array.from(container.querySelectorAll("a"));
    const match = links.find((a) => a.getAttribute("href") === "/dashboard/tesis/42");
    expect(match).toBeTruthy();
  });
});

describe("MyProjectCard — people and title", () => {
  it("renders the tutor name from advisorNames[0]", () => {
    render(<MyProjectCard project={makeProject({ advisorNames: ["Prof. Romero"] })} />);
    expect(screen.getByText("Prof. Romero")).toBeTruthy();
  });

  it("renders the jurado name from reviewerName", () => {
    render(<MyProjectCard project={makeProject({ reviewerName: "Prof. Salazar" })} />);
    expect(screen.getByText("Prof. Salazar")).toBeTruthy();
  });

  it("renders the project title as a heading", () => {
    render(<MyProjectCard project={makeProject({ title: "Mi proyecto de prueba" })} />);
    expect(screen.getByRole("heading", { name: /mi proyecto de prueba/i })).toBeTruthy();
  });
});
