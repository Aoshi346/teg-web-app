import React from "react";
import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import type { UserOption } from "../hooks/useDocumentData";

// ---------------------------------------------------------------------------
// Mocks — aggressive stubbing to keep the render cheap. We are testing
// structure only; no submit flow assertions in this task.
// ---------------------------------------------------------------------------

vi.mock("@features/projects/api/projectService", () => ({
  createProject: vi.fn(),
  uploadProjectFile: vi.fn(),
}));

vi.mock("@features/semesters/api/semesters", () => ({
  getCurrentSemester: () => "2026-01",
}));

// Combobox is portal-based; skip it entirely in structural tests.
vi.mock("./Combobox", () => ({ default: () => null }));

// AdvisorsChips replaced via test stub so we can assert its presence.
vi.mock("./AdvisorsChips", () => ({
  default: () => <div data-testid="advisors-chips" />,
}));

// DocumentTypeSelector is visual only for structural purposes — stub it.
vi.mock("./DocumentTypeSelector", () => ({
  default: () => <div data-testid="doc-type-selector" />,
}));

// ---------------------------------------------------------------------------
// Component under test
// ---------------------------------------------------------------------------

import DocumentFormNew from "./DocumentFormNew";

// ---------------------------------------------------------------------------
// Fixture factory
// ---------------------------------------------------------------------------

const TUTORS: UserOption[] = [
  { id: 1, label: "Prof. Alpha", email: "alpha@test.com" },
];

const STUDENTS: UserOption[] = [
  { id: 10, label: "Estudiante Uno", email: "est1@test.com" },
];

const JURADOS: UserOption[] = [
  { id: 20, label: "Jurado Uno", email: "jur1@test.com" },
];

interface DefaultPropsOverrides {
  userRole?: string;
  isStudent?: boolean;
  defaultDocType?: "proyecto" | "tesis";
  allowedDocumentTypes?: readonly ("proyecto" | "tesis")[];
  currentUser?: {
    id?: number;
    fullName?: string;
    email: string;
    semester?: string;
  } | null;
}

function buildDefaultProps(overrides: DefaultPropsOverrides = {}) {
  return {
    userRole: overrides.userRole ?? "Administrador",
    currentUser: overrides.currentUser ?? {
      id: 99,
      fullName: "Admin User",
      email: "admin@test.com",
    },
    isStudent: overrides.isStudent ?? false,
    students: STUDENTS,
    tutors: TUTORS,
    jurados: JURADOS,
    partners: STUDENTS,
    semesters: ["2026-01"],
    defaultSemester: "2026-01",
    defaultDocType: overrides.defaultDocType ?? "proyecto",
    allowedDocumentTypes: overrides.allowedDocumentTypes ?? (["proyecto", "tesis"] as const),
  };
}

// ---------------------------------------------------------------------------
// Tests
// ---------------------------------------------------------------------------

