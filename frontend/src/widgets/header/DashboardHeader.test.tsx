import React from "react";
import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen, fireEvent } from "@testing-library/react";
import * as SidebarContext from "@widgets/sidebar/SidebarContext";

// ── next/navigation mock ──────────────────────────────────────────────────────
// vitest.setup.ts already mocks this globally; re-declare here so we can
// spy on the push call within individual tests if needed.
vi.mock("next/navigation", async () => {
  const actual = await vi.importActual<typeof import("next/navigation")>("next/navigation");
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
    usePathname: () => "/dashboard/planificacion",
    useSearchParams: () => new URLSearchParams(),
  };
});

// ── clientAuth mock ───────────────────────────────────────────────────────────
const mockGetUserEmail = vi.fn<() => string | null>();
const mockGetUserRole = vi.fn<() => string | null>();
const mockLogout = vi.fn();

vi.mock("@features/auth/api/clientAuth", () => ({
  getUserEmail: () => mockGetUserEmail(),
  getUserRole: () => mockGetUserRole(),
  logout: () => mockLogout(),
  // Sidebar.tsx also imports getUser/getUserRole — keep them available
  getUser: () => null,
}));

// ── NotificationBell stub ─────────────────────────────────────────────────────
vi.mock("@features/notifications", () => ({
  NotificationBell: () => <div data-testid="notification-bell" />,
}));

// ── SidebarContext mock ───────────────────────────────────────────────────────
const mockToggleCollapse = vi.fn();
const mockToggleMobile = vi.fn();

vi.mock("@widgets/sidebar/SidebarContext", () => ({
  useSidebar: vi.fn(),
}));

// ── ProfileMenu stub — render it predictably ──────────────────────────────────
// We test open/close behavior via the hd-prof chip; ProfileMenu internals are
// tested separately in ProfileMenu.test.tsx.
vi.mock("@widgets/header/ProfileMenu", () => ({
  default: ({ isOpen }: { isOpen: boolean }) =>
    isOpen ? <div data-testid="profile-menu" role="menu" /> : null,
}));

// ── component under test ──────────────────────────────────────────────────────
import DashboardHeader from "./DashboardHeader";

// ─────────────────────────────────────────────────────────────────────────────

function setup(overrides?: Partial<{ pageTitle: string }>) {
  mockGetUserEmail.mockReturnValue("salazar@unimet.edu.ve");
  mockGetUserRole.mockReturnValue("Administrador");
  vi.mocked(SidebarContext.useSidebar).mockReturnValue({
    isCollapsed: false,
    setIsCollapsed: vi.fn(),
    mobileOpen: false,
    setMobileOpen: vi.fn(),
    toggleCollapse: mockToggleCollapse,
    toggleMobile: mockToggleMobile,
  });
  return render(<DashboardHeader pageTitle={overrides?.pageTitle ?? "Planificación"} />);
}

describe("DashboardHeader — basic structure", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("renders a <header> element", () => {
    setup();
    expect(screen.getByRole("banner")).toBeInTheDocument();
  });

  it("desktop collapse button has aria-label matching /colapsar|expandir/i", () => {
    setup();
    const btn = screen.getByRole("button", { name: /colapsar|expandir/i });
    expect(btn).toBeInTheDocument();
  });

  it("clicking the collapse button calls toggleCollapse", () => {
    setup();
    const btn = screen.getByRole("button", { name: /colapsar|expandir/i });
    fireEvent.click(btn);
    expect(mockToggleCollapse).toHaveBeenCalledTimes(1);
  });

  it("mobile hamburger button has aria-label matching /^(abrir|cerrar) menú$/i", () => {
    setup();
    const btn = screen.getByRole("button", { name: /^(abrir|cerrar) menú$/i });
    expect(btn).toBeInTheDocument();
  });

  it("clicking the mobile hamburger calls toggleMobile", () => {
    setup();
    const btn = screen.getByRole("button", { name: /^(abrir|cerrar) menú$/i });
    fireEvent.click(btn);
    expect(mockToggleMobile).toHaveBeenCalledTimes(1);
  });
});

describe("DashboardHeader — no plain page title heading", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("does NOT render pageTitle as a standalone <h2> heading", () => {
    setup({ pageTitle: "Planificación" });
    expect(screen.queryByRole("heading", { name: "Planificación" })).toBeNull();
  });
});

describe("DashboardHeader — breadcrumb (expanded, isCollapsed=false)", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("renders the .hd-crumb element when sidebar is expanded", () => {
    const { container } = setup();
    expect(container.querySelector(".hd-crumb")).not.toBeNull();
  });

  it(".hd-crumb contains a home link with text 'Workspace'", () => {
    const { container } = setup();
    const crumb = container.querySelector(".hd-crumb");
    expect(crumb).not.toBeNull();
    expect(crumb!.textContent).toMatch(/Workspace/i);
  });

  it(".hd-crumb-now segment contains the page title", () => {
    const { container } = setup({ pageTitle: "Planificación" });
    const now = container.querySelector(".hd-crumb-now");
    expect(now).not.toBeNull();
    expect(now!.textContent).toMatch(/Planificación/i);
  });

  it(".hd-crumb does NOT exist (pill used instead) when sidebar is collapsed", () => {
    // Rerender with collapsed sidebar context
    vi.mocked(SidebarContext.useSidebar).mockReturnValue({
      isCollapsed: true,
      setIsCollapsed: vi.fn(),
      mobileOpen: false,
      setMobileOpen: vi.fn(),
      toggleCollapse: mockToggleCollapse,
      toggleMobile: mockToggleMobile,
    });
    const { container } = render(<DashboardHeader pageTitle="Planificación" />);
    expect(container.querySelector(".hd-crumb")).toBeNull();
  });
});

