import React from "react";
import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen, waitFor, fireEvent } from "@testing-library/react";
import type { Project } from "@features/projects/types/project";

// ---------------------------------------------------------------------------
// Module-level mocks
// ---------------------------------------------------------------------------

const mockGetUserRole = vi.fn<() => string | null>();
const mockGetUser = vi.fn();

vi.mock("@features/auth/api/clientAuth", () => ({
  getUser: () => mockGetUser(),
  getUserRole: () => mockGetUserRole(),
  isAuthenticated: () => true,
}));

const mockGetAllProjects = vi.fn<() => Promise<Project[]>>();

vi.mock("@features/projects/api/projectService", () => ({
  getAllProjects: () => mockGetAllProjects(),
}));

vi.mock("@features/semesters/api/semesters", async (importOriginal) => {
  const actual = await importOriginal<typeof import("@features/semesters/api/semesters")>();
  return {
    ...actual,
    getSemesters: vi.fn(async () => [
      {
        id: 1,
        period: "2026-01",
        is_active: true,
        start_month: 1,
        end_month: 6,
        label: "Ene 2026 – Jun 2026",
        created_at: "2025-12-01",
        project_count: 3,
      },
    ]),
    getStoredSemester: () => "2026-01",
    setStoredSemester: vi.fn(),
    getCurrentSemester: () => "2026-01",
    getAvailableSemesters: (_projects: Project[], extra: string[] = []) => {
      const all = new Set(["2026-01", ...extra]);
      return Array.from(all);
    },
  };
});

// next/navigation is already mocked in vitest.setup.ts, but we override
// useSearchParams per-test via the module spy (see helpers below).
vi.mock("next/navigation", async () => {
  const actual = await vi.importActual<typeof import("next/navigation")>(
    "next/navigation",
  );
  return {
    ...actual,
    useRouter: () => ({
      push: vi.fn(),
      replace: vi.fn(),
      back: vi.fn(),
      forward: vi.fn(),
      refresh: vi.fn(),
      prefetch: vi.fn(),
    }),
    useSearchParams: () => mockUseSearchParams(),
    usePathname: () => "/dashboard/tracking",
  };
});

// We use a module-level variable that each test can override.
let mockUseSearchParams = () => new URLSearchParams();

// Mock DashboardHeader to avoid unrelated dependencies.
vi.mock("@widgets/header/DashboardHeader", () => ({
  default: () => <div data-testid="dashboard-header" />,
}));

// ---------------------------------------------------------------------------
// Project fixture factory
// ---------------------------------------------------------------------------

let _idCounter = 1;

function makeProject(overrides: Partial<Project> = {}): Project {
  return {
    id: _idCounter++,
    title: "Proyecto de prueba",
    student: "Estudiante Ejemplo",
    advisorNames: ["Tutor Ejemplo"],
    reviewer: 10,
    reviewerName: "Jurado Ejemplo",
    submittedDate: "2026-02-01",
    state: "pending_review_1",
    period: "2026-01",
    type: "proyecto",
    ...overrides,
  };
}

// Canonical fixture set used across multiple tests.
const ptegPendingReview = makeProject({
  title: "Sistema de inventario platform",
  student: "Ana Torres",
  type: "proyecto",
  state: "pending_review_1",
  reviewerName: "Dr. Rodríguez",
});

const tegPendingEntrega = makeProject({
  title: "Tesis de redes neuronales",
  student: "Carlos Gómez",
  type: "tesis",
  state: "pending_entrega",
  reviewerName: "Dra. Suárez",
});

const ptegPendingDefensa = makeProject({
  title: "App de gestión estudiantil",
  student: "María López",
  type: "proyecto",
  state: "pending_defense",
  reviewerName: null,
});

const tegApproved = makeProject({
  title: "Análisis de datos climáticos",
  student: "Juan Pérez",
  type: "tesis",
  state: "approved",
  reviewerName: "Prof. Martínez",
});

// Mixed project set used across tests.
const ALL_PROJECTS: Project[] = [
  ptegPendingReview,
  tegPendingEntrega,
  ptegPendingDefensa,
  tegApproved,
];

// ---------------------------------------------------------------------------
// The component under test — imported AFTER mocks are registered.
// ---------------------------------------------------------------------------

import TrackingPage from "./page";

// ---------------------------------------------------------------------------
// Helper: render page with a given role + optional project list.
// ---------------------------------------------------------------------------