describe("DocumentFormNew — Sub-H structural smoke", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  // Test 1: Admin sees 3 sections: Identificación / Equipo / Archivos
  it("renders Identificación section heading for admin role", () => {
    render(<DocumentFormNew {...buildDefaultProps({ userRole: "Administrador", isStudent: false })} />);
    // The rewritten component must render an explicit "Identificación" heading
    // in section 01. Currently the monolith only has "Información del Documento".
    expect(screen.getByText(/identificaci[oó]n/i)).toBeTruthy();
  });

  it("renders Equipo section heading for admin role", () => {
    render(<DocumentFormNew {...buildDefaultProps({ userRole: "Administrador", isStudent: false })} />);
    expect(screen.getByText(/equipo/i)).toBeTruthy();
  });

  it("renders Archivos section heading for admin role", () => {
    render(<DocumentFormNew {...buildDefaultProps({ userRole: "Administrador", isStudent: false })} />);
    expect(screen.getByText(/archivos/i)).toBeTruthy();
  });

  // Test 2: Estudiante sees 2 sections: Información / Archivo — Equipo is absent
  it("renders Información section heading for estudiante role", () => {
    render(
      <DocumentFormNew
        {...buildDefaultProps({
          userRole: "Estudiante",
          isStudent: true,
          allowedDocumentTypes: ["proyecto"] as const,
          currentUser: { id: 10, fullName: "Est Uno", email: "est@test.com", semester: "9no" },
        })}
      />,
    );
    expect(screen.getByText(/informaci[oó]n/i)).toBeTruthy();
  });

  it("renders Archivo section heading for estudiante role", () => {
    render(
      <DocumentFormNew
        {...buildDefaultProps({
          userRole: "Estudiante",
          isStudent: true,
          allowedDocumentTypes: ["proyecto"] as const,
          currentUser: { id: 10, fullName: "Est Uno", email: "est@test.com", semester: "9no" },
        })}
      />,
    );
    // Must be at least one match for "Archivo" (e.g., "Archivo" or "Archivos")
    expect(screen.getAllByText(/archivo/i).length).toBeGreaterThan(0);
  });

  it("does NOT render an Equipo section heading for estudiante role", () => {
    render(
      <DocumentFormNew
        {...buildDefaultProps({
          userRole: "Estudiante",
          isStudent: true,
          allowedDocumentTypes: ["proyecto"] as const,
          currentUser: { id: 10, fullName: "Est Uno", email: "est@test.com", semester: "9no" },
        })}
      />,
    );
    // "Equipo" as an exact section head must not be present for students.
    // The current monolith has no section heads at all; after the refactor only admin
    // gets the Equipo section. We check there is no element whose text is exactly "Equipo"
    // (case-insensitive) appearing as a section title.
    const equipo = screen.queryByText(/^equipo$/i);
    expect(equipo).toBeNull();
  });

  // Test 3: Submit button label varies by role
  it("shows 'Registrar trabajo' submit button for admin role", () => {
    render(<DocumentFormNew {...buildDefaultProps({ userRole: "Administrador", isStudent: false })} />);
    // Current component shows "Agregar Documento" — this will fail once refactored.
    expect(screen.getByRole("button", { name: /registrar trabajo/i })).toBeTruthy();
  });

  it("shows 'Subir proyecto' submit button for estudiante with proyecto docType", () => {
    render(
      <DocumentFormNew
        {...buildDefaultProps({
          userRole: "Estudiante",
          isStudent: true,
          defaultDocType: "proyecto",
          allowedDocumentTypes: ["proyecto"] as const,
          currentUser: { id: 10, fullName: "Est Uno", email: "est@test.com", semester: "9no" },
        })}
      />,
    );
    // The button text must contain "Subir proyecto" (case-insensitive).
    // Current component shows "Agregar Documento" — this test will fail.
    expect(screen.getByRole("button", { name: /subir proyecto/i })).toBeTruthy();
  });

  // Test 4: No raw Tailwind color leakage in the rendered tree
  it("renders no raw bg-purple-50/bg-emerald-50/bg-indigo classes (semantic token migration)", () => {
    const { container } = render(
      <DocumentFormNew {...buildDefaultProps({ userRole: "Administrador", isStudent: false })} />,
    );
    // The current component uses bg-purple-50/30, bg-indigo-50/60, bg-amber-50/30, etc.
    // After the Sub-H refactor all raw colors must be replaced with semantic tokens or agg-* classes.
    // This selector intentionally casts a wide net — any hit is a regression.
    const leaked = container.querySelector(
      ".bg-purple-50, .bg-emerald-50, .bg-indigo-50, .text-purple-500, .text-indigo-500, .text-teal-500, .text-amber-500, .bg-amber-50, .bg-blue-50",
    );
    expect(leaked).toBeNull();
  });

  // Test 5: AdvisorsChips stub renders (confirms the import was updated)
  it("renders the AdvisorsChips component (stub present in the tree)", () => {
    render(<DocumentFormNew {...buildDefaultProps({ userRole: "Administrador", isStudent: false })} />);
    expect(screen.getByTestId("advisors-chips")).toBeTruthy();
  });

  // Test 6: Cancelar button is always present
  it("renders a Cancelar button", () => {
    render(<DocumentFormNew {...buildDefaultProps({ userRole: "Administrador", isStudent: false })} />);
    expect(screen.getByRole("button", { name: /cancelar/i })).toBeTruthy();
  });

  // Test 7: Section numerals — "01" must appear as a Fraunces numeral heading
  // The rewritten component uses <span class="agg-sec-num">01</span> inside each section head.
  // The current monolith has no "01" text anywhere — this test will fail until the refactor.
  it("renders section numeral '01' in the admin form (Fraunces section heads)", () => {
    render(<DocumentFormNew {...buildDefaultProps({ userRole: "Administrador", isStudent: false })} />);
    expect(screen.getByText("01")).toBeTruthy();
  });

  it("renders section numerals '01' and '02' in the estudiante form", () => {
    render(
      <DocumentFormNew
        {...buildDefaultProps({
          userRole: "Estudiante",
          isStudent: true,
          allowedDocumentTypes: ["proyecto"] as const,
          currentUser: { id: 10, fullName: "Est Uno", email: "est@test.com", semester: "9no" },
        })}
      />,
    );
    expect(screen.getByText("01")).toBeTruthy();
    expect(screen.getByText("02")).toBeTruthy();
  });

  // Phase 3 RED — submit feedback bug
  // Confirms that DocumentFormNew renders the advisors validation error message
  // after a failed submit attempt. Today the component never renders
  // errors.advisors?.message, so the second assertion below fails.
  it("surfaces 'Debe asignar al menos un tutor' when admin submits without adding a tutor", async () => {
    const user = userEvent.setup();
    render(
      <DocumentFormNew
        {...buildDefaultProps({
          userRole: "Administrador",
          isStudent: false,
          currentUser: null,
        })}
      />,
    );

    // Type a title long enough to pass the title validation (≥10 chars)
    const titleInput = screen.getByPlaceholderText("Ingresa el título completo...");
    await user.type(titleInput, "Título válido de prueba");

    // Click submit without selecting a student or adding a tutor
    const submitButton = screen.getByRole("button", { name: /registrar trabajo/i });
    await user.click(submitButton);

    // Sanity check: the studentId error IS rendered today (confirms validation ran)
    await waitFor(() => {
      expect(screen.queryByText("Debe seleccionar un estudiante.")).toBeInTheDocument();
    });

    // This assertion MUST fail today: errors.advisors is never rendered in DocumentFormNew.tsx
    expect(screen.queryByText("Debe asignar al menos un tutor.")).toBeInTheDocument();
  });
});
