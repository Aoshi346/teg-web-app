import { describe, it, expect } from "vitest";
import {
  applyPresentationFilters,
  countByModality,
  countForPeriod,
  isFiltersActive,
  DEFAULT_FILTERS,
} from "./applyPresentationFilters";
import type { PresentationDay, Presentation } from "../types/planificacion";

// ── Fixture ────────────────────────────────────────────────────────────────────
// 4 days spanning March 8–25 2026 with a mix of PTEG/TEG, varied names.

function makePresentation(id: number, overrides: Partial<Presentation> = {}): Presentation {
  return {
    id,
    day: 1,
    project: id + 100,
    project_title: `Project ${id}`,
    project_type: "proyecto",
    student_name: "Ana López",
    student_email: "ana@test.com",
    tutor: 5,
    tutor_name: "Carlos Méndez",
    jurado: [9, 10],
    jurado_names: ["Rosa Díaz", "Luis Herrera"],
    start_time: "10:00",
    duration_minutes: 30,
    order: id,
    ...overrides,
  };
}

// Day 1: 2026-03-08 — 2 PTEG
const DAY_MAR_08: PresentationDay = {
  id: 1,
  date: "2026-03-08",
  notes: "",
  presentations: [
    makePresentation(1, { project_type: "proyecto", project_title: "Sistema de Inventario", student_name: "Ana López", tutor_name: "Carlos Méndez" }),
    makePresentation(2, { project_type: "proyecto", project_title: "Plataforma Educativa", student_name: "Pedro Rojas", tutor_name: "María Torres" }),
  ],
};

// Day 2: 2026-03-12 — 1 PTEG + 1 TEG
const DAY_MAR_12: PresentationDay = {
  id: 2,
  date: "2026-03-12",
  notes: "",
  presentations: [
    makePresentation(3, { project_type: "proyecto", project_title: "App Móvil Salud", student_name: "Laura Gómez", tutor_name: "Jorge Ruiz" }),
    makePresentation(4, { project_type: "tesis", project_title: "Redes Neuronales Aplicadas", student_name: "Marco Vega", tutor_name: "Elena Pino" }),
  ],
};

// Day 3: 2026-03-18 — 2 TEG
const DAY_MAR_18: PresentationDay = {
  id: 3,
  date: "2026-03-18",
  notes: "",
  presentations: [
    makePresentation(5, { project_type: "tesis", project_title: "Blockchain en Finanzas", student_name: "Sofia Castro", tutor_name: "Raúl Medina" }),
    makePresentation(6, { project_type: "tesis", project_title: "Machine Learning Industrial", student_name: "Diego Flores", tutor_name: "Nora Silva" }),
  ],
};

// Day 4: 2026-03-25 — 1 PTEG
const DAY_MAR_25: PresentationDay = {
  id: 4,
  date: "2026-03-25",
  notes: "",
  presentations: [
    makePresentation(7, { project_type: "proyecto", project_title: "Portal Ciudadano", student_name: "Isabel Mora", tutor_name: "Carlos Méndez" }),
  ],
};

const ALL_DAYS = [DAY_MAR_08, DAY_MAR_12, DAY_MAR_18, DAY_MAR_25];

// now = 2026-03-12 for period tests
const NOW = new Date("2026-03-12T00:00:00.000Z");

// ── applyPresentationFilters ───────────────────────────────────────────────────