function renderPage(
  role: "Administrador" | "Jurado" | "Tutor" | "Estudiante",
  {
    projects = ALL_PROJECTS,
    userId = 10,
    searchParams = new URLSearchParams(),
  }: {
    projects?: Project[];
    userId?: number;
    searchParams?: URLSearchParams;
  } = {},
) {
  mockGetUserRole.mockReturnValue(role);
  mockGetUser.mockReturnValue({
    id: userId,
    email: "test@example.com",
    role,
    status: "active",
    fullName: "Test User",
  });
  mockGetAllProjects.mockResolvedValue(projects);
  mockUseSearchParams = () => searchParams;

  return render(<TrackingPage />);
}

// ---------------------------------------------------------------------------
// 1. Admin sees SeguimientoTable with all admin columns
// ---------------------------------------------------------------------------

describe("TrackingPage — admin view", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    _idCounter = 100;
  });

  it("renders SeguimientoTable (a <table> element) for admin", async () => {
    renderPage("Administrador");
    await waitFor(() => {
      expect(screen.getByRole("table")).toBeTruthy();
    });
  });

  it("admin sees 'Trabajo' column header", async () => {
    renderPage("Administrador");
    await waitFor(() => {
      expect(screen.getByRole("columnheader", { name: /^trabajo$/i })).toBeTruthy();
    });
  });

  it("admin sees 'Fase' column header", async () => {
    renderPage("Administrador");
    await waitFor(() => {
      expect(screen.getByRole("columnheader", { name: /^fase$/i })).toBeTruthy();
    });
  });

  it("admin sees 'Tutor / Jurado' column header", async () => {
    renderPage("Administrador");
    await waitFor(() => {
      expect(screen.getByRole("columnheader", { name: /tutor\s*\/\s*jurado/i })).toBeTruthy();
    });
  });
});

// ---------------------------------------------------------------------------
// 2. Jurado sees SeguimientoTable without "Fase" column
// ---------------------------------------------------------------------------

describe("TrackingPage — jurado view", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    _idCounter = 200;
  });

  it("renders SeguimientoTable for jurado", async () => {
    renderPage("Jurado");
    await waitFor(() => {
      expect(screen.getByRole("table")).toBeTruthy();
    });
  });

  it("jurado does NOT see 'Fase' column header", async () => {
    renderPage("Jurado");
    await waitFor(() => {
      expect(screen.getByRole("table")).toBeTruthy();
    });
    expect(screen.queryByRole("columnheader", { name: /^fase$/i })).toBeNull();
  });
});

// ---------------------------------------------------------------------------
// 3. Tutor sees SeguimientoTable with "Última actividad" column
// ---------------------------------------------------------------------------

describe("TrackingPage — tutor view", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    _idCounter = 300;
  });

  it("renders SeguimientoTable for tutor", async () => {
    renderPage("Tutor");
    await waitFor(() => {
      expect(screen.getByRole("table")).toBeTruthy();
    });
  });

  it("tutor sees 'Última actividad' column header", async () => {
    renderPage("Tutor");
    await waitFor(() => {
      expect(screen.getByRole("columnheader", { name: /última actividad/i })).toBeTruthy();
    });
  });
});

// ---------------------------------------------------------------------------
// 4. Estudiante sees MyProjectCard, not a table
// ---------------------------------------------------------------------------

describe("TrackingPage — estudiante view", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    _idCounter = 400;
  });

  const studentProject = makeProject({
    id: 401,
    title: "Mi tesis de inteligencia artificial",
    student: "Yo Mismo",
    type: "tesis",
    state: "pending_articulo",
    reviewerName: "Prof. García",
  });

  it("does NOT render a <table> for estudiante", async () => {
    renderPage("Estudiante", { projects: [studentProject] });
    // Wait for async data load to complete.
    await waitFor(() => {
      // The page should be in a settled state (no loading spinner).
      expect(screen.queryByRole("status")).toBeNull();
    });
    expect(screen.queryByRole("table")).toBeNull();
  });

  it("renders the first own project's title as a heading for estudiante", async () => {
    renderPage("Estudiante", { projects: [studentProject] });
    await waitFor(() => {
      expect(
        screen.getByText(/mi tesis de inteligencia artificial/i),
      ).toBeTruthy();
    });
  });
});

// ---------------------------------------------------------------------------
// 5. Tutor dropdown is admin-only in the filter bar
// ---------------------------------------------------------------------------

