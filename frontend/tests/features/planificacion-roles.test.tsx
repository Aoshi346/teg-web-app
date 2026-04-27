import React from "react";
import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen } from "@testing-library/react";

// ── next/navigation mock ──────────────────────────────────────────────────────
vi.mock("next/navigation", () => ({
  useRouter: () => ({ prefetch: vi.fn(), push: vi.fn(), replace: vi.fn(), back: vi.fn() }),
  usePathname: () => "/dashboard/planificacion",
  useSearchParams: () => new URLSearchParams(),
  redirect: vi.fn(),
}));

// ── clientAuth mock — overridden per test via mockReturnValue ─────────────────
// getUser is also mockable so each test can inject the correct id/email for
// role-aware filtering (tutor id=7 matches tutor field, jurado id=8 matches
// jurado array, estudiante email matches student_email in mock data).
const mockGetUserRole = vi.fn<() => string>();
const mockGetUser = vi.fn();

vi.mock("@features/auth/api/clientAuth", () => ({
  isAuthenticated: () => true,
  getUser: () => mockGetUser(),
  getUserRole: () => mockGetUserRole(),
  logout: vi.fn(),
}));

// ── planificacionService mock ─────────────────────────────────────────────────
// student_email matches the Estudiante viewer's email so PlanStudentView can
// locate the presentation via filterPresentationsForRole.
const mockDays = [
  {
    id: 1,
    date: "2026-05-12",
    notes: "",
    presentations: [
      {
        id: 10,
        start_time: "14:30",
        duration_minutes: 30,
        project: 5,
        project_title: "Sistema de Gestión Académica",
        project_type: "tesis",
        student_name: "Ana López",
        student_email: "student@test.com",
        tutor: 7,
        tutor_name: "Prof. Carlos Méndez",
        jurado: [8, 9],
        jurado_names: ["Prof. María Ruiz", "Prof. Juan Silva"],
        order: 0,
      },
    ],
  },
];

vi.mock("@features/planificacion/api/planificacionService", () => ({
  listDays: vi.fn().mockResolvedValue(mockDays),
}));

// ── component under test ──────────────────────────────────────────────────────
import PlanificacionView from "@features/planificacion/components/PlanificacionView";

// ─────────────────────────────────────────────────────────────────────────────

describe("PlanificacionView — role-based affordances", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  // Tutor: id=7 matches presentation.tutor — PlanReviewerView will show the row
  it("renders read-only for Tutor", async () => {
    mockGetUserRole.mockReturnValue("Tutor");
    mockGetUser.mockReturnValue({ id: 7, email: "tutor@test.com", role: "Tutor" });
    render(<PlanificacionView />);

    expect(await screen.findByText("Sistema de Gestión Académica")).toBeInTheDocument();

    expect(screen.queryByRole("button", { name: /crear días/i })).toBeNull();
    expect(screen.queryByRole("button", { name: /eliminar/i })).toBeNull();
    expect(screen.queryByRole("button", { name: /editar/i })).toBeNull();
  });

  // Jurado: id=8 matches presentation.jurado array — PlanReviewerView shows the row
  it("renders read-only for Jurado", async () => {
    mockGetUserRole.mockReturnValue("Jurado");
    mockGetUser.mockReturnValue({ id: 8, email: "jurado@test.com", role: "Jurado" });
    render(<PlanificacionView />);

    expect(await screen.findByText("Sistema de Gestión Académica")).toBeInTheDocument();

    expect(screen.queryByRole("button", { name: /crear días/i })).toBeNull();
    expect(screen.queryByRole("button", { name: /eliminar/i })).toBeNull();
    expect(screen.queryByRole("button", { name: /editar/i })).toBeNull();
  });

  // Estudiante: email matches student_email — PlanStudentView renders MyDefCard
  it("renders read-only for Estudiante", async () => {
    mockGetUserRole.mockReturnValue("Estudiante");
    mockGetUser.mockReturnValue({ id: 3, email: "student@test.com", role: "Estudiante" });
    render(<PlanificacionView />);

    // PlanStudentView shows the project title inside MyDefCard
    expect(await screen.findByText("Sistema de Gestión Académica")).toBeInTheDocument();

    expect(screen.queryByRole("button", { name: /crear días/i })).toBeNull();
    expect(screen.queryByRole("button", { name: /eliminar/i })).toBeNull();
    expect(screen.queryByRole("button", { name: /editar/i })).toBeNull();
  });

  it("renders admin controls for Administrador", async () => {
    mockGetUserRole.mockReturnValue("Administrador");
    mockGetUser.mockReturnValue({ id: 1, email: "admin@test.com", role: "Administrador" });
    render(<PlanificacionView />);

    // PlanAdminView renders all presentations unconditionally
    expect(await screen.findByText("Sistema de Gestión Académica")).toBeInTheDocument();

    // "Crear días" mode toggle is visible in the calendar toolbar for admin
    expect(screen.getByRole("button", { name: /crear días/i })).toBeInTheDocument();

    // Admin edit/delete affordances on PresentationRow — implemented as
    // aria-label attributes on icon buttons so RTL can find them by role.
    // "Eliminar" matches both the PresentationRow delete button and the new
    // DayCard delete button ("Eliminar día"), so use getAllByRole.
    expect(screen.getByRole("button", { name: /editar/i })).toBeInTheDocument();
    expect(screen.getAllByRole("button", { name: /eliminar/i }).length).toBeGreaterThan(0);
  });

  // The canonical entry point for creating days is the calendar's "Crear días"
  // mode toggle button (the former "+ Nuevo día" button in the day-management
  // section was removed in fix-pass-4 as redundant).
  it("shows Crear días mode-toggle button for Administrador", async () => {
    mockGetUserRole.mockReturnValue("Administrador");
    mockGetUser.mockReturnValue({ id: 1, email: "admin@test.com", role: "Administrador" });
    render(<PlanificacionView />);

    // Waits for async data load before checking
    await screen.findByText("Sistema de Gestión Académica");
    expect(screen.getByRole("button", { name: /crear días/i })).toBeInTheDocument();
  });

  it("shows time in HH:MM format for Estudiante", async () => {
    mockGetUserRole.mockReturnValue("Estudiante");
    mockGetUser.mockReturnValue({ id: 3, email: "student@test.com", role: "Estudiante" });
    render(<PlanificacionView />);

    // MyDefCard renders start_time directly
    expect(await screen.findByText("14:30")).toBeInTheDocument();
  });
});
