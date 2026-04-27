import { describe, it, expect } from "vitest";
import { filterPresentationsForRole } from "./filterForRole";
import type {
  Presentation,
  PresentationDay,
} from "@features/planificacion/types/planificacion";

// ---------------------------------------------------------------------------
// Fixtures
// ---------------------------------------------------------------------------

function mkPresentation(overrides: Partial<Presentation> = {}): Presentation {
  return {
    id: 1,
    day: 10,
    project: 1,
    project_title: "Proyecto X",
    project_type: "tesis",
    student_name: "Ana García",
    student_email: "ana@example.com",
    tutor: 5,
    tutor_name: "Tutor Principal",
    jurado: [9, 10],
    jurado_names: ["Jurado A", "Jurado B"],
    start_time: "14:00",
    duration_minutes: 60,
    order: 0,
    ...overrides,
  };
}

function mkDay(
  id: number,
  presentations: Presentation[],
  overrides: Partial<PresentationDay> = {}
): PresentationDay {
  return {
    id,
    date: `2026-06-${String(id).padStart(2, "0")}`,
    notes: "",
    presentations,
    ...overrides,
  };
}

// Tutor 5 tutors presentations 1 and 2; Jurado 9 is on all three.
const presA = mkPresentation({ id: 1, tutor: 5, jurado: [9, 10], student_email: "ana@example.com" });
const presB = mkPresentation({ id: 2, tutor: 5, jurado: [9, 11], student_email: "bob@example.com" });
const presC = mkPresentation({ id: 3, tutor: 7, jurado: [9, 12], student_email: "carmen@example.com" });
const presD = mkPresentation({ id: 4, tutor: 8, jurado: [12, 13], student_email: "david@example.com" });

// Day 1: presA (tutor=5, jurado=[9,10]) + presC (tutor=7, jurado=[9,12])
// Day 2: presB (tutor=5, jurado=[9,11])
// Day 3: presD (tutor=8, jurado=[12,13]) — neither tutor5 nor jurado9
const dayOne = mkDay(1, [presA, presC]);
const dayTwo = mkDay(2, [presB]);
const dayThree = mkDay(3, [presD]);

const allDays: PresentationDay[] = [dayOne, dayTwo, dayThree];

// ---------------------------------------------------------------------------
// Administrador
// ---------------------------------------------------------------------------

describe("filterPresentationsForRole — Administrador", () => {
  it("returns all days unchanged", () => {
    const result = filterPresentationsForRole(allDays, "Administrador", {});
    expect(result).toHaveLength(3);
    expect(result).toEqual(allDays);
  });

  it("returns all days even when viewerId is undefined", () => {
    const result = filterPresentationsForRole(allDays, "Administrador", { viewerId: undefined });
    expect(result).toHaveLength(3);
  });

  it("returns empty array when days array is empty", () => {
    const result = filterPresentationsForRole([], "Administrador", {});
    expect(result).toHaveLength(0);
  });
});

// ---------------------------------------------------------------------------
// Tutor
// ---------------------------------------------------------------------------

describe("filterPresentationsForRole — Tutor", () => {
  it("returns only days that have at least one presentation where tutor === viewerId", () => {
    // tutor=5 is on dayOne (presA) and dayTwo (presB); not on dayThree
    const result = filterPresentationsForRole(allDays, "Tutor", { viewerId: 5 });
    expect(result).toHaveLength(2);
    const ids = result.map((d) => d.id);
    expect(ids).toContain(1);
    expect(ids).toContain(2);
    expect(ids).not.toContain(3);
  });

  it("filters day.presentations to only those where tutor === viewerId", () => {
    // dayOne has presA (tutor=5) and presC (tutor=7); only presA should survive
    const result = filterPresentationsForRole(allDays, "Tutor", { viewerId: 5 });
    const returnedDayOne = result.find((d) => d.id === 1)!;
    expect(returnedDayOne.presentations).toHaveLength(1);
    expect(returnedDayOne.presentations[0].id).toBe(presA.id);
  });

  it("returns [] when viewerId is undefined", () => {
    const result = filterPresentationsForRole(allDays, "Tutor", {});
    expect(result).toHaveLength(0);
  });

  it("returns [] when no day contains a presentation for the given tutor", () => {
    const result = filterPresentationsForRole(allDays, "Tutor", { viewerId: 999 });
    expect(result).toHaveLength(0);
  });

  it("preserves the original day object shape (id, date, notes) on filtered days", () => {
    const result = filterPresentationsForRole(allDays, "Tutor", { viewerId: 5 });
    const d = result.find((d) => d.id === 2)!;
    expect(d.date).toBe(dayTwo.date);
    expect(d.notes).toBe(dayTwo.notes);
  });
});

// ---------------------------------------------------------------------------
// Jurado
// ---------------------------------------------------------------------------