describe("TrackingPage — filter bar tutor dropdown", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    _idCounter = 500;
  });

  it("admin sees a 'Tutor' label in the filter bar", async () => {
    renderPage("Administrador");
    await waitFor(() => {
      expect(screen.getByRole("table")).toBeTruthy();
    });
    // The filter bar should expose a select/combobox with aria-label "Tutor".
    expect(screen.getByRole("combobox", { name: /tutor/i })).toBeTruthy();
  });

  it("jurado does NOT see a 'Tutor' filter in the filter bar", async () => {
    renderPage("Jurado");
    await waitFor(() => {
      expect(screen.getByRole("table")).toBeTruthy();
    });
    // There should be no combobox / select / label specifically for Tutor filter.
    // We check by looking for a labeled element named "Tutor" — not the column header.
    const tutorFilters = screen
      .queryAllByRole("combobox")
      .filter((el) => el.getAttribute("aria-label")?.toLowerCase().includes("tutor"));
    expect(tutorFilters).toHaveLength(0);

    // Also assert no text node "Tutor:" (colon distinguishes filter label from column header).
    expect(screen.queryByText(/^tutor\s*:?\s*$/i)).toBeNull();
  });
});

// ---------------------------------------------------------------------------
// 6. State filter via URL: ?state=pending_defense filters correctly
// ---------------------------------------------------------------------------

describe("TrackingPage — state filter via URL", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    _idCounter = 600;
  });

  it("with ?state=pending_defense only shows PTEG pending_defense projects", async () => {
    const defensa = makeProject({
      id: 601,
      title: "Proyecto en Defensa",
      type: "proyecto",
      state: "pending_defense",
    });
    const review1 = makeProject({
      id: 602,
      title: "Proyecto en Revisión",
      type: "proyecto",
      state: "pending_review_1",
    });
    const tegProject = makeProject({
      id: 603,
      title: "Tesis en Entrega",
      type: "tesis",
      state: "pending_entrega",
    });

    renderPage("Administrador", {
      projects: [defensa, review1, tegProject],
      searchParams: new URLSearchParams("state=pending_defense"),
    });

    await waitFor(() => {
      expect(screen.getByRole("table")).toBeTruthy();
    });

    expect(screen.getByText("Proyecto en Defensa")).toBeTruthy();
    expect(screen.queryByText("Proyecto en Revisión")).toBeNull();
    expect(screen.queryByText("Tesis en Entrega")).toBeNull();
  });
});

// ---------------------------------------------------------------------------
// 7. Search filters by title
// ---------------------------------------------------------------------------

describe("TrackingPage — search filter", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    _idCounter = 700;
  });

  it("typing in the search input hides non-matching rows", async () => {
    const p1 = makeProject({
      id: 701,
      title: "Sistema de gestión de inventario",
      state: "pending_review_1",
    });
    const p2 = makeProject({
      id: 702,
      title: "Plataforma de aprendizaje platform",
      state: "pending_review_2",
    });

    renderPage("Administrador", { projects: [p1, p2] });

    await waitFor(() => {
      expect(screen.getByRole("table")).toBeTruthy();
    });

    // Both projects should be visible initially.
    expect(screen.getByText("Sistema de gestión de inventario")).toBeTruthy();
    expect(screen.getByText("Plataforma de aprendizaje platform")).toBeTruthy();

    // Type "platform" into the search input.
    const searchInput = screen.getByRole("textbox", { name: /buscar/i });
    fireEvent.change(searchInput, { target: { value: "platform" } });

    await waitFor(() => {
      expect(screen.queryByText("Sistema de gestión de inventario")).toBeNull();
    });
    expect(screen.getByText("Plataforma de aprendizaje platform")).toBeTruthy();
  });
});

// ---------------------------------------------------------------------------
// 8. Hero pill-summary shows active-project count
// ---------------------------------------------------------------------------

describe("TrackingPage — hero pill-summary", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    _idCounter = 800;
  });

  it("renders a pill-summary line with a number followed by a Spanish phrase", async () => {
    renderPage("Administrador", {
      projects: [
        makeProject({ id: 801, state: "pending_review_1" }),
        makeProject({ id: 802, state: "pending_review_2" }),
        makeProject({ id: 803, state: "approved" }),
      ],
    });

    await waitFor(() => {
      expect(screen.getByRole("table")).toBeTruthy();
    });

    // The pill-summary should contain a digit followed by Spanish words.
    // We match broadly since the exact copy may evolve.
    const summaryEl = document.querySelector(".seg-pill-summary, .pill-summary, [class*='pill-summary'], [class*='seg-summary']");
    expect(summaryEl, "Expected a pill-summary element in the hero band").not.toBeNull();
    expect(summaryEl!.textContent).toMatch(/\d/);
  });
});
