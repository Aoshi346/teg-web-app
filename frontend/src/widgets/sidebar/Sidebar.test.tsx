import React from "react";
import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen, waitFor } from "@testing-library/react";

// ── next/image mock ───────────────────────────────────────────────────────────
vi.mock("next/image", () => ({
  default: ({ src, alt }: { src: string; alt: string }) => (
    // eslint-disable-next-line @next/next/no-img-element
    <img src={src} alt={alt} />
  ),
}));

// ── next/link mock ────────────────────────────────────────────────────────────
vi.mock("next/link", () => ({
  default: ({
    href,
    children,
    onClick,
    onMouseEnter,
    className,
    ...rest
  }: React.AnchorHTMLAttributes<HTMLAnchorElement> & {
    href: string;
    children?: React.ReactNode;
  }) => (
    <a href={href} onClick={onClick} onMouseEnter={onMouseEnter} className={className} {...rest}>
      {children}
    </a>
  ),
}));

// ── gsap mock — the sidebar lazy-imports gsap for drawer animation ────────────
vi.mock("gsap", () => ({
  gsap: { to: vi.fn(), fromTo: vi.fn() },
}));

// ── clientAuth mock ───────────────────────────────────────────────────────────
const mockGetUserRole = vi.fn<() => string | null>();
const mockGetUser = vi.fn();

vi.mock("@features/auth/api/clientAuth", () => ({
  getUser: () => mockGetUser(),
  getUserRole: () => mockGetUserRole(),
}));

// ── component under test ──────────────────────────────────────────────────────
import Sidebar from "./Sidebar";

// ─────────────────────────────────────────────────────────────────────────────

const defaultProps = {
  isCollapsed: false,
  setIsCollapsed: vi.fn(),
  mobileOpen: false,
  setMobileOpen: vi.fn(),
};

describe("Sidebar — Agregar item role gating", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("Administrador sees the Agregar item in the sidebar", async () => {
    mockGetUserRole.mockReturnValue("Administrador");
    mockGetUser.mockReturnValue({ email: "admin@test.com", role: "Administrador", status: "active" });

    render(<Sidebar {...defaultProps} />);

    // Note: the sidebar renders the menu list twice — desktop <aside> + mobile portal drawer.
    // We use queryAllByText and check at least one instance is present.
    await waitFor(() => {
      expect(screen.queryAllByText(/^Agregar$/i).length).toBeGreaterThan(0);
    });
  });

  it("Tutor does NOT see the Agregar item in the sidebar", async () => {
    mockGetUserRole.mockReturnValue("Tutor");
    mockGetUser.mockReturnValue({ email: "tutor@test.com", role: "Tutor", status: "active" });

    render(<Sidebar {...defaultProps} />);

    await waitFor(() => {
      expect(screen.queryAllByText(/^Agregar$/i)).toHaveLength(0);
    });
  });

  it("Jurado does NOT see the Agregar item in the sidebar", async () => {
    mockGetUserRole.mockReturnValue("Jurado");
    mockGetUser.mockReturnValue({ email: "jurado@test.com", role: "Jurado", status: "active" });

    render(<Sidebar {...defaultProps} />);

    await waitFor(() => {
      expect(screen.queryAllByText(/^Agregar$/i)).toHaveLength(0);
    });
  });

  it("Estudiante (semester 9no) does NOT see the Agregar item in the sidebar", async () => {
    mockGetUserRole.mockReturnValue("Estudiante");
    mockGetUser.mockReturnValue({
      email: "student@test.com",
      role: "Estudiante",
      status: "active",
      semester: "9no",
    });

    render(<Sidebar {...defaultProps} />);

    await waitFor(() => {
      expect(screen.queryAllByText(/^Agregar$/i)).toHaveLength(0);
    });
  });

  it("Administrador sees all expected base navigation items", async () => {
    mockGetUserRole.mockReturnValue("Administrador");
    mockGetUser.mockReturnValue({ email: "admin@test.com", role: "Administrador", status: "active" });

    render(<Sidebar {...defaultProps} />);

    await waitFor(() => {
      expect(screen.queryAllByText(/^Dashboard$/i).length).toBeGreaterThan(0);
    });

    expect(screen.queryAllByText(/^PTEG$/i).length).toBeGreaterThan(0);
    expect(screen.queryAllByText(/^TEG$/i).length).toBeGreaterThan(0);
    expect(screen.queryAllByText(/^Seguimiento$/i).length).toBeGreaterThan(0);
    expect(screen.queryAllByText(/^Configuración$/i).length).toBeGreaterThan(0);
  });
});