describe("DashboardHeader — breadcrumb pill (collapsed)", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    mockGetUserEmail.mockReturnValue("salazar@unimet.edu.ve");
    mockGetUserRole.mockReturnValue("Administrador");
    vi.mocked(SidebarContext.useSidebar).mockReturnValue({
      isCollapsed: true,
      setIsCollapsed: vi.fn(),
      mobileOpen: false,
      setMobileOpen: vi.fn(),
      toggleCollapse: mockToggleCollapse,
      toggleMobile: mockToggleMobile,
    });
  });

  it("renders .hd-crumb-pill when isCollapsed=true", () => {
    const { container } = render(<DashboardHeader pageTitle="Planificación" />);
    expect(container.querySelector(".hd-crumb-pill")).not.toBeNull();
  });

  it("first .step in pill shows 'Workspace' (uppercase)", () => {
    const { container } = render(<DashboardHeader pageTitle="Planificación" />);
    const steps = container.querySelectorAll(".hd-crumb-pill .step");
    expect(steps.length).toBeGreaterThanOrEqual(1);
    expect(steps[0].textContent?.toUpperCase()).toContain("WORKSPACE");
  });

  it("second .step in pill contains the page title", () => {
    const { container } = render(<DashboardHeader pageTitle="Planificación" />);
    const steps = container.querySelectorAll(".hd-crumb-pill .step");
    expect(steps.length).toBeGreaterThanOrEqual(2);
    expect(steps[1].textContent).toMatch(/Planificación/i);
  });

  it(".hd-crumb-pill does NOT have class hd-crumb", () => {
    const { container } = render(<DashboardHeader pageTitle="Planificación" />);
    const pill = container.querySelector(".hd-crumb-pill");
    expect(pill).not.toBeNull();
    expect(pill!.classList.contains("hd-crumb")).toBe(false);
  });
});

describe("DashboardHeader — notification bell", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("renders the NotificationBell stub", () => {
    setup();
    expect(screen.getByTestId("notification-bell")).toBeInTheDocument();
  });
});

describe("DashboardHeader — profile chip", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("profile chip element with class hd-prof is rendered", () => {
    const { container } = setup();
    expect(container.querySelector(".hd-prof")).not.toBeNull();
  });

  it("profile chip contains avatar element with class hd-prof-ava", () => {
    const { container } = setup();
    expect(container.querySelector(".hd-prof-ava")).not.toBeNull();
  });

  it("profile chip shows name derived from email (local part, first letter uppercased)", () => {
    setup();
    // "salazar@unimet.edu.ve" → "Salazar"
    const { container } = render(<DashboardHeader pageTitle="Planificación" />);
    const nameEl = container.querySelector(".hd-prof-name");
    expect(nameEl).not.toBeNull();
    expect(nameEl!.textContent?.toLowerCase()).toContain("salazar");
  });

  it("profile chip contains a chevron element", () => {
    const { container } = setup();
    const chip = container.querySelector(".hd-prof");
    expect(chip).not.toBeNull();
    // Chevron is inside the hd-prof button (svg or element with class chev)
    expect(chip!.querySelector("svg, .chev")).not.toBeNull();
  });
});

describe("DashboardHeader — profile chip toggles ProfileMenu", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    mockGetUserEmail.mockReturnValue("salazar@unimet.edu.ve");
    mockGetUserRole.mockReturnValue("Administrador");
    vi.mocked(SidebarContext.useSidebar).mockReturnValue({
      isCollapsed: false,
      setIsCollapsed: vi.fn(),
      mobileOpen: false,
      setMobileOpen: vi.fn(),
      toggleCollapse: mockToggleCollapse,
      toggleMobile: mockToggleMobile,
    });
  });

  it("ProfileMenu is not visible initially", () => {
    render(<DashboardHeader pageTitle="Planificación" />);
    expect(screen.queryByTestId("profile-menu")).toBeNull();
  });

  it("clicking the profile chip opens the ProfileMenu", () => {
    const { container } = render(<DashboardHeader pageTitle="Planificación" />);
    const chip = container.querySelector(".hd-prof") as HTMLElement;
    fireEvent.click(chip);
    expect(screen.getByTestId("profile-menu")).toBeInTheDocument();
  });

  it("clicking the profile chip a second time closes the ProfileMenu", () => {
    const { container } = render(<DashboardHeader pageTitle="Planificación" />);
    const chip = container.querySelector(".hd-prof") as HTMLElement;
    fireEvent.click(chip);
    expect(screen.getByTestId("profile-menu")).toBeInTheDocument();
    fireEvent.click(chip);
    expect(screen.queryByTestId("profile-menu")).toBeNull();
  });

  // ESC + outside-click are owned by ProfileMenu (covered in ProfileMenu.test.tsx).
  // DashboardHeader only forwards onClose; the toggle test above verifies the wire-up.
});

describe("DashboardHeader — no legacy color classes", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  const BANNED_CLASSES = [
    "text-slate-",
    "bg-slate-",
    "bg-primary/10",
    "border-slate-",
    "bg-blue-100",
    "bg-purple-100",
    "bg-emerald-100",
    "bg-amber-100",
  ];

  it("rendered HTML does not contain legacy Tailwind color classes", () => {
    const { container } = setup();
    const html = container.innerHTML;
    for (const cls of BANNED_CLASSES) {
      expect(html, `should not contain '${cls}'`).not.toContain(cls);
    }
  });
});
