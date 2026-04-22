import React from "react";
import { render, screen, fireEvent } from "@testing-library/react";
import { vi, describe, it, expect, beforeEach } from "vitest";

vi.mock("next/navigation", () => ({
  usePathname: vi.fn(() => "/dashboard"),
  useRouter: vi.fn(() => ({
    push: vi.fn(),
    prefetch: vi.fn(),
  })),
}));

vi.mock("next/image", () => ({
  default: ({ alt, ...props }: { alt: string; [key: string]: unknown }) => (
    // eslint-disable-next-line @next/next/no-img-element
    <img alt={alt} {...(props as React.ImgHTMLAttributes<HTMLImageElement>)} />
  ),
}));

vi.mock("@features/auth/api/clientAuth", () => ({
  getUser: vi.fn(() => null),
  getUserRole: vi.fn(() => null),
  getUserEmail: vi.fn(() => null),
  logout: vi.fn(),
}));

vi.mock("@widgets/sidebar/SidebarContext", () => ({
  useSidebar: vi.fn(() => ({
    isCollapsed: false,
    setIsCollapsed: vi.fn(),
    toggleCollapse: vi.fn(),
    mobileOpen: false,
    setMobileOpen: vi.fn(),
    toggleMobile: vi.fn(),
  })),
}));

import type { AppRouterInstance } from "next/dist/shared/lib/app-router-context.shared-runtime";
import { usePathname, useRouter } from "next/navigation";
import { getUser, getUserRole, getUserEmail } from "@features/auth/api/clientAuth";
import { useSidebar } from "@widgets/sidebar/SidebarContext";
import Sidebar from "@widgets/sidebar/Sidebar";
import DashboardHeader from "@widgets/header/DashboardHeader";

function makeRouter(overrides: Partial<AppRouterInstance> = {}): AppRouterInstance {
  return {
    push: vi.fn(),
    prefetch: vi.fn(),
    back: vi.fn(),
    forward: vi.fn(),
    refresh: vi.fn(),
    replace: vi.fn(),
    ...overrides,
  } as unknown as AppRouterInstance;
}

const mockSidebarProps = {
  isCollapsed: false,
  setIsCollapsed: vi.fn(),
  mobileOpen: false,
  setMobileOpen: vi.fn(),
};

describe("Sidebar", () => {
  beforeEach(() => {
    vi.mocked(usePathname).mockReturnValue("/dashboard");
    vi.mocked(useRouter).mockReturnValue(makeRouter());
    vi.mocked(getUser).mockReturnValue(null);
    vi.mocked(getUserRole).mockReturnValue(null);
  });

  it("sets aria-current='page' on the active link when pathname matches", () => {
    vi.mocked(usePathname).mockReturnValue("/dashboard");
    render(<Sidebar {...mockSidebarProps} />);
    const activeLinks = screen.getAllByRole("link", { name: /dashboard/i });
    expect(activeLinks.length).toBeGreaterThan(0);
    expect(activeLinks[0]).toHaveAttribute("aria-current", "page");
  });

  it("does not set aria-current on inactive links", () => {
    vi.mocked(usePathname).mockReturnValue("/dashboard");
    vi.mocked(getUserRole).mockReturnValue("Administrador");
    render(<Sidebar {...mockSidebarProps} />);
    const ptegLinks = screen.getAllByRole("link", { name: /pteg/i });
    ptegLinks.forEach((link) => {
      expect(link).not.toHaveAttribute("aria-current", "page");
    });
  });

  it("renders TEG link for Estudiante in semester 10", () => {
    vi.mocked(getUserRole).mockReturnValue("Estudiante");
    vi.mocked(getUser).mockReturnValue({
      email: "student@test.com",
      role: "Estudiante",
      status: "active",
      semester: "10mo Semestre",
    });
    render(<Sidebar {...mockSidebarProps} />);
    expect(screen.getAllByRole("link", { name: /teg/i }).length).toBeGreaterThan(0);
    expect(screen.queryByRole("link", { name: /^pteg$/i })).not.toBeInTheDocument();
  });

  it("renders PTEG link for Estudiante in earlier semester", () => {
    vi.mocked(getUserRole).mockReturnValue("Estudiante");
    vi.mocked(getUser).mockReturnValue({
      email: "student@test.com",
      role: "Estudiante",
      status: "active",
      semester: "8vo Semestre",
    });
    render(<Sidebar {...mockSidebarProps} />);
    expect(screen.getAllByRole("link", { name: /pteg/i }).length).toBeGreaterThan(0);
    expect(screen.queryByRole("link", { name: /^teg$/i })).not.toBeInTheDocument();
  });

  it("renders all menu items for Administrador", () => {
    vi.mocked(getUserRole).mockReturnValue("Administrador");
    render(<Sidebar {...mockSidebarProps} />);
    expect(screen.getAllByRole("link", { name: /pteg/i }).length).toBeGreaterThan(0);
    expect(screen.getAllByRole("link", { name: /teg/i }).length).toBeGreaterThan(0);
    expect(screen.getAllByRole("link", { name: /agregar/i }).length).toBeGreaterThan(0);
    expect(screen.getAllByRole("link", { name: /planificación/i }).length).toBeGreaterThan(0);
  });

  it("fires router.push('/dashboard') on Alt+1 keydown", () => {
    const mockPush = vi.fn();
    vi.mocked(useRouter).mockReturnValue(makeRouter({ push: mockPush }));
    render(<Sidebar {...mockSidebarProps} />);
    fireEvent.keyDown(window, { key: "1", altKey: true });
    expect(mockPush).toHaveBeenCalledWith("/dashboard");
  });
});

