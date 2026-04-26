import { describe, it, expect } from "vitest";
import { cardAction } from "./cardAction";
import type { Project } from "@features/projects/types/project";

function mkProject(overrides: Partial<Project> = {}): Project {
  return {
    id: 1,
    title: "Test",
    student: "Alumno",
    submittedDate: "2026-04-12",
    state: "pending_review_1",
    period: "2026-01",
    type: "proyecto",
    reviewer: 99,
    ...overrides,
  } as Project;
}

describe("cardAction", () => {
  it("Jurado on PTEG pending_review_1 → Revisar (primary)", () => {
    const p = mkProject({ state: "pending_review_1" });
    expect(cardAction("Jurado", p)).toEqual({
      label: "Revisar",
      intent: "primary",
      href: "/dashboard/proyectos/1/evaluar",
    });
  });

  it("Jurado on PTEG pending_review_2 → Revisar (primary)", () => {
    const p = mkProject({ state: "pending_review_2" });
    expect(cardAction("Jurado", p).label).toBe("Revisar");
    expect(cardAction("Jurado", p).intent).toBe("primary");
  });

  it("Jurado on PTEG pending_defense → Evaluar defensa (primary)", () => {
    const p = mkProject({ state: "pending_defense" });
    expect(cardAction("Jurado", p).label).toBe("Evaluar defensa");
    expect(cardAction("Jurado", p).intent).toBe("primary");
  });

  it("Admin on TEG pending_articulo → Revisar artículo (primary)", () => {
    const p = mkProject({ type: "tesis", state: "pending_articulo" });
    expect(cardAction("Administrador", p).label).toBe("Revisar artículo");
    expect(cardAction("Administrador", p).href).toBe("/dashboard/tesis/1/evaluar/articulo");
  });

  it("Admin on TEG pending_entrega → Revisar entrega (primary)", () => {
    const p = mkProject({ type: "tesis", state: "pending_entrega" });
    expect(cardAction("Administrador", p).label).toBe("Revisar entrega");
    expect(cardAction("Administrador", p).href).toBe("/dashboard/tesis/1/evaluar/entrega");
  });

  it("Admin on TEG pending_defensa → Evaluar defensa (primary)", () => {
    const p = mkProject({ type: "tesis", state: "pending_defensa" });
    expect(cardAction("Administrador", p).label).toBe("Evaluar defensa");
    expect(cardAction("Administrador", p).href).toBe("/dashboard/tesis/1/evaluar/defensa");
  });

  it("Estudiante on own pending_review_1 → Ver detalles (muted)", () => {
    const p = mkProject({ state: "pending_review_1" });
    expect(cardAction("Estudiante", p).label).toBe("Ver detalles");
    expect(cardAction("Estudiante", p).intent).toBe("muted");
    expect(cardAction("Estudiante", p).href).toBe("/dashboard/proyectos/1");
  });

  it("Tutor on advised PTEG → Ver detalles (muted)", () => {
    const p = mkProject({ state: "pending_review_1" });
    expect(cardAction("Tutor", p).label).toBe("Ver detalles");
    expect(cardAction("Tutor", p).intent).toBe("muted");
  });

  it("any role on approved PTEG → Ver evaluación (muted)", () => {
    const p = mkProject({ state: "approved" });
    expect(cardAction("Jurado", p).label).toBe("Ver evaluación");
    expect(cardAction("Estudiante", p).label).toBe("Ver evaluación");
    expect(cardAction("Jurado", p).intent).toBe("muted");
  });

  it("any role on failed_final → Ver motivo (danger)", () => {
    const p = mkProject({ state: "failed_final" });
    expect(cardAction("Jurado", p).label).toBe("Ver motivo");
    expect(cardAction("Jurado", p).intent).toBe("danger");
  });

  it("Jurado on PTEG when not assigned as reviewer → Ver detalles (muted)", () => {
    const p = mkProject({ reviewer: 42, state: "pending_review_1" });
    expect(cardAction("Jurado", p, /* viewerId */ 99).label).toBe("Ver detalles");
    expect(cardAction("Jurado", p, 99).intent).toBe("muted");
  });

  it("Jurado on PTEG when assigned as reviewer → Revisar (primary)", () => {
    const p = mkProject({ reviewer: 99, state: "pending_review_1" });
    expect(cardAction("Jurado", p, 99).label).toBe("Revisar");
  });

  it("TEG href routes to /dashboard/tesis/...", () => {
    const p = mkProject({ id: 7, type: "tesis", state: "approved" });
    expect(cardAction("Estudiante", p).href).toBe("/dashboard/tesis/7");
  });
});