describe("applyPresentationFilters", () => {
  it("returns all days unchanged when using DEFAULT_FILTERS", () => {
    const result = applyPresentationFilters(ALL_DAYS, DEFAULT_FILTERS, NOW);
    expect(result).toHaveLength(4);
    expect(result.flatMap((d) => d.presentations)).toHaveLength(7);
  });

  it("filters by project_title (case-insensitive); days with no match are dropped", () => {
    const filters = { ...DEFAULT_FILTERS, search: "redes neuronales" };
    const result = applyPresentationFilters(ALL_DAYS, filters, NOW);
    expect(result).toHaveLength(1);
    expect(result[0].date).toBe("2026-03-12");
    expect(result[0].presentations).toHaveLength(1);
    expect(result[0].presentations[0].project_title).toBe("Redes Neuronales Aplicadas");
  });

  it("filters by project_title; days with at least one match keep only matching presentations", () => {
    const filters = { ...DEFAULT_FILTERS, search: "plataforma" };
    const result = applyPresentationFilters(ALL_DAYS, filters, NOW);
    expect(result).toHaveLength(1);
    expect(result[0].date).toBe("2026-03-08");
    expect(result[0].presentations).toHaveLength(1);
    expect(result[0].presentations[0].project_title).toBe("Plataforma Educativa");
  });

  it("filters by student_name (case-insensitive)", () => {
    const filters = { ...DEFAULT_FILTERS, search: "sofia castro" };
    const result = applyPresentationFilters(ALL_DAYS, filters, NOW);
    expect(result).toHaveLength(1);
    expect(result[0].date).toBe("2026-03-18");
    expect(result[0].presentations[0].student_name).toBe("Sofia Castro");
  });

  it("filters by tutor_name (case-insensitive)", () => {
    const filters = { ...DEFAULT_FILTERS, search: "carlos méndez" };
    const result = applyPresentationFilters(ALL_DAYS, filters, NOW);
    // DAY_MAR_08 has 1 match (Carlos Méndez), DAY_MAR_25 has 1 match (Carlos Méndez)
    expect(result).toHaveLength(2);
    const allMatched = result.flatMap((d) => d.presentations);
    expect(allMatched.every((p) => p.tutor_name === "Carlos Méndez")).toBe(true);
  });

  it("modality=proyecto keeps only PTEG presentations; days with no PTEG are dropped", () => {
    const filters = { ...DEFAULT_FILTERS, modality: "proyecto" as const };
    const result = applyPresentationFilters(ALL_DAYS, filters, NOW);
    // DAY_MAR_18 has only TEG → dropped. Others kept.
    expect(result).toHaveLength(3);
    const allTypes = result.flatMap((d) => d.presentations).map((p) => p.project_type);
    expect(allTypes.every((t) => t === "proyecto")).toBe(true);
  });

  it("modality=tesis keeps only TEG presentations", () => {
    const filters = { ...DEFAULT_FILTERS, modality: "tesis" as const };
    const result = applyPresentationFilters(ALL_DAYS, filters, NOW);
    // Only DAY_MAR_12 (1 TEG) and DAY_MAR_18 (2 TEG)
    expect(result).toHaveLength(2);
    const allTypes = result.flatMap((d) => d.presentations).map((p) => p.project_type);
    expect(allTypes.every((t) => t === "tesis")).toBe(true);
  });

  it("modality=all applies no modality filtering", () => {
    const filters = { ...DEFAULT_FILTERS, modality: "all" as const };
    const result = applyPresentationFilters(ALL_DAYS, filters, NOW);
    expect(result).toHaveLength(4);
  });

  it("period=today (now=2026-03-12) returns only 2026-03-12 days", () => {
    const filters = { ...DEFAULT_FILTERS, period: "today" as const };
    const result = applyPresentationFilters(ALL_DAYS, filters, NOW);
    expect(result).toHaveLength(1);
    expect(result[0].date).toBe("2026-03-12");
  });

  it("period=week (now=2026-03-12) returns days within 7 days from now", () => {
    const filters = { ...DEFAULT_FILTERS, period: "week" as const };
    const result = applyPresentationFilters(ALL_DAYS, filters, NOW);
    // 2026-03-12 and 2026-03-18 are within 7 days (12..18 inclusive)
    // 2026-03-08 is before now, 2026-03-25 is after the 7-day window
    const dates = result.map((d) => d.date);
    expect(dates).toContain("2026-03-12");
    expect(dates).toContain("2026-03-18");
    expect(dates).not.toContain("2026-03-08");
    expect(dates).not.toContain("2026-03-25");
  });

  it("period=month (now=2026-03-12) returns days from now to end of March", () => {
    const filters = { ...DEFAULT_FILTERS, period: "month" as const };
    const result = applyPresentationFilters(ALL_DAYS, filters, NOW);
    // 2026-03-08 is before now → excluded
    const dates = result.map((d) => d.date);
    expect(dates).not.toContain("2026-03-08");
    expect(dates).toContain("2026-03-12");
    expect(dates).toContain("2026-03-18");
    expect(dates).toContain("2026-03-25");
  });

  it("period=all applies no period filtering", () => {
    const filters = { ...DEFAULT_FILTERS, period: "all" as const };
    const result = applyPresentationFilters(ALL_DAYS, filters, NOW);
    expect(result).toHaveLength(4);
  });

  it("combined filters (search + modality + period) work together", () => {
    const filters = {
      search: "méndez",
      modality: "proyecto" as const,
      period: "month" as const,
    };
    const result = applyPresentationFilters(ALL_DAYS, filters, NOW);
    // Only PTEG, tutor_name contains "méndez", from 2026-03-12 to end of month
    // DAY_MAR_08 excluded (before NOW by month filter logic)
    // DAY_MAR_25 has Isabel Mora / Carlos Méndez → matches tutor + modality + in month
    const dates = result.map((d) => d.date);
    expect(dates).not.toContain("2026-03-08");
    expect(dates).toContain("2026-03-25");
    const allTypes = result.flatMap((d) => d.presentations).map((p) => p.project_type);
    expect(allTypes.every((t) => t === "proyecto")).toBe(true);
  });

  it("does not mutate the input days array", () => {
    const original = JSON.parse(JSON.stringify(ALL_DAYS));
    const filters = { ...DEFAULT_FILTERS, modality: "proyecto" as const };
    applyPresentationFilters(ALL_DAYS, filters, NOW);
    expect(ALL_DAYS).toEqual(original);
  });
});