describe("filterPresentationsForRole — Jurado", () => {
  it("returns only days that have at least one presentation where jurado.includes(viewerId)", () => {
    // jurado=9 is on dayOne (presA, presC) and dayTwo (presB); not on dayThree
    const result = filterPresentationsForRole(allDays, "Jurado", { viewerId: 9 });
    expect(result).toHaveLength(2);
    const ids = result.map((d) => d.id);
    expect(ids).toContain(1);
    expect(ids).toContain(2);
    expect(ids).not.toContain(3);
  });

  it("filters day.presentations to only those where jurado.includes(viewerId)", () => {
    // jurado=10 is only on presA (dayOne); dayTwo presB has [9,11], not 10
    const result = filterPresentationsForRole(allDays, "Jurado", { viewerId: 10 });
    expect(result).toHaveLength(1);
    expect(result[0].id).toBe(1);
    expect(result[0].presentations).toHaveLength(1);
    expect(result[0].presentations[0].id).toBe(presA.id);
  });

  it("returns [] when viewerId is undefined", () => {
    const result = filterPresentationsForRole(allDays, "Jurado", {});
    expect(result).toHaveLength(0);
  });

  it("returns [] when viewerId is on no jurado list", () => {
    const result = filterPresentationsForRole(allDays, "Jurado", { viewerId: 999 });
    expect(result).toHaveLength(0);
  });
});

// ---------------------------------------------------------------------------
// Tutor-also-Jurado overlap
// ---------------------------------------------------------------------------

describe("filterPresentationsForRole — tutor who is also jurado on the same presentation", () => {
  // presE: viewerId=5 is both tutor and in jurado array
  const presE = mkPresentation({ id: 5, tutor: 5, jurado: [5, 9], student_email: "elena@example.com" });
  const dayOverlap = mkDay(5, [presE]);

  it("Tutor view: presentation appears exactly once (no double-count)", () => {
    // When role=Tutor and viewerId=5, the presentation where tutor===5 should
    // appear once even though viewerId is also in jurado[]. Chip logic (Tutor
    // wins) is NOT the responsibility of this helper — just don't double-count.
    const result = filterPresentationsForRole([dayOverlap], "Tutor", { viewerId: 5 });
    expect(result).toHaveLength(1);
    expect(result[0].presentations).toHaveLength(1);
    expect(result[0].presentations[0].id).toBe(5);
  });

  it("Jurado view: presentation also appears exactly once", () => {
    const result = filterPresentationsForRole([dayOverlap], "Jurado", { viewerId: 5 });
    expect(result).toHaveLength(1);
    expect(result[0].presentations).toHaveLength(1);
  });
});

// ---------------------------------------------------------------------------
// Estudiante
// ---------------------------------------------------------------------------

describe("filterPresentationsForRole — Estudiante", () => {
  it("returns at most one day containing only the student's own presentation", () => {
    const result = filterPresentationsForRole(allDays, "Estudiante", {
      viewerEmail: "ana@example.com",
    });
    expect(result).toHaveLength(1);
    expect(result[0].presentations).toHaveLength(1);
    expect(result[0].presentations[0].student_email).toBe("ana@example.com");
  });

  it("does not include presentations belonging to other students in the same day", () => {
    // dayOne has presA (ana) and presC (carmen); viewing as ana should only see presA
    const result = filterPresentationsForRole(allDays, "Estudiante", {
      viewerEmail: "ana@example.com",
    });
    expect(result[0].presentations.every((p) => p.student_email === "ana@example.com")).toBe(true);
  });

  it("returns [] when viewerEmail is undefined", () => {
    const result = filterPresentationsForRole(allDays, "Estudiante", {});
    expect(result).toHaveLength(0);
  });

  it("returns [] when student_email matches no presentation", () => {
    const result = filterPresentationsForRole(allDays, "Estudiante", {
      viewerEmail: "nobody@example.com",
    });
    expect(result).toHaveLength(0);
  });

  it("returns the first matching day only (at most one)", () => {
    // Edge case: same student appears twice in the dataset across different days
    const presStudent1 = mkPresentation({ id: 10, student_email: "twin@example.com", tutor: 5 });
    const presStudent2 = mkPresentation({ id: 11, student_email: "twin@example.com", tutor: 7 });
    const dayA = mkDay(10, [presStudent1]);
    const dayB = mkDay(11, [presStudent2]);
    const result = filterPresentationsForRole([dayA, dayB], "Estudiante", {
      viewerEmail: "twin@example.com",
    });
    // Real-world: a student should have exactly one scheduled presentation.
    // The helper guarantees "at most one day" even in this degenerate case.
    expect(result.length).toBeLessThanOrEqual(1);
  });
});

// ---------------------------------------------------------------------------
// Unknown / fallback role
// ---------------------------------------------------------------------------

describe("filterPresentationsForRole — unknown role", () => {
  it("unknown role behaves like admin (returns all days) as a safe fallback", () => {
    const result = filterPresentationsForRole(allDays, "UnknownRole", {});
    expect(result).toHaveLength(allDays.length);
  });
});
