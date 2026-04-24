import { describe, it, expect } from "vitest";
import { buildDashboardContent } from "@features/dashboard/lib/roleContent";
import type { Project } from "@features/projects/types/project";

const baseProject = (over: Partial<Project>): Project => ({
  id: 1,
  title: "P",
  student: "S",
  submittedDate: "2026-01-01",
  status: "pending",
  state: "pending_review_1",
  score: 0,
  diagramacionScore: 0,
  contenidoScore: 0,
  stage1Passed: false,
  period: "2026-01",
  type: "proyecto",
  files: [],
  failedAttempts: 0,
  ...over,
});

describe("Sub-D role tiles — Administrador", () => {
  it("emits 4 tiles: hero PTEG with chips + TEG + defensas + tu acción", () => {
    const projects = [
      baseProject({ id: 1, type: "proyecto", state: "pending_review_1", status: "pending" }),
      baseProject({ id: 2, type: "proyecto", state: "pending_defense", status: "pending" }),
      baseProject({ id: 3, type: "proyecto", state: "approved", status: "checked" }),
      baseProject({ id: 4, type: "tesis", status: "checked" }),
    ];
    const c = buildDashboardContent({
      role: "Administrador",
      user: { role: "Administrador", id: 99 },
      semester: "2026-01",
      projects,
    });
    expect(c.stats.length).toBe(4);
    expect(c.stats[0].tone).toBe("hero");
    expect(c.stats[0].label).toMatch(/PTEG/i);
    expect(c.stats[0].chips).toBeDefined();
    expect(c.stats[0].chips!.length).toBeGreaterThan(0);
    expect(c.stats[1].label).toMatch(/TEG/i);
    expect(c.stats[2].label).toMatch(/Defensas/i);
    expect(c.stats[2].value).toBe("1");
    expect(c.stats[3].urgent).toBe(true);
  });

  it("filters projects to active semester only", () => {
    const projects = [
      baseProject({ id: 1, period: "2026-01", type: "proyecto" }),
      baseProject({ id: 2, period: "2025-02", type: "proyecto" }),
    ];
    const c = buildDashboardContent({
      role: "Administrador",
      user: null,
      semester: "2026-01",
      projects,
    });
    expect(c.stats[0].value).toBe("1");
  });

  it("admin chips link to /dashboard/proyectos?state=<state>", () => {
    const c = buildDashboardContent({
      role: "Administrador",
      user: null,
      semester: "2026-01",
      projects: [baseProject({ id: 11, type: "proyecto", state: "pending_defense" })],
    });
    const chip = c.stats[0].chips?.[0];
    expect(chip?.href).toBe("/dashboard/proyectos?state=pending_defense");
  });

  it("emits 3 semesterStats", () => {
    const c = buildDashboardContent({
      role: "Administrador",
      user: { role: "Administrador", id: 99 },
      semester: "2026-01",
      projects: [],
    });
    expect(c.semesterStats?.length).toBe(3);
  });
});

describe("Sub-D role tiles — Tutor", () => {
  it("emits 4 tiles with hero chips + atención (urgent) + aprobados + defensas", () => {
    const projects = [
      baseProject({ id: 1, type: "proyecto", advisors: [10], status: "pending" }),
      baseProject({ id: 2, type: "tesis", advisors: [10], status: "checked" }),
      baseProject({ id: 3, type: "proyecto", advisors: [10], status: "rejected" }),
    ];
    const c = buildDashboardContent({
      role: "Tutor",
      user: { role: "Tutor", id: 10 },
      semester: "2026-01",
      projects,
    });
    expect(c.stats.length).toBe(4);
    expect(c.stats[0].tone).toBe("hero");
    expect(c.stats[0].chips).toBeDefined();
    expect(c.stats[1].label).toMatch(/Atención/i);
    expect(c.stats[1].urgent).toBe(true);
    expect(c.stats[2].label).toMatch(/Aprobados/i);
    expect(c.stats[3].label).toMatch(/Defensas/i);
    expect(c.stats.find((s) => /Comentarios/i.test(s.label))).toBeUndefined();
  });

  it("only counts advisor's own projects", () => {
    const projects = [
      baseProject({ id: 1, type: "proyecto", advisors: [10], status: "pending" }),
      baseProject({ id: 2, type: "proyecto", advisors: [99], status: "pending" }),
    ];
    const c = buildDashboardContent({
      role: "Tutor",
      user: { role: "Tutor", id: 10 },
      semester: "2026-01",
      projects,
    });
    expect(c.stats[0].value).toBe("1");
  });
});