// ── countByModality ────────────────────────────────────────────────────────────

describe("countByModality", () => {
  it("counts total, PTEG and TEG presentations across all days", () => {
    const result = countByModality(ALL_DAYS);
    // Total 7: PTEG = 5 (ids 1,2,3,7 + project_type="proyecto"), TEG = 2 (ids 4,5,6)
    // DAY_MAR_08: 2 PTEG, DAY_MAR_12: 1 PTEG + 1 TEG, DAY_MAR_18: 2 TEG, DAY_MAR_25: 1 PTEG
    expect(result.total).toBe(7);
    expect(result.pteg).toBe(4);
    expect(result.teg).toBe(3);
  });

  it("returns zeros for empty days array", () => {
    const result = countByModality([]);
    expect(result).toEqual({ total: 0, pteg: 0, teg: 0 });
  });
});

// ── countForPeriod ─────────────────────────────────────────────────────────────

describe("countForPeriod", () => {
  it("period=all returns total count across all days", () => {
    const count = countForPeriod(ALL_DAYS, "all", NOW);
    expect(count).toBe(7);
  });

  it("period=week (now=2026-03-12) returns count within 7 days from now", () => {
    const count = countForPeriod(ALL_DAYS, "week", NOW);
    // DAY_MAR_12 (2 presentations) + DAY_MAR_18 (2 presentations) = 4
    expect(count).toBe(4);
  });

  it("returns 0 for empty days array", () => {
    const count = countForPeriod([], "all", NOW);
    expect(count).toBe(0);
  });
});

// ── isFiltersActive ────────────────────────────────────────────────────────────

describe("isFiltersActive", () => {
  it("returns false for DEFAULT_FILTERS", () => {
    expect(isFiltersActive(DEFAULT_FILTERS)).toBe(false);
  });

  it("returns true when search is non-empty", () => {
    expect(isFiltersActive({ ...DEFAULT_FILTERS, search: "hola" })).toBe(true);
  });

  it("returns true when modality is not all", () => {
    expect(isFiltersActive({ ...DEFAULT_FILTERS, modality: "proyecto" })).toBe(true);
  });

  it("returns true when period is not all", () => {
    expect(isFiltersActive({ ...DEFAULT_FILTERS, period: "today" })).toBe(true);
  });
});