describe("DashboardHeader", () => {
  beforeEach(() => {
    vi.mocked(useRouter).mockReturnValue(makeRouter());
    vi.mocked(getUserEmail).mockReturnValue("test@example.com");
    vi.mocked(getUserRole).mockReturnValue("Administrador");
    vi.mocked(useSidebar).mockReturnValue({
      isCollapsed: false,
      setIsCollapsed: vi.fn(),
      toggleCollapse: vi.fn(),
      mobileOpen: false,
      setMobileOpen: vi.fn(),
      toggleMobile: vi.fn(),
    });
  });

  function getProfileButton() {
    return screen.getAllByRole("button").find(
      (btn) => btn.getAttribute("aria-haspopup") === "menu"
    )!;
  }

  it("opens profile dropdown on button click and renders user email", () => {
    render(<DashboardHeader pageTitle="Dashboard" />);
    fireEvent.click(getProfileButton());
    expect(screen.getByText("test@example.com")).toBeInTheDocument();
  });

  it("dropdown does not contain 'Identificado como'", () => {
    render(<DashboardHeader pageTitle="Dashboard" />);
    fireEvent.click(getProfileButton());
    expect(screen.queryByText("Identificado como")).not.toBeInTheDocument();
  });

  it("dropdown contains Configuración and Cerrar Sesión buttons", () => {
    render(<DashboardHeader pageTitle="Dashboard" />);
    fireEvent.click(getProfileButton());
    expect(screen.getByRole("button", { name: /configuración/i })).toBeInTheDocument();
    expect(screen.getByRole("button", { name: /cerrar sesión/i })).toBeInTheDocument();
  });

  it("profile button has aria-expanded='false' when closed and 'true' when open", () => {
    render(<DashboardHeader pageTitle="Dashboard" />);
    const btn = getProfileButton();
    expect(btn).toHaveAttribute("aria-expanded", "false");
    fireEvent.click(btn);
    expect(btn).toHaveAttribute("aria-expanded", "true");
  });

  it("closes profile dropdown on outside click", () => {
    render(<DashboardHeader pageTitle="Dashboard" />);
    fireEvent.click(getProfileButton());
    expect(screen.getByText("Cerrar Sesión")).toBeInTheDocument();
    fireEvent.mouseDown(document.body);
    expect(screen.queryByText("Cerrar Sesión")).not.toBeInTheDocument();
  });

  it("calls sidebar.toggleMobile when mobile menu button is clicked", () => {
    const mockToggleMobile = vi.fn();
    vi.mocked(useSidebar).mockReturnValue({
      isCollapsed: false,
      setIsCollapsed: vi.fn(),
      toggleCollapse: vi.fn(),
      mobileOpen: false,
      setMobileOpen: vi.fn(),
      toggleMobile: mockToggleMobile,
    });
    render(<DashboardHeader pageTitle="Dashboard" />);
    const mobileToggle = screen.getByRole("button", { name: /abrir menú/i });
    fireEvent.click(mobileToggle);
    expect(mockToggleMobile).toHaveBeenCalledOnce();
  });
});
