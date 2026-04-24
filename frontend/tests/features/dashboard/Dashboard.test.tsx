import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen } from "@testing-library/react";

vi.mock("@features/auth/api/clientAuth", () => ({
  getUser: () => ({ id: 99, role: "Administrador", fullName: "Pedro García", email: "p@x.com" }),
}));

vi.mock("@features/projects/api/projectService", () => ({
  getAllProjects: vi.fn(async () => []),
}));

vi.mock("@features/semesters/api/semesters", () => ({
  fetchActiveSemester: vi.fn(async () => ({
    id: 1,
    period: "2026-01",
    is_active: true,
    start_month: 1,
    end_month: 6,
    label: "",
    created_at: "2025-12-01",
    project_count: 0,
  })),
  getSemesters: vi.fn(async () => [
    {
      id: 1,
      period: "2026-01",
      is_active: true,
      start_month: 1,
      end_month: 6,
      label: "",
      created_at: "2025-12-01",
      project_count: 0,
    },
  ]),
  getStoredSemester: () => "2026-01",
  setStoredSemester: () => {},
  getAvailableSemesters: () => ["2026-01"],
}));

vi.mock("next/navigation", () => ({
  useRouter: () => ({ prefetch: () => {} }),
}));

vi.mock("@widgets/header/DashboardHeader", () => ({
  default: () => <div data-testid="header" />,
}));

import Dashboard from "@features/dashboard/components/Dashboard";

describe("Dashboard layout", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("renders the dashboard hero, four tiles, list panel and activity feed for admin", async () => {
    render(<Dashboard />);
    expect(await screen.findByText(/Bienvenido/i)).toBeInTheDocument();
    expect(screen.getByText("2026-01")).toBeInTheDocument();
    expect(await screen.findByText(/Proyectos PTEG/i)).toBeInTheDocument();
    expect(screen.getAllByText(/Tesis TEG/i)[0]).toBeInTheDocument();
    expect(screen.getAllByText(/Defensas/i)[0]).toBeInTheDocument();
    expect(screen.getAllByText(/Tu acción/i)[0]).toBeInTheDocument();
  });

  it("does not render a role badge in the greeting row", async () => {
    render(<Dashboard />);
    await screen.findByText(/Bienvenido/i);
    expect(screen.queryByText(/^Administrador$/)).toBeNull();
  });
});
