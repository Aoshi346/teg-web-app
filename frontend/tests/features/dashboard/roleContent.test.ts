import { describe, it, expect } from "vitest";
import { buildDashboardContent } from "@features/dashboard/lib/roleContent";
import type { Project } from "@features/projects/types/project";

const proj = (overrides: Partial<Project>): Project => ({
  id: 1,
  title: "P",
  student: "Ana Perez",
  submittedDate: "2026-04-01",
  status: "pending",
  state: "pending_review_1",
  period: "2026-01",
  type: "proyecto",
  ...overrides,
});

describe("buildDashboardContent — Administrador", () => {
  it("returns two stat tiles and pending list", () => {
    const projects = [
      proj({ id: 1, type: "proyecto", status: "pending" }),
      proj({ id: 2, type: "proyecto", status: "checked" }),
      proj({ id: 3, type: "tesis", status: "pending" }),
    ];
    const result = buildDashboardContent({
      role: "Administrador",
      user: null,
      semester: "2026-01",
      projects,
    });
    expect(result.stats).toHaveLength(2);
    expect(result.stats[0].label).toMatch(/PTEG/i);
    expect(result.stats[0].value).toBe("2");
    expect(result.stats[1].label).toMatch(/TEG/i);
    expect(result.stats[1].value).toBe("1");
    expect(result.listItems.length).toBeGreaterThan(0);
  });

  it("filters projects to active semester only", () => {
    const projects = [
      proj({ id: 1, period: "2026-01", type: "proyecto" }),
      proj({ id: 2, period: "2025-02", type: "proyecto" }),
    ];
    const result = buildDashboardContent({
      role: "Administrador",
      user: null,
      semester: "2026-01",
      projects,
    });
    expect(result.stats[0].value).toBe("1");
  });
});

describe("buildDashboardContent — Estudiante", () => {
  it("returns single-tile view for PTEG student", () => {
    const user = { role: "Estudiante", semester: "9no" } as unknown as { role: string; semester: string };
    const myProject = proj({ id: 10, title: "Mi PTEG", type: "proyecto", status: "pending" });
    const result = buildDashboardContent({
      role: "Estudiante",
      user,
      semester: "2026-01",
      projects: [myProject],
    });
    expect(result.stats).toHaveLength(1);
    expect(result.stats[0].tone).toBe("primary");
    expect(result.listItems).toHaveLength(1);
    expect(result.listItems[0].title).toBe("Mi PTEG");
  });

  it("shows empty state when student has no project this semester", () => {
    const user = { role: "Estudiante", semester: "9no" } as unknown as { role: string; semester: string };
    const result = buildDashboardContent({
      role: "Estudiante",
      user,
      semester: "2026-01",
      projects: [],
    });
    expect(result.listItems).toHaveLength(0);
    expect(result.listEmpty.text).toMatch(/sin proyectos/i);
  });
});

describe("buildDashboardContent — Jurado", () => {
  it("counts evaluations by current reviewer and upcoming panels", () => {
    const user = { role: "Jurado", id: 7 } as unknown as { role: string; id: number };
    const projects = [
      proj({ id: 1, type: "proyecto", period: "2026-01" }),
      proj({ id: 2, type: "tesis", period: "2026-01" }),
    ];
    const evaluations = [
      { id: 100, projectId: 1, reviewerId: 7, period: "2026-01" },
      { id: 101, projectId: 2, reviewerId: 7, period: "2026-01" },
      { id: 102, projectId: 1, reviewerId: 9, period: "2026-01" },
    ];
    const presentations = [
      { id: 500, projectTitle: "Defensa A", date: "2026-05-01", jurorIds: [7] },
      { id: 501, projectTitle: "Defensa B", date: "2026-05-02", jurorIds: [8] },
    ];

    const result = buildDashboardContent({
      role: "Jurado",
      user,
      semester: "2026-01",
      projects,
      evaluations,
      presentations,
    });
    expect(result.stats[0].label).toMatch(/evaluadas/i);
    expect(result.stats[0].value).toBe("2");
    expect(result.stats[1].label).toMatch(/panel/i);
    expect(result.stats[1].value).toBe("1");
    expect(result.listItems.some((r) => r.title.includes("Defensa A"))).toBe(true);
  });

  it("renders em-dash when evaluations array is undefined", () => {
    const user = { role: "Jurado", id: 7 } as unknown as { role: string; id: number };
    const result = buildDashboardContent({
      role: "Jurado",
      user,
      semester: "2026-01",
      projects: [],
      evaluations: undefined,
      presentations: [],
    });
    expect(result.stats[0].value).toBe("—");
  });

  it("uses assignedProjectsCount when provided, skipping em-dash fallback", () => {
    const user = { role: "Jurado", id: 7 } as unknown as { role: string; id: number };
    const result = buildDashboardContent({
      role: "Jurado",
      user,
      semester: "2026-01",
      projects: [],
      evaluations: undefined,
      presentations: [],
      assignedProjectsCount: 4,
    });
    expect(result.stats[0].value).toBe("4");
  });
});

describe("buildDashboardContent — Tutor", () => {
  it("shows only advised projects in stats and list", () => {
    const user = { role: "Tutor", id: 42 } as unknown as { role: string; id: number };
    const projects = [
      proj({ id: 1, type: "proyecto", status: "pending", advisors: [42] }),
      proj({ id: 2, type: "tesis", status: "pending", advisors: [42] }),
      proj({ id: 3, type: "proyecto", status: "pending", advisors: [99] }),
    ];
    const result = buildDashboardContent({
      role: "Tutor",
      user,
      semester: "2026-01",
      projects,
    });
    expect(result.stats[0].value).toBe("1");
    expect(result.stats[1].value).toBe("1");
    expect(result.listItems.every((r) => r.id === 1 || r.id === 2)).toBe(true);
  });
});
