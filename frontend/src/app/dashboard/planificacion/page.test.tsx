import React from "react";
import { describe, it, expect, vi, beforeEach } from "vitest";
import { render } from "@testing-library/react";
import * as auth from "@features/auth/api/clientAuth";

// ── Module mocks ──────────────────────────────────────────────────────────────

vi.mock("@features/auth/api/clientAuth", () => ({
  getUserRole: vi.fn(),
  getUser: vi.fn(),
  getUserEmail: vi.fn(),
  logout: vi.fn(),
}));

vi.mock("@features/planificacion/hooks/usePlanificacion", () => ({
  usePlanificacion: vi.fn(() => ({
    days: [],
    loading: false,
    error: null,
    refresh: vi.fn(),
  })),
}));

vi.mock("@features/semesters/api/semesters", () => ({
  getCurrentSemester: vi.fn(() => "2026-01"),
}));

vi.mock("@widgets/header/DashboardHeader", () => ({
  default: ({ pageTitle }: { pageTitle?: string }) => (
    <header data-testid="dashboard-header">{pageTitle}</header>
  ),
}));

// ── Helpers ───────────────────────────────────────────────────────────────────

function setupRole(role: string) {
  vi.mocked(auth.getUserRole).mockReturnValue(role);
  vi.mocked(auth.getUser).mockReturnValue({
    id: 1,
    email: "a@b.c",
    role: role as auth.User["role"],
    status: "active",
    firstName: "Admin",
  });
}

// Lazy import so mocks are applied before the module loads
async function renderPage() {
  const { default: PlanificacionPage } = await import("./page");
  return render(<PlanificacionPage />);
}

// ── Tests ─────────────────────────────────────────────────────────────────────

describe("PlanificacionPage — page integration (Task 11)", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  // 1 — Mounts without throwing, has at least one main element
  it("mounts without throwing and renders at least one main element", async () => {
    setupRole("Administrador");
    const { container } = await renderPage();

    const mains = container.querySelectorAll("main");
    expect(mains.length).toBeGreaterThanOrEqual(1);
  });

  // 2 — DashboardHeader present — page title "Planificación" visible
  it("renders the mocked DashboardHeader with page title Planificación", async () => {
    setupRole("Administrador");
    const { getByTestId } = await renderPage();

    const header = getByTestId("dashboard-header");
    expect(header.textContent).toMatch(/planificaci[oó]n/i);
  });

  // 3 — No legacy color classes in the rendered HTML
  it("contains no legacy bg-gray-50 class in rendered HTML", async () => {
    setupRole("Administrador");
    const { container } = await renderPage();
    expect(container.innerHTML).not.toContain("bg-gray-50");
  });

  it("contains no legacy bg-white/60 class in rendered HTML", async () => {
    setupRole("Administrador");
    const { container } = await renderPage();
    expect(container.innerHTML).not.toContain("bg-white/60");
  });

  it("contains no legacy bg-[#0f172a] class in rendered HTML", async () => {
    setupRole("Administrador");
    const { container } = await renderPage();
    expect(container.innerHTML).not.toContain("bg-[#0f172a]");
  });

  it("contains no legacy text-gray-500 class in rendered HTML", async () => {
    setupRole("Administrador");
    const { container } = await renderPage();
    expect(container.innerHTML).not.toContain("text-gray-500");
  });

  it("contains no legacy text-gray-900 class in rendered HTML", async () => {
    setupRole("Administrador");
    const { container } = await renderPage();
    expect(container.innerHTML).not.toContain("text-gray-900");
  });

  // 4 — Role: Administrador → hero h1 "Planificación de presentaciones"
  it("renders h1 Planificación de presentaciones for Administrador role", async () => {
    setupRole("Administrador");
    const { container } = await renderPage();

    const h1 = container.querySelector("h1");
    expect(h1).not.toBeNull();
    expect(h1!.textContent).toMatch(/planificaci[oó]n de presentaciones/i);
  });

  // 5 — Role: Tutor → hero h1 "Mis defensas"
  it("renders h1 Mis defensas for Tutor role", async () => {
    setupRole("Tutor");
    const { container } = await renderPage();

    const h1 = container.querySelector("h1");
    expect(h1).not.toBeNull();
    expect(h1!.textContent).toMatch(/mis defensas/i);
  });

  // 6 — Role: Estudiante → hero h1 contains "defensa"
  it("renders h1 containing defensa for Estudiante role", async () => {
    setupRole("Estudiante");
    const { container } = await renderPage();

    const h1 = container.querySelector("h1");
    expect(h1).not.toBeNull();
    expect(h1!.textContent).toMatch(/defensa/i);
  });
});
