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
const mockGetUserRole = vi.fn<() => string>();
vi.mock("@features/auth/api/clientAuth", () => ({
  isAuthenticated: () => true,
  getUser: () => ({ email: "u@test.com", status: "active", role: "Estudiante", fullName: "U" }),
  getUserRole: () => mockGetUserRole(),
  logout: vi.fn(),
}));

// ── planificacionService mock ─────────────────────────────────────────────────
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
        student_email: "ana@example.com",
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
// This import will fail with "Cannot find module" until the frontend-worker
// creates the file — that is the correct RED state.
import PlanificacionView from "@features/planificacion/components/PlanificacionView";

// ─────────────────────────────────────────────────────────────────────────────

const readOnlyRoles = ["Estudiante", "Tutor", "Jurado"] as const;

describe("PlanificacionView — role-based affordances", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  for (const role of readOnlyRoles) {
    it(`renders read-only for ${role}`, async () => {
      mockGetUserRole.mockReturnValue(role);
      render(<PlanificacionView />);

      expect(await screen.findByText("Sistema de Gestión Académica")).toBeInTheDocument();

      expect(screen.queryByRole("button", { name: /agregar presentación/i })).toBeNull();
      expect(screen.queryByRole("button", { name: /crear .* días/i })).toBeNull();
      expect(screen.queryByRole("button", { name: /eliminar/i })).toBeNull();
      expect(screen.queryByRole("button", { name: /editar/i })).toBeNull();
    });
  }

  it("renders admin controls for Administrador", async () => {
    mockGetUserRole.mockReturnValue("Administrador");
    render(<PlanificacionView />);

    expect(await screen.findByText("Sistema de Gestión Académica")).toBeInTheDocument();

    expect(screen.getByRole("button", { name: /agregar presentación/i })).toBeInTheDocument();
    expect(screen.getByRole("button", { name: /crear .* días/i })).toBeInTheDocument();

    // Admin edit/delete affordances — the frontend-worker MUST implement these
    // as aria-label attributes on icon buttons so RTL can find them by role.
    expect(screen.getByRole("button", { name: /editar/i })).toBeInTheDocument();
    expect(screen.getByRole("button", { name: /eliminar/i })).toBeInTheDocument();
  });

  it("shows time pill in HH:MM format", async () => {
    mockGetUserRole.mockReturnValue("Estudiante");
    render(<PlanificacionView />);

    expect(await screen.findByText("14:30")).toBeInTheDocument();
  });
});
