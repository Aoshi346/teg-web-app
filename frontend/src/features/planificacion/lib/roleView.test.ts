import { describe, it, expect } from "vitest";
import { planificacionRoleView } from "./roleView";

describe("planificacionRoleView", () => {
  it('maps "Administrador" to "admin"', () => {
    expect(planificacionRoleView("Administrador")).toBe("admin");
  });

  it('maps "Tutor" to "reviewer"', () => {
    expect(planificacionRoleView("Tutor")).toBe("reviewer");
  });

  it('maps "Jurado" to "reviewer"', () => {
    expect(planificacionRoleView("Jurado")).toBe("reviewer");
  });

  it('maps "Estudiante" to "student"', () => {
    expect(planificacionRoleView("Estudiante")).toBe("student");
  });

  it("unknown role falls back to admin (safe default — shows most content, no destructive side effects)", () => {
    // Rationale: an unknown/empty role should degrade to the broadest read-only
    // view rather than hiding useful content or throwing. Admin is read-only on
    // the calendar in view mode, so this is safe.
    expect(planificacionRoleView("UnknownRole")).toBe("admin");
  });

  it("empty string role falls back to admin", () => {
    expect(planificacionRoleView("")).toBe("admin");
  });

  it("undefined role falls back to admin", () => {
    expect(planificacionRoleView(undefined as unknown as string)).toBe("admin");
  });

  it("accepts an optional viewerId without throwing", () => {
    // viewerId is part of the signature for call-site symmetry with filterPresentationsForRole
    // but is unused by the role-mapping logic itself.
    expect(() => planificacionRoleView("Tutor", 42)).not.toThrow();
    expect(planificacionRoleView("Tutor", 42)).toBe("reviewer");
  });

  it("omitting viewerId does not throw", () => {
    expect(() => planificacionRoleView("Administrador")).not.toThrow();
  });
});