describe("Sub-D role tiles — Jurado", () => {
  it("emits hero asignados + por evaluar (urgent) + evaluadas + defensas", () => {
    const projects = [
      baseProject({ id: 1, status: "pending", state: "pending_review_1" }),
      baseProject({ id: 2, status: "pending", state: "pending_review_2" }),
      baseProject({ id: 3, status: "pending", state: "pending_defense" }),
      baseProject({ id: 4, status: "checked", state: "approved" }),
    ];
    const c = buildDashboardContent({
      role: "Jurado",
      user: { role: "Jurado", id: 7 },
      semester: "2026-01",
      projects,
      assignedProjectsCount: 4,
    });
    expect(c.stats.length).toBe(4);
    expect(c.stats[0].tone).toBe("hero");
    expect(c.stats[0].label).toMatch(/asignados/i);
    expect(c.stats[1].urgent).toBe(true);
    expect(c.stats[1].label).toMatch(/Por evaluar/i);
    expect(c.stats[2].label).toMatch(/Evaluadas/i);
    expect(c.stats[3].label).toMatch(/Defensas/i);
  });

  it("uses assignedProjectsCount when provided for hero value", () => {
    const c = buildDashboardContent({
      role: "Jurado",
      user: { role: "Jurado", id: 7 },
      semester: "2026-01",
      projects: [],
      assignedProjectsCount: 4,
    });
    expect(c.stats[0].value).toBe("4");
  });
});

describe("Sub-D role tiles — Estudiante", () => {
  it("emits hero state tile + 3 secondary tiles", () => {
    const projects = [
      baseProject({
        id: 1,
        type: "proyecto",
        state: "pending_review_1",
        status: "pending",
        student: "Yo",
      }),
    ];
    const c = buildDashboardContent({
      role: "Estudiante",
      user: { role: "Estudiante", id: 99 },
      semester: "2026-01",
      projects,
    });
    expect(c.stats.length).toBe(4);
    expect(c.stats[0].tone).toBe("hero");
    expect(c.stats[0].label).toMatch(/PTEG/i);
    expect(c.stats[1].label).toMatch(/Entregas/i);
    expect(c.stats[2].label).toMatch(/Notas|Comentarios/i);
    expect(c.stats[3].label).toMatch(/Días/i);
  });

  it("shows empty state when student has no project this semester", () => {
    const c = buildDashboardContent({
      role: "Estudiante",
      user: { role: "Estudiante", semester: "9no" },
      semester: "2026-01",
      projects: [],
    });
    expect(c.listItems).toHaveLength(0);
    expect(c.listEmpty.text).toMatch(/sin proyectos/i);
  });
});

describe("Sub-D — PTEG student hint from state", () => {
  const basePTEG = (state: Project["state"], status: Project["status"] = "pending") =>
    baseProject({
      id: 42,
      title: "Mi proyecto",
      student: "Alice",
      type: "proyecto",
      status,
      period: "2026-01",
      submittedDate: "2026-01-15",
      state,
    });

  it("shows espera hint for pending_review_1", () => {
    const c = buildDashboardContent({
      role: "Estudiante",
      user: { role: "Estudiante", id: 1, semester: "9no" },
      semester: "2026-01",
      projects: [basePTEG("pending_review_1")],
    });
    expect(c.listItems[0].hint).toMatch(/espera|pendiente/i);
  });

  it("shows retry hint for pending_review_2", () => {
    const c = buildDashboardContent({
      role: "Estudiante",
      user: { role: "Estudiante", id: 1, semester: "9no" },
      semester: "2026-01",
      projects: [basePTEG("pending_review_2")],
    });
    expect(c.listItems[0].hint).toMatch(/intento 2|corrige/i);
  });

  it("shows defense hint for pending_defense", () => {
    const c = buildDashboardContent({
      role: "Estudiante",
      user: { role: "Estudiante", id: 1, semester: "9no" },
      semester: "2026-01",
      projects: [basePTEG("pending_defense")],
    });
    expect(c.listItems[0].hint).toMatch(/defensa/i);
  });

  it("shows approved hint for approved", () => {
    const c = buildDashboardContent({
      role: "Estudiante",
      user: { role: "Estudiante", id: 1, semester: "9no" },
      semester: "2026-01",
      projects: [basePTEG("approved", "checked")],
    });
    expect(c.listItems[0].hint).toMatch(/aprobad|listo/i);
  });

  it("shows no-more-attempts hint for failed_final", () => {
    const c = buildDashboardContent({
      role: "Estudiante",
      user: { role: "Estudiante", id: 1, semester: "9no" },
      semester: "2026-01",
      projects: [basePTEG("failed_final", "rejected")],
    });
    expect(c.listItems[0].hint).toMatch(/sin más|no hay más|reprobado/i);
  });
});
